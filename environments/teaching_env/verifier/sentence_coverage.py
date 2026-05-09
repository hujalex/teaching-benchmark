import numpy as np
import nltk
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


def compute(source_text: str, completion: str, model: SentenceTransformer) -> float:
    source_sents = nltk.sent_tokenize(source_text)
    comp_sents = nltk.sent_tokenize(completion)
    if not source_sents or not comp_sents:
        return 0.0
    src_embs = model.encode(source_sents)
    comp_embs = model.encode(comp_sents)
    sims = cosine_similarity(src_embs, comp_embs)
    return float(np.mean(sims.max(axis=1)))
