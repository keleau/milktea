from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import now_ms
from app.models import MemberLevel, PointsLog, User


def levels(db: Session) -> list[MemberLevel]:
    return list(db.scalars(select(MemberLevel).order_by(MemberLevel.min_points)))


def level_text(level: MemberLevel | None, fallback: str = "") -> str:
    if level is None:
        return fallback
    return f"{level.code} {level.name}"


def change_points(db: Session, user: User, delta: int, title: str, log_type: str) -> int:
    user.points = max(0, user.points + delta)
    chosen = None
    for level in levels(db):
        if user.points >= level.min_points:
            chosen = level
    if chosen is not None:
        user.level = chosen
    db.add(
        PointsLog(
            user_id=user.id,
            title=title,
            points=delta,
            type=log_type,
            created_at=now_ms(),
        )
    )
    return user.points
