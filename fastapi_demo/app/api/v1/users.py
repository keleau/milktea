import time

from fastapi import APIRouter, Depends, File, Query, UploadFile

import app.data as db
from app.core.config import settings
from app.core.response import ApiResponse, BizError, ok
from app.deps import get_current_user
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

router = APIRouter(prefix="/users", tags=["用户"])


def _coupon_list(user_id: int, status: CouponStatus) -> list[dict]:
    coupons = db.user_coupons(user_id)
    if status != "all":
        coupons = [c for c in coupons if c["status"] == status]
    return sorted(coupons, key=lambda c: (c["status"] != "unused", c["expire_at"]))


@router.get("/me", response_model=ApiResponse[UserOut], summary="当前用户信息")
def get_me(user: dict = Depends(get_current_user)):
    return ok(db.user_out(user))


@router.patch("/me", response_model=ApiResponse[UserOut], summary="修改昵称")
def patch_me(payload: UserPatchIn, user: dict = Depends(get_current_user)):
    user["nickname"] = payload.nickname.strip()
    return ok(db.user_out(user))


@router.post("/me/avatar", response_model=ApiResponse[AvatarData], summary="上传头像（multipart）")
async def upload_avatar(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    ext = ext_map.get(file.content_type or "")
    if ext is None:
        raise BizError(1001, "仅支持 jpg/png/webp 图片", 400)
    data = await file.read()
    if not data:
        raise BizError(1001, "图片内容为空", 400)
    if len(data) > settings.max_avatar_bytes:
        raise BizError(1001, "头像不能超过 2MB", 400)

    settings.avatar_dir.mkdir(parents=True, exist_ok=True)
    filename = f"user_{user['id']}_{int(time.time())}.{ext}"
    (settings.avatar_dir / filename).write_bytes(data)
    avatar_url = f"{settings.base_url}/static/avatars/{filename}"
    user["avatar"] = avatar_url
    return ok({"avatar": avatar_url})


@router.get("/me/coupons", response_model=ApiResponse[ListData[CouponOut]], summary="我的优惠券")
def my_coupons(
    status: CouponStatus = Query("all"),
    user: dict = Depends(get_current_user),
):
    return ok({"items": _coupon_list(user["id"], status)})


@router.get("/me/favorites", response_model=ApiResponse[ListData[ProductOut]], summary="我的常点")
def my_favorites(user: dict = Depends(get_current_user)):
    products = []
    for product_id in db.frequent_product_ids(user["id"]):
        product = db.PRODUCTS_BY_ID.get(product_id)
        if product is not None and product["on_sale"]:
            products.append(product)
    return ok({"items": products})


@router.post("/me/favorites/{product_id}", response_model=ApiResponse[FavoriteOut], summary="收藏商品")
def add_favorite(product_id: int, user: dict = Depends(get_current_user)):
    if product_id not in db.PRODUCTS_BY_ID:
        raise BizError(1004, "商品不存在", 404)
    favorites = db.FAVORITES.setdefault(user["id"], [])
    if product_id not in favorites:
        favorites.append(product_id)
    return ok({"product_id": product_id, "favorited": True})


@router.delete("/me/favorites/{product_id}", response_model=ApiResponse[FavoriteOut], summary="取消收藏")
def remove_favorite(product_id: int, user: dict = Depends(get_current_user)):
    favorites = db.FAVORITES.setdefault(user["id"], [])
    if product_id in favorites:
        favorites.remove(product_id)
    return ok({"product_id": product_id, "favorited": False})
