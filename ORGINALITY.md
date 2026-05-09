# Originality Metric

## Goal

Measure how much a model response **paraphrases and synthesises** the source text
versus merely copying it verbatim. A good teaching explanation covers all the key
ideas but expresses them in the model's own words — high n-gram overlap with the
source indicates shallow regurgitation, not genuine understanding.

---

## Why ROUGE?

ROUGE (Recall-Oriented Understudy for Gisting Evaluation) measures n-gram
overlap between two texts. Here we invert it: **high ROUGE = low originality**.

| ROUGE variant | What it captures |
|---------------|-----------------|
| ROUGE-1 | Unigram (word) overlap — surface vocabulary reuse |
| ROUGE-2 | Bigram overlap — phrase-level copying |
| ROUGE-L | Longest common subsequence — structural sentence copying |

ROUGE-2 and ROUGE-L are the most diagnostic: a model that just shuffles words
will score low on ROUGE-2 even if ROUGE-1 stays high, and ROUGE-L catches
verbatim sentence fragments regardless of word order.

---

## Metric Definition

```
originality = 1 - rouge_combined(source, completion)

rouge_combined = w1 * R1_precision + w2 * R2_precision + wL * RL_precision
```

**Precision** (not recall) is the right direction: we care about what fraction of
the *completion*'s n-grams were copied from the source, not how much of the source
was covered (that is `sentence_coverage`'s job).

Default weights:

```python
ROUGE_WEIGHTS = {"rouge1": 0.20, "rouge2": 0.50, "rougeL": 0.30}
```

ROUGE-2 dominates because bigram copying is the clearest signal of verbatim
regurgitation without being thrown off by shared single words (articles, prepositions).

---

## Score Interpretation

| `originality` | Interpretation |
|---------------|---------------|
| 0.85 – 1.00 | Highly original — model explains in its own words |
| 0.65 – 0.84 | Moderate originality — some paraphrasing, some lifting |
| 0.40 – 0.64 | Heavy copying — response is largely a restatement |
| < 0.40 | Near-verbatim — little to no synthesis |

A floor of ~0.50 is expected even for genuinely original responses because
technical terminology (e.g., "Newton's second law", "kinetic energy") must reuse
source vocabulary.

---

## Interaction With Existing Metrics

Originality does **not** replace `sentence_coverage`; the two are complementary
and intentionally in tension:

- `sentence_coverage` (semantic): rewards *covering* the source ideas
- `originality` (lexical): rewards *rephrasing* rather than copying them

A model that scores high on both has understood and synthesised the material.
A model that scores high on `sentence_coverage` but low on `originality` is
paraphrasing by swapping synonyms. A model that scores high on `originality` but
low on `sentence_coverage` is going off-topic.

---

## Implementation

### 1. New module — `verifier/originality.py`

```python
from rouge_score import rouge_scorer

_SCORER = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)

ROUGE_WEIGHTS = {"rouge1": 0.20, "rouge2": 0.50, "rougeL": 0.30}


def compute(source: str, completion: str) -> float:
    """Return originality in [0, 1]. Higher = more original phrasing."""
    if not completion.strip():
        return 0.0
    scores = _SCORER.score(source, completion)
    # Use precision: fraction of completion n-grams that came from source
    rouge_combined = sum(
        scores[k].precision * w for k, w in ROUGE_WEIGHTS.items()
    )
    return round(1.0 - rouge_combined, 4)
```

### 2. Register in `verifier/__init__.py`

```python
from . import originality
```

### 3. Wire into `TeachingVerifier.score_all`

Add the call alongside existing metrics:

```python
scores = {
    ...existing metrics...,
    "originality": originality.compute(source_text, completion),
}
```

### 4. Add to `WEIGHTS` (zero weight initially)

```python
WEIGHTS = {
    ...existing keys...,
    "originality": 0.00,   # metric-only until validated
}
```

Keep it at zero weight during the first eval run so it appears in rollout logs
without shifting the composite reward. Promote it to a positive weight once the
score distribution is understood.

### 5. Expose as a metric in `teaching_env.py`

The existing `_make_metric` loop reads from `state["teaching_scores"]`, so no
extra code is needed — adding `"originality"` to `WEIGHTS` automatically creates
the zero-weight metric function.

---

## Subject-Specific Considerations

| Subject | Expected natural originality | Notes |
|---------|------------------------------|-------|
| Math | Lower (~0.55–0.70) | Notation and definitions are fixed vocabulary |
| Chemistry | Lower (~0.55–0.70) | Chemical names and formulae must be copied |
| CS | Moderate (~0.65–0.75) | Code terms fixed; explanations can vary |
| Business | Higher (~0.70–0.85) | Flexible vocabulary; many equivalent phrasings |
| Humanities | Higher (~0.70–0.85) | Narrative language is highly paraphrasable |

These baselines should be calibrated empirically on the first eval run before
assigning subject-specific weights.

---

## Dependency

```toml
# pyproject.toml
dependencies = [
    ...
    "rouge-score>=0.1.2",
]
```

`rouge-score` is pure-Python with no heavy ML dependencies — it adds negligible
install time and no GPU requirement.

---

## Validation Plan

1. Run `prime eval run teaching-env` with `originality` at weight `0` and inspect
   the distribution of raw scores per subject.
2. Spot-check low-scoring responses manually to confirm they are genuinely
   verbatim copies (not just technical-vocabulary-heavy explanations).
3. Tune `ROUGE_WEIGHTS` if needed — increase `rouge2` weight if ROUGE-1 is noisy
   due to shared terminology.
4. Set a subject-specific floor (e.g., `max(raw_score, FLOOR[subject])`) to avoid
   penalising unavoidable terminology reuse.
5. Promote to positive weight (suggested 0.05–0.10) once calibration is complete,
   and update `SUBJECT_WEIGHTS` accordingly.
