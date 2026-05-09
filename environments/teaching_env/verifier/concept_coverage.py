import re


def _strip_latex(text: str) -> str:
    """Remove LaTeX delimiters and common commands, leaving the core symbols."""
    text = re.sub(r'\\\(|\\\)|\$', '', text)
    text = re.sub(r'\\[a-zA-Z]+\s*', '', text)
    return text.strip()


def compute(completion: str, kg: dict) -> float:
    concepts = kg.get("concepts", [])
    if not concepts:
        return 1.0
    completion_lower = completion.lower()
    completion_stripped = _strip_latex(completion_lower)

    def _mentioned(c: dict) -> bool:
        forms = c.get("surface_forms", [c.get("canonical", "")])
        for sf in forms:
            sf_lower = sf.lower()
            if sf_lower in completion_lower:
                return True
            # Also match after stripping LaTeX markup from both sides
            if _strip_latex(sf_lower) in completion_stripped:
                return True
        return False

    mentioned = sum(1 for c in concepts if _mentioned(c))
    return mentioned / len(concepts)
