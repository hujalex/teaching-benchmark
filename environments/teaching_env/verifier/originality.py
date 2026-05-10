from rouge_score import rouge_scorer

_SCORER = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)

ROUGE_WEIGHTS = {"rouge1": 0.10, "rouge2": 0.50, "rougeL": 0.40}


def compute(source: str, completion: str) -> float:
    """Return originality in [0, 1]. Higher = more original phrasing."""
    if not completion.strip():
        return 0.0
    scores = _SCORER.score(source, completion)
    rouge_combined = sum(scores[k].precision * w for k, w in ROUGE_WEIGHTS.items())
    return round(1.0 - rouge_combined, 4)
