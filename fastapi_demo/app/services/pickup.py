"""店员取餐核销。

演示版用 .env 里的 STAFF_PIN 做店员口令；真实系统应改为店员账号 + 角色权限。
"""

import hmac

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.constants import now_ms
from app.core.config import settings
from app.core.response import BizError
from app.models import Order

CODE_PREFIX = "PICK"


def _check_pin(pin: str) -> None:
    expected = settings.staff_pin
    if not expected:
        raise BizError(9000, "核销功能未配置，请在后端 .env 设置 STAFF_PIN", 503)
    if not hmac.compare_digest(pin, expected):
        raise BizError(1003, "店员口令不正确", 403)


def _find_order(db: Session, code: str) -> Order:
    raw = code.strip()
    if raw.upper().startswith(f"{CODE_PREFIX}:"):
        parts = raw.split(":")
        if len(parts) != 3 or not parts[1] or not parts[2]:
            raise BizError(1001, "取餐码格式不正确", 400)
        order = db.get(Order, parts[1])
        if order is None or order.pick_code != parts[2]:
            raise BizError(1004, "订单不存在或取餐码不匹配", 404)
        return order

    if not raw:
        raise BizError(1001, "请输入取餐码", 400)
    orders = list(db.scalars(select(Order).where(Order.pick_code == raw)).all())
    if not orders:
        raise BizError(1004, "没有找到该取餐码", 404)
    if len(orders) > 1:
        raise BizError(4001, "取餐码重复，请扫描顾客的二维码", 409)
    return orders[0]


def _ensure_making(order: Order) -> None:
    if order.state == "making":
        return
    if order.state == "completed":
        raise BizError(4001, "该订单已核销", 409)
    if order.state == "cancelled":
        raise BizError(4001, "该订单已取消", 409)
    raise BizError(4001, "订单还未支付，不能核销", 409)


def lookup_pickup(db: Session, code: str, pin: str) -> Order:
    _check_pin(pin)
    order = _find_order(db, code)
    _ensure_making(order)
    return order


def complete_pickup(db: Session, code: str, pin: str) -> Order:
    _check_pin(pin)
    order = _find_order(db, code)
    _ensure_making(order)
    finish_time = now_ms()
    result = db.execute(
        update(Order)
        .where(
            Order.out_trade_no == order.out_trade_no,
            Order.state == "making",
        )
        .values(state="completed", finish_time=finish_time)
    )
    if (result.rowcount or 0) != 1:
        db.rollback()
        current = db.get(Order, order.out_trade_no)
        if current is not None and current.state == "completed":
            return current
        raise BizError(4001, "订单状态已变化，请刷新后重试", 409)
    order.state = "completed"
    order.finish_time = finish_time
    db.commit()
    return order
