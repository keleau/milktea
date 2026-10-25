import hashlib

from fastapi import APIRouter

import app.data as db
from app.core.response import ApiResponse, BizError, ok
from app.core.security import decode_token, issue_tokens
from app.schemas import AuthData, LoginIn, RefreshIn, TokenPairOut

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/wx-login", response_model=ApiResponse[AuthData], summary="微信登录（演示：code=demo 使用预置会员）")
def wx_login(payload: LoginIn):
    if payload.code == "demo":
        openid = "mock-openid-demo"
    else:
        openid = "mock-" + hashlib.sha256(payload.code.encode()).hexdigest()[:24]

    user = db.get_user_by_openid(openid)
    if user is None:
        user = db.create_user(openid, payload.nickname, payload.avatar)
    else:
        if payload.nickname:
            user["nickname"] = payload.nickname
        if payload.avatar:
            user["avatar"] = payload.avatar

    tokens = issue_tokens(user["id"])
    return ok({**tokens, "user": db.user_out(user)})


@router.post("/refresh", response_model=ApiResponse[TokenPairOut], summary="刷新 access_token")
def refresh(payload: RefreshIn):
    user_id = decode_token(payload.refresh_token, "refresh")
    if user_id not in db.USERS:
        raise BizError(1002, "用户不存在或登录已失效", 401)
    return ok(issue_tokens(user_id))
