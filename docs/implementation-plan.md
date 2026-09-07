# Implementation Plan

**Project:** Play Store Weekly Review Pulse
**Stack:** LangChain · Groq · MCP (Google Docs + Gmail) · Python
**Delivery:** Phase-by-phase, each phase is independently runnable and testable.

---

## Overview

```
Phase 0 → Project Setup & Environment
Phase 1 → Review Ingestor (Data Layer)
Phase 2 → Thematic Engine (Clustering & Summarization)
Phase 3 → Pulse Builder (Note Assembly)
Phase 4 → MCP Integration (Google Docs & Gmail)
Phase 5 → LangChain Orchestrator (Agent Wiring)
Phase 6 → End-to-End Testing & Hardening
Phase 7 → Scheduler Component (Automation)
```

---

## Phase 0 — Project Setup & Environment

**Goal:** Establish the project skeleton, dependencies, and configuration so every subsequent phase has a clean foundation to build on.

### Tasks

- [ ] Create the project directory structure as defined in `architecture.md §7`:
  ```
  mcp/
  ├── docs/
  ├── agent/
  │   ├── tools/
  │   └── prompts/
  ├── data/
  ├── config/
  ├── mcp_servers/
  │   ├── google_docs_server/
  │   └── gmail_server/
  └── README.md
  ```
- [ ] Create `requirements.txt` (or `pyproject.toml`) with core dependencies:
  ```
  langchain
  langchain-groq               # ChatGroq (Groq)
  langchain-mcp-adapters       # MCP ↔ LangChain bridge
  python-dotenv
  pandas                       # CSV parsing
  ```
- [ ] Create `.env.example` with required environment variables:
  ```
  GROQ_API_KEY=            # Groq API key
  RECIPIENT_EMAIL=         # Email alias for Gmail draft
  PLAY_STORE_CSV_PATH=     # Path to exported Play Store CSV
  WEEKS_LOOKBACK=10        # Review window (8-12 weeks)
  ```
- [ ] Create `config/settings.py` — loads `.env`, exposes typed config constants.
- [ ] Set up `.gitignore` (exclude `.env`, `data/*.csv`, `__pycache__`).
- [ ] Verify Python version ≥ 3.10.

### Exit Criteria
- `pip install -r requirements.txt` completes without errors.
- `python -c "import langchain; import langchain_groq"` succeeds.
- Directory structure is in place.

---

## Phase 1 — Review Ingestor (Data Layer)

**Goal:** Load, normalize, filter, and PII-strip raw Play Store reviews from a CSV export so they are safe and ready for the Thematic Engine.

### Input
- Play Store CSV export from Google Play Console (`Reviews > Export`).
- Expected columns: `date`, `rating`, `title`, `text` (exact column names may vary — handle gracefully).

### Tasks

- [ ] Implement `agent/tools/ingest_reviews.py`:
  - [ ] `load_reviews(csv_path: str) -> list[dict]` — read CSV with pandas, rename columns to canonical schema (`rating`, `title`, `text`, `date`).
  - [ ] `filter_by_date(reviews, weeks: int) -> list[dict]` — keep only reviews within the last N weeks.
  - [ ] `strip_pii(reviews) -> list[dict]` — remove any columns that may carry PII (reviewer name, device ID, reviewer language if not needed, etc.). Keep only `rating`, `title`, `text`, `date`.
  - [ ] `ingest_reviews(csv_path: str, weeks: int) -> list[dict]` — orchestrates the three steps above; returns clean, anonymous review list.
- [ ] Wrap `ingest_reviews` as a **LangChain tool** using `@tool` decorator.
- [ ] Write a sample test / smoke script (`data/sample_reviews.csv` with 20 synthetic rows) to verify the tool end-to-end.

### Output Schema (per review)
```python
{
  "rating": int,       # 1–5
  "title":  str,       # review title (may be empty)
  "text":   str,       # review body
  "date":   str        # ISO date string, e.g. "2026-06-15"
}
```

### Exit Criteria
- Given a real or synthetic CSV, `ingest_reviews()` returns a list of clean dicts.
- No PII fields present in output.
- Reviews outside the time window are excluded.

---

## Phase 2 — Thematic Engine (Clustering & Summarization)

**Goal:** Use an LLM (Groq via LangChain) to cluster reviews into ≤5 themes, rank by volume, select 3 verbatim quotes, and generate 3 action ideas.

### Tasks

- [ ] Write prompt template `agent/prompts/cluster_prompt.txt`:
  - Instructs the LLM to read the review list and cluster into **at most 5 themes**.
  - Specifies output format as structured JSON: `{themes, quotes, action_ideas}`.
  - Explicitly prohibits paraphrasing quotes — must be verbatim from the input.
  - Instructs ranking themes by review count (descending).
- [ ] Implement `agent/tools/thematic_engine.py`:
  - [ ] `build_llm()` — instantiate `ChatGroq(model="llama3-70b-8192", temperature=0)`.
  - [ ] `cluster_and_summarize(reviews: list[dict]) -> dict` — formats reviews into the prompt, calls the LLM, parses JSON response.
  - [ ] Output validation: assert `len(themes) <= 5`, `len(quotes) == 3`, `len(action_ideas) == 3`.
- [ ] Wrap `cluster_and_summarize` as a **LangChain tool**.
- [ ] Handle large review sets: if token budget exceeded, batch reviews and merge results.

### Output Schema
```python
{
  "themes": [
    {"name": str, "summary": str, "count": int},
    ...  # max 5 entries
  ],
  "quotes": [str, str, str],            # 3 verbatim quotes
  "action_ideas": [str, str, str]       # 3 concrete actions
}
```

### Exit Criteria
- Given 50 synthetic reviews, `cluster_and_summarize()` returns valid JSON matching the schema.
- Themes ≤ 5; top 3 are returned ranked by count.
- Quotes are exact substrings of the input review texts.
- Action ideas reference the identified themes.

---

## Phase 3 — Pulse Builder (Note Assembly)

**Goal:** Assemble the structured output from the Thematic Engine into a formatted, ≤250-word one-page weekly note ready to be written to Google Docs and emailed.

### Tasks

- [ ] Implement `agent/tools/pulse_builder.py`:
  - [ ] `build_pulse(themes: list, quotes: list[str], action_ideas: list[str], date_range: str) -> str`
  - Format the note exactly as defined in `architecture.md §3.3`:
    ```
    Weekly Play Store Review Pulse — [Date Range]
    ──────────────────────────────────────
    TOP THEMES
    1. [Theme]: [Summary]
    ...
    USER QUOTES
    • "[quote]"
    ...
    ACTION IDEAS
    1. [action]
    ...
    ```
  - [ ] Enforce ≤250-word limit: truncate summaries if needed, log a warning if over limit.
  - [ ] Return the formatted string.
- [ ] Wrap `build_pulse` as a **LangChain tool**.

### Exit Criteria
- Given valid input, `build_pulse()` returns a string ≤250 words.
- Output contains exactly 3 themes, 3 quotes, 3 action ideas.
- Date range is correctly interpolated.

---

## Phase 4 — MCP Integration (Google Docs & Gmail)

**Goal:** Configure and validate the MCP servers for Google Docs and Gmail, then expose them as LangChain tools via `langchain-mcp-adapters`.

### 4.1 MCP Server Setup

- [ ] Configure the **Google Docs MCP server** in `mcp_servers/google_docs_server/`:
  - Install and configure the MCP server (e.g., `@modelcontextprotocol/server-gdrive` or equivalent).
  - Verify it exposes `create_document` / `update_document` tools.
  - Document any auth/token setup in `mcp_servers/google_docs_server/README.md`.
- [ ] Configure the **Gmail MCP server** in `mcp_servers/gmail_server/`:
  - Install and configure the MCP server (e.g., `@modelcontextprotocol/server-gmail` or equivalent).
  - Verify it exposes a `create_draft` tool.
  - Document auth/token setup in `mcp_servers/gmail_server/README.md`.

### 4.2 LangChain Tool Wrappers

- [ ] Implement `agent/tools/docs_tool.py`:
  - [ ] Connect to the Google Docs MCP server using `langchain-mcp-adapters` (`MCPToolkit` or `MultiServerMCPClient`).
  - [ ] Expose `google_docs_create(title: str, content: str) -> str` — returns the Doc URL.
  - [ ] Wrap as a LangChain tool.
- [ ] Implement `agent/tools/gmail_tool.py`:
  - [ ] Connect to the Gmail MCP server via `langchain-mcp-adapters`.
  - [ ] Expose `gmail_create_draft(subject: str, body: str, doc_url: str, recipient: str) -> str` — returns draft ID or confirmation.
  - [ ] Wrap as a LangChain tool.

### 4.3 Integration Smoke Test

- [ ] Write a standalone smoke test that:
  1. Calls `google_docs_create` with dummy content → verifies a Doc URL is returned.
  2. Calls `gmail_create_draft` with dummy body → verifies a draft appears in Gmail.

### Exit Criteria
- Both MCP servers are running and reachable from Python.
- `google_docs_create()` creates a real Google Doc and returns its URL.
- `gmail_create_draft()` creates a real Gmail draft visible in the inbox.
- No direct Google REST API calls are made — all traffic goes through MCP.

---

## Phase 5 — LangChain Orchestrator (Agent Wiring)

**Goal:** Wire all tools into a single LangChain ReAct agent that executes the full pipeline end-to-end from a single prompt.

### Tasks

- [ ] Implement `agent/agent.py`:
  - [ ] Instantiate `ChatGroq` (Groq model, `temperature=0`).
  - [ ] Collect all tools: `[ingest_reviews, cluster_and_summarize, build_pulse, google_docs_create, gmail_create_draft]`.
  - [ ] Create the agent using `create_react_agent(llm, tools, prompt)` or `AgentExecutor`.
  - [ ] Write a system prompt that instructs the agent to:
    1. Call `ingest_reviews` with the configured CSV path and week window.
    2. Pass the reviews to `cluster_and_summarize`.
    3. Pass the result to `build_pulse` to generate the formatted note.
    4. Call `google_docs_create` with the note.
    5. Call `gmail_create_draft` with the note and Doc URL to `RECIPIENT_EMAIL`.
  - [ ] Add a `run_pipeline()` entry function that invokes the agent with a single trigger message.

- [ ] Create a `main.py` at the project root:
  ```python
  from agent.agent import run_pipeline
  if __name__ == "__main__":
      run_pipeline()
  ```

### Agent Execution Sequence
```
User trigger → Agent
  → Tool: ingest_reviews(csv_path, weeks=10)
      ↳ [cleaned review list]
  → Tool: cluster_and_summarize(reviews)
      ↳ {themes, quotes, action_ideas}
  → Tool: build_pulse(themes, quotes, action_ideas, date_range)
      ↳ formatted_note (str)
  → Tool: google_docs_create(title, content=formatted_note)
      ↳ doc_url
  → Tool: gmail_create_draft(subject, body=formatted_note, doc_url, recipient)
      ↳ draft_id / confirmation
```

### Exit Criteria
- `python main.py` runs without errors end-to-end.
- A Google Doc is created with the weekly pulse content.
- A Gmail draft is created addressed to `RECIPIENT_EMAIL`.
- The agent does not hallucinate extra tool calls or skip steps.

---

## Phase 6 — End-to-End Testing & Hardening

**Goal:** Validate the full pipeline with real data, enforce all constraints, and make the system production-ready.

### Tasks

#### 6.1 Constraint Validation
- [ ] Verify pulse word count ≤ 250 (add automated assertion).
- [ ] Verify themes ≤ 5 in clustering output (add automated assertion).
- [ ] Verify quotes are verbatim substrings of input review texts (add assertion in thematic engine).
- [ ] Verify no PII fields present in the review list passed to the LLM.

#### 6.2 Real Data Test
- [ ] Export a real Play Store CSV from Google Play Console.
- [ ] Run `python main.py` with real data.
- [ ] Manually review the generated Google Doc for quality, accuracy, and ≤250-word compliance.
- [ ] Manually verify the Gmail draft is correct and sendable.

#### 6.3 Edge Case Handling
- [ ] Empty CSV or CSV with 0 reviews in the time window → graceful error message, no crash.
- [ ] CSV with missing columns → clear error with column name guidance.
- [ ] LLM returns malformed JSON → retry with corrective prompt; fail gracefully after 2 retries.
- [ ] MCP server unreachable → informative error; do not silently skip delivery.

#### 6.4 Logging & Observability
- [ ] Add `logging` throughout the pipeline (INFO for each step, WARNING for constraint violations, ERROR for failures).
- [ ] Log: number of reviews ingested, date range, themes identified, word count of pulse, Doc URL, draft ID.

#### 6.5 Documentation
- [ ] Update `README.md` with:
  - Setup instructions (env vars, dependencies, MCP server config).
  - How to export Play Store reviews from Google Play Console.
  - How to run `python main.py`.
  - Expected outputs (Google Doc + Gmail draft).

### Exit Criteria
- All constraint assertions pass on real data.
- No crashes on edge case inputs.
- Logs provide a clear audit trail of each pipeline run.
- `README.md` is complete and sufficient for a new developer to set up and run the project.

---

## Phase 7 — Scheduler Component (Automation)

**Goal:** Automate the pipeline to run on a weekly schedule so that new reviews are fetched, clustered, and reports are generated and sent automatically.

### Tasks

- [ ] Implement a lightweight scheduler mechanism (e.g., using `cron`, GitHub Actions, or a Python scheduler like `schedule`/`APScheduler`).
- [ ] Configure the scheduler to run `main.py` automatically once a week (e.g., every Monday at 9:00 AM).
- [ ] Ensure the environment variables (`.env`) are securely accessible by the scheduler.
- [ ] Add logging or alerting for the scheduled job to notify if the automated run fails.

### Exit Criteria
- The pipeline executes successfully on the designated schedule without manual triggering.
- The Google Doc is appended and the Gmail draft is created automatically each week.

---

## Phase Summary

| Phase | Name | Key Deliverable | Dependencies |
|---|---|---|---|
| **0** | Setup | Project skeleton, `requirements.txt`, `.env` | None |
| **1** | Review Ingestor | `ingest_reviews` LangChain tool | Phase 0 |
| **2** | Thematic Engine | `cluster_and_summarize` LangChain tool | Phase 1 |
| **3** | Pulse Builder | `build_pulse` LangChain tool | Phase 2 |
| **4** | MCP Integration | Docs + Gmail LangChain tools via MCP | Phase 0 |
| **5** | Orchestrator | `agent.py` + `main.py` end-to-end agent | Phases 1–4 |
| **6** | Testing & Hardening | Validated pipeline, README | Phase 5 |
| **7** | Scheduler | Automated weekly cron/job | Phase 6 |

> [!NOTE]
> Phases 1–3 (data pipeline) and Phase 4 (MCP integration) can be developed in parallel once Phase 0 is complete, then joined in Phase 5.

---

## Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Play Store CSV column names differ from expected | Use flexible column mapping in `ingest_reviews`; log available columns on load |
| Groq token limit exceeded on large review sets | Batch reviews; summarize in chunks then merge |
| MCP server auth/setup is complex | Document setup step-by-step in `mcp_servers/*/README.md`; test in Phase 4 before wiring agent |
| LLM returns non-verbatim quotes | Add post-processing assertion; re-prompt if quotes not found in source texts |
| Gmail draft goes to wrong recipient | Read `RECIPIENT_EMAIL` from `.env`; log recipient at draft creation time |
