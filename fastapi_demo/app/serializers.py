from decimal import Decimal

from app.constants import MODE_TEXT, STATE_TEXT
from app.core.config import settings
from app.models import (
    Address,
    CouponTemplate,
    ExchangeItem,
    Order,
    OrderItem,
    PointsLog,
    Product,
    ProductLine,
    Store,
    Topping,
    User,
    UserCoupon,
)


def money(value: Decimal | int | float | None) -> float:
    return float(value or 0)


def asset_url(path: str | None) -> str:
    if not path:
        return ""
    if path.startswith(("http://", "https://")):
        return path
    if path.startswith("/"):
        return f"{settings.base_url}{path}"
    return f"{settings.image_url}/{path}"


def serialize_line(line: ProductLine) -> dict:
    return {
        "id": line.id,
        "name": line.name,
        "tag": line.tag,
        "en": line.en,
        "desc": line.description,
        "color": line.color,
        "bg": line.bg,
    }


def serialize_product(product: Product) -> dict:
    return {
        "id": product.id,
        "line_id": product.line_id,
        "name": product.name,
        "price": money(product.price),
        "orig_price": money(product.orig_price) if product.orig_price is not None else None,
        "paws": product.paws,
        "is_hot": product.is_hot,
        "is_new": product.is_new,
        "desc": product.description,
        "image": asset_url(product.image_path),
        "stock": product.stock,
        "on_sale": product.on_sale,
    }


def serialize_topping(topping: Topping) -> dict:
    return {"id": topping.id, "name": topping.name, "price": money(topping.price)}


def serialize_store(store: Store) -> dict:
    return {
        "id": store.id,
        "name": store.name,
        "area": store.area,
        "address": store.address,
        "lat": store.lat,
        "lng": store.lng,
        "distance": store.distance,
        "status": store.status,
        "business_hours": store.business_hours,
        "making_cups": store.making_cups,
        "pack_fee": money(store.pack_fee),
        "delivery_fee": money(store.delivery_fee),
    }


def serialize_user(user: User, coupon_count: int) -> dict:
    level = user.level
    level_text = f"{level.code} {level.name}" if level is not None else user.level_code
    return {
        "id": user.id,
        "nickname": user.nickname,
        "avatar": asset_url(user.avatar_path),
        "level": level_text,
        "points": user.points,
        "balance": money(user.balance),
        "coupon_count": coupon_count,
        "created_at": user.created_at,
    }


def serialize_coupon(coupon: UserCoupon) -> dict:
    return {
        "id": coupon.id,
        "template_id": coupon.template_id,
        "title": coupon.title,
        "desc": coupon.description,
        "cut": money(coupon.cut),
        "min_amount": money(coupon.min_amount),
        "status": coupon.status,
        "expire_at": coupon.expire_at,
    }


def serialize_template(template: CouponTemplate, claimed: bool = False) -> dict:
    return {
        "id": template.id,
        "title": template.title,
        "desc": template.description,
        "cut": money(template.cut),
        "min_amount": money(template.min_amount),
        "valid_days": template.valid_days,
        "claimed": claimed,
    }


def serialize_address(address: Address) -> dict:
    return {
        "id": address.id,
        "name": address.name,
        "phone": address.phone,
        "detail": address.detail,
        "is_default": address.is_default,
    }


def serialize_order_item(item: OrderItem) -> dict:
    toppings = sorted(item.toppings, key=lambda topping: topping.sort_order)
    return {
        "product_id": item.product_id,
        "name": item.name,
        "image": asset_url(item.image_path),
        "line_id": item.line_id,
        "ice": item.ice,
        "sugar": item.sugar,
        "topping_ids": [topping.topping_id for topping in toppings],
        "topping_names": "+".join(topping.name for topping in toppings),
        "count": item.count,
        "unit_price": money(item.unit_price),
        "amount": money(item.amount),
    }


def _serialize_review(order: Order) -> dict | None:
    if order.review_rating is None:
        return None
    return {
        "rating": order.review_rating,
        "content": order.review_content or "",
        "created_at": order.review_created_at,
    }


def serialize_order(order: Order) -> dict:
    address = None
    if order.address_name is not None:
        address = {
            "id": order.address_id,
            "name": order.address_name,
            "phone": order.address_phone,
            "detail": order.address_detail,
            "is_default": bool(order.address_is_default),
        }
    return {
        "out_trade_no": order.out_trade_no,
        "state": order.state,
        "state_text": STATE_TEXT[order.state],
        "store_id": order.store_id,
        "store_name": order.store_name,
        "mode": order.mode,
        "mode_text": MODE_TEXT[order.mode],
        "items": [serialize_order_item(item) for item in order.items],
        "subtotal": money(order.subtotal),
        "pack_fee": money(order.pack_fee),
        "coupon_cut": money(order.coupon_cut),
        "total": money(order.total),
        "pick_code": order.pick_code,
        "table_no": order.table_no,
        "address": address,
        "remark": order.remark,
        "create_time": order.create_time,
        "pay_time": order.pay_time,
        "finish_time": order.finish_time,
        "review": _serialize_review(order),
    }


def serialize_points_log(log: PointsLog) -> dict:
    return {
        "id": log.id,
        "title": log.title,
        "points": log.points,
        "type": log.type,
        "created_at": log.created_at,
    }


def serialize_exchange_item(item: ExchangeItem) -> dict:
    return {"id": item.id, "title": item.title, "cost": item.cost, "type": item.item_type}
