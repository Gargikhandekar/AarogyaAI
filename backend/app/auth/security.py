"""Password hashing and JWT helpers."""

from datetime import datetime, timedelta
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.utils.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    # bcrypt has a 72-byte limit
    raw = password.encode("utf-8")[:72]
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    raw = plain_password.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(raw, hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str | int, extra: Optional[dict[str, Any]] = None) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
