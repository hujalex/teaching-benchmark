# Benchmark Commercial Assessment & Roadmap

## Current Verdict

**Not sellable to AI labs yet. Credible as a technical demo. Promising as a seed.**

The concept is genuinely differentiated — "can a model teach from source material?" is a real problem labs care about, and no widely-adopted benchmark addresses it. The infrastructure (Verifiers/Prime environment shape, multi-dimensional reward, subject-specific weights, saved eval runs) is real work, not just a spec. But the repo reads as a prototype, not a product-grade benchmark.

---

## What Is Strong

- **Clear benchmark thesis**: source-grounded tutoring quality is underexplored. Coverage, contradiction, and entailment benchmarks exist in summarization and NLI literature, but teaching quality evaluation as an RL signal does not.
- **Prerequisite order metric**: the most novel piece. Measuring whether a model introduces concept A before concept B given a KG of dependencies has no direct precedent in existing NLG evaluation literature. This is the angle most worth investing in.
- **Subject-specific weighting**: the intuition that math explanations should weight logical entailment heavily while humanities should weight readability and example grounding reflects real pedagogical knowledge.
- **Multi-dimensional reward**: interpretable sub-scores alongside a composite reward is the right design for RL training — practitioners can diagnose failure modes rather than just watching composite reward move.
- **Saved eval runs**: shows the environment runs end-to-end, not just on paper.

---

## Technical Flaws That Undermine Credibility

### 1. KG Extraction Noise
Auto-extracted concepts include artifacts like `contractandnotpurchaseanyrice` from PDF conversion noise. Any concept extracted from garbled text corrupts every downstream metric that uses the KG (coverage, order). This needs to be fixed before scale, not after.

**Root cause**: keyword extractor runs on raw markdown before PDF conversion noise is cleaned. Fix: strip non-alphanumeric runs before extraction, add a minimum concept quality filter (e.g. drop concepts with similarity score below threshold or containing digit/punctuation runs).

### 2. Contradiction Scoring Uses Max, Not Min
`contradiction_detection.py` computes `scores.max(axis=1).mean()` — for each source sentence, it asks "does the completion say something compatible?" A model can write four contradictory sentences and one consistent one and score well. The metric should penalize the worst-case match, not reward the best-case.

**Fix**: replace `scores.max(axis=1).mean()` with a penalty-weighted formulation that flags when *any* completion sentence contradicts a source sentence.

### 3. Concept Coverage Uses Substring Matching
`concept_coverage.py:22` checks surface form substrings. Generic words extracted as concepts (e.g. "use", "model", "data") inflate scores for any response that uses common vocabulary. This is partly mitigated by the KG quality filter but needs to be addressed directly.

**Fix**: require embedding similarity between the concept mention in context and its canonical form, not just substring presence.

### 4. Reward Hacking Surface Is Large
A model trained on this reward can learn to: mention source keywords (boosts concept_coverage), write smooth flowing text (boosts entailment_chain), paraphrase source sentences (boosts sentence_coverage). None of these behaviors require actually teaching the concept. The metrics collectively do not guard against this failure mode.

**Fix**: adversarial validation cases (see roadmap below) are necessary to prove hack-resistance before the reward is used for RL training.

---

## Gaps That Would Kill a Sale

| Gap | Why It Matters |
|-----|---------------|
| No human validation | Without evidence that composite reward correlates with human judgments of teaching quality, the benchmark is a plausible hypothesis, not a validated tool |
| Dataset scale: ~34 markdown files | Demo scale, not lab benchmark scale. Frontier model evaluations need hundreds to thousands of examples |
| No model ladder results | No evidence the benchmark discriminates between weak, mid, and frontier models. If GPT-4o and a 7B model both score 0.85+, the benchmark has a ceiling problem |
| Eval history thin and uneven | 88 result rows, 8 unique examples, mean reward ~0.44, median ~0.61, some zero/error rows |
| Documentation thin | No dataset provenance, licensing, validation methodology, baselines, or failure mode documentation |

---

## Roadmap to Sellable

Priority order — each step is a prerequisite for the next.

### Step 1: Fix Technical Flaws (Before Anything Else)
- Strip PDF conversion noise before KG extraction
- Add concept quality filter (no non-alphanumeric runs, minimum length, minimum similarity score)
- Fix contradiction scoring to penalize worst-case rather than reward best-case
- Add adversarial test cases that the current metrics fail on — document these failures honestly

### Step 2: Adversarial Validation Suite
Define canonical failure modes and verify the reward catches them:
- **Copy-paste**: completion is verbatim source → should score low on originality, possibly sentence_coverage if no synthesis occurs
- **Hallucination**: completion states a plausible but false fact → should score low on contradiction
- **Missing prerequisite**: explanation of derivatives without mentioning limits → should score low on order
- **Verbose fluff**: correct but padded with filler sentences → should score low on information_density
- **Wrong simplification**: explanation oversimplifies to the point of being incorrect → should score low on contradiction
- **False example**: example that doesn't actually illustrate the concept → should score low on example_grounding

If the current reward does not correctly flag all of these, the metric needs fixing before claiming validity.

### Step 3: Dataset Expansion
Scale to hundreds of passages with:
- Clear licensing (CC-licensed textbooks, OpenStax, etc.)
- Documented provenance per passage
- Subject balance across the seven covered domains
- Difficulty variation within each subject (introductory vs. advanced)

Target: 500+ passages minimum for a credible benchmark paper, 1000+ for a lab-grade asset.

### Step 4: Human Validation Study
Run at least 100-200 human judgments (Mechanical Turk or domain expert annotation) across a stratified sample of model responses. Show:
- Spearman/Pearson correlation between composite reward and human teaching quality ratings
- Per-metric correlations to identify which sub-scores are most predictive
- Disagreement analysis: where does the reward diverge from human judgment and why?

This is the single most important step for commercial credibility. Without it, the benchmark is a hypothesis.

### Step 5: Model Ladder Results
Evaluate across at least four model tiers:
- Small/weak (7B instruction-tuned)
- Mid (Llama 3 70B or equivalent)
- Frontier (GPT-4o, Claude 3.5 Sonnet)
- Reasoning (o1, Claude 3.5 with extended thinking)

Expected result: scores should increase monotonically up the ladder on most metrics, with reasoning models potentially scoring higher on entailment_chain and order. If this pattern doesn't hold, the benchmark needs revision.

### Step 6: Benchmark Report
A buyer-facing document covering:
- Task definition and motivation
- Why existing benchmarks don't cover this
- Dataset provenance and licensing
- Scoring methodology with validity evidence
- Model ladder results
- Known limitations and failure modes
- Eval commands (reproduce results in one command)

---

## Core Differentiator to Invest In

The **prerequisite order metric** is the strongest reason to keep building this rather than walking away. It is novel, interpretable, and directly tied to a real pedagogical failure mode (explaining derivatives before limits, or force before mass). All other metrics in this benchmark have partial precedents elsewhere. Prerequisite ordering for tutoring quality evaluation does not.

If this benchmark becomes a paper, that metric should be the thesis. The rest are supporting evidence that the benchmark is comprehensive.

---

## Positioning Summary

| Audience | Positioning |
|----------|-------------|
| AI lab (buy benchmark) | Not ready. Return after Steps 1-5. |
| AI lab (research collaboration) | Possible now — pitch as work-in-progress with clear roadmap |
| Open source community | Release now to build citations and surface failures early |
| EdTech / LLM-for-education buyer | Concept pitch only; needs human validation before product claims |
