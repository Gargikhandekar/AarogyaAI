"""Chat and history endpoints."""

from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import SessionLocal, get_db
from app.models import Chat, User
from app.schemas import (
    ChatDetail,
    ChatOut,
    ChatRename,
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    MessageOut,
)
from app.rag import KnowledgeBaseUnavailable, rag_pipeline
from app.services import chat_service
from app.utils.helpers import DISCLAIMER, logger

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


def _unavailable(exc: KnowledgeBaseUnavailable) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail=f"The medical knowledge base is not loaded, so I can't answer right now. ({exc})",
    )


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        result = chat_service.process_chat(
            db=db,
            user=user,
            message=payload.message.strip(),
            chat_id=payload.chat_id,
            category=payload.category,
        )
    except KnowledgeBaseUnavailable as exc:
        raise _unavailable(exc) from exc
    return ChatResponse(**result)


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


# A plain `def` (not async): retrieval, the DB and the LLM client are all blocking, so
# FastAPI runs this in a worker thread instead of stalling the event loop.
@router.post("/chat/stream")
def chat_stream(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Server-sent events: one `meta` event (sources), `token` events, then `done`."""
    try:
        prepared = chat_service.prepare_stream_chat(
            db=db,
            user=user,
            message=payload.message.strip(),
            chat_id=payload.chat_id,
            category=payload.category,
        )
    except KnowledgeBaseUnavailable as exc:
        raise _unavailable(exc) from exc

    def event_generator():
        yield _sse(
            {
                "type": "meta",
                "chat_id": prepared.chat_id,
                "status": prepared.early.status if prepared.early else "generating",
                "confidence": prepared.scored[0][1] if prepared.scored else 0.0,
                "sources": prepared.preview_sources,
                "category": prepared.category,
                "is_emergency": prepared.is_emergency,
                "disclaimer": DISCLAIMER,
            }
        )
        try:
            if prepared.early is not None:
                result = prepared.early
                yield _sse({"type": "token", "content": result.answer})
            else:
                chunks: list[str] = []
                for token in rag_pipeline.stream(prepared.message, prepared.scored):
                    chunks.append(token)
                    yield _sse({"type": "token", "content": token})
                result = rag_pipeline.finalize("".join(chunks).strip(), prepared.scored)

            # The request's session is closed once the response starts, so use a new one.
            with SessionLocal() as db_local:
                chat_row = db_local.get(Chat, prepared.chat_id)
                saved = chat_service.save_assistant_message(
                    db_local, chat_row, result, prepared.category, prepared.is_emergency
                )
            yield _sse(
                {
                    "type": "done",
                    "message_id": saved["message_id"],
                    "status": result.status,
                    "answer": result.answer,
                    "sources": result.sources,
                }
            )
        except Exception:  # noqa: BLE001 - the HTTP status is already sent; report in-band
            logger.exception("Streaming chat failed")
            yield _sse({"type": "error", "detail": "Something went wrong while answering."})

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
