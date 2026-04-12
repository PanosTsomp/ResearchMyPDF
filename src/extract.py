#Find the sections of intrest specifically. Extract the important context

import json
import re
from dataclasses import dataclass, field

import ollama
import pymupdf


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PaperSections:
    title: str = ""
    abstract: str = ""
    introduction: str = ""
    methodology: str = ""
    results: str = ""
    conclusion: str = ""
    raw_sections: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Fuzzy keyword mapping
# Each key is a PaperSections field name.
# If ANY of its keywords appear in a section heading, that heading maps to the field.
# ---------------------------------------------------------------------------

SECTION_KEYWORDS: dict[str, list[str]] = {
    "abstract": [
        "abstract", "summary", "synopsis", "précis", "highlights", "in brief",
    ],
    "introduction": [
        "introduction", "background", "overview", "motivation",
    ],
    "methodology": [
        "methodology", "methods", "method", "approach", "proposed method",
        "our method", "technique", "framework", "system", "architecture",
        "experimental setup",
    ],
    "results": [
        "results", "experiments", "evaluation", "experimental results",
        "experiments and results", "results and discussion", "findings",
        "performance", "analysis",
    ],
    "conclusion": [
        "conclusion", "conclusions", "concluding remarks", "summary and conclusion",
        "final remarks", "closing remarks", "future work", "discussion",
    ],
}

# Flat list used for initial header scoring before AI enrichment
_BASE_KEYWORDS: list[str] = [kw for kws in SECTION_KEYWORDS.values() for kw in kws]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _body_size(doc: pymupdf.Document) -> float:
    """Return the most common font size in the document — the body text baseline."""
    counts: dict[float, int] = {}
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    size = round(span["size"], 1)
                    counts[size] = counts.get(size, 0) + 1
    return max(counts, key=counts.get) if counts else 10.0


def _get_title(doc: pymupdf.Document) -> str:
    """Return the title — the largest font text on the first page."""
    page = doc[0]
    largest = 0.0
    parts: list[str] = []

    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                size = round(span["size"], 1)
                text = span["text"].strip()
                if not text:
                    continue
                if _is_metadata(text):
                    continue
                if size > largest:
                    largest = size
                    parts = [text]
                elif size == largest:
                    parts.append(text)

    return " ".join(parts)


def _score_span(text: str, size: float, is_bold: bool,
                body_size: float, keywords: list[str]) -> int:
    """
    Score how likely a span is to be a section header.

    Points:
        +2  bold
        +2  font size above body baseline
        +2  starts with a number (e.g. "3. Results")
        +3  contains a known section keyword
    """
    score = 0
    text_stripped = text.strip()
    text_lower = text_stripped.lower()

    if is_bold:
        score += 2
    if size > body_size:
        score += 2
    if re.match(r"^\d+[\.\s]", text_stripped):
        score += 2
    for kw in keywords:
        if kw in text_lower:
            score += 3
            break

    return score


def _build_lines(doc: pymupdf.Document) -> list[dict]:
    """
    Flatten the entire document into a list of line-level dicts.
    Each dict has: page, text, size, is_bold.
    Lines that are only whitespace are dropped.
    """
    lines = []
    for page_idx, page in enumerate(doc):
        for block in page.get_text("dict")["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                text = " ".join(s["text"] for s in line["spans"])
                text = " ".join(text.split())  # ← collapse spaces here
                text = " ".join(text.split())
                text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
                if not text:
                    continue
                first = line["spans"][0]
                lines.append({
                    "page": page_idx,
                    "text": text,
                    "size": round(first["size"], 1),
                    "is_bold": bool(first["flags"] & 16),
                    
                })
    return lines


def _find_headers(lines, body_size, keywords, threshold=4):
    return [
        i for i, line in enumerate(lines)
        if not _is_metadata(line["text"])
        and _score_span(line["text"], line["size"], line["is_bold"],
                       body_size, keywords) >= threshold
        and len(" ".join(line["text"].split())) < 80
        and len(" ".join(line["text"].split())) > 3
    ]


def _build_raw_sections(lines: list[dict],
                         header_indices: list[int]) -> dict[str, str]:
    """
    Given header positions, collect the text between each header and the next.
    Returns {header_text: body_text}.
    """
    sections: dict[str, str] = {}
    for i, idx in enumerate(header_indices):
        header_text = lines[idx]["text"]
        end = header_indices[i + 1] if i + 1 < len(header_indices) else len(lines)
        body = "\n".join(lines[j]["text"] for j in range(idx + 1, end))
        sections[header_text] = body
    return sections


def _map_to_field(heading: str) -> str | None:
    """
    Map a raw section heading to a PaperSections field name using fuzzy matching.
    Returns None if no match is found.
    """
    heading_lower = heading.lower().strip()
    for field_name, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in heading_lower:
                return field_name
    return None


# ---------------------------------------------------------------------------
# AI enrichment
# ---------------------------------------------------------------------------

def _ask_ollama_for_sections(text: str) -> list[str]:
    """
    Send abstract + introduction text to Ollama.
    Ask it to return JSON list of section names found or mentioned in the text.
    Falls back gracefully — never crashes the pipeline.
    """
    prompt = (
        "Given the following text from the start of a research paper, "
        "extract the names of all sections in the paper exactly as they appear or are mentioned.\n\n"
        "Return ONLY valid JSON in this exact format, nothing else:\n"
        '{"sections": ["Section Name 1", "Section Name 2", ...]}\n\n'
        f"Text:\n{text[:3000]}"
    )

    def _parse(content: str) -> list[str]:
        # Try direct parse first
        try:
            return json.loads(content).get("sections", [])
        except (json.JSONDecodeError, AttributeError):
            pass
        # Try extracting just the {...} blob
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group()).get("sections", [])
            except (json.JSONDecodeError, AttributeError):
                pass
        return []

    try:
        response = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
        )
        content = response["message"]["content"]
        result = _parse(content)
        if result:
            return result

        # One retry with a stricter prompt
        retry_prompt = (
            "Your previous response was not valid JSON.\n"
            "Return ONLY this JSON object, nothing else:\n"
            '{"sections": ["section name 1", "section name 2", ...]}\n\n'
            f"Text:\n{text[:2000]}"
        )
        retry = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": retry_prompt}],
        )
        return _parse(retry["message"]["content"])

    except Exception:
        # Ollama not running, model missing, network error — doesn't matter
        return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_sections(pdf_path: str) -> PaperSections:
    doc = pymupdf.open(pdf_path)
    body_size = _body_size(doc)
    title = _get_title(doc)
    lines = _build_lines(doc)

    # --- Pass 1: find headers using base keywords only ---
    header_indices = _find_headers(lines, body_size, _BASE_KEYWORDS)
    raw_sections = _build_raw_sections(lines, header_indices)

    # --- AI enrichment: send abstract + intro to Ollama ---
    early_text = ""
    for heading, content in raw_sections.items():
        if _map_to_field(heading) in ("abstract", "introduction"):
            early_text += f"{heading}\n{content}\n\n"

    ai_section_names = _ask_ollama_for_sections(early_text) if early_text else []

    # Merge AI-discovered section names into our keyword pool
    enriched_keywords = _BASE_KEYWORDS + [name.lower() for name in ai_section_names]

    # --- Pass 2: re-score with enriched keywords ---
    header_indices = _find_headers(lines, body_size, enriched_keywords)
    raw_sections = _build_raw_sections(lines, header_indices)

    # --- Map into PaperSections dataclass ---
    paper = PaperSections(title=title, raw_sections=raw_sections)

    for heading, content in raw_sections.items():
        field_name = _map_to_field(heading)
        # Only set a field once — first match wins
        if field_name and not getattr(paper, field_name):
            setattr(paper, field_name, content)

    return paper

# ---------------------------------------------------------------------------
# See If it has any metadata and ignore it
# ---------------------------------------------------------------------------
def _is_metadata(text: str) -> bool:
    t = text.lower()
    if "arxiv" in t: return True
    if re.search(r'\[.*?\]', t): return True
    if re.search(r'\bv\d+\b', t): return True
    if re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b', t): return True
    if re.search(r'\b10\.\d{4}/', t): return True
    if re.search(r'\bfig\.', t): return True
    if re.search(r'\btable\.', t): return True
    if re.search(r'\bet al\.', t): return True
    if re.search(r'^\d+\.\s+[A-Z][a-z]+-[A-Z]', t): return True
    if text.strip() in ("RESEARCH", "Open Access", "ORIGINAL"): return True
    digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
    if digit_ratio > 0.3: return True
    return False

# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
"""
if __name__ == "__main__":
    result = extract_sections("papers/s12903-022-02436-3.pdf")
    print(f"Title:        {result.title}\n")
    print(f"Abstract:     {result.abstract[:200]}\n")
    print(f"Introduction: {result.introduction[:200]}\n")
    print(f"Methodology:  {result.methodology[:200]}\n")
    print(f"Results:      {result.results[:200]}\n")
    print(f"Conclusion:   {result.conclusion[:200]}\n")
    print(f"All sections found: {list(result.raw_sections.keys())}")

"""