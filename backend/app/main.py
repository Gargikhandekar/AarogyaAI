"""Aarogya AI FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.api import admin, auth, chat, profile, tools
from app.auth.security import hash_password
from app.database import SessionLocal, init_db
from app.models import User
from app.rag import rag_pipeline
from app.utils.config import get_settings
from app.utils.helpers import DISCLAIMER, logger

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])


def seed_admin() -> None:
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.ADMIN_EMAIL.lower()).first()
        if not existing:
            admin_user = User(
                name=settings.ADMIN_NAME,
                email=settings.ADMIN_EMAIL.lower(),
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()
            logger.info("Seeded admin user: %s", settings.ADMIN_EMAIL)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s…", settings.APP_NAME)
    init_db()
    seed_admin()
    # Warm RAG with safe TF-IDF first; optional FAISS/embeddings if the stack supports it
    try:
        rag_pipeline.initialize()
    except Exception as exc:  # noqa: BLE001
        logger.warning("RAG warm-up issue: %s", exc)
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title="Aarogya AI",
    description=(
        "Intelligent Medical Chatbot with RAG over MedQuAD. "
        f"{DISCLAIMER}"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(profile.router)
app.include_router(tools.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {
        "name": "Aarogya AI",
        "status": "ok",
        "disclaimer": DISCLAIMER,
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "rag_ready": rag_pipeline.ready,
        "documents": len(rag_pipeline.documents),
        "llm": settings.OLLAMA_MODEL,
    }


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
