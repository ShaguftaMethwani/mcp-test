"""
tests/test_thematic_engine.py

Phase 2 unit + integration tests for agent/tools/thematic_engine.py

Unit tests mock the LLM and test the JSON parsing and schema validation logic.
Integration tests hit the actual Groq API (requires GROQ_API_KEY).

Run unit tests only:
    pytest tests/test_thematic_engine.py -v -m "not integration"

Run all tests:
    pytest tests/test_thematic_engine.py -v
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from agent.tools.thematic_engine import (
    _extract_json,
    _validate_output,
    cluster_and_summarize,
)

# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_reviews(count: int, texts: list[str] = None) -> list[dict]:
    if texts is None:
        texts = [f"This is review number {i}." for i in range(count)]
    return [
        {"rating": (i % 5) + 1, "title": f"Title {i}", "text": texts[i], "date": "2026-08-01"}
        for i in range(len(texts))
    ]

# ─── 4.1 Unit Tests — Output Schema Validation ───────────────────────────────

def test_extract_json_valid():
    """U-TE-01: Valid JSON output parsed correctly."""
    raw = '''```json
{
  "themes": [{"name": "Bugs", "summary": "Fix them", "count": 10}],
  "quotes": ["This is review number 0."],
  "action_ideas": ["Fix bugs"]
}
```'''
    res = _extract_json(raw)
    assert len(res["themes"]) == 1
    assert res["themes"][0]["name"] == "Bugs"


def test_validate_truncates_themes():
    """U-TE-02: LLM returns 6 themes → truncated to 5."""
    reviews = _make_reviews(1)
    result = {
        "themes": [
            {"name": f"Theme {i}", "summary": "...", "count": i} for i in range(6)
        ],
        "quotes": [reviews[0]["text"]] * 3,
        "action_ideas": ["Action 1", "Action 2", "Action 3"],
    }
    validated = _validate_output(result, reviews)
    assert len(validated["themes"]) == 5


@patch("agent.tools.thematic_engine.ChatGroq")
def test_retry_on_malformed_json(MockChatGroq):
    """U-TE-03: Malformed JSON triggers retry."""
    # First call returns bad JSON, second call returns good JSON
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = [
        AIMessage(content="{ invalid json"),
        AIMessage(content='{"themes": [{"name": "Good", "summary": "...", "count": 1}], "quotes": ["Review 0."], "action_ideas": ["Action 1", "Action 2", "Action 3"]}'),
    ]
    MockChatGroq.return_value = mock_llm

    reviews = _make_reviews(1, ["Review 0."])
    # Use patch to speed up the wait time of tenacity for testing
    with patch("agent.tools.thematic_engine.wait_exponential", return_value=MagicMock(return_value=0)):
        result = cluster_and_summarize(reviews)
    
    assert len(result["themes"]) == 1
    assert mock_llm.invoke.call_count == 2


@patch("agent.tools.thematic_engine.ChatGroq")
def test_max_retries_exceeded(MockChatGroq):
    """U-TE-04: Malformed JSON continuously → raises RetryError."""
    from tenacity import RetryError
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="{ invalid json")
    MockChatGroq.return_value = mock_llm

    reviews = _make_reviews(1, ["Review 0."])
    with patch("agent.tools.thematic_engine.wait_exponential", return_value=MagicMock(return_value=0)):
        with pytest.raises(RetryError):
            cluster_and_summarize(reviews)


def test_fewer_quotes_accepted():
    """U-TE-05: LLM returns only 2 quotes → padded to 3 using review text."""
    reviews = _make_reviews(3, ["Bad app.", "Slow app.", "Crashes."])
    result = {
        "themes": [{"name": "Bugs", "summary": "...", "count": 3}],
        "quotes": ["Bad app.", "Slow app."], # missing one
        "action_ideas": ["A", "B", "C"],
    }
    validated = _validate_output(result, reviews)
    assert len(validated["quotes"]) == 3
    # Check that it filled the gap with another valid quote
    assert validated["quotes"][2] in ["Bad app.", "Slow app.", "Crashes."]


def test_empty_reviews_list():
    """U-TE-06: Empty reviews list passed in → Short circuit."""
    result = cluster_and_summarize([])
    assert result == {"themes": [], "quotes": [], "action_ideas": []}


def test_non_verbatim_quote_rejected():
    """Quotes not found in text are rejected, padded from real text."""
    reviews = _make_reviews(3, ["Review A.", "Review B.", "Review C fallback."])
    result = {
        "themes": [{"name": "Bugs", "summary": "...", "count": 2}],
        "quotes": ["Review A.", "Review Fake.", "Review B."], # 'Review Fake.' is fake
        "action_ideas": ["A", "B", "C"],
    }
    validated = _validate_output(result, reviews)
    assert len(validated["quotes"]) == 3
    assert "Review Fake." not in validated["quotes"]
    assert "Review C fallback." in validated["quotes"]


# ─── 4.2 Integration Tests — LLM Quality ──────────────────────────────────────

@pytest.mark.integration
def test_live_clustering():
    """I-TE-01 to 05: Run a real LLM call and verify output structure."""
    reviews = []
    # Plant 3 distinct topics
    reviews.extend(_make_reviews(10, ["App crashes on login."] * 10))
    reviews.extend(_make_reviews(5, ["KYC is very slow."] * 5))
    reviews.extend(_make_reviews(2, ["Add dark mode please."] * 2))

    result = cluster_and_summarize(reviews)
    
    themes = result.get("themes", [])
    quotes = result.get("quotes", [])
    actions = result.get("action_ideas", [])

    assert 1 <= len(themes) <= 5
    assert len(quotes) == 3
    assert len(actions) == 3

    # I-TE-05: Ranking by volume
    counts = [t["count"] for t in themes]
    assert counts == sorted(counts, reverse=True), "Themes must be ranked by volume descending"

    # I-TE-02: Verbatim quote check
    all_texts = [r["text"] for r in reviews]
    for q in quotes:
        assert any(q in t for t in all_texts), f"Quote not verbatim: {q}"
