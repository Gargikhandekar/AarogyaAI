"""Application settings loaded from environment variables (and an optional .env file).

Every tunable lives here; see .env.example in the project root for documentation.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/utils/config.py -> project root is three levels above backend/app/utils
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_SECRET_KEY = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Aarogya AI"
    APP_ENV: Literal["development", "production", "test"] = "development"
    DEBUG: bool = False
    SECRET_KEY: str = DEFAULT_SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    DATABASE_URL: str = "sqlite:///./aarogya.db"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    RATE_LIMIT: str = "60/minute"

    # Only seeded when both are set, so no default admin password ships with the code.
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""
    ADMIN_NAME: str = "Aarogya Admin"

    # --- LLM (Ollama) ---
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 512
    LLM_NUM_CTX: int = 4096
    LLM_CONNECT_TIMEOUT: float = 5.0  # seconds to open a connection to Ollama
    LLM_READ_TIMEOUT: float = 120.0  # max seconds to wait between streamed tokens
    LLM_HEALTH_TTL: float = 30.0  # seconds to cache an Ollama up/down check

    # --- Retrieval ---
    DATASET_PATH: str = "dataset/medquad.json"
    RETRIEVER: Literal["tfidf", "faiss"] = "tfidf"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    FAISS_INDEX_DIR: str = "vector_db"
    CHUNK_SIZE: int = 1000  # characters; 0 disables chunking (one chunk per answer)
    CHUNK_OVERLAP: int = 100
    TOP_K_RETRIEVAL: int = 4
    # Below this top score the bot declines instead of answering. The right value depends
    # on the retriever (TF-IDF cosine vs embedding cosine); calibrate it with eval/.
    MIN_RELEVANCE_TFIDF: float = 0.15
    MIN_RELEVANCE_FAISS: float = 0.45

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def min_relevance(self) -> float:
        return self.MIN_RELEVANCE_FAISS if self.RETRIEVER == "faiss" else self.MIN_RELEVANCE_TFIDF

    @property
    def dataset_path(self) -> Path:
        return resolve_path(self.DATASET_PATH)

    @property
    def faiss_index_dir(self) -> Path:
        return resolve_path(self.FAISS_INDEX_DIR)

    def check_production_safety(self) -> None:
        """Refuse to run in production with development defaults."""
        if self.APP_ENV != "production":
            return
        if self.SECRET_KEY == DEFAULT_SECRET_KEY or len(self.SECRET_KEY) < 32:
            raise RuntimeError("Set a random SECRET_KEY (32+ chars) before running in production.")
        if self.DEBUG:
            raise RuntimeError("DEBUG must be false in production.")


def resolve_path(value: str) -> Path:
    """Relative paths are resolved against the project root, not the current directory."""
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
