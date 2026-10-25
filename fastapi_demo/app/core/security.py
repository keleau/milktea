import base64
import hashlib
import hmac
import json
import time

from app.core.config import settings
from app.core.response import BizError


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _sign(body: str) -> str:
    digest = hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest()
    return _b64encode(digest)


def create_token(user_id: int, token_type: str, ttl: int) -> str:
    payload = {"sub": str(user_id), "type": token_type, "exp": int(time.time()) + ttl}
    body = _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    return f"{body}.{_sign(body)}"


def decode_token(token: str, expected_type: str) -> int:
    try:
        body, signature = token.split(".", 1)
    except ValueError:
        raise BizError(1002, "token 格式不正确", 401)
    if not hmac.compare_digest(signature, _sign(body)):
        raise BizError(1002, "token 无效", 401)
    try:
        payload = json.loads(_b64decode(body))
    except (ValueError, json.JSONDecodeError):
        raise BizError(1002, "token 无效", 401)
    if payload.get("type") != expected_type:
        raise BizError(1002, "token 类型不正确", 401)
    if int(payload.get("exp", 0)) <= int(time.time()):
        raise BizError(1002, "登录已过期，请重新登录", 401)
    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise BizError(1002, "token 无效", 401)


def issue_tokens(user_id: int) -> dict:
    return {
        "access_token": create_token(user_id, "access", settings.access_token_ttl),
        "refresh_token": create_token(user_id, "refresh", settings.refresh_token_ttl),
        "token_type": "Bearer",
        "expires_in": settings.access_token_ttl,
    }
