import nltk
import spacy

_CONTENT_POS = frozenset(["NOUN", "VERB", "ADJ", "ADV"])


def compute(completion: str, nlp: spacy.Language) -> float:
    sentences = nltk.sent_tokenize(completion)
    if not sentences:
        return 0.0

    scores = []
    for sent in sentences:
        doc = nlp(sent)
        tokens = [t for t in doc if not t.is_space]
        if not tokens:
            continue
        content = sum(1 for t in tokens if t.pos_ in _CONTENT_POS)
        scores.append(content / len(tokens))

    return float(sum(scores) / len(scores)) if scores else 0.0
