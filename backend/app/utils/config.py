"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Aarogya AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-change-in-production-aarogya-ai-2024"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    DATABASE_URL: str = "sqlite:///./aarogya.db"

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 384

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "../vector_db/faiss_index"
    DATASET_PATH: str = "../dataset/medquad_sample.json"
    TOP_K_RETRIEVAL: int = 3
    SIMILARITY_THRESHOLD: float = 0.35

    RATE_LIMIT: str = "60/minute"

    ADMIN_EMAIL: str = "admin@aarogya.ai"
    ADMIN_PASSWORD: str = "Admin@12345"
    ADMIN_NAME: str = "Aarogya Admin"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
