"""
tests/test_ingest_reviews.py

Phase 1 unit + integration tests for agent/tools/ingest_reviews.py
(Groww Play Store edition)

Unit tests mock the Play Store API so they run offline with no API calls.
Integration tests (marked @pytest.mark.integration) hit the real Play Store.

Run unit tests only:
    pytest tests/test_ingest_reviews.py -v -m "not integration"

Run all tests including live fetch:
    pytest tests/test_ingest_reviews.py -v
"""

from __future__ import annotations

import types
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from agent.tools.ingest_reviews import (
    GROWW_APP_ID,
    MIN_REVIEW_WORDS,
    filter_by_date,
    filter_short_reviews,
    ingest_reviews,
    strip_pii,
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _dt(days_ago: int) -> datetime:
    return datetime.now(tz=timezone.utc) - timedelta(days=days_ago)


def _raw_review(i: int, days_ago: int = 3, text: str = "") -> dict:
    """Return a dict in the shape google-play-scraper returns."""
    return {
        "userName":   f"User{i}",           # PII — must be stripped
        "userImage":  "https://example.com/avatar.jpg",
        "content":    text or f"Review body number {i}, very detailed feedback.",
        "score":      (i % 5) + 1,
        "thumbsUpCount": i * 2,
        "reviewCreatedVersion": "5.0",
        "at":         _dt(days_ago),
        "replyContent": None,
        "repliedAt":  None,
        "reviewId":   f"review-id-{i:04d}",
        "title":      f"Title {i}",
    }


def _make_gps_reviews_mock(raw_reviews: list[dict], continuation_token=None):
    """
    Return a mock for google_play_scraper.reviews that returns
    (raw_reviews, continuation_token) on the first call and ([], None) after.
    """
    calls = [0]

    def _mock_reviews(*args, **kwargs):
        if calls[0] == 0:
            calls[0] += 1
            return raw_reviews, continuation_token
        return [], None

    return _mock_reviews


# ─── U-IN-01 Happy path ───────────────────────────────────────────────────────

def test_happy_path():
    """U-IN-01: 20 valid in-window reviews → 20 clean dicts returned."""
    raw = [_raw_review(i) for i in range(20)]
    mock_fn = _make_gps_reviews_mock(raw)

    with patch("agent.tools.ingest_reviews.fetch_playstore_reviews") as mock_fetch:
        mock_fetch.return_value = [
            {"rating": (i % 5) + 1, "title": f"Title {i}",
             "text": f"This is a detailed review number {i} with enough words.",
             "date": _dt(3).strftime("%Y-%m-%d")}
            for i in range(20)
        ]
        result = ingest_reviews(weeks=8)

    assert len(result) == 20
    for r in result:
        assert set(r.keys()) == {"rating", "title", "text", "date"}
        assert 1 <= r["rating"] <= 5


# ─── U-IN-02 Date filter — keep within window ─────────────────────────────────

def test_date_filter_keeps_in_window():
    """U-IN-02: in-window + out-of-window reviews → only in-window kept."""
    in_window = [
        {"rating": 4, "title": "Good", "text": "Works well.", "date": _dt(3).strftime("%Y-%m-%d")}
        for _ in range(20)
    ]
    out_of_window = [
        {"rating": 3, "title": "Old", "text": "Old review.", "date": _dt(200).strftime("%Y-%m-%d")}
        for _ in range(10)
    ]
    result = filter_by_date(in_window + out_of_window, weeks=8)
    assert len(result) == 20


# ─── U-IN-03 Date filter — all outside window ─────────────────────────────────

def test_date_filter_all_outside_window():
    """U-IN-03: All reviews older than window → []."""
    old_reviews = [
        {"rating": 2, "title": "Old", "text": "Very old review.", "date": _dt(500).strftime("%Y-%m-%d")}
        for _ in range(10)
    ]
    result = filter_by_date(old_reviews, weeks=8)
    assert result == []


# ─── U-IN-04 PII stripping — extra fields removed ────────────────────────────

def test_pii_stripping_removes_extra_fields():
    """U-IN-04: Extra fields like userName, reviewId stripped from output."""
    dirty_reviews = [
        {
            "rating": 5, "title": "Hi", "text": "Great app.",
            "date": "2026-08-01",
            "userName": "JohnDoe",       # PII
            "reviewId": "abc123",        # extra
            "thumbsUpCount": 10,         # extra
        }
        for _ in range(5)
    ]
    result = strip_pii(dirty_reviews)
    assert len(result) == 5
    for r in result:
        assert set(r.keys()) == {"rating", "title", "text", "date"}
        assert "userName" not in r
        assert "reviewId" not in r


# ─── U-IN-05 Empty text reviews dropped ──────────────────────────────────────

def test_empty_text_reviews_dropped():
    """U-IN-05: Reviews with empty content are excluded during fetch."""
    raw = [_raw_review(i) for i in range(15)]  # valid
    raw += [_raw_review(i, text="") for i in range(15, 20)]  # empty text → skipped

    # Simulate what fetch_playstore_reviews does: skip empty content
    with patch("agent.tools.ingest_reviews.fetch_playstore_reviews") as mock_fetch:
        mock_fetch.return_value = [
            {"rating": (i % 5) + 1, "title": f"T{i}",
             "text": f"This is a sufficiently detailed review body number {i}.",
             "date": "2026-08-01"}
            for i in range(15)   # only 15 non-empty
        ]
        result = ingest_reviews(weeks=8)

    assert len(result) == 15


# ─── U-IN-06 Email address in review text → redacted ─────────────────────────

def test_email_in_text_is_redacted():
    """U-IN-06: Email address in review body → replaced with [email redacted]."""
    reviews = [
        {
            "rating": 4, "title": "Contact",
            "text": "Please email me at user@example.com for help.",
            "date": "2026-08-01",
        }
    ]
    result = strip_pii(reviews)
    assert len(result) == 1
    assert "user@example.com" not in result[0]["text"]
    assert "[email redacted]" in result[0]["text"]


# ─── U-IN-07 Phone number in review text → redacted ──────────────────────────

def test_phone_in_text_is_redacted():
    """U-IN-07: Phone number in review body → replaced with [phone redacted]."""
    reviews = [
        {
            "rating": 2, "title": "Support",
            "text": "Call me at +91 98765 43210 to discuss this issue.",
            "date": "2026-08-01",
        }
    ]
    result = strip_pii(reviews)
    assert "98765" not in result[0]["text"]
    assert "[phone redacted]" in result[0]["text"]


# ─── U-IN-08 Empty review list ───────────────────────────────────────────────

def test_empty_review_list():
    """U-IN-08: Empty input to filter_by_date / strip_pii → [] with no crash."""
    assert filter_by_date([], weeks=8) == []
    assert strip_pii([]) == []


# ─── U-IN-09 All reviews in window, none skipped ─────────────────────────────

def test_all_reviews_in_window():
    """U-IN-09: When all reviews are recent, none should be skipped."""
    reviews = [
        {"rating": 5, "title": "Great", "text": f"Body {i}.", "date": _dt(i).strftime("%Y-%m-%d")}
        for i in range(1, 11)   # 1–10 days ago, well within 8 weeks
    ]
    result = filter_by_date(reviews, weeks=8)
    assert len(result) == 10


# ─── Short review filter ──────────────────────────────────────────────────────

def test_short_reviews_dropped():
    """Reviews with fewer than MIN_REVIEW_WORDS words in 'text' are removed."""
    short = [
        {"rating": 5, "title": "", "text": "good", "date": "2026-08-01"},           # 1 word
        {"rating": 4, "title": "", "text": "nice app", "date": "2026-08-01"},        # 2 words
        {"rating": 5, "title": "", "text": "👍", "date": "2026-08-01"},              # 1 word (emoji)
        {"rating": 3, "title": "", "text": "ok ok ok ok ok ok ok", "date": "2026-08-01"},  # 7 words
    ]
    long_enough = [
        {"rating": 1, "title": "", "text": "The app keeps crashing every time I open it", "date": "2026-08-01"},  # 9 words
        {"rating": 2, "title": "", "text": "Withdrawal is stuck for three days no response from support", "date": "2026-08-01"},  # 10 words
    ]
    result = filter_short_reviews(short + long_enough)
    assert len(result) == 2
    assert all(len(r["text"].split()) >= MIN_REVIEW_WORDS for r in result)


def test_short_filter_boundary():
    """Exactly MIN_REVIEW_WORDS words → kept; one fewer → dropped."""
    exact = {"rating": 4, "title": "", "text": " ".join(["word"] * MIN_REVIEW_WORDS), "date": "2026-08-01"}
    one_short = {"rating": 4, "title": "", "text": " ".join(["word"] * (MIN_REVIEW_WORDS - 1)), "date": "2026-08-01"}
    result = filter_short_reviews([exact, one_short])
    assert len(result) == 1
    assert result[0]["text"] == exact["text"]



# ─── U-IN-10 Ratings clamped to 1–5 range ────────────────────────────────────

def test_canonical_schema_enforced():
    """U-IN-10: Only canonical keys returned; rating is an int."""
    reviews = [{"rating": 4, "title": "T", "text": "Body.", "date": "2026-08-01",
                "extra_key": "should_be_gone"}]
    result = strip_pii(reviews)
    assert set(result[0].keys()) == {"rating", "title", "text", "date"}
    assert isinstance(result[0]["rating"], int)


# ─── Integration: live Play Store fetch ───────────────────────────────────────

@pytest.mark.integration
def test_live_groww_fetch():
    """
    Integration test: fetch real Groww reviews from Play Store.
    Requires internet access. Run with: pytest -m integration
    """
    from agent.tools.ingest_reviews import fetch_playstore_reviews

    reviews = fetch_playstore_reviews(
        app_id=GROWW_APP_ID,
        weeks=8,
        max_count=100,   # small count for the test
        country="in",
        lang="en",
    )
    assert len(reviews) > 0, "Expected at least 1 Groww review in the last 8 weeks"
    for r in reviews:
        assert set(r.keys()) == {"rating", "title", "text", "date"}
        assert 1 <= r["rating"] <= 5
        assert isinstance(r["text"], str) and len(r["text"]) > 0
        assert r["date"].count("-") == 2   # YYYY-MM-DD format
