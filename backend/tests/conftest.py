"""Shared fixtures. Tests use the small hand-written sample and a fake LLM, so they need
no dataset download, no embedding model and no running Ollama."""

import os
import tempfile
from pathlib import Path

# Settings are read once at import time, so configure them before importing the app.
_tmp = Path(tempfile.mkdtemp(prefix="aarogya-tests-"))
os.environ.update(
    {
        "APP_ENV": "test",
        "DATABASE_URL": f"sqlite:///{_tmp / 'test.db'}",
        "DATASET_PATH": "dataset/sample_qa.json",
        "RETRIEVER": "tfidf",
        "CHUNK_SIZE": "0",
        "MIN_RELEVANCE_TFIDF": "0.15",
        "RATE_LIMIT": "1000/minute",
        "OLLAMA_BASE_URL": "http://127.0.0.1:9",  # nothing listens here
        "ADMIN_EMAIL": "",
        "ADMIN_PASSWORD": "",
    }
)

import itertools  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from langchain_core.language_models.fake_chat_models import FakeListChatModel  # noqa: E402

from app.main import app  # noqa: E402
from app.rag import rag_pipeline  # noqa: E402

_emails = itertools.count()


class FakeHealth:
    def __init__(self, ok: bool = True, detail: str = "ok"):
        self.ok, self.detail = ok, detail

    def status(self):
        return self.ok, self.detail

    def mark_down(self, reason: str) -> None:
        self.ok, self.detail = False, reason


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:  # runs the lifespan: DB tables + knowledge base
        yield c


@pytest.fixture
def auth(client):
    """Headers for a freshly registered user."""
    email = f"user{next(_emails)}@example.com"
    resp = client.post(
        "/api/auth/register", json={"name": "Test", "email": email, "password": "Passw0rdX"}
    )
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def fake_llm(client):
    """Install a fake chat model and a healthy Ollama status; restore afterwards."""
    original_llm, original_health = rag_pipeline.llm, rag_pipeline.llm_health

    def install(*responses: str, healthy: bool = True, model=None):
        rag_pipeline.use_llm(model or FakeListChatModel(responses=list(responses) or ["unused"]))
        rag_pipeline.llm_health = FakeHealth(ok=healthy, detail="ok" if healthy else "Ollama is down")

    yield install
    rag_pipeline.use_llm(original_llm)
    rag_pipeline.llm_health = original_health
