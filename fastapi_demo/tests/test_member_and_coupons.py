from sqlalchemy import select

from app.constants import now_ms
from app.models import PointsLog, User, UserCoupon
from app.services.coupons import count_unused
from app.services.member import change_points


def test_change_points_clamps_and_logs_actual_delta(db):
    user = db.get(User, 1001)
    user.points = 1
    db.commit()

    change_points(db, user, -5, "测试退款", "refund")
    db.commit()

    assert user.points == 0
    log = db.scalars(
        select(PointsLog).where(PointsLog.user_id == 1001, PointsLog.type == "refund")
    ).one()
    assert log.points == -1


def test_count_unused_excludes_expired_coupons(db):
    coupon = db.get(UserCoupon, 501)
    coupon.expire_at = now_ms() - 1
    db.commit()

    assert count_unused(db, 1001) == 1

    db.expire_all()
    assert db.get(UserCoupon, 501).status == "unused"
