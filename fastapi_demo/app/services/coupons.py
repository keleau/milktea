from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import DAY_MS, now_ms
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
    coupons = db.scalars(
        select(UserCoupon).where(
            UserCoupon.user_id == user_id,
            UserCoupon.status == "unused",
        )
    ).all()
    return sum(1 for coupon in coupons if refresh_status(coupon).status == "unused")


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
