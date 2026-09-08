# Architecture

## 1. Project Overview

This system transforms raw **Google Play Store** feedback into a concise **weekly pulse document** delivered via Google Docs and Gmail, while simultaneously extracting product friction points (like fee confusion) for customer support.

It is built using a modern decoupled architecture:

1. **Frontend**: A React/Vite dashboard deployed on **Vercel**.
2. **Backend**: A FastAPI server acting as an API/middleware layer deployed on **Railway**.
3. **AI Orchestrator**: LangChain ReAct agents running the clustering, summarization, and fee explanation pipeline.
4. **Integration Layer (MCP)**: A remote Model Context Protocol (MCP) server that handles Google Docs and Gmail API interactions over **Server-Sent Events (SSE)**.

A core feature is the **Human-in-the-Loop Approval Gate**, which pauses the pipeline after the AI finishes its analysis, allowing a human to review the generated content before it is dispatched to external tools via MCP.

---

## 2. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Vercel)                                    │
│              Vite + React + Tailwind CSS v4                              │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────────────────┐      │
│  │   Review     │  │   Synthesized    │  │     MCP Dispatcher    │      │
│  │ Intelligence │  │    Outputs       │  │   (Approval Gate UI)  │      │
│  └──────────────┘  └──────────────────┘  └───────────────────────┘      │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │  REST API (VITE_API_BASE_URL)
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     BACKEND (Railway)                                     │
│                    FastAPI (api.py)                                       │
│                                                                          │
│  POST /api/run-pipeline ──► Steps 1–4 (Analysis Phase)                   │
│  POST /api/approve      ──► Steps 5–6 (MCP Dispatch Phase)               │
│  POST /api/reject       ──► Cancel MCP dispatch                          │
│  GET  /api/status       ──► Current pipeline state                       │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                   AI ORCHESTRATION LAYER                                  │
│                  LangChain ReAct Agent                                    │
│                                                                          │
│  Step 1: Review Ingestor ──► google-play-scraper (live fetch)            │
│  Step 2: Thematic Engine ──► Groq LLM (cluster into ≤5 themes)          │
│  Step 3: Pulse Builder   ──► Groq LLM (≤250-word note)                  │
│  Step 4: Fee Explainer   ──► Groq LLM (support macro)                   │
│                                                                          │
│  ─── APPROVAL GATE (human reviews content) ───                           │
│                                                                          │
│  Step 5: Google Docs     ──► Append pulse to Doc via MCP                 │
│  Step 6: Gmail Draft     ──► Create email draft via MCP                  │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │  SSE (Server-Sent Events)
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                   REMOTE MCP SERVER (Railway)                             │
│         https://mcpserver-test-production.up.railway.app/mcp             │
│                                                                          │
│  google_docs_append ──► Google Docs API (OAuth managed by MCP)           │
│  gmail_create_draft ──► Gmail API (OAuth managed by MCP)                 │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Breakdown

### 3.1 Frontend Layer (React Dashboard)

**Responsibility:** Provide a human-in-the-loop interface to trigger, review, and approve the AI pipeline.

| Property | Detail |
|---|---|
| **Framework** | Vite + React |
| **Styling** | Tailwind CSS v4 with custom design tokens |
| **Deployment** | Vercel (Root Directory: `frontend/`) |
| **Config** | `VITE_API_BASE_URL` env variable pointing to Railway backend |

**Layout (3-column dashboard):**
- **Review Intelligence** (left): Cluster volume distribution bars, flagged fee-confusion quotes.
- **Synthesized Outputs** (center): Weekly Pulse note and Support Fee Explainer macro.
- **MCP Dispatcher** (right): Approval gate with payload previews for Google Docs and Gmail, plus Approve/Reject buttons.

**Key Files:**
- `frontend/src/App.jsx` — Main container, state management, API calls.
- `frontend/src/components/ReviewIntelligence.jsx` — Cluster visualization.
- `frontend/src/components/SynthesizedOutputs.jsx` — Pulse & fee explainer display.
- `frontend/src/components/McpDispatcher.jsx` — Approval gate UI.
- `frontend/src/components/PipelineStepper.jsx` — Step progress indicator.
- `frontend/vercel.json` — SPA rewrite rules for Vercel.

---

### 3.2 API Layer (FastAPI)

**Responsibility:** Wrap the AI agent's tools in stateless REST endpoints for frontend interaction.

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/status` | GET | Return current pipeline state |
| `/api/run-pipeline` | POST | Execute Steps 1–4 (Ingest → Cluster → Pulse → Fee Explainer) |
| `/api/approve` | POST | Execute Steps 5–6 (Google Docs + Gmail via MCP) |
| `/api/reject` | POST | Cancel MCP dispatch |

**Key Details:**
- CORS middleware configured with `allow_origins=["*"]` to accept requests from Vercel.
- Imports and calls the agent tools directly (no LLM orchestration needed at the API layer).
- Deployed on Railway with `Procfile`: `web: uvicorn api:app --host 0.0.0.0 --port $PORT`.

---

### 3.3 Review Ingestor (Data Layer)

**Responsibility:** Fetch and normalize recent reviews from the Google Play Store.

| Property | Detail |
|---|---|
| **Source** | Live fetch via `google-play-scraper` (no auth needed) |
| **Time window** | Configurable via `WEEKS_LOOKBACK` (default: 2 weeks) |
| **Fields captured** | `rating`, `title`, `text`, `date` |
| **Privacy filter** | Strips PII (usernames, emails, device IDs) at ingest |
| **Short review filter** | Drops reviews with fewer than 8 words |
| **Storage** | In-memory only — no persistent database |

---

### 3.4 Thematic Engine (Clustering & Summarization)

**Responsibility:** Group reviews into meaningful themes and extract signal using Groq LLM.

| Property | Detail |
|---|---|
| **LLM** | Groq via `ChatGroq` (`openai/gpt-oss-120b`) |
| **Max themes** | 5 (hard constraint) |
| **Pulse highlights** | Top 3 themes ranked by volume |
| **Quotes** | 3 verbatim (anonymous) snippets — verified against source text |
| **Action ideas** | 3 concrete, grounded next steps |
| **Fee confusion** | Detects recurring confusion around hidden charges/fees |
| **Batching** | Reviews are split into batches of 50 to stay within Groq's 8K TPM limit |

---

### 3.5 Fee Explainer (Milestone 2)

**Responsibility:** If fee/charge confusion is detected by the Thematic Engine, generate a customer-facing support macro that explains the fee clearly.

| Property | Detail |
|---|---|
| **Input** | `fee_confusion` object from the Thematic Engine |
| **Output** | A ready-to-use customer support response (plain text) |
| **Prompt** | `agent/prompts/fee_explainer_prompt.txt` |

---

### 3.6 Pulse Builder (Note Assembly)

**Responsibility:** Assemble the final one-page weekly note (≤250 words).

**Output format:**
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
1. [Actionable next step]
2. [Actionable next step]
3. [Actionable next step]
──────────────────────────────────────
```

---

### 3.7 MCP Integration Layer (Remote Server via SSE)

**Responsibility:** Deliver outputs to Google Docs and Gmail using a **remote MCP server** — no direct Google API calls or OAuth code in the main codebase.

| Property | Detail |
|---|---|
| **Protocol** | Model Context Protocol (MCP) over Server-Sent Events (SSE) |
| **Server URL** | `https://mcpserver-test-production.up.railway.app/mcp` |
| **Bridge** | `langchain-mcp-adapters` converts MCP tools to LangChain tools |
| **Auth** | OAuth tokens managed entirely inside the MCP server |

**Available MCP Tools:**
- `google_docs_append` — Appends the Weekly Pulse to a configured Google Document.
- `gmail_create_draft` — Creates a Gmail draft addressed to `RECIPIENT_EMAIL`.

---

## 4. Execution Flow (Human-in-the-Loop)

```
User clicks "Trigger Pipeline"
         │
         ▼
┌─── POST /api/run-pipeline ───────────────────────────────┐
│  Step 1: Ingest reviews (google-play-scraper)            │
│  Step 2: Cluster & summarize (Groq LLM, batched)         │
│  Step 3: Build pulse note (Groq LLM)                     │
│  Step 4: Generate fee explainer (Groq LLM, if needed)    │
│  ──► Return JSON to frontend                             │
└──────────────────────────────────────────────────────────┘
         │
         ▼
   User reviews outputs on dashboard
   (Pulse note, Fee Explainer, Cluster data)
         │
         ├─── Approve ──► POST /api/approve
         │                  Step 5: Append to Google Doc (MCP)
         │                  Step 6: Create Gmail draft (MCP)
         │                  ──► Return success to frontend
         │
         └─── Reject  ──► POST /api/reject
                           ──► Pipeline cancelled, no MCP calls
```

---

## 5. Deployment Architecture

| Component | Platform | URL |
|---|---|---|
| **Frontend** | Vercel | `https://<your-app>.vercel.app` |
| **Backend (API)** | Railway | `https://<your-app>.up.railway.app` |
| **MCP Server** | Railway | `https://mcpserver-test-production.up.railway.app/mcp` |

**Frontend (Vercel) Configuration:**
- Root Directory: `frontend/`
- Framework: Vite (auto-detected)
- Environment Variable: `VITE_API_BASE_URL=https://<railway-backend-url>`

**Backend (Railway) Configuration:**
- Start Command (via `Procfile`): `web: uvicorn api:app --host 0.0.0.0 --port $PORT`
- Environment Variables: `GROQ_API_KEY`, `RECIPIENT_EMAIL`, `GOOGLE_DOC_ID`, `REMOTE_MCP_URL`

**Automated Scheduler (GitHub Actions):**
- Runs `python main.py` every Monday at 9:00 AM UTC.
- Secrets configured in GitHub Actions: `GROQ_API_KEY`, `RECIPIENT_EMAIL`, `GOOGLE_DOC_ID`, `REMOTE_MCP_URL`.

---

## 6. Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | Vite + React + Tailwind CSS v4 |
| **Backend API** | FastAPI + Uvicorn |
| **Agent Framework** | LangChain (`create_react_agent`) |
| **LLM** | Groq via `ChatGroq` (`openai/gpt-oss-120b`) |
| **MCP Bridge** | `langchain-mcp-adapters` (SSE transport) |
| **Review Fetching** | `google-play-scraper` (live, no auth) |
| **Delivery** | Google Docs + Gmail via remote MCP server |
| **Frontend Hosting** | Vercel |
| **Backend Hosting** | Railway |

---

## 7. Directory Structure

```
mcp/
├── docs/                              # Project documentation
│   ├── problemStatement.md
│   ├── architecture.md                # This document
│   ├── implementation-plan.md
│   ├── edge-cases.md
│   └── eval.md
├── agent/
│   ├── agent.py                       # LangChain ReAct Agent (Orchestrator)
│   ├── tools/
│   │   ├── ingest_reviews.py          # Review Ingestor (live Play Store fetch)
│   │   ├── thematic_engine.py         # Clustering & Summarization (Groq LLM)
│   │   ├── pulse_builder.py           # Note Assembly (Groq LLM)
│   │   ├── fee_explainer.py           # Fee Confusion Explainer (Milestone 2)
│   │   ├── approval_gate.py           # Human-in-the-loop approval logic
│   │   ├── docs_tool.py               # Google Docs MCP wrapper
│   │   └── gmail_tool.py              # Gmail MCP wrapper
│   └── prompts/
│       ├── cluster_prompt.txt         # LLM prompt for clustering
│       ├── pulse_prompt.txt           # LLM prompt for pulse generation
│       └── fee_explainer_prompt.txt   # LLM prompt for fee explainer
├── config/
│   └── settings.py                    # Typed config loaded from .env
├── frontend/                          # React Dashboard (Vercel)
│   ├── src/
│   │   ├── App.jsx                    # Main app with API integration
│   │   ├── index.css                  # Design system tokens
│   │   └── components/
│   │       ├── Sidebar.jsx
│   │       ├── TopBar.jsx
│   │       ├── PipelineStepper.jsx
│   │       ├── ReviewIntelligence.jsx
│   │       ├── SynthesizedOutputs.jsx
│   │       └── McpDispatcher.jsx
│   ├── vercel.json                    # Vercel SPA rewrite rules
│   ├── vite.config.js                 # Vite config with proxy
│   └── package.json
├── api.py                             # FastAPI server (Railway)
├── main.py                            # CLI pipeline entry point
├── Procfile                           # Railway start command
├── requirements.txt
├── .env.example
├── .github/
│   └── workflows/
│       └── weekly-pulse.yml           # GitHub Actions scheduler
└── .gitignore
```

---

## 8. Security & Privacy Considerations

- **Auth isolation:** All OAuth tokens and credentials are managed inside the remote MCP server. The agent and API never see raw Google credentials.
- **PII stripping:** Review ingestor strips reviewer usernames, display names, device IDs, and embedded emails before passing data to the LLM.
- **Verbatim quotes:** Selected from existing review text only — never AI-generated or paraphrased.
- **No persistent store of raw reviews:** Once the pipeline completes, raw review data is discarded from memory.
- **CORS:** Backend configured to accept cross-origin requests from the Vercel frontend.
- **Environment variables:** All secrets (`GROQ_API_KEY`, `GOOGLE_DOC_ID`, etc.) stored in platform-level env vars, never committed to the repo.
