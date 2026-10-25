import random

from sqlalchemy import func, select
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
from app.services.coupons import refresh_status
from app.services.member import change_points
from app.services.pricing import quote


def get_owned_order(db: Session, user: User, out_trade_no: str) -> Order:
    order = db.get(Order, out_trade_no)
    if order is None:
        raise BizError(1004, "订单不存在", 404)
    if order.user_id != user.id:
        raise BizError(1003, "无权操作该订单", 403)
    return order


def _set_state(order: Order, state: str) -> None:
    order.state = state


def _release_coupon(db: Session, order: Order) -> None:
    if not order.coupon_id:
        return
    coupon = db.get(UserCoupon, order.coupon_id)
    if coupon is None:
        return
    if coupon.locked_by == order.out_trade_no:
        coupon.locked_by = None
    if coupon.status == "used":
        coupon.status = "unused"
    refresh_status(coupon)


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
        db.commit()
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

    address = None
    if payload["mode"] == "delivery":
        address_id = payload.get("address_id")
        if not address_id:
            raise BizError(1001, "外送订单需要选择收货地址", 400)
        address = db.get(Address, address_id)
        if address is None or address.user_id != user.id:
            raise BizError(1004, "收货地址不存在", 404)

    out_trade_no = _new_order_no(db)
    order = Order(
        out_trade_no=out_trade_no,
        user_id=user.id,
        state="pending_pay",
        store_id=store.id,
        store_name=store.name,
        mode=payload["mode"],
        subtotal=result["subtotal"],
        pack_fee=result["pack_fee"],
        coupon_id=result["coupon"].id if result["coupon"] is not None else None,
        coupon_cut=result["coupon_cut"],
        total=result["total"],
        pick_code=None,
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

    if result["coupon"] is not None:
        result["coupon"].locked_by = out_trade_no

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
    db.commit()
    return order


def cancel_order(db: Session, user: User, out_trade_no: str) -> Order:
    order = get_owned_order(db, user, out_trade_no)
    if order.state not in ("pending_pay", "making"):
        raise BizError(4001, "当前订单状态不可取消", 409)

    if order.state == "making":
        for item in order.items:
            product = db.get(Product, item.product_id)
            if product is not None:
                product.stock += item.count
        _release_coupon(db, order)
        if order.earning_points:
            change_points(db, user, -order.earning_points, "订单取消，积分退回", "refund")
            order.earning_points = 0
    else:
        _release_coupon(db, order)

    _set_state(order, "cancelled")
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

    products: dict[int, Product] = {}
    for item in order.items:
        product = db.get(Product, item.product_id)
        if product is None or not product.on_sale:
            raise BizError(2001, "订单中的商品已下架", 400)
        if product.stock < item.count:
            raise BizError(2002, f"{product.name} 库存不足", 409)
        products[product.id] = product

    if order.coupon_id:
        coupon = db.get(UserCoupon, order.coupon_id)
        if coupon is not None:
            if coupon.locked_by not in (None, out_trade_no):
                raise BizError(3004, "优惠券已被其他订单占用", 409)
            refresh_status(coupon)
            if coupon.status == "used":
                raise BizError(3002, "优惠券已使用", 409)
            if coupon.status == "expired":
                raise BizError(3002, "优惠券已过期", 409)
            coupon.status = "used"
            coupon.locked_by = None

    for item in order.items:
        products[item.product_id].stock -= item.count

    user = db.get(User, order.user_id)
    earned = int(order.total)
    if earned > 0:
        change_points(db, user, earned, f"下单奖励 +{earned}", "order")
    order.earning_points = earned

    order.pick_code = _new_pick_code()
    order.pay_time = now_ms()
    order.transaction_id = transaction_id or f"MOCK{now_ms()}"
    _set_state(order, "making")
    db.commit()
    return order


def complete_order(db: Session, user: User, out_trade_no: str) -> Order:
    order = get_owned_order(db, user, out_trade_no)
    if order.state != "making":
        raise BizError(4001, "只有制作中的订单可以完成", 409)
    order.finish_time = now_ms()
    _set_state(order, "completed")
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
