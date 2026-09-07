"""
tests/test_mcp_integration.py

Integration smoke test for Phase 4 MCP setup.
Calls the LangChain tools (which in turn call the local Python MCP servers).

By default, the MCP servers are designed to require a valid credentials.json
downloaded from Google Cloud. If the environment variable MCP_MOCK_GOOGLE=true
is set, the MCP servers will return mock URLs/IDs to pass the test locally
without requiring an actual Google Cloud setup.

Run with:
MCP_MOCK_GOOGLE=true pytest tests/test_mcp_integration.py -v
"""

from agent.tools.docs_tool import google_docs_create
from agent.tools.gmail_tool import gmail_create_draft

def test_google_docs_mcp_tool():
    """Test that the google_docs_create tool connects to the MCP server and returns a URL."""
    url = google_docs_create.invoke({
        "title": "Smoke Test Doc",
        "content": "This is a smoke test."
    })
    
    assert url.startswith("https://docs.google.com/document/d/")
    print(f"Doc created at: {url}")


def test_gmail_mcp_tool():
    """Test that the gmail_create_draft tool connects to the MCP server and returns a success message."""
    response = gmail_create_draft.invoke({
        "subject": "Smoke Test Subject",
        "body": "Smoke Test Body",
        "doc_url": "https://docs.google.com/document/d/mock-doc-id/edit",
        "recipient": "test@example.com"
    })
    
    assert "Successfully created Gmail draft" in response
    assert "ID:" in response
    print(response)
