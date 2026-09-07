# Play Store Weekly Review Pulse

Turn raw Google Play Store reviews into a concise **weekly pulse** — top themes, real user quotes, and action ideas — delivered to **Google Docs** and **Gmail** via MCP.

---

## Project Structure

```
mcp/
├── docs/                          # Project documentation
│   ├── problemStatement.md
│   ├── architecture.md
│   ├── implementation-plan.md
│   ├── edge-cases.md
│   └── eval.md
├── agent/
│   ├── agent.py                   # LangChain Orchestrator (Phase 5)
│   ├── tools/
│   │   ├── ingest_reviews.py      # Review Ingestor (Phase 1)
│   │   ├── thematic_engine.py     # Clustering & Summarization (Phase 2)
│   │   ├── pulse_builder.py       # Note Assembly (Phase 3)
│   │   ├── docs_tool.py           # Google Docs MCP tool (Phase 4)
│   │   └── gmail_tool.py          # Gmail MCP tool (Phase 4)
│   └── prompts/
│       ├── cluster_prompt.txt     # LLM prompt for clustering (Phase 2)
│       └── pulse_prompt.txt       # LLM prompt for pulse (Phase 3)
├── config/
│   └── settings.py                # Typed config loaded from .env
├── data/
│   └── playstore_reviews.csv      # Play Store CSV export (not committed)
├── mcp_servers/
│   ├── google_docs_server/        # Google Docs MCP server config (Phase 4)
│   └── gmail_server/              # Gmail MCP server config (Phase 4)
├── main.py                        # Pipeline entry point
├── requirements.txt
├── .env.example                   # Copy to .env and fill in values
└── .gitignore
```

---

## Setup

### 1. Prerequisites

- Python ≥ 3.10
- Node.js ≥ 18 (required for MCP servers via `npx`)
- A Google account with access to Google Docs and Gmail
- A Groq API key (from [Groq Console](https://console.groq.com/))

### 2. Clone & Install

1. Clone the repository
2. Run `pip install -r requirements.txt` (or use virtual environment)
3. Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key |
| `RECIPIENT_EMAIL` | Email address to receive the Gmail draft |
| `GOOGLE_DOC_ID` | The ID of the Google Doc to append to (e.g. `1AbCdEfGhIjKlMnOpQrStUvWxYz`) |
| `REMOTE_MCP_URL` | The URL of the remote MCP server (e.g. `https://mcpserver-test-production.up.railway.app/mcp`) |
| `WEEKS_LOOKBACK` | Number of weeks of reviews to include (default: 1) |
| `MAX_REVIEWS_PER_FETCH` | Max reviews to fetch (capped for Groq free tier) |
| `GROQ_MODEL` | Groq model to use (default: `openai/gpt-oss-20b`) |

*Note: Reviews are automatically fetched from the Play Store via `google-play-scraper`. No manual CSV export is required.*

### 4. Run the Pipeline Locally

```bash
python main.py
```

### 5. Automated Weekly Scheduler (GitHub Actions)

This project includes a Phase 7 scheduler component powered by GitHub Actions. It will automatically run the pipeline every Monday at 9:00 AM UTC.

To enable the scheduler:
1. Push this repository to GitHub.
2. Go to your repository **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret** and add the following secrets matching your `.env`:
   - `GROQ_API_KEY`
   - `RECIPIENT_EMAIL`
   - `GOOGLE_DOC_ID`
   - `REMOTE_MCP_URL`
4. The workflow will now run automatically. You can also trigger it manually from the **Actions** tab.


---

## Running the Pipeline

```bash
python main.py
```

**What happens:**
1. Reads Play Store reviews from the CSV
2. Clusters them into ≤ 5 themes using Groq
3. Builds a ≤ 250-word weekly pulse note
4. Creates a Google Doc with the pulse (via MCP)
5. Creates a Gmail draft addressed to `RECIPIENT_EMAIL` (via MCP)

---

## Output

| Output | Where |
|---|---|
| Weekly pulse document | A new Google Doc (URL logged to console) |
| Draft email | Gmail Drafts folder addressed to `RECIPIENT_EMAIL` |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent framework | [LangChain](https://python.langchain.com/) |
| LLM | Groq via `langchain-groq` |
| MCP bridge | `langchain-mcp-adapters` |
| Delivery | Google Docs + Gmail via MCP servers |
| Data | pandas (CSV parsing) |

---

## Development Phases

| Phase | Status | Description |
|---|---|---|
| Phase 0 | ✅ Complete | Project setup & environment |
| Phase 1 | ✅ Complete | Review Ingestor |
| Phase 2 | ✅ Complete | Thematic Engine |
| Phase 3 | ✅ Complete | Pulse Builder |
| Phase 4 | ✅ Complete | MCP Integration |
| Phase 5 | ✅ Complete | LangChain Orchestrator |
| Phase 6 | ✅ Complete | Testing & Hardening |
| Phase 7 | ✅ Complete | Scheduler Component |

See [`docs/implementation-plan.md`](docs/implementation-plan.md) for the full plan.

---

## Key Constraints

- Reviews sourced from **public Play Store exports only** — no ToS-violating scraping
- Maximum **5 themes** in clustering; pulse highlights **top 3**
- Pulse note is **≤ 250 words**
- **No PII** in any output (reviewer names, emails, device IDs stripped at ingest)
- All Google Docs and Gmail interactions go through **MCP** — no direct REST calls
