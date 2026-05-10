import nltk
import numpy as np
import spacy
from sklearn.metrics.pairwise import cosine_similarity

from .base import BaseVerifier, clean_source
from .embedder import Embedder
from .nli_model import NLIModel
from . import (
    concept_coverage,
    contradiction_detection,
    entailment_chain,
    prerequisite_order,
    example_grounding,
    information_density,
    readability_curve,
    originality,
)


class TeachingVerifier(BaseVerifier):
    # Subject-agnostic fallback. Leans STEM-ish (high contradiction + concept
    # coverage) but keeps every metric visible so a missing subject tag still
    # produces a usable signal.
    WEIGHTS = {
        "concept_coverage":    0.20,
        "sentence_coverage":   0.17,
        "contradiction":       0.18,
        "entailment_chain":    0.16,
        "order":               0.12,
        "example_grounding":   0.04,
        "information_density": 0.05,
        "readability_curve":   0.02,
        "originality":         0.06,
    }

    # Per-subject weights are tuned around two axes:
    #   1. metric reliability for the subject (NLI is unreliable on humanities;
    #      concept_coverage is unreliable when the KG is fuzzy);
    #   2. what the subject actually rewards pedagogically (math = order +
    #      logical chain; humanities = voice + readability; business = cases).
    # Rule of thumb: do not put high weight on a metric that misfires for the
    # subject — it amplifies noise where it matters most.
    #
    # Originality scale (for reference):
    #   math                    0.02       — fixed notation, F=ma is F=ma
    #   chemistry/physics       0.02–0.03  — formulae and units constrain phrasing
    #   biology/CS              0.05       — moderate vocabulary flexibility
    #   business                0.09       — many equivalent phrasings available
    #   humanities              0.15       — voice is the discriminating signal
    SUBJECT_WEIGHTS: dict[str, dict[str, float]] = {
      
        "math": {
            "concept_coverage":    0.20,
            "sentence_coverage":   0.13,
            "contradiction":       0.22,
            "entailment_chain":    0.20,
            "order":               0.15,
            "example_grounding":   0.04,
            "information_density": 0.03,
            "readability_curve":   0.01,
            "originality":         0.02,
        },
      
        "chemistry": {
            "concept_coverage":    0.20,
            "sentence_coverage":   0.17,
            "contradiction":       0.22,
            "entailment_chain":    0.18,
            "order":               0.13,
            "example_grounding":   0.04,
            "information_density": 0.02,
            "readability_curve":   0.01,
            "originality":         0.03,
        },
      
        "physics": {
            "concept_coverage":    0.20,
            "sentence_coverage":   0.14,
            "contradiction":       0.22,
            "entailment_chain":    0.20,
            "order":               0.13,
            "example_grounding":   0.06,
            "information_density": 0.02,
            "readability_curve":   0.01,
            "originality":         0.02,
        },
     
        "biology": {
            "concept_coverage":    0.22,
            "sentence_coverage":   0.20,
            "contradiction":       0.14,
            "entailment_chain":    0.13,
            "order":               0.09,
            "example_grounding":   0.08,
            "information_density": 0.07,
            "readability_curve":   0.02,
            "originality":         0.05,
        },
    
        "computer_science": {
            "concept_coverage":    0.18,
            "sentence_coverage":   0.14,
            "contradiction":       0.18,
            "entailment_chain":    0.18,
            "order":               0.13,
            "example_grounding":   0.08,
            "information_density": 0.04,
            "readability_curve":   0.02,
            "originality":         0.05,
        },
     
        "business": {
            "concept_coverage":    0.15,
            "sentence_coverage":   0.16,
            "contradiction":       0.13,
            "entailment_chain":    0.12,
            "order":               0.08,
            "example_grounding":   0.12,
            "information_density": 0.08,
            "readability_curve":   0.07,
            "originality":         0.09,
        },
        "humanities": {
            "concept_coverage":    0.13,
            "sentence_coverage":   0.20,
            "contradiction":       0.10,
            "entailment_chain":    0.10,
            "order":               0.05,
            "example_grounding":   0.05,
            "information_density": 0.07,
            "readability_curve":   0.15,
            "originality":         0.15,
        },
    }

    def __init__(self):
        self._embedder = Embedder()
        self._nli_model = NLIModel()
        try:
            self._nlp = spacy.load("en_core_web_sm")
        except OSError:
            from spacy.cli import download
            download("en_core_web_sm")
            self._nlp = spacy.load("en_core_web_sm")
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
        self.kg_index: dict = {}

    def score_all(self, prompt: str, completion: str, metadata: dict) -> dict:
        """Run all metrics and return sub-scores plus a 'composite' key."""
        topic = metadata["topic"]
        kg = metadata.get("kg") or self.kg_index.get(
            topic, {"concepts": [], "prerequisite_edges": []}
        )
        weights = self.SUBJECT_WEIGHTS.get(metadata.get("subject", ""), self.WEIGHTS)
        source_text = clean_source(prompt)

        src_sents = nltk.sent_tokenize(source_text)
        comp_sents = nltk.sent_tokenize(completion)

        # Embeddings computed once and shared across embedding-based metrics.
        src_embs = self._embedder.encode(src_sents) if src_sents else np.empty((0, Embedder.DEFAULT_DIM))
        comp_embs = self._embedder.encode(comp_sents) if comp_sents else np.empty((0, Embedder.DEFAULT_DIM))

        # Batch NLI inference for contradiction and entailment metrics.
        pairs_src_x_comp = [(s, c) for s in src_sents for c in comp_sents]
        pairs_consecutive = [(comp_sents[i], comp_sents[i + 1]) for i in range(len(comp_sents) - 1)]

        all_pairs = pairs_src_x_comp + pairs_consecutive
        all_nli = self._nli_model.predict(all_pairs) if all_pairs else np.empty((0, 3))

        n3 = len(pairs_src_x_comp)
        nli_src_x_comp = all_nli[:n3] if pairs_src_x_comp else np.empty((0, 3))
        nli_consecutive = all_nli[n3:] if pairs_consecutive else np.empty((0, 3))

        # Shared similarity matrix — used by both sentence_coverage and copy detection.
        sims = (
            cosine_similarity(src_embs, comp_embs)
            if src_embs.size > 0 and comp_embs.size > 0
            else np.empty((0, 0))
        )

        scores = {
            "concept_coverage":    self._concept_coverage(completion, kg),
            "sentence_coverage":   self._sentence_coverage(sims),
            "contradiction":       self._contradiction(nli_src_x_comp, len(src_sents), len(comp_sents)),
            "entailment_chain":    self._entailment_chain(nli_consecutive),
            "order":               self._prerequisite_order(completion, kg),
            "example_grounding":   self._example_grounding(completion),
            "information_density": self._information_density(completion),
            "readability_curve":   self._readability_curve(completion),
            "originality":         self._originality(source_text, completion),
            "copy_rate":           self._copy_rate(sims),
        }

        composite = sum(scores[k] * weights[k] for k in weights)

        # Apply copy penalty: ramps from 0 at copy_rate=0.90 to 0.50 at copy_rate=1.0,
        # halving the composite for a verbatim copy regardless of subject weights.
        copy_penalty = max(0.0, (scores["copy_rate"] - 0.90) / 0.10)
        scores["composite"] = composite * (1.0 - copy_penalty * 0.50)
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

    def _sentence_coverage(self, sims: np.ndarray) -> float:
        if sims.size == 0:
            return 0.0
        score = float(np.mean(sims.max(axis=1)))
        self._log("sentence_coverage", score)
        return score

    def _copy_rate(self, sims: np.ndarray) -> float:
        """Per completion sentence: similarity to its nearest source sentence.

        Mean across completion sentences.  Values near 1.0 indicate the
        completion reproduces source sentences verbatim.  This reuses the
        already-computed sims matrix at zero extra inference cost.
        """
        if sims.size == 0:
            return 0.0
        score = float(np.mean(sims.max(axis=0)))
        self._log("copy_rate", score)
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
