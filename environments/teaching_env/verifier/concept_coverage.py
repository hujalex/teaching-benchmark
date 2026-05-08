def compute(completion: str, kg: dict) -> float:
    concepts = kg.get("concepts", [])
    if not concepts:
        return 1.0
    completion_lower = completion.lower()
    mentioned = sum(
        1 for c in concepts
        if any(sf.lower() in completion_lower for sf in c.get("surface_forms", [c.get("canonical", "")]))
    )
    return mentioned / len(concepts)
