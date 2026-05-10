import json
import re
from pathlib import Path

from datasets import Dataset, Features, Sequence, Value
import frontmatter
from markdown_it import MarkdownIt
from verifier.base import clean_source


md_parser = MarkdownIt()

_kw_embedder = None


def _get_kw_embedder(embedder=None):
    global _kw_embedder
    if embedder is not None:
        return embedder
    if _kw_embedder is None:
        from verifier.embedder import Embedder
        _kw_embedder = Embedder()
    return _kw_embedder


# Patterns: (compiled regex, signal_name, swap_concept_prereq)
# swap=True means group 1 is the prereq, group 2 is the concept (e.g. "A is prereq for B")
_PREREQ_PATTERNS: list[tuple[re.Pattern, str, bool]] = [
    (re.compile(r"([\w][\w\s]+?)\s+requires?\s+([\w][\w\s]+?)(?=[.,;])", re.I), "requires", False),
    (re.compile(r"([\w][\w\s]+?)\s+depends?\s+on\s+([\w][\w\s]+?)(?=[.,;])", re.I), "depends_on", False),
    (re.compile(r"([\w][\w\s]+?)\s+is\s+(?:a\s+)?prerequisite\s+for\s+([\w][\w\s]+?)(?=[.,;])", re.I), "prerequisite_for", True),
    (re.compile(r"before\s+(?:understanding|learning|using)\s+([\w][\w\s]+?),\s*([\w][\w\s]+?)(?=[.,;])", re.I), "before_marker", False),
]


_CONCEPT_NOISE = re.compile(r'[^a-zA-Z0-9\s\-]')   # non-word chars beyond hyphen
_MIN_CONCEPT_SIM = 0.25    # drop keywords below this similarity to the document
_MAX_CONCEPT_LEN = 40      # single-token concepts longer than this are PDF artifacts


def _is_valid_concept(kw: str, score: float) -> bool:
    """Return False for concepts that are likely PDF extraction noise."""
    if score < _MIN_CONCEPT_SIM:
        return False
    tokens = kw.split()
    for tok in tokens:
        # Reject tokens that are pure digits or longer than the artifact threshold
        if tok.isdigit() or len(tok) > _MAX_CONCEPT_LEN:
            return False
        # Reject tokens with non-alphanumeric characters beyond hyphens
        if _CONCEPT_NOISE.search(tok):
            return False
    return True


def build_kg(raw_text: str, top_n: int = 12, embedder=None) -> dict:
    """Extract a knowledge graph from raw markdown text."""
    from verifier.keyword_extractor import extract_keywords
    emb = _get_kw_embedder(embedder)
    keywords = extract_keywords(raw_text, emb, top_n=top_n)

    concepts = []
    cid_map: dict[str, str] = {}  # canonical_lower -> concept_id

    for kw, score in keywords:
        if not _is_valid_concept(kw, score):
            continue
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


def convert_pdf_to_markdown(
    source_pdf: str | Path,
    output_markdown: str | Path,
) -> Path:
    source_path = Path(source_pdf)
    output_path = Path(output_markdown)

    if output_path.exists():
        return output_path

    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    from markitdown import MarkItDown
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
        next_token.children[0].content
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


def _subject_label(folder_name: str) -> str:
    """Normalise a folder name to a subject label (hyphens → underscores)."""
    return folder_name.replace("-", "_")


def create_dataset(
    pdf_dir: str | Path | None = None,
    markdown_dir: str | Path | None = None,
    embedder=None,
) -> Dataset:
    _here = Path(__file__).parent
    pdf_path = Path(pdf_dir) if pdf_dir else _here / "data" / "pdf"
    md_path = Path(markdown_dir) if markdown_dir else _here / "data" / "markdown"

    # Discover subject subdirectories; fall back to flat root layout.
    subject_dirs = sorted(d for d in pdf_path.iterdir() if d.is_dir()) if pdf_path.exists() else []

    if subject_dirs:
        # Subject-structured layout: pdf/<subject>/*.pdf → markdown/<subject>/*.md
        for subject_dir in subject_dirs:
            subject_md_path = md_path / subject_dir.name
            for pdf_file in sorted(subject_dir.glob("*.pdf")):
                output_md = subject_md_path / f"{pdf_file.stem}.md"
                convert_pdf_to_markdown(source_pdf=pdf_file, output_markdown=output_md)

        # Collect (markdown_path, folder_name) pairs from every subject subdir.
        md_files: list[tuple[Path, str]] = []
        for subject_dir in subject_dirs:
            subject_md_path = md_path / subject_dir.name
            md_files.extend(
                (f, subject_dir.name) for f in sorted(subject_md_path.glob("*.md"))
            )
    else:
        # Flat legacy layout: pdf/*.pdf → markdown/*.md
        for pdf_file in sorted(pdf_path.glob("*.pdf")):
            output_md = md_path / f"{pdf_file.stem}.md"
            convert_pdf_to_markdown(source_pdf=pdf_file, output_markdown=output_md)

        md_files = [(f, "") for f in sorted(md_path.glob("*.md"))]

    if not md_files:
        raise ValueError(f"No markdown files found under {md_path}")

    records = []
    for f, folder_name in md_files:
        page = parse_markdown(f)
        # Folder name is the authoritative subject source; frontmatter is the fallback.
        subject = _subject_label(folder_name) if folder_name else page.get("subject", "")
        page["subject"] = subject
        cleaned_text = clean_source(page["raw_text"])
        kg = build_kg(cleaned_text, embedder=embedder)
        records.append({
            **page,
            "question": cleaned_text,
            "info": json.dumps({"topic": page["topic"], "subject": subject, "kg": kg}),
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
