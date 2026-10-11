"""Sample the evaluation questions from MedQuAD (run once; the output is committed).

    python eval/build_eval_set.py

Writes eval/eval_set.json with two disjoint splits:
- dev:  used to calibrate the decline threshold (and anything else we tune)
- test: only used to report final numbers, never to tune

Each split has N MedQuAD questions (expected: "answer") from N different documents, plus
the hand-written out-of-domain questions in ood_questions.json (expected: "decline").
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "dataset" / "medquad.json")
    parser.add_argument("--per-split", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    pairs = json.loads(args.dataset.read_text(encoding="utf-8"))
    rng = random.Random(args.seed)
    rng.shuffle(pairs)

    # One question per document, so a split is not dominated by a single topic.
    picked, used_docs = [], set()
    for pair in pairs:
        if pair["doc_id"] not in used_docs:
            used_docs.add(pair["doc_id"])
            picked.append(pair)
        if len(picked) == 2 * args.per_split:
            break

    ood = json.loads((ROOT / "eval" / "ood_questions.json").read_text(encoding="utf-8"))
    items = []
    for split, chunk in (("dev", picked[: args.per_split]), ("test", picked[args.per_split :])):
        for p in chunk:
            items.append(
                {
                    "split": split,
                    "expected": "answer",
                    "question": p["question"],
                    "qa_id": p["qa_id"],
                    "doc_id": p["doc_id"],
                    "source": p["source"],
                    "qtype": p["qtype"],
                }
            )
        for q in ood[split]:
            items.append({"split": split, "expected": "decline", "question": q})

    out = ROOT / "eval" / "eval_set.json"
    out.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(items)} questions to {out}")


if __name__ == "__main__":
    main()
