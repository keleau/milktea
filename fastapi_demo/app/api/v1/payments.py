import secrets
import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.constants import STATE_TEXT
from app.core.response import ApiResponse, BizError, ok
from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    PaymentNotifyData,
    PaymentNotifyIn,
    PaymentStatusOut,
    PrepayIn,
    PrepayOut,
)
from app.services import orders as order_service

router = APIRouter(prefix="/payments", tags=["支付"])


@router.post("/wechat/prepay", response_model=ApiResponse[PrepayOut], summary="统一下单（演示返回模拟支付参数）")
def prepay(
    payload: PrepayIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = order_service.get_owned_order(db, user, payload.out_trade_no)
    if order.state in ("making", "completed"):
        raise BizError(4002, "订单已支付，请勿重复支付", 409)
    if order.state == "cancelled":
        raise BizError(4003, "订单已取消", 410)
    return ok(
        {
            "timeStamp": str(int(time.time())),
            "nonceStr": secrets.token_hex(8).upper(),
            "package": f"prepay_id=demo{secrets.token_hex(8)}",
            "signType": "RSA",
            "paySign": "demo-sign",
        }
    )


@router.post("/wechat/notify", response_model=ApiResponse[PaymentNotifyData], summary="支付回调（演示：直接置为支付成功）")
def wechat_notify(payload: PaymentNotifyIn, db: Session = Depends(get_db)):
    if payload.result_code != "SUCCESS":
        raise BizError(5002, "支付结果失败", 400)
    order = order_service.pay_order(db, payload.out_trade_no, payload.transaction_id)
    return ok(
        {
            "out_trade_no": order.out_trade_no,
            "state": order.state,
            "state_text": STATE_TEXT[order.state],
        }
    )


@router.get("/{out_trade_no}", response_model=ApiResponse[PaymentStatusOut], summary="查询支付状态")
def payment_status(
    out_trade_no: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = order_service.get_owned_order(db, user, out_trade_no)
    return ok(
        {
            "out_trade_no": order.out_trade_no,
            "state": order.state,
            "state_text": STATE_TEXT[order.state],
            "paid": order.pay_time is not None,
            "transaction_id": order.transaction_id,
            "pay_time": order.pay_time,
        }
    )
