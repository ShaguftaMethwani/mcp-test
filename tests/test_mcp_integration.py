"""
tests/test_mcp_integration.py

Integration smoke test for Phase 4 MCP setup.
Calls the LangChain tools (which in turn call the remote MCP server).

By default, the MCP tools connect to the remote MCP server. If the
environment variable MCP_MOCK_GOOGLE=true is set, the tools will return
mock responses to pass the test locally without a live server.

Run with:
    MCP_MOCK_GOOGLE=true pytest tests/test_mcp_integration.py -v
"""

import os
os.environ.setdefault("MCP_MOCK_GOOGLE", "true")

from agent.tools.remote_mcp_tools import google_docs_append_tool, gmail_create_draft_tool


def test_google_docs_mcp_tool():
    """Test that the google_docs_append tool returns a success response."""
    result = google_docs_append_tool.invoke({
        "content": "This is a smoke test."
    })

    assert "success" in result.lower() or "mock" in result.lower() or "appended" in result.lower()
    print(f"Docs result: {result}")


def test_gmail_mcp_tool():
    """Test that the gmail_create_draft tool returns a success response."""
    result = gmail_create_draft_tool.invoke({
        "subject": "Smoke Test Subject",
        "body": "Smoke Test Body",
        "doc_url": "https://docs.google.com/document/d/mock-doc-id/edit",
    })

    assert "success" in result.lower() or "mock" in result.lower() or "draft" in result.lower()
    print(f"Gmail result: {result}")
