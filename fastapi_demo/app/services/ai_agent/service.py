import logging
import threading

from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import now_ms
from app.core.config import settings
from app.core.response import BizError
from app.models import Store, User
from app.serializers import serialize_order
from app.services import orders as order_service
from app.services.ai_agent.graph import build_graph
from app.services.ai_agent.prompt import build_system_prompt
from app.services.ai_agent.tools import build_tools

logger = logging.getLogger("simaotea.ai")

_MAX_MESSAGES = 20
_MAX_LLM_HISTORY = 10
_SESSION_TTL_MS = 2 * 3600 * 1000

_state_lock = threading.RLock()
_sessions: dict[int, dict] = {}
_user_locks: dict[int, threading.Lock] = {}


def _get_session(user_id: int) -> dict:
    with _state_lock:
        session = _sessions.get(user_id)
        if session is not None and now_ms() - session["updated_at"] > _SESSION_TTL_MS:
            _sessions.pop(user_id, None)
            session = None
        if session is None:
            session = {"messages": [], "updated_at": now_ms()}
            _sessions[user_id] = session
        return session


def get_history(user_id: int) -> list[dict]:
    session = _get_session(user_id)
    with _state_lock:
        return [dict(message) for message in session["messages"]]


def clear_history(user_id: int) -> None:
    with _state_lock:
        _sessions.pop(user_id, None)


def _append_message(user_id: int, role: str, content: str, order: dict | None = None) -> None:
    with _state_lock:
        session = _get_session(user_id)
        message = {"role": role, "content": content, "created_at": now_ms()}
        if order is not None:
            message["order"] = order
        session["messages"].append(message)
        session["messages"] = session["messages"][-_MAX_MESSAGES:]
        session["updated_at"] = now_ms()


def _user_lock(user_id: int) -> threading.Lock:
    with _state_lock:
        return _user_locks.setdefault(user_id, threading.Lock())


def _resolve_store(db: Session, store_id: int | None) -> Store:
    if store_id is not None:
        store = db.get(Store, store_id)
    else:
        store = db.scalar(
            select(Store)
            .where(Store.status != "closed")
            .order_by(Store.sort_order, Store.id)
        )
        if store is None:
            store = db.scalar(select(Store).order_by(Store.sort_order, Store.id))
    if store is None:
        raise BizError(1004, "门店不存在", 404)
    return store


def _history_messages(history: list[dict]) -> list:
    messages = []
    for item in history[-_MAX_LLM_HISTORY:]:
        if item["role"] == "user":
            messages.append(HumanMessage(content=item["content"]))
        elif item["role"] == "assistant":
            messages.append(AIMessage(content=item["content"]))
    return messages


def _message_text(message) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts).strip()
    return str(content or "").strip()


def _extract_answer(result: dict) -> str:
    messages = result.get("messages") or []
    if messages:
        text = _message_text(messages[-1])
        if text:
            return text
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            text = _message_text(message)
            if text:
                return text
    return "我在呢～可以告诉我想喝什么，比如「少冰五分糖一杯黑糖波波厚奶茶」。"


def chat(
    db: Session,
    user: User,
    message: str,
    store_id: int | None = None,
    table_no: str | None = None,
) -> dict:
    text = (message or "").strip()
    if not text:
        raise BizError(1001, "消息不能为空", 400)
    if len(text) > 500:
        raise BizError(1001, "消息不能超过 500 字", 400)
    if not settings.ai_enabled:
        raise BizError(9000, "智能点单助手暂未配置大模型密钥，请联系门店", 503)

    store = _resolve_store(db, store_id)
    table_no = (table_no or "").strip().upper() or None

    with _user_lock(user.id):
        history = get_history(user.id)
        context: dict = {}
        tools = build_tools(db, user, store.id, context, table_no)
        graph = build_graph(tools)
        payload = {
            "messages": [*_history_messages(history), HumanMessage(content=text)],
            "system_prompt": build_system_prompt(db, store, table_no),
            "user_id": user.id,
            "store_id": store.id,
            "order_context": context,
        }

        try:
            result = graph.invoke(payload, config={"recursion_limit": 10})
        except Exception:
            logger.exception("AI 对话调用失败 user_id=%s", user.id)
            result = None

        if result is None:
            if context.get("order_no"):
                order = order_service.get_owned_order(db, user, context["order_no"])
                answer = "订单已经创建好了，但助手回复超时了。请到订单详情查看并完成支付。"
                card = serialize_order(order)
                _append_message(user.id, "user", text)
                _append_message(user.id, "assistant", answer, card)
                return {"answer": answer, "order": card}
            raise BizError(9000, "智能助手有点忙，请稍后再试", 503)

        answer = _extract_answer(result)
        card = None
        if context.get("order_no"):
            try:
                order = order_service.get_owned_order(db, user, context["order_no"])
                card = serialize_order(order)
            except BizError:
                card = None

        _append_message(user.id, "user", text)
        _append_message(user.id, "assistant", answer, card)
        return {"answer": answer, "order": card}
