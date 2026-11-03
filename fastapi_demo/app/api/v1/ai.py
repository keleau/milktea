from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import ApiResponse, ok
from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import AiChatIn, AiChatOut, AiHistoryOut
from app.services.ai_agent import service as ai_service

router = APIRouter(prefix="/ai", tags=["AI 点单"])


@router.post("/chat", response_model=ApiResponse[AiChatOut], summary="AI 点单对话")
def ai_chat(
    payload: AiChatIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(ai_service.chat(db, user, payload.message, payload.store_id, payload.table_no))


@router.get("/history", response_model=ApiResponse[AiHistoryOut], summary="AI 会话历史")
def ai_history(user: User = Depends(get_current_user)):
    return ok({"messages": ai_service.get_history(user.id)})


@router.delete("/session", response_model=ApiResponse[dict], summary="清空 AI 会话")
def clear_ai_session(user: User = Depends(get_current_user)):
    ai_service.clear_history(user.id)
    return ok({"cleared": True})
