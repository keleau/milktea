import app.data as db
from app.core.response import BizError


def normalize_item(raw: dict) -> dict:
    product = db.PRODUCTS_BY_ID.get(raw["product_id"])
    if product is None:
        raise BizError(1004, "商品不存在", 404)
    if not product["on_sale"]:
        raise BizError(2001, "商品已下架", 400)
    if raw["ice"] not in db.ICE_OPTIONS:
        raise BizError(1001, "冰度选项不正确", 400)
    if raw["sugar"] not in db.SUGAR_OPTIONS:
        raise BizError(1001, "糖度选项不正确", 400)

    toppings = []
    for topping_id in dict.fromkeys(raw.get("topping_ids", [])):
        topping = db.TOPPINGS_BY_ID.get(topping_id)
        if topping is None:
            raise BizError(1001, f"小料 {topping_id} 不存在", 400)
        toppings.append(topping)

    count = raw["count"]
    unit_price = round(product["price"] + sum(t["price"] for t in toppings), 2)
    return {
        "product_id": product["id"],
        "name": product["name"],
        "image": product["image"],
        "line_id": product["line_id"],
        "ice": raw["ice"],
        "sugar": raw["sugar"],
        "topping_ids": [t["id"] for t in toppings],
        "topping_names": "+".join(t["name"] for t in toppings),
        "count": count,
        "unit_price": unit_price,
        "amount": round(unit_price * count, 2),
    }


def validate_coupon(user_id: int, coupon_id: int, subtotal: float) -> dict:
    coupon = db.COUPONS.get(coupon_id)
    if coupon is None or coupon["user_id"] != user_id:
        raise BizError(3001, "优惠券不存在或不可用", 400)
    db.refresh_coupon_status(coupon)
    if coupon["status"] == "used":
        raise BizError(3002, "优惠券已使用", 409)
    if coupon["status"] == "expired":
        raise BizError(3002, "优惠券已过期", 409)
    if coupon["locked_by"]:
        raise BizError(3004, "优惠券已被其他订单占用", 409)
    if subtotal < coupon["min_amount"]:
        raise BizError(3001, f"还差 ¥{round(coupon['min_amount'] - subtotal, 2)} 可用", 400)
    return coupon


def usable_coupons(user_id: int, subtotal: float) -> list[dict]:
    result = []
    for coupon in db.user_coupons(user_id):
        if (
            coupon["status"] == "unused"
            and not coupon["locked_by"]
            and subtotal >= coupon["min_amount"]
        ):
            result.append(coupon)
    return sorted(result, key=lambda c: c["cut"], reverse=True)


def pack_fee_for(store: dict, mode: str) -> float:
    return store["pack_fee"] if mode == "pickup" else store["delivery_fee"]


def estimated_ready_minutes(store: dict) -> int:
    return 8 + store["making_cups"] // 5


def quote(user_id: int | None, payload: dict) -> dict:
    store = db.STORES_BY_ID.get(payload["store_id"])
    if store is None:
        raise BizError(1004, "门店不存在", 404)
    if store["status"] == "closed":
        raise BizError(2004, "门店已打烊", 409)

    snapshots = [normalize_item(item) for item in payload["items"]]
    required: dict[int, int] = {}
    for snapshot in snapshots:
        required[snapshot["product_id"]] = required.get(snapshot["product_id"], 0) + snapshot["count"]
    for product_id, quantity in required.items():
        product = db.PRODUCTS_BY_ID[product_id]
        if product["stock"] < quantity:
            raise BizError(2002, f"{product['name']} 库存不足", 409)

    subtotal = round(sum(snapshot["amount"] for snapshot in snapshots), 2)
    pack_fee = pack_fee_for(store, payload["mode"])

    coupon = None
    coupon_cut = 0.0
    if payload.get("coupon_id"):
        if user_id is None:
            raise BizError(1002, "使用优惠券需要先登录", 401)
        coupon = validate_coupon(user_id, payload["coupon_id"], subtotal)
        coupon_cut = coupon["cut"]

    total = max(0.0, round(subtotal + pack_fee - coupon_cut, 2))
    return {
        "store": store,
        "items": snapshots,
        "subtotal": subtotal,
        "pack_fee": pack_fee,
        "coupon": coupon,
        "coupon_cut": coupon_cut,
        "total": total,
    }
