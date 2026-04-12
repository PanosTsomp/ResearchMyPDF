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

def _build_prompt(sections: PaperSections) -> str:
    """
    Build the prompt we send to the LLM.
    We include all key sections so the AI has full context.
    """
    parts = []

    if sections.abstract:
        parts.append(f"ABSTRACT:\n{sections.abstract}")
    if sections.introduction:
        parts.append(f"INTRODUCTION:\n{sections.introduction}")
    if sections.methodology:
        parts.append(f"METHODOLOGY:\n{sections.methodology}")
    if sections.results:
        parts.append(f"RESULTS:\n{sections.results}")
    if sections.conclusion:
        parts.append(f"CONCLUSION:\n{sections.conclusion}")

    context = "\n\n".join(parts)

    return (
        "You are a research assistant. Your job is to extract key information "
        "from a research paper accurately and completely, without leaving anything out.\n\n"
        "Based on the following sections from a research paper, extract the information "
        "and return it as valid JSON only. No preamble, no explanation, just JSON.\n\n"
        "Return this exact structure:\n"
        "{\n"
        '  "problem": "What specific problem or question does this paper address?",\n'
        '  "methodology": "What methods, models, or approaches were used?",\n'
        '  "key_findings": "What were the main results or conclusions?",\n'
        '  "limitations": "What limitations or future work did the authors mention?",\n'
        '  "confidence": "high, medium, or low based on how complete the provided text is"\n'
        "}\n\n"
        f"Paper title: {sections.title}\n\n"
        f"{context}"
    )


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------

def _parse_response(content: str) -> dict:
    """
    Try to parse the LLM response as JSON.
    Falls back to regex extraction if the model adds extra text around the JSON.
    """
    # Direct parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to extract just the {...} blob
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Give up — return empty structure so pipeline doesn't crash
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
    """
    Generate a structured summary of a paper's sections using the given LLM provider.
    """
    prompt = _build_prompt(sections)
    raw_response = provider.summarize(prompt)
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

    sections = extract_sections("papers/GradCam.pdf")
    provider = OllamaProvider()
    summary = summarize(sections, provider)

    print(f"Title:        {summary.title}\n")
    print(f"Problem:      {summary.problem}\n")
    print(f"Methodology:  {summary.methodology}\n")
    print(f"Key Findings: {summary.key_findings}\n")
    print(f"Limitations:  {summary.limitations}\n")
    print(f"Confidence:   {summary.confidence}\n")