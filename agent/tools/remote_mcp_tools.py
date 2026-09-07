"""
agent/tools/remote_mcp_tools.py

Phase 4 — MCP Integration (Remote)
===================================
Connects to the remote hosted MCP Google Server via Streamable HTTP,
and exposes `google_docs_append_tool` and `gmail_create_draft_tool` as LangChain tools.
"""

from __future__ import annotations

import asyncio
import os
from langchain_core.tools import tool
from mcp.client.streamable_http import streamable_http_client
from mcp.client.session import ClientSession

# When MCP_MOCK_GOOGLE is set, we bypass network calls entirely for fast unit tests.
_IS_MOCK = os.environ.get("MCP_MOCK_GOOGLE") == "true"


async def _call_remote_mcp(tool_name: str, arguments: dict) -> str:
    """Helper to connect to the remote MCP server and call a tool."""
    from config.settings import REMOTE_MCP_URL
    
    try:
        async with streamable_http_client(url=REMOTE_MCP_URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Call the tool exposed by the remote MCP server
                result = await session.call_tool(
                    tool_name,
                    arguments=arguments
                )
                
                if result.content and len(result.content) > 0:
                    # The node SDK typically returns text content in an array
                    if hasattr(result.content[0], "text"):
                        return result.content[0].text
                    # Fallback if structure differs slightly
                    return str(result.content[0])
                return "No text returned."
    except Exception as e:
        return f"Error connecting to MCP server at {REMOTE_MCP_URL}: {str(e)}"


async def _async_google_docs_append(content: str) -> str:
    if _IS_MOCK:
        return '{"success": true, "document_id": "mock-doc-id", "message": "Content appended successfully."}'
    
    from config.settings import GOOGLE_DOC_ID
    return await _call_remote_mcp(
        "google_docs_append",
        arguments={
            "document_id": GOOGLE_DOC_ID,
            "content": f"\n\n{content}", # prepend some newlines for separation
            "add_newline": True
        }
    )


async def _async_gmail_create_draft(subject: str, body: str, doc_url: str) -> str:
    if _IS_MOCK:
        return '{"success": true, "draft_id": "mock-draft-id", "message": "Draft created successfully."}'
    
    from config.settings import RECIPIENT_EMAIL
    
    full_body = f"{body}\n\nView the full rolling document here:\n{doc_url}"
    
    return await _call_remote_mcp(
        "gmail_create_draft",
        arguments={
            "to": [RECIPIENT_EMAIL],
            "subject": subject,
            "body": full_body,
            "body_type": "plain"
        }
    )


@tool
def google_docs_append_tool(content: str) -> str:
    """
    Appends the provided content to the end of the configured weekly pulse Google Doc.
    Returns the confirmation message or document ID.
    """
    return asyncio.run(_async_google_docs_append(content))


@tool
def gmail_create_draft_tool(subject: str, body: str, doc_url: str) -> str:
    """
    Creates an email draft in Gmail containing the Pulse note and Doc URL.
    Returns the confirmation message with the draft ID.
    """
    return asyncio.run(_async_gmail_create_draft(subject, body, doc_url))
