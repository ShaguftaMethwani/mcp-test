"""
tests/test_agent.py

Unit tests for Phase 5 — LangChain Orchestrator.
Validates agent wiring, tool registration, and prompt correctness.

Run with:
    MCP_MOCK_GOOGLE=true python -m pytest tests/test_agent.py -v
"""

import os
import pytest

# Ensure MCP mock mode for tests that import MCP tools
os.environ.setdefault("MCP_MOCK_GOOGLE", "true")

from agent.agent import ALL_TOOLS, SYSTEM_PROMPT, build_agent, _compute_date_range


# ─────────────────────────────────────────────────────────────────────────────
# Tool wiring tests
# ─────────────────────────────────────────────────────────────────────────────

EXPECTED_TOOL_NAMES = {
    "ingest_reviews_tool",
    "cluster_and_summarize_tool",
    "build_pulse_tool",
    "google_docs_append_tool",
    "gmail_create_draft_tool",
}


def test_all_tools_registered():
    """ALL_TOOLS must contain exactly the 5 expected tools."""
    actual_names = {t.name for t in ALL_TOOLS}
    assert actual_names == EXPECTED_TOOL_NAMES, (
        f"Expected tools {EXPECTED_TOOL_NAMES}, got {actual_names}"
    )


def test_all_tools_count():
    """There must be exactly 5 tools."""
    assert len(ALL_TOOLS) == 5


def test_tools_have_descriptions():
    """Every tool must have a non-empty description (required for ReAct agents)."""
    for t in ALL_TOOLS:
        assert t.description and len(t.description.strip()) > 0, (
            f"Tool '{t.name}' has no description"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Prompt tests
# ─────────────────────────────────────────────────────────────────────────────

def test_system_prompt_mentions_all_tools():
    """The system prompt must reference every tool name so the agent knows about them."""
    for name in EXPECTED_TOOL_NAMES:
        assert name in SYSTEM_PROMPT, (
            f"System prompt is missing reference to tool '{name}'"
        )


def test_system_prompt_has_all_steps():
    """The system prompt must contain all 5 pipeline steps."""
    for step in ["STEP 1", "STEP 2", "STEP 3", "STEP 4", "STEP 5"]:
        assert step in SYSTEM_PROMPT, f"System prompt is missing '{step}'"


# ─────────────────────────────────────────────────────────────────────────────
# Date range helper
# ─────────────────────────────────────────────────────────────────────────────

def test_compute_date_range_format():
    """_compute_date_range should return a string like 'Jul 13 – Sep 07, 2026'."""
    result = _compute_date_range(8)
    assert "–" in result, f"Expected '–' separator in date range, got: {result}"
    # Should contain a year
    assert "20" in result, f"Expected year in date range, got: {result}"


def test_compute_date_range_different_weeks():
    """Different week values should produce different start dates."""
    range_4 = _compute_date_range(4)
    range_12 = _compute_date_range(12)
    # The 12-week range should have an earlier start date
    assert range_4 != range_12


# ─────────────────────────────────────────────────────────────────────────────
# Agent build test
# ─────────────────────────────────────────────────────────────────────────────

def test_build_agent_returns_compiled_graph():
    """build_agent() should return a compiled LangGraph app."""
    agent = build_agent()
    assert agent is not None
    assert hasattr(agent, "invoke")
