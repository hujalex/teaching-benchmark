import asyncio
import json
import threading

import verifiers as vf


SYSTEM_PROMPT = (
    "You are an expert tutor. Read the textbook excerpt provided and explain the "
    "concept clearly to a student with no prior knowledge of the topic. "
    "Introduce prerequisite ideas before the main concept, use at least one concrete "
    "example, and connect each idea to the next with explicit reasoning."
)


def load_environment(**_kwargs) -> vf.Environment:
    # ------------------------------------------------------------------ #
    # Lazy initialization — keep load_environment() near-zero cost so    #
    # `prime env install` and import-time tests don't hang on model      #
    # downloads or PDF processing. Heavy imports (fastembed, spacy) are  #
    # deferred until first rollout.                                       #
    # ------------------------------------------------------------------ #
    _verifier = None
    _verifier_lock = threading.Lock()

    def _get_verifier():
        nonlocal _verifier
        # Double-checked locking: fast path skips the lock once initialized,
        # slow path serializes concurrent first-callers so model loads happen
        # exactly once even under parallel rollouts.
        if _verifier is None:
            with _verifier_lock:
                if _verifier is None:
                    from verifier.teaching_verifier import TeachingVerifier
                    _verifier = TeachingVerifier()
        return _verifier

    def dataset_builder():
        from parsing import create_dataset
        return create_dataset(embedder=_get_verifier()._embedder)

    # ------------------------------------------------------------------ #
    # Primary reward — runs score_all() once and caches sub-scores in    #
    # state so the zero-weight metric functions don't repeat the work.   #
    # asyncio.to_thread() prevents CPU-bound inference from blocking the  #
    # event loop during concurrent rollouts.                             #
    # ------------------------------------------------------------------ #

    async def teaching_quality(prompt, completion, info, state) -> float:
        source_text = prompt[-1]["content"]
        response = completion[-1]["content"]
        if isinstance(info, str):
            info = json.loads(info)
        metadata = {"topic": info["topic"], "subject": info.get("subject", ""), "kg": info["kg"]}
        verifier = _get_verifier()
        scores = await asyncio.to_thread(verifier.score_all, source_text, response, metadata)
        state["teaching_scores"] = scores
        return scores["composite"]

    # ------------------------------------------------------------------ #
    # Zero-weight metric functions — one per sub-score (visible in       #
    # prime eval tui and rollout logs alongside the composite reward).   #
    # ------------------------------------------------------------------ #

    def _make_metric(key: str):
        async def metric(state) -> float:
            return state.get("teaching_scores", {}).get(key, 0.0)
        metric.__name__ = key
        return metric

    _METRIC_KEYS = [
        "concept_coverage", "sentence_coverage", "contradiction",
        "entailment_chain", "order", "example_grounding",
        "information_density", "readability_curve", "originality",
        "copy_rate",
    ]

    rubric = vf.Rubric(funcs=[teaching_quality], weights=[1.0])
    for key in _METRIC_KEYS:
        rubric.add_metric(_make_metric(key))


    return vf.SingleTurnEnv(
        dataset=dataset_builder,
        system_prompt=SYSTEM_PROMPT,
        rubric=rubric,
        pass_threshold=0.75,
    )
