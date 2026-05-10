import numpy as np

# cross-encoder/nli-deberta-v3-small label order: 0=contradiction, 1=entailment, 2=neutral
_LABEL_SCORES = np.array([0.0, 1.0, 0.5])


def compute(nli_outputs: np.ndarray) -> float:
    """Score logical flow between consecutive completion sentences.

    nli_outputs: shape (n_consecutive_pairs, 3), pre-sliced from the batched call.
    Returns a value in [0, 1] where 1.0 means every consecutive pair entails.
    """
    if nli_outputs.size == 0:
        return 1.0
    labels = nli_outputs.argmax(axis=-1)
    scores = _LABEL_SCORES[labels]
    return float(scores.mean())
