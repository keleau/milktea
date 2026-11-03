from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.response import ApiResponse, BizError, ok
from app.db import get_db
from app.deps import get_current_user
from app.models import CouponTemplate, ExchangeItem, PointsLog, User
from app.schemas import (
    ExchangeData,
    ExchangeIn,
    ExchangeItemOut,
    ListData,
    MemberProfileOut,
    PageData,
    PointsLogOut,
)
from app.serializers import (
    money,
    serialize_coupon,
    serialize_exchange_item,
    serialize_points_log,
)
from app.services.coupons import add_coupon, count_unused
from app.services.member import change_points, level_text, levels

router = APIRouter(prefix="/member", tags=["会员"])


@router.get("/profile", response_model=ApiResponse[MemberProfileOut], summary="会员等级、积分、余额、成长值")
def profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    growth = user.growth or 0
    all_levels = levels(db)
    index = 0
    for position, level in enumerate(all_levels):
        if growth >= level.min_points:
            index = position

    current = all_levels[index]
    if index + 1 < len(all_levels):
        following = all_levels[index + 1]
        span = following.min_points - current.min_points
        progress = round((growth - current.min_points) / span, 2) if span else 1.0
        next_level = level_text(following)
        next_threshold = following.min_points
    else:
        next_level, next_threshold, progress = None, None, 1.0

    coupon_count = count_unused(db, user.id)
    db.commit()
    return ok(
        {
            "level": level_text(current),
            "points": user.points,
            "balance": money(user.balance),
            "growth": growth,
            "next_level": next_level,
            "next_level_growth": next_threshold,
            "progress": progress,
            "coupon_count": coupon_count,
        }
    )


@router.get("/points/logs", response_model=ApiResponse[PageData[PointsLogOut]], summary="积分明细")
def points_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = (
        db.scalar(
            select(func.count()).select_from(PointsLog).where(PointsLog.user_id == user.id)
        )
        or 0
    )
    logs = db.scalars(
        select(PointsLog)
        .where(PointsLog.user_id == user.id)
        .order_by(PointsLog.created_at.desc(), PointsLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return ok(
        {
            "items": [serialize_points_log(log) for log in logs],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/points/items", response_model=ApiResponse[ListData[ExchangeItemOut]], summary="积分兑换商品")
def exchange_items(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.scalars(
        select(ExchangeItem).order_by(ExchangeItem.sort_order, ExchangeItem.id)
    ).all()
    return ok({"items": [serialize_exchange_item(item) for item in items]})


@router.post("/points/exchange", response_model=ApiResponse[ExchangeData], summary="积分兑换")
def exchange(
    payload: ExchangeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.get(ExchangeItem, payload.item_id)
    if item is None:
        raise BizError(1004, "兑换商品不存在", 404)
    if user.points < item.cost:
        raise BizError(6001, "积分不足", 400)

    coupon = None
    if item.item_type == "coupon":
        template = db.get(CouponTemplate, item.template_id) if item.template_id else None
        if template is None:
            raise BizError(1004, "优惠券模板不存在", 404)
        coupon = add_coupon(db, user.id, template)

    points = change_points(db, user, -item.cost, f"积分兑换：{item.title}", "exchange")
    db.commit()
    return ok(
        {
            "points": points,
            "coupon": serialize_coupon(coupon) if coupon is not None else None,
            "message": "兑换成功",
        }
    )
