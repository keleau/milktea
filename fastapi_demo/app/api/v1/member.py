from fastapi import APIRouter, Depends, Query

import app.data as db
from app.core.response import ApiResponse, BizError, ok
from app.deps import get_current_user
from app.schemas import (
    ExchangeData,
    ExchangeIn,
    ExchangeItemOut,
    ListData,
    MemberProfileOut,
    PageData,
    PointsLogOut,
)

router = APIRouter(prefix="/member", tags=["会员"])


@router.get("/profile", response_model=ApiResponse[MemberProfileOut], summary="会员等级、积分、余额、成长值")
def profile(user: dict = Depends(get_current_user)):
    growth = user["points"]
    index = 0
    for i, (_, threshold) in enumerate(db.MEMBER_LEVELS):
        if growth >= threshold:
            index = i

    level = db.MEMBER_LEVELS[index][0]
    current_threshold = db.MEMBER_LEVELS[index][1]
    if index + 1 < len(db.MEMBER_LEVELS):
        next_level, next_threshold = db.MEMBER_LEVELS[index + 1]
        span = next_threshold - current_threshold
        progress = round((growth - current_threshold) / span, 2) if span else 1.0
    else:
        next_level, next_threshold, progress = None, None, 1.0

    return ok(
        {
            "level": level,
            "points": user["points"],
            "balance": user["balance"],
            "growth": growth,
            "next_level": next_level,
            "next_level_growth": next_threshold,
            "progress": progress,
            "coupon_count": db.coupon_count(user["id"]),
        }
    )


@router.get("/points/logs", response_model=ApiResponse[PageData[PointsLogOut]], summary="积分明细")
def points_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    logs = db.POINTS_LOGS.get(user["id"], [])
    total = len(logs)
    start = (page - 1) * page_size
    return ok(
        {
            "items": logs[start : start + page_size],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/points/items", response_model=ApiResponse[ListData[ExchangeItemOut]], summary="积分兑换商品")
def exchange_items(user: dict = Depends(get_current_user)):
    return ok({"items": db.POINT_EXCHANGE_ITEMS})


@router.post("/points/exchange", response_model=ApiResponse[ExchangeData], summary="积分兑换")
def exchange(payload: ExchangeIn, user: dict = Depends(get_current_user)):
    item = db.POINT_EXCHANGE_BY_ID.get(payload.item_id)
    if item is None:
        raise BizError(1004, "兑换商品不存在", 404)
    if user["points"] < item["cost"]:
        raise BizError(6001, "积分不足", 400)

    coupon = None
    if item["type"] == "coupon":
        template = db.COUPON_TEMPLATES_BY_ID[item["template_id"]]
        coupon = db.add_coupon(user["id"], template)

    points = db.change_points(user, -item["cost"], f"积分兑换：{item['title']}", "exchange")
    return ok({"points": points, "coupon": coupon, "message": "兑换成功"})
