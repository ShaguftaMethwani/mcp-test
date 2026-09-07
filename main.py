"""
main.py — Entry point for the Play Store Weekly Review Pulse pipeline.

Usage:
    python main.py

This triggers the LangChain agent to:
  1. Ingest Play Store reviews from the Groww app
  2. Cluster them into themes and extract quotes + action ideas
  3. Assemble a one-page weekly pulse note
  4. Create a Google Doc with the pulse (via MCP)
  5. Create a Gmail draft with the pulse and Doc link (via MCP)

See docs/implementation-plan.md for the full phase-by-phase plan.
"""

import logging
import sys
import time


def main():
    """Run the full weekly pulse pipeline."""
    # ── Configure logging ─────────────────────────────────────────────────────
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger(__name__)

    print()
    print("=" * 60)
    print("  Play Store Weekly Review Pulse")
    print("  Powered by LangChain + Groq + MCP")
    print("=" * 60)
    print()

    start = time.time()

    try:
        from agent.agent import run_pipeline
        result = run_pipeline()

        elapsed = time.time() - start

        print()
        print("=" * 60)
        print(f"  ✅ Pipeline finished in {elapsed:.1f}s")
        print("=" * 60)
        print()
        print(result.get("output", ""))
        print()

    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user.")
        sys.exit(130)
    except Exception as exc:
        elapsed = time.time() - start
        logger.error("Pipeline failed after %.1fs: %s", elapsed, exc, exc_info=True)
        print()
        print("=" * 60)
        print(f"  ❌ Pipeline failed after {elapsed:.1f}s")
        print("=" * 60)
        print(f"\nError: {exc}")
        print("\nTroubleshooting:")
        print("  • Check your .env file has GROQ_API_KEY and RECIPIENT_EMAIL set")
        print("  • For MCP tools, ensure credentials.json is in the MCP server dirs")
        print("  • Or set MCP_MOCK_GOOGLE=true to test without Google credentials")
        print("  • See mcp_servers/google_docs_server/README.md for setup help")
        sys.exit(1)


if __name__ == "__main__":
    main()
