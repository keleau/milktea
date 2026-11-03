import hashlib
import json
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import urlopen

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import now_ms
from app.core.config import settings
from app.core.response import ApiResponse, BizError, ok
from app.core.security import decode_token, issue_tokens
from app.db import get_db
from app.models import MemberLevel, User
from app.schemas import AuthData, LoginIn, RefreshIn, TokenPairOut
from app.serializers import serialize_user
from app.services.coupons import count_unused

router = APIRouter(prefix="/auth", tags=["认证"])

WECHAT_SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


def _code2session(code: str) -> str:
    """用小程序 code 换 openid；session_key 留在服务端，不返回给前端"""
    query = urlencode(
        {
            "appid": settings.wechat_appid,
            "secret": settings.wechat_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }
    )
    try:
        with urlopen(f"{WECHAT_SESSION_URL}?{query}", timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise BizError(9000, "微信登录服务暂时不可用，请稍后再试", 502) from exc

    if data.get("errcode"):
        raise BizError(
            1001,
            f"微信登录失败：{data.get('errmsg') or 'code 无效'}（{data.get('errcode')}）",
            400,
        )
    openid = data.get("openid")
    if not openid:
        raise BizError(9000, "微信登录返回数据异常", 502)
    return openid


@router.post("/wx-login", response_model=ApiResponse[AuthData], summary="微信登录（code=demo 使用预置会员）")
def wx_login(payload: LoginIn, db: Session = Depends(get_db)):
    if payload.code == "demo":
        openid = "mock-openid-demo"
    elif settings.wechat_login_enabled:
        openid = _code2session(payload.code)
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
            growth=0,
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
