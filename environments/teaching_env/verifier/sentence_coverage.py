import nltk
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def compute(source_text: str, completion: str, embedder) -> float:
    source_sents = nltk.sent_tokenize(source_text)
    comp_sents = nltk.sent_tokenize(completion)
    if not source_sents or not comp_sents:
        return 0.0
    src_embs = embedder.encode(source_sents)
    comp_embs = embedder.encode(comp_sents)
    sims = cosine_similarity(src_embs, comp_embs)
    return float(np.mean(sims.max(axis=1)))
