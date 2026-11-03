import random

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.constants import MODE_TEXT, STATE_TEXT, now_ms
from app.core.config import settings
from app.core.response import BizError
from app.models import (
    Address,
    IdempotencyKey,
    Order,
    OrderItem,
    OrderItemTopping,
    Product,
    Store,
    User,
    UserCoupon,
)
from app.services.coupons import (
    claim_for_order,
    consume_for_order,
    release_for_order,
)
from app.services.member import change_points
from app.services.pricing import quote
from app.tables import table_exists


def get_owned_order(
    db: Session,
    user: User,
    out_trade_no: str,
    for_update: bool = False,
) -> Order:
    statement = select(Order).where(Order.out_trade_no == out_trade_no)
    if for_update:
        statement = statement.with_for_update()
    order = db.scalar(statement)
    if order is None:
        raise BizError(1004, "订单不存在", 404)
    if order.user_id != user.id:
        raise BizError(1003, "无权操作该订单", 403)
    return order


def _snapshot_quantities(snapshots: list[dict]) -> tuple[dict[int, int], dict[int, str]]:
    required: dict[int, int] = {}
    names: dict[int, str] = {}
    for snapshot in snapshots:
        product_id = snapshot["product_id"]
        required[product_id] = required.get(product_id, 0) + snapshot["count"]
        names[product_id] = snapshot["name"]
    return required, names


def _order_quantities(order: Order) -> tuple[dict[int, int], dict[int, str]]:
    required: dict[int, int] = {}
    names: dict[int, str] = {}
    for item in order.items:
        required[item.product_id] = required.get(item.product_id, 0) + item.count
        names[item.product_id] = item.name
    return required, names


def _normalize_table_no(payload: dict, store: Store) -> str | None:
    table_no = (payload.get("table_no") or "").strip().upper() or None
    if not table_no:
        return None
    if payload["mode"] != "pickup":
        raise BizError(1001, "堂食订单只能选自取", 400)
    if not table_exists(store.id, table_no):
        raise BizError(1004, "桌号不存在，请重新扫码", 404)
    return table_no


def _resolve_address(db: Session, user: User, payload: dict) -> Address | None:
    if payload["mode"] != "delivery":
        return None
    address_id = payload.get("address_id")
    if not address_id:
        raise BizError(1001, "外送订单需要选择收货地址", 400)
    address = db.get(Address, address_id)
    if address is None or address.user_id != user.id:
        raise BizError(1004, "收货地址不存在", 404)
    return address


def _deduct_stock(
    db: Session,
    required: dict[int, int],
    names: dict[int, str] | None = None,
) -> None:
    """条件更新扣库存：并发下只有库存足够的请求能成功。"""
    names = names or {}
    for product_id, quantity in required.items():
        result = db.execute(
            update(Product)
            .where(
                Product.id == product_id,
                Product.on_sale.is_(True),
                Product.stock >= quantity,
            )
            .values(stock=Product.stock - quantity)
        )
        if (result.rowcount or 0) == 1:
            continue
        db.rollback()
        product = db.get(Product, product_id)
        if product is None or not product.on_sale:
            raise BizError(2001, f"{names.get(product_id, '商品')} 已下架", 400)
        raise BizError(2002, f"{names.get(product_id, product.name)} 库存不足", 409)


def _restore_stock(db: Session, order: Order) -> None:
    required, _ = _order_quantities(order)
    for product_id, quantity in required.items():
        db.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(stock=Product.stock + quantity)
        )


def _claim_order_state(
    db: Session,
    out_trade_no: str,
    from_states: tuple[str, ...],
    to_state: str,
    **values,
) -> bool:
    """用条件 UPDATE 抢占状态，避免取消/支付/核销并发重复执行。"""
    result = db.execute(
        update(Order)
        .where(
            Order.out_trade_no == out_trade_no,
            Order.state.in_(from_states),
        )
        .values(state=to_state, **values)
    )
    return (result.rowcount or 0) == 1


def _new_order_no(db: Session) -> str:
    stamp = now_ms()
    for _ in range(1000):
        order_no = f"CAT{stamp}{random.randint(100, 999)}"
        if db.get(Order, order_no) is None:
            return order_no
    return f"CAT{stamp}{random.randint(1000, 9999)}"


def _new_pick_code() -> str:
    return f"{random.randint(10, 99)}{now_ms() % 1000:03d}"


def get_idempotent(db: Session, user_id: int, key: str) -> str | None:
    row = db.get(IdempotencyKey, (user_id, key))
    if row is None:
        return None
    if row.expires_at <= now_ms() or db.get(Order, row.order_no) is None:
        db.delete(row)
        db.flush()
        return None
    return row.order_no


def create_order(
    db: Session,
    user: User,
    payload: dict,
    idempotency_key: str | None = None,
) -> Order:
    if idempotency_key:
        cached_no = get_idempotent(db, user.id, idempotency_key)
        if cached_no:
            cached = db.get(Order, cached_no)
            if cached is not None:
                return cached

    result = quote(db, user.id, payload)
    store = result["store"]

    table_no = _normalize_table_no(payload, store)
    address = _resolve_address(db, user, payload)

    required, names = _snapshot_quantities(result["items"])
    _deduct_stock(db, required, names)

    out_trade_no = _new_order_no(db)

    if result["coupon"] is not None:
        claim_for_order(db, result["coupon"], user.id, out_trade_no)

    order = Order(
        out_trade_no=out_trade_no,
        user_id=user.id,
        state="pending_pay",
        stock_reserved=True,
        store_id=store.id,
        store_name=store.name,
        mode=payload["mode"],
        subtotal=result["subtotal"],
        pack_fee=result["pack_fee"],
        coupon_id=result["coupon"].id if result["coupon"] is not None else None,
        coupon_cut=result["coupon_cut"],
        total=result["total"],
        pick_code=None,
        table_no=table_no,
        address_id=address.id if address is not None else None,
        address_name=address.name if address is not None else None,
        address_phone=address.phone if address is not None else None,
        address_detail=address.detail if address is not None else None,
        address_is_default=address.is_default if address is not None else None,
        remark=payload.get("remark", ""),
        create_time=now_ms(),
        earning_points=0,
    )

    for index, snapshot in enumerate(result["items"]):
        item = OrderItem(
            product_id=snapshot["product_id"],
            name=snapshot["name"],
            image_path=snapshot["image_path"],
            line_id=snapshot["line_id"],
            ice=snapshot["ice"],
            sugar=snapshot["sugar"],
            count=snapshot["count"],
            unit_price=snapshot["unit_price"],
            amount=snapshot["amount"],
            sort_order=index,
        )
        for topping_index, topping in enumerate(snapshot["toppings"]):
            item.toppings.append(
                OrderItemTopping(
                    topping_id=topping.id,
                    name=topping.name,
                    price=topping.price,
                    sort_order=topping_index,
                )
            )
        order.items.append(item)

    db.add(order)
    db.flush()
    if idempotency_key:
        db.add(
            IdempotencyKey(
                user_id=user.id,
                idem_key=idempotency_key,
                order_no=out_trade_no,
                expires_at=now_ms() + settings.idempotency_ttl * 1000,
            )
        )
    try:
        db.commit()
    except IntegrityError:
        # 同一幂等键被两个请求同时提交：让后到者返回先到者已经创建的订单。
        db.rollback()
        if idempotency_key:
            existing = db.get(IdempotencyKey, (user.id, idempotency_key))
            if existing is not None:
                existing_order = db.get(Order, existing.order_no)
                if existing_order is not None:
                    return existing_order
        raise
    return order


def cancel_order(db: Session, user: User, out_trade_no: str) -> Order:
    order = get_owned_order(db, user, out_trade_no, for_update=True)
    if order.state not in ("pending_pay", "making"):
        raise BizError(4001, "当前订单状态不可取消", 409)
    was_making = order.state == "making"

    if not _claim_order_state(
        db,
        out_trade_no,
        ("pending_pay", "making"),
        "cancelled",
    ):
        db.rollback()
        current = db.get(Order, out_trade_no)
        if current is not None and current.state == "cancelled":
            return current
        raise BizError(4001, "订单状态已变化，请刷新后重试", 409)

    order.state = "cancelled"

    # 新订单在创建时已预占库存；旧版 making 订单在支付时扣过库存。
    # 旧版 pending_pay 订单（stock_reserved=False）从未扣库存，不能回补。
    if order.stock_reserved or was_making:
        _restore_stock(db, order)

    release_for_order(db, order.coupon_id, order.out_trade_no)
    if was_making and order.earning_points:
        change_points(db, user, -order.earning_points, "订单取消，积分退回", "refund")
        order.earning_points = 0
    db.commit()
    return order


def pay_order(db: Session, out_trade_no: str, transaction_id: str | None = None) -> Order:
    order = db.scalar(
        select(Order).where(Order.out_trade_no == out_trade_no).with_for_update()
    )
    if order is None:
        raise BizError(1004, "订单不存在", 404)
    if order.state in ("making", "completed"):
        return order
    if order.state == "cancelled":
        raise BizError(4003, "订单已取消", 410)

    for item in order.items:
        product = db.get(Product, item.product_id)
        if product is None or not product.on_sale:
            raise BizError(2001, "订单中的商品已下架", 400)

    coupon = db.get(UserCoupon, order.coupon_id) if order.coupon_id else None

    pick_code = _new_pick_code()
    pay_time = now_ms()
    transaction_id = transaction_id or f"MOCK{pay_time}"

    if not _claim_order_state(
        db,
        out_trade_no,
        ("pending_pay",),
        "making",
        pick_code=pick_code,
        pay_time=pay_time,
        transaction_id=transaction_id,
    ):
        db.rollback()
        current = db.get(Order, out_trade_no)
        if current is not None and current.state in ("making", "completed"):
            return current
        if current is not None and current.state == "cancelled":
            raise BizError(4003, "订单已取消", 410)
        raise BizError(4001, "订单状态已变化，请刷新后重试", 409)

    order.state = "making"
    order.pick_code = pick_code
    order.pay_time = pay_time
    order.transaction_id = transaction_id

    if not order.stock_reserved:
        # 兼容旧订单：旧版创建订单不预占库存，支付时才扣减。
        required, names = _order_quantities(order)
        _deduct_stock(db, required, names)

    if coupon is not None:
        consume_for_order(db, coupon, out_trade_no)

    user = db.get(User, order.user_id)
    earned = int(order.total)
    if earned > 0:
        change_points(db, user, earned, f"下单奖励 +{earned}", "order")
    order.earning_points = earned

    db.commit()
    return order


def complete_order(db: Session, user: User, out_trade_no: str) -> Order:
    order = get_owned_order(db, user, out_trade_no, for_update=True)
    if order.state != "making":
        raise BizError(4001, "只有制作中的订单可以完成", 409)
    finish_time = now_ms()
    if not _claim_order_state(
        db,
        out_trade_no,
        ("making",),
        "completed",
        finish_time=finish_time,
    ):
        db.rollback()
        current = db.get(Order, out_trade_no)
        if current is not None and current.state == "completed":
            return current
        raise BizError(4001, "订单状态已变化，请刷新后重试", 409)
    order.state = "completed"
    order.finish_time = finish_time
    db.commit()
    return order


def review_order(db: Session, user: User, out_trade_no: str, rating: int, content: str) -> dict:
    order = get_owned_order(db, user, out_trade_no)
    if order.state != "completed":
        raise BizError(4001, "订单完成后才能评价", 409)
    if order.review_rating is not None:
        raise BizError(4001, "该订单已评价", 409)
    review = {"rating": rating, "content": content, "created_at": now_ms()}
    order.review_rating = rating
    order.review_content = content
    order.review_created_at = review["created_at"]
    db.commit()
    return review


def repeat_data(db: Session, user: User, out_trade_no: str) -> dict:
    order = get_owned_order(db, user, out_trade_no)
    store = db.get(Store, order.store_id)
    if store is None:
        raise BizError(1004, "门店已不存在", 404)

    address_id = None
    if order.mode == "delivery" and order.address_id:
        address = db.get(Address, order.address_id)
        if address is not None and address.user_id == user.id:
            address_id = address.id

    return {
        "store_id": order.store_id,
        "store_name": order.store_name,
        "mode": order.mode,
        "mode_text": MODE_TEXT[order.mode],
        "address_id": address_id,
        "remark": order.remark,
        "items": [
            {
                "product_id": item.product_id,
                "ice": item.ice,
                "sugar": item.sugar,
                "topping_ids": [topping.topping_id for topping in item.toppings],
                "count": item.count,
            }
            for item in order.items
        ],
    }


def counts(db: Session, user: User) -> dict:
    rows = db.execute(
        select(Order.state, func.count())
        .where(Order.user_id == user.id)
        .group_by(Order.state)
    ).all()
    result = {state: 0 for state in STATE_TEXT}
    for state, count in rows:
        if state in result:
            result[state] = count
    return result


def expire_pending_orders(db: Session, timeout_minutes: int | None = None) -> int:
    """取消超时未支付订单并释放预占库存和优惠券。"""
    minutes = settings.order_expiry_minutes if timeout_minutes is None else timeout_minutes
    if minutes <= 0:
        return 0
    cutoff = now_ms() - minutes * 60 * 1000
    orders = db.scalars(
        select(Order).where(
            Order.state == "pending_pay",
            Order.create_time < cutoff,
        )
    ).all()
    expired = 0
    for order in orders:
        if not _claim_order_state(
            db,
            order.out_trade_no,
            ("pending_pay",),
            "cancelled",
        ):
            continue
        order.state = "cancelled"
        if order.stock_reserved:
            _restore_stock(db, order)
        release_for_order(db, order.coupon_id, order.out_trade_no)
        expired += 1
    db.commit()
    return expired
