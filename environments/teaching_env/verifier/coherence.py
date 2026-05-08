import spacy

_CONNECTIVES = frozenset([
    "therefore", "however", "because", "thus", "hence",
    "consequently", "this means", "as a result",
])


def compute(completion: str, nlp: spacy.Language) -> float:
    """Score textual coherence via pronoun resolution + connective usage.

    The supplied ``nlp`` pipeline is expected to have the ``coreferee``
    component registered (see ``TeachingVerifier.__init__``).
    """
    doc = nlp(completion)

    pronouns = [t for t in doc if t.pos_ == "PRON"]
    if pronouns:
        # coreferee attaches a chain to each token that participates in coref.
        # A pronoun is "resolved" if it belongs to a chain with another mention.
        resolved = 0
        for tok in pronouns:
            chains = tok._.coref_chains
            if any(len(chain) > 1 for chain in chains):
                resolved += 1
        pronoun_score = resolved / len(pronouns)
    else:
        pronoun_score = 1.0

    sentences = list(doc.sents)
    if not sentences:
        return 0.6 * pronoun_score

    with_connective = sum(
        1 for s in sentences
        if any(c in s.text.lower() for c in _CONNECTIVES)
    )
    connective_score = with_connective / len(sentences)

    return 0.6 * pronoun_score + 0.4 * connective_score
