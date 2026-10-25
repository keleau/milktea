from fastapi import APIRouter, Depends, Header, Query

import app.data as db
from app.core.response import ApiResponse, BizError, ok
from app.deps import get_current_user, get_optional_user
from app.schemas import (
    OrderCountsOut,
    OrderCreateIn,
    OrderOut,
    OrderState,
    PageData,
    PricePreviewIn,
    PricePreviewOut,
    RepeatData,
    ReviewIn,
    ReviewOut,
)
from app.services import orders as order_service
from app.services.pricing import estimated_ready_minutes, quote, usable_coupons

router = APIRouter(prefix="/orders", tags=["订单"])


@router.post("/price-preview", response_model=ApiResponse[PricePreviewOut], summary="订单金额试算")
def price_preview(payload: PricePreviewIn, user: dict | None = Depends(get_optional_user)):
    result = quote(user["id"] if user else None, payload.model_dump())
    coupons = usable_coupons(user["id"], result["subtotal"]) if user else []
    return ok(
        {
            "subtotal": result["subtotal"],
            "pack_fee": result["pack_fee"],
            "coupon_cut": result["coupon_cut"],
            "total": result["total"],
            "usable_coupons": coupons,
            "estimated_ready_minutes": estimated_ready_minutes(result["store"]),
        }
    )


@router.post("", response_model=ApiResponse[OrderOut], summary="创建订单")
def create_order(
    payload: OrderCreateIn,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user: dict = Depends(get_current_user),
):
    order = order_service.create_order(user, payload.model_dump(), idempotency_key)
    return ok(order)


@router.get("", response_model=ApiResponse[PageData[OrderOut]], summary="订单列表（分页）")
def list_orders(
    state: OrderState | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    orders = [order for order in db.ORDERS.values() if order["user_id"] == user["id"]]
    if state:
        orders = [order for order in orders if order["state"] == state]
    orders.sort(key=lambda order: order["create_time"], reverse=True)
    total = len(orders)
    start = (page - 1) * page_size
    return ok(
        {
            "items": orders[start : start + page_size],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/counts", response_model=ApiResponse[OrderCountsOut], summary="各状态订单数")
def order_counts(user: dict = Depends(get_current_user)):
    return ok(order_service.counts(user))


@router.get("/{out_trade_no}", response_model=ApiResponse[OrderOut], summary="订单详情")
def order_detail(out_trade_no: str, user: dict = Depends(get_current_user)):
    return ok(order_service.get_owned_order(user, out_trade_no))


@router.post("/{out_trade_no}/cancel", response_model=ApiResponse[OrderOut], summary="取消订单")
def cancel_order(out_trade_no: str, user: dict = Depends(get_current_user)):
    return ok(order_service.cancel_order(user, out_trade_no))


@router.post("/{out_trade_no}/complete", response_model=ApiResponse[OrderOut], summary="完成订单（演示：模拟门店出杯）")
def complete_order(out_trade_no: str, user: dict = Depends(get_current_user)):
    return ok(order_service.complete_order(user, out_trade_no))


@router.post("/{out_trade_no}/repeat", response_model=ApiResponse[RepeatData], summary="再来一单（返回下单草稿）")
def repeat_order(out_trade_no: str, user: dict = Depends(get_current_user)):
    return ok(order_service.repeat_data(user, out_trade_no))


@router.post("/{out_trade_no}/review", response_model=ApiResponse[ReviewOut], summary="评价订单")
def review_order(out_trade_no: str, payload: ReviewIn, user: dict = Depends(get_current_user)):
    review = order_service.review_order(user, out_trade_no, payload.rating, payload.content)
    return ok(review)
