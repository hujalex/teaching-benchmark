# Integration Plan: TeachingVerifier → load_environment()

## Goal

Wire `TeachingVerifier` into `load_environment()` so the composite teaching-quality
score becomes the rollout reward used during RL training and evaluation.

---

## Current State

| File | Role |
|---|---|
| `verifier/teaching_verifier.py` | Standalone scorer; `verify(prompt, completion, metadata) -> float` |
| `teaching_env.py` | `load_environment()` returns a `TeachingEnv` with a placeholder rubric |
| `parsing.py` | Builds a HuggingFace `Dataset` from local PDF/markdown files |

The two pieces are not yet connected. `load_environment()` creates a dataset whose
rows have `topic` and `raw_text` fields but does not pass them through to any verifier.

---

## Integration Steps

### Step 1 — Enrich the dataset rows

`parsing.py:create_dataset()` already parses `topic` and `raw_text` from each
markdown file. Add a `kg` column that stores the knowledge graph dict for that page.

Two options:

**Option A (recommended) — build KG at dataset-creation time**

Extend `create_dataset()` to call a `build_kg(raw_text)` function that returns the
`{"concepts": [...], "prerequisite_edges": [...]}` dict for each page. Store it as a
JSON string in an `info` column so it survives `Dataset.from_list()` serialisation.

**Option B — load KG from HuggingFace at verifier init**

Pass a `kg_dataset_path` to `TeachingVerifier.__init__`. The verifier builds
`self.kg_index` keyed by topic. The dataset rows only need `topic`; the verifier
looks up the KG internally. Use this if the KG dataset is published on the Hub.

For the local-first workflow, Option A avoids an external dependency.

---

### Step 2 — Build the reward function (closure over the verifier)

In `teaching_env.py`, instantiate `TeachingVerifier` once and capture it in a closure:

```python
from verifier import TeachingVerifier

def load_environment(**kwargs) -> vf.Environment:
    dataset = create_dataset()          # rows: topic, raw_text, info (JSON with kg)
    verifier = TeachingVerifier()       # loads all models once

    async def teaching_quality(prompt, completion, info) -> float:
        metadata = {
            "topic": info["topic"],
            "kg":    info["kg"],        # or omit if verifier uses kg_index
        }
        # verify() is CPU-bound; offload to thread pool to avoid blocking the event loop
        return await asyncio.to_thread(
            verifier.verify,
            prompt[-1]["content"],      # source_text from the last user message
            completion[-1]["content"],
            metadata,
        )

    rubric = vf.Rubric(funcs=[teaching_quality], weights=[1.0])
    return vf.SingleTurnEnv(dataset=dataset, rubric=rubric)
```

The `asyncio.to_thread()` wrapper is required because `TeachingVerifier.verify()` is
synchronous and CPU-heavy (NLI inference, spacy, SentenceTransformer). Without it the
call blocks the event loop and serialises all concurrent rollouts.

---

### Step 3 — Thread source_text through the prompt

`verify()` treats `prompt` as the source text. The dataset's `prompt` column must
therefore contain the raw textbook page, not an instruction wrapper. Two sub-options:

**Option A — use `question` column**

Set `question = raw_text` in each dataset row. `SingleTurnEnv` wraps it in a user
message automatically. The reward function extracts `prompt[-1]["content"]` as
`source_text`.

**Option B — use a system prompt + structured user message**

```python
SYSTEM = (
    "You are an expert tutor. Read the textbook excerpt below and explain the "
    "concept clearly to a student who has no prior knowledge of the topic."
)
return vf.SingleTurnEnv(
    dataset=dataset,
    system_prompt=SYSTEM,
    rubric=rubric,
)
```

The model's task is clearer, and `prompt[-1]["content"]` still holds `raw_text`.

---

### Step 4 — Pass `info` with topic and KG

The dataset must have an `info` column (JSON string) containing at least `topic`.
If using Option A from Step 1, also include the serialised KG:

```python
import json

records = [
    {
        "question": page["raw_text"],
        "info": json.dumps({"topic": page["topic"], "kg": build_kg(page["raw_text"])}),
    }
    for page in parsed_pages
]
```

`vf.SingleTurnEnv` deserialises the JSON string into a dict before passing it to
reward functions, so the reward function receives `info` as a plain dict.

---

### Step 5 — Verify end-to-end with prime eval

After wiring everything, smoke-test locally:

```bash
prime env install teaching-env
prime eval run teaching-env --num-examples 2 --rollouts-per-example 1
```

Check that:
- Sub-scores appear in the rollout metrics (currently they only `print`; promote them
  to `self._log()` calls that write to a shared `state` dict or return a metrics dict
  if the rubric framework supports it)
- The composite reward is in `[0, 1]`
- No event-loop blocking (watch wall-clock time per rollout)

---

## Open Questions

1. **KG source** — do we build the KG locally from raw text (using KeyBERT + heuristics)
   or publish a labelled KG dataset to HuggingFace and load via `kg_dataset_path`?
   Answering this determines which option in Step 1 to pursue.

2. **Multi-turn vs single-turn** — the current `TeachingEnv` is a `MultiTurnEnv`.
   The verifier scores a single completion. If we keep multi-turn, `verify()` should
   run on the concatenated teacher turns, or we move to `SingleTurnEnv` with a
   single-shot teaching prompt.

3. **Sub-score visibility** — `_log()` currently prints to stdout. For `prime eval tui`
   visibility, each sub-score should be emitted as a metric (weight=0 reward function
   or via `state`). Consider adding a `metrics` dict return alongside the float, or
   splitting into separate zero-weight rubric functions.
