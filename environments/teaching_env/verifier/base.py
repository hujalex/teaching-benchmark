import re


def clean_source(text: str) -> str:
    """Remove PDF extraction artifacts that corrupt metric scoring."""
    text = re.sub(r'\(cid:\d+\)', '', text)
    text = re.sub(r'\|[\s\-|]+\|', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


class BaseVerifier:
    def _log(self, name: str, score: float) -> None:
        print(f"  [{name}] {score:.4f}")

    def verify(self, prompt: str, completion: str, metadata: dict) -> float:
        raise NotImplementedError
