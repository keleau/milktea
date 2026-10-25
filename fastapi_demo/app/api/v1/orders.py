import segno
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.response import ApiResponse, BizError, ok
from app.db import get_db
from app.deps import get_current_user, get_optional_user
from app.models import Order, User
from app.schemas import (
    OrderCountsOut,
    OrderCreateIn,
    OrderOut,
    OrderState,
    PageData,
    PickupQrOut,
    PricePreviewIn,
    PricePreviewOut,
    RepeatData,
    ReviewIn,
    ReviewOut,
)
from app.serializers import money, serialize_coupon, serialize_order
from app.services import orders as order_service
from app.services.pricing import estimated_ready_minutes, quote, usable_coupons

router = APIRouter(prefix="/orders", tags=["订单"])


@router.post("/price-preview", response_model=ApiResponse[PricePreviewOut], summary="订单金额试算")
def price_preview(
    payload: PricePreviewIn,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    result = quote(db, user.id if user else None, payload.model_dump())
    coupons = usable_coupons(db, user.id, result["subtotal"]) if user else []
    return ok(
        {
            "subtotal": money(result["subtotal"]),
            "pack_fee": money(result["pack_fee"]),
            "coupon_cut": money(result["coupon_cut"]),
            "total": money(result["total"]),
            "usable_coupons": [serialize_coupon(coupon) for coupon in coupons],
            "estimated_ready_minutes": estimated_ready_minutes(result["store"]),
        }
    )


@router.post("", response_model=ApiResponse[OrderOut], summary="创建订单")
def create_order(
    payload: OrderCreateIn,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = order_service.create_order(db, user, payload.model_dump(), idempotency_key)
    return ok(serialize_order(order))


@router.get("", response_model=ApiResponse[PageData[OrderOut]], summary="订单列表（分页）")
def list_orders(
    state: OrderState | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filters = [Order.user_id == user.id]
    if state:
        filters.append(Order.state == state)

    total = db.scalar(select(func.count()).select_from(Order).where(*filters)) or 0
    orders = db.scalars(
        select(Order)
        .where(*filters)
        .order_by(Order.create_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return ok(
        {
            "items": [serialize_order(order) for order in orders],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/counts", response_model=ApiResponse[OrderCountsOut], summary="各状态订单数")
def order_counts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(order_service.counts(db, user))


@router.get("/{out_trade_no}", response_model=ApiResponse[OrderOut], summary="订单详情")
def order_detail(
    out_trade_no: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(serialize_order(order_service.get_owned_order(db, user, out_trade_no)))


@router.get("/{out_trade_no}/pickup-qr", response_model=ApiResponse[PickupQrOut], summary="取餐二维码")
def pickup_qr(
    out_trade_no: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = order_service.get_owned_order(db, user, out_trade_no)
    if order.state not in ("making", "completed") or not order.pick_code:
        raise BizError(4001, "订单还未进入制作，暂无取餐码", 409)
    content = f"PICK:{order.out_trade_no}:{order.pick_code}"
    image = segno.make(content, error="m").png_data_uri(scale=8, border=2)
    return ok({"content": content, "image": image})


@router.post("/{out_trade_no}/cancel", response_model=ApiResponse[OrderOut], summary="取消订单")
def cancel_order(
    out_trade_no: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(serialize_order(order_service.cancel_order(db, user, out_trade_no)))


@router.post("/{out_trade_no}/complete", response_model=ApiResponse[OrderOut], summary="完成订单（演示：模拟门店出杯）")
def complete_order(
    out_trade_no: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(serialize_order(order_service.complete_order(db, user, out_trade_no)))


@router.post("/{out_trade_no}/repeat", response_model=ApiResponse[RepeatData], summary="再来一单（返回下单草稿）")
def repeat_order(
    out_trade_no: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(order_service.repeat_data(db, user, out_trade_no))


@router.post("/{out_trade_no}/review", response_model=ApiResponse[ReviewOut], summary="评价订单")
def review_order(
    out_trade_no: str,
    payload: ReviewIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = order_service.review_order(
        db, user, out_trade_no, payload.rating, payload.content
    )
    return ok(review)
