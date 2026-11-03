from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.constants import DAY_MS, now_ms
from app.core.response import BizError
from app.models import CouponTemplate, UserCoupon


def refresh_status(coupon: UserCoupon) -> UserCoupon:
    if coupon.status == "unused" and coupon.expire_at <= now_ms():
        coupon.status = "expired"
    return coupon


def list_for_user(db: Session, user_id: int) -> list[UserCoupon]:
    coupons = db.scalars(
        select(UserCoupon).where(UserCoupon.user_id == user_id).order_by(UserCoupon.id)
    ).all()
    for coupon in coupons:
        refresh_status(coupon)
    return list(coupons)


def count_unused(db: Session, user_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(UserCoupon)
            .where(
                UserCoupon.user_id == user_id,
                UserCoupon.status == "unused",
                UserCoupon.expire_at > now_ms(),
            )
        )
        or 0
    )


def claim_for_order(db: Session, coupon: UserCoupon, user_id: int, order_no: str) -> UserCoupon:
    """把券锁到订单上；条件 UPDATE 保证并发下同一张券只会被一个订单占用。"""
    claimed = db.execute(
        update(UserCoupon)
        .where(
            UserCoupon.id == coupon.id,
            UserCoupon.user_id == user_id,
            UserCoupon.status == "unused",
            UserCoupon.locked_by.is_(None),
            UserCoupon.expire_at > now_ms(),
        )
        .values(locked_by=order_no)
    )
    if (claimed.rowcount or 0) != 1:
        db.rollback()
        fresh = db.get(UserCoupon, coupon.id)
        if fresh is None:
            raise BizError(3001, "优惠券不存在或不可用", 400)
        refresh_status(fresh)
        if fresh.status == "used":
            raise BizError(3002, "优惠券已使用", 409)
        if fresh.status == "expired":
            raise BizError(3002, "优惠券已过期", 409)
        raise BizError(3004, "优惠券已被其他订单占用", 409)
    coupon.locked_by = order_no
    return coupon


def consume_for_order(db: Session, coupon: UserCoupon, order_no: str) -> UserCoupon:
    """支付成功时把券置为已使用；重复回调或并发支付只会有一次成功。"""
    used = db.execute(
        update(UserCoupon)
        .where(
            UserCoupon.id == coupon.id,
            UserCoupon.status == "unused",
            (UserCoupon.locked_by.is_(None)) | (UserCoupon.locked_by == order_no),
        )
        .values(status="used", locked_by=None)
    )
    if (used.rowcount or 0) != 1:
        db.rollback()
        refresh_status(coupon)
        if coupon.status == "used":
            raise BizError(3002, "优惠券已使用", 409)
        if coupon.status == "expired":
            raise BizError(3002, "优惠券已过期", 409)
        raise BizError(3004, "优惠券已被其他订单占用", 409)
    coupon.status = "used"
    coupon.locked_by = None
    return coupon


def release_for_order(db: Session, coupon_id: int | None, order_no: str) -> None:
    """取消/超时时释放券：只清掉本订单的锁，已使用的券恢复为未使用。"""
    if not coupon_id:
        return
    coupon = db.get(UserCoupon, coupon_id)
    if coupon is None:
        return
    if coupon.locked_by == order_no:
        coupon.locked_by = None
    if coupon.status == "used":
        coupon.status = "unused"
    refresh_status(coupon)


def add_coupon(
    db: Session,
    user_id: int,
    template: CouponTemplate,
    expire_at: int | None = None,
) -> UserCoupon:
    coupon = UserCoupon(
        user_id=user_id,
        template_id=template.id,
        title=template.title,
        description=template.description,
        cut=template.cut,
        min_amount=template.min_amount,
        status="unused",
        expire_at=expire_at if expire_at is not None else now_ms() + template.valid_days * DAY_MS,
        locked_by=None,
        created_at=now_ms(),
    )
    db.add(coupon)
    db.flush()
    return coupon
