"""RAG pipeline: embeddings/FAISS when available, pure-Python retrieval fallback."""

from __future__ import annotations

import json
import math
import pickle
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.utils.config import get_settings
from app.utils.helpers import DISCLAIMER, clean_text, infer_category, logger

settings = get_settings()

RAG_SYSTEM_PROMPT = """You are Aarogya AI, a careful and empathetic medical education assistant.
Rules:
1. Answer the USER QUESTION directly using ONLY the provided Context.
2. If Context is weakly related, say you have limited matching information and give cautious general guidance only from Context.
3. Do NOT invent unrelated conditions, drugs, or dosages.
4. Do NOT mix in topics that are not in the Context.
5. Prefer clear Markdown with short sections (What it may mean / Self-care / When to seek care).
6. End by reminding the user this is educational and not a substitute for professional care.
"""

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return _TOKEN.findall(text.lower())


class PurePythonIndex:
    """Lightweight TF-IDF index that does not require NumPy/FAISS/Torch."""

    def __init__(self, documents: List[Dict[str, Any]]) -> None:
        self.documents = documents
        self.doc_tokens: List[List[str]] = []
        self.doc_tf: List[Counter] = []
        self.idf: Dict[str, float] = {}
        self._build()

    def _build(self) -> None:
        df: Counter = Counter()
        for doc in self.documents:
            tokens = _tokenize(f"{doc['question']} {doc['answer']}")
            self.doc_tokens.append(tokens)
            tf = Counter(tokens)
            self.doc_tf.append(tf)
            for term in tf:
                df[term] += 1
        n = max(len(self.documents), 1)
        self.idf = {t: math.log((n + 1) / (df_t + 1)) + 1.0 for t, df_t in df.items()}

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []
        q_tf = Counter(q_tokens)
        q_norm = math.sqrt(sum((q_tf[t] * self.idf.get(t, 0.0)) ** 2 for t in q_tf)) or 1.0

        scored: List[Tuple[float, int]] = []
        for i, tf in enumerate(self.doc_tf):
            score = 0.0
            for t, qv in q_tf.items():
                if t in tf:
                    idf = self.idf.get(t, 0.0)
                    score += (qv * idf) * (tf[t] * idf)
            d_norm = math.sqrt(sum((tf[t] * self.idf.get(t, 0.0)) ** 2 for t in tf)) or 1.0
            cosine = score / (q_norm * d_norm)
            if cosine > 0:
                scored.append((cosine, i))

        scored.sort(reverse=True)
        results = []
        for score, idx in scored[:top_k]:
            doc = dict(self.documents[idx])
            doc["score"] = round(float(score), 4)
            results.append(doc)
        return results


class RAGPipeline:
    """Retrieval-Augmented Generation for medical Q&A."""

    def __init__(self) -> None:
        self.settings = settings
        self.embedder = None
        self.index = None
        self.python_index: Optional[PurePythonIndex] = None
        self.documents: List[Dict[str, Any]] = []
        self._ready = False
        self._use_faiss = False
        self._llm_available: Optional[bool] = None

    @property
    def ready(self) -> bool:
        return self._ready

    def initialize(self) -> None:
        try:
            self._load_documents()
            self.python_index = PurePythonIndex(self.documents)
            self._ready = bool(self.documents)
            logger.info(
                "RAG ready with %s documents (TF-IDF fallback active)",
                len(self.documents),
            )
            # Optional FAISS: enable with ENABLE_FAISS=true (can crash on some Win/Py3.13 builds)
            import os

            if os.getenv("ENABLE_FAISS", "false").lower() in {"1", "true", "yes"}:
                self._try_load_faiss()
        except Exception as exc:  # noqa: BLE001
            logger.exception("RAG initialization failed: %s", exc)
            self._ready = bool(self.documents)

    def _project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    def _find_dataset(self) -> Optional[Path]:
        root = self._project_root()
        candidates = [
            Path(self.settings.DATASET_PATH),
            Path.cwd() / self.settings.DATASET_PATH,
            root / "dataset" / "medquad_sample.json",
            Path.cwd().parent / "dataset" / "medquad_sample.json",
        ]
        for c in candidates:
            try:
                if c.exists():
                    return c
            except OSError:
                continue
        return None

    def _load_documents(self) -> None:
        dataset_path = self._find_dataset()
        if dataset_path is None:
            raise FileNotFoundError("MedQuAD sample dataset not found")
        with open(dataset_path, encoding="utf-8") as f:
            raw = json.load(f)
        self.documents = self._preprocess(raw)
        logger.info("Loaded %s MedQuAD documents from %s", len(self.documents), dataset_path)

    def _preprocess(self, raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        docs: List[Dict[str, Any]] = []
        for item in raw:
            q = clean_text(str(item.get("question", "")))
            a = clean_text(str(item.get("answer", "")))
            if not q or not a:
                continue
            key = q.lower()
            if key in seen:
                continue
            seen.add(key)
            category = item.get("category") or infer_category(q + " " + a)
            docs.append(
                {
                    "question": q,
                    "answer": a,
                    "category": category,
                    "source": item.get("source", "MedQuAD"),
                    "source_url": item.get("source_url"),
                }
            )
        return docs

    def _try_load_faiss(self) -> None:
        """Best-effort FAISS load. Safe to skip on unsupported Python/OS builds."""
        try:
            import faiss  # noqa: F401
            import numpy as np  # noqa: F401
            from sentence_transformers import SentenceTransformer  # noqa: F401
        except Exception as exc:  # noqa: BLE001
            logger.warning("Embedding stack unavailable (%s). Using TF-IDF retrieval.", exc)
            return

        vector_dir = self._project_root() / "vector_db"
        vector_dir.mkdir(parents=True, exist_ok=True)
        index_path = vector_dir / "faiss_index.faiss"
        docs_path = vector_dir / "documents.pkl"

        try:
            if index_path.exists() and docs_path.exists():
                self.index = faiss.read_index(str(index_path))
                with open(docs_path, "rb") as f:
                    stored = pickle.load(f)
                if len(stored) == len(self.documents):
                    self.documents = stored
                    self.python_index = PurePythonIndex(self.documents)
                    self._use_faiss = True
                    logger.info("Loaded FAISS index (%s vectors)", self.index.ntotal)
                    return

            logger.info("Building FAISS index for %s documents…", len(self.documents))
            self.embedder = SentenceTransformer(self.settings.EMBEDDING_MODEL)
            texts = [f"Q: {d['question']}\nA: {d['answer']}" for d in self.documents]
            embeddings = self.embedder.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            embeddings = np.asarray(embeddings, dtype=np.float32)
            faiss.normalize_L2(embeddings)
            self.index = faiss.IndexFlatIP(embeddings.shape[1])
            self.index.add(embeddings)
            faiss.write_index(self.index, str(index_path))
            with open(docs_path, "wb") as f:
                pickle.dump(self.documents, f)
            self._use_faiss = True
            logger.info("FAISS index saved to %s", index_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("FAISS build skipped (%s). TF-IDF remains active.", exc)
            self.index = None
            self._use_faiss = False

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        if not self.documents:
            return []
        k = top_k or self.settings.TOP_K_RETRIEVAL

        if self._use_faiss and self.index is not None:
            try:
                return self._faiss_retrieve(query, k)
            except Exception as exc:  # noqa: BLE001
                logger.warning("FAISS retrieve failed (%s); falling back to TF-IDF", exc)

        if self.python_index is None:
            self.python_index = PurePythonIndex(self.documents)
        results = self.python_index.search(query, k)
        return [r for r in results if r["score"] >= min(0.05, self.settings.SIMILARITY_THRESHOLD)]

    def _faiss_retrieve(self, query: str, k: int) -> List[Dict[str, Any]]:
        import faiss
        import numpy as np

        if self.embedder is None:
            from sentence_transformers import SentenceTransformer

            self.embedder = SentenceTransformer(self.settings.EMBEDDING_MODEL)

        vec = self.embedder.encode([clean_text(query)], convert_to_numpy=True)
        vec = np.asarray(vec, dtype=np.float32)
        faiss.normalize_L2(vec)
        scores, indices = self.index.search(vec, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue
            if float(score) < self.settings.SIMILARITY_THRESHOLD:
                continue
            doc = dict(self.documents[idx])
            doc["score"] = float(score)
            results.append(doc)
        return results

    def _check_ollama(self) -> bool:
        if self._llm_available is not None:
            return self._llm_available
        try:
            import httpx

            r = httpx.get(f"{self.settings.OLLAMA_BASE_URL}/api/tags", timeout=2.0)
            self._llm_available = r.status_code == 200
        except Exception:  # noqa: BLE001
            self._llm_available = False
        return self._llm_available

    def _build_prompt(self, question: str, context_docs: List[Dict[str, Any]]) -> str:
        context_blocks = []
        for i, d in enumerate(context_docs[:3], 1):
            answer = d["answer"][:420]
            context_blocks.append(
                f"[{i}] {d.get('source', 'MedQuAD')}\nQ: {d['question']}\nA: {answer}"
            )
        context = "\n\n".join(context_blocks) if context_blocks else "No relevant documents found."
        return (
            f"{RAG_SYSTEM_PROMPT}\n\n"
            f"### Context\n{context}\n\n"
            f"### User Question\n{question}\n\n"
            f"Answer in concise Markdown (max ~180 words). Use only relevant Context.\n\n"
            f"### Answer\n"
        )

    def _ollama_options(self) -> Dict[str, Any]:
        return {
            "temperature": min(self.settings.LLM_TEMPERATURE, 0.2),
            "num_predict": self.settings.LLM_MAX_TOKENS,
            "top_p": 0.9,
            "num_ctx": 2048,
        }

    def _generate_with_ollama(self, question: str, context_docs: List[Dict[str, Any]]) -> str:
        import httpx

        payload = {
            "model": self.settings.OLLAMA_MODEL,
            "prompt": self._build_prompt(question, context_docs),
            "stream": False,
            "keep_alive": "30m",
            "options": self._ollama_options(),
        }
        with httpx.Client(timeout=90.0) as client:
            resp = client.post(f"{self.settings.OLLAMA_BASE_URL}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "").strip()

    def stream_answer(self, question: str, context_docs: List[Dict[str, Any]]):
        """Yield tokens as they arrive from Ollama, or chunked extractive fallback."""
        if not self._check_ollama() or not context_docs:
            text = self._generate_extractive(question, context_docs)
            step = 28
            for i in range(0, len(text), step):
                yield text[i : i + step]
            return

        import httpx

        payload = {
            "model": self.settings.OLLAMA_MODEL,
            "prompt": self._build_prompt(question, context_docs),
            "stream": True,
            "keep_alive": "30m",
            "options": self._ollama_options(),
        }
        full: List[str] = []
        try:
            with httpx.Client(timeout=90.0) as client:
                with client.stream(
                    "POST", f"{self.settings.OLLAMA_BASE_URL}/api/generate", json=payload
                ) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        token = data.get("response") or ""
                        if token:
                            full.append(token)
                            yield token
                        if data.get("done"):
                            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("Ollama stream failed (%s); extractive fallback", exc)
            self._llm_available = False
            text = self._generate_extractive(question, context_docs)
            step = 28
            for i in range(0, len(text), step):
                yield text[i : i + step]
            return

        joined = "".join(full).strip()
        if joined and DISCLAIMER.lower() not in joined.lower():
            yield f"\n\n---\n*{DISCLAIMER}*"

    def _generate_extractive(self, question: str, context_docs: List[Dict[str, Any]]) -> str:
        if not context_docs or float(context_docs[0].get("score", 0)) < 0.08:
            return (
                "I couldn't find a close match in the medical knowledge base for that question. "
                "Please try rephrasing (for example: symptoms, duration, or the condition name), "
                "or consult a licensed healthcare professional.\n\n"
                f"*{DISCLAIMER}*"
            )

        top = context_docs[0]
        others = context_docs[1:3]
        parts = [
            "### Based on medical knowledge related to your question\n\n",
            f"**Related topic:** {top['question']}\n\n",
            f"{top['answer']}\n",
        ]
        if others:
            parts.append("\n### Additional related information\n\n")
            for d in others:
                snippet = d["answer"][:280] + ("…" if len(d["answer"]) > 280 else "")
                parts.append(f"- **{d['question']}**: {snippet}\n")
        parts.append(
            "\n> **Note:** Answer synthesized from retrieved MedQuAD documents. "
            "For personalized advice, please see a doctor.\n"
        )
        parts.append(f"\n*{DISCLAIMER}*")
        return "".join(parts)

    def answer(self, question: str) -> Tuple[str, float, List[Dict[str, Any]], str]:
        category = infer_category(question)
        docs = self.retrieve(question)
        confidence = float(docs[0]["score"]) if docs else 0.0

        if self._check_ollama() and docs:
            try:
                text = self._generate_with_ollama(question, docs)
                if DISCLAIMER.lower() not in text.lower():
                    text = f"{text}\n\n---\n*{DISCLAIMER}*"
            except Exception as exc:  # noqa: BLE001
                logger.warning("Ollama generation failed: %s", exc)
                self._llm_available = False
                text = self._generate_extractive(question, docs)
        else:
            text = self._generate_extractive(question, docs)

        return text, confidence, docs, category


rag_pipeline = RAGPipeline()
