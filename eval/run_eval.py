"""Evaluate retrieval and answer quality on the held-out MedQuAD questions.

Retrieval only (no LLM needed, ~1 minute with TF-IDF):
    python eval/run_eval.py --chunk-sizes 500 1000 0

Calibrate the decline threshold on the dev split:
    python eval/run_eval.py --split dev --chunk-sizes 1000

Answer quality with Ollama (needs the models pulled; slow on CPU):
    python eval/run_eval.py --chunk-sizes 500 1000 --models llama3.1:8b qwen2.5:7b

Metrics
- hit@k (exact):  the gold MedQuAD answer is among the top-k chunks.
- hit@k (topic):  some chunk from the gold answer's document (same disease/topic) is in the
                  top-k. MedQuAD has many near-identical questions per topic ("symptoms of X",
                  "treatment for X"), so this shows whether we found the right page.
- MRR:            mean reciprocal rank of the gold answer (exact), 0 if outside top-k.
- kept / declined: share of in-domain questions answered and of out-of-domain questions
                  declined by the relevance gate at the configured threshold.
- faithful:       LLM-as-judge: are all claims in the answer supported by the passages?
                  1 = fully, 0.5 = partially, 0 = not. Averaged over answered questions.
- cited:          share of answers containing at least one valid [n] citation.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from langchain_core.language_models import BaseChatModel  # noqa: E402
from langchain_core.output_parsers import JsonOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402

from app.rag.llm import build_chat_model  # noqa: E402
from app.rag.pipeline import RAGPipeline  # noqa: E402
from app.rag.prompts import cited_numbers, format_context  # noqa: E402
from app.utils.config import Settings  # noqa: E402

KS = (1, 3, 5)
RESULTS_DIR = ROOT / "eval" / "results"

JUDGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You check whether a medical chatbot's answer is faithful to its source passages. "
            "An answer is faithful if every factual claim in it is stated in, or directly "
            "follows from, the passages. General safety advice such as 'see a doctor' does not "
            "count as a claim. Respond with JSON only: "
            '{{"verdict": "faithful" | "partially_faithful" | "unfaithful", '
            '"unsupported_claims": ["..."]}}',
        ),
        ("human", "PASSAGES:\n{context}\n\nANSWER:\n{answer}"),
    ]
)
VERDICT_SCORE = {"faithful": 1.0, "partially_faithful": 0.5, "unfaithful": 0.0}


def chunk_label(size: int) -> str:
    return "whole answer" if size == 0 else f"{size} chars"


# ── Retrieval ────────────────────────────────────────────────────────────────


@dataclass
class RetrievalRun:
    chunk_size: int
    num_chunks: int
    rows: List[dict]  # one per question, with rank and top score


def run_retrieval(pipeline: RAGPipeline, items: Sequence[dict], max_k: int) -> List[dict]:
    rows = []
    for item in items:
        scored = pipeline.retriever.search(item["question"], max_k)
        exact_rank = topic_rank = None
        for rank, (doc, _score) in enumerate(scored, 1):
            if exact_rank is None and doc.metadata.get("qa_id") == item.get("qa_id"):
                exact_rank = rank
            if topic_rank is None and doc.metadata.get("doc_id") == item.get("doc_id"):
                topic_rank = rank
        rows.append(
            {
                **item,
                "top_score": scored[0][1] if scored else 0.0,
                "exact_rank": exact_rank,
                "topic_rank": topic_rank,
            }
        )
    return rows


def retrieval_metrics(rows: List[dict], threshold: float) -> Dict[str, float]:
    inside = [r for r in rows if r["expected"] == "answer"]
    outside = [r for r in rows if r["expected"] == "decline"]
    m: Dict[str, float] = {}
    for k in KS:
        m[f"hit@{k}"] = mean(r["exact_rank"] is not None and r["exact_rank"] <= k for r in inside)
        m[f"topic@{k}"] = mean(r["topic_rank"] is not None and r["topic_rank"] <= k for r in inside)
    m["mrr"] = mean(1 / r["exact_rank"] if r["exact_rank"] else 0.0 for r in inside)
    m["kept"] = mean(r["top_score"] >= threshold for r in inside)
    m["declined"] = mean(r["top_score"] < threshold for r in outside) if outside else float("nan")
    return m


def best_threshold(rows: List[dict]) -> float:
    """Threshold that maximises balanced accuracy of keep (in-domain) vs decline (OOD)."""
    inside = [r["top_score"] for r in rows if r["expected"] == "answer"]
    outside = [r["top_score"] for r in rows if r["expected"] == "decline"]
    candidates = sorted(set(inside + outside))
    best, best_acc = 0.0, -1.0
    for i, t in enumerate(candidates):
        acc = mean(s >= t for s in inside) / 2 + mean(s < t for s in outside) / 2
        if acc > best_acc:
            # midpoint between this score and the one below generalises better than the edge
            best = round((t + candidates[i - 1]) / 2 if i else t, 3)
            best_acc = acc
    return best


# ── Generation + judge ───────────────────────────────────────────────────────


class AlwaysUp:
    """Ollama health stub: the eval checks the model once up front instead."""

    def status(self):
        return True, "ok"

    def mark_down(self, reason: str) -> None:
        raise RuntimeError(reason)


def run_generation(
    pipeline: RAGPipeline, judge: Optional[BaseChatModel], items: Sequence[dict]
) -> List[dict]:
    pipeline.llm_health = AlwaysUp()
    judge_chain = JUDGE_PROMPT | judge | JsonOutputParser() if judge else None
    rows = []
    for item in items:
        start = time.perf_counter()
        scored, early = pipeline.plan(item["question"])
        if early is None:
            text = pipeline._chain.invoke(pipeline._inputs(item["question"], scored)).strip()
            result = pipeline.finalize(text, scored)
        else:
            result = early
        row = {
            **item,
            "status": result.status,
            "answer": result.answer,
            "seconds": round(time.perf_counter() - start, 2),
            "cited": bool(cited_numbers(result.answer, len(scored))),
            "verdict": None,
        }
        if result.status == "answered" and judge_chain is not None:
            try:
                out = judge_chain.invoke(
                    {"context": format_context(scored), "answer": result.answer}
                )
                row["verdict"] = out.get("verdict")
                row["unsupported_claims"] = out.get("unsupported_claims", [])
            except Exception as exc:  # noqa: BLE001 - a malformed judge reply is recorded
                row["verdict"] = f"judge_error: {exc}"
        rows.append(row)
        print(f"  [{len(rows)}/{len(items)}] {row['status']:9} {row['verdict']} {row['question'][:60]}")
    return rows


def generation_metrics(rows: List[dict]) -> Dict[str, float]:
    inside = [r for r in rows if r["expected"] == "answer"]
    outside = [r for r in rows if r["expected"] == "decline"]
    answered = [r for r in inside if r["status"] == "answered"]
    judged = [VERDICT_SCORE[r["verdict"]] for r in answered if r["verdict"] in VERDICT_SCORE]
    return {
        "answered": mean(r["status"] == "answered" for r in inside),
        "faithful": mean(judged) if judged else float("nan"),
        "judged": len(judged),
        "cited": mean(r["cited"] for r in answered) if answered else float("nan"),
        "ood_declined": mean(r["status"] == "declined" for r in outside) if outside else float("nan"),
        "sec_per_answer": mean(r["seconds"] for r in answered) if answered else float("nan"),
    }


# ── Reporting ────────────────────────────────────────────────────────────────


def mean(values) -> float:
    values = [float(v) for v in values]
    return sum(values) / len(values) if values else float("nan")


def fmt(v) -> str:
    if isinstance(v, float):
        return "–" if v != v else f"{v:.2f}"
    return str(v)


def write_table(path: Path, header: List[str], rows: List[List]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path.with_suffix(".csv"), "w", newline="") as f:
        csv.writer(f).writerows([header, *rows])
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(fmt(c) for c in r) + " |" for r in rows]
    table = "\n".join(lines) + "\n"
    path.with_suffix(".md").write_text(table)
    return table


def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate AarogyaAI retrieval and answers.")
    ap.add_argument("--split", choices=["dev", "test"], default="test")
    ap.add_argument("--chunk-sizes", type=int, nargs="+", default=[500, 1000])
    ap.add_argument("--chunk-overlap-ratio", type=float, default=0.1)
    ap.add_argument("--retriever", choices=["tfidf", "faiss"], default="tfidf")
    ap.add_argument("--threshold", type=float, help="decline threshold (default: from config)")
    ap.add_argument("--models", nargs="*", default=[], help="Ollama models to compare")
    ap.add_argument("--judge-model", help="Ollama model used as judge (default: first model)")
    ap.add_argument("--limit", type=int, help="only the first N in-domain questions (smoke test)")
    args = ap.parse_args()

    items = [i for i in json.loads((ROOT / "eval" / "eval_set.json").read_text()) if i["split"] == args.split]
    if args.limit:
        inside = [i for i in items if i["expected"] == "answer"][: args.limit]
        items = inside + [i for i in items if i["expected"] == "decline"][: max(1, args.limit // 4)]
    tag = f"{args.split}_{args.retriever}"
    print(f"{len(items)} {args.split} questions, retriever={args.retriever}")

    retrieval_rows, generation_rows, raw = [], [], []
    for size in args.chunk_sizes:
        settings = Settings(
            RETRIEVER=args.retriever,
            CHUNK_SIZE=size,
            CHUNK_OVERLAP=int(size * args.chunk_overlap_ratio),
            FAISS_INDEX_DIR=f"vector_db/eval_{size}",
        )
        if args.threshold is not None:
            settings = settings.model_copy(
                update={"MIN_RELEVANCE_TFIDF": args.threshold, "MIN_RELEVANCE_FAISS": args.threshold}
            )
        threshold = settings.min_relevance
        pipeline = RAGPipeline(settings)
        t0 = time.perf_counter()
        pipeline.initialize()
        if not pipeline.ready:
            print(f"Could not build the index: {pipeline.error}", file=sys.stderr)
            return 1
        print(f"\nChunk size {chunk_label(size)}: {pipeline.num_chunks} chunks ({time.perf_counter() - t0:.0f}s)")

        rows = run_retrieval(pipeline, items, max(KS))
        m = retrieval_metrics(rows, threshold)
        suggested = best_threshold(rows)
        row = [chunk_label(size), pipeline.num_chunks]
        row += [m[f"hit@{k}"] for k in KS] + [m[f"topic@{k}"] for k in KS]
        row += [m["mrr"], threshold, m["kept"], m["declined"]]
        # Only suggest thresholds on dev: tuning on the test split would leak.
        retrieval_rows.append(row + [suggested] if args.split == "dev" else row)
        raw += [{"chunk_size": size, **r} for r in rows]

        for model in args.models:
            print(f"  Generating with {model} ...")
            settings_m = settings.model_copy(update={"OLLAMA_MODEL": model})
            gen_pipeline = RAGPipeline(settings_m, llm=build_chat_model(settings_m, model))
            gen_pipeline.retriever = pipeline.retriever
            judge_name = args.judge_model or args.models[0]
            judge = build_chat_model(settings_m, judge_name, format="json", temperature=0)
            rows_g = run_generation(gen_pipeline, judge, items)
            g = generation_metrics(rows_g)
            generation_rows.append(
                [model, chunk_label(size), judge_name, g["answered"], g["faithful"], g["judged"],
                 g["cited"], g["ood_declined"], g["sec_per_answer"]]
            )
            raw += [{"chunk_size": size, "model": model, **r} for r in rows_g]

    header = ["chunk size", "chunks"] + [f"hit@{k}" for k in KS] + [f"topic@{k}" for k in KS]
    header += ["MRR", "threshold", "in-domain kept", "OOD declined"]
    if args.split == "dev":
        header.append("best threshold (dev)")
    print("\nRetrieval\n" + write_table(RESULTS_DIR / f"retrieval_{tag}", header, retrieval_rows))
    if generation_rows:
        header = ["model", "chunk size", "judge", "answered", "faithful", "judged", "cited",
                  "OOD declined", "sec/answer"]
        print("Generation\n" + write_table(RESULTS_DIR / f"generation_{tag}", header, generation_rows))
    with open(RESULTS_DIR / f"raw_{tag}.jsonl", "w") as f:
        for r in raw:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
