from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import ApiResponse, ok
from app.db import get_db
from app.schemas import OrderOut, StaffPickupIn
from app.serializers import serialize_order
from app.services import pickup as pickup_service

router = APIRouter(prefix="/staff", tags=["店员"])


@router.post("/pickup/lookup", response_model=ApiResponse[OrderOut], summary="核销前查询订单")
def lookup_pickup(payload: StaffPickupIn, db: Session = Depends(get_db)):
    order = pickup_service.lookup_pickup(db, payload.code, payload.pin)
    return ok(serialize_order(order))


@router.post("/pickup/complete", response_model=ApiResponse[OrderOut], summary="确认取餐核销")
def complete_pickup(payload: StaffPickupIn, db: Session = Depends(get_db)):
    order = pickup_service.complete_pickup(db, payload.code, payload.pin)
    return ok(serialize_order(order))
