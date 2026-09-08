# Play Store Weekly Review Pulse

Turn raw Google Play Store reviews into a concise **weekly pulse** — top themes, real user quotes, action ideas, and fee confusion explanations — delivered to **Google Docs** and **Gmail** via MCP, with a **React dashboard** for human-in-the-loop review and approval.

---

## Features

- **Automated Review Ingestion** — Fetches live reviews from the Google Play Store (no manual CSV export needed).
- **AI-Powered Clustering** — Groups reviews into ≤5 themes, selects 3 verbatim quotes, generates 3 action ideas.
- **Fee Confusion Detection** — Identifies recurring confusion around hidden fees/charges and generates a customer-facing support macro.
- **Human-in-the-Loop Approval** — Dashboard lets you review AI outputs before dispatching to Google Docs and Gmail.
- **MCP Integration** — All Google Docs and Gmail interactions happen via a remote MCP server (SSE transport) — no OAuth code in the app.
- **Automated Scheduling** — GitHub Actions runs the pipeline weekly every Monday at 9:00 AM UTC.

---

## Project Structure

```
mcp/
├── docs/                              # Project documentation
│   ├── architecture.md                # System architecture
│   ├── implementation-plan.md         # Development phases
│   ├── edge-cases.md                  # Edge case handling
│   └── eval.md                        # Evaluation methodology
├── agent/
│   ├── agent.py                       # LangChain ReAct Agent
│   ├── tools/
│   │   ├── ingest_reviews.py          # Live Play Store review fetcher
│   │   ├── thematic_engine.py         # LLM-powered clustering
│   │   ├── pulse_builder.py           # Weekly note assembly
│   │   ├── fee_explainer.py           # Fee confusion explainer
│   │   ├── approval_gate.py           # Human approval logic
│   │   ├── docs_tool.py               # Google Docs MCP wrapper
│   │   └── gmail_tool.py              # Gmail MCP wrapper
│   └── prompts/
│       ├── cluster_prompt.txt
│       ├── pulse_prompt.txt
│       └── fee_explainer_prompt.txt
├── config/
│   └── settings.py                    # Typed config from .env
├── frontend/                          # React Dashboard
│   ├── src/
│   │   ├── App.jsx                    # Main app with API integration
│   │   ├── index.css                  # Design system tokens
│   │   └── components/                # UI components
│   ├── vercel.json                    # Vercel SPA config
│   ├── vite.config.js
│   └── package.json
├── api.py                             # FastAPI backend server
├── main.py                            # CLI pipeline entry point
├── Procfile                           # Railway start command
├── requirements.txt
├── .env.example
└── .github/workflows/weekly-pulse.yml # GitHub Actions scheduler
```

---

## Setup

### Prerequisites

- Python ≥ 3.10
- Node.js ≥ 18
- A Groq API key ([Groq Console](https://console.groq.com/))

### 1. Clone & Install Backend

```bash
git clone https://github.com/ShaguftaMethwani/mcp-test.git
cd mcp-test

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq API key |
| `RECIPIENT_EMAIL` | ✅ | Email address for the Gmail draft |
| `GOOGLE_DOC_ID` | ✅ | ID of the Google Doc to append to |
| `REMOTE_MCP_URL` | ✅ | Remote MCP server URL |
| `GROQ_MODEL` | ❌ | Groq model (default: `openai/gpt-oss-120b`) |
| `APP_ID` | ❌ | Play Store package ID (default: `com.nextbillion.groww`) |
| `WEEKS_LOOKBACK` | ❌ | Weeks of reviews to fetch (default: `2`) |
| `MAX_REVIEWS_PER_FETCH` | ❌ | Max reviews to fetch (default: `50`) |

### 3. Install Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env` for local development:

```
VITE_API_BASE_URL=http://localhost:8000
```

---

## Running Locally

### Option A: Full Dashboard (Frontend + Backend)

Start both servers in separate terminals:

**Terminal 1 — Backend:**
```bash
# From project root
source .venv/bin/activate
uvicorn api:app --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) to use the dashboard.

**Pipeline flow:**
1. Click **"Trigger Pipeline"** → Runs Steps 1–4 (Ingest → Cluster → Pulse → Fee Explainer).
2. Review the AI-generated outputs on the dashboard.
3. Click **"Approve & Trigger MCP Actions"** → Runs Steps 5–6 (Google Docs + Gmail via MCP).

### Option B: CLI Only (No UI)

```bash
source .venv/bin/activate
python main.py
```

This runs the full 6-step pipeline end-to-end without the approval gate.

---

## Production Deployment

The system is designed for a split deployment:

| Component | Platform | Details |
|---|---|---|
| **Frontend** | Vercel | React dashboard |
| **Backend** | Railway | FastAPI API server |
| **MCP Server** | Railway | Remote Google integrations |

### Deploy Backend to Railway

1. Push this repository to GitHub.
2. Create a new Railway project from the GitHub repo.
3. Railway will auto-detect the `Procfile` and use: `uvicorn api:app --host 0.0.0.0 --port $PORT`.
4. Add environment variables in Railway: `GROQ_API_KEY`, `RECIPIENT_EMAIL`, `GOOGLE_DOC_ID`, `REMOTE_MCP_URL`.
5. Note the generated public URL (e.g., `https://your-app.up.railway.app`).

### Deploy Frontend to Vercel

1. Import the same GitHub repository into Vercel.
2. Set **Root Directory** to `frontend`.
3. Add environment variable: `VITE_API_BASE_URL=https://your-app.up.railway.app` (your Railway URL, no trailing slash).
4. Deploy!

### Automated Weekly Scheduler (GitHub Actions)

The pipeline runs automatically every Monday at 9:00 AM UTC via GitHub Actions.

To enable:
1. Go to your GitHub repo **Settings > Secrets and variables > Actions**.
2. Add secrets: `GROQ_API_KEY`, `RECIPIENT_EMAIL`, `GOOGLE_DOC_ID`, `REMOTE_MCP_URL`.
3. The workflow triggers automatically. You can also trigger it manually from the **Actions** tab.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vite + React + Tailwind CSS v4 |
| Backend API | FastAPI + Uvicorn |
| Agent Framework | LangChain (`create_react_agent`) |
| LLM | Groq via `ChatGroq` |
| MCP Bridge | `langchain-mcp-adapters` (SSE) |
| Review Fetching | `google-play-scraper` |
| Delivery | Google Docs + Gmail via remote MCP server |
| Frontend Hosting | Vercel |
| Backend Hosting | Railway |
| Scheduling | GitHub Actions (cron) |

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/status` | GET | Get current pipeline state |
| `/api/run-pipeline` | POST | Execute analysis (Steps 1–4) |
| `/api/approve` | POST | Approve and dispatch via MCP (Steps 5–6) |
| `/api/reject` | POST | Reject and cancel MCP dispatch |

---

## Key Constraints

- Reviews sourced from **public Play Store data** via `google-play-scraper` — no ToS-violating scraping.
- Maximum **5 themes** in clustering; pulse highlights **top 3**.
- Pulse note is **≤ 250 words**.
- **No PII** in any output (reviewer names, emails, device IDs stripped at ingest).
- All Google Docs and Gmail interactions go through **MCP** — no direct REST calls.
- Reviews batched at **50 per LLM call** to stay within Groq's 8K TPM free-tier limit.
