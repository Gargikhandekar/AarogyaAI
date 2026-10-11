"""Chat service: persistence + RAG orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import Chat, Message, User
from app.rag import KnowledgeBaseUnavailable, RAGResult, rag_pipeline
from app.rag.retrievers import ScoredDocs
from app.utils.helpers import (
    DISCLAIMER,
    EMERGENCY_RESPONSE,
    build_chat_title,
    detect_emergency,
    infer_category,
)


def ensure_knowledge_base() -> None:
    """Fail before anything is saved if the dataset or index did not load."""
    if not rag_pipeline.ready:
        raise KnowledgeBaseUnavailable(rag_pipeline.error or "knowledge base not loaded")


def get_or_create_chat(
    db: Session,
    user: User,
    chat_id: Optional[int],
    first_message: str,
    category: Optional[str],
) -> Chat:
    if chat_id:
        chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
        if chat:
            return chat

    chat = Chat(
        user_id=user.id,
        title=build_chat_title(first_message),
        category=category or infer_category(first_message),
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def _save_user_message(db: Session, chat: Chat, message: str, cat: str) -> None:
    db.add(Message(chat_id=chat.id, role="user", content=message, category=cat))
    chat.updated_at = datetime.utcnow()
    if chat.title == "New Chat":
        chat.title = build_chat_title(message)
    db.commit()


def save_assistant_message(
    db: Session,
    chat: Chat,
    result: RAGResult,
    cat: str,
    is_emergency: bool = False,
) -> Dict[str, Any]:
    assistant = Message(
        chat_id=chat.id,
        role="assistant",
        content=result.answer,
        confidence=result.top_score,
        category=cat,
        is_emergency=is_emergency,
        sources=json.dumps(result.sources),
    )
    db.add(assistant)
    chat.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assistant)
    return {
        "chat_id": chat.id,
        "message_id": assistant.id,
        "answer": result.answer,
        "status": result.status,
        "confidence": round(float(result.top_score), 4),
        "sources": result.sources,
        "category": cat,
        "is_emergency": is_emergency,
        "disclaimer": DISCLAIMER,
        "timestamp": assistant.created_at,
    }


def _emergency_result(reason: Optional[str]) -> RAGResult:
    answer = EMERGENCY_RESPONSE.format(reason=reason or "This may be urgent.")
    return RAGResult(answer=answer, status="emergency", top_score=0.0)


def process_chat(
    db: Session,
    user: User,
    message: str,
    chat_id: Optional[int] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    ensure_knowledge_base()
    is_emergency, reason = detect_emergency(message)
    cat = category or infer_category(message)
    chat = get_or_create_chat(db, user, chat_id, message, cat)
    _save_user_message(db, chat, message, cat)

    result = _emergency_result(reason) if is_emergency else rag_pipeline.answer(message)
    return save_assistant_message(db, chat, result, cat, is_emergency)


@dataclass
class PreparedStream:
    chat_id: int
    message: str
    category: str
    is_emergency: bool
    scored: ScoredDocs
    early: Optional[RAGResult]  # set when no LLM call is needed

    @property
    def preview_sources(self) -> List[Dict[str, Any]]:
        if self.early is not None:
            return self.early.sources
        return rag_pipeline.sources(self.scored, cited=set())


def prepare_stream_chat(
    db: Session,
    user: User,
    message: str,
    chat_id: Optional[int] = None,
    category: Optional[str] = None,
) -> PreparedStream:
    """Save the user message and run retrieval, so sources can be sent before tokens."""
    ensure_knowledge_base()
    is_emergency, reason = detect_emergency(message)
    cat = category or infer_category(message)
    chat = get_or_create_chat(db, user, chat_id, message, cat)
    _save_user_message(db, chat, message, cat)

    if is_emergency:
        return PreparedStream(chat.id, message, cat, True, [], _emergency_result(reason))
    scored, early = rag_pipeline.plan(message)
    return PreparedStream(chat.id, message, cat, False, scored, early)


# ── History ─────────────────────────────────────────────────────────────────
# Every query filters on user_id, so one user can never read or change another's chats.


def list_chats(db: Session, user: User, search: Optional[str] = None) -> List[Chat]:
    query = db.query(Chat).filter(Chat.user_id == user.id)
    if search:
        query = query.filter(Chat.title.ilike(f"%{search.strip()}%"))
    return query.order_by(Chat.updated_at.desc()).all()


def get_chat_detail(db: Session, user: User, chat_id: int) -> Optional[Chat]:
    return db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()


def rename_chat(db: Session, user: User, chat_id: int, title: str) -> Optional[Chat]:
    chat = get_chat_detail(db, user, chat_id)
    if chat:
        chat.title = title
        db.commit()
        db.refresh(chat)
    return chat


def delete_chat(db: Session, user: User, chat_id: int) -> bool:
    chat = get_chat_detail(db, user, chat_id)
    if not chat:
        return False
    db.delete(chat)
    db.commit()
    return True


def delete_all_chats(db: Session, user: User) -> int:
    chats = db.query(Chat).filter(Chat.user_id == user.id).all()
    for chat in chats:
        db.delete(chat)
    db.commit()
    return len(chats)


def set_feedback(db: Session, user: User, message_id: int, feedback: str) -> Optional[Message]:
    msg = (
        db.query(Message)
        .join(Chat)
        .filter(Message.id == message_id, Chat.user_id == user.id)
        .first()
    )
    if msg:
        msg.feedback = None if feedback == "none" else feedback
        db.commit()
        db.refresh(msg)
    return msg
