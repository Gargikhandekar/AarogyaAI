"""Two interchangeable retrievers over the same chunks.

- TfidfRetriever: pure Python, no downloads. The default, and what CI uses.
- FaissRetriever: dense embeddings (sentence-transformers) in a LangChain FAISS store.

Both return (Document, score) pairs, highest score first, where score is a cosine
similarity. The two scales differ, so each has its own relevance threshold in config.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Protocol, Tuple

from langchain_core.documents import Document

from app.utils.helpers import logger

ScoredDocs = List[Tuple[Document, float]]

_TOKEN = re.compile(r"[a-z0-9]+")

# Function words that carry no topic. Without this list, "What is the capital of France?"
# matched medical answers on "what", "is" and "the".
STOPWORDS = frozenset(
    """a about above after again all also am an and any are as at be because been before
    being below between both but by can could did do does doing down during each few for
    from further had has have having he her here hers him his how i if in into is it its
    itself just me more most my no nor not of off on once only or other our out over own
    same she should so some such than that the their them then there these they this those
    through to too under until up very was we were what when where which while who whom why
    will with would you your yours tell know get much many""".split()
)


def tokenize(text: str) -> List[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in STOPWORDS]


class Retriever(Protocol):
    def search(self, query: str, k: int) -> ScoredDocs: ...


class TfidfRetriever:
    """TF-IDF with cosine similarity, using an inverted index so a query only touches
    chunks that share at least one term with it."""

    def __init__(self, chunks: List[Document]) -> None:
        self.chunks = chunks
        doc_freq: Counter = Counter()
        term_freqs: List[Counter] = []
        for chunk in chunks:
            tf = Counter(tokenize(chunk.page_content))
            term_freqs.append(tf)
            doc_freq.update(tf.keys())

        n = max(len(chunks), 1)
        self.idf: Dict[str, float] = {
            t: math.log((n + 1) / (df + 1)) + 1.0 for t, df in doc_freq.items()
        }
        # postings[term] = [(chunk index, tf-idf weight), ...]
        self.postings: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
        self.norms: List[float] = []
        for i, tf in enumerate(term_freqs):
            weights = {t: c * self.idf[t] for t, c in tf.items()}
            self.norms.append(math.sqrt(sum(w * w for w in weights.values())) or 1.0)
            for t, w in weights.items():
                self.postings[t].append((i, w))

    def search(self, query: str, k: int) -> ScoredDocs:
        q_tf = Counter(tokenize(query))
        q_weights = {t: c * self.idf[t] for t, c in q_tf.items() if t in self.idf}
        if not q_weights:
            return []
        q_norm = math.sqrt(sum(w * w for w in q_weights.values()))

        dots: Dict[int, float] = defaultdict(float)
        for t, qw in q_weights.items():
            for i, dw in self.postings[t]:
                dots[i] += qw * dw

        scored = sorted(
            ((dot / (q_norm * self.norms[i]), i) for i, dot in dots.items()), reverse=True
        )
        return [(self.chunks[i], round(score, 4)) for score, i in scored[:k]]


class FaissRetriever:
    """Dense retrieval: all-MiniLM-L6-v2 embeddings in a FAISS inner-product index.

    Vectors are L2-normalised, so inner product equals cosine similarity. The index is
    saved to disk with a manifest; it is rebuilt when the chunks or the model change.
    """

    def __init__(self, chunks: List[Document], embedding_model: str, index_dir: Path) -> None:
        from langchain_community.vectorstores import FAISS
        from langchain_community.vectorstores.utils import DistanceStrategy
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model, encode_kwargs={"normalize_embeddings": True}
        )
        fingerprint = _fingerprint(chunks, embedding_model)
        manifest = index_dir / "manifest.json"

        if manifest.exists() and json.loads(manifest.read_text()).get("fingerprint") == fingerprint:
            # The pickle inside is our own file, written by build_index.py / a previous run.
            self.store = FAISS.load_local(
                str(index_dir),
                embeddings,
                allow_dangerous_deserialization=True,
                distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT,
            )
            logger.info("Loaded FAISS index from %s", index_dir)
        else:
            logger.info("Building FAISS index for %s chunks (this can take minutes)", len(chunks))
            self.store = FAISS.from_documents(
                chunks, embeddings, distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT
            )
            index_dir.mkdir(parents=True, exist_ok=True)
            self.store.save_local(str(index_dir))
            manifest.write_text(json.dumps({"fingerprint": fingerprint, "chunks": len(chunks)}))
            logger.info("Saved FAISS index to %s", index_dir)

    def search(self, query: str, k: int) -> ScoredDocs:
        results = self.store.similarity_search_with_score(query, k=k)
        return [(doc, round(float(score), 4)) for doc, score in results]


def _fingerprint(chunks: List[Document], embedding_model: str) -> str:
    h = hashlib.sha256(embedding_model.encode())
    for c in chunks:
        h.update(c.page_content.encode())
    return h.hexdigest()
