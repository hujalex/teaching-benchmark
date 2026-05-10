"""ONNX Runtime NLI cross-encoder — no PyTorch required.

Uses ``optimum[onnxruntime]`` to load the pre-exported ONNX weights from
``cross-encoder/nli-deberta-v3-small`` on the HuggingFace Hub.  The ``onnx/``
subfolder in that repo contains ``model.onnx`` (and several quantized
variants), so no export step or torch installation is needed at runtime.

Label order (matches the original CrossEncoder):
  0 → contradiction  (score 0.0)
  1 → entailment     (score 1.0)
  2 → neutral        (score 0.5)
"""

from __future__ import annotations

import numpy as np


class NLIModel:
    """Thin wrapper around ORTModelForSequenceClassification.

    ``predict(pairs)`` mirrors the ``CrossEncoder.predict`` API so call sites
    in ``teaching_verifier`` need no changes beyond swapping the class.
    """

    MODEL_ID = "cross-encoder/nli-deberta-v3-small"
    BATCH_SIZE = 32

    def __init__(self):
        from optimum.onnxruntime import ORTModelForSequenceClassification
        from transformers import AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(self.MODEL_ID)
        # ONNX files live in the onnx/ subfolder of the Hub repo.
        self._model = ORTModelForSequenceClassification.from_pretrained(
            self.MODEL_ID,
            subfolder="onnx",
            file_name="model.onnx",
        )

    def predict(self, pairs: list[tuple[str, str]]) -> np.ndarray:
        """Return logits of shape ``(n_pairs, 3)`` for each (premise, hypothesis) pair."""
        if not pairs:
            return np.empty((0, 3))

        batches: list[np.ndarray] = []
        for i in range(0, len(pairs), self.BATCH_SIZE):
            batch = pairs[i : i + self.BATCH_SIZE]
            enc = self._tokenizer(
                [p[0] for p in batch],
                [p[1] for p in batch],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="np",
            )
            outputs = self._model(**enc)
            batches.append(np.array(outputs.logits))

        return np.concatenate(batches, axis=0)
