"""Download MedQuAD and convert it to the JSON format the app loads.

    python scripts/prepare_medquad.py            # clone + convert
    python scripts/prepare_medquad.py --src DIR  # convert an existing MedQuAD checkout

MedQuAD (Ben Abacha & Demner-Fushman, 2019; CC BY 4.0) has 47,457 question-answer
pairs from 12 NIH websites. Three MedlinePlus subsets ship without answers for
copyright reasons, so they are skipped here.

Writes dataset/medquad.json: a list of
    {qa_id, doc_id, question, answer, focus, qtype, source, source_url}
The raw checkout (dataset/raw/) and the JSON output are gitignored.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/abachaa/MedQuAD.git"
DEFAULT_SRC = ROOT / "dataset" / "raw" / "MedQuAD"
DEFAULT_OUT = ROOT / "dataset" / "medquad.json"


def clean_answer(text: str) -> str:
    """Collapse whitespace inside paragraphs but keep paragraph breaks for the splitter."""
    paragraphs = re.split(r"\n\s*\n", text.strip())
    return "\n\n".join(" ".join(p.split()) for p in paragraphs if p.strip())


def parse_file(path: Path) -> list[dict]:
    root = ET.parse(path).getroot()
    source = root.get("source", "")
    doc_id = f"{source}:{root.get('id')}"
    focus = (root.findtext("Focus") or "").strip()
    pairs = []
    for qa in root.iter("QAPair"):
        question_el = qa.find("Question")
        answer = clean_answer(qa.findtext("Answer") or "")
        if question_el is None or not answer:
            continue
        pairs.append(
            {
                "qa_id": f"{source}:{question_el.get('qid')}",
                "doc_id": doc_id,
                "question": " ".join((question_el.text or "").split()),
                "answer": answer,
                "focus": focus,
                "qtype": question_el.get("qtype", ""),
                "source": source,
                "source_url": root.get("url"),
            }
        )
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC, help="MedQuAD checkout")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output JSON file")
    args = parser.parse_args()

    if not args.src.exists():
        print(f"Cloning {REPO_URL} into {args.src} ...")
        args.src.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(args.src)], check=True)

    pairs: list[dict] = []
    seen: set[tuple[str, str]] = set()
    files = sorted(args.src.glob("*/*.xml"))
    if not files:
        print(f"No MedQuAD XML files found under {args.src}", file=sys.stderr)
        return 1
    for path in files:
        for pair in parse_file(path):
            key = (pair["question"].lower(), pair["answer"][:200].lower())
            if key not in seen:  # some answers appear in more than one collection
                seen.add(key)
                pairs.append(pair)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(pairs, ensure_ascii=False), encoding="utf-8")
    sources = sorted({p["source"] for p in pairs})
    print(f"Wrote {len(pairs)} Q&A pairs from {len(files)} files ({', '.join(sources)}) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
