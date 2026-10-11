"""Ollama access: a LangChain chat model with explicit timeouts, plus a cached health check."""

from __future__ import annotations

import time
from typing import Optional, Tuple

import httpx
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama

from app.utils.config import Settings


def build_chat_model(settings: Settings, model: Optional[str] = None, **overrides) -> BaseChatModel:
    timeout = httpx.Timeout(settings.LLM_READ_TIMEOUT, connect=settings.LLM_CONNECT_TIMEOUT)
    params = dict(
        model=model or settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=settings.LLM_TEMPERATURE,
        num_predict=settings.LLM_MAX_TOKENS,
        num_ctx=settings.LLM_NUM_CTX,
        keep_alive="30m",
        client_kwargs={"timeout": timeout},
    )
    return ChatOllama(**{**params, **overrides})


class OllamaHealth:
    """Checks that Ollama is up and the model is pulled. Results are cached for a short
    TTL: long enough not to add latency to every request, short enough that starting
    Ollama after the API is picked up without a restart."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._checked_at = 0.0
        self._status: Tuple[bool, str] = (False, "not checked yet")

    def status(self) -> Tuple[bool, str]:
        if time.monotonic() - self._checked_at < self.settings.LLM_HEALTH_TTL:
            return self._status
        self._status = self._probe()
        self._checked_at = time.monotonic()
        return self._status

    def mark_down(self, reason: str) -> None:
        self._status = (False, reason)
        self._checked_at = time.monotonic()

    def _probe(self) -> Tuple[bool, str]:
        url = f"{self.settings.OLLAMA_BASE_URL}/api/tags"
        try:
            resp = httpx.get(url, timeout=2.0)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            return False, f"Ollama is not reachable at {self.settings.OLLAMA_BASE_URL} ({exc})"
        model = self.settings.OLLAMA_MODEL
        names = {m.get("name", "") for m in resp.json().get("models", [])}
        # "llama3.1" matches "llama3.1:latest"
        if model not in names and f"{model}:latest" not in names:
            return False, f"Model '{model}' is not pulled. Run: ollama pull {model}"
        return True, "ok"
