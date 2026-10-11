"""Build the FAISS vector index ahead of time.

The index is a build artifact and is not committed to git. With RETRIEVER=faiss the API
builds it on first start if it is missing or stale; this script does the same up front so
the first request is not slow:

    RETRIEVER=faiss python scripts/build_index.py

Needs backend/requirements-embeddings.txt. Writes to FAISS_INDEX_DIR (default vector_db/).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("RETRIEVER", "faiss")

from app.rag.pipeline import RAGPipeline  # noqa: E402


def main() -> int:
    pipeline = RAGPipeline()
    pipeline.initialize()
    if not pipeline.ready:
        print(f"Index was not built: {pipeline.error}", file=sys.stderr)
        return 1
    s = pipeline.settings
    print(
        f"{s.RETRIEVER} index ready: {pipeline.num_chunks} chunks "
        f"(chunk size {s.CHUNK_SIZE}) from {pipeline.num_pairs} Q&A pairs"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
