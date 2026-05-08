import nltk
import textstat


def compute(completion: str) -> float:
    sentences = nltk.sent_tokenize(completion)
    if len(sentences) < 2:
        return 1.0
    grades = [textstat.flesch_kincaid_grade(s) for s in sentences]
    increasing = sum(1 for i in range(len(grades) - 1) if grades[i + 1] > grades[i])
    return increasing / (len(sentences) - 1)
