import json
import re
from pathlib import Path

from markitdown import MarkItDown
from datasets import Dataset, Features, Sequence, Value
import frontmatter
from markdown_it import MarkdownIt
from keybert import KeyBERT


md_parser = MarkdownIt()

_kw_model: KeyBERT | None = None


def _get_kw_model() -> KeyBERT:
    global _kw_model
    if _kw_model is None:
        _kw_model = KeyBERT()
    return _kw_model


# Patterns: (compiled regex, signal_name, swap_concept_prereq)
# swap=True means group 1 is the prereq, group 2 is the concept (e.g. "A is prereq for B")
_PREREQ_PATTERNS: list[tuple[re.Pattern, str, bool]] = [
    (re.compile(r"([\w][\w\s]+?)\s+requires?\s+([\w][\w\s]+?)(?=[.,;])", re.I), "requires", False),
    (re.compile(r"([\w][\w\s]+?)\s+depends?\s+on\s+([\w][\w\s]+?)(?=[.,;])", re.I), "depends_on", False),
    (re.compile(r"([\w][\w\s]+?)\s+is\s+(?:a\s+)?prerequisite\s+for\s+([\w][\w\s]+?)(?=[.,;])", re.I), "prerequisite_for", True),
    (re.compile(r"before\s+(?:understanding|learning|using)\s+([\w][\w\s]+?),\s*([\w][\w\s]+?)(?=[.,;])", re.I), "before_marker", False),
]


def build_kg(raw_text: str, top_n: int = 12) -> dict:
    """Extract a knowledge graph from raw markdown text using KeyBERT."""
    model = _get_kw_model()
    keywords = model.extract_keywords(
        raw_text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        top_n=top_n,
    )

    concepts = []
    cid_map: dict[str, str] = {}  # canonical_lower -> concept_id

    for kw, _ in keywords:
        cid = re.sub(r"\s+", "_", kw.strip().lower())
        words = kw.split()
        forms: set[str] = {kw, kw.lower()}
        for w in words:
            if len(w) > 3:
                forms.add(w)
                forms.add(w.lower())
        concepts.append({"concept_id": cid, "canonical": kw, "surface_forms": sorted(forms)})
        cid_map[kw.lower()] = cid

    def _match_concept(text: str) -> str | None:
        t = text.strip().lower()
        return next(
            (cid for canon, cid in cid_map.items() if canon in t or t in canon),
            None,
        )

    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for pattern, signal, swap in _PREREQ_PATTERNS:
        for m in pattern.finditer(raw_text):
            g1, g2 = m.group(1), m.group(2)
            concept_text, prereq_text = (g2, g1) if swap else (g1, g2)
            c_id = _match_concept(concept_text)
            p_id = _match_concept(prereq_text)
            if c_id and p_id and c_id != p_id and (c_id, p_id) not in seen:
                edges.append({"concept": c_id, "prereq": p_id, "confidence": "high", "signal": signal})
                seen.add((c_id, p_id))

    return {"concepts": concepts, "prerequisite_edges": edges}


def convert_math_textbook_page_to_markdown(
    source_pdf: str | Path = "data/pdf/Math-textbook-page.pdf",
    output_markdown: str | Path = "data/markdown/Math-textbook-page.md",
) -> Path:
    source_path = Path(source_pdf)
    output_path = Path(output_markdown)

    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    converter = MarkItDown()
    conversion = converter.convert(str(source_path))

    markdown_text = getattr(conversion, "text_content", None)
    if markdown_text is None:
        markdown_text = getattr(conversion, "markdown", None)
    if markdown_text is None:
        markdown_text = str(conversion)
    markdown_text = markdown_text.strip()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown_text + "\n", encoding="utf-8")
    return output_path


def parse_markdown(filepath: Path) -> dict:
    post = frontmatter.load(filepath)
    tokens = md_parser.parse(post.content)

    headers = [
        token.children[0].content
        for token in tokens
        if token.type == "heading_open"
        and (next_token := tokens[tokens.index(token) + 1])
        and next_token.children
    ]

    sections = []
    current: list[str] = []
    for token in tokens:
        if token.type == "heading_open":
            if current:
                sections.append(" ".join(current).strip())
                current = []
        elif token.type == "inline" and token.children:
            current.append(token.content)
    if current:
        sections.append(" ".join(current).strip())

    return {
        "topic":        post.metadata.get("topic", filepath.stem),
        "source":       post.metadata.get("source", ""),
        "page_number":  post.metadata.get("page_number", -1),
        "subject":      post.metadata.get("subject", ""),
        "source_file":  filepath.name,
        "raw_text":     post.content,
        "headers":      headers,
        "sections":     sections,
        "num_sections": len(sections),
    }


def create_dataset(
    pdf_dir: str = "data/pdf",
    markdown_dir: str = "data/markdown",
) -> Dataset:
    pdf_path = Path(pdf_dir)
    md_path = Path(markdown_dir)
    if not pdf_path.exists():
        return Dataset.from_list(
            [
                {
                    "topic": "newton_second_law",
                    "source": "fallback",
                    "page_number": 1,
                    "subject": "physics",
                    "source_file": "fallback",
                    "raw_text": "Newton's second law connects force, mass, and acceleration.",
                    "headers": ["Newton's second law"],
                    "sections": ["Force is proportional to acceleration and scales with mass."],
                    "num_sections": 1,
                    "question": "Explain Newton's second law to a beginner.",
                    "info": json.dumps(
                        {
                            "topic": "newton_second_law",
                            "kg": {
                                "concepts": [
                                    {"concept_id": "force", "canonical": "force", "surface_forms": ["force", "F"]},
                                    {"concept_id": "mass", "canonical": "mass", "surface_forms": ["mass", "m"]},
                                    {
                                        "concept_id": "acceleration",
                                        "canonical": "acceleration",
                                        "surface_forms": ["acceleration", "a"],
                                    },
                                ],
                                "prerequisite_edges": [
                                    {
                                        "concept": "force",
                                        "prereq": "mass",
                                        "confidence": "high",
                                        "signal": "fallback",
                                    },
                                    {
                                        "concept": "force",
                                        "prereq": "acceleration",
                                        "confidence": "high",
                                        "signal": "fallback",
                                    },
                                ],
                            },
                        }
                    ),
                }
            ]
        )

    pdf_files = sorted(pdf_path.glob("*.pdf"))
    if not pdf_files:
        return Dataset.from_list(
            [
                {
                    "topic": "newton_second_law",
                    "source": "fallback",
                    "page_number": 1,
                    "subject": "physics",
                    "source_file": "fallback",
                    "raw_text": "Newton's second law connects force, mass, and acceleration.",
                    "headers": ["Newton's second law"],
                    "sections": ["Force is proportional to acceleration and scales with mass."],
                    "num_sections": 1,
                    "question": "Explain Newton's second law to a beginner.",
                    "info": json.dumps(
                        {
                            "topic": "newton_second_law",
                            "kg": {
                                "concepts": [
                                    {"concept_id": "force", "canonical": "force", "surface_forms": ["force", "F"]},
                                    {"concept_id": "mass", "canonical": "mass", "surface_forms": ["mass", "m"]},
                                    {
                                        "concept_id": "acceleration",
                                        "canonical": "acceleration",
                                        "surface_forms": ["acceleration", "a"],
                                    },
                                ],
                                "prerequisite_edges": [
                                    {
                                        "concept": "force",
                                        "prereq": "mass",
                                        "confidence": "high",
                                        "signal": "fallback",
                                    },
                                    {
                                        "concept": "force",
                                        "prereq": "acceleration",
                                        "confidence": "high",
                                        "signal": "fallback",
                                    },
                                ],
                            },
                        }
                    ),
                }
            ]
        )

    for pdf_file in pdf_files:
        output_md = md_path / f"{pdf_file.stem}.md"
        convert_math_textbook_page_to_markdown(source_pdf=pdf_file, output_markdown=output_md)

    files = sorted(md_path.glob("*.md"))
    if not files:
        raise ValueError(f"No markdown files found in {md_path}")

    records = []
    for f in files:
        page = parse_markdown(f)
        kg = build_kg(page["raw_text"])
        records.append({
            **page,
            # verifiers-framework columns
            "question": page["raw_text"],
            "info": json.dumps({"topic": page["topic"], "kg": kg}),
        })

    features = Features({
        "topic":        Value("string"),
        "source":       Value("string"),
        "page_number":  Value("int32"),
        "subject":      Value("string"),
        "source_file":  Value("string"),
        "raw_text":     Value("string"),
        "headers":      Sequence(Value("string")),
        "sections":     Sequence(Value("string")),
        "num_sections": Value("int32"),
        "question":     Value("string"),
        "info":         Value("string"),
    })

    return Dataset.from_list(records, features=features)
