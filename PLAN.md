# PLAN.md — Fleshed-out specification for the Teaching Benchmark Environment

This document expands `SPEC.md` into an implementation-ready spec for the
`teaching_env` Prime Intellect / Verifiers environment. It sits alongside
`SPEC.md` as the canonical design doc and reflects the latest SPEC additions:
explicit `test_question` / `test_answer` / `required_information` columns,
F1 over required information, and the verified-understanding handshake
(re-test with perturbed numerics on early-stop).

---

## 1. Goal

Build a `vf.Environment` that measures **how well a model can teach a subject**,
not merely how well it can answer. A teacher model interacts with a simulated
student (smaller LLM) over multiple turns. Reward is driven by:

1. **Content correctness** — does the teacher's reasoning match ground truth?
2. **Coverage** — does the teacher mention the *required information*
   (formulas, vocabulary, context) for the problem? Scored by F1.
3. **Learning delta** — does the simulated student improve from pre-test to
   post-test?
4. **Verified understanding** — when the student claims to understand, can
   they solve a *perturbed* version of the same problem?
5. **Pedagogical soundness** — judged step-checklist over the trajectory.

The environment is multi-turn: the teacher keeps explaining until the student
verifiably understands or `max_turns` is hit.

---

## 2. Scope (v1) and Non-Goals

**In scope (v1):**
- Single subject domain: STEM problems from `xw27/scibench` (physics/chemistry/math).
- Single simulated student persona ("struggling beginner, no outside knowledge").
- Text-only chat; no tools, no sandbox, no documents.
- Required-information lists generated offline and cached on the dataset row.
- Numeric-perturbation handshake for verified understanding.

**Non-goals (v1, parked):**
- Document/slideshow-grounded teaching with student-generated probes (SPEC §Ideas).
- Multiple student personas / adaptive confusion.
- Curriculum-level scoring across multiple topics in one rollout.

---

## 3. Dataset

### 3.1 Source
- HuggingFace: `xw27/scibench`, `split="train"`.
- Map original columns: `problem_text` → `question`, `answer_number` → `answer`.

### 3.2 Required row schema (per SPEC §Dataset)
After preprocessing, every row exposes:

| Column | Type | Purpose |
|---|---|---|
| `question` | str | Problem the teacher is asked to teach |
| `answer` | str | Canonical answer to `question` |
| `test_question` | str | Probe used to evaluate the student (pre/post-test) |
| `test_answer` | str | Canonical answer to `test_question` |
| `required_information` | list[str] | Formulas / vocab / context the teacher must mention |
| `info` | JSON str | `{subject, type, difficulty, unit, perturbation_seed}` |

`required_information` and `test_question`/`test_answer` are produced by an
**offline preprocessing step** (see §3.4); v1 caches them as part of a
re-published dataset row so that `load_environment` is fast and deterministic.

### 3.3 Splits and sizing
- `eval_dataset`: first N rows (configurable via `num_examples`, default 50).
- `dataset` (train): remaining rows, shuffled with `seed`.
- Use `vf.DatasetBuilder` for lazy loading so replicas don't all pull HF concurrently.

### 3.4 Offline preprocessing pipeline
A small script (`scripts/build_dataset.py`, not part of the env package):

1. Pull `xw27/scibench`.
2. For each row, call an LLM to produce:
   - `required_information`: 3–8 atomic strings (formula names, constants,
     definitions). Stored canonicalized (lowercased, stripped).
   - `test_question`: a paraphrase or numeric variant of `question`.
   - `test_answer`: solved canonical answer for `test_question`.
3. Validate `test_answer` symbolically (math-verify) where possible.
4. Save to a HF dataset (e.g. `<user>/scibench-teaching`) or a local parquet.

`load_environment` reads the **preprocessed** dataset; falls back to the raw
scibench rows with an empty `required_information` and `test_question = question`
if the preprocessed dataset is unavailable (with a warning).

### 3.5 Perturbed re-test (verified understanding)
For the "student claims to understand → re-test with different numerics" loop
(SPEC §Stop Condition), the env generates a perturbation **on the fly**:
- For numeric scibench problems, parse numbers in `question`, scale each by a
  per-rollout RNG seeded from `info.perturbation_seed`, and recompute `answer`
  using a small symbolic helper or LLM (cached per rollout).
- If perturbation is not safely automatable, fall back to `test_question` /
  `test_answer` as the re-test probe (still a different problem from `question`).

---

## 4. Environment Class

`TeachingEnv(vf.MultiTurnEnv)`.

### 4.1 Configuration (load_environment kwargs)
| Kwarg | Type | Default | Purpose |
|---|---|---|---|
| `dataset_name` | str | `"xw27/scibench"` (or preprocessed mirror) | HF dataset id |
| `num_examples` | int | `50` | Cap eval size; `-1` for all |
| `max_turns` | int | `10` | Hard cap from SPEC |
| `student_model` | str | `"gpt-4.1-mini"` | Simulated student LLM |
| `judge_model` | str | `"gpt-4.1-mini"` | Rubric judge LLM |
| `student_base_url` | str \| None | None | OpenAI-compatible endpoint override |
| `understanding_threshold` | float | `0.8` | Min judge score for soft "understands" signal |
| `perturbation_strategy` | `"numeric" \| "test_question"` | `"numeric"` | How re-test is generated |
| `seed` | int | `0` | Determinism |
| `weights` | dict | see §7.5 | Override rubric weights |
| `api_key_var` | str | `"OPENAI_API_KEY"` | Validated via `vf.ensure_keys` |

`load_environment()` MUST call `vf.ensure_keys([api_key_var])`.

### 4.2 State (per-rollout)
`setup_state(state)` initializes:
```python
state["pre_test_score"]              = None     # float in [0,1]
state["post_test_score"]             = None     # float in [0,1]
state["learning_delta"]              = None     # post - pre
state["student_messages"]            = []       # full student conversation
state["student_understands"]         = False    # soft claim from student
state["student_understanding_verified"] = False # post-perturbation success
state["perturbed_question"]          = None
state["perturbed_answer"]            = None
state["turn_count"]                  = 0
state["required_info_hits"]          = set()    # which required items appeared
state["step_quality"]                = []       # optional per-turn pedagogy scores
```

### 4.3 Initial prompt to the teacher
System message:
> You are a teacher helping a struggling student learn. The student knows
> nothing about the topic and will only learn from what you tell them. Teach
> step by step, motivate each formula, and check the student's understanding.
> When the student claims to understand, give them a similar problem with
> different numbers to verify before concluding the lesson.

First user message: `"Teach the student how to solve: {question}"`.

### 4.4 The rollout loop
1. **Pre-test** (hidden from teacher).
   - Ask the student model `test_question` cold (persona only, no transcript).
   - Score against `test_answer` → `state["pre_test_score"]`.
2. **Teaching loop** (`env_response` per turn):
   - Forward the teacher's latest message to the student LLM with the
     student persona + running history.
   - Append teacher↔student exchange to `state["student_messages"]`.
   - Update `state["required_info_hits"]` by checking new teacher tokens
     against `required_information` (case-insensitive, normalized).
   - If the student's reply contains an "I understand" signal → set
     `state["student_understands"] = True`.
3. **Verified-understanding handshake** (when `student_understands` flips True):
   - Generate `perturbed_question` / `perturbed_answer` (§3.5) and inject a
     synthetic teacher-style user message:
     `"Great — solve this similar problem to confirm: {perturbed_question}"`.
   - The next student reply is graded against `perturbed_answer`.
   - If correct → `student_understanding_verified = True` (stop).
   - If incorrect → reset `student_understands = False`, continue teaching.
4. **Stop conditions** (see §6).
5. **Post-test** (hidden).
   - Cold-ask the student `test_question` again with the **full transcript**
     prepended (so post-test reflects what they learned).
   - Record `post_test_score`, compute `learning_delta`.

### 4.5 `env_response` contract
`env_response(messages, state)` must:
- Increment `state["turn_count"]`.
- Update `required_info_hits` from the latest teacher message.
- Call the student LLM via `AsyncOpenAI`; never use a sync client on the hot path.
- Drive the verified-understanding handshake (§4.4 step 3).
- On verified success, set `state["final_env_response"]` to the perturbation
  result message and return it (signals early termination per
  `environments/AGENTS.md`).
- Otherwise return `[{"role": "user", "content": <student reply>}]`.

---

## 5. Simulated student

### 5.1 System prompt (canonical, parameterized)
```
You are a student struggling with {subject}. Do not use outside knowledge.
Only learn from what the teacher tells you. If the teacher has not told you
something, say "I don't know" rather than guessing. When asked if you
understand, answer honestly based only on what they have taught you. If you
genuinely understand, say "I understand" and briefly restate the idea in
your own words.
```
`{subject}` is filled from `info.subject` (default: "this topic"). This matches
SPEC §"System Prompt for smaller model".

### 5.2 Behavioral guarantees
- The student is a **fresh** chat per rollout (no leakage between examples).
- Pre-test: persona + probe only (no transcript).
- Post-test: persona + transcript + probe.
- Re-test (verified-understanding): persona + transcript + perturbed probe.
- Sampling: `temperature=0.7`, `max_tokens=512` (tunable).

---

## 6. Stop conditions

Implemented with `@vf.stop`:

| Priority | Name | Condition |
|---|---|---|
| 100 | `understanding_verified` | `state["student_understanding_verified"] is True` |
| 50  | `max_turns_reached`      | `state["turn_count"] >= max_turns` (built-in also fires) |
| 10  | `teacher_gave_up`        | Teacher message matches a "give up" regex |

Note: `student_understands` (the soft claim) does **not** stop the loop on its
own — only the *verified* flag does. This is the SPEC's
"different numerical values" handshake.

Built-in `has_error`, `overlong_prompt`, and `max_total_completion_tokens`
remain enabled.

---

## 7. Rubrics

A `RubricGroup` of two rubrics per SPEC §Verifiers, with the deterministic
rubric augmented to include F1 over required information.

### 7.1 Deterministic rubric — `vf.Rubric`
Reward functions:
- `correct_final_answer(completion, answer)` — does the teacher's trajectory
  contain the canonical `answer` (math-verify for numerics, normalized
  exact-match for strings)? **Weight: 0.2**
- `required_info_f1(completion, info, state)` — F1 between
  `state["required_info_hits"]` and `info["required_information"]`. Computed
  with case-insensitive normalization and lemma-light matching. **Weight: 0.2**
- `student_post_test_correct(state)` — 1.0 iff `post_test_score == 1.0`. **Weight: 0.2**
- `learning_delta(state)` — `clip(post − pre, 0, 1)`. **Weight: 0.2**
- `verified_understanding(state)` — 1.0 iff `student_understanding_verified`. **Weight: 0.2**

### 7.2 Judging rubric — `vf.JudgeRubric`
Single judge with a custom prompt covering both:
1. **Understanding score** — judge reads the transcript + the student's post-test
   answer and rates apparent understanding 0–10 (normalize to [0,1]).
2. **Step checklist** (SPEC §"Step checklist"):
   a. Did the teacher break the problem into steps?
   b. Were the steps in a sound order?
   c. Did the teacher check student understanding?
   d. Did the teacher avoid just stating the answer without reasoning?
   e. Did the teacher correct misconceptions?

Judge is asked to return a JSON object `{understanding: 0-10, checklist: [0/1]*5}`;
reward = `0.5 * understanding/10 + 0.5 * mean(checklist)`. **Weight: 0.5**

### 7.3 Metrics (weight=0, observability only)
- `num_turns`
- `pre_test_score`, `post_test_score`, `learning_delta`
- `student_understood_early` (bool→float)
- `student_understanding_verified` (bool→float)
- `required_info_precision`, `required_info_recall`, `required_info_f1`
- `mean_step_quality` (if per-turn pedagogy scoring is enabled)

### 7.4 Aggregation
Final reward = weighted sum across rubrics. Weights default to:
```python
{
  "correct_final_answer": 0.2,
  "required_info_f1":    0.2,
  "student_post_test_correct": 0.2,
  "learning_delta":      0.2,
  "verified_understanding": 0.2,
  "judge":               0.5,   # in the judge rubric
}
```
All overridable via `load_environment(weights=...)`.

---

## 8. Files and packaging

```
environments/teaching_env/
├── teaching_env.py         # load_environment, TeachingEnv, rubrics
├── pyproject.toml          # name="teaching-env"
├── README.md               # usage, kwargs, env vars, sample eval cmd
└── outputs/                # eval artifacts (gitignored)

scripts/
└── build_dataset.py        # offline preprocessing for §3.4
```

`pyproject.toml`:
- `tags = ["multi-turn", "teaching", "judge", "stem", "eval"]`
- `dependencies = ["verifiers>=0.1.8", "datasets", "math-verify", "openai"]`
- `[tool.verifiers.eval] num_examples = 20, rollouts_per_example = 3`

----

## 9. Validation plan

1. **Smoke test:** `prime eval run teaching-env -m gpt-4.1-mini -n 2 -r 1`.
2. **Sanity test:** strong teacher → mean `learning_delta > 0` over 20 examples.
3. **Negative control:** "teacher" that always emits "I don't know" → mean
   reward < 0.2, `learning_delta ≈ 0`, `verified_understanding == 0`.
4. **Determinism:** with `seed=0` and `temperature=0` for student/judges,
   identical rollouts produce identical metrics.
5. **F1 sanity:** for a teacher that copies `required_information` verbatim,
   `required_info_f1 ≈ 1.0`.
6. **Handshake test:** synthetic transcript where the student claims
   understanding but fails the perturbed probe → loop continues, final
   `student_understanding_verified == False`.
7. **Concurrency:** grep for `requests.`, `time.sleep`, `OpenAI(` (sync) on
   hot paths — must be zero.

---

## 11. Open design questions

1. **Required-info matching.** Substring vs. embedding similarity vs.
   LLM-judged hits? v1 uses normalized substring matching; v2 may upgrade.
2. **Perturbation correctness.** Auto-perturbing numeric problems risks
   producing incorrect ground-truth answers. v1 uses an LLM solver +
   math-verify validation; on validation failure, fall back to `test_question`.
3. **Student honesty.** Smaller models leak training knowledge. Mitigations:
   low temperature, periodic system reminder ("only use what the teacher said"),
   or a memoryless "fresh student" reset before the post-test.
4. **Early-stop gaming.** The verified-understanding handshake (perturbed re-test)
   is the primary defense. Soft claim alone never grants reward.
5. **Judge cost.** Combined understanding+checklist judge runs once at
   end-of-rollout in v1.
6. **Document-grounded variant** (SPEC §Ideas). Defer to v2; `info` schema
   already accommodates `info.document`.

---

## 12. Roadmap

- **v1 (this plan):** scibench rows with `test_question` / `test_answer` /
  `required_information`, F1 coverage reward, verified-understanding handshake,
  combined judge, `prime eval run` ready.
- **v1.1:** Per-turn pedagogy judge with caching; embedding-based required-info
  matching; richer perturbation strategies.
- **v2:** Document/slideshow-grounded teaching (`info.document`), student-generated
  probes via data labeling (SPEC §Ideas), longer contexts (RLM-style decomposition).
- **v2.1:** Multiple student personas (beginner / confused / adversarial),
  difficulty-stratified eval, GEPA optimization of teacher system prompt.
- **v3:** Multi-topic curriculum scoring; persistent student across multiple
  lessons in one rollout group.

---

## 13. Acceptance criteria for v1

- [ ] `prime env install teaching-env` succeeds in a clean lab workspace.
- [ ] `prime eval run teaching-env -n 5 -r 1` completes end-to-end with no
      sync warnings and produces every metric in §7.3.
- [ ] Dataset rows expose `question`, `answer`, `test_question`, `test_answer`,
      `required_information` per SPEC §Dataset.
- [ ] Verified-understanding handshake fires at least once on the smoke set
      and correctly stops the rollout when the perturbed re-test succeeds.
- [ ] Negative-control test (§10.3) yields mean reward < 0.2.
- [ ] Strong-teacher test (§10.2) yields mean `learning_delta > 0`.
- [ ] F1-sanity test (§10.5) yields `required_info_f1 > 0.9`.
- [ ] README documents every kwarg in §4.1 and required env vars in §9.
