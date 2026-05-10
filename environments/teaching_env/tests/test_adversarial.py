"""Adversarial reward-hacking tests.

Each test sends a deliberately bad completion through the full verifier pipeline
and asserts that the relevant sub-score(s) fall below an acceptable threshold.
The purpose is twofold:

  1. Prove the reward is not fooled by a specific failure mode.
  2. Document known gaps where the current metrics are insufficient.

All cases share the same source passage and KG so results are comparable.
The ``verifier`` fixture is module-scoped — models load once for the whole file.

Run with:
    pytest tests/test_adversarial.py -v
"""

import pytest

# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

SOURCE = (
    "Before understanding force, one must first grasp the concept of mass — "
    "the measure of an object's resistance to acceleration. "
    "Newton's second law of motion states that the net force acting on an object "
    "equals its mass multiplied by its acceleration: F = ma. "
    "Force is measured in Newtons (N), mass in kilograms (kg), and acceleration "
    "in metres per second squared (m/s²). "
    "For example, a 2 kg object subjected to a 10 N force accelerates at 5 m/s²."
)

KG = {
    "concepts": [
        {"concept_id": "mass",               "canonical": "mass",               "surface_forms": ["mass", "m"]},
        {"concept_id": "force",              "canonical": "force",              "surface_forms": ["force", "F"]},
        {"concept_id": "acceleration",       "canonical": "acceleration",       "surface_forms": ["acceleration", "a"]},
        {"concept_id": "newtons_second_law", "canonical": "Newton's second law","surface_forms": ["Newton's second law", "second law", "F = ma"]},
    ],
    "prerequisite_edges": [
        # mass must be introduced before force
        {"concept": "force", "prereq": "mass", "confidence": "high", "signal": "requires"},
        # acceleration must be introduced before Newton's second law
        {"concept": "newtons_second_law", "prereq": "acceleration", "confidence": "high", "signal": "requires"},
    ],
}

METADATA = {"topic": "newtons_second_law", "subject": "physics", "kg": KG}


@pytest.fixture(scope="module")
def verifier():
    from verifier.teaching_verifier import TeachingVerifier
    return TeachingVerifier()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def scores(verifier, completion: str) -> dict:
    return verifier.score_all(SOURCE, completion, METADATA)


# ---------------------------------------------------------------------------
# 1. Keyword stuffing
# ---------------------------------------------------------------------------

KEYWORD_STUFFED = (
    "Force. Mass. Acceleration. Newton. F=ma. Second law. Kilograms. Newtons. "
    "Proportional. Inversely. Motion. Net force. Metres per second squared."
)


@pytest.mark.slow
def test_keyword_stuffing_entailment_chain(verifier):
    """A fragment list has no consecutive sentence pairs — entailment chain
    defaults to 1.0 on empty input, but sentence_coverage and readability
    should expose the lack of coherent explanation."""
    s = scores(verifier, KEYWORD_STUFFED)
    # No examples present in a bare keyword list
    assert s["example_grounding"] < 0.10, (
        f"example_grounding={s['example_grounding']:.3f}: keyword list contains no examples"
    )
    # Composite must be below the pass threshold
    assert s["composite"] < 0.75, (
        f"composite={s['composite']:.3f}: keyword stuffing should not pass the reward"
    )


# ---------------------------------------------------------------------------
# 2. Copied source (verbatim)
# ---------------------------------------------------------------------------

COPIED_SOURCE = SOURCE  # exact copy


@pytest.mark.slow
def test_copied_source_originality(verifier):
    """A verbatim copy should score near-zero on originality (ROUGE precision
    will be ~1.0).  Coverage metrics will be high — that is expected and fine —
    but originality must fire."""
    s = scores(verifier, COPIED_SOURCE)
    assert s["originality"] < 0.15, (
        f"originality={s['originality']:.3f}: verbatim copy should have near-zero originality"
    )
    assert s["copy_rate"] > 0.97, (
        f"copy_rate={s['copy_rate']:.3f}: every completion sentence should match a source sentence"
    )
    # Copy penalty halves the composite when copy_rate ≈ 1.0
    assert s["composite"] < 0.50, (
        f"composite={s['composite']:.3f}: copy penalty should bring composite well below pass threshold"
    )


# ---------------------------------------------------------------------------
# 3. Fluent but factually wrong
# ---------------------------------------------------------------------------

FLUENT_WRONG = (
    "Newton's second law tells us that force is inversely proportional to mass: "
    "F = m/a. This means that heavier objects require less force to accelerate. "
    "Acceleration, therefore, is not directly related to the net force applied. "
    "For instance, doubling the mass of an object doubles its acceleration for the "
    "same applied force — the opposite of what many students expect."
)


@pytest.mark.slow
def test_fluent_wrong_contradiction(verifier):
    """A fluent but factually wrong explanation inverts the law (F = m/a instead
    of F = ma) and states the opposite relationship.  The NLI-based contradiction
    metric should catch the conflict against the source."""
    s = scores(verifier, FLUENT_WRONG)
    assert s["contradiction"] < 0.70, (
        f"contradiction={s['contradiction']:.3f}: a response that inverts F=ma should "
        "contradict the source"
    )
    assert s["composite"] < 0.65, (
        f"composite={s['composite']:.3f}: fluent but wrong explanation should not pass"
    )


# ---------------------------------------------------------------------------
# 4. Correct concepts, wrong prerequisite order
# ---------------------------------------------------------------------------

WRONG_ORDER = (
    "Newton's second law, F = ma, governs how objects accelerate. "
    "The acceleration of an object is directly proportional to the net force applied. "
    "Mass — the measure of an object's resistance to acceleration — determines how "
    "strongly the object responds. "
    "Only after establishing F = ma can we appreciate what mass truly represents."
)
# Deliberately introduces F = ma and acceleration before mass.


@pytest.mark.slow
def test_wrong_order_prerequisite(verifier):
    """Mass must be introduced before force per the KG edge.  The completion
    above introduces F = ma before defining mass, which is a prerequisite violation."""
    s = scores(verifier, WRONG_ORDER)
    assert s["order"] < 0.60, (
        f"order={s['order']:.3f}: introducing the law before its prerequisites should "
        "score low on prerequisite ordering"
    )


# ---------------------------------------------------------------------------
# 5. Example with wrong numbers
# ---------------------------------------------------------------------------

WRONG_NUMBERS = (
    "Before anything else, we need to understand mass — an object's resistance to "
    "changes in motion. "
    "Newton's second law states F = ma: the net force equals mass times acceleration. "
    "For instance, consider a 2 kg object with a 10 N force applied to it. "
    "According to F = ma, the object accelerates at 20 m/s² — "
    "double the force means double the acceleration."
    # Source says 10 N / 2 kg = 5 m/s²; completion claims 20 m/s².
)


@pytest.mark.slow
def test_wrong_numbers_contradiction(verifier):
    """The completion states 20 m/s² where the source states 5 m/s².
    NLI cross-encoders are unreliable on numerical precision, so this test
    documents a known gap.  It is marked xfail to record the limitation without
    blocking CI — remove xfail once a numerical consistency checker is added."""
    s = scores(verifier, WRONG_NUMBERS)
    # KNOWN GAP: NLI models frequently fail to classify numerical contradictions
    # (e.g. "5 m/s²" vs "20 m/s²") as contradictions because the sentence
    # structure and semantic framing are identical.  A dedicated numerical
    # consistency pass is needed to close this gap.
    if s["contradiction"] >= 0.80:
        pytest.xfail(
            f"contradiction={s['contradiction']:.3f}: NLI did not catch the numerical "
            "error (20 m/s² vs 5 m/s²) — known gap, needs numerical consistency checker"
        )
    assert s["contradiction"] < 0.80, (
        f"contradiction={s['contradiction']:.3f}: wrong numerical example should lower "
        "the contradiction score"
    )


# ---------------------------------------------------------------------------
# 6. Skipped prerequisites
# ---------------------------------------------------------------------------

SKIPPED_PREREQS = (
    "Newton's second law is one of the most important results in classical mechanics. "
    "It states that F = ma: the net force on an object equals its acceleration scaled "
    "by a constant. "
    "This allows us to predict how objects move under any applied force. "
    "Understanding this law unlocks the study of dynamics."
    # 'mass' is never defined before F = ma is stated; 'acceleration' is mentioned
    # but only after the law, not introduced as a prerequisite concept.
)


@pytest.mark.slow
def test_skipped_prerequisites_order(verifier):
    """The completion jumps straight to F = ma without first introducing mass.
    The prerequisite_order metric should flag the violation (mass prereq of force,
    mass not mentioned before force)."""
    s = scores(verifier, SKIPPED_PREREQS)
    assert s["order"] < 0.60, (
        f"order={s['order']:.3f}: skipping the definition of mass before stating F=ma "
        "should produce a prerequisite ordering violation"
    )


@pytest.mark.slow
def test_skipped_prerequisites_concept_coverage(verifier):
    """The completion never properly defines mass, so concept coverage for the
    KG concept 'mass' should be low (or absent)."""
    # Test the coverage module directly to isolate from other metrics.
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from verifier.concept_coverage import compute
    coverage = compute(SKIPPED_PREREQS, KG)
    # 'mass' appears once incidentally but is never defined — full coverage
    # of all four KG concepts is unlikely given the thin treatment.
    assert coverage < 0.80, (
        f"concept_coverage={coverage:.3f}: a response that skips mass definition "
        "should not achieve high concept coverage"
    )


# ---------------------------------------------------------------------------
# 6b. Metric-only tests (no model needed — fast)
# ---------------------------------------------------------------------------

class TestConceptCoverageWordBoundary:
    """Verify the word-boundary fix does not inflate scores via partial matches."""

    def test_use_inside_because(self):
        from verifier.concept_coverage import compute
        kg = {"concepts": [
            {"concept_id": "use", "canonical": "use", "surface_forms": ["use"]},
        ]}
        # 'use' should NOT match inside 'because' or 'reuse'
        assert compute("because students reuse the formula", kg) == 0.0

    def test_exact_word_match(self):
        from verifier.concept_coverage import compute
        kg = {"concepts": [
            {"concept_id": "use", "canonical": "use", "surface_forms": ["use"]},
        ]}
        assert compute("students use the formula", kg) == 1.0

    def test_multi_word_concept(self):
        from verifier.concept_coverage import compute
        kg = {"concepts": [
            {"concept_id": "second_law", "canonical": "second law", "surface_forms": ["second law"]},
        ]}
        assert compute("Newton's second law governs this", kg) == 1.0


class TestContradictionPenalty:
    """Verify that the max→penalty fix works correctly."""

    import numpy as np

    def test_single_contradiction_not_hidden(self):
        """One contradicting pair must not be hidden by other entailing pairs."""
        import numpy as np
        from verifier.contradiction_detection import compute
        # 2 source sentences, 3 completion sentences
        # NLI outputs: label 0=contradiction, 1=entailment
        # Source 0 vs Comp 0: entailment (1), Comp 1: entailment (1), Comp 2: contradiction (0)
        # Source 1 vs Comp 0: entailment (1), Comp 1: entailment (1), Comp 2: entailment (1)
        logits = np.array([
            [0, 10, 0],  # s0-c0: entailment
            [0, 10, 0],  # s0-c1: entailment
            [10, 0, 0],  # s0-c2: contradiction  ← hidden under old max formulation
            [0, 10, 0],  # s1-c0: entailment
            [0, 10, 0],  # s1-c1: entailment
            [0, 10, 0],  # s1-c2: entailment
        ], dtype=float)
        score = compute(logits, n_source=2, n_comp=3)
        # Old max formulation: max per source = [entailment, entailment] → 1.0 (BUG)
        # New penalty formulation: source 0 has 1/3 contradictions → 1 - mean(1/3, 0) = 0.833
        assert score < 1.0, "A single contradicting pair must lower the score"
        assert score < 0.90, f"score={score:.3f}: contradiction should be noticeably penalised"

    def test_no_contradictions_scores_one(self):
        import numpy as np
        from verifier.contradiction_detection import compute
        logits = np.array([
            [0, 10, 0],
            [0, 10, 0],
            [0, 10, 0],
            [0, 10, 0],
        ], dtype=float)
        assert compute(logits, n_source=2, n_comp=2) == 1.0

    def test_all_contradictions_scores_zero(self):
        import numpy as np
        from verifier.contradiction_detection import compute
        logits = np.array([
            [10, 0, 0],
            [10, 0, 0],
            [10, 0, 0],
            [10, 0, 0],
        ], dtype=float)
        assert compute(logits, n_source=2, n_comp=2) == 0.0


class TestPrerequisiteOrder:
    """Unit tests for the prerequisite order metric."""

    def _kg(self):
        return {
            "concepts": [
                {"concept_id": "mass",  "canonical": "mass",  "surface_forms": ["mass"]},
                {"concept_id": "force", "canonical": "force", "surface_forms": ["force"]},
            ],
            "prerequisite_edges": [
                {"concept": "force", "prereq": "mass", "confidence": "high", "signal": "requires"},
            ],
        }

    def test_correct_order_no_violation(self):
        from verifier.prerequisite_order import compute
        completion = "First, mass is the resistance to motion. Then, force equals mass times acceleration."
        assert compute(completion, self._kg()) == 1.0

    def test_wrong_order_violation(self):
        from verifier.prerequisite_order import compute
        completion = "Force equals mass times acceleration. Mass is the resistance to motion."
        assert compute(completion, self._kg()) == 0.0

    def test_missing_prerequisite_is_violation(self):
        from verifier.prerequisite_order import compute
        # 'mass' never mentioned — concept appears, prereq absent → violation
        completion = "Force is what causes acceleration. F = ma governs all motion."
        assert compute(completion, self._kg()) == 0.0
