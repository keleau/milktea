from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.response import ApiResponse, BizError, ok
from app.db import get_db
from app.deps import get_current_user, get_optional_user
from app.models import CouponTemplate, Store, User, UserCoupon
from app.schemas import CouponOut, CouponTemplateOut, ListData
from app.serializers import serialize_coupon, serialize_template
from app.services.coupons import add_coupon
from app.services.pricing import usable_coupons

router = APIRouter(prefix="/coupons", tags=["优惠券"])


@router.get("/templates", response_model=ApiResponse[ListData[CouponTemplateOut]], summary="券包中心可领券模板")
def list_templates(
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    templates = db.scalars(
        select(CouponTemplate).order_by(CouponTemplate.sort_order, CouponTemplate.id)
    ).all()
    owned_templates: set[int] = set()
    if user is not None:
        owned_templates = set(
            db.scalars(
                select(UserCoupon.template_id).where(UserCoupon.user_id == user.id)
            ).all()
        )
    items = [
        serialize_template(template, template.id in owned_templates)
        for template in templates
    ]
    return ok({"items": items})


@router.post("/{template_id}/claim", response_model=ApiResponse[CouponOut], summary="领取优惠券")
def claim_coupon(
    template_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.get(CouponTemplate, template_id)
    if template is None:
        raise BizError(1004, "优惠券模板不存在", 404)
    claimed = db.scalar(
        select(UserCoupon.id)
        .where(UserCoupon.user_id == user.id, UserCoupon.template_id == template_id)
        .limit(1)
    )
    if claimed is not None:
        raise BizError(3003, "优惠券重复领取", 409)
    coupon = add_coupon(db, user.id, template)
    db.commit()
    return ok(serialize_coupon(coupon))


@router.get("/usable", response_model=ApiResponse[ListData[CouponOut]], summary="当前金额可用券（结算页）")
def get_usable(
    amount: float = Query(..., ge=0),
    store_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if store_id is not None and db.get(Store, store_id) is None:
        raise BizError(1004, "门店不存在", 404)
    coupons = usable_coupons(db, user.id, Decimal(str(amount)))
    db.commit()
    return ok({"items": [serialize_coupon(coupon) for coupon in coupons]})
