"""
agent/agent.py

Phase 5 — LangChain Orchestrator
==================================
Wires all seven tools (ingest, cluster, pulse, fee explainer, approval gate,
docs, gmail) into a single LangChain ReAct agent that executes the full
weekly-pulse pipeline end-to-end from a single trigger.

Public API
----------
  build_agent()    -> AgentExecutor
  run_pipeline()   -> dict          <- main entry point
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq

# ── Tool imports ──────────────────────────────────────────────────────────────
from agent.tools.ingest_reviews import ingest_reviews_tool
from agent.tools.thematic_engine import cluster_and_summarize_tool
from agent.tools.pulse_builder import build_pulse_tool
from agent.tools.fee_explainer import fee_explainer_tool
from agent.tools.approval_gate import approval_gate_tool
from agent.tools.remote_mcp_tools import google_docs_append_tool, gmail_create_draft_tool

logger = logging.getLogger(__name__)

# ── System prompt ─────────────────────────────────────────────────────────────
# Deterministic step-by-step instructions. The agent must follow these in order
# and not improvise extra steps. This is deliberate — the pipeline is sequential
# with known dependencies, so autonomous planning adds no value.

SYSTEM_PROMPT = """\
You are the Weekly Pulse Agent for the Groww investing app.
Your job is to execute the following pipeline IN STRICT ORDER.
Do NOT skip steps. Do NOT invent extra steps. Follow the sequence exactly.

STEP 1 — INGEST REVIEWS
  Call the `ingest_reviews_tool` tool with weeks={weeks}.
  This fetches Groww Play Store reviews from the last {weeks} weeks.
  Store the returned list of reviews for the next step.
  If the list is empty, stop and report "No reviews found in the last {weeks} weeks."

STEP 2 — CLUSTER & SUMMARIZE
  Call the `cluster_and_summarize_tool` tool with the full list of reviews
  from Step 1.
  This returns a dict with keys: themes, quotes, action_ideas, fee_confusion.
  Store this result for the next steps.

STEP 3 — BUILD PULSE
  Call the `build_pulse_tool` tool with:
    - themes: the themes list from Step 2
    - quotes: the quotes list from Step 2
    - action_ideas: the action_ideas list from Step 2
    - date_range: "{date_range}"
  This returns a formatted pulse note string. Store it for the next steps.

STEP 4 — FEE EXPLAINER
  If fee_confusion from Step 2 is NOT null:
    Call the `fee_explainer_tool` tool with:
      - fee_confusion: the fee_confusion dict from Step 2
    Store the returned fee explanation string.
  If fee_confusion is null:
    Skip this step. Set fee_explanation to "No fee confusion was identified in the reviews."

STEP 5 — APPROVAL GATE
  Combine the pulse note from Step 3 and the fee explanation from Step 4
  into a single preview string (pulse first, then fee explanation separated by a blank line).
  Call the `approval_gate_tool` tool with:
    - preview: the combined preview string
  If the result is "rejected", stop and report "Pipeline halted: user rejected MCP actions."
  If the result is "approved", continue to Step 6.

STEP 6 — APPEND TO GOOGLE DOC
  Call the `google_docs_append_tool` tool with:
    - content: the combined pulse note + fee explanation from Steps 3 and 4
  The content is appended to the configured rolling Google Doc.

STEP 7 — CREATE GMAIL DRAFT
  Call the `gmail_create_draft_tool` tool with:
    - subject: "Weekly Play Store Review Pulse + Customer Clarification — {date_range}"
    - body: the combined pulse note + fee explanation from Steps 3 and 4
    - doc_url: "https://docs.google.com/document/d/{google_doc_id}/edit"
  Report the draft confirmation message.

After completing all 7 steps, provide a final summary listing:
  - Number of reviews ingested
  - Number of themes identified
  - Fee issue identified (or "None")
  - The Google Doc URL
  - The Gmail draft status
"""


# ─────────────────────────────────────────────────────────────────────────────
# LLM factory
# ─────────────────────────────────────────────────────────────────────────────

def build_llm() -> ChatGroq:
    """Instantiate a ChatGroq LLM from project settings."""
    from config.settings import GROQ_API_KEY, GROQ_MODEL
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Agent factory
# ─────────────────────────────────────────────────────────────────────────────

ALL_TOOLS = [
    ingest_reviews_tool,
    cluster_and_summarize_tool,
    build_pulse_tool,
    fee_explainer_tool,
    approval_gate_tool,
    google_docs_append_tool,
    gmail_create_draft_tool,
]


def _compute_date_range(weeks: int) -> str:
    """Compute a human-readable date range string for the pulse header."""
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(weeks=weeks)
    return f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"


def build_agent():
    """
    Construct the ReAct agent with all seven pipeline tools using LangGraph.

    Returns a compiled LangGraph application.
    """
    from config.settings import WEEKS_LOOKBACK, RECIPIENT_EMAIL, GOOGLE_DOC_ID

    llm = build_llm()
    date_range = _compute_date_range(WEEKS_LOOKBACK)

    # Fill in the static variables in the system prompt
    clean_prompt = SYSTEM_PROMPT.format(
        weeks=WEEKS_LOOKBACK,
        date_range=date_range,
        google_doc_id=GOOGLE_DOC_ID,
    )

    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=clean_prompt
    )

    logger.info(
        "Agent built with %d tools: %s",
        len(ALL_TOOLS),
        [t.name for t in ALL_TOOLS],
    )
    return agent


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline runner
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline() -> dict:
    """
    Build and invoke the agent to run the full weekly-pulse pipeline.

    Returns the agent's final output dict including:
      - output: the agent's final answer string
      - intermediate_steps: list of (AgentAction, observation) tuples
    """
    from config.settings import WEEKS_LOOKBACK

    logger.info("=" * 60)
    logger.info("  WEEKLY PLAY STORE REVIEW PULSE — PIPELINE START")
    logger.info("=" * 60)

    executor = build_agent()

    trigger = (
        f"Run the complete weekly pulse pipeline for the Groww app. "
        f"Fetch the last {WEEKS_LOOKBACK} weeks of reviews, cluster them, "
        f"build the pulse note, generate a fee explainer if needed, "
        f"request approval, then create a Google Doc and draft a Gmail."
    )

    logger.info("Triggering agent with: %s", trigger)

    result = executor.invoke({"messages": [("user", trigger)]})

    logger.info("=" * 60)
    logger.info("  PIPELINE COMPLETE")
    logger.info("=" * 60)
    final_output = result["messages"][-1].content
    logger.info("Final output:\n%s", final_output)

    return {"output": final_output}
