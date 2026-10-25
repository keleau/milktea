from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.response import BizError
from app.core.security import decode_token
from app.db import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)


def _resolve(credentials: HTTPAuthorizationCredentials | None, db: Session) -> User | None:
    if credentials is None:
        return None
    user_id = decode_token(credentials.credentials, "access")
    user = db.get(User, user_id)
    if user is None:
        raise BizError(1002, "用户不存在或登录已失效", 401)
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    user = _resolve(credentials, db)
    if user is None:
        raise BizError(1002, "未登录", 401)
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User | None:
    try:
        return _resolve(credentials, db)
    except BizError:
        return None
