import numpy as np

# cross-encoder/nli-deberta-v3-small label order: 0=contradiction, 1=entailment, 2=neutral
_CONTRADICTION_LABEL = 0


def compute(nli_outputs: np.ndarray, n_source: int, n_comp: int) -> float:
    """Score how well the completion avoids contradicting the source.

    nli_outputs: shape (n_source * n_comp, 3), pre-sliced from the batched call.
    Returns a value in [0, 1] where 1.0 means no contradictions detected.

    Scoring: for each source sentence, measure what fraction of completion
    sentences contradict it.  Averaging this rate across source sentences and
    subtracting from 1.0 means a single contradicting sentence always causes a
    visible penalty — unlike a max-based formulation where a good sentence can
    mask many bad ones.
    """
    if n_source == 0 or n_comp == 0 or nli_outputs.size == 0:
        return 1.0
    labels = nli_outputs.argmax(axis=-1).reshape(n_source, n_comp)
    is_contradiction = (labels == _CONTRADICTION_LABEL)          # (n_source, n_comp) bool
    per_source_rate = is_contradiction.mean(axis=1)              # fraction of comp sents that contradict each source sent
    return float(1.0 - per_source_rate.mean())
