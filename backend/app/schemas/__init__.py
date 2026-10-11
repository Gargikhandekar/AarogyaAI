"""Pydantic request/response schemas."""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("Password must include at least one uppercase letter and one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    photo_url: Optional[str] = None
    is_admin: bool = False
    theme: str = "light"
    font_size: str = "medium"
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    photo_url: Optional[str] = None
    theme: Optional[str] = None
    font_size: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=8, max_length=128)


class ProfileStats(BaseModel):
    total_chats: int
    total_messages: int
    favorite_count: int
    member_since: datetime


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    chat_id: Optional[int] = None
    category: Optional[str] = None
    stream: bool = False


class SourceDocument(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None
    source: Optional[str] = None
    score: float = 0.0


class ChatResponse(BaseModel):
    chat_id: int
    message_id: int
    answer: str
    confidence: float
    sources: List[SourceDocument] = []
    category: Optional[str] = None
    is_emergency: bool = False
    disclaimer: str
    timestamp: datetime


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[Any] = None
    confidence: Optional[float] = None
    category: Optional[str] = None
    is_emergency: bool = False
    feedback: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatOut(BaseModel):
    id: int
    title: str
    category: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class ChatDetail(ChatOut):
    messages: List[MessageOut] = []


class ChatRename(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class FeedbackRequest(BaseModel):
    feedback: str = Field(..., pattern="^(like|dislike|none)$")


# ── Tools ────────────────────────────────────────────────────────────────────

class BMIRequest(BaseModel):
    height_cm: float = Field(..., gt=50, lt=300)
    weight_kg: float = Field(..., gt=10, lt=500)


class BMIResponse(BaseModel):
    bmi: float
    category: str
    advice: str


class SymptomCheckRequest(BaseModel):
    symptoms: List[str] = Field(..., min_length=1, max_length=20)
    duration_days: Optional[int] = None
    severity: Optional[str] = "moderate"


class ReminderCreate(BaseModel):
    medicine_name: str = Field(..., min_length=1, max_length=255)
    dosage: str = Field(..., min_length=1, max_length=120)
    schedule_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    notes: Optional[str] = None


class ReminderOut(BaseModel):
    id: int
    medicine_name: str
    dosage: str
    schedule_time: str
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class VoiceRequest(BaseModel):
    text: Optional[str] = None
    language: str = "en"


class HealthTip(BaseModel):
    tip: str
    category: str
    date: str


class HospitalPlaceholder(BaseModel):
    name: str
    address: str
    phone: str
    distance_km: float
    specialties: List[str]


class AdminStats(BaseModel):
    total_users: int
    total_chats: int
    total_messages: int
    total_documents: int
    emergency_flags: int
    active_users_today: int


class Message(BaseModel):
    detail: str


TokenResponse.model_rebuild()
