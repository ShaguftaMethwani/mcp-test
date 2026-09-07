# Problem Statement

**App:** [Groww — Stocks & Mutual Fund](https://play.google.com/store/apps/details?id=com.nextbillion.groww&hl=en_IN)
**Platform:** Google Play Store
**Package ID:** `com.nextbillion.groww`

---

The goal is to turn raw **Google Play Store** feedback for the **Groww** investing app into a weekly pulse your team can scan in minutes: what users care about, what they actually said, and what to do next. Reviews are already public; the system aggregates, themes, summarises, and delivers that insight through familiar surfaces — Google Docs for the written pulse and Gmail for a draft you can send — without handling credentials or REST wiring manually.

## End-to-End Flow

1. **Fetch** the last 8 weeks of Groww Play Store reviews programmatically via `google-play-scraper` (public data, no login, no ToS violation).
2. **Cluster** them into ≤ 5 themes and distil a one-page weekly pulse note.
3. **Publish** that note to Google Docs (via MCP).
4. **Draft** an email containing or linking to the pulse (via Gmail MCP).

## Why Groww

Groww is one of India's fastest-growing investment platforms, serving millions of retail investors across Stocks, Mutual Funds, FDs, Gold, and US Stocks. Its Play Store listing accumulates hundreds of reviews weekly — covering topics like:

- KYC / account opening friction
- Payment gateway failures
- Portfolio / statement accuracy
- Withdrawal & fund transfer delays
- App crashes and performance
- Brokerage & tax queries

A weekly pulse of these signals lets the Product, Growth, Support, and Leadership teams act on real user pain rather than gut feel.

## Who This Helps

| Audience | Why |
|---|---|
| **Product / Growth** | Prioritise fixes and improvements from real user signals |
| **Support** | Align response messaging with what users are actually saying |
| **Leadership** | One-page health check without drowning in raw reviews |

## What Must Be Built

- **Fetch** Groww Play Store reviews for the last **8 weeks** using `google-play-scraper` (no CSV export needed).
- **Group** reviews into ≤ 5 themes (e.g. KYC, payments, crashes, withdrawals, performance).
- **Generate** a weekly one-page pulse with:
  - Top 3 themes (by volume)
  - 3 verbatim user quotes (one per theme)
  - 3 concrete action ideas grounded in the themes
- **Deliver** the pulse via:
  - A new Google Doc (created via MCP)
  - A Gmail draft addressed to the configured recipient (via MCP)

## Integrations: Google Docs & Gmail via MCP

All Google Docs and Gmail interactions go through **MCP** (Model Context Protocol) servers — no bespoke OAuth or direct REST calls. LangChain's `langchain-mcp-adapters` exposes MCP server tools as native LangChain tools so the agent can call Docs and Gmail directly.

## Agent Framework: LangChain

The orchestration layer uses **LangChain** (`create_react_agent` / `AgentExecutor`) backed by **Groq** (`ChatGroq`). LangChain manages the agent loop, tool calling, prompt management, and LLM abstraction needed to wire together review fetching, thematic clustering, pulse assembly, and MCP-based delivery.

## Key Constraints

| Constraint | Rule |
|---|---|
| **Source** | Public Play Store reviews via `google-play-scraper` — no login, no ToS-violating scraping |
| **Time window** | Last **8 weeks** of reviews |
| **Themes** | Maximum 5; pulse highlights top 3 |
| **Pulse length** | ≤ 250 words |
| **Privacy** | No PII in any artifact — usernames, device IDs, and emails stripped at ingest |
| **Quotes** | Must be verbatim substrings of actual review text — no paraphrasing |

## Future Scope

- Trend comparison: this week vs. last week by theme
- Rating-weighted clustering (weight 1-star reviews more heavily)
- Slack / Teams delivery in addition to Gmail
