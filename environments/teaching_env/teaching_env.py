import json
import re
import os
from typing import Any

import verifiers as vf
from datasets import load_dataset
from openai import AsyncOpenAI


# ---------------------------------------------------------------------------
# Student simulator helpers
# ---------------------------------------------------------------------------

STUDENT_SYSTEM_PROMPT = (
    "You are a student struggling with {subject}. "
    "Do not use outside knowledge. "
    "Only learn from what the teacher tells you in this conversation. "
    "If the teacher has not told you something, say \"I don't know\" rather than guessing. "
    "When the teacher asks if you understand, answer honestly based only on what they have "
    "taught you. If you genuinely understand, say \"I understand\" and briefly restate the "
    "idea in your own words."
)

UNDERSTANDING_PATTERN = re.compile(
    r"\bI understand\b|\bI get it\b|\bI see\b|\bthat makes sense\b",
    re.IGNORECASE,
)


def _resolve_api_key(api_key_var: str) -> str:
    """Read the API key from env var; for PRIME_API_KEY, fall back to ~/.prime/config.json."""
    key = os.environ.get(api_key_var)
    if key:
        return key
    if api_key_var == "PRIME_API_KEY":
        prime_cfg = os.path.expanduser("~/.prime/config.json")
        if os.path.exists(prime_cfg):
            try:
                with open(prime_cfg) as f:
                    cfg = json.load(f)
                if cfg.get("api_key"):
                    return cfg["api_key"]
            except (json.JSONDecodeError, OSError):
                pass
    return "placeholder"


def _make_client(base_url: str | None = None, api_key_var: str = "OPENAI_API_KEY") -> AsyncOpenAI:
    """Create an AsyncOpenAI client.

    If base_url is provided, use it with the specified API key variable.
    Otherwise default to OpenAI.
    """
    kwargs: dict[str, Any] = {"api_key": _resolve_api_key(api_key_var)}
    if base_url:
        kwargs["base_url"] = base_url
    return AsyncOpenAI(**kwargs)


async def _call_student(
    client: AsyncOpenAI,
    model: str,
    subject: str,
    history: list[dict],
    user_message: str,
) -> str:
    messages = [
        {"role": "system", "content": STUDENT_SYSTEM_PROMPT.format(subject=subject)}
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=512,
    )
    return response.choices[0].message.content or ""


def _score_answer(reply: str, expected: str) -> float:
    """Return 1.0 if expected answer is present in reply (numeric-aware)."""
    norm_reply = reply.lower().strip()
    norm_ans = expected.lower().strip()
    try:
        numeric = float(norm_ans.replace(",", ""))
        nums = [float(m) for m in re.findall(r"[-+]?\d*\.?\d+", norm_reply)]
        return 1.0 if any(abs(n - numeric) / (abs(numeric) + 1e-9) < 0.05 for n in nums) else 0.0
    except ValueError:
        pass
    return 1.0 if norm_ans in norm_reply else 0.0


async def _probe_student(
    client: AsyncOpenAI,
    model: str,
    subject: str,
    history: list[dict],
    probe_question: str,
    probe_answer: str,
) -> float:
    reply = await _call_student(client, model, subject, history, probe_question)
    return _score_answer(reply, probe_answer)


# ---------------------------------------------------------------------------
# Required-information F1 helpers
# ---------------------------------------------------------------------------

def _normalize(t: str) -> str:
    return re.sub(r"[^a-z0-9]", " ", t.lower()).strip()


def _find_hits(teacher_text: str, required: list[str]) -> set[str]:
    norm_text = _normalize(teacher_text)
    return {r for r in required if _normalize(r) in norm_text}


def _prf(hits: set[str], required: list[str]) -> tuple[float, float, float]:
    if not required:
        return 1.0, 1.0, 1.0
    p = len(hits) / len(required)
    r = len(hits) / len(required)
    f1 = 2 * p * r / (p + r + 1e-9)
    return p, r, f1


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

TEACHER_SYSTEM_PROMPT = (
    "You are a teacher helping a struggling student learn. "
    "The student knows nothing about the topic and will only learn from what you tell them. "
    "Teach step by step, motivate each formula, and check the student's understanding. "
    "When the student claims to understand, give them a similar problem with different numbers "
    "to verify before concluding the lesson."
)


class TeachingEnv(vf.MultiTurnEnv):

    def __init__(
        self,
        student_model: str = "gpt-4.1-mini",
        student_base_url: str | None = None,
        student_api_key_var: str = "OPENAI_API_KEY",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._student_model = student_model
        self._student_client = _make_client(student_base_url, student_api_key_var)

    # -- State ---------------------------------------------------------------

    async def setup_state(self, state: vf.State) -> vf.State:
        state["pre_test_score"] = None
        state["post_test_score"] = None
        state["learning_delta"] = None
        state["student_messages"] = []
        state["student_understands"] = False
        state["student_understanding_verified"] = False
        state["perturbed_question"] = None
        state["perturbed_answer"] = None
        state["turn_count"] = 0
        state["required_info_hits"] = set()
        state = await self._run_pre_test(state)
        return await super().setup_state(state)

    # -- Pre / post tests ----------------------------------------------------

    def _subject(self, state: vf.State) -> str:
        info = _parse_info(state.get("info", "{}"))
        return info.get("subject", "this topic")

    async def _run_pre_test(self, state: vf.State) -> vf.State:
        test_q = state.get("test_question") or state.get("question", "")
        test_a = state.get("test_answer") or state.get("answer", "")
        if test_q and test_a:
            state["pre_test_score"] = await _probe_student(
                self._student_client, self._student_model,
                self._subject(state), [], test_q, test_a,
            )
        else:
            state["pre_test_score"] = 0.0
        return state

    async def _run_post_test(self, state: vf.State) -> vf.State:
        test_q = state.get("test_question") or state.get("question", "")
        test_a = state.get("test_answer") or state.get("answer", "")
        if test_q and test_a:
            state["post_test_score"] = await _probe_student(
                self._student_client, self._student_model,
                self._subject(state), list(state["student_messages"]), test_q, test_a,
            )
        else:
            state["post_test_score"] = 0.0
        pre = state.get("pre_test_score") or 0.0
        state["learning_delta"] = max(0.0, state["post_test_score"] - pre)
        return state

    # -- Rollout loop --------------------------------------------------------

    async def env_response(self, messages: vf.Messages, state: vf.State, **kwargs) -> vf.Messages:
        state["turn_count"] += 1
        teacher_msg = messages[-1].get("content", "") if messages else ""
        subject = self._subject(state)

        # Track required-information coverage from the teacher's message
        required: list[str] = _get_required_info(state)
        new_hits = _find_hits(teacher_msg, required)
        state["required_info_hits"] = state.get("required_info_hits", set()) | new_hits

        # --- Verified-understanding handshake ---
        # Teacher just administered the perturbed problem; grade the student's reply.
        if state.get("student_understands") and state.get("perturbed_question"):
            perturbed_q = state["perturbed_question"]
            perturbed_a = state["perturbed_answer"] or state.get("answer", "")
            student_reply = await _call_student(
                self._student_client, self._student_model,
                subject, list(state["student_messages"]), perturbed_q,
            )
            state["student_messages"].append({"role": "user", "content": perturbed_q})
            state["student_messages"].append({"role": "assistant", "content": student_reply})

            if _score_answer(student_reply, perturbed_a) >= 0.5:
                state["student_understanding_verified"] = True
                await self._run_post_test(state)
                final_msg = {"role": "user", "content": f"Student verified: {student_reply}"}
                state["final_env_response"] = [final_msg]
                return [final_msg]
            else:
                # Reset and continue teaching
                state["student_understands"] = False
                state["perturbed_question"] = None
                state["perturbed_answer"] = None
                return [{"role": "user", "content": f"The student attempted but struggled: {student_reply}. Please continue teaching."}]

        # --- Normal turn: forward teacher message to student ---
        student_reply = await _call_student(
            self._student_client, self._student_model,
            subject, list(state["student_messages"]), teacher_msg,
        )
        state["student_messages"].append({"role": "user", "content": teacher_msg})
        state["student_messages"].append({"role": "assistant", "content": student_reply})

        if UNDERSTANDING_PATTERN.search(student_reply):
            state["student_understands"] = True
            perturbed_q, perturbed_a = _make_perturbed_probe(state)
            state["perturbed_question"] = perturbed_q
            state["perturbed_answer"] = perturbed_a
            follow_up = (
                f"Student reply: {student_reply}\n\n"
                f"The student claims to understand. Please give them this similar problem to verify: {perturbed_q}"
            )
            return [{"role": "user", "content": follow_up}]

        return [{"role": "user", "content": student_reply}]

    # -- Stop conditions -----------------------------------------------------

    @vf.stop(priority=100)
    async def understanding_verified(self, state: vf.State) -> bool:
        return bool(state.get("student_understanding_verified"))

    @vf.stop(priority=10)
    async def teacher_gave_up(self, state: vf.State) -> bool:
        return bool(state.get("teacher_gave_up_flag"))

    # -- Cleanup -------------------------------------------------------------

    @vf.cleanup
    async def finalize_post_test(self, state: vf.State):
        if state.get("post_test_score") is None:
            await self._run_post_test(state)


# ---------------------------------------------------------------------------
# Shared state helpers
# ---------------------------------------------------------------------------

def _parse_info(info_val: Any) -> dict:
    if isinstance(info_val, dict):
        return info_val
    if isinstance(info_val, str):
        try:
            return json.loads(info_val)
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def _get_required_info(state: vf.State) -> list[str]:
    raw = state.get("required_information", [])
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return [raw] if raw else []
    return list(raw) if raw else []


def _make_perturbed_probe(state: vf.State) -> tuple[str, str]:
    """Use test_question if available; otherwise perturb numerics in the original."""
    test_q = state.get("test_question")
    test_a = state.get("test_answer")
    if test_q and test_a:
        return test_q, test_a

    question = state.get("question", "")
    answer = state.get("answer", "")
    numbers = re.findall(r"[-+]?\d*\.?\d+", question)
    if numbers:
        original = numbers[0]
        try:
            perturbed_val = float(original) * 2
            return question.replace(original, str(perturbed_val), 1), answer
        except ValueError:
            pass
    return question, answer


# ---------------------------------------------------------------------------
# Reward functions
# ---------------------------------------------------------------------------

async def correct_final_answer(completion: vf.Messages, answer: str) -> float:
    """1.0 if the canonical answer appears in the teacher's trajectory."""
    full_text = " ".join(
        m.get("content", "") for m in completion if m.get("role") == "assistant"
    )
    return _score_answer(full_text, answer)


async def required_info_f1(state: vf.State) -> float:
    """F1 over required-information coverage."""
    required = _get_required_info(state)
    if not required:
        return 1.0
    hits = state.get("required_info_hits", set())
    _, _, f1 = _prf(hits, required)
    return f1


async def student_post_test_correct(state: vf.State) -> float:
    """1.0 if the student passed the post-test."""
    return 1.0 if (state.get("post_test_score") or 0.0) >= 1.0 else 0.0


async def learning_delta_reward(state: vf.State) -> float:
    """Improvement from pre- to post-test, clipped to [0, 1]."""
    return float(max(0.0, min(1.0, state.get("learning_delta") or 0.0)))


async def verified_understanding(state: vf.State) -> float:
    """1.0 if the student passed the perturbed verification problem."""
    return 1.0 if state.get("student_understanding_verified") else 0.0


# Observability metrics (weight=0)

async def metric_num_turns(state: vf.State) -> float:
    return float(state.get("turn_count", 0))

async def metric_pre_test_score(state: vf.State) -> float:
    return float(state.get("pre_test_score") or 0.0)

async def metric_post_test_score(state: vf.State) -> float:
    return float(state.get("post_test_score") or 0.0)

async def metric_learning_delta(state: vf.State) -> float:
    return float(state.get("learning_delta") or 0.0)

async def metric_student_understood_early(state: vf.State) -> float:
    return 1.0 if state.get("student_understands") else 0.0

async def metric_understanding_verified(state: vf.State) -> float:
    return 1.0 if state.get("student_understanding_verified") else 0.0

async def metric_required_info_precision(state: vf.State) -> float:
    required = _get_required_info(state)
    if not required:
        return 1.0
    hits = state.get("required_info_hits", set())
    p, _, _ = _prf(hits, required)
    return p

async def metric_required_info_recall(state: vf.State) -> float:
    required = _get_required_info(state)
    if not required:
        return 1.0
    hits = state.get("required_info_hits", set())
    _, r, _ = _prf(hits, required)
    return r


# ---------------------------------------------------------------------------
# Judge reward function
# ---------------------------------------------------------------------------

JUDGE_PROMPT = """\
You are evaluating a teaching session. Review the full teacher-student conversation below
and score it on two dimensions.

**Conversation:**
{response}

**Topic / correct answer:** {answer}

Return a JSON object with exactly this structure:
{{
  "understanding": <integer 0-10>,
  "checklist": [<0 or 1>, <0 or 1>, <0 or 1>, <0 or 1>, <0 or 1>]
}}

Where:
- "understanding" (0-10): How well does the student appear to understand the material by the end?
- "checklist" is 5 binary items in order:
  1. Did the teacher break the problem into clear steps?
  2. Were the steps in a logical, sound order?
  3. Did the teacher check the student's understanding during the session?
  4. Did the teacher explain reasoning rather than just stating the answer?
  5. Did the teacher correct any student misconceptions?

Return only valid JSON, no commentary."""


async def judge_teaching_quality(
    prompt: vf.Messages,
    completion: vf.Messages,
    answer: str,
    judge_client,
    judge_model: str,
) -> float:
    full_text = "\n".join(
        f"{m['role'].upper()}: {m.get('content', '')}"
        for m in list(prompt) + list(completion)
        if m.get("content")
    )
    filled = JUDGE_PROMPT.format(response=full_text[:8000], answer=answer)
    try:
        resp = await judge_client.chat.completions.create(
            model=judge_model,
            messages=[{"role": "user", "content": filled}],
            temperature=0.0,
            max_tokens=256,
        )
        raw = resp.choices[0].message.content or "{}"
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return 0.0
        data = json.loads(match.group())
        understanding = float(data.get("understanding", 0)) / 10.0
        checklist = data.get("checklist", [])
        checklist_score = sum(int(bool(v)) for v in checklist) / max(len(checklist), 1)
        return 0.5 * understanding + 0.5 * checklist_score
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Endpoint resolution
# ---------------------------------------------------------------------------

_ENDPOINT_MAP = {
    "trinity-mini": ("arcee/trinity-mini", "https://api.pinference.ai/api/v1", "PRIME_API_KEY"),
    "olmo3-7b-i": ("allenai/olmo-3-7b-instruct", "https://api.pinference.ai/api/v1", "PRIME_API_KEY"),
    "olmo3-32b-t": ("allenai/olmo-3-32b-think", "https://api.pinference.ai/api/v1", "PRIME_API_KEY"),
    "gemini-2.5-flash": ("google/gemini-2.5-flash", "https://api.pinference.ai/api/v1", "PRIME_API_KEY"),
    "gemini-3-flash": ("google/gemini-3-flash", "https://api.pinference.ai/api/v1", "PRIME_API_KEY"),
    "qwen3-30b-i": ("qwen/qwen3-30b-a3b-instruct-2507", "https://api.pinference.ai/api/v1", "PRIME_API_KEY"),
    "gpt-4.1-mini": ("gpt-4.1-mini", "https://api.openai.com/v1", "OPENAI_API_KEY"),
    "gpt-4.1": ("gpt-4.1", "https://api.openai.com/v1", "OPENAI_API_KEY"),
}


def _resolve_endpoint(
    endpoint_id: str,
    override_model: str | None = None,
    override_url: str | None = None,
) -> tuple[str, str | None, str]:
    """Resolve endpoint_id to (model_name, base_url, api_key_var).

    If override_model or override_url are provided, they take precedence.
    Falls back to hardcoded _ENDPOINT_MAP, then defaults to OpenAI.
    """
    if endpoint_id in _ENDPOINT_MAP:
        model, url, key = _ENDPOINT_MAP[endpoint_id]
        model = override_model or model
        url = override_url or url
        return model, url, key
    # Fallback: assume it's an OpenAI model name
    model = override_model or endpoint_id
    url = override_url
    return model, url, "OPENAI_API_KEY"


# ---------------------------------------------------------------------------
# load_environment
# ---------------------------------------------------------------------------

def load_environment(
    dataset_name: str = "xw27/scibench",
    num_examples: int = 50,
    max_turns: int = 10,
    student_endpoint_id: str = "gemini-2.5-flash",
    judge_endpoint_id: str = "gemini-2.5-flash",
    student_model: str | None = None,
    judge_model: str | None = None,
    student_base_url: str | None = None,
    judge_base_url: str | None = None,
    seed: int = 0,
    api_key_var: str = "PRIME_API_KEY",
    **kwargs,
) -> vf.Environment:
    """Load the teaching environment.

    By default, uses Prime Intellect credits (endpoint-based).

    Args:
        student_endpoint_id: Endpoint alias from configs/endpoints.toml (default: "trinity-mini")
        judge_endpoint_id: Endpoint alias from configs/endpoints.toml (default: "trinity-mini")
        student_model: Override the model name (ignored if student_endpoint_id is set)
        judge_model: Override the model name (ignored if judge_endpoint_id is set)
        student_base_url: Override the base URL for student LLM
        judge_base_url: Override the base URL for judge LLM
        api_key_var: API key environment variable (default: "PRIME_API_KEY")
    """
    # Resolve endpoint IDs to model names and URLs
    student_model, student_url, student_key = _resolve_endpoint(
        student_endpoint_id, student_model, student_base_url
    )
    judge_model, judge_url, judge_key = _resolve_endpoint(
        judge_endpoint_id, judge_model, judge_base_url
    )

    # Make sure the resolved key is also visible as an env var (some downstream
    # libraries read it directly). If we can resolve it via _resolve_api_key —
    # including from ~/.prime/config.json — populate the env var so
    # vf.ensure_keys passes.
    for key_var in {student_key, judge_key}:
        if not os.environ.get(key_var):
            resolved = _resolve_api_key(key_var)
            if resolved != "placeholder":
                os.environ[key_var] = resolved
    vf.ensure_keys([student_key, judge_key])

    # -- Dataset -------------------------------------------------------------
    def build_dataset():
        ds = load_dataset(dataset_name, split="train")

        col_map = {}
        if "problem_text" in ds.column_names:
            col_map["problem_text"] = "question"
        if "answer_number" in ds.column_names:
            col_map["answer_number"] = "answer"
        if col_map:
            ds = ds.rename_columns(col_map)

        keep = ["question", "answer"]
        for opt in ["test_question", "test_answer", "required_information", "unit", "source"]:
            if opt in ds.column_names:
                keep.append(opt)
        ds = ds.select_columns([c for c in keep if c in ds.column_names])

        def add_info(row):
            info = {
                "subject": row.get("source", "physics/chemistry"),
                "type": "math",
                "difficulty": 3,
            }
            if "unit" in row:
                info["unit"] = row["unit"]
            row["info"] = json.dumps(info)

            # Ensure required_information is a list
            ri = row.get("required_information")
            if not ri:
                row["required_information"] = []
            elif isinstance(ri, str):
                try:
                    row["required_information"] = json.loads(ri)
                except (json.JSONDecodeError, ValueError):
                    row["required_information"] = [ri]

            # Fallback test probes
            if not row.get("test_question"):
                row["test_question"] = row.get("question", "")
            if not row.get("test_answer"):
                row["test_answer"] = row.get("answer", "")
            return row

        ds = ds.map(add_info)
        ds = ds.shuffle(seed=seed)
        if num_examples > 0:
            ds = ds.select(range(min(num_examples, len(ds))))
        return ds

    # -- Deterministic rubric ------------------------------------------------
    det_rubric = vf.Rubric(
        funcs=[
            correct_final_answer,
            required_info_f1,
            student_post_test_correct,
            learning_delta_reward,
            verified_understanding,
        ],
        weights=[0.2, 0.2, 0.2, 0.2, 0.2],
    )
    for metric_fn in [
        metric_num_turns,
        metric_pre_test_score,
        metric_post_test_score,
        metric_learning_delta,
        metric_student_understood_early,
        metric_understanding_verified,
        metric_required_info_precision,
        metric_required_info_recall,
    ]:
        det_rubric.add_metric(metric_fn)

    # -- Judge rubric --------------------------------------------------------
    judge_kwargs: dict[str, Any] = {"api_key": _resolve_api_key(judge_key)}
    if judge_url:
        judge_kwargs["base_url"] = judge_url
    judge_client = AsyncOpenAI(**judge_kwargs)
    judge_rubric = vf.JudgeRubric(judge_model=judge_model, judge_client=judge_client)
    judge_rubric.add_class_object("judge_client", judge_client)
    judge_rubric.add_class_object("judge_model", judge_model)
    judge_rubric.add_reward_func(judge_teaching_quality, weight=1.0)

    rubric = vf.RubricGroup([det_rubric, judge_rubric])

    return TeachingEnv(
        dataset=build_dataset,
        system_prompt=TEACHER_SYSTEM_PROMPT,
        rubric=rubric,
        max_turns=max_turns,
        student_model=student_model,
        student_base_url=student_url,
        student_api_key_var=student_key,
        **kwargs,
    )
