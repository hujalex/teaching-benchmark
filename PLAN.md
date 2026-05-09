# Subject-Specific Metric Weight Plan

## Overview

The `TeachingVerifier` scores every response across eight metrics and combines them
into a single composite reward via a weighted sum. The default weights treat all
subjects equally. This plan defines subject-specific weight tables so that the
reward signal better reflects the kind of teaching quality that actually matters
for each discipline.

**Guiding principle:**

- **STEM subjects (math, chemistry, computer science)** — reward *logical
  correctness, structured reasoning, and prerequisite ordering* more heavily.
  Creativity and prose flow matter less than precision.
- **Narrative subjects (humanities)** — reward *coverage, concrete illustration,
  and accessible presentation* more heavily. Strict logical entailment is less
  critical than engagement and contextual richness.
- **Applied subjects (business)** — sit in between: practical examples and
  accessible language matter, but internal consistency and concept fidelity still
  count.

---

## Metric Definitions (from `TeachingVerifier.WEIGHTS`)

| Key | What it measures |
|-----|-----------------|
| `concept_coverage` | Fraction of knowledge-graph concepts mentioned in the response |
| `sentence_coverage` | Semantic coverage of the source text's key sentences |
| `contradiction` | Absence of contradictions between source and response |
| `entailment_chain` | Logical flow between consecutive response sentences |
| `order` | Prerequisite concepts introduced before dependent ones |
| `example_grounding` | Presence of concrete examples / illustrations |
| `information_density` | Ratio of informative tokens to total length |
| `readability_curve` | Sentence-complexity progression (simpler → more complex) |

---

## Default Weights (Baseline)

```python
WEIGHTS = {
    "concept_coverage":    0.20,
    "sentence_coverage":   0.20,
    "contradiction":       0.20,
    "entailment_chain":    0.18,
    "order":               0.10,
    "example_grounding":   0.01,
    "information_density": 0.10,
    "readability_curve":   0.01,
}
```

---

## Subject-Specific Weights

All rows sum to **1.00**.

---

### Math

Mathematical explanations must be logically watertight, follow strict prerequisite
order (e.g. limits before derivatives), and pack precise information into every
sentence. Readability scaffolding and example variety are helpful but secondary to
correctness and structure.

```python
MATH_WEIGHTS = {
    "concept_coverage":    0.22,  # every defined term must appear
    "sentence_coverage":   0.15,  # source fidelity matters less than correctness
    "contradiction":       0.22,  # mathematical contradictions are fatal
    "entailment_chain":    0.20,  # step-by-step logical flow is core
    "order":               0.12,  # prerequisite ordering is critical
    "example_grounding":   0.03,  # worked examples aid intuition
    "information_density": 0.05,  # conciseness valued but not over logic
    "readability_curve":   0.01,  # least critical for technical audiences
}
```

---

### Chemistry

Chemistry shares math's need for precision and prerequisite structure (atoms before
molecules, nomenclature before reactions), plus heavy reliance on factual accuracy.
Concrete examples (lab observations, reaction equations) are moderately important.

```python
CHEMISTRY_WEIGHTS = {
    "concept_coverage":    0.22,  # chemical nomenclature must be complete
    "sentence_coverage":   0.18,  # source material should be well covered
    "contradiction":       0.22,  # factual errors in chemistry are serious
    "entailment_chain":    0.18,  # mechanisms require logical sequence
    "order":               0.12,  # bonding → reactions prerequisite chain
    "example_grounding":   0.03,  # lab/reaction examples aid understanding
    "information_density": 0.04,  # precision over brevity
    "readability_curve":   0.01,  # technical audience, less critical
}
```

---

### Computer Science

CS values correctness and structured reasoning equally with math and chemistry, but
also benefits meaningfully from concrete examples (code snippets, pseudocode,
worked algorithms). Prerequisite order is important (data structures before
algorithms, syntax before semantics).

```python
COMPUTER_SCIENCE_WEIGHTS = {
    "concept_coverage":    0.20,  # all concepts must be defined
    "sentence_coverage":   0.15,  # less weight on source paraphrase
    "contradiction":       0.20,  # technical accuracy is non-negotiable
    "entailment_chain":    0.18,  # algorithm steps need logical flow
    "order":               0.12,  # prerequisite concepts scaffold understanding
    "example_grounding":   0.08,  # code examples are highly valued in CS
    "information_density": 0.05,  # precision matters, but clarity too
    "readability_curve":   0.02,  # slightly more than other STEM subjects
}
```

---

### Business

Business explanations blend analytical structure with practical storytelling.
Case studies and real-world examples are central to the pedagogy. Strict logical
entailment and rigid prerequisite ordering matter less; accessible, consistent
prose that illustrates practical application matters more.

```python
BUSINESS_WEIGHTS = {
    "concept_coverage":    0.18,  # concepts important but interpretation flexible
    "sentence_coverage":   0.18,  # reasonable source fidelity expected
    "contradiction":       0.16,  # consistency valued, context-dependency allowed
    "entailment_chain":    0.14,  # business logic admits non-linear flow
    "order":               0.10,  # some prerequisite order useful
    "example_grounding":   0.10,  # case studies are the primary teaching tool
    "information_density": 0.08,  # accessible language preferred over density
    "readability_curve":   0.06,  # progressive complexity aids engagement
}
```

---

### Humanities

Humanities (history, literature, philosophy, etc.) prioritise narrative completeness,
contextual richness, and accessible engagement over formal logic. A good humanities
explanation tells a story, grounds ideas in concrete events or texts, and gently
guides the reader from familiar to unfamiliar. Strict prerequisite ordering and tight
entailment chains are far less important than in STEM.

```python
HUMANITIES_WEIGHTS = {
    "concept_coverage":    0.14,  # interpretation matters more than completeness
    "sentence_coverage":   0.22,  # narrative completeness of the source is key
    "contradiction":       0.12,  # interpretive disagreement is often legitimate
    "entailment_chain":    0.10,  # narrative flow ≠ strict logical entailment
    "order":               0.06,  # thematic order is often non-linear
    "example_grounding":   0.14,  # anecdotes, events, and quotes are central
    "information_density": 0.06,  # richer, less dense prose is appropriate
    "readability_curve":   0.16,  # accessibility and progressive complexity are vital
}
```

---

### Physics

Physics demands the same logical rigor as math — derivations must follow step by
step, cause must precede effect, and contradictions invalidate an explanation.
Prerequisite order is critical (kinematics before dynamics, classical before
quantum). Thought experiments and physical intuition examples are valuable but
secondary to structural correctness.

```python
PHYSICS_WEIGHTS = {
    "concept_coverage":    0.22,  # every physical quantity and law must appear
    "sentence_coverage":   0.16,  # source fidelity matters less than correctness
    "contradiction":       0.22,  # contradicting a physical law is fatal
    "entailment_chain":    0.20,  # cause→effect and derivation steps are core
    "order":               0.12,  # prerequisite ordering critical (kinematics → dynamics)
    "example_grounding":   0.04,  # thought experiments and physical intuition helpful
    "information_density": 0.03,  # precision over brevity
    "readability_curve":   0.01,  # technical audience, least critical
}
```

---

### Biology

Biology is more descriptive than physics or math — processes, structures, and
organisms must be covered accurately but are explained narratively rather than
derived logically. Concept coverage is high-priority because biological terminology
is precise and extensive. Prerequisite order still matters (cell structure before
cellular processes, genetics before evolution), and concrete examples (organisms,
lab observations) meaningfully aid understanding.

```python
BIOLOGY_WEIGHTS = {
    "concept_coverage":    0.22,  # biological terminology is precise and extensive
    "sentence_coverage":   0.20,  # descriptive coverage of processes is important
    "contradiction":       0.18,  # factual accuracy matters for biological facts
    "entailment_chain":    0.14,  # less strict than physics/math; processes are narrative
    "order":               0.10,  # cell→organelle→process ordering matters
    "example_grounding":   0.08,  # organisms, lab examples, and case studies aid learning
    "information_density": 0.06,  # moderate density; descriptive prose acceptable
    "readability_curve":   0.02,  # slightly more important than pure STEM
}
```

---

## Summary Comparison Table

| Metric | Default | Math | Chemistry | Physics | Biology | CS | Business | Humanities |
|--------|---------|------|-----------|---------|---------|-----|----------|------------|
| `concept_coverage` | 0.20 | **0.22** | **0.22** | **0.22** | **0.22** | 0.20 | 0.18 | 0.14 |
| `sentence_coverage` | 0.20 | 0.15 | 0.18 | 0.16 | 0.20 | 0.15 | 0.18 | **0.22** |
| `contradiction` | 0.20 | **0.22** | **0.22** | **0.22** | 0.18 | 0.20 | 0.16 | 0.12 |
| `entailment_chain` | 0.18 | **0.20** | 0.18 | **0.20** | 0.14 | 0.18 | 0.14 | 0.10 |
| `order` | 0.10 | **0.12** | **0.12** | **0.12** | 0.10 | **0.12** | 0.10 | 0.06 |
| `example_grounding` | 0.01 | 0.03 | 0.03 | 0.04 | 0.08 | 0.08 | 0.10 | **0.14** |
| `information_density` | 0.10 | 0.05 | 0.04 | 0.03 | 0.06 | 0.05 | 0.08 | 0.06 |
| `readability_curve` | 0.01 | 0.01 | 0.01 | 0.01 | 0.02 | 0.02 | 0.06 | **0.16** |

Bold = highest value for that metric across all subjects.

---

## Implementation Notes

**Where to apply**: the subject label should live in `info["subject"]` (or be
derived from `info["topic"]`) in the dataset row.

**Routing sketch** — map subject → weight dict inside `score_all()` or the reward
function closure in `load_environment()`:

```python
SUBJECT_WEIGHTS = {
    "math":             MATH_WEIGHTS,
    "chemistry":        CHEMISTRY_WEIGHTS,
    "physics":          PHYSICS_WEIGHTS,
    "biology":          BIOLOGY_WEIGHTS,
    "computer_science": COMPUTER_SCIENCE_WEIGHTS,
    "business":         BUSINESS_WEIGHTS,
    "humanities":       HUMANITIES_WEIGHTS,
}

def composite(scores: dict, subject: str) -> float:
    weights = SUBJECT_WEIGHTS.get(subject, TeachingVerifier.WEIGHTS)
    return sum(scores[k] * weights[k] for k in weights)
```

**Validation**: after implementing, run `prime eval run teaching-env` split by
subject and compare mean composite scores against baseline to confirm sensible
reward distributions across disciplines.
