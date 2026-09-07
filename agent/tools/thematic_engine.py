"""
agent/tools/thematic_engine.py

Phase 2 — Thematic Engine (Clustering & Summarization)
=======================================================
Uses Groq (ChatGroq) via LangChain to:
  1. Cluster reviews into ≤5 themes ranked by volume
  2. Select 3 verbatim quotes (one per top theme)
  3. Generate 3 actionable improvement ideas

Handles large review sets by batching into chunks that fit within
Groq's context window and merging the per-batch results.

Public API
----------
  build_llm()                            -> ChatGroq
  cluster_and_summarize(reviews)         -> dict
  cluster_and_summarize_tool             @tool (LangChain wrapper)
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "cluster_prompt.txt"

# ── Batching config ───────────────────────────────────────────────────────────
# llama3-70b-8192 has an 8192-token context window on Groq's free tier.
# We stay well under by limiting each batch to ~150 reviews (~4000 tokens).
MAX_REVIEWS_PER_BATCH = 150

# ── Output constraints ────────────────────────────────────────────────────────
MAX_THEMES = 5
NUM_QUOTES = 3
NUM_ACTIONS = 3


# ─────────────────────────────────────────────────────────────────────────────
# LLM factory
# ─────────────────────────────────────────────────────────────────────────────

def build_llm() -> ChatGroq:
    """
    Instantiate a ChatGroq LLM.
    Reads GROQ_API_KEY and GROQ_MODEL from config/settings.py.
    """
    from config.settings import GROQ_API_KEY, GROQ_MODEL
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Prompt helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_prompt_template() -> str:
    """Load the cluster prompt template from disk."""
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(f"Cluster prompt not found at: {_PROMPT_PATH}")
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _format_reviews_for_prompt(reviews: list[dict]) -> str:
    """
    Serialise the review list into a compact numbered text block.
    Format: [n] ★rating | date | text
    """
    lines = []
    for i, r in enumerate(reviews, 1):
        text = r.get("text", "").strip()
        rating = r.get("rating", "?")
        date = r.get("date", "")
        lines.append(f"[{i}] ★{rating} | {date} | {text}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# JSON parsing & validation
# ─────────────────────────────────────────────────────────────────────────────

def _extract_json(raw: str) -> dict:
    """
    Extract and parse a JSON object from the LLM response.
    Handles:
    - Responses that are pure JSON
    - Responses wrapped in markdown code fences (```json ... ```)
    - Leading/trailing whitespace or explanation text
    """
    # Strip markdown fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
    cleaned = re.sub(r"```\s*$", "", cleaned).strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to extract the first {...} block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM response:\n{raw[:500]}")


def _validate_output(result: dict, reviews: list[dict]) -> dict:
    """
    Validate and enforce all hard constraints on the LLM output.

    - Themes: max MAX_THEMES, each has name/summary/count
    - Quotes: exactly NUM_QUOTES, each must be a verbatim substring of some review
    - Action ideas: exactly NUM_ACTIONS
    - Fee confusion: optional dict with fee_name, user_pain, related_theme (or None)

    Returns the validated (and possibly trimmed) result dict.
    """
    # ── Themes ────────────────────────────────────────────────────────────────
    themes = result.get("themes", [])
    if not isinstance(themes, list):
        raise ValueError(f"'themes' must be a list, got {type(themes)}")
    if len(themes) > MAX_THEMES:
        logger.warning("LLM returned %d themes — truncating to %d.", len(themes), MAX_THEMES)
        themes = themes[:MAX_THEMES]
    if not themes:
        raise ValueError("LLM returned 0 themes — cannot produce a pulse.")
    # Ensure each theme has required keys with fallbacks
    validated_themes = []
    for t in themes:
        validated_themes.append({
            "name":    str(t.get("name", "Unknown")),
            "summary": str(t.get("summary", "")),
            "count":   int(t.get("count", 0)),
        })
    result["themes"] = validated_themes

    # ── Quotes ────────────────────────────────────────────────────────────────
    all_texts = [r.get("text", "") for r in reviews]
    quotes = result.get("quotes", [])
    if not isinstance(quotes, list):
        quotes = []

    verified_quotes: list[str] = []
    for q in quotes:
        q = str(q).strip()
        # Check verbatim: the quote must appear as a substring of at least one review
        is_verbatim = any(q in text for text in all_texts)
        if is_verbatim:
            verified_quotes.append(q)
        else:
            logger.warning(
                "Non-verbatim quote rejected: '%.80s...'", q
            )

    if len(verified_quotes) < NUM_QUOTES:
        logger.warning(
            "Only %d/%d verbatim quotes verified. Filling remainder from longest reviews.",
            len(verified_quotes), NUM_QUOTES
        )
        # Fallback: use sentences from the longest 1-star and low-star reviews
        fallback_pool = sorted(
            [r for r in reviews if r.get("rating", 5) <= 3],
            key=lambda r: len(r.get("text", "")),
            reverse=True,
        )
        for r in fallback_pool:
            text = r.get("text", "").strip()
            if text and text not in verified_quotes:
                verified_quotes.append(text[:200])  # cap at 200 chars
            if len(verified_quotes) >= NUM_QUOTES:
                break

    result["quotes"] = verified_quotes[:NUM_QUOTES]

    # ── Action ideas ──────────────────────────────────────────────────────────
    actions = result.get("action_ideas", [])
    if not isinstance(actions, list):
        actions = []
    if len(actions) < NUM_ACTIONS:
        logger.warning(
            "Only %d/%d action ideas returned — padding with placeholders.",
            len(actions), NUM_ACTIONS
        )
        while len(actions) < NUM_ACTIONS:
            actions.append("Investigate the identified theme and address top user pain points.")
    result["action_ideas"] = [str(a) for a in actions[:NUM_ACTIONS]]

    # ── Fee confusion (optional) ──────────────────────────────────────────────
    fee_confusion = result.get("fee_confusion", None)
    if fee_confusion is not None and isinstance(fee_confusion, dict):
        result["fee_confusion"] = {
            "fee_name":      str(fee_confusion.get("fee_name", "Unknown fee")),
            "user_pain":     str(fee_confusion.get("user_pain", "")),
            "related_theme": str(fee_confusion.get("related_theme", "")),
        }
        logger.info(
            "Fee confusion detected: '%s' (theme: '%s')",
            result["fee_confusion"]["fee_name"],
            result["fee_confusion"]["related_theme"],
        )
    else:
        result["fee_confusion"] = None
        logger.info("No fee/charge confusion detected in reviews.")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Single-batch clustering
# ─────────────────────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _cluster_batch(reviews: list[dict], llm: ChatGroq, prompt_template: str) -> dict:
    """
    Run clustering on a single batch of reviews.
    Retries up to 3 times on LLM / JSON parse errors.
    """
    review_text = _format_reviews_for_prompt(reviews)
    prompt = prompt_template.replace("{reviews}", review_text)

    logger.info("Calling Groq for batch of %d reviews...", len(reviews))
    response = llm.invoke(prompt)
    raw = response.content if hasattr(response, "content") else str(response)

    result = _extract_json(raw)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Multi-batch merge
# ─────────────────────────────────────────────────────────────────────────────

def _merge_batch_results(batch_results: list[dict], all_reviews: list[dict]) -> dict:
    """
    Merge multiple batch clustering results into one final result.

    Strategy:
    - Aggregate theme counts: same theme name → sum counts
    - Collect all verified quotes across batches
    - Collect all action ideas across batches
    - Re-rank themes by count, trim to MAX_THEMES
    - Select best NUM_QUOTES quotes and NUM_ACTIONS actions
    """
    theme_map: dict[str, dict] = {}
    all_quotes: list[str] = []
    all_actions: list[str] = []
    fee_confusion = None  # Keep the first non-null fee_confusion across batches

    for batch in batch_results:
        for theme in batch.get("themes", []):
            name = str(theme.get("name", "")).strip().lower()
            if name in theme_map:
                theme_map[name]["count"] += int(theme.get("count", 0))
            else:
                theme_map[name] = {
                    "name":    theme.get("name", name),
                    "summary": theme.get("summary", ""),
                    "count":   int(theme.get("count", 0)),
                }
        all_quotes.extend(batch.get("quotes", []))
        all_actions.extend(batch.get("action_ideas", []))
        # Preserve the first fee_confusion found across batches
        if fee_confusion is None and batch.get("fee_confusion") is not None:
            fee_confusion = batch["fee_confusion"]

    # Re-rank themes
    merged_themes = sorted(theme_map.values(), key=lambda t: t["count"], reverse=True)[:MAX_THEMES]

    # Deduplicate quotes, keep first NUM_QUOTES
    seen_quotes: set[str] = set()
    deduped_quotes: list[str] = []
    for q in all_quotes:
        q = q.strip()
        if q and q not in seen_quotes:
            seen_quotes.add(q)
            deduped_quotes.append(q)
        if len(deduped_quotes) >= NUM_QUOTES:
            break

    # Deduplicate actions, keep first NUM_ACTIONS
    seen_actions: set[str] = set()
    deduped_actions: list[str] = []
    for a in all_actions:
        a = a.strip()
        if a and a not in seen_actions:
            seen_actions.add(a)
            deduped_actions.append(a)
        if len(deduped_actions) >= NUM_ACTIONS:
            break

    merged = {
        "themes":       merged_themes,
        "quotes":       deduped_quotes[:NUM_QUOTES],
        "action_ideas": deduped_actions[:NUM_ACTIONS],
        "fee_confusion": fee_confusion,
    }
    return _validate_output(merged, all_reviews)


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def cluster_and_summarize(reviews: list[dict]) -> dict:
    """
    Cluster a list of Groww Play Store reviews into themes using Groq.

    Handles large review sets by batching (MAX_REVIEWS_PER_BATCH per call).
    If only one batch is needed, returns that batch's result directly.

    Args:
        reviews: List of clean review dicts from the ingestor
                 (keys: rating, title, text, date).

    Returns:
        {
          "themes":       [{"name", "summary", "count"}, ...],   # ≤5, ranked
          "quotes":       [str, str, str],                        # 3 verbatim
          "action_ideas": [str, str, str],                        # 3 actionable
          "fee_confusion": {"fee_name", "user_pain", "related_theme"} | None
        }

    Raises:
        ValueError: If reviews is empty or LLM output cannot be parsed.
        RuntimeError: If all retries fail.
    """
    if not reviews:
        logger.warning("cluster_and_summarize called with 0 reviews.")
        return {"themes": [], "quotes": [], "action_ideas": [], "fee_confusion": None}

    llm = build_llm()
    prompt_template = _load_prompt_template()

    # ── Batch the reviews ─────────────────────────────────────────────────────
    batches = [
        reviews[i: i + MAX_REVIEWS_PER_BATCH]
        for i in range(0, len(reviews), MAX_REVIEWS_PER_BATCH)
    ]
    logger.info(
        "Clustering %d reviews in %d batch(es) of up to %d.",
        len(reviews), len(batches), MAX_REVIEWS_PER_BATCH
    )

    batch_results: list[dict] = []
    for idx, batch in enumerate(batches, 1):
        logger.info("Processing batch %d/%d (%d reviews)...", idx, len(batches), len(batch))
        raw_result = _cluster_batch(batch, llm, prompt_template)
        # Validate per-batch before merging
        validated = _validate_output(raw_result, batch)
        batch_results.append(validated)

    # ── Merge if multi-batch, or return single result ─────────────────────────
    if len(batch_results) == 1:
        final = batch_results[0]
    else:
        logger.info("Merging %d batch results...", len(batch_results))
        final = _merge_batch_results(batch_results, reviews)

    fee_status = final.get("fee_confusion", {}).get("fee_name", "none") if final.get("fee_confusion") else "none"
    logger.info(
        "Clustering complete: %d themes, %d quotes, %d action ideas, fee_confusion=%s.",
        len(final["themes"]), len(final["quotes"]), len(final["action_ideas"]), fee_status
    )
    return final


# ─────────────────────────────────────────────────────────────────────────────
# LangChain Tool wrapper
# ─────────────────────────────────────────────────────────────────────────────

@tool
def cluster_and_summarize_tool(reviews: list[dict]) -> dict:
    """
    Cluster Groww Play Store reviews into themes using the Groq LLM.

    Use this tool after ingesting reviews. It groups them into ≤5 meaningful
    themes, selects 3 verbatim user quotes, generates 3 actionable
    improvement ideas, and identifies any fee/charge-related confusion.

    Args:
        reviews: List of review dicts (from ingest_reviews_tool).
                 Each dict has: rating (int), title (str), text (str), date (str).

    Returns:
        Dict with keys:
          themes        — list of {"name", "summary", "count"} (≤5, ranked)
          quotes        — list of 3 verbatim review text excerpts
          action_ideas  — list of 3 concrete improvement suggestions
          fee_confusion — dict with {"fee_name", "user_pain", "related_theme"} or null
    """
    return cluster_and_summarize(reviews)
