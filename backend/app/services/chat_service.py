"""Chat service: persistence + RAG orchestration."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

from sqlalchemy.orm import Session

from app.models import Chat, Message, User
from app.rag import rag_pipeline
from app.utils.helpers import (
    DISCLAIMER,
    EMERGENCY_RESPONSE,
    build_chat_title,
    detect_emergency,
    infer_category,
)


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


def _source_payload(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "question": d["question"],
            "answer": d["answer"][:500],
            "category": d.get("category"),
            "source": d.get("source"),
            "score": round(float(d.get("score", 0)), 4),
        }
        for d in docs
    ]


def _finalize_chat(
    db: Session,
    chat: Chat,
    message: str,
    answer: str,
    confidence: float,
    sources: List[Dict[str, Any]],
    cat: str,
    is_emergency: bool,
) -> Dict[str, Any]:
    assistant = Message(
        chat_id=chat.id,
        role="assistant",
        content=answer,
        confidence=confidence,
        category=cat,
        is_emergency=is_emergency,
        sources=json.dumps(sources),
    )
    db.add(assistant)
    chat.updated_at = datetime.utcnow()
    if chat.title == "New Chat":
        chat.title = build_chat_title(message)
    db.commit()
    db.refresh(assistant)
    return {
        "chat_id": chat.id,
        "message_id": assistant.id,
        "answer": answer,
        "confidence": round(float(confidence), 4),
        "sources": sources,
        "category": cat,
        "is_emergency": is_emergency,
        "disclaimer": DISCLAIMER,
        "timestamp": assistant.created_at,
    }


def process_chat(
    db: Session,
    user: User,
    message: str,
    chat_id: Optional[int] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    is_emergency, reason = detect_emergency(message)
    cat = category or infer_category(message)
    chat = get_or_create_chat(db, user, chat_id, message, cat)

    user_msg = Message(chat_id=chat.id, role="user", content=message, category=cat)
    db.add(user_msg)
    db.commit()

    if is_emergency:
        answer = EMERGENCY_RESPONSE.format(reason=reason or "This may be urgent.")
        return _finalize_chat(db, chat, message, answer, 1.0, [], cat, True)

    answer, confidence, docs, cat = rag_pipeline.answer(message)
    sources = _source_payload(docs)
    return _finalize_chat(db, chat, message, answer, confidence, sources, cat, False)


def prepare_stream_chat(
    db: Session,
    user: User,
    message: str,
    chat_id: Optional[int] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Create chat + user message, retrieve docs, return meta for streaming generation."""
    is_emergency, reason = detect_emergency(message)
    cat = category or infer_category(message)
    chat = get_or_create_chat(db, user, chat_id, message, cat)

    user_msg = Message(chat_id=chat.id, role="user", content=message, category=cat)
    db.add(user_msg)
    chat.updated_at = datetime.utcnow()
    if chat.title == "New Chat":
        chat.title = build_chat_title(message)
    db.commit()
    db.refresh(chat)

    if is_emergency:
        answer = EMERGENCY_RESPONSE.format(reason=reason or "This may be urgent.")
        return {
            "chat": chat,
            "is_emergency": True,
            "answer": answer,
            "confidence": 1.0,
            "sources": [],
            "category": cat,
            "docs": [],
            "message": message,
        }

    docs = rag_pipeline.retrieve(message)
    confidence = float(docs[0]["score"]) if docs else 0.0
    return {
        "chat": chat,
        "is_emergency": False,
        "answer": None,
        "confidence": confidence,
        "sources": _source_payload(docs),
        "category": cat or infer_category(message),
        "docs": docs,
        "message": message,
    }


def save_streamed_answer(
    db: Session,
    chat: Chat,
    message: str,
    answer: str,
    confidence: float,
    sources: List[Dict[str, Any]],
    category: str,
    is_emergency: bool = False,
) -> Dict[str, Any]:
    return _finalize_chat(db, chat, message, answer, confidence, sources, category, is_emergency)


def stream_tokens(question: str, docs: List[Dict[str, Any]]) -> Generator[str, None, None]:
    """Yield answer tokens (Ollama stream or extractive chunks)."""
    yield from rag_pipeline.stream_answer(question, docs)
