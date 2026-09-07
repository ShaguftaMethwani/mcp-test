"""
agent/tools/pulse_builder.py

Phase 3 — Pulse Builder (Note Assembly)
=======================================
Takes the structured output (JSON dict) from the Thematic Engine and formats
it into a concise (<= 250 words) one-page weekly note.

The output is a Markdown-like text string ready to be written to a Google Doc
or inserted into a Gmail draft.

Public API
----------
  build_pulse(themes, quotes, action_ideas, date_range) -> str
  build_pulse_tool                                      @tool
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

def _count_words(text: str) -> int:
    return len(text.split())

def _truncate_text(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def build_pulse(
    themes: list[dict[str, Any]],
    quotes: list[str],
    action_ideas: list[str],
    date_range: str,
) -> str:
    """
    Format the thematic engine output into a single string note.
    Highlights exactly 3 themes, 3 quotes, and 3 actions.
    Enforces a strict 250-word limit by truncating summaries if necessary.
    """
    from config.settings import MAX_PULSE_WORDS, PULSE_THEMES, NUM_QUOTES, NUM_ACTIONS

    # 1. Enforce constraints
    top_themes = themes[:PULSE_THEMES]
    top_quotes = quotes[:NUM_QUOTES]
    top_actions = action_ideas[:NUM_ACTIONS]

    # 2. Build the string iteratively to manage word count
    header = (
        f"Weekly Play Store Review Pulse — {date_range}\n"
        f"──────────────────────────────────────\n"
    )

    # Calculate remaining budget
    budget = MAX_PULSE_WORDS - _count_words(header)

    # Action Ideas (we keep these intact as much as possible)
    actions_block = "ACTION IDEAS\n"
    for i, act in enumerate(top_actions, 1):
        actions_block += f"{i}. {act}\n"
    actions_block = actions_block.strip()
    budget -= _count_words(actions_block)

    # Quotes (we keep these intact as much as possible, since they are verbatim)
    quotes_block = "USER QUOTES\n"
    for q in top_quotes:
        quotes_block += f"• \"{q}\"\n"
    quotes_block = quotes_block.strip()
    budget -= _count_words(quotes_block)

    # Themes (these can be truncated if we are running low on budget)
    themes_block = "TOP THEMES\n"
    
    # Divide remaining budget among the theme summaries
    budget_per_theme = max(5, budget // max(1, len(top_themes)))

    for i, t in enumerate(top_themes, 1):
        name = str(t.get("name", "Unknown"))
        summary = str(t.get("summary", ""))
        
        # Format the prefix: "1. [Theme]: "
        prefix = f"{i}. {name}: "
        prefix_words = _count_words(prefix)
        
        # Remaining budget for this specific summary
        summary_budget = max(3, budget_per_theme - prefix_words)
        
        truncated_summary = _truncate_text(summary, summary_budget)
        themes_block += f"{prefix}{truncated_summary}\n"

    themes_block = themes_block.strip()

    # 3. Assemble final pulse
    pulse = f"{header}{themes_block}\n\n{quotes_block}\n\n{actions_block}"

    final_words = _count_words(pulse)
    if final_words > MAX_PULSE_WORDS:
        logger.warning(
            "Pulse exceeded word limit: %d > %d words.",
            final_words, MAX_PULSE_WORDS
        )
    else:
        logger.info("Pulse built successfully (%d words).", final_words)

    return pulse


@tool
def build_pulse_tool(
    themes: list[dict[str, Any]],
    quotes: list[str],
    action_ideas: list[str],
    date_range: str,
) -> str:
    """
    Assemble structured thematic data into a formatted weekly note.

    Use this tool after extracting themes from reviews. It takes the structured
    themes, quotes, and action ideas and generates a clean, readable one-page
    pulse note (<= 250 words) that can be sent to Google Docs and Gmail.

    Args:
        themes: List of dicts (name, summary, count).
        quotes: List of exactly 3 string quotes.
        action_ideas: List of exactly 3 string actionable ideas.
        date_range: String representing the date window, e.g. "Jul 5 - Aug 29, 2026".

    Returns:
        A formatted string note.
    """
    return build_pulse(themes, quotes, action_ideas, date_range)
