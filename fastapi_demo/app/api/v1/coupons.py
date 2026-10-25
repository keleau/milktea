from fastapi import APIRouter, Depends, Query

import app.data as db
from app.core.response import ApiResponse, BizError, ok
from app.deps import get_current_user, get_optional_user
from app.schemas import CouponOut, CouponTemplateOut, ListData
from app.services.pricing import usable_coupons

router = APIRouter(prefix="/coupons", tags=["优惠券"])


@router.get("/templates", response_model=ApiResponse[ListData[CouponTemplateOut]], summary="券包中心可领券模板")
def list_templates(user: dict | None = Depends(get_optional_user)):
    owned_templates = set()
    if user is not None:
        owned_templates = {coupon["template_id"] for coupon in db.user_coupons(user["id"])}
    items = [{**template, "claimed": template["id"] in owned_templates} for template in db.COUPON_TEMPLATES]
    return ok({"items": items})


@router.post("/{template_id}/claim", response_model=ApiResponse[CouponOut], summary="领取优惠券")
def claim_coupon(template_id: int, user: dict = Depends(get_current_user)):
    template = db.COUPON_TEMPLATES_BY_ID.get(template_id)
    if template is None:
        raise BizError(1004, "优惠券模板不存在", 404)
    if any(coupon["template_id"] == template_id for coupon in db.user_coupons(user["id"])):
        raise BizError(3003, "优惠券重复领取", 409)
    coupon = db.add_coupon(user["id"], template)
    return ok(coupon)


@router.get("/usable", response_model=ApiResponse[ListData[CouponOut]], summary="当前金额可用券（结算页）")
def get_usable(
    amount: float = Query(..., ge=0),
    store_id: int | None = Query(None),
    user: dict = Depends(get_current_user),
):
    if store_id is not None and store_id not in db.STORES_BY_ID:
        raise BizError(1004, "门店不存在", 404)
    return ok({"items": usable_coupons(user["id"], amount)})
