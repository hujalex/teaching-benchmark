"""KeyBERT-style keyword extraction without the KeyBERT dependency.

Algorithm:
  1. Generate candidate n-grams from the document via scikit-learn's
     ``CountVectorizer`` (handles stopword removal and lowercasing).
  2. Embed the document and each candidate with the shared :class:`Embedder`.
  3. Rank candidates by cosine similarity to the document embedding and
     return the top ``top_n``.

This matches the core KeyBERT algorithm (Grootendorst, 2020) at the
fidelity used by ``parsing.build_kg``. Diversity (MMR) is intentionally
omitted — ``build_kg`` collapses near-duplicates downstream when it derives
``surface_forms`` and matches them to prerequisite-edge regexes.
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def extract_keywords(
    text: str,
    embedder,
    top_n: int = 12,
    keyphrase_ngram_range: tuple[int, int] = (1, 2),
    stop_words: str | list[str] | None = "english",
) -> list[tuple[str, float]]:
    """Return ``[(phrase, similarity_score), ...]`` sorted by score desc."""
    if not text or not text.strip():
        return []

    try:
        vectorizer = CountVectorizer(
            ngram_range=keyphrase_ngram_range,
            stop_words=stop_words,
        ).fit([text])
    except ValueError:
        # Empty vocabulary after stopword removal (e.g. very short input).
        return []

    candidates = vectorizer.get_feature_names_out().tolist()
    if not candidates:
        return []

    doc_emb = embedder.encode([text])
    cand_embs = embedder.encode(candidates)
    if doc_emb.size == 0 or cand_embs.size == 0:
        return []

    sims = cosine_similarity(doc_emb, cand_embs)[0]
    # Argsort ascending, then take the last ``top_n`` and reverse for desc.
    top_idx = np.argsort(sims)[-top_n:][::-1]
    return [(candidates[i], float(sims[i])) for i in top_idx]
