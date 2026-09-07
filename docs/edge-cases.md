# Edge Cases & Corner Scenarios

**Project:** Play Store Weekly Review Pulse
**Purpose:** Catalogue every known corner case across each pipeline layer, with the expected behavior and recommended handling strategy. Use this document alongside `implementation-plan.md` during development and testing.

---

## Table of Contents

1. [Review Ingestor (Data Layer)](#1-review-ingestor-data-layer)
2. [Thematic Engine (Clustering & Summarization)](#2-thematic-engine-clustering--summarization)
3. [Pulse Builder (Note Assembly)](#3-pulse-builder-note-assembly)
4. [MCP Integration — Google Docs](#4-mcp-integration--google-docs)
5. [MCP Integration — Gmail](#5-mcp-integration--gmail)
6. [LangChain Orchestrator (Agent)](#6-langchain-orchestrator-agent)
7. [End-to-End / Cross-Layer Scenarios](#7-end-to-end--cross-layer-scenarios)
8. [Privacy & Compliance](#8-privacy--compliance)

---

## 1. Review Ingestor (Data Layer)

### 1.1 CSV File Issues

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **I-01** | CSV file does not exist at `PLAY_STORE_CSV_PATH` | Fail fast with a clear `FileNotFoundError` | Validate path at startup; print actionable message with expected path |
| **I-02** | CSV file is empty (0 bytes) | Raise a descriptive error: "CSV file is empty" | Check file size before parsing |
| **I-03** | CSV file has header row but zero data rows | Return empty list; log warning "No reviews found in CSV" | Check `len(df) == 0` after load and warn |
| **I-04** | CSV file is malformed / not valid CSV (corrupt encoding) | Catch `ParserError`; log error with filename | Wrap `pd.read_csv` in try/except; suggest re-exporting from Play Console |
| **I-05** | CSV uses a different delimiter (e.g., semicolon `;`) | Attempt common delimiters as fallback | Try `sep=','`, then `sep=';'`, then `sep='\t'` |
| **I-06** | CSV has unexpected or renamed columns | Log available column names; raise `KeyError` with helpful message | Map known column aliases (e.g., `"Review Text"` → `text`, `"Star Rating"` → `rating`) |
| **I-07** | CSV is very large (10,000+ reviews) | Still works, but may be slow or hit LLM token limits | Warn if row count > 2,000; downstream batching handles token limits |

### 1.2 Date & Time Window Issues

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **I-08** | `date` column is missing or all null | Raise error: "Date column missing or empty — cannot filter by time window" | Validate date column before filtering |
| **I-09** | `date` column has mixed formats (e.g., `2026-01-15` and `Jan 15, 2026`) | Parse using `pd.to_datetime(..., infer_datetime_format=True)` | Use flexible date parser; log rows that fail to parse as dates |
| **I-10** | All reviews are older than the `WEEKS_LOOKBACK` window | Return empty list with clear warning: "0 reviews in the last N weeks" | Check count after date filter; pipeline should exit gracefully, not crash |
| **I-11** | `WEEKS_LOOKBACK` is set to 0 or negative | Raise `ValueError`: "WEEKS_LOOKBACK must be a positive integer" | Validate config at startup |
| **I-12** | Reviews are in a timezone other than UTC | Normalize all timestamps to UTC before comparison | Strip or convert timezone info using `pd.to_datetime(..., utc=True)` |

### 1.3 Data Quality Issues

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **I-13** | `text` field is null or empty for some reviews | Exclude those rows from processing; log count of skipped rows | Filter `df.dropna(subset=['text'])` before returning |
| **I-14** | `rating` field contains non-numeric values | Coerce to numeric; rows that fail become `NaN` and are dropped | Use `pd.to_numeric(..., errors='coerce')` |
| **I-15** | Duplicate reviews (same text, date, rating) | Deduplicate silently; log count of duplicates removed | `df.drop_duplicates(subset=['text', 'date'])` |
| **I-16** | Reviews in non-English languages | Pass through as-is; LLM handles multilingual input | Do not filter by language; note in logs if detected |
| **I-17** | `text` field contains only whitespace or punctuation | Exclude as empty text | Strip and check `len(text.strip()) == 0` |

---

## 2. Thematic Engine (Clustering & Summarization)

### 2.1 LLM Input Issues

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **T-01** | Review list is empty (downstream of I-10 or I-13) | Short-circuit: skip LLM call; return a "no reviews" signal to Pulse Builder | Check `len(reviews) == 0` before calling LLM; return structured empty result |
| **T-02** | Single review in the list | Still cluster and return; may produce only 1 theme | Handle gracefully; 1-theme result is valid output |
| **T-03** | Review texts are very short (e.g., "Good", "Bad") | LLM may produce low-quality themes | Proceed; log a warning about low-signal data |
| **T-04** | Review texts are extremely long (wall of text) | May exceed context window | Truncate each review to a max character limit (e.g., 500 chars) before passing to LLM |
| **T-05** | Total token count of all reviews exceeds LLM context window | Some reviews are dropped silently | Batch reviews into chunks; merge chunk-level themes using a secondary LLM call |

### 2.2 LLM Output Issues

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **T-06** | LLM returns malformed JSON (not parseable) | Retry once with a corrective prompt; fail after 2 retries | Wrap JSON parse in try/except; re-prompt with "Your response must be valid JSON matching this schema: ..." |
| **T-07** | LLM returns > 5 themes | Truncate to top 5 by count | Post-process: sort by `count` descending, slice `[:5]` |
| **T-08** | LLM returns < 3 themes (e.g., only 2 themes found) | Accept; Pulse Builder uses however many themes exist | Do not force 3 themes; handle 1–5 range in Pulse Builder |
| **T-09** | LLM returns fewer than 3 quotes | Pad with an empty string or re-prompt for more quotes | Re-prompt once; if still < 3, use what's available and log a warning |
| **T-10** | LLM invents a quote not present in the input reviews | Constraint violation — verbatim-only rule broken | Post-validate: check each quote is a substring of at least one input `text` field; discard and re-prompt if not |
| **T-11** | LLM paraphrases a quote (not verbatim) | Same as T-10 — invalid | Same substring check; flag with a warning |
| **T-12** | Action ideas reference themes not in the clustered output | Inconsistency; may confuse readers | Log a warning; accept as-is in v1, add cross-reference validation in hardening phase |
| **T-13** | LLM call fails with API error (rate limit, timeout) | Retry with exponential backoff (up to 3 attempts) | Use LangChain's built-in retry or wrap in `tenacity` |
| **T-14** | Groq API key is missing or invalid | Fail immediately with clear error: "GROQ_API_KEY not set or invalid" | Validate API key at startup before any LLM call |

---

## 3. Pulse Builder (Note Assembly)

### 3.1 Input Issues

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **P-01** | `themes` list is empty (no themes returned from T-01) | Return a "No data" pulse: "No Play Store reviews found for this period." | Handle `len(themes) == 0` explicitly; do not attempt normal formatting |
| **P-02** | `themes` has only 1 or 2 entries (< 3) | Format with however many themes are available (1 or 2) | Do not pad with empty themes; the format should be flexible |
| **P-03** | `quotes` list has fewer than 3 entries | Format with available quotes | Same as P-02 — use what exists |
| **P-04** | `action_ideas` list has fewer than 3 entries | Format with available action ideas | Same approach |
| **P-05** | A quote contains special formatting characters (e.g., `"`, `\n`, `—`) | Render cleanly in the note | Sanitize quotes: strip leading/trailing whitespace, normalize smart quotes |

### 3.2 Output Constraint Issues

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **P-06** | Assembled note exceeds 250 words | Truncate theme summaries to fit; log warning | Trim theme summaries first (they're most verbose); check word count after each section |
| **P-07** | `date_range` is `None` or empty string | Use a fallback: "Last N weeks" | Default to `f"Last {WEEKS_LOOKBACK} weeks"` if `date_range` is not computable |
| **P-08** | Unicode characters in theme names or quotes (e.g., emoji, CJK) | Render correctly | Ensure output is UTF-8 encoded end-to-end |

---

## 4. MCP Integration — Google Docs

### 4.1 Server Availability

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **D-01** | Google Docs MCP server is not running | Clear error: "Google Docs MCP server unreachable" | Catch connection error at tool call time; do not silently skip; abort pipeline |
| **D-02** | MCP server starts but returns an unexpected tool schema | Tool calls may fail or behave unexpectedly | Validate expected tool names (`create_document`, `update_document`) at startup |
| **D-03** | MCP server connection drops mid-call | Retry once; fail gracefully if retry also fails | Wrap MCP tool calls in retry logic |

### 4.2 Document Creation Issues

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **D-04** | Google account does not have write permission to create Docs | Fail with auth error; log clearly | Surface the MCP server's auth error message verbatim; link to setup docs |
| **D-05** | Doc title is empty or `None` | Use a default title: `"Weekly Play Store Pulse — [date]"` | Validate title in `docs_tool.py` before calling MCP |
| **D-06** | Doc content is empty (empty pulse — from P-01) | Still create the doc with the "No data" message | Do not skip doc creation; always deliver a document |
| **D-07** | Doc is created but URL is not returned by MCP tool | Log error; continue to Gmail with a placeholder | Check for URL in response; if missing, use `"(Doc URL unavailable)"` in Gmail body |
| **D-08** | Duplicate doc created on re-run (same title, same week) | Creates a second doc; this is acceptable in v1 | Note: deduplication / overwrite logic is a future enhancement |
| **D-09** | Doc content contains characters that break MCP serialization | MCP call fails | Sanitize content: strip null bytes; ensure UTF-8 |

---

## 5. MCP Integration — Gmail

### 5.1 Server Availability

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **G-01** | Gmail MCP server is not running | Clear error: "Gmail MCP server unreachable" | Same as D-01 — abort pipeline; do not silently skip |
| **G-02** | Gmail MCP server auth token expired | Fail with auth error; surface message clearly | Catch and log; instruct user to re-authenticate the MCP server |

### 5.2 Draft Creation Issues

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **G-03** | `RECIPIENT_EMAIL` is not set in `.env` | Fail fast at startup: "`RECIPIENT_EMAIL` is required" | Validate all required env vars at startup |
| **G-04** | `RECIPIENT_EMAIL` is not a valid email address format | Log a warning; attempt to create draft anyway (MCP may validate it) | Add basic regex validation in `gmail_tool.py` |
| **G-05** | Draft is created but body is truncated by MCP server | Draft appears incomplete in Gmail | Check if MCP server has a body length limit; truncate proactively if needed |
| **G-06** | `doc_url` is `None` or unavailable (from D-07) | Include a note in email body: "Note: Google Doc could not be created this run" | Handle `doc_url=None` in `gmail_tool.py` |
| **G-07** | Gmail draft is created but is not visible in inbox | Likely a Gmail label/folder issue | Log the draft ID returned by MCP; advise user to check "Drafts" folder |
| **G-08** | Draft creation succeeds but MCP returns no draft ID | Log warning: "Draft created but no ID returned" | Accept as success; log whatever response was received |

---

## 6. LangChain Orchestrator (Agent)

### 6.1 Agent Reasoning Issues

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **A-01** | Agent calls tools out of order (e.g., calls `build_pulse` before `cluster_and_summarize`) | Incorrect output or runtime error | Add strict sequential instructions in the system prompt; use `AgentExecutor` with step-by-step chain if needed |
| **A-02** | Agent skips a tool entirely (e.g., skips `google_docs_create`) | Pulse is not delivered to Docs | Add a post-execution check: verify all 5 tool calls were made; re-prompt if any were skipped |
| **A-03** | Agent calls a tool more than once (e.g., calls `ingest_reviews` twice) | Duplicate processing; waste of API calls | Detect repeated tool calls in execution log; warn and de-duplicate |
| **A-04** | Agent hallucinates a tool name that doesn't exist | LangChain raises `ToolNotFound` error | Catch `ToolNotFound`; log and abort |
| **A-05** | Agent enters an infinite loop (keeps calling tools without finishing) | Pipeline never completes | Set `max_iterations` on `AgentExecutor` (e.g., 15); fail with clear message if exceeded |
| **A-06** | Agent tries to pass the full raw review list (1000s of items) directly in a prompt string | Token overflow | The `ingest_reviews` tool should return a reference/summary, not raw text; intermediate results stored in agent state |
| **A-07** | LLM decides to generate the pulse content itself instead of calling `cluster_and_summarize` | Fabricated content, not grounded in real reviews | System prompt must explicitly forbid generating content directly; require tool calls for every step |

### 6.2 Configuration Issues

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **A-08** | `GROQ_API_KEY` is missing | Fail immediately at agent init: "GROQ_API_KEY not set" | Validate all required env vars in `config/settings.py` at import time |
| **A-09** | Groq model name in config is deprecated or unavailable | LangChain raises a model not found error | Use a well-known stable model ID (e.g., `llama3-70b-8192`); add a config validation note |
| **A-10** | `PLAY_STORE_CSV_PATH` points to a directory instead of a file | `pd.read_csv` raises `IsADirectoryError` | Check `os.path.isfile()` before passing to ingestor |

---

## 7. End-to-End / Cross-Layer Scenarios

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **E-01** | All reviews in the CSV have the same 1-star rating | Still valid — 1-star data is real signal | No special handling; LLM will find themes from the text regardless of rating |
| **E-02** | All reviews are 5-star with no critical feedback | Pulse reflects positive signal | Acceptable; action ideas should still be forward-looking improvements, not fabricated problems |
| **E-03** | Pipeline is run twice in the same week | Creates a second Google Doc and second Gmail draft | Acceptable in v1; warn user; deduplification is a future enhancement |
| **E-04** | Network drops midway through the pipeline (after ingest, before MCP) | MCP tool call fails | Each tool call wrapped in retry; if retry fails, abort and log progress clearly so user knows which step failed |
| **E-05** | The pulse note text itself contains a URL (e.g., a user pastes a link in their review) | May appear in a verbatim quote | Accept; do not strip URLs from quotes as that alters verbatim content |
| **E-06** | `WEEKS_LOOKBACK` is set to a very large value (e.g., 52 weeks) | Large review set; may hit token limits | Warn if review count > 2,000; downstream batching handles overflow |
| **E-07** | No internet connection | All MCP calls and LLM calls fail | Fail fast with `ConnectionError`; log which service failed first |
| **E-08** | Pipeline is interrupted (Ctrl+C) mid-run | Leaves a partial state (e.g., Doc created, no draft) | Log the last completed step; in future, add idempotency / resume capability |
| **E-09** | `main.py` is run without `python-dotenv` loading `.env` (env vars not set) | Multiple `KeyError` or `None` failures | Call `load_dotenv()` at the very top of `main.py`; validate required vars immediately after |

---

## 8. Privacy & Compliance

| ID | Scenario | Expected Behavior | Handling Strategy |
|---|---|---|---|
| **PR-01** | CSV contains a column with reviewer display names | Must be stripped before data is passed to LLM | Drop any column matching known PII patterns: `reviewer_name`, `author`, `display_name`, `username` |
| **PR-02** | Review `text` embeds a user's email address (e.g., "contact me at john@example.com") | Email appears in LLM input; may appear in a quote | Add a PII redaction pass on `text` field: replace email addresses with `[email redacted]` using regex |
| **PR-03** | Review `text` contains a phone number | Same risk as PR-02 | Extend PII redaction to cover common phone number patterns |
| **PR-04** | CSV export includes a reviewer `user_id` or `device_id` column | Must not be passed to LLM or included in any output | Strip all columns except `rating`, `title`, `text`, `date` after load |
| **PR-05** | A verbatim quote uniquely identifies a user (e.g., mentions their own name) | Quote should be excluded or redacted | After quote selection, run the same PII regex on the 3 chosen quotes; replace or skip if PII is detected |
| **PR-06** | Raw review list is inadvertently logged at DEBUG level | PII exposure via logs | Ensure `logging.debug` calls never log full review objects; log counts and IDs only |
| **PR-07** | Google Doc is shared publicly by accident | Pulse (with stripped-PII quotes) is visible to anyone with the link | The MCP server controls sharing; default to "restricted" access; document this in setup README |

---

## Summary: Recommended Validation Checklist

Use this as a pre-deployment gate:

| Check | Tool / Layer |
|---|---|
| ✅ CSV path exists and is a valid file | Ingestor |
| ✅ CSV has required columns (with alias mapping) | Ingestor |
| ✅ At least 1 review exists after date filtering | Ingestor |
| ✅ No PII columns in output of ingestor | Ingestor |
| ✅ Email addresses / phone numbers redacted from text | Ingestor |
| ✅ `GROQ_API_KEY` is set and valid | Thematic Engine |
| ✅ LLM returns valid JSON on first or second attempt | Thematic Engine |
| ✅ Themes ≤ 5 | Thematic Engine |
| ✅ All 3 quotes are verbatim substrings of input texts | Thematic Engine |
| ✅ Pulse word count ≤ 250 | Pulse Builder |
| ✅ Both MCP servers are reachable before agent starts | MCP Layer |
| ✅ `RECIPIENT_EMAIL` is set and valid | Gmail Tool |
| ✅ Google Doc URL is captured and included in draft | Orchestrator |
| ✅ All 5 tool calls were made (no skipped steps) | Orchestrator |
| ✅ Agent completes within `max_iterations` | Orchestrator |
