from decimal import Decimal

from sqlalchemy.orm import Session

from app.constants import ICE_OPTIONS, SUGAR_OPTIONS
from app.core.response import BizError
from app.models import Product, Store, Topping, UserCoupon
from app.services.coupons import list_for_user, refresh_status

CENT = Decimal("0.01")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(CENT)


def normalize_item(db: Session, raw: dict) -> dict:
    product = db.get(Product, raw["product_id"])
    if product is None:
        raise BizError(1004, "商品不存在", 404)
    if not product.on_sale:
        raise BizError(2001, "商品已下架", 400)
    if raw["ice"] not in ICE_OPTIONS:
        raise BizError(1001, "冰度选项不正确", 400)
    if raw["sugar"] not in SUGAR_OPTIONS:
        raise BizError(1001, "糖度选项不正确", 400)

    toppings: list[Topping] = []
    for topping_id in dict.fromkeys(raw.get("topping_ids", [])):
        topping = db.get(Topping, topping_id)
        if topping is None:
            raise BizError(1001, f"小料 {topping_id} 不存在", 400)
        toppings.append(topping)

    count = raw["count"]
    unit_price = _quantize(product.price + sum((topping.price for topping in toppings), Decimal("0")))
    return {
        "product": product,
        "product_id": product.id,
        "name": product.name,
        "image_path": product.image_path,
        "line_id": product.line_id,
        "ice": raw["ice"],
        "sugar": raw["sugar"],
        "toppings": toppings,
        "count": count,
        "unit_price": unit_price,
        "amount": _quantize(unit_price * count),
    }


def validate_coupon(db: Session, user_id: int, coupon_id: int, subtotal: Decimal) -> UserCoupon:
    coupon = db.get(UserCoupon, coupon_id)
    if coupon is None or coupon.user_id != user_id:
        raise BizError(3001, "优惠券不存在或不可用", 400)
    refresh_status(coupon)
    if coupon.status == "used":
        raise BizError(3002, "优惠券已使用", 409)
    if coupon.status == "expired":
        raise BizError(3002, "优惠券已过期", 409)
    if coupon.locked_by:
        raise BizError(3004, "优惠券已被其他订单占用", 409)
    if subtotal < coupon.min_amount:
        gap = _quantize(coupon.min_amount - subtotal)
        raise BizError(3001, f"还差 ¥{gap} 可用", 400)
    return coupon


def usable_coupons(db: Session, user_id: int, subtotal: Decimal) -> list[UserCoupon]:
    result = [
        coupon
        for coupon in list_for_user(db, user_id)
        if coupon.status == "unused"
        and not coupon.locked_by
        and subtotal >= coupon.min_amount
    ]
    return sorted(result, key=lambda coupon: coupon.cut, reverse=True)


def pack_fee_for(store: Store, mode: str) -> Decimal:
    return store.pack_fee if mode == "pickup" else store.delivery_fee


def estimated_ready_minutes(store: Store) -> int:
    return 8 + store.making_cups // 5


def quote(db: Session, user_id: int | None, payload: dict) -> dict:
    store = db.get(Store, payload["store_id"])
    if store is None:
        raise BizError(1004, "门店不存在", 404)
    if store.status == "closed":
        raise BizError(2004, "门店已打烊", 409)

    snapshots = [normalize_item(db, item) for item in payload["items"]]

    required: dict[int, int] = {}
    for snapshot in snapshots:
        required[snapshot["product_id"]] = (
            required.get(snapshot["product_id"], 0) + snapshot["count"]
        )
    for product_id, quantity in required.items():
        product = db.get(Product, product_id)
        if product.stock < quantity:
            raise BizError(2002, f"{product.name} 库存不足", 409)

    subtotal = _quantize(sum((snapshot["amount"] for snapshot in snapshots), Decimal("0")))
    pack_fee = pack_fee_for(store, payload["mode"])

    coupon = None
    coupon_cut = Decimal("0.00")
    if payload.get("coupon_id"):
        if user_id is None:
            raise BizError(1002, "使用优惠券需要先登录", 401)
        coupon = validate_coupon(db, user_id, payload["coupon_id"], subtotal)
        coupon_cut = coupon.cut

    total = max(Decimal("0.00"), _quantize(subtotal + pack_fee - coupon_cut))
    return {
        "store": store,
        "items": snapshots,
        "subtotal": subtotal,
        "pack_fee": pack_fee,
        "coupon": coupon,
        "coupon_cut": coupon_cut,
        "total": total,
    }
