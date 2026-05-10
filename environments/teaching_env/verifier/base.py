import re

# Lowercase runs longer than this with no spaces are almost certainly PDF
# word-merging artifacts (e.g. "contractandnotpurchaseanyrice").  Legitimate
# long technical terms (e.g. "deoxyribonucleicacid") still get caught, so we
# also require that the run contains at least one embedded common function word.
_MERGE_ARTIFACT = re.compile(
    r'\b(?=[a-z]{20,})(?=\w*(?:and|not|the|for|with|from|that|this|have|been|'
    r'ment|tion|ing|ness|ance|ence)\w*)([a-z]{20,})\b'
)


def clean_source(text: str) -> str:
    """Remove PDF extraction artifacts that corrupt metric scoring."""
    # Standard CID glyph substitution markers
    text = re.sub(r'\(cid:\d+\)', '', text)
    # Markdown table borders left by markitdown
    text = re.sub(r'\|[\s\-|]+\|', '', text)
    # Likely PDF word-merge artifacts: long lowercase runs containing embedded
    # function words (e.g. "contractandnotpurchaseanyrice")
    text = _MERGE_ARTIFACT.sub(' ', text)
    # Collapse excess blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


class BaseVerifier:
    def _log(self, name: str, score: float) -> None:
        print(f"  [{name}] {score:.4f}")

    def verify(self, prompt: str, completion: str, metadata: dict) -> float:
        raise NotImplementedError
