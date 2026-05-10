import re


def _strip_latex(text: str) -> str:
    """Remove LaTeX delimiters and common commands, leaving the core symbols."""
    text = re.sub(r'\\\(|\\\)|\$', '', text)
    text = re.sub(r'\\[a-zA-Z]+\s*', '', text)
    return text.strip()


def _word_boundary_match(pattern: str, text: str) -> bool:
    """Return True if pattern appears as a whole word (or phrase) in text."""
    escaped = re.escape(pattern)
    return bool(re.search(r'(?<!\w)' + escaped + r'(?!\w)', text))


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
            # Require word-boundary match so "use" doesn't hit "because" or "reuse".
            if _word_boundary_match(sf_lower, completion_lower):
                return True
            sf_stripped = _strip_latex(sf_lower)
            if sf_stripped and _word_boundary_match(sf_stripped, completion_stripped):
                return True
        return False

    mentioned = sum(1 for c in concepts if _mentioned(c))
    return mentioned / len(concepts)
