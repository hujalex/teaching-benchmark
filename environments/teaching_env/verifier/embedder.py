"""Lightweight sentence embedder backed by fastembed (ONNX Runtime).

Replaces ``sentence_transformers.SentenceTransformer`` to drop PyTorch as a
transitive dependency. The public surface mirrors ``model.encode(list[str])``
returning a numpy ``ndarray`` so callers don't need to know about the swap.

The default model (``BAAI/bge-small-en-v1.5``) is ~130 MB on first load and
produces 384-dim embeddings — comparable footprint to the previous
``all-MiniLM-L6-v2`` (~80 MB, 384-dim) but downloaded via the HuggingFace
Hub the first time it's used. The ONNX runtime backing fastembed installs
in ~150 MB versus the ~750 MB CPU build of PyTorch.
"""

from __future__ import annotations

import numpy as np


class Embedder:
    """Thin wrapper exposing a SentenceTransformer-compatible ``encode`` API."""

    DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
    DEFAULT_DIM = 384

    def __init__(self, model_name: str = DEFAULT_MODEL):
        # Lazy import: fastembed pulls in onnxruntime (~150 MB) and we want
        # the parent package to import cheaply for tests that just verify
        # the environment loads.
        from fastembed import TextEmbedding

        self.model_name = model_name
        self._model = TextEmbedding(model_name=model_name)

    def encode(self, sentences: list[str]) -> np.ndarray:
        """Return a ``(len(sentences), dim)`` array of embeddings.

        Mirrors ``SentenceTransformer.encode`` semantics for the call sites we
        use — we don't expose batch_size / show_progress / convert_to_numpy
        kwargs because none of the verifier modules pass them.
        """
        if not sentences:
            return np.empty((0, self.DEFAULT_DIM))
        # ``TextEmbedding.embed`` returns a generator of np.ndarray rows.
        return np.array(list(self._model.embed(sentences)))
