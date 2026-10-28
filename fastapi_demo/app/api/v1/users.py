import time

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import now_ms
from app.core.config import settings
from app.core.response import ApiResponse, BizError, ok
from app.db import get_db
from app.deps import get_current_user
from app.models import Favorite, Product, User
from app.schemas import (
    AvatarData,
    CouponOut,
    CouponStatus,
    FavoriteOut,
    ListData,
    ProductOut,
    UserOut,
    UserPatchIn,
)
from app.serializers import serialize_coupon, serialize_product, serialize_user
from app.services.catalog import frequent_product_ids
from app.services.coupons import count_unused, list_for_user

router = APIRouter(prefix="/users", tags=["用户"])

_AVATAR_EXT_BY_TYPE = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def _sniff_image_ext(data: bytes) -> str | None:
    """微信 chooseAvatar 的临时文件偶尔没有 MIME，按文件头兜底识别"""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _coupon_list(db: Session, user_id: int, status: CouponStatus) -> list[dict]:
    coupons = list_for_user(db, user_id)
    if status != "all":
        coupons = [coupon for coupon in coupons if coupon.status == status]
    coupons.sort(key=lambda coupon: (coupon.status != "unused", coupon.expire_at))
    return [serialize_coupon(coupon) for coupon in coupons]


@router.get("/me", response_model=ApiResponse[UserOut], summary="当前用户信息")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(serialize_user(user, count_unused(db, user.id)))


@router.patch("/me", response_model=ApiResponse[UserOut], summary="修改昵称")
def patch_me(
    payload: UserPatchIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.nickname = payload.nickname.strip()
    db.commit()
    return ok(serialize_user(user, count_unused(db, user.id)))


@router.post("/me/avatar", response_model=ApiResponse[AvatarData], summary="上传头像（multipart）")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = await file.read()
    if not data:
        raise BizError(1001, "图片内容为空", 400)
    if len(data) > settings.max_avatar_bytes:
        raise BizError(1001, "头像不能超过 2MB", 400)

    ext = _AVATAR_EXT_BY_TYPE.get(file.content_type or "") or _sniff_image_ext(data)
    if ext is None:
        raise BizError(1001, "仅支持 jpg/png/webp 图片", 400)

    settings.avatar_dir.mkdir(parents=True, exist_ok=True)
    filename = f"user_{user.id}_{int(time.time())}.{ext}"
    (settings.avatar_dir / filename).write_bytes(data)
    user.avatar_path = f"/static/avatars/{filename}"
    db.commit()
    return ok({"avatar": f"{settings.base_url}/static/avatars/{filename}"})


@router.get("/me/coupons", response_model=ApiResponse[ListData[CouponOut]], summary="我的优惠券")
def my_coupons(
    status: CouponStatus = Query("all"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = _coupon_list(db, user.id, status)
    db.commit()
    return ok({"items": items})


@router.get("/me/favorites", response_model=ApiResponse[ListData[ProductOut]], summary="我的常点")
def my_favorites(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product_ids = frequent_product_ids(db, user.id)
    products = []
    if product_ids:
        rows = db.scalars(
            select(Product).where(Product.id.in_(product_ids), Product.on_sale.is_(True))
        ).all()
        by_id = {product.id: product for product in rows}
        products = [serialize_product(by_id[pid]) for pid in product_ids if pid in by_id]
    return ok({"items": products})


@router.post("/me/favorites/{product_id}", response_model=ApiResponse[FavoriteOut], summary="收藏商品")
def add_favorite(
    product_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.get(Product, product_id) is None:
        raise BizError(1004, "商品不存在", 404)
    if db.get(Favorite, (user.id, product_id)) is None:
        db.add(Favorite(user_id=user.id, product_id=product_id, created_at=now_ms()))
        db.commit()
    return ok({"product_id": product_id, "favorited": True})


@router.delete("/me/favorites/{product_id}", response_model=ApiResponse[FavoriteOut], summary="取消收藏")
def remove_favorite(
    product_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorite = db.get(Favorite, (user.id, product_id))
    if favorite is not None:
        db.delete(favorite)
        db.commit()
    return ok({"product_id": product_id, "favorited": False})
