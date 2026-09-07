"""
agent/tools/fee_explainer.py

Fee Explainer Tool
==================
Takes the fee_confusion dict identified by the Thematic Engine and uses the
Groq LLM to generate a structured, customer-facing fee explanation with:
  - ≤6 bullet points in neutral, facts-only tone
  - 2 official source links
  - "Last checked" date

Public API
----------
  generate_fee_explainer(fee_confusion)  -> str
  fee_explainer_tool                     @tool (LangChain wrapper)
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "fee_explainer_prompt.txt"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_prompt_template() -> str:
    """Load the fee explainer prompt template from disk."""
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(f"Fee explainer prompt not found at: {_PROMPT_PATH}")
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _extract_json(raw: str) -> dict:
    """Extract and parse a JSON object from the LLM response."""
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
    cleaned = re.sub(r"```\s*$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM response:\n{raw[:500]}")


def _build_llm():
    """Instantiate a ChatGroq LLM."""
    from langchain_groq import ChatGroq
    from config.settings import GROQ_API_KEY, GROQ_MODEL
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Core logic
# ─────────────────────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_llm_for_explanation(fee_name: str, user_pain: str) -> dict:
    """Call the LLM to generate the fee explanation. Retries on failure."""
    llm = _build_llm()
    prompt_template = _load_prompt_template()

    prompt = prompt_template.replace("{fee_name}", fee_name)
    prompt = prompt.replace("{user_pain}", user_pain)

    logger.info("Calling Groq for fee explanation of '%s'...", fee_name)
    response = llm.invoke(prompt)
    raw = response.content if hasattr(response, "content") else str(response)

    result = _extract_json(raw)
    return result


def _validate_explanation(result: dict) -> dict:
    """Validate and enforce constraints on the fee explanation output."""
    fee_name = str(result.get("fee_name", "Unknown Fee"))

    bullets = result.get("bullets", [])
    if not isinstance(bullets, list):
        bullets = []
    # Ensure exactly 6 bullets
    bullets = [str(b) for b in bullets[:6]]
    while len(bullets) < 6:
        bullets.append("Please contact Groww support for more details about this fee.")

    source_links = result.get("source_links", [])
    if not isinstance(source_links, list):
        source_links = []
    source_links = [str(s) for s in source_links[:2]]
    while len(source_links) < 2:
        source_links.append("https://groww.in/help")

    return {
        "fee_name": fee_name,
        "bullets": bullets,
        "source_links": source_links,
    }


def _format_explanation(validated: dict) -> str:
    """Format the validated explanation into a human-readable string."""
    today = datetime.now(tz=timezone.utc).strftime("%B %d, %Y")

    lines = []
    lines.append(f"FEE EXPLAINER — {validated['fee_name']}")
    lines.append("─" * 40)
    for bullet in validated["bullets"]:
        lines.append(f"• {bullet}")
    lines.append("")
    lines.append("Sources:")
    for i, link in enumerate(validated["source_links"], 1):
        lines.append(f"  {i}. {link}")
    lines.append(f"\nLast checked: {today}")

    return "\n".join(lines)


def generate_fee_explainer(fee_confusion: dict) -> str:
    """
    Generate a structured fee explanation from the identified confusion.

    Args:
        fee_confusion: Dict with keys fee_name, user_pain, related_theme
                       (from the thematic engine's cluster output).

    Returns:
        A formatted string with ≤6 bullet points, 2 source links,
        and a "Last checked" date.
    """
    if not fee_confusion:
        return "No fee confusion was identified in the reviews."

    fee_name = str(fee_confusion.get("fee_name", "Unknown Fee"))
    user_pain = str(fee_confusion.get("user_pain", ""))

    logger.info("Generating fee explainer for: %s", fee_name)

    raw_result = _call_llm_for_explanation(fee_name, user_pain)
    validated = _validate_explanation(raw_result)
    formatted = _format_explanation(validated)

    logger.info("Fee explainer generated successfully (%d chars).", len(formatted))
    return formatted


# ─────────────────────────────────────────────────────────────────────────────
# LangChain Tool wrapper
# ─────────────────────────────────────────────────────────────────────────────

@tool
def fee_explainer_tool(fee_confusion: dict) -> str:
    """
    Generate a clear, customer-facing explanation for a fee/charge that
    users are confused about, based on insights from review clustering.

    Use this tool after clustering reviews (Step 2) if a fee_confusion was
    identified. It produces a structured explanation with ≤6 bullet points,
    2 official source links, and a "Last checked" date.

    Args:
        fee_confusion: Dict with keys:
          - fee_name (str): name of the fee/charge
          - user_pain (str): description of user confusion
          - related_theme (str): which cluster theme this belongs to

    Returns:
        A formatted string containing the fee explanation ready for
        inclusion in the Google Doc and email draft.
    """
    return generate_fee_explainer(fee_confusion)
