#Takes the extracted sections and sends them to the LLM

# Takes a PaperSections object and returns a structured PaperSummary.
# Does not care which LLM provider is used — works with anything
# that implements the LLMProvider Protocol.

import json
import re
from dataclasses import dataclass

from extract import PaperSections
from providers.base import LLMProvider


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PaperSummary:
    title: str
    problem: str           # What problem does this paper solve?
    methodology: str       # How did they solve it?
    key_findings: str      # What did they find?
    limitations: str       # What limitations did they mention?
    confidence: str        # high / medium / low — how complete was the extraction?


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

MAX_SECTION = 1500

def _build_prompt(sections: PaperSections) -> str:
    parts = []

    if sections.abstract:
        parts.append(f"ABSTRACT:\n{sections.abstract[:MAX_SECTION]}")
    if sections.introduction:
        parts.append(f"INTRODUCTION:\n{sections.introduction[:MAX_SECTION]}")
    if sections.methodology:
        parts.append(f"METHODOLOGY:\n{sections.methodology[:MAX_SECTION]}")
    if sections.results:
        parts.append(f"RESULTS:\n{sections.results[:MAX_SECTION]}")
    if sections.conclusion:
        parts.append(f"CONCLUSION:\n{sections.conclusion[:MAX_SECTION]}")

    context = "\n\n".join(parts)

    return (
        "You are a research assistant extracting key information from a paper.\n\n"
        f"Paper title: {sections.title}\n\n"
        f"{context}\n\n"
        "---\n"
        "Based on the paper above, return ONLY this JSON object, nothing else. "
        "No markdown, no explanation, just the raw JSON:\n"
        "{\n"
        '  "problem": "what problem does this paper solve",\n'
        '  "methodology": "what methods or approaches were used",\n'
        '  "key_findings": "what were the main results",\n'
        '  "limitations": "what limitations were mentioned",\n'
        '  "confidence": "high, medium, or low"\n'
        "}"
    )


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------

def _parse_response(content: str) -> dict:
    # Direct parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to repair incomplete JSON by closing it
    repaired = content.strip()
    if not repaired.endswith("}"):
        repaired += "\n}"
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # Try to extract just the {...} blob
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Give up
    return {
        "problem": "",
        "methodology": "",
        "key_findings": "",
        "limitations": "",
        "confidence": "low",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def summarize(sections: PaperSections, provider: LLMProvider) -> PaperSummary:
    prompt = _build_prompt(sections)
    print(f"DEBUG prompt length: {len(prompt)} chars")
    raw_response = provider.summarize(prompt)
    print(f"DEBUG raw response:\n{raw_response[:2000]}")
    data = _parse_response(raw_response)

    return PaperSummary(
        title=sections.title,
        problem=data.get("problem", ""),
        methodology=data.get("methodology", ""),
        key_findings=data.get("key_findings", ""),
        limitations=data.get("limitations", ""),
        confidence=data.get("confidence", "low"),
    )


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from extract import extract_sections
    from providers.ollama_provider import OllamaProvider

    sections = extract_sections("papers/LatIA_2025_117.pdf")
    provider = OllamaProvider()
    summary = summarize(sections, provider)

    print(f"Title:        {summary.title}\n")
    print(f"Problem:      {summary.problem}\n")
    print(f"Methodology:  {summary.methodology}\n")
    print(f"Key Findings: {summary.key_findings}\n")
    print(f"Limitations:  {summary.limitations}\n")
    print(f"Confidence:   {summary.confidence}\n")