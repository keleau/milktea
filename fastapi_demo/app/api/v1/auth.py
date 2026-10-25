import hashlib
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import now_ms
from app.core.response import ApiResponse, BizError, ok
from app.core.security import decode_token, issue_tokens
from app.db import get_db
from app.models import MemberLevel, User
from app.schemas import AuthData, LoginIn, RefreshIn, TokenPairOut
from app.serializers import serialize_user
from app.services.coupons import count_unused

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/wx-login", response_model=ApiResponse[AuthData], summary="微信登录（演示：code=demo 使用预置会员）")
def wx_login(payload: LoginIn, db: Session = Depends(get_db)):
    if payload.code == "demo":
        openid = "mock-openid-demo"
    elif payload.mock_id:
        # 未接微信 code2session 前，用设备固定 ID 保证同一台设备重复登录是同一个账号
        openid = "mock-" + hashlib.sha256(f"device:{payload.mock_id}".encode()).hexdigest()[:24]
    else:
        openid = "mock-" + hashlib.sha256(payload.code.encode()).hexdigest()[:24]

    user = db.scalar(select(User).where(User.openid == openid))
    if user is None:
        user = User(
            openid=openid,
            nickname=payload.nickname or "猫友1234",
            avatar_path=payload.avatar or "/static/images/avatar.jpg",
            level=db.get(MemberLevel, "V1"),
            level_code="V1",
            points=0,
            balance=Decimal("0.00"),
            created_at=now_ms(),
        )
        db.add(user)
    else:
        if payload.nickname:
            user.nickname = payload.nickname
        if payload.avatar:
            user.avatar_path = payload.avatar
    db.commit()

    tokens = issue_tokens(user.id)
    return ok({**tokens, "user": serialize_user(user, count_unused(db, user.id))})


@router.post("/refresh", response_model=ApiResponse[TokenPairOut], summary="刷新 access_token")
def refresh(payload: RefreshIn, db: Session = Depends(get_db)):
    user_id = decode_token(payload.refresh_token, "refresh")
    if db.get(User, user_id) is None:
        raise BizError(1002, "用户不存在或登录已失效", 401)
    return ok(issue_tokens(user_id))
