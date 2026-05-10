# teaching-env

### Overview
- **Environment ID**: `teaching-env`
- **Short description**: Evaluates LLM explanations of textbook excerpts across pedagogy dimensions including concept coverage, coherence, prerequisite ordering, and originality.
- **Tags**: single-turn, teaching, pedagogy, nlp, train, eval

### Datasets
- **Primary dataset(s)**: Curated textbook excerpts covering math, physics, chemistry, biology, business, CS, and humanities topics stored in `data/`.
- **Source links**: Local dataset parsed from `data/` directory (markdown, PDF, slideshow, and textbook formats).
- **Split sizes**: Train and eval split from the same curated dataset.

### Task
- **Type**: single-turn
- **Output format expectations**: Plain text explanation written for a student with no prior knowledge of the topic.
- **Rubric overview**: Composite score from nine pedagogy-focused reward functions (see Metrics below). Subject-specific weight profiles are applied automatically based on the topic's academic domain.

### Quickstart
Run an evaluation with default settings:

```bash
prime eval run teaching-env
```

Configure model and sampling:

```bash
prime eval run teaching-env \
  -m openai/gpt-4.1-mini \
  -n 20 -r 3 -t 1024 -T 0.7
```

### Environment Arguments

This environment takes no user-facing arguments. The dataset and subject-weight profiles are loaded automatically.

### Metrics

| Metric | Meaning |
| ------ | ------- |
| `reward` | Weighted composite of all nine pedagogy scores |
| `concept_coverage` | Fraction of key concepts from the source text present in the response |
| `sentence_coverage` | Semantic coverage of source sentences in the response |
| `contradiction` | Absence of factual contradictions with the source text |
| `entailment_chain` | Logical coherence of reasoning steps |
| `order` | Prerequisite concepts introduced before dependent ones |
| `example_grounding` | Presence and quality of concrete examples |
| `information_density` | Signal-to-noise ratio of the response |
| `readability_curve` | Gradual increase in complexity across the explanation |
| `originality` | Degree of paraphrasing rather than verbatim copying from source |
