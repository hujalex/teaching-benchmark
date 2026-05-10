"""ONNX Runtime NLI cross-encoder — no optimum/transformers/torch needed.

Uses ``onnxruntime`` + ``tokenizers`` + ``huggingface_hub`` directly.  All three
are transitive dependencies of ``fastembed``, so no new top-level deps are
required.

Loads the pre-exported ONNX weights from ``cross-encoder/nli-deberta-v3-small``:
the repo's ``onnx/`` subfolder contains ``model.onnx``, and the root contains
``tokenizer.json`` (fast-tokenizer port of the SentencePiece model).

Label order (matches the original CrossEncoder):
  0 → contradiction  (score 0.0)
  1 → entailment     (score 1.0)
  2 → neutral        (score 0.5)
"""

from __future__ import annotations

import numpy as np


class NLIModel:
    """Direct onnxruntime + tokenizers wrapper exposing a ``predict(pairs)`` API."""

    MODEL_REPO = "cross-encoder/nli-deberta-v3-small"
    MODEL_FILE = "onnx/model.onnx"
    TOKENIZER_FILE = "tokenizer.json"
    BATCH_SIZE = 16
    MAX_LENGTH = 512

    def __init__(self):
        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer
        import onnxruntime as ort

        model_path = hf_hub_download(self.MODEL_REPO, self.MODEL_FILE)
        tokenizer_path = hf_hub_download(self.MODEL_REPO, self.TOKENIZER_FILE)

        self._session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
        )
        self._tokenizer = Tokenizer.from_file(tokenizer_path)
        self._tokenizer.enable_truncation(
            max_length=self.MAX_LENGTH,
            strategy="longest_first",
        )
        # Cache the input names declared by the ONNX graph — DeBERTa typically
        # has input_ids + attention_mask + token_type_ids.
        self._input_names = {inp.name for inp in self._session.get_inputs()}

    def predict(self, pairs: list[tuple[str, str]]) -> np.ndarray:
        """Return logits of shape ``(n_pairs, 3)`` for each (premise, hypothesis) pair."""
        if not pairs:
            return np.empty((0, 3))

        all_logits: list[np.ndarray] = []
        for i in range(0, len(pairs), self.BATCH_SIZE):
            batch = pairs[i : i + self.BATCH_SIZE]
            # encode_batch with pair tuples produces premise+hypothesis tokens
            # with the correct special tokens and token_type_ids per the
            # tokenizer's post-processor.
            encodings = self._tokenizer.encode_batch(
                [(p[0], p[1]) for p in batch]
            )

            max_len = max(len(e.ids) for e in encodings)
            n = len(batch)
            input_ids = np.zeros((n, max_len), dtype=np.int64)
            attention_mask = np.zeros((n, max_len), dtype=np.int64)
            token_type_ids = np.zeros((n, max_len), dtype=np.int64)

            for j, enc in enumerate(encodings):
                k = len(enc.ids)
                input_ids[j, :k] = enc.ids
                attention_mask[j, :k] = enc.attention_mask
                token_type_ids[j, :k] = enc.type_ids

            feed = {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
            }
            if "token_type_ids" in self._input_names:
                feed["token_type_ids"] = token_type_ids

            outputs = self._session.run(None, feed)
            all_logits.append(outputs[0])  # logits is the first output

        return np.concatenate(all_logits, axis=0)
