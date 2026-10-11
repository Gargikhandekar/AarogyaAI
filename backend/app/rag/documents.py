"""Load the Q&A dataset and split answers into chunks for retrieval."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.utils.helpers import clean_text, infer_category


def clean_passage(text: str) -> str:
    """Collapse whitespace inside paragraphs but keep paragraph breaks for the splitter."""
    paragraphs = re.split(r"\n\s*\n", text.strip())
    return "\n\n".join(" ".join(p.split()) for p in paragraphs if p.strip())


def load_qa_pairs(path: Path) -> List[Dict[str, Any]]:
    """Read a JSON list of {question, answer, ...} records, dropping empties and duplicates."""
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}. Run `python scripts/prepare_medquad.py` "
            "or point DATASET_PATH at an existing JSON file."
        )
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    seen = set()
    pairs: List[Dict[str, Any]] = []
    for i, item in enumerate(raw):
        question = clean_text(str(item.get("question", "")))
        answer = clean_passage(str(item.get("answer", "")))
        if not question or not answer:
            continue
        key = (question.lower(), answer[:200].lower())
        if key in seen:
            continue
        seen.add(key)
        pairs.append(
            {
                "qa_id": str(item.get("qa_id") or i),
                "doc_id": str(item.get("doc_id") or item.get("qa_id") or i),
                "question": question,
                "answer": answer,
                "focus": item.get("focus") or "",
                "category": item.get("category") or infer_category(f"{question} {answer}"),
                "source": item.get("source", "unknown"),
                "source_url": item.get("source_url"),
            }
        )
    return pairs


def chunk_qa_pairs(
    pairs: List[Dict[str, Any]], chunk_size: int, chunk_overlap: int
) -> List[Document]:
    """Split each answer into overlapping chunks.

    Only the answer text is indexed, prefixed with the topic ("focus") so a chunk from the
    middle of a long answer still says what it is about. The question is kept as metadata;
    indexing it would let evaluation queries match their own question text verbatim.
    chunk_size=0 keeps each answer as a single chunk.
    """
    splitter = (
        RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if chunk_size > 0
        else None
    )
    chunks: List[Document] = []
    for pair in pairs:
        pieces = splitter.split_text(pair["answer"]) if splitter else [pair["answer"]]
        header = f"{pair['focus']}: " if pair["focus"] else ""
        for n, piece in enumerate(pieces):
            metadata = {k: v for k, v in pair.items() if k != "answer"}
            metadata["chunk"] = n
            chunks.append(Document(page_content=header + piece, metadata=metadata))
    return chunks
