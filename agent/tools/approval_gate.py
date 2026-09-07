"""
agent/tools/approval_gate.py

Approval Gate Tool
==================
Implements a human-in-the-loop approval step before MCP actions
(Google Docs append and Gmail draft creation) are executed.

Behaviour:
  - Interactive (TTY): Displays a preview and prompts for y/n approval.
  - Non-interactive (CI/GitHub Actions): Auto-approves with a log message.

Public API
----------
  request_approval(preview)  -> str   ("approved" | "rejected")
  approval_gate_tool         @tool (LangChain wrapper)
"""

from __future__ import annotations

import logging
import sys

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def _is_interactive() -> bool:
    """Check if stdin is connected to a terminal (interactive mode)."""
    try:
        return sys.stdin.isatty()
    except AttributeError:
        return False


def request_approval(preview: str) -> str:
    """
    Display a preview of the content about to be sent via MCP tools
    and ask for user approval.

    In non-interactive mode (CI/GitHub Actions), auto-approves.

    Args:
        preview: A text preview of the content to be sent to Google Docs
                 and Gmail.

    Returns:
        "approved" if the user approves, "rejected" otherwise.
    """
    if not _is_interactive():
        logger.info("Non-interactive mode detected — auto-approving MCP actions.")
        return "approved"

    # Interactive mode: show preview and prompt
    print()
    print("=" * 60)
    print("  🔒 APPROVAL REQUIRED — Review before MCP actions")
    print("=" * 60)
    print()
    print("The following content will be:")
    print("  1. Appended to the Google Doc")
    print("  2. Included in a Gmail draft")
    print()
    print("─" * 60)
    # Show a truncated preview to keep the terminal readable
    preview_lines = preview.split("\n")
    if len(preview_lines) > 30:
        for line in preview_lines[:30]:
            print(f"  {line}")
        print(f"  ... ({len(preview_lines) - 30} more lines)")
    else:
        for line in preview_lines:
            print(f"  {line}")
    print("─" * 60)
    print()

    try:
        response = input("Approve and proceed? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n⚠️  Approval cancelled.")
        logger.info("Approval cancelled by user (EOF/interrupt).")
        return "rejected"

    if response in ("y", "yes"):
        logger.info("User approved MCP actions.")
        return "approved"
    else:
        logger.info("User rejected MCP actions.")
        return "rejected"


# ─────────────────────────────────────────────────────────────────────────────
# LangChain Tool wrapper
# ─────────────────────────────────────────────────────────────────────────────

@tool
def approval_gate_tool(preview: str) -> str:
    """
    Request user approval before executing MCP actions (Google Docs and Gmail).

    This tool displays a preview of the content that will be sent to
    Google Docs and Gmail, and asks for explicit user approval.
    In non-interactive environments (CI/GitHub Actions), it auto-approves.

    IMPORTANT: Call this tool BEFORE any Google Docs or Gmail tool calls.
    If the result is "rejected", do NOT proceed with MCP actions.

    Args:
        preview: The full text content (pulse + fee explainer) that will be
                 sent to Google Docs and included in the Gmail draft.

    Returns:
        "approved" if the user approves, "rejected" if not.
    """
    return request_approval(preview)
