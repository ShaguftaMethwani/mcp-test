# Evaluation Plan

**Project:** Play Store Weekly Review Pulse
**Stack:** LangChain · Groq · MCP (Google Docs + Gmail) · Python
**Purpose:** Define how every component and the end-to-end pipeline is evaluated — covering unit tests, integration tests, LLM output quality, constraint compliance, and manual review gates.

---

## Table of Contents

1. [Evaluation Philosophy](#1-evaluation-philosophy)
2. [Evaluation Layers](#2-evaluation-layers)
3. [Phase 1 — Review Ingestor Evaluation](#3-phase-1--review-ingestor-evaluation)
4. [Phase 2 — Thematic Engine Evaluation](#4-phase-2--thematic-engine-evaluation)
5. [Phase 3 — Pulse Builder Evaluation](#5-phase-3--pulse-builder-evaluation)
6. [Phase 4 — MCP Integration Evaluation](#6-phase-4--mcp-integration-evaluation)
7. [Phase 5 — Orchestrator (Agent) Evaluation](#7-phase-5--orchestrator-agent-evaluation)
8. [End-to-End Pipeline Evaluation](#8-end-to-end-pipeline-evaluation)
9. [LLM Output Quality Rubric](#9-llm-output-quality-rubric)
10. [Constraint Compliance Checklist](#10-constraint-compliance-checklist)
11. [Regression Test Suite](#11-regression-test-suite)
12. [Evaluation Summary Table](#12-evaluation-summary-table)

---

## 1. Evaluation Philosophy

This project has two distinct evaluation dimensions:

| Dimension | What it tests | Method |
|---|---|---|
| **Functional correctness** | Does the code do what it's supposed to? | Automated unit + integration tests |
| **LLM output quality** | Is the AI-generated content accurate, grounded, and useful? | Rubric-based human + LLM-as-judge evaluation |

**Goal:** Use an LLM (Groq via LangChain) to cluster reviews into ≤5 themes, rank by volume, select 3 verbatim quotes, and generate 3 action ideas. Because the core value of this system lives in the **LLM-generated pulse** (themes, quotes, action ideas), functional tests alone are not enough. Both dimensions must pass for a run to be considered successful.

---

## 2. Evaluation Layers

```
Layer 1 — Unit Tests          (per tool, pure Python, no LLM/MCP calls)
Layer 2 — Integration Tests   (with real LLM or real MCP, one component at a time)
Layer 3 — End-to-End Tests    (full pipeline run with real data)
Layer 4 — Quality Evaluation  (human + LLM-as-judge rubric on generated pulse)
Layer 5 — Regression Suite    (curated fixed inputs → expected outputs, re-run on changes)
```

---

## 3. Phase 1 — Review Ingestor Evaluation

### 3.1 Unit Tests (`tests/test_ingest_reviews.py`)

| Test ID | Test Case | Input | Expected Output | Pass Condition |
|---|---|---|---|---|
| **U-IN-01** | Happy path — valid CSV | `sample_reviews.csv` (20 rows, all valid) | List of 20 clean dicts | All fields present: `rating`, `title`, `text`, `date` |
| **U-IN-02** | Date filter — keep within window | 30 rows: 20 in last 10 weeks, 10 older | List of 20 dicts | Only in-window reviews returned |
| **U-IN-03** | Date filter — all outside window | 30 rows all older than 10 weeks | Empty list `[]` | Return `[]`; no crash |
| **U-IN-04** | PII stripping — extra columns removed | CSV with extra columns: `reviewer_name`, `device_id` | Output has only `rating`, `title`, `text`, `date` | No extra keys in output dicts |
| **U-IN-05** | Empty `text` rows dropped | 20 rows, 5 have empty/whitespace `text` | List of 15 dicts | 5 rows excluded |
| **U-IN-06** | Duplicate rows deduplicated | 20 rows, 5 exact duplicates | List of 15 unique dicts | Dedup applied |
| **U-IN-07** | Missing `text` column | CSV without a `text` column | `KeyError` or mapped equivalent | Clear error with available columns logged |
| **U-IN-08** | CSV with only header, no data rows | Header only | `[]` with warning log | No crash; warning emitted |
| **U-IN-09** | Semicolon-delimited CSV | `;`-separated file | Same as U-IN-01 | Auto-detects delimiter |
| **U-IN-10** | Email address in review text | Review contains `"email me at foo@bar.com"` | Email replaced with `[email redacted]` | PII redacted before output |

### 3.2 How to Run
```bash
pytest tests/test_ingest_reviews.py -v
```

### 3.3 Test Fixtures Needed
- `tests/fixtures/valid_reviews.csv` — 20 rows, standard columns, all in window
- `tests/fixtures/mixed_dates.csv` — rows spanning 20 weeks
- `tests/fixtures/extra_columns.csv` — includes `reviewer_name`, `device_id`
- `tests/fixtures/empty_text.csv` — 5 rows with blank `text`
- `tests/fixtures/header_only.csv` — only header row

---

## 4. Phase 2 — Thematic Engine Evaluation

### 4.1 Unit Tests — Output Schema Validation (`tests/test_thematic_engine.py`)

These tests mock the LLM and validate the parsing and post-processing logic.

| Test ID | Test Case | Mocked LLM Output | Expected Behavior | Pass Condition |
|---|---|---|---|---|
| **U-TE-01** | Valid JSON output | Correct JSON with 3 themes, 3 quotes, 3 actions | Parsed dict returned | Schema matches exactly |
| **U-TE-02** | LLM returns 6 themes | JSON with 6 theme entries | Truncated to 5 | `len(themes) == 5` |
| **U-TE-03** | LLM returns malformed JSON (first attempt) | `"{ invalid json"` | Retry triggered | Second call made; valid response accepted |
| **U-TE-04** | LLM returns malformed JSON twice | Two malformed responses | Raises `RuntimeError` after 2 retries | Exception raised; no infinite loop |
| **U-TE-05** | LLM returns only 2 quotes | JSON with 2 quotes | Accepted; warning logged | `len(quotes) == 2`; no crash |
| **U-TE-06** | Empty reviews list passed in | `[]` | Short-circuit, no LLM call | Returns `{"themes": [], "quotes": [], "action_ideas": []}` |

### 4.2 Integration Tests — LLM Quality (requires real Groq API key)

| Test ID | Test Case | Input | Evaluation Criteria |
|---|---|---|---|
| **I-TE-01** | Standard clustering | 50 synthetic reviews across 3 clear topics | Themes match the 3 planted topics; count ordering is correct |
| **I-TE-02** | Verbatim quote check | 50 reviews with known text | All 3 returned quotes are exact substrings of input `text` fields |
| **I-TE-03** | Max theme constraint | 100 reviews across 7 topics | Output has ≤ 5 themes |
| **I-TE-04** | Action idea grounding | Reviews about a payment bug | At least 1 action idea references "payment" or related topic |
| **I-TE-05** | Ranking by volume | 30 reviews about "crashes", 10 about "UI" | "crashes" theme appears before "UI" theme in output |

### 4.3 How to Run
```bash
# Unit (mocked LLM)
pytest tests/test_thematic_engine.py -v -m "not integration"

# Integration (real LLM, requires GROQ_API_KEY)
pytest tests/test_thematic_engine.py -v -m "integration"
```

---

## 5. Phase 3 — Pulse Builder Evaluation

### 5.1 Unit Tests (`tests/test_pulse_builder.py`)

| Test ID | Test Case | Input | Expected Output | Pass Condition |
|---|---|---|---|---|
| **U-PB-01** | Happy path | 3 themes, 3 quotes, 3 actions, valid date range | Formatted string | All sections present; structure matches template |
| **U-PB-02** | Word count ≤ 250 | Standard valid input | Pulse string | `len(pulse.split()) <= 250` |
| **U-PB-03** | Word count enforcement — long summaries | Themes with 100-word summaries each | Truncated summaries | Output ≤ 250 words after truncation |
| **U-PB-04** | Empty themes (0 themes) | `themes=[]` | "No reviews found for this period" message | Does not crash; returns fallback message |
| **U-PB-05** | 1 theme, 1 quote, 1 action | Minimal valid input | Partial pulse | Output contains 1 of each; no crash |
| **U-PB-06** | Missing date range | `date_range=None` | Fallback: "Last N weeks" | `date_range` placeholder is not empty |
| **U-PB-07** | Unicode in quotes | Quote contains emoji 🚀 and accented chars | Renders correctly | No encoding error; UTF-8 output |
| **U-PB-08** | Section headers present | Standard input | Formatted string | Output contains "TOP THEMES", "USER QUOTES", "ACTION IDEAS" |

### 5.2 How to Run
```bash
pytest tests/test_pulse_builder.py -v
```

---

## 6. Phase 4 — MCP Integration Evaluation

### 6.1 Google Docs MCP — Integration Smoke Tests

> These require a live MCP server. Run against a dedicated test Google account.

| Test ID | Test Case | Action | Pass Condition |
|---|---|---|---|
| **I-MCP-01** | Server reachability | Connect to Google Docs MCP server | Connection succeeds; tool list returned |
| **I-MCP-02** | Document creation | Call `google_docs_create("Test Doc", "Hello World")` | Returns a valid `https://docs.google.com/...` URL |
| **I-MCP-03** | Document content accuracy | Create doc; open URL | Doc content matches the string passed in |
| **I-MCP-04** | No direct REST calls | Monitor outbound HTTP | No calls to `googleapis.com` from Python code directly |
| **I-MCP-05** | Empty content | Call with `content=""` | Doc created with empty body; no crash |

### 6.2 Gmail MCP — Integration Smoke Tests

| Test ID | Test Case | Action | Pass Condition |
|---|---|---|---|
| **I-MCP-06** | Server reachability | Connect to Gmail MCP server | Connection succeeds; tool list returned |
| **I-MCP-07** | Draft creation | Call `gmail_create_draft(subject, body, doc_url, recipient)` | Returns a draft ID or confirmation string |
| **I-MCP-08** | Draft visibility | Check Gmail Drafts folder | Draft appears with correct subject and recipient |
| **I-MCP-09** | Draft body accuracy | Open the Gmail draft | Body matches the pulse text passed in |
| **I-MCP-10** | Doc URL in body | Pass a real `doc_url` | Draft body contains the URL |
| **I-MCP-11** | Invalid recipient email | Pass `"not-an-email"` | Error is surfaced; does not silently succeed |

### 6.3 How to Run
```bash
# Requires MCP servers to be running and GOOGLE credentials in .env
pytest tests/test_mcp_integration.py -v -m "integration"
```

---

## 7. Phase 5 — Orchestrator (Agent) Evaluation

### 7.1 Agent Behavior Tests (`tests/test_agent.py`)

These tests use mocked tools to verify the agent's reasoning and sequencing.

| Test ID | Test Case | Setup | Expected Agent Behavior | Pass Condition |
|---|---|---|---|---|
| **U-AG-01** | All 5 tools called in order | Mock all tools to return valid data | Agent calls tools in sequence: ingest → cluster → build → docs → gmail | Tool call order matches expected sequence |
| **U-AG-02** | No tool skipped | Mock all tools | All 5 tools are called exactly once | `call_count == 1` for each tool |
| **U-AG-03** | Agent does not hallucinate output | Mock tools return valid data | Agent does not generate the pulse text directly — must call `build_pulse` | `build_pulse` tool was called |
| **U-AG-04** | `doc_url` passed to Gmail | Mock `google_docs_create` to return a fake URL | `gmail_create_draft` receives the same URL | URL propagated correctly |
| **U-AG-05** | Agent stops within `max_iterations` | Tools succeed normally | Agent completes in < 15 iterations | `iterations < max_iterations` |
| **U-AG-06** | Agent handles tool error gracefully | Mock one tool to raise an exception | Agent does not crash silently; error is surfaced | Exception message visible in output |

### 7.2 How to Run
```bash
pytest tests/test_agent.py -v -m "not integration"
```

---

## 8. End-to-End Pipeline Evaluation

### 8.1 Full Run Test (requires real API keys + MCP servers)

```bash
python main.py
```

| Check | Method | Pass Condition |
|---|---|---|
| Pipeline completes without error | Observe exit code | `exit code == 0` |
| Google Doc created | Check returned URL | URL opens a valid Google Doc |
| Doc content matches pulse | Open Doc manually | Content is the pulse text, properly formatted |
| Gmail draft created | Check Gmail Drafts | Draft exists with correct subject and recipient |
| Draft body is complete | Open Gmail draft | Body contains pulse text + Doc URL |
| All 5 tool calls logged | Check application logs | All 5 tool invocations appear in INFO logs |
| Word count ≤ 250 | Count words in Doc | `len(doc_content.split()) <= 250` |
| No PII in Doc | Read Doc content | No email addresses, device IDs, or reviewer names |
| No PII in Gmail draft | Read draft content | Same check as above |

### 8.2 End-to-End with Synthetic Data

Before testing with real Play Store data, run with a controlled synthetic dataset:

**Synthetic dataset spec** (`tests/fixtures/e2e_synthetic.csv`):
- 60 reviews
- 3 clear planted themes: `onboarding` (25 reviews), `payments` (20 reviews), `crashes` (15 reviews)
- Date range: last 8 weeks
- No PII in any field

**Expected e2e output:**
```
TOP THEMES
1. Onboarding: ... (count ~25)
2. Payments: ... (count ~20)
3. Crashes: ... (count ~15)

USER QUOTES
• [verbatim quote from an onboarding review]
• [verbatim quote from a payments review]
• [verbatim quote from a crashes review]

ACTION IDEAS
1. [action related to onboarding]
2. [action related to payments]
3. [action related to crashes]
```

**Assertions on synthetic run:**
- [ ] Theme 1 name contains "onboarding" or synonymous term
- [ ] Theme 2 name contains "payment" or synonymous term
- [ ] All quotes found verbatim in `e2e_synthetic.csv`
- [ ] Word count ≤ 250
- [ ] Google Doc created and URL returned
- [ ] Gmail draft created with correct recipient

---

## 9. LLM Output Quality Rubric

Use this rubric to evaluate the generated pulse in both synthetic and real-data runs. Score each dimension from **1–5**.

### 9.1 Rubric Dimensions

| Dimension | Score 1 (Poor) | Score 3 (Acceptable) | Score 5 (Excellent) |
|---|---|---|---|
| **Theme Relevance** | Themes are generic or unrelated to actual reviews | Themes broadly match review content | Themes precisely reflect the top concerns in the reviews |
| **Theme Distinctness** | Themes heavily overlap (e.g., "bugs" and "crashes" are both listed separately) | Some overlap but mostly distinct | All themes are clearly differentiated |
| **Quote Verbatim Accuracy** | Quotes are paraphrased or invented | Quotes are close to original but slightly altered | Quotes are exact substrings of input reviews |
| **Quote Representativeness** | Quotes all come from the same theme | Quotes cover 2 of 3 themes | Each quote comes from a different top theme |
| **Action Idea Grounding** | Actions are generic best practices unrelated to themes (e.g., "improve UX") | Actions broadly relate to themes | Each action directly addresses a specific identified theme |
| **Action Idea Specificity** | Actions are vague (e.g., "fix bugs") | Actions name the area but not the how | Actions are specific and actionable (e.g., "Add a retry button on failed payment screens") |
| **Scannability** | Note is dense, hard to skim | Note is mostly scannable | Note is instantly scannable with clear sections |
| **Word Count Compliance** | > 300 words | 251–300 words (over but close) | ≤ 250 words |

### 9.2 Scoring

| Total Score | Interpretation | Action |
|---|---|---|
| **34–40** | Excellent — ship it | No changes needed |
| **26–33** | Good — minor prompt tuning | Tweak prompt for weak dimensions |
| **18–25** | Acceptable — prompt needs work | Revisit `cluster_prompt.txt`; add few-shot examples |
| **< 18** | Poor — do not ship | Redesign thematic engine prompt; investigate LLM selection |

### 9.3 LLM-as-Judge (Automated Quality Check)

For automated quality evaluation, use a secondary LLM call after pulse generation:

**Prompt template:**
```
You are evaluating an AI-generated weekly app review pulse.

Source reviews (anonymized):
{reviews_sample}

Generated pulse:
{pulse_text}

Score each dimension from 1–5:
1. Theme Relevance (are themes grounded in the reviews?)
2. Quote Verbatim Accuracy (are quotes exact from the source?)
3. Action Idea Grounding (are actions tied to specific themes?)
4. Word Count Compliance (is the note ≤250 words?)

Return JSON: {"theme_relevance": int, "quote_accuracy": int, "action_grounding": int, "word_count_compliance": int, "overall": int, "notes": str}
```

**Acceptance threshold:** `overall >= 3` on every dimension for the run to be considered passing.

---

## 10. Constraint Compliance Checklist

Run these assertions programmatically after every pipeline execution:

```python
# In tests/test_constraints.py or agent/agent.py post-run

def assert_constraints(reviews_input, clustering_output, pulse_text):

    # Constraint 1: Max 5 themes
    assert len(clustering_output["themes"]) <= 5, \
        f"Too many themes: {len(clustering_output['themes'])}"

    # Constraint 2: Pulse ≤ 250 words
    word_count = len(pulse_text.split())
    assert word_count <= 250, \
        f"Pulse too long: {word_count} words (limit: 250)"

    # Constraint 3: Verbatim quotes
    input_texts = [r["text"] for r in reviews_input]
    for quote in clustering_output["quotes"]:
        assert any(quote in text for text in input_texts), \
            f"Non-verbatim quote detected: '{quote[:60]}...'"

    # Constraint 4: No PII in output
    pii_patterns = [r'\S+@\S+\.\S+', r'\b\d{10,}\b']  # email, phone
    import re
    for pattern in pii_patterns:
        assert not re.search(pattern, pulse_text), \
            f"Possible PII detected in pulse (pattern: {pattern})"

    # Constraint 5: Exactly 3 action ideas
    assert len(clustering_output["action_ideas"]) == 3, \
        f"Expected 3 action ideas, got {len(clustering_output['action_ideas'])}"

    print("✅ All constraints passed.")
```

---

## 11. Regression Test Suite

Maintain a fixed set of inputs with known expected properties. Re-run on every significant code or prompt change.

| Test ID | Input Fixture | What It Validates |
|---|---|---|
| **R-01** | `fixtures/valid_reviews.csv` (20 rows, 3 topics) | Core happy path; themes, quotes, pulse generated correctly |
| **R-02** | `fixtures/high_volume.csv` (500 rows, 5 topics) | Batching logic; theme count ≤ 5; no token overflow |
| **R-03** | `fixtures/single_review.csv` (1 row) | Edge case; system does not crash on minimal input |
| **R-04** | `fixtures/mixed_languages.csv` (English + non-English) | Multilingual handling; no crash |
| **R-05** | `fixtures/pii_heavy.csv` (emails, phone numbers in text) | PII redaction; no PII in pulse output |
| **R-06** | `fixtures/all_outside_window.csv` (all reviews > 12 weeks old) | Empty ingestor output handled gracefully |
| **R-07** | `fixtures/short_reviews.csv` (all reviews < 5 words) | Low-signal data; LLM still produces output without crash |

### Regression Run Command
```bash
pytest tests/test_regression.py -v --tb=short
```

---

## 12. Evaluation Summary Table

| Phase | Eval Type | Tool | Automated? | Gate |
|---|---|---|---|---|
| Phase 0 — Setup | Environment check | `pip install` + import smoke test | ✅ Yes | Must pass before Phase 1 |
| Phase 1 — Ingestor | Unit tests | `pytest test_ingest_reviews.py` | ✅ Yes | All 10 unit tests green |
| ✅ `GROQ_API_KEY` is set and valid | Thematic Engine | Unit + integration | `pytest test_thematic_engine.py` | ✅ / 🔶 Partial | Unit tests automated; integration needs API key |
| Phase 3 — Pulse Builder | Unit tests | `pytest test_pulse_builder.py` | ✅ Yes | All 8 unit tests green |
| Phase 4 — MCP | Integration smoke tests | `pytest test_mcp_integration.py` | 🔶 Manual setup | Both MCP smoke tests pass |
| Phase 5 — Orchestrator | Agent behavior tests | `pytest test_agent.py` | ✅ Yes (mocked) | All 6 agent tests green |
| E2E — Synthetic data | End-to-end + assertions | `python main.py` + `assert_constraints()` | 🔶 Semi-automated | All constraint assertions pass |
| E2E — Real data | Manual + LLM-as-judge | Human review + judge prompt | 🔶 Manual | Quality rubric score ≥ 3 on all dimensions |
| Regression | Full suite | `pytest test_regression.py` | ✅ Yes | All 7 regression fixtures pass |

> [!IMPORTANT]
> Every code change to `thematic_engine.py`, `cluster_prompt.txt`, or `pulse_builder.py` must be followed by a full regression run **and** a re-run of the LLM-as-judge quality check, since these directly affect output quality.

> [!TIP]
> Run `pytest tests/ -v --ignore=tests/test_mcp_integration.py` to execute all automated tests that do not require live MCP servers or API keys. Use this as your local pre-commit gate.
