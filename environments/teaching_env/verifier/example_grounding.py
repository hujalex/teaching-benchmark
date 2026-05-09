import re
import nltk
import spacy

_EXAMPLE_MARKERS = frozenset(["for example", "e.g.", "consider", "suppose", "imagine", "such as"])
_CODE_RE = re.compile(r'`[^`]+`|\d+')
# Matches LaTeX inline math containing a digit: \( 4! \), \( n=2 \), etc.
_LATEX_NUM_RE = re.compile(r'\\\(.*?\d+.*?\\\)|\$[^$]*\d+[^$]*\$')


def compute(completion: str, nlp: spacy.Language) -> float:
    sentences = nltk.sent_tokenize(completion)
    example_sents = [s for s in sentences if any(m in s.lower() for m in _EXAMPLE_MARKERS)]

    if not example_sents:
        return 0.0

    grounded = 0
    for sent in example_sents:
        doc = nlp(sent)
        if (
            any(t.like_num for t in doc)
            or doc.ents
            or _CODE_RE.search(sent)
            or _LATEX_NUM_RE.search(sent)
        ):
            grounded += 1

    return grounded / len(example_sents)
