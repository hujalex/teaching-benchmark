class BaseVerifier:
    def _log(self, name: str, score: float) -> None:
        print(f"  [{name}] {score:.4f}")

    def verify(self, prompt: str, completion: str, metadata: dict) -> float:
        raise NotImplementedError
