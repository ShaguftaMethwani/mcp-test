"""
tests/test_fee_explainer.py

Unit tests for the Fee Explainer tool.
Tests JSON parsing, validation, and formatting logic with mocked LLM.

Run with:
    python -m pytest tests/test_fee_explainer.py -v
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from agent.tools.fee_explainer import (
    _extract_json,
    _validate_explanation,
    _format_explanation,
    generate_fee_explainer,
)


# ── Sample data ──────────────────────────────────────────────────────────────

SAMPLE_FEE_CONFUSION = {
    "fee_name": "Exit Load",
    "user_pain": "Users are surprised by exit load charges when redeeming mutual funds within 1 year.",
    "related_theme": "Pricing Confusion",
}

VALID_LLM_RESPONSE = json.dumps({
    "fee_name": "Exit Load",
    "bullets": [
        "Exit load is a fee charged when you redeem mutual fund units before a specified period.",
        "It typically applies if you redeem units within 1 year of purchase.",
        "The standard exit load is 1% of the redemption amount for most equity mutual funds.",
        "Exit load exists to discourage short-term trading and protect long-term investors.",
        "You can avoid exit load by holding your investment for at least 1 year.",
        "Check the 'Fund Details' section in the Groww app for the exit load policy of each fund.",
    ],
    "source_links": [
        "https://groww.in/p/exit-load-in-mutual-funds",
        "https://www.sebi.gov.in/legal/circulars",
    ],
})


# ── JSON parsing ─────────────────────────────────────────────────────────────

def test_extract_json_valid():
    """Valid JSON is parsed correctly."""
    result = _extract_json(VALID_LLM_RESPONSE)
    assert result["fee_name"] == "Exit Load"
    assert len(result["bullets"]) == 6


def test_extract_json_with_markdown_fences():
    """JSON wrapped in markdown code fences is parsed correctly."""
    wrapped = f"```json\n{VALID_LLM_RESPONSE}\n```"
    result = _extract_json(wrapped)
    assert result["fee_name"] == "Exit Load"


def test_extract_json_invalid_raises():
    """Non-JSON input raises ValueError."""
    with pytest.raises(ValueError, match="Could not parse JSON"):
        _extract_json("This is not JSON at all")


# ── Validation ───────────────────────────────────────────────────────────────

def test_validate_explanation_valid():
    """A valid explanation passes validation unchanged."""
    raw = json.loads(VALID_LLM_RESPONSE)
    validated = _validate_explanation(raw)
    assert validated["fee_name"] == "Exit Load"
    assert len(validated["bullets"]) == 6
    assert len(validated["source_links"]) == 2


def test_validate_explanation_pads_bullets():
    """Missing bullets are padded to exactly 6."""
    raw = {"fee_name": "DP Charges", "bullets": ["Bullet 1", "Bullet 2"], "source_links": []}
    validated = _validate_explanation(raw)
    assert len(validated["bullets"]) == 6
    assert validated["bullets"][0] == "Bullet 1"


def test_validate_explanation_truncates_bullets():
    """Extra bullets beyond 6 are truncated."""
    raw = {
        "fee_name": "DP Charges",
        "bullets": [f"Bullet {i}" for i in range(10)],
        "source_links": ["https://groww.in"],
    }
    validated = _validate_explanation(raw)
    assert len(validated["bullets"]) == 6


def test_validate_explanation_pads_source_links():
    """Missing source links are padded to exactly 2."""
    raw = {"fee_name": "STT", "bullets": ["b"] * 6, "source_links": []}
    validated = _validate_explanation(raw)
    assert len(validated["source_links"]) == 2
    assert "groww.in" in validated["source_links"][0]


# ── Formatting ───────────────────────────────────────────────────────────────

def test_format_explanation_structure():
    """Formatted output contains all required sections."""
    raw = json.loads(VALID_LLM_RESPONSE)
    validated = _validate_explanation(raw)
    formatted = _format_explanation(validated)

    assert "FEE EXPLAINER — Exit Load" in formatted
    assert "•" in formatted
    assert "Sources:" in formatted
    assert "Last checked:" in formatted
    assert "groww.in" in formatted


# ── End-to-end (mocked LLM) ─────────────────────────────────────────────────

@patch("agent.tools.fee_explainer._build_llm")
def test_generate_fee_explainer_success(mock_build_llm):
    """Full pipeline with mocked LLM returns formatted explanation."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content=VALID_LLM_RESPONSE)
    mock_build_llm.return_value = mock_llm

    result = generate_fee_explainer(SAMPLE_FEE_CONFUSION)

    assert "FEE EXPLAINER — Exit Load" in result
    assert "Last checked:" in result
    mock_llm.invoke.assert_called_once()


def test_generate_fee_explainer_no_confusion():
    """No fee_confusion returns a descriptive message."""
    result = generate_fee_explainer(None)
    assert "No fee confusion" in result


def test_generate_fee_explainer_empty_dict():
    """Empty fee_confusion dict returns a descriptive message."""
    result = generate_fee_explainer({})
    assert "No fee confusion" in result
