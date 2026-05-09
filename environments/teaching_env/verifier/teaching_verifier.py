# Required dependencies:
# pip install spacy sentence-transformers keybert networkx nltk textstat datasets scikit-learn
# python -m spacy download en_core_web_sm

import numpy as np
import nltk
import spacy
from sentence_transformers import SentenceTransformer, CrossEncoder
from datasets import load_dataset

from .base import BaseVerifier, clean_source
from . import (
    concept_coverage,
    sentence_coverage,
    contradiction_detection,
    entailment_chain,
    prerequisite_order,
    example_grounding,
    information_density,
    readability_curve,
    originality,
)


class TeachingVerifier(BaseVerifier):
    WEIGHTS = {
        "concept_coverage":    0.20,
        "sentence_coverage":   0.18,
        "contradiction":       0.20,
        "entailment_chain":    0.16,
        "order":               0.10,
        "example_grounding":   0.01,
        "information_density": 0.09,
        "readability_curve":   0.01,
        "originality":         0.05,
    }

    # Originality weight scale (for reference):
    #   math/chemistry/physics  0.02–0.03  — fixed notation, unavoidable term reuse
    #   biology/CS              0.04–0.05  — moderate vocabulary flexibility
    #   business                0.07       — many equivalent phrasings available
    #   humanities              0.10       — narrative language is highly paraphrasable
    SUBJECT_WEIGHTS: dict[str, dict[str, float]] = {
        "math": {
            "concept_coverage":    0.22,
            "sentence_coverage":   0.15,
            "contradiction":       0.22,
            "entailment_chain":    0.20,
            "order":               0.12,
            "example_grounding":   0.03,
            "information_density": 0.03,
            "readability_curve":   0.01,
            "originality":         0.02,
        },
        "chemistry": {
            "concept_coverage":    0.22,
            "sentence_coverage":   0.18,
            "contradiction":       0.22,
            "entailment_chain":    0.18,
            "order":               0.11,
            "example_grounding":   0.03,
            "information_density": 0.02,
            "readability_curve":   0.01,
            "originality":         0.03,
        },
        "physics": {
            "concept_coverage":    0.22,
            "sentence_coverage":   0.16,
            "contradiction":       0.22,
            "entailment_chain":    0.19,
            "order":               0.11,
            "example_grounding":   0.04,
            "information_density": 0.02,
            "readability_curve":   0.01,
            "originality":         0.03,
        },
        "biology": {
            "concept_coverage":    0.22,
            "sentence_coverage":   0.20,
            "contradiction":       0.16,
            "entailment_chain":    0.14,
            "order":               0.10,
            "example_grounding":   0.06,
            "information_density": 0.06,
            "readability_curve":   0.02,
            "originality":         0.04,
        },
        "computer_science": {
            "concept_coverage":    0.20,
            "sentence_coverage":   0.15,
            "contradiction":       0.20,
            "entailment_chain":    0.16,
            "order":               0.12,
            "example_grounding":   0.07,
            "information_density": 0.04,
            "readability_curve":   0.01,
            "originality":         0.05,
        },
        "business": {
            "concept_coverage":    0.16,
            "sentence_coverage":   0.16,
            "contradiction":       0.15,
            "entailment_chain":    0.13,
            "order":               0.10,
            "example_grounding":   0.09,
            "information_density": 0.08,
            "readability_curve":   0.06,
            "originality":         0.07,
        },
        "humanities": {
            "concept_coverage":    0.12,
            "sentence_coverage":   0.20,
            "contradiction":       0.12,
            "entailment_chain":    0.10,
            "order":               0.06,
            "example_grounding":   0.14,
            "information_density": 0.06,
            "readability_curve":   0.10,
            "originality":         0.10,
        },
    }

    def __init__(self, kg_dataset_path: str | None = None):
        self._st_model = SentenceTransformer("all-MiniLM-L6-v2")
        self._nli_model = CrossEncoder("cross-encoder/nli-deberta-v3-small")
        self._nlp = spacy.load("en_core_web_sm")
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
        self.kg_index: dict = {}
        if kg_dataset_path:
            ds = load_dataset(kg_dataset_path, split="train")
            self.kg_index = {row["topic"]: row["kg"] for row in ds}

    def score_all(self, prompt: str, completion: str, metadata: dict) -> dict:
        """Run all metrics and return sub-scores plus a 'composite' key."""
        topic = metadata["topic"]
        # Prefer KG injected directly (from info dict) over the index lookup
        kg = metadata.get("kg") or self.kg_index.get(
            topic, {"concepts": [], "prerequisite_edges": []}
        )
        weights = self.SUBJECT_WEIGHTS.get(metadata.get("subject", ""), self.WEIGHTS)
        source_text = clean_source(prompt)

        src_sents = nltk.sent_tokenize(source_text)
        comp_sents = nltk.sent_tokenize(completion)

        pairs_3 = [(s, c) for s in src_sents for c in comp_sents]
        pairs_4 = [(comp_sents[i], comp_sents[i + 1]) for i in range(len(comp_sents) - 1)]

        all_pairs = pairs_3 + pairs_4
        all_nli = self._nli_model.predict(all_pairs) if all_pairs else np.empty((0, 3))

        nli_3 = all_nli[: len(pairs_3)] if pairs_3 else np.empty((0, 3))
        nli_4 = all_nli[len(pairs_3) :] if pairs_4 else np.empty((0, 3))

        scores = {
            "concept_coverage":    self._concept_coverage(completion, kg),
            "sentence_coverage":   self._sentence_coverage(source_text, completion),
            "contradiction":       self._contradiction(nli_3, len(src_sents), len(comp_sents)),
            "entailment_chain":    self._entailment_chain(nli_4),
            "order":               self._prerequisite_order(completion, kg),
            "example_grounding":   self._example_grounding(completion),
            "information_density": self._information_density(completion),
            "readability_curve":   self._readability_curve(completion),
            "originality":         self._originality(source_text, completion),
        }

        scores["composite"] = sum(scores[k] * weights[k] for k in weights)
        return scores

    def verify(self, prompt: str, completion: str, metadata: dict) -> float:
        return self.score_all(prompt, completion, metadata)["composite"]

    # ------------------------------------------------------------------ #
    # Private metric methods                                               #
    # ------------------------------------------------------------------ #

    def _concept_coverage(self, completion: str, kg: dict) -> float:
        score = concept_coverage.compute(completion, kg)
        self._log("concept_coverage", score)
        return score

    def _sentence_coverage(self, source_text: str, completion: str) -> float:
        score = sentence_coverage.compute(source_text, completion, self._st_model)
        self._log("sentence_coverage", score)
        return score

    def _contradiction(self, nli_outputs: np.ndarray, n_source: int, n_comp: int) -> float:
        score = contradiction_detection.compute(nli_outputs, n_source, n_comp)
        self._log("contradiction", score)
        return score

    def _entailment_chain(self, nli_outputs: np.ndarray) -> float:
        score = entailment_chain.compute(nli_outputs)
        self._log("entailment_chain", score)
        return score

    def _prerequisite_order(self, completion: str, kg: dict) -> float:
        score = prerequisite_order.compute(completion, kg)
        self._log("prerequisite_order", score)
        return score

    def _example_grounding(self, completion: str) -> float:
        score = example_grounding.compute(completion, self._nlp)
        self._log("example_grounding", score)
        return score

    def _information_density(self, completion: str) -> float:
        score = information_density.compute(completion, self._nlp)
        self._log("information_density", score)
        return score

    def _readability_curve(self, completion: str) -> float:
        score = readability_curve.compute(completion)
        self._log("readability_curve", score)
        return score

    def _originality(self, source_text: str, completion: str) -> float:
        score = originality.compute(source_text, completion)
        self._log("originality", score)
        return score


# ------------------------------------------------------------------ #
# Smoke test                                                           #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    _SOURCE = (
        "Newton's second law of motion states that the acceleration of an object is "
        "directly proportional to the net force acting on it and inversely proportional "
        "to its mass. Mathematically, F = ma. Force is measured in Newtons (N), mass in "
        "kilograms (kg), and acceleration in meters per second squared (m/s²). "
        "Before understanding force, one must understand the concept of mass and acceleration."
    )

    _COMPLETION = (
        "Newton's second law tells us how force, mass, and acceleration are related. "
        "For example, consider a 5 kg box: if we apply a 10 N force, it accelerates at 2 m/s². "
        "This means that heavier objects require more force to achieve the same acceleration. "
        "Therefore, the relationship F = ma is fundamental to classical mechanics. "
        "However, this law applies only when mass is constant."
    )

    _KG = {
        "concepts": [
            {"concept_id": "force", "canonical": "force", "surface_forms": ["force", "F"]},
            {"concept_id": "mass", "canonical": "mass", "surface_forms": ["mass", "m"]},
            {"concept_id": "acceleration", "canonical": "acceleration", "surface_forms": ["acceleration", "a"]},
        ],
        "prerequisite_edges": [
            {"concept": "force", "prereq": "mass", "confidence": "high", "signal": "explicit"},
            {"concept": "force", "prereq": "acceleration", "confidence": "high", "signal": "explicit"},
        ],
    }

    verifier = TeachingVerifier()
    verifier.kg_index["newton_2nd_law"] = _KG

    print("Running smoke test...")
    composite = verifier.verify(
        _SOURCE,
        _COMPLETION,
        {"topic": "newton_2nd_law"},
    )
    print(f"\nComposite score: {composite:.4f}")
