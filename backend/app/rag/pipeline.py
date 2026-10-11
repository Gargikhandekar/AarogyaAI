"""RAG pipeline: retrieve MedQuAD passages -> relevance gate -> cited answer from Ollama.

Flow for one question:
1. retrieve():   top-k chunks with cosine scores (TF-IDF or FAISS).
2. relevance:    if the best score is below the threshold, decline without calling the LLM.
3. generate:     the LLM answers from the numbered passages and cites them as [n].
4. sources:      the passages are returned with a `cited` flag; if the model itself says
                 the passages do not answer the question, that counts as a decline.
If Ollama is down or times out, the user gets the top passages verbatim with a clear note.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Tuple

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser

from app.rag.documents import chunk_qa_pairs, load_qa_pairs
from app.rag.llm import OllamaHealth, build_chat_model
from app.rag.prompts import NO_ANSWER, RAG_PROMPT, cited_numbers, format_context, is_refusal
from app.rag.retrievers import FaissRetriever, Retriever, ScoredDocs, TfidfRetriever
from app.utils.config import Settings, get_settings
from app.utils.helpers import logger

DECLINE_MESSAGE = (
    f"{NO_ANSWER} My knowledge base (MedQuAD) has nothing closely related to your question. "
    "Try naming the condition, symptom or medicine, or ask a healthcare professional."
)

FALLBACK_PREFIX = "> ⚠️ The answer generator is unavailable"


class KnowledgeBaseUnavailable(RuntimeError):
    """The dataset or index failed to load, so no question can be answered."""


@dataclass
class RAGResult:
    answer: str
    status: str  # "answered" | "declined" | "fallback"
    top_score: float
    sources: List[Dict[str, Any]] = field(default_factory=list)


class RAGPipeline:
    def __init__(self, settings: Optional[Settings] = None, llm: Optional[BaseChatModel] = None):
        self.settings = settings or get_settings()
        self.retriever: Optional[Retriever] = None
        self.num_pairs = 0
        self.num_chunks = 0
        self.error: Optional[str] = "not initialised"
        self.llm_health = OllamaHealth(self.settings)
        self.use_llm(llm or build_chat_model(self.settings))

    def use_llm(self, llm: BaseChatModel) -> None:
        """Swap the chat model (tests use a fake one; eval compares Ollama models)."""
        self.llm = llm
        self._chain = RAG_PROMPT | llm | StrOutputParser()

    # ── Setup ────────────────────────────────────────────────────────────────

    @property
    def ready(self) -> bool:
        return self.retriever is not None

    def initialize(self) -> None:
        s = self.settings
        try:
            pairs = load_qa_pairs(s.dataset_path)
            chunks = chunk_qa_pairs(pairs, s.CHUNK_SIZE, s.CHUNK_OVERLAP)
            if s.RETRIEVER == "faiss":
                self.retriever = FaissRetriever(chunks, s.EMBEDDING_MODEL, s.faiss_index_dir)
            else:
                self.retriever = TfidfRetriever(chunks)
            self.num_pairs, self.num_chunks = len(pairs), len(chunks)
            self.error = None
            logger.info(
                "Knowledge base ready: %s Q&A pairs, %s chunks, %s retriever",
                len(pairs), len(chunks), s.RETRIEVER,
            )
        except Exception as exc:  # noqa: BLE001 - reported via /api/health and 503s
            self.retriever = None
            self.error = str(exc)
            logger.error("Knowledge base failed to load: %s", exc)

    # ── Retrieval ────────────────────────────────────────────────────────────

    def retrieve(self, question: str) -> ScoredDocs:
        if self.retriever is None:
            raise KnowledgeBaseUnavailable(self.error or "knowledge base not loaded")
        return self.retriever.search(question, self.settings.TOP_K_RETRIEVAL)

    def is_relevant(self, scored: ScoredDocs) -> bool:
        return bool(scored) and scored[0][1] >= self.settings.min_relevance

    # ── Generation ───────────────────────────────────────────────────────────

    def plan(self, question: str) -> Tuple[ScoredDocs, Optional[RAGResult]]:
        """Retrieve, then decide whether the LLM is needed.

        Returns (passages, early_result). early_result is set when no generation is needed:
        a decline (nothing relevant) or the extractive fallback (Ollama unavailable).
        Raises KnowledgeBaseUnavailable.
        """
        scored = self.retrieve(question)
        if not self.is_relevant(scored):
            top = scored[0][1] if scored else 0.0
            return scored, RAGResult(DECLINE_MESSAGE, "declined", top)
        ok, reason = self.llm_health.status()
        if not ok:
            return scored, self._fallback(scored, reason)
        return scored, None

    def answer(self, question: str) -> RAGResult:
        """Non-streaming answer. Raises KnowledgeBaseUnavailable."""
        scored, early = self.plan(question)
        if early:
            return early
        try:
            text = self._chain.invoke(self._inputs(question, scored)).strip()
        except Exception as exc:  # noqa: BLE001 - timeouts, connection errors, bad model
            return self._llm_failed(exc, scored)
        return self.finalize(text, scored)

    def stream(self, question: str, scored: ScoredDocs) -> Iterator[str]:
        """Yield LLM tokens for passages that plan() approved; call finalize() afterwards."""
        emitted = False
        try:
            for token in self._chain.stream(self._inputs(question, scored)):
                emitted = True
                yield token
        except Exception as exc:  # noqa: BLE001
            fallback = self._llm_failed(exc, scored)
            if emitted:
                yield "\n\n_(Answer cut off: the connection to Ollama failed.)_"
            else:
                yield fallback.answer

    def finalize(self, text: str, scored: ScoredDocs) -> RAGResult:
        top = scored[0][1] if scored else 0.0
        if is_refusal(text):
            return RAGResult(DECLINE_MESSAGE, "declined", top)
        cited = cited_numbers(text, len(scored))
        status = "fallback" if text.startswith(FALLBACK_PREFIX) else "answered"
        return RAGResult(text, status, top, self.sources(scored, cited))

    def _llm_failed(self, exc: Exception, scored: ScoredDocs) -> RAGResult:
        self.llm_health.mark_down(f"Ollama request failed: {exc}")
        logger.warning("LLM generation failed: %s", exc)
        return self._fallback(scored, f"the request to Ollama failed ({type(exc).__name__})")

    def _fallback(self, scored: ScoredDocs, reason: str) -> RAGResult:
        """Extractive answer used when the LLM is unavailable."""
        shown = scored[:2]
        lines = [
            f"{FALLBACK_PREFIX} ({reason}), so here are the most relevant MedQuAD "
            "passages, quoted directly.\n"
        ]
        for n, (doc, _score) in enumerate(shown, 1):
            lines.append(f"**[{n}] {doc.metadata.get('question', '')}**\n\n{doc.page_content}\n")
        cited = set(range(1, len(shown) + 1))
        return RAGResult("\n".join(lines), "fallback", scored[0][1], self.sources(shown, cited))

    @staticmethod
    def _inputs(question: str, scored: ScoredDocs) -> Dict[str, str]:
        return {"question": question, "context": format_context(scored)}

    @staticmethod
    def sources(scored: ScoredDocs, cited: set) -> List[Dict[str, Any]]:
        return [
            {
                "id": n,
                "question": doc.metadata.get("question", ""),
                "answer": doc.page_content[:600],
                "category": doc.metadata.get("category"),
                "source": doc.metadata.get("source"),
                "source_url": doc.metadata.get("source_url"),
                "score": float(score),
                "cited": n in cited,
            }
            for n, (doc, score) in enumerate(scored, 1)
        ]


rag_pipeline = RAGPipeline()
