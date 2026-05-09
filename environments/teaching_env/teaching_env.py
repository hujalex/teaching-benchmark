import asyncio
import json

import verifiers as vf
from parsing import create_dataset
from verifier import TeachingVerifier


SYSTEM_PROMPT = (
    "You are an expert tutor. Read the textbook excerpt provided and explain the "
    "concept clearly to a student with no prior knowledge of the topic. "
    "Introduce prerequisite ideas before the main concept, use at least one concrete "
    "example, and connect each idea to the next with explicit reasoning."
)


def load_environment(**_kwargs) -> vf.Environment:
    dataset = create_dataset()
    verifier = TeachingVerifier()

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
        metadata = {"topic": info["topic"], "kg": info["kg"]}
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

    rubric = vf.Rubric(funcs=[teaching_quality], weights=[1.0])
    for key in TeachingVerifier.WEIGHTS:
        rubric.add_metric(_make_metric(key))


    return vf.SingleTurnEnv(
        dataset=dataset,
        system_prompt=SYSTEM_PROMPT,
        rubric=rubric,
        pass_threshold=0.75,
    )
