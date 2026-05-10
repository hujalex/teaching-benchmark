import numpy as np

# cross-encoder/nli-deberta-v3-small label order: 0=contradiction, 1=entailment, 2=neutral
_LABEL_SCORES = np.array([0.0, 1.0, 0.5])


def compute(nli_outputs: np.ndarray, n_source: int, n_comp: int) -> float:
    """Score how well the completion avoids contradicting the source.

    nli_outputs: shape (n_source * n_comp, 3), pre-sliced from the batched call.
    Returns a value in [0, 1] where 1.0 means no contradictions detected.
    """
    if n_source == 0 or n_comp == 0 or nli_outputs.size == 0:
        return 1.0
    labels = nli_outputs.argmax(axis=-1)           # (n_source * n_comp,)
    scores = _LABEL_SCORES[labels].reshape(n_source, n_comp)
    return float(scores.max(axis=1).mean())
