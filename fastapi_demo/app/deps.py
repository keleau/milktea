from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import app.data as db
from app.core.response import BizError
from app.core.security import decode_token

bearer = HTTPBearer(auto_error=False)


def _resolve(credentials: HTTPAuthorizationCredentials | None) -> dict | None:
    if credentials is None:
        return None
    user_id = decode_token(credentials.credentials, "access")
    user = db.USERS.get(user_id)
    if user is None:
        raise BizError(1002, "用户不存在或登录已失效", 401)
    return user


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    user = _resolve(credentials)
    if user is None:
        raise BizError(1002, "未登录", 401)
    return user


def get_optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict | None:
    try:
        return _resolve(credentials)
    except BizError:
        return None
