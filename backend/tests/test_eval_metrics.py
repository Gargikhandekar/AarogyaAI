"""The evaluation numbers in the README come from these functions, so test the maths."""

from run_eval import best_threshold, retrieval_metrics


def row(expected, top_score, exact_rank=None, topic_rank=None):
    return {"expected": expected, "top_score": top_score,
            "exact_rank": exact_rank, "topic_rank": topic_rank}


ROWS = [
    row("answer", 0.8, exact_rank=1, topic_rank=1),
    row("answer", 0.6, exact_rank=3, topic_rank=1),
    row("answer", 0.5, exact_rank=None, topic_rank=2),
    row("answer", 0.3, exact_rank=None, topic_rank=None),
    row("decline", 0.2),
    row("decline", 0.4),
]


def test_hit_rates_and_mrr():
    m = retrieval_metrics(ROWS, threshold=0.45)
    assert m["hit@1"] == 0.25 and m["hit@3"] == 0.5 and m["hit@5"] == 0.5
    assert m["topic@1"] == 0.5 and m["topic@3"] == 0.75
    assert abs(m["mrr"] - (1 + 1 / 3) / 4) < 1e-9


def test_decline_rates_at_threshold():
    m = retrieval_metrics(ROWS, threshold=0.45)
    assert m["kept"] == 0.75  # 0.3 falls below the threshold
    assert m["declined"] == 1.0


def test_best_threshold_separates_the_classes():
    t = best_threshold(ROWS)
    assert 0.4 < t <= 0.5
