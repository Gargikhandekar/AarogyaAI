"""Tools, voice, suggestions, and bonus feature endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import FavoriteResponse, MedicineReminder, Message, User
from app.schemas import (
    BMIRequest,
    BMIResponse,
    HealthTip,
    HospitalPlaceholder,
    ReminderCreate,
    ReminderOut,
    SymptomCheckRequest,
    VoiceRequest,
)
from app.services.tools_service import (
    MEDICAL_NEWS,
    calculate_bmi,
    nearby_hospitals_placeholder,
    simple_symptom_check,
    tip_of_the_day,
)
from app.utils.helpers import MEDICAL_CATEGORIES, SMART_SUGGESTIONS

router = APIRouter(prefix="/api", tags=["Tools"])


@router.get("/suggestions")
def suggestions():
    return {"suggestions": SMART_SUGGESTIONS}


@router.get("/categories")
def categories():
    return {"categories": MEDICAL_CATEGORIES}


@router.post("/bmi", response_model=BMIResponse)
def bmi(payload: BMIRequest, user: User = Depends(get_current_user)):
    return BMIResponse(**calculate_bmi(payload.height_cm, payload.weight_kg))


@router.post("/symptom-checker")
def symptom_checker(payload: SymptomCheckRequest, user: User = Depends(get_current_user)):
    return simple_symptom_check(payload.symptoms, payload.severity or "moderate")


@router.get("/health-tip", response_model=HealthTip)
def health_tip():
    return HealthTip(**tip_of_the_day())


@router.get("/hospitals", response_model=List[HospitalPlaceholder])
def hospitals(city: str = Query("Your City"), user: User = Depends(get_current_user)):
    return nearby_hospitals_placeholder(city)


@router.get("/news")
def news():
    return {"articles": MEDICAL_NEWS}


@router.post("/voice")
def voice(payload: VoiceRequest, user: User = Depends(get_current_user)):
    """
    Voice endpoint stub.
    Browser Web Speech API handles STT/TTS on the client.
    This endpoint echoes text for TTS clients that prefer server round-trip.
    """
    text = (payload.text or "").strip()
    return {
        "text": text,
        "language": payload.language,
        "note": "Use the browser SpeechRecognition / speechSynthesis APIs for real-time voice.",
    }


@router.post("/reminders", response_model=ReminderOut)
def create_reminder(
    payload: ReminderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rem = MedicineReminder(
        user_id=user.id,
        medicine_name=payload.medicine_name,
        dosage=payload.dosage,
        schedule_time=payload.schedule_time,
        notes=payload.notes,
    )
    db.add(rem)
    db.commit()
    db.refresh(rem)
    return ReminderOut.model_validate(rem)


@router.get("/reminders", response_model=List[ReminderOut])
def list_reminders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (
        db.query(MedicineReminder)
        .filter(MedicineReminder.user_id == user.id)
        .order_by(MedicineReminder.schedule_time)
        .all()
    )
    return [ReminderOut.model_validate(r) for r in rows]


@router.delete("/reminders/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rem = (
        db.query(MedicineReminder)
        .filter(MedicineReminder.id == reminder_id, MedicineReminder.user_id == user.id)
        .first()
    )
    if rem:
        db.delete(rem)
        db.commit()
    return {"detail": "Reminder deleted"}


@router.post("/favorites/{message_id}")
def add_favorite(message_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        return {"detail": "Message not found"}
    existing = (
        db.query(FavoriteResponse)
        .filter(FavoriteResponse.user_id == user.id, FavoriteResponse.message_id == message_id)
        .first()
    )
    if existing:
        return {"detail": "Already favorited"}
    fav = FavoriteResponse(user_id=user.id, message_id=message_id)
    db.add(fav)
    db.commit()
    return {"detail": "Saved to favorites"}
