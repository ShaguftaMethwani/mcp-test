# Architecture

## 1. Project Overview

This system transforms raw **Google Play Store** feedback into a concise **weekly pulse document** delivered via Google Docs and Gmail. It is built on an **MCP-first (Model Context Protocol)** integration pattern, which means all interaction with Google Docs and Gmail happens through MCP server tooling—no direct OAuth client or REST plumbing code. The orchestration layer is powered by **LangChain**, using its MCP adapter to bridge the agent and MCP tools seamlessly.

The system is designed to run on a recurring (weekly) schedule and produces a one-page, ≤250-word note surfacing the top 3 themes, 3 real user quotes, and 3 actionable next steps.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Orchestrator                         │
│                    (LLM-powered Agent)                      │
└──────────┬──────────────────────────┬───────────────────────┘
           │                          │
           ▼                          ▼
┌─────────────────┐        ┌──────────────────────┐
│  Review Ingestor│        │   MCP Client Layer    │
│  (Data Layer)   │        │  (Integration Layer)  │
└────────┬────────┘        └────────┬─────────────┘
         │                          │
         ▼                          ├──► Google Docs MCP Server
┌─────────────────┐                 │       (Create/Update Doc)
│ Thematic Engine │                 │
│ (Clustering &   │                 └──► Gmail MCP Server
│  Summarization) │                         (Create Draft)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pulse Builder  │
│ (Note Assembly) │
└─────────────────┘
```

---

## 3. Component Breakdown

### 3.1 Review Ingestor (Data Layer)

**Responsibility:** Fetch and normalize recent reviews from the Google Play Store.

| Property | Detail |
|---|---|
| **Source** | Public review export files (CSV/JSON/RSS) — no store-login scraping |
| **Time window** | Last 8–12 weeks |
| **Fields captured** | `rating`, `title`, `text`, `date` (and any other available metadata) |
| **Privacy filter** | Strip all PII at ingest: no usernames, emails, device IDs |
| **Output** | Normalized list of anonymous review objects |

**Approach:**
- **Play Store:** Use the exported CSV from the [Google Play Console](https://play.google.com/console) (`Reviews > Export`) or the publicly accessible Google Play RSS/Atom feed.
- Fields extracted: `rating`, `title`, `text`, `date`.
- Load into an in-memory list or lightweight local store (e.g., JSON file) for the agent to process.

---

### 3.2 Thematic Engine (Clustering & Summarization)

**Responsibility:** Group reviews into meaningful themes and extract signal.

| Property | Detail |
|---|---|
| **Max themes** | 5 (hard constraint) |
| **Pulse highlights** | Top 3 themes only |
| **Theme examples** | Onboarding, KYC, Payments, Statements, Withdrawals |
| **Quotes** | 3 verbatim (anonymous) snippets selected from top themes |
| **Action ideas** | 3 concrete, grounded next steps |

**Approach:**
- The LLM agent reads all ingested reviews in a single prompt or batched passes.
- Uses zero-shot or few-shot prompting to cluster reviews into ≤5 themes based on topic similarity.
- Ranks themes by review volume/frequency.
- Selects 3 representative verbatim quotes from the top themes (no paraphrasing or invented text).
- Generates 3 action ideas directly grounded in the identified themes.

---

### 3.3 Pulse Builder (Note Assembly)

**Responsibility:** Assemble the final one-page weekly note.

**Output format (≤250 words):**

```
Weekly App Review Pulse — [Date Range]

──────────────────────────────────────
TOP THEMES
1. [Theme Name]: [Brief summary]
2. [Theme Name]: [Brief summary]
3. [Theme Name]: [Brief summary]

──────────────────────────────────────
USER QUOTES
• "[Verbatim quote 1]"
• "[Verbatim quote 2]"
• "[Verbatim quote 3]"

──────────────────────────────────────
ACTION IDEAS
1. [Actionable next step grounded in themes]
2. [Actionable next step grounded in themes]
3. [Actionable next step grounded in themes]
──────────────────────────────────────
```

---

### 3.4 MCP Client Layer (Integration Layer)

**Responsibility:** Deliver the assembled pulse to Google Docs and Gmail using MCP tooling — no direct Google API calls.

#### 3.4.1 Google Docs MCP Server

| Operation | Detail |
|---|---|
| **Tool used** | `create_document` or `update_document` (via MCP) |
| **Purpose** | Persist the weekly pulse as a shareable Google Doc |
| **Output** | A link to the created/updated Google Doc |

**Flow:**
1. Pulse Builder produces the formatted note text.
2. MCP Client calls the Google Docs MCP server tool to create (or overwrite) a doc titled e.g. `Weekly App Review Pulse — [YYYY-WW]`.
3. The Doc URL is captured for inclusion in the Gmail draft.

#### 3.4.2 Gmail MCP Server

| Operation | Detail |
|---|---|
| **Tool used** | `create_draft` (via MCP) |
| **Purpose** | Compose a draft email to self / alias with the pulse or a link to it |
| **Output** | A Gmail draft ready to send |

**Flow:**
1. MCP Client calls the Gmail MCP server tool to create a draft.
2. Draft subject: `Weekly App Review Pulse — [Date Range]`
3. Draft body: The pulse text inline and/or a link to the Google Doc.
4. Draft recipient: Configured email address (self or team alias).

---

### 3.5 Orchestrator (LLM Agent)

**Responsibility:** Coordinate all components end-to-end in the correct sequence.

**Agent type:** A **LangChain** agent (`create_react_agent` or `AgentExecutor`) backed by an LLM (e.g., `ChatGroq` with Groq) and equipped with the following tools:
- `ingest_reviews` — LangChain tool that calls the Review Ingestor
- `cluster_and_summarize` — LangChain tool that calls the Thematic Engine (LLM chain)
- `build_pulse` — LangChain tool that calls the Pulse Builder
- `google_docs_create` — MCP tool exposed via `langchain-mcp-adapters`
- `gmail_create_draft` — MCP tool exposed via `langchain-mcp-adapters`

**Execution sequence:**
```
1. ingest_reviews(time_window="8-12 weeks")
      └─► Returns: [list of anonymous review objects]

2. cluster_and_summarize(reviews)
      └─► Returns: {themes, quotes, action_ideas}

3. build_pulse(themes, quotes, action_ideas)
      └─► Returns: formatted_note (str, ≤250 words)

4. google_docs_create(title, content=formatted_note)
      └─► Returns: doc_url

5. gmail_create_draft(subject, body=formatted_note, doc_link=doc_url)
      └─► Returns: draft_id / confirmation
```

---

## 4. Data Flow Diagram

```
[Play Store Export / CSV]  ──►  [Review Ingestor]  ──►  [raw reviews: rating, title, text, date]
                                                                  ▼
                                                     [PII Stripper / Normalizer]
                                                                  │
                                                                  ▼
                                                     [Thematic Engine / LLM]
                                                       (cluster → top 3 themes,
                                                        3 quotes, 3 action ideas)
                                                                  │
                                                                  ▼
                                                        [Pulse Builder]
                                                    (assembles ≤250-word note)
                                                           │          │
                                                           ▼          ▼
                                              [Google Docs MCP]  [Gmail MCP]
                                              (Create/Update Doc) (Create Draft)
                                                           │          │
                                                           ▼          ▼
                                                    [Google Doc]  [Gmail Draft]
                                                    (shareable)   (ready to send)
```

---

## 5. Technology Choices

| Layer | Technology / Approach |
|---|---|
| **Agent Framework** | **LangChain** (`create_react_agent` / `AgentExecutor`) |
| **LLM** | Groq via `ChatGroq` (LangChain Groq integration) |
| **MCP ↔ LangChain bridge** | `langchain-mcp-adapters` — converts MCP tools to LangChain tools |
| **Review Ingestion** | Play Store CSV export from Google Play Console |
| **Google Docs integration** | MCP server (Google Docs MCP tool) via `langchain-mcp-adapters` |
| **Gmail integration** | MCP server (Gmail MCP tool) via `langchain-mcp-adapters` |
| **Local storage** | JSON / in-memory — lightweight, no DB needed |
| **Scheduling** | Cron job / Cloud Scheduler / manual trigger |
| **Auth** | Handled entirely by MCP server layer (no bespoke OAuth code) |

---

## 6. Key Constraints & How the Architecture Addresses Them

| Constraint | How It's Addressed |
|---|---|
| **No ToS-violating scraping** | Ingestion uses only public RSS feeds and official console CSV exports |
| **Max 5 themes** | Hard-coded in the Thematic Engine prompt and output schema |
| **≤250 words** | Pulse Builder enforces a word limit in the assembly step |
| **No PII** | PII Stripper runs at ingest time; agent is instructed not to include usernames or identifiers in quotes |
| **MCP-first integration** | All Docs/Gmail calls go through MCP server tools — no direct REST client code |
| **Verbatim quotes only** | Agent is explicitly prompted to select existing review text, never paraphrase or generate quotes |

---

## 7. Directory Structure (Proposed)

```
mcp/
├── docs/
│   ├── problemStatement.md     # Project requirements
│   └── architecture.md         # This document
├── agent/
│   ├── agent.py                # LLM Agent definition (Orchestrator)
│   ├── tools/
│   │   ├── ingest_reviews.py   # Review Ingestor tool
│   │   ├── thematic_engine.py  # Clustering & summarization tool
│   │   ├── pulse_builder.py    # Note assembly tool
│   │   ├── docs_tool.py        # Google Docs MCP wrapper tool
│   │   └── gmail_tool.py       # Gmail MCP wrapper tool
│   └── prompts/
│       ├── cluster_prompt.txt  # LLM prompt for theme clustering
│       └── pulse_prompt.txt    # LLM prompt for pulse generation
├── data/
│   └── playstore_reviews.csv   # Play Store export from Google Play Console
├── config/
│   └── settings.py             # Config: email alias, date window, theme list
├── mcp_servers/
│   ├── google_docs_server/     # MCP server config for Google Docs
│   └── gmail_server/           # MCP server config for Gmail
└── README.md
```

---

## 8. Security & Privacy Considerations

- **Auth isolation:** All OAuth tokens and credentials are managed inside the MCP server layer. The agent and tools never see raw credentials.
- **PII stripping:** Review ingestor strips reviewer usernames, display names, device IDs, and any embedded emails before passing data to the LLM.
- **Verbatim quotes:** Selected from existing review text only — never AI-generated or paraphrased to avoid fabrication.
- **No persistent store of raw reviews:** Once the pulse is generated and delivered, raw review data is discarded (not stored long-term).

---

## 9. Future Extensibility

| Enhancement | Approach |
|---|---|
| **Multi-app support** | Parameterize `ingest_reviews` with Play Store package name |
| **Trend tracking** | Persist weekly pulses and compare theme shifts over time |
| **App Store support** | Extend ingestor to also pull from iTunes RSS / App Store Connect exports |
| **Slack/Teams delivery** | Add a Slack or Teams MCP tool in the integration layer |
| **Automated scheduling** | Wrap the agent in a Cloud Scheduler or GitHub Actions cron |
| **Confidence scoring** | Add review volume and rating distribution metadata to themes |
| **Sentiment overlay** | Augment thematic engine with per-theme sentiment scores |
