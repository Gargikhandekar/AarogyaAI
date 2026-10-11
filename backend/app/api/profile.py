"""Profile endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from sqlalchemy.orm import Session

from app.auth import get_current_user, hash_password, verify_password
from app.database import get_db
from app.models import Chat, FavoriteResponse, Message, User
from app.schemas import ProfileStats, ProfileUpdate, UserOut

router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.get("", response_model=UserOut)
def get_profile(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.put("", response_model=UserOut)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.name:
        user.name = payload.name.strip()
    if payload.photo_url is not None:
        user.photo_url = payload.photo_url
    if payload.theme:
        user.theme = payload.theme
    if payload.font_size:
        user.font_size = payload.font_size
    if payload.new_password:
        if not payload.current_password or not verify_password(payload.current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        user.hashed_password = hash_password(payload.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/stats", response_model=ProfileStats)
def stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total_chats = db.query(Chat).filter(Chat.user_id == user.id).count()
    total_messages = (
        db.query(Message).join(Chat).filter(Chat.user_id == user.id).count()
    )
    favorites = db.query(FavoriteResponse).filter(FavoriteResponse.user_id == user.id).count()
    return ProfileStats(
        total_chats=total_chats,
        total_messages=total_messages,
        favorite_count=favorites,
        member_since=user.created_at,
    )


@router.delete("")
def delete_account(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.delete(user)
    db.commit()
    return {"detail": "Account deleted"}


@router.get("/export")
def export_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Export chat history as a simple text download (PDF-ready content)."""
    chats = db.query(Chat).filter(Chat.user_id == user.id).order_by(Chat.updated_at.desc()).all()
    lines = [f"Aarogya AI Chat Export — {user.name}", f"Generated: {datetime.utcnow().isoformat()}Z", ""]
    for chat in chats:
        lines.append(f"## {chat.title} ({chat.updated_at.date()})")
        for m in chat.messages:
            lines.append(f"[{m.role.upper()}] {m.content}")
            lines.append("")
        lines.append("---")
    content = "\n".join(lines)
    buffer = BytesIO(content.encode("utf-8"))
    return StreamingResponse(
        buffer,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=aarogya_chat_export.txt"},
    )
