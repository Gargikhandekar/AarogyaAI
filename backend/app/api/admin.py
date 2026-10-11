"""Admin panel endpoints."""

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_admin
from app.database import get_db
from app.models import AppLog, Chat, MedicalDocument, Message, User
from app.schemas import AdminStats, UserOut
from app.utils.helpers import logger
import json

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/dashboard", response_model=AdminStats)
def dashboard(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())
    active_today = (
        db.query(func.count(func.distinct(Chat.user_id)))
        .filter(Chat.updated_at >= start)
        .scalar()
        or 0
    )
    return AdminStats(
        total_users=db.query(User).count(),
        total_chats=db.query(Chat).count(),
        total_messages=db.query(Message).count(),
        total_documents=db.query(MedicalDocument).count(),
        emergency_flags=db.query(Message).filter(Message.is_emergency.is_(True)).count(),
        active_users_today=active_today,
    )


@router.get("/users", response_model=List[UserOut])
def users(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return [UserOut.model_validate(u) for u in db.query(User).order_by(User.created_at.desc()).all()]


@router.get("/chats")
def chats(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    rows = db.query(Chat).order_by(Chat.updated_at.desc()).limit(100).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "user_id": c.user_id,
            "category": c.category,
            "updated_at": c.updated_at,
            "messages": len(c.messages),
        }
        for c in rows
    ]


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    # Messages per day for last 7 days
    days = []
    for i in range(6, -1, -1):
        day = (datetime.utcnow() - timedelta(days=i)).date()
        start = datetime.combine(day, datetime.min.time())
        end = start + timedelta(days=1)
        count = db.query(Message).filter(Message.created_at >= start, Message.created_at < end).count()
        days.append({"date": day.isoformat(), "messages": count})

    categories = (
        db.query(Chat.category, func.count(Chat.id))
        .group_by(Chat.category)
        .all()
    )
    return {
        "messages_per_day": days,
        "chats_by_category": [{"category": c or "Uncategorized", "count": n} for c, n in categories],
    }


@router.post("/dataset/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    raw = await file.read()
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"detail": f"Invalid JSON: {exc}"}

    inserted = 0
    if isinstance(data, list):
        for item in data:
            q = str(item.get("question", "")).strip()
            a = str(item.get("answer", "")).strip()
            if not q or not a:
                continue
            doc = MedicalDocument(
                question=q,
                answer=a,
                category=item.get("category"),
                source=item.get("source", "Upload"),
                source_url=item.get("source_url"),
            )
            db.add(doc)
            inserted += 1
        db.commit()

    log = AppLog(level="INFO", message=f"Admin uploaded {inserted} documents", user_id=admin.id)
    db.add(log)
    db.commit()
    logger.info("Admin %s uploaded %s docs", admin.email, inserted)
    return {"detail": f"Uploaded {inserted} documents. Rebuild FAISS index to include them in RAG."}


@router.get("/logs")
def logs(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    rows = db.query(AppLog).order_by(AppLog.created_at.desc()).limit(100).all()
    return [
        {"id": r.id, "level": r.level, "message": r.message, "user_id": r.user_id, "created_at": r.created_at}
        for r in rows
    ]
