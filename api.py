"""
api.py — FastAPI backend for the PulseFlow AI dashboard.

Exposes the pipeline as REST endpoints that the React frontend calls.
Separates pipeline execution from MCP approval for human-in-the-loop gating.

Usage:
    uvicorn api:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Configure logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="PulseFlow AI API",
    description="Backend API for the Play Store Weekly Review Pulse dashboard",
    version="1.0.0",
)

# Allow CORS for the Vite dev server and Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory state ─────────────────────────────────────────────────────────
# Stores the latest pipeline results so the approve endpoint can use them.
_pipeline_state: dict[str, Any] = {
    "status": "idle",          # idle | running | completed | error
    "reviews": [],
    "cluster_result": None,
    "pulse_text": None,
    "fee_explainer_text": None,
    "mcp_status": "pending",   # pending | approved | rejected
    "mcp_results": None,
    "error": None,
    "started_at": None,
    "completed_at": None,
}


def _reset_state():
    """Reset pipeline state for a new run."""
    _pipeline_state.update({
        "status": "idle",
        "reviews": [],
        "cluster_result": None,
        "pulse_text": None,
        "fee_explainer_text": None,
        "mcp_status": "pending",
        "mcp_results": None,
        "error": None,
        "started_at": None,
        "completed_at": None,
    })


# ── API Models ───────────────────────────────────────────────────────────────

class PipelineResponse(BaseModel):
    status: str
    reviews_count: int = 0
    cluster_result: Optional[dict] = None
    pulse_text: Optional[str] = None
    fee_explainer_text: Optional[str] = None
    mcp_status: str = "pending"
    mcp_results: Optional[dict] = None
    error: Optional[str] = None
    elapsed_seconds: Optional[float] = None


class ApproveResponse(BaseModel):
    status: str
    docs_result: Optional[str] = None
    gmail_result: Optional[str] = None
    error: Optional[str] = None


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/status")
def get_status() -> dict:
    """Return the current pipeline state."""
    return {
        "status": _pipeline_state["status"],
        "reviews_count": len(_pipeline_state["reviews"]),
        "cluster_result": _pipeline_state["cluster_result"],
        "pulse_text": _pipeline_state["pulse_text"],
        "fee_explainer_text": _pipeline_state["fee_explainer_text"],
        "mcp_status": _pipeline_state["mcp_status"],
        "mcp_results": _pipeline_state["mcp_results"],
        "error": _pipeline_state["error"],
    }


@app.post("/api/run-pipeline", response_model=PipelineResponse)
def run_pipeline():
    """
    Run the pipeline steps 1-4 (ingest → cluster → pulse → fee explainer).
    Does NOT trigger MCP actions — those require explicit approval.
    """
    from config.settings import WEEKS_LOOKBACK, APP_ID, MAX_REVIEWS_PER_FETCH, REVIEW_COUNTRY, REVIEW_LANG
    from agent.tools.ingest_reviews import ingest_reviews
    from agent.tools.thematic_engine import cluster_and_summarize
    from agent.tools.pulse_builder import build_pulse
    from agent.tools.fee_explainer import generate_fee_explainer

    _reset_state()
    _pipeline_state["status"] = "running"
    _pipeline_state["started_at"] = time.time()

    try:
        # Step 1: Ingest reviews
        logger.info("API: Step 1 — Ingesting reviews...")
        reviews = ingest_reviews(
            weeks=WEEKS_LOOKBACK,
            app_id=APP_ID,
            max_count=MAX_REVIEWS_PER_FETCH,
            country=REVIEW_COUNTRY,
            lang=REVIEW_LANG,
        )
        _pipeline_state["reviews"] = reviews

        if not reviews:
            _pipeline_state["status"] = "completed"
            _pipeline_state["completed_at"] = time.time()
            return PipelineResponse(
                status="completed",
                reviews_count=0,
                error="No reviews found in the specified time window.",
            )

        # Step 2: Cluster & summarize
        logger.info("API: Step 2 — Clustering %d reviews...", len(reviews))
        cluster_result = cluster_and_summarize(reviews)
        _pipeline_state["cluster_result"] = cluster_result

        # Step 3: Build pulse
        logger.info("API: Step 3 — Building pulse note...")
        end_date = datetime.now(tz=timezone.utc)
        start_date = end_date - timedelta(weeks=WEEKS_LOOKBACK)
        date_range = f"{start_date.strftime('%b %d')} – {end_date.strftime('%b %d, %Y')}"

        pulse_text = build_pulse(
            themes=cluster_result["themes"],
            quotes=cluster_result["quotes"],
            action_ideas=cluster_result["action_ideas"],
            date_range=date_range,
        )
        _pipeline_state["pulse_text"] = pulse_text

        # Step 4: Fee explainer
        logger.info("API: Step 4 — Generating fee explainer...")
        fee_confusion = cluster_result.get("fee_confusion")
        fee_explainer_text = generate_fee_explainer(fee_confusion)
        _pipeline_state["fee_explainer_text"] = fee_explainer_text

        _pipeline_state["status"] = "completed"
        _pipeline_state["completed_at"] = time.time()
        elapsed = _pipeline_state["completed_at"] - _pipeline_state["started_at"]

        logger.info("API: Pipeline completed in %.1fs", elapsed)

        return PipelineResponse(
            status="completed",
            reviews_count=len(reviews),
            cluster_result=cluster_result,
            pulse_text=pulse_text,
            fee_explainer_text=fee_explainer_text,
            mcp_status="pending",
            elapsed_seconds=round(elapsed, 1),
        )

    except Exception as exc:
        elapsed = time.time() - (_pipeline_state["started_at"] or time.time())
        _pipeline_state["status"] = "error"
        _pipeline_state["error"] = str(exc)
        logger.error("API: Pipeline failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/approve", response_model=ApproveResponse)
def approve_mcp_actions():
    """
    Approve and execute MCP actions (Google Docs append + Gmail draft).
    Only works after a successful pipeline run.
    """
    if _pipeline_state["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Pipeline is not in 'completed' state (current: {_pipeline_state['status']}). Run the pipeline first.",
        )

    if _pipeline_state["mcp_status"] == "approved":
        raise HTTPException(
            status_code=400,
            detail="MCP actions have already been approved and executed.",
        )

    from config.settings import GOOGLE_DOC_ID, WEEKS_LOOKBACK
    from agent.tools.remote_mcp_tools import (
        google_docs_append_tool,
        gmail_create_draft_tool,
    )

    pulse_text = _pipeline_state["pulse_text"] or ""
    fee_text = _pipeline_state["fee_explainer_text"] or ""
    combined_content = f"{pulse_text}\n\n{fee_text}"

    end_date = datetime.now(tz=timezone.utc)
    start_date = end_date - timedelta(weeks=WEEKS_LOOKBACK)
    date_range = f"{start_date.strftime('%b %d')} – {end_date.strftime('%b %d, %Y')}"

    try:
        # Step 5: Append to Google Doc
        logger.info("API: Step 5 — Appending to Google Doc...")
        docs_result = google_docs_append_tool.invoke({"content": combined_content})

        # Step 6: Create Gmail draft
        logger.info("API: Step 6 — Creating Gmail draft...")
        gmail_result = gmail_create_draft_tool.invoke({
            "subject": f"Weekly Play Store Review Pulse + Customer Clarification — {date_range}",
            "body": combined_content,
            "doc_url": f"https://docs.google.com/document/d/{GOOGLE_DOC_ID}/edit",
        })

        _pipeline_state["mcp_status"] = "approved"
        _pipeline_state["mcp_results"] = {
            "docs": docs_result,
            "gmail": gmail_result,
        }

        logger.info("API: MCP actions completed successfully.")

        return ApproveResponse(
            status="approved",
            docs_result=docs_result,
            gmail_result=gmail_result,
        )

    except Exception as exc:
        _pipeline_state["mcp_status"] = "error"
        logger.error("API: MCP actions failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/reject")
def reject_mcp_actions():
    """Reject MCP actions — pipeline results are preserved but no actions are taken."""
    if _pipeline_state["status"] != "completed":
        raise HTTPException(status_code=400, detail="No completed pipeline to reject.")

    _pipeline_state["mcp_status"] = "rejected"
    logger.info("API: MCP actions rejected by user.")
    return {"status": "rejected", "message": "MCP actions have been rejected. Pipeline results are preserved."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
