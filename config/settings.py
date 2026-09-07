"""
config/settings.py

Loads environment variables from .env and exposes them as typed constants.
All required variables are validated at import time so the app fails fast
if the environment is misconfigured.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from the project root ─────────────────────────────────────────
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")


def _require(key: str) -> str:
    """Return the value of an env var or exit with a clear error."""
    value = os.getenv(key, "").strip()
    if not value:
        print(f"[ERROR] Required environment variable '{key}' is not set.")
        print(f"        Copy .env.example to .env and fill in your values.")
        sys.exit(1)
    return value


def _optional(key: str, default: str) -> str:
    """Return the value of an env var or a default."""
    return os.getenv(key, default).strip() or default


# ── Required ─────────────────────────────────────────────────────────────────

# Groq API key
GROQ_API_KEY: str = _require("GROQ_API_KEY")

# Recipient email for the Gmail draft
RECIPIENT_EMAIL: str = _require("RECIPIENT_EMAIL")

# Google Doc ID to append the weekly pulse to
GOOGLE_DOC_ID: str = _require("GOOGLE_DOC_ID")

# ── Optional (with sensible defaults) ────────────────────────────────────────

# Groq model name
GROQ_MODEL: str = _optional("GROQ_MODEL", "llama-3.1-70b-versatile")

# Groww Play Store package ID
APP_ID: str = _optional("APP_ID", "com.nextbillion.groww")

# Max reviews to fetch per scraper call
_max_reviews_raw = _optional("MAX_REVIEWS_PER_FETCH", "40")
try:
    MAX_REVIEWS_PER_FETCH: int = int(_max_reviews_raw)
except ValueError:
    print(f"[ERROR] MAX_REVIEWS_PER_FETCH must be an integer, got: '{_max_reviews_raw}'")
    sys.exit(1)

# Play Store country and language for review fetching
REVIEW_COUNTRY: str = _optional("REVIEW_COUNTRY", "in")
REVIEW_LANG: str = _optional("REVIEW_LANG", "en")

# How many weeks of reviews to include
_weeks_raw = _optional("WEEKS_LOOKBACK", "1")
try:
    WEEKS_LOOKBACK: int = int(_weeks_raw)
    if WEEKS_LOOKBACK <= 0:
        raise ValueError
except ValueError:
    print(f"[ERROR] WEEKS_LOOKBACK must be a positive integer, got: '{_weeks_raw}'")
    sys.exit(1)

# ── MCP Server Config ─────────────────────────────────────────────────────────

REMOTE_MCP_URL: str = _optional(
    "REMOTE_MCP_URL", 
    "https://mcpserver-test-production.up.railway.app/mcp"
)

# ── Derived / computed constants ──────────────────────────────────────────────

# Max themes the Thematic Engine may produce (hard constraint)
MAX_THEMES: int = 5

# Target themes to highlight in the pulse
PULSE_THEMES: int = 3

# Max word count for the weekly pulse note
MAX_PULSE_WORDS: int = 250

# Number of verbatim quotes to include
NUM_QUOTES: int = 3

# Number of action ideas to include
NUM_ACTIONS: int = 3
