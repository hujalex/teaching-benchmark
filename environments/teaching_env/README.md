# teaching-env

### Overview
- **Environment ID**: `teaching-env`
- **Short description**: Multi-turn environment that scores how well a model teaches a STEM problem to a simulated struggling student.
- **Tags**: multi-turn, teaching, judge, stem, eval

### Datasets
- **Primary dataset**: `xw27/scibench` — physics/chemistry/math problems with numerical answers.
- **Columns used**: `question`, `answer`, `test_question`, `test_answer`, `required_information` (latter three are optional; the env falls back gracefully if absent).

### Task
- **Type**: multi-turn
- **Protocol**:
  1. A pre-test probes the simulated student's baseline knowledge.
  2. The teacher model explains the concept over up to `max_turns` turns, with the student model replying each turn.
  3. When the student claims to understand, the teacher gives a perturbed version of the problem to verify.
  4. If the student solves it correctly, the rollout ends with `student_understanding_verified = True`.
  5. A post-test scores the student after teaching completes.
- **Rubric overview**:
  - **Deterministic (weight 1.0 total)**: `correct_final_answer` · `required_info_f1` · `student_post_test_correct` · `learning_delta` · `verified_understanding` (each 0.2)
  - **Judge (weight 1.0 total)**: combined understanding score + 5-item pedagogical step-checklist

### Required Environment Variables

| Variable | When Used | Purpose |
| -------- | --------- | ------- |
| `PRIME_API_KEY` | Default (endpoint-based) | Prime Intellect credits; used for both student & judge by default |
| `OPENAI_API_KEY` | If using OpenAI endpoints | Required only if `student_endpoint_id` or `judge_endpoint_id` is set to an OpenAI model |

### Quickstart

**With Prime Intellect credits (default):**
```bash
prime env install teaching-env
prime eval run teaching-env -m openai/gpt-4.1-mini -n 5 -r 1
```
This uses `trinity-mini` (arcee's fast model) via Prime Intellect for both the student simulator and the judge.

**Override to use OpenAI models:**
```bash
prime eval run teaching-env -a '{"student_endpoint_id": "gpt-4.1-mini", "judge_endpoint_id": "gpt-4.1-mini"}'
```
(Requires `OPENAI_API_KEY` to be set.)

### Environment Arguments

| Arg | Type | Default | Description |
| --- | ---- | ------- | ----------- |
| `dataset_name` | str | `"xw27/scibench"` | HuggingFace dataset ID |
| `num_examples` | int | `50` | Number of rows to use; `-1` for all |
| `max_turns` | int | `10` | Hard cap on teaching turns per rollout |
| **Endpoints (Primary)** | | | |
| `student_endpoint_id` | str | `"trinity-mini"` | Endpoint alias for student LLM (from `configs/endpoints.toml`) |
| `judge_endpoint_id` | str | `"trinity-mini"` | Endpoint alias for judge LLM |
| **Fallback Overrides** | | | |
| `student_model` | str | `null` | Explicit model name (overrides endpoint) |
| `judge_model` | str | `null` | Explicit model name (overrides endpoint) |
| `student_base_url` | str | `null` | Explicit base URL (overrides endpoint) |
| `judge_base_url` | str | `null` | Explicit base URL (overrides endpoint) |
| **Other** | | | |
| `seed` | int | `0` | Dataset shuffle seed |
| `api_key_var` | str | `"PRIME_API_KEY"` | Env var name holding the API key (for backward compat) |

#### Available Endpoint IDs (from `configs/endpoints.toml`)

**Prime Intellect models** (use `PRIME_API_KEY`):
- `trinity-mini` — fast, cost-effective (default)
- `olmo3-7b-i`, `olmo3-32b-t` — AllenAI OLMo models
- `gemini-2.5-flash`, `gemini-3-flash` — Google Gemini (fast variants)
- `gemini-2.5-pro`, `gemini-3-pro` — Google Gemini (full models)
- `qwen3-30b-i`, `qwen3-235b-i` — Alibaba Qwen (instruct)
- Many others — see `configs/endpoints.toml` for the full list

**OpenAI models** (use `OPENAI_API_KEY`):
- `gpt-4.1-mini` — fast GPT-4 variant
- `gpt-4.1` — full GPT-4
- `gpt-5-mini`, `gpt-5` — newer models

#### Example Usage

```bash
# Use OLMo 7B instruct (Prime Intellect)
prime eval run teaching-env -a '{"student_endpoint_id": "olmo3-7b-i", "judge_endpoint_id": "olmo3-7b-i"}' -n 10 -r 2

# Use Gemini 2.5 Flash (Prime Intellect)
prime eval run teaching-env -a '{"student_endpoint_id": "gemini-2.5-flash", "judge_endpoint_id": "gemini-2.5-flash"}' -n 20 -r 1

# Mix endpoints: Prime Intellect student, OpenAI judge
prime eval run teaching-env -a '{"student_endpoint_id": "trinity-mini", "judge_endpoint_id": "gpt-4.1-mini"}' -n 5 -r 1
```

### Metrics

| Metric | Meaning |
| ------ | ------- |
| `reward` | Weighted sum of all reward functions |
| `correct_final_answer` | 1.0 if the teacher's trajectory contains the canonical answer |
| `required_info_f1` | F1 over required formulas/vocab the teacher mentioned |
| `student_post_test_correct` | 1.0 if the student answered the post-test correctly |
| `learning_delta_reward` | Post-test minus pre-test score, clipped to [0, 1] |
| `verified_understanding` | 1.0 if the student passed the perturbed verification problem |
| `judge_teaching_quality` | Combined understanding (0–1) + step-checklist (0–1) judge score |
| `metric_num_turns` | Number of teaching turns used |
| `metric_pre_test_score` | Student's score before teaching |
| `metric_post_test_score` | Student's score after teaching |
| `metric_learning_delta` | Raw post − pre delta |
| `metric_student_understood_early` | 1.0 if student claimed understanding (soft signal) |
| `metric_understanding_verified` | 1.0 if soft claim was verified by perturbed re-test |
| `metric_required_info_precision` | Precision of required-information coverage |
| `metric_required_info_recall` | Recall of required-information coverage |
