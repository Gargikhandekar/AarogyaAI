"""Prompt for grounded, cited answers."""

from __future__ import annotations

import re
from typing import List, Set, Tuple

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

# The model is told to reply with exactly this when the passages do not answer the
# question, so the API and the evaluation can detect a refusal reliably.
NO_ANSWER = "I don't have enough information in my sources to answer that."

SYSTEM_PROMPT = f"""You are Aarogya AI, a medical education assistant.
Answer the user's question using ONLY the numbered passages below. They come from
MedQuAD, a collection of question-answer pairs from NIH websites.

Rules:
- Every factual sentence must end with the number of the passage it came from, like [1] or [2][3].
- Do not add facts, drugs, doses or conditions that are not in the passages.
- If the passages do not answer the question, reply with exactly: "{NO_ANSWER}"
- Do not diagnose the user or tell them which treatment to take.
- Be concise: at most about 150 words, plain language, Markdown bullets where helpful.

Passages:
{{context}}"""

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", "{question}")]
)

_CITATION = re.compile(r"\[(\d+)\]")


def format_context(scored: List[Tuple[Document, float]]) -> str:
    blocks = []
    for n, (doc, _score) in enumerate(scored, 1):
        title = doc.metadata.get("question", "")
        blocks.append(f"[{n}] ({title})\n{doc.page_content}")
    return "\n\n".join(blocks)


def cited_numbers(answer: str, max_n: int) -> Set[int]:
    """Passage numbers the answer actually cites, ignoring out-of-range numbers."""
    return {int(m) for m in _CITATION.findall(answer) if 1 <= int(m) <= max_n}


def is_refusal(answer: str) -> bool:
    return NO_ANSWER.lower().rstrip(".") in answer.lower()
