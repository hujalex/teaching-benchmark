def _first_mention(completion_lower: str, surface_forms: list) -> int:
    positions = [completion_lower.find(sf.lower()) for sf in surface_forms if sf]
    valid = [p for p in positions if p >= 0]
    return min(valid) if valid else -1


def compute(completion: str, kg: dict) -> float:
    edges = [e for e in kg.get("prerequisite_edges", []) if e.get("confidence") == "high"]
    if not edges:
        return 1.0

    concept_map = {c["concept_id"]: c for c in kg.get("concepts", [])}
    completion_lower = completion.lower()

    violations = 0
    for edge in edges:
        c_forms = concept_map.get(edge["concept"], {}).get("surface_forms", [edge["concept"]])
        p_forms = concept_map.get(edge["prereq"], {}).get("surface_forms", [edge["prereq"]])

        c_pos = _first_mention(completion_lower, c_forms)
        p_pos = _first_mention(completion_lower, p_forms)

        # Violation: concept appears before its prerequisite (or prereq not mentioned)
        if c_pos >= 0 and (p_pos < 0 or p_pos > c_pos):
            violations += 1

    return 1.0 - (violations / len(edges))
