"""
agent/tools/ingest_reviews.py

Phase 1 — Review Ingestor (Groww Play Store edition)
=====================================================
Fetches, normalises, date-filters, and PII-strips public Play Store reviews
for the Groww app (com.nextbillion.groww) so the downstream Thematic Engine
only ever sees clean, anonymous review dicts.

Data source
-----------
  google-play-scraper (pip package) — reads publicly available review pages,
  no Google account or login required.  Fully within Play Store ToS.

Public API
----------
  fetch_playstore_reviews(app_id, weeks, max_count, country, lang)
                           -> list[dict]   ← main fetch + filter
  filter_by_date(reviews, weeks)           -> list[dict]
  strip_pii(reviews)                       -> list[dict]
  ingest_reviews(weeks, app_id, ...)       -> list[dict]   ← full pipeline

LangChain tool
--------------
  ingest_reviews_tool  @tool — wraps ingest_reviews for agent use
"""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# ── Canonical output columns (all other keys are dropped) ────────────────────
CANONICAL_COLUMNS = {"rating", "title", "text", "date"}

# ── Minimum useful review length (words) ─────────────────────────────────────
MIN_REVIEW_WORDS = 8

# ── Groww app defaults ────────────────────────────────────────────────────────
GROWW_APP_ID = "com.nextbillion.groww"
DEFAULT_COUNTRY = "in"
DEFAULT_LANG = "en"

# ── PII patterns to redact from review text ───────────────────────────────────
_PII_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
     "[email redacted]"),
    # Indian mobile: +91 followed by 10 digits (various spacing/punctuation)
    (re.compile(r"\+?91[\s.\-]?[6-9]\d{9}\b"),
     "[phone redacted]"),
    # Indian mobile: standalone 10-digit number starting with 6-9
    (re.compile(r"\b[6-9]\d{4}[\s.\-]?\d{5}\b"),
     "[phone redacted]"),
    # General international phone numbers
    (re.compile(r"\b(?:\+?\d{1,3}[\s.\-]?)?\(?\d{3,5}\)?[\s.\-]?\d{3,5}[\s.\-]?\d{4}\b"),
     "[phone redacted]"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Fetch from Play Store
# ─────────────────────────────────────────────────────────────────────────────

def fetch_playstore_reviews(
    app_id: str = GROWW_APP_ID,
    weeks: int = 8,
    max_count: int = 2000,
    country: str = DEFAULT_COUNTRY,
    lang: str = DEFAULT_LANG,
) -> list[dict[str, Any]]:
    """
    Fetch public Play Store reviews for `app_id` published within the last
    `weeks` calendar weeks.

    Uses google-play-scraper (no auth/login required).  Reviews are fetched
    in batches (continuation token) until we have either `max_count` reviews
    or we hit reviews older than the cutoff date.

    Returns a list of normalised dicts with the canonical schema:
      {rating: int, title: str, text: str, date: str (ISO date)}
    """
    # Lazy import so the rest of the module works even without the package in
    # test environments that mock this function.
    try:
        from google_play_scraper import Sort, reviews as gps_reviews
    except ImportError as exc:
        raise ImportError(
            "google-play-scraper is required for Play Store fetching.\n"
            "Install it with: pip install google-play-scraper"
        ) from exc

    cutoff = datetime.now(tz=timezone.utc) - timedelta(weeks=weeks)
    logger.info(
        "Fetching Play Store reviews for '%s' (last %d weeks, cutoff=%s).",
        app_id, weeks, cutoff.date()
    )

    all_reviews: list[dict[str, Any]] = []
    continuation_token = None
    batch_size = 200          # max per API call
    total_fetched = 0
    hit_cutoff = False

    while total_fetched < max_count and not hit_cutoff:
        try:
            result, continuation_token = gps_reviews(
                app_id,
                lang=lang,
                country=country,
                sort=Sort.NEWEST,
                count=min(batch_size, max_count - total_fetched),
                continuation_token=continuation_token,
            )
        except Exception as exc:
            logger.error("Play Store fetch error: %s", exc)
            raise RuntimeError(
                f"Failed to fetch reviews for '{app_id}': {exc}"
            ) from exc

        if not result:
            logger.info("No more reviews returned by Play Store API.")
            break

        for raw in result:
            review_date = raw.get("at")
            # 'at' is a datetime object from google-play-scraper
            if isinstance(review_date, datetime):
                if review_date.tzinfo is None:
                    review_date = review_date.replace(tzinfo=timezone.utc)
            else:
                # Fallback: try to parse as string
                try:
                    review_date = datetime.fromisoformat(str(review_date))
                    if review_date.tzinfo is None:
                        review_date = review_date.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    logger.debug("Skipping review with unparseable date: %s", raw.get("at"))
                    continue

            # Stop fetching once we pass the cutoff (reviews are NEWEST first)
            if review_date < cutoff:
                hit_cutoff = True
                break

            text = (raw.get("content") or "").strip()
            if not text:
                continue  # skip empty body reviews

            all_reviews.append({
                "rating": int(raw.get("score", 3)),
                "title":  (raw.get("title") or "").strip(),
                "text":   text,
                "date":   review_date.strftime("%Y-%m-%d"),
            })

        total_fetched += len(result)
        logger.info(
            "Batch done: %d fetched this batch, %d kept in window so far.",
            len(result), len(all_reviews)
        )

        if continuation_token is None:
            logger.info("No continuation token — reached end of reviews.")
            break

        # Be polite: small delay between batches
        time.sleep(0.3)

    logger.info(
        "Fetch complete: %d reviews within the last %d weeks for '%s'.",
        len(all_reviews), weeks, app_id
    )
    return all_reviews


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Date filter (secondary guard, reviews already pre-filtered above)
# ─────────────────────────────────────────────────────────────────────────────

def filter_by_date(reviews: list[dict], weeks: int) -> list[dict]:
    """
    Secondary date filter — keeps only reviews whose 'date' field falls
    within the last `weeks` calendar weeks.

    The fetch step already applies the cutoff, but this guard handles any edge
    cases (e.g. timezone shifts) and makes the function independently testable.
    """
    if not reviews:
        return []

    cutoff = datetime.now(tz=timezone.utc) - timedelta(weeks=weeks)
    kept: list[dict] = []
    skipped = 0

    for review in reviews:
        raw_date = review.get("date", "")
        try:
            parsed = datetime.strptime(raw_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if parsed >= cutoff:
                kept.append(review)
            else:
                skipped += 1
        except ValueError:
            logger.warning("Could not parse date '%s' — skipping row.", raw_date)
            skipped += 1

    logger.info(
        "Date filter (last %d weeks): kept %d, skipped %d reviews.",
        weeks, len(kept), skipped,
    )
    return kept


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — PII stripping
# ─────────────────────────────────────────────────────────────────────────────

def strip_pii(reviews: list[dict]) -> list[dict]:
    """
    1. Enforce the canonical column whitelist (drops usernames, device IDs,
       reviewer location, etc. that google-play-scraper may include).
    2. Redact email addresses and phone numbers from 'text' and 'title' fields.
    """
    cleaned: list[dict] = []
    for review in reviews:
        # Enforce column whitelist — drop userName, reviewId, thumbsUp, etc.
        clean: dict = {k: review[k] for k in CANONICAL_COLUMNS if k in review}

        # Redact PII from text fields
        for field in ("text", "title"):
            value = str(clean.get(field, ""))
            for pattern, replacement in _PII_PATTERNS:
                value = pattern.sub(replacement, value)
            clean[field] = value

        cleaned.append(clean)
    return cleaned


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — Minimum-length filter
# ─────────────────────────────────────────────────────────────────────────────

def filter_short_reviews(reviews: list[dict], min_words: int = MIN_REVIEW_WORDS) -> list[dict]:
    """
    Drop reviews whose 'text' field contains fewer than `min_words` words.
    Short reviews like "good", "nice app", "👍" carry no actionable signal
    for the Thematic Engine.
    """
    kept: list[dict] = []
    skipped = 0
    for review in reviews:
        word_count = len(str(review.get("text", "")).split())
        if word_count >= min_words:
            kept.append(review)
        else:
            skipped += 1
    if skipped:
        logger.info(
            "Short-review filter (min %d words): dropped %d, kept %d reviews.",
            min_words, skipped, len(kept)
        )
    return kept


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator — full pipeline
# ─────────────────────────────────────────────────────────────────────────────

def ingest_reviews(
    weeks: int = 8,
    app_id: str = GROWW_APP_ID,
    max_count: int = 2000,
    country: str = DEFAULT_COUNTRY,
    lang: str = DEFAULT_LANG,
) -> list[dict]:
    """
    Full Groww review ingest pipeline:
      1. fetch_playstore_reviews — pull from Play Store API (no auth needed)
      2. filter_by_date          — secondary date-window guard
      3. strip_pii               — drop non-canonical fields; redact PII in text
      4. filter_short_reviews    — drop reviews with < MIN_REVIEW_WORDS words

    Returns a list of dicts with exactly: rating, title, text, date.
    Returns [] if no reviews fall within the date window.
    """
    reviews = fetch_playstore_reviews(
        app_id=app_id,
        weeks=weeks,
        max_count=max_count,
        country=country,
        lang=lang,
    )
    reviews = filter_by_date(reviews, weeks)
    reviews = strip_pii(reviews)
    reviews = filter_short_reviews(reviews)
    logger.info("ingest_reviews: final output = %d reviews.", len(reviews))
    return reviews


# ─────────────────────────────────────────────────────────────────────────────
# LangChain Tool wrapper
# ─────────────────────────────────────────────────────────────────────────────

@tool
def ingest_reviews_tool(weeks: int = 8) -> list[dict]:
    """
    Fetch and pre-process Groww Play Store reviews.

    Use this tool to fetch the most recent Play Store reviews for the Groww
    app, filter them to the last `weeks` weeks, remove PII, and return a clean
    list ready for thematic clustering.

    Args:
        weeks: Number of weeks of reviews to fetch (default: 8).

    Returns:
        A list of dicts, each with keys: rating (int 1-5), title (str),
        text (str), date (str ISO-8601 YYYY-MM-DD).
        Returns an empty list if no reviews found in the window.
    """
    from config.settings import APP_ID, MAX_REVIEWS_PER_FETCH, REVIEW_COUNTRY, REVIEW_LANG
    return ingest_reviews(
        weeks=weeks,
        app_id=APP_ID,
        max_count=MAX_REVIEWS_PER_FETCH,
        country=REVIEW_COUNTRY,
        lang=REVIEW_LANG,
    )
