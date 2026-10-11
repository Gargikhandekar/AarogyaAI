"""Rebuild the FAISS vector index from the dataset.

The index is a build artifact and is not committed to git. Run this after
cloning, or whenever the dataset or embedding model changes:

    python scripts/build_index.py

Writes vector_db/faiss_index.faiss and vector_db/documents.pkl.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.chdir(ROOT / "backend")  # settings use paths relative to backend/

from app.rag.pipeline import rag_pipeline  # noqa: E402


def main() -> int:
    vector_dir = ROOT / "vector_db"
    for name in ("faiss_index.faiss", "documents.pkl"):
        (vector_dir / name).unlink(missing_ok=True)

    rag_pipeline._load_documents()
    rag_pipeline._try_load_faiss()
    if not rag_pipeline._use_faiss:
        print("FAISS index was not built; see the warning above.", file=sys.stderr)
        return 1
    print(f"Indexed {rag_pipeline.index.ntotal} documents into {vector_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
