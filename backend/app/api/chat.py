"""Chat and history endpoints."""

from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Chat, Message, User
from app.schemas import (
    ChatDetail,
    ChatOut,
    ChatRename,
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    MessageOut,
    SourceDocument,
)
from app.services import chat_service
from app.utils.helpers import DISCLAIMER

router = APIRouter(prefix="/api", tags=["Chat"])


def _chat_out(chat: Chat) -> ChatOut:
    return ChatOut(
        id=chat.id,
        title=chat.title,
        category=chat.category,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        message_count=len(chat.messages) if chat.messages is not None else 0,
    )


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    result = chat_service.process_chat(
        db=db,
        user=user,
        message=payload.message.strip(),
        chat_id=payload.chat_id,
        category=payload.category,
    )
    return ChatResponse(
        chat_id=result["chat_id"],
        message_id=result["message_id"],
        answer=result["answer"],
        confidence=result["confidence"],
        sources=[SourceDocument(**s) for s in result["sources"]],
        category=result["category"],
        is_emergency=result["is_emergency"],
        disclaimer=result["disclaimer"],
        timestamp=result["timestamp"],
    )


@router.post("/chat/stream")
async def chat_stream(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """True token streaming from Ollama (or fast extractive fallback)."""
    prepared = chat_service.prepare_stream_chat(
        db=db,
        user=user,
        message=payload.message.strip(),
        chat_id=payload.chat_id,
        category=payload.category,
    )
    chat_obj: Chat = prepared["chat"]
    chat_id = chat_obj.id

    def event_generator():
        # Re-bind session work inside generator carefully — use fresh session for final save
        from app.database import SessionLocal

        meta = {
            "type": "meta",
            "chat_id": chat_id,
            "message_id": None,
            "confidence": prepared["confidence"],
            "sources": prepared["sources"],
            "category": prepared["category"],
            "is_emergency": prepared["is_emergency"],
            "disclaimer": DISCLAIMER,
        }
        yield f"data: {json.dumps(meta)}\n\n"

        chunks: list[str] = []
        if prepared["is_emergency"]:
            answer = prepared["answer"]
            step = 28
            for i in range(0, len(answer), step):
                part = answer[i : i + step]
                chunks.append(part)
                yield f"data: {json.dumps({'type': 'token', 'content': part})}\n\n"
        else:
            for token in chat_service.stream_tokens(prepared["message"], prepared["docs"]):
                chunks.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        full_answer = "".join(chunks)
        db_local = SessionLocal()
        try:
            chat_row = db_local.query(Chat).filter(Chat.id == chat_id).first()
            saved = chat_service.save_streamed_answer(
                db=db_local,
                chat=chat_row,
                message=prepared["message"],
                answer=full_answer,
                confidence=prepared["confidence"],
                sources=prepared["sources"],
                category=prepared["category"],
                is_emergency=prepared["is_emergency"],
            )
            yield f"data: {json.dumps({'type': 'done', 'message_id': saved['message_id']})}\n\n"
        finally:
            db_local.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history", response_model=List[ChatOut])
def history(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chats = chat_service.list_chats(db, user, search)
    return [_chat_out(c) for c in chats]


@router.get("/history/{chat_id}", response_model=ChatDetail)
def history_detail(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = chat_service.get_chat_detail(db, user, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages = []
    for m in chat.messages:
        sources = None
        if m.sources:
            try:
                sources = json.loads(m.sources)
            except json.JSONDecodeError:
                sources = None
        messages.append(
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=sources,
                confidence=m.confidence,
                category=m.category,
                is_emergency=m.is_emergency,
                feedback=m.feedback,
                created_at=m.created_at,
            )
        )
    base = _chat_out(chat)
    return ChatDetail(**base.model_dump(), messages=messages)


@router.put("/history/{chat_id}", response_model=ChatOut)
def rename(chat_id: int, payload: ChatRename, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = chat_service.rename_chat(db, user, chat_id, payload.title.strip())
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return _chat_out(chat)


@router.delete("/history/{chat_id}")
def delete_one(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ok = chat_service.delete_chat(db, user, chat_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"detail": "Chat deleted"}


@router.delete("/history")
def delete_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = chat_service.delete_all_chats(db, user)
    return {"detail": f"Deleted {count} chats"}


@router.post("/messages/{message_id}/feedback")
def feedback(
    message_id: int,
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    msg = chat_service.set_feedback(db, user, message_id, payload.feedback)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"detail": "Feedback saved", "feedback": msg.feedback}
