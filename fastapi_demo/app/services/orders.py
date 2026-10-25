import app.data as db
from app.core.response import BizError
from app.services.pricing import quote

STATE_TEXT = {
    "pending_pay": "待支付",
    "making": "制作中",
    "completed": "已完成",
    "cancelled": "已取消",
}
MODE_TEXT = {"pickup": "自取", "delivery": "外送"}


def get_owned_order(user: dict, out_trade_no: str) -> dict:
    order = db.ORDERS.get(out_trade_no)
    if order is None:
        raise BizError(1004, "订单不存在", 404)
    if order["user_id"] != user["id"]:
        raise BizError(1003, "无权操作该订单", 403)
    return order


def _set_state(order: dict, state: str) -> None:
    order["state"] = state
    order["state_text"] = STATE_TEXT[state]


def _release_coupon(order: dict) -> None:
    coupon_id = order.get("coupon_id")
    if not coupon_id:
        return
    coupon = db.COUPONS.get(coupon_id)
    if coupon is None:
        return
    if coupon["locked_by"] == order["out_trade_no"]:
        coupon["locked_by"] = None
    # 已支付订单取消时券已被核销，需退回；券已过期则保持过期
    if coupon["status"] == "used":
        coupon["status"] = "unused"
    db.refresh_coupon_status(coupon)


def create_order(user: dict, payload: dict, idempotency_key: str | None = None) -> dict:
    if idempotency_key:
        cached_no = db.get_idempotent(user["id"], idempotency_key)
        if cached_no:
            return db.ORDERS[cached_no]

    result = quote(user["id"], payload)
    store = result["store"]

    address = None
    if payload["mode"] == "delivery":
        address_id = payload.get("address_id")
        if not address_id:
            raise BizError(1001, "外送订单需要选择收货地址", 400)
        address = db.ADDRESSES.get(address_id)
        if address is None or address["user_id"] != user["id"]:
            raise BizError(1004, "收货地址不存在", 404)
        address = {k: v for k, v in address.items() if k != "user_id"}

    out_trade_no = db.new_order_no()
    order = {
        "out_trade_no": out_trade_no,
        "user_id": user["id"],
        "state": "pending_pay",
        "state_text": STATE_TEXT["pending_pay"],
        "store_id": store["id"],
        "store_name": store["name"],
        "mode": payload["mode"],
        "mode_text": MODE_TEXT[payload["mode"]],
        "items": result["items"],
        "subtotal": result["subtotal"],
        "pack_fee": result["pack_fee"],
        "coupon_id": result["coupon"]["id"] if result["coupon"] else None,
        "coupon_cut": result["coupon_cut"],
        "total": result["total"],
        "pick_code": None,
        "address": address,
        "remark": payload.get("remark", ""),
        "create_time": db.now_ms(),
        "pay_time": None,
        "finish_time": None,
        "review": None,
        "earning_points": 0,
        "transaction_id": None,
    }

    if result["coupon"] is not None:
        result["coupon"]["locked_by"] = out_trade_no

    db.ORDERS[out_trade_no] = order
    if idempotency_key:
        db.set_idempotent(user["id"], idempotency_key, out_trade_no)
    return order


def cancel_order(user: dict, out_trade_no: str) -> dict:
    order = get_owned_order(user, out_trade_no)
    if order["state"] not in ("pending_pay", "making"):
        raise BizError(4001, "当前订单状态不可取消", 409)

    if order["state"] == "making":
        for item in order["items"]:
            product = db.PRODUCTS_BY_ID.get(item["product_id"])
            if product is not None:
                product["stock"] += item["count"]
        _release_coupon(order)
        if order["earning_points"]:
            db.change_points(user, -order["earning_points"], "订单取消，积分退回", "refund")
            order["earning_points"] = 0
    else:
        _release_coupon(order)

    _set_state(order, "cancelled")
    return order


def pay_order(out_trade_no: str, transaction_id: str | None = None) -> dict:
    order = db.ORDERS.get(out_trade_no)
    if order is None:
        raise BizError(1004, "订单不存在", 404)
    if order["state"] in ("making", "completed"):
        return order
    if order["state"] == "cancelled":
        raise BizError(4003, "订单已取消", 410)

    for item in order["items"]:
        product = db.PRODUCTS_BY_ID.get(item["product_id"])
        if product is None or not product["on_sale"]:
            raise BizError(2001, "订单中的商品已下架", 400)
        if product["stock"] < item["count"]:
            raise BizError(2002, f"{product['name']} 库存不足", 409)

    coupon_id = order.get("coupon_id")
    if coupon_id:
        coupon = db.COUPONS.get(coupon_id)
        if coupon is not None:
            if coupon["locked_by"] not in (None, out_trade_no):
                raise BizError(3004, "优惠券已被其他订单占用", 409)
            db.refresh_coupon_status(coupon)
            if coupon["status"] == "used":
                raise BizError(3002, "优惠券已使用", 409)
            if coupon["status"] == "expired":
                raise BizError(3002, "优惠券已过期", 409)
            coupon["status"] = "used"
            coupon["locked_by"] = None

    for item in order["items"]:
        db.PRODUCTS_BY_ID[item["product_id"]]["stock"] -= item["count"]

    user = db.USERS[order["user_id"]]
    earned = int(order["total"])
    if earned > 0:
        db.change_points(user, earned, f"下单奖励 +{earned}", "order")
    order["earning_points"] = earned

    order["pick_code"] = db.new_pick_code()
    order["pay_time"] = db.now_ms()
    order["transaction_id"] = transaction_id or f"MOCK{db.now_ms()}"
    _set_state(order, "making")
    return order


def complete_order(user: dict, out_trade_no: str) -> dict:
    order = get_owned_order(user, out_trade_no)
    if order["state"] != "making":
        raise BizError(4001, "只有制作中的订单可以完成", 409)
    order["finish_time"] = db.now_ms()
    _set_state(order, "completed")
    return order


def review_order(user: dict, out_trade_no: str, rating: int, content: str) -> dict:
    order = get_owned_order(user, out_trade_no)
    if order["state"] != "completed":
        raise BizError(4001, "订单完成后才能评价", 409)
    if order["review"] is not None:
        raise BizError(4001, "该订单已评价", 409)
    order["review"] = {"rating": rating, "content": content, "created_at": db.now_ms()}
    return order["review"]


def repeat_data(user: dict, out_trade_no: str) -> dict:
    order = get_owned_order(user, out_trade_no)
    store = db.STORES_BY_ID.get(order["store_id"])
    if store is None:
        raise BizError(1004, "门店已不存在", 404)
    address_id = None
    if order["mode"] == "delivery" and order["address"]:
        address = db.ADDRESSES.get(order["address"]["id"])
        if address is not None and address["user_id"] == user["id"]:
            address_id = address["id"]
    return {
        "store_id": order["store_id"],
        "store_name": order["store_name"],
        "mode": order["mode"],
        "mode_text": order["mode_text"],
        "address_id": address_id,
        "remark": order.get("remark", ""),
        "items": [
            {
                "product_id": item["product_id"],
                "ice": item["ice"],
                "sugar": item["sugar"],
                "topping_ids": item["topping_ids"],
                "count": item["count"],
            }
            for item in order["items"]
        ],
    }


def counts(user: dict) -> dict:
    result = {state: 0 for state in STATE_TEXT}
    for order in db.ORDERS.values():
        if order["user_id"] == user["id"] and order["state"] in result:
            result[order["state"]] += 1
    return result
