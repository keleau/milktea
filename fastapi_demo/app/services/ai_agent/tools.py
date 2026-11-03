import logging
import re
import threading
import time
import uuid
from datetime import datetime
from difflib import SequenceMatcher

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import ICE_OPTIONS, STATE_TEXT, SUGAR_OPTIONS
from app.core.response import BizError
from app.models import Order, Product, Store, Topping, User
from app.serializers import money
from app.services import orders as order_service

logger = logging.getLogger("simaotea.ai")

_recent_lock = threading.Lock()
_recent_orders: dict[tuple, tuple[str, float]] = {}


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", value or "").lower()


def _match_products(db: Session, name: str) -> list[Product]:
    products = db.scalars(
        select(Product).order_by(Product.sort_order, Product.id)
    ).all()
    query = _normalize(name)
    if not query:
        return []

    exact = [product for product in products if _normalize(product.name) == query]
    if exact:
        return exact

    partial = [
        product
        for product in products
        if query in _normalize(product.name) or _normalize(product.name) in query
    ]
    if partial:
        return partial

    scored = [
        (SequenceMatcher(None, query, _normalize(product.name)).ratio(), product)
        for product in products
    ]
    scored = [(ratio, product) for ratio, product in scored if ratio >= 0.5]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [product for _, product in scored[:3]]


def _stock_text(product: Product) -> str:
    if not product.on_sale:
        return "已下架"
    if product.stock <= 0:
        return "已售罄"
    return f"库存 {product.stock}"


def _product_text(product: Product) -> str:
    text = f"{product.name}｜¥{money(product.price)}｜{_stock_text(product)}"
    if product.description:
        text += f"｜{product.description}"
    return text


def _menu_text(products: list[Product], limit: int = 12) -> str:
    if not products:
        return "当前没有可售饮品。"
    return "；".join(_product_text(product) for product in products[:limit])


def _prune_recent() -> None:
    cutoff = time.monotonic() - 120
    stale = [key for key, (_, created_at) in _recent_orders.items() if created_at < cutoff]
    for key in stale:
        _recent_orders.pop(key, None)


def build_tools(
    db: Session,
    user: User,
    store_id: int,
    context: dict,
    table_no: str | None = None,
) -> list:
    store = db.get(Store, store_id)
    toppings = db.scalars(select(Topping).order_by(Topping.sort_order, Topping.id)).all()
    topping_label = "、".join(f"{topping.name}（¥{money(topping.price)}）" for topping in toppings)

    @tool
    def query_stock(goods_name: str = "") -> str:
        """查询饮品库存与价格。goods_name 传用户提到的饮品名；为空时返回有库存的在售菜单，适合做推荐。"""
        name = (goods_name or "").strip()
        if not name:
            products = db.scalars(
                select(Product)
                .where(Product.on_sale.is_(True))
                .order_by(Product.sort_order, Product.id)
            ).all()
            available = [product for product in products if product.stock > 0]
            return "在售且有库存的饮品：" + _menu_text(available)

        matches = _match_products(db, name)
        if not matches:
            products = db.scalars(
                select(Product)
                .where(Product.on_sale.is_(True))
                .order_by(Product.sort_order, Product.id)
            ).all()
            return f"没有找到「{name}」。目前在售：{_menu_text(products)}"

        if len(matches) > 1:
            options = "；".join(_product_text(product) for product in matches[:6])
            return f"「{name}」匹配到多款饮品：{options}。请让用户确认完整名称后再继续。"

        product = matches[0]
        return (
            f"{_product_text(product)}。冰度可选 {'、'.join(ICE_OPTIONS)}；"
            f"糖度可选 {'、'.join(SUGAR_OPTIONS)}。"
        )

    @tool
    def create_order(
        goods_name: str,
        ice: str,
        sugar: str,
        count: int = 1,
        topping_names: str = "",
    ) -> str:
        """创建自取订单。参数必须来自用户明确表述；下单前先确认商品全名、数量、冰度、糖度。"""
        if store is None:
            return "当前没有可用门店，暂时无法下单。"
        if store.status == "closed":
            return f"{store.name} 已打烊，暂时无法下单，建议换一家门店或稍后再试。"
        if context.get("order_no"):
            existing = db.get(Order, context["order_no"])
            if existing is not None:
                return (
                    f"本轮已经创建过订单 {existing.out_trade_no}，请勿重复下单；"
                    "提醒用户到订单详情支付即可。"
                )

        name = (goods_name or "").strip()
        if not name:
            return "缺少饮品名称，请先向用户确认想喝哪一款。"
        if ice not in ICE_OPTIONS:
            return f"冰度不合法，必须是：{'、'.join(ICE_OPTIONS)}。请向用户确认。"
        if sugar not in SUGAR_OPTIONS:
            return f"糖度不合法，必须是：{'、'.join(SUGAR_OPTIONS)}。请向用户确认。"
        try:
            quantity = int(count)
        except (TypeError, ValueError):
            return "数量必须是整数杯数，请向用户确认。"
        if quantity < 1 or quantity > 99:
            return "数量需为 1~99 杯，请向用户确认。"

        matches = _match_products(db, name)
        if not matches:
            return f"菜单里没有「{name}」，不能下单。请让用户换一款在售饮品。"
        if len(matches) > 1:
            options = "；".join(_product_text(product) for product in matches[:6])
            return f"「{name}」匹配到多款饮品：{options}。请让用户说完整名称后再下单。"

        product = matches[0]
        if not product.on_sale:
            return f"{product.name} 已下架，不能下单，请推荐其他在售饮品。"
        if product.stock <= 0:
            return f"{product.name} 已售罄，不能下单。可以推荐用户换一款有库存的饮品。"
        if product.stock < quantity:
            return f"{product.name} 目前只剩 {product.stock} 杯，无法下单 {quantity} 杯。"

        picked_toppings: list[Topping] = []
        seen_topping_ids: set[int] = set()
        for raw_name in re.split(r"[+＋、,，/\s]+", topping_names or ""):
            raw_name = raw_name.strip()
            if not raw_name:
                continue
            matched = [item for item in toppings if _normalize(item.name) == _normalize(raw_name)]
            if not matched:
                return f"没有找到小料「{raw_name}」。可选小料：{topping_label or '暂无'}。"
            if matched[0].id not in seen_topping_ids:
                seen_topping_ids.add(matched[0].id)
                picked_toppings.append(matched[0])

        recent_key = (
            user.id,
            store.id,
            table_no,
            product.id,
            ice,
            sugar,
            quantity,
            tuple(topping.id for topping in picked_toppings),
        )
        now = time.monotonic()
        with _recent_lock:
            _prune_recent()
            cached = _recent_orders.get(recent_key)
            if cached is not None and now - cached[1] < 30:
                cached_order = db.get(Order, cached[0])
                if cached_order is not None:
                    context["order_no"] = cached_order.out_trade_no
                    return (
                        f"同一杯订单刚刚已经创建过（订单号 {cached_order.out_trade_no}），"
                        "请勿重复下单，直接提醒用户去订单详情支付即可。"
                    )

        payload = {
            "store_id": store.id,
            "mode": "pickup",
            "coupon_id": None,
            "remark": "AI 点单",
            "table_no": table_no,
            "items": [
                {
                    "product_id": product.id,
                    "ice": ice,
                    "sugar": sugar,
                    "topping_ids": [topping.id for topping in picked_toppings],
                    "count": quantity,
                }
            ],
        }
        try:
            order = order_service.create_order(
                db,
                user,
                payload,
                idempotency_key=f"AI-{user.id}-{uuid.uuid4().hex[:12]}",
            )
        except BizError as exc:
            return f"下单未成功：{exc.message}"
        except Exception:
            logger.exception("AI 下单工具异常 user_id=%s", user.id)
            return "下单失败：系统繁忙，请稍后再试。"

        with _recent_lock:
            _recent_orders[recent_key] = (order.out_trade_no, now)
        context["order_no"] = order.out_trade_no

        spec = f"{ice}/{sugar}"
        if picked_toppings:
            spec += "+" + "+".join(topping.name for topping in picked_toppings)
        return (
            f"下单成功：{product.name}×{quantity}（{spec}），门店 {order.store_name}，"
            f"合计 ¥{money(order.total)}，订单号 {order.out_trade_no}，"
            f"当前状态 {STATE_TEXT[order.state]}。请提醒用户到订单详情完成支付。"
        )

    @tool
    def query_my_orders(limit: int = 3) -> str:
        """查询当前登录用户最近的订单状态、金额和取餐码。用户问订单进度时使用。"""
        try:
            size = max(1, min(int(limit), 5))
        except (TypeError, ValueError):
            size = 3
        orders = db.scalars(
            select(Order)
            .where(Order.user_id == user.id)
            .order_by(Order.create_time.desc())
            .limit(size)
        ).all()
        if not orders:
            return "当前账号还没有订单记录。"

        lines = []
        for order in orders:
            item_text = "、".join(f"{item.name}×{item.count}" for item in order.items[:3])
            created = datetime.fromtimestamp(order.create_time / 1000).strftime("%m-%d %H:%M")
            extra = f"，取餐码 {order.pick_code}" if order.pick_code else ""
            lines.append(
                f"{order.out_trade_no}｜{STATE_TEXT[order.state]}｜{item_text}"
                f"｜¥{money(order.total)}｜{created}{extra}"
            )
        return "最近订单：" + "；".join(lines)

    return [query_stock, create_order, query_my_orders]
