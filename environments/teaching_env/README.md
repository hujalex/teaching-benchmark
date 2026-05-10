# teaching-env

### Overview
- **Environment ID**: `teaching-env`
- **Short description**: Evaluates LLM explanations of textbook excerpts across pedagogy dimensions including concept coverage, coherence, prerequisite ordering, and originality.
- **Tags**: single-turn, teaching, pedagogy, nlp, train, eval

---

## Quickstart

### 1. Install

```bash
pip install -e .
# spaCy model (downloaded automatically on first run, or manually:)
python -m spacy download en_core_web_sm
```

### 2. Run an evaluation

```bash
# Default: 5 examples, 3 rollouts each
prime eval run teaching-env

# Specify model, scale, and sampling
prime eval run teaching-env \
  --model openai/gpt-4.1-mini \
  --num-examples 20 \
  --rollouts-per-example 3 \
  --max-tokens 1024 \
  --temperature 0.7
```

### 3. Run the test suite

```bash
# Fast metric-only tests (no model needed, ~1s)
pytest tests/test_adversarial.py -v -m "not slow"

# Full adversarial suite including NLI + embedder (~5 min first run)
pytest tests/test_adversarial.py -v
```

---

## Sample Task

**System prompt:**
```
You are an expert tutor. Read the textbook excerpt provided and explain the concept
clearly to a student with no prior knowledge of the topic. Introduce prerequisite
ideas before the main concept, use at least one concrete example, and connect each
idea to the next with explicit reasoning.
```

**User message (source excerpt):**
```
Before understanding force, one must first grasp the concept of mass — the measure
of an object's resistance to acceleration. Newton's second law of motion states that
the net force acting on an object equals its mass multiplied by its acceleration:
F = ma. Force is measured in Newtons (N), mass in kilograms (kg), and acceleration
in metres per second squared (m/s²). For example, a 2 kg object subjected to a 10 N
force accelerates at 5 m/s².
```

---

## Sample Rollout

**Model response (gpt-4.1-mini, reward = 0.82):**
```
To understand Newton's second law, we first need to know what mass is.

Mass is a measure of how much matter an object contains, and more practically,
how hard it is to get the object moving or to stop it. A bowling ball has much
more mass than a tennis ball — it takes a lot more effort to throw.

Force is a push or a pull. When you kick a soccer ball, your foot applies a force
to the ball. Force is measured in Newtons (N).

Acceleration is the rate at which an object's speed changes. Step on a car's gas
pedal and the car accelerates — its speed increases.

Newton's second law connects all three: F = ma. The net force on an object equals
its mass times its acceleration.

Concrete example: a 2 kg book is pushed across a table with a 10 N force.
  acceleration = F / m = 10 N / 2 kg = 5 m/s²
If we doubled the force to 20 N, the acceleration would double to 10 m/s².
If instead we doubled the mass to 4 kg and kept the force at 10 N, the acceleration
would halve to 2.5 m/s².

So the law tells us two things: more force produces more acceleration, and more mass
produces less acceleration for the same force.
```

---

## Sample Grader Output

```json
{
  "concept_coverage":    0.92,
  "sentence_coverage":   0.81,
  "contradiction":       0.97,
  "entailment_chain":    0.84,
  "order":               1.00,
  "example_grounding":   1.00,
  "information_density": 0.61,
  "readability_curve":   0.73,
  "originality":         0.78,
  "copy_rate":           0.31,
  "composite":           0.82
}
```

**Score interpretation:**

| Score | What it means |
|---|---|
| `concept_coverage = 0.92` | mass, force, acceleration, and F=ma all appear in the response |
| `contradiction = 0.97` | response does not contradict source claims |
| `order = 1.00` | mass introduced before force, prerequisites respected |
| `example_grounding = 1.00` | at least one concrete numerical example present |
| `entailment_chain = 0.84` | most consecutive sentences follow logically from the previous |
| `originality = 0.78` | response is largely paraphrased rather than copied |
| `copy_rate = 0.31` | only 31% of response sentences closely match a source sentence |
| `composite = 0.82` | weighted average (passes threshold of 0.75) |

---

## Metrics

| Metric | Weight (physics) | Meaning |
|---|---|---|
| `concept_coverage` | 0.20 | Fraction of KG concepts present in the response (word-boundary matched) |
| `sentence_coverage` | 0.14 | Semantic similarity: how much of the source each response sentence covers |
| `contradiction` | 0.22 | Absence of NLI-detected contradictions between source and response |
| `entailment_chain` | 0.20 | Logical coherence of consecutive response sentences |
| `order` | 0.13 | Prerequisite concepts introduced before dependent concepts |
| `example_grounding` | 0.06 | Presence of concrete examples with quantitative anchors or named entities |
| `information_density` | 0.02 | Content word density (signal-to-noise) |
| `readability_curve` | 0.01 | Gradual increase in sentence complexity across the explanation |
| `originality` | 0.02 | Paraphrase distance from source (ROUGE-based, penalises verbatim copying) |

Subject-specific weight profiles are applied automatically from `metadata["subject"]`. Supported subjects: `math`, `chemistry`, `physics`, `biology`, `computer_science`, `business`, `humanities`. The default profile is used when no subject is provided.

### Copy penalty

A multiplicative penalty is applied to the composite when `copy_rate` exceeds 0.90:

```
copy_penalty = max(0, (copy_rate - 0.90) / 0.10)
composite    = composite × (1 − copy_penalty × 0.50)
```

A verbatim copy (`copy_rate ≈ 1.0`) halves the composite regardless of other scores.

---

## Datasets

- **Primary dataset**: Curated textbook excerpts in `data/` covering math, physics, chemistry, biology, CS, business, and humanities.
- **Formats**: Markdown, PDF, slideshow, and plain text — parsed and cleaned via `parsing.py`.
- **KG generation**: Knowledge graphs (concepts + prerequisite edges) are auto-generated per excerpt using fastembed embeddings and keyword extraction.

---

## Environment Arguments

This environment takes no user-facing arguments. Dataset, KG, and subject-weight profiles are loaded automatically.

---

## Known Limitations

- **Numerical contradictions**: NLI models frequently fail to flag wrong numbers (e.g., "20 m/s²" vs "5 m/s²") because the sentence structure is identical. A dedicated numerical-consistency pass is not yet implemented.
- **Humanities grounding**: `example_grounding` is STEM-shaped (detects numbers/entities/code) and under-detects entity-free vivid prose — the primary mode of humanities teaching examples.
- **KG quality**: `concept_coverage` and `order` are only as good as the auto-generated KG. Noisy source text (PDF extraction artifacts) can produce noisy concepts; `_is_valid_concept()` filters the worst cases.
- **RL suitability**: Validated for offline evaluation. Not yet validated for online RL training — length gaming and adversarial NLI evasion are untested exploit vectors.
