# Decisions

Dated entries; newest last. Each records a deviation or an architecture choice and its reason.

## 2026-11-15 — Backend foundation

- **Stack:** Python 3.12, FastAPI, Pydantic v2, SQLite (WAL) in `data/runs/evi.sqlite3`, filesystem artifacts in `data/runs/artifacts/`, and a separate worker process (`python -m evi.worker`). No pre-existing backend existed.
- **Durable jobs:** jobs are rows with leases. An expired lease (crashed worker) makes the job runnable again with `attempts+1`. Retryable provider errors back off exponentially up to `EVI_JOB_MAX_ATTEMPTS`. Terminal states: `succeeded`, `failed`, `cancelled`, `blocked`, `outcome_unknown`.
- **One user action, real stages:** `POST /documents/{id}/parse` creates a `process_document` job. It runs the Docling parse (or reuses a cached parse with identical source hash + parser version + config + page coverage), then enqueues `extract_facts` for a new run. `GET /jobs/{id}` follows that continuation and reports the current real stage (`stage`, `stages[]`). The frontend no longer calls `POST /runs` itself; the route remains for explicit re-extraction with a valid parse_id.
- **Health flags:** `processing_enabled` = worker heartbeat within 30 s AND a SERV key is configured. `live_execution_enabled` additionally requires a Reppo key. The frontend gates Process on the first flag and the feedback actions on the second. Neither flag is set just because the HTTP process is running.

## 2026-11-15 — Page-limited Docling parse

Each registered source parses only its consolidated income statement page (Verizon FY2025: physical page 52; FY2024: physical page 54). Checked with pypdf before parsing: each page has the statement title, `(dollars in millions, except per share amounts)`, `Years Ended December 31`, and the year column headers. Every parse records its coverage note ("Statement-page parse of physical pages [...] out of N; not full-document coverage").

## 2026-11-15 — Reppo API changed since docs/07

`https://eval.reppo.xyz/agents.md` (read 2026-11-15) now documents `POST /api/v1/agents/evals` with `{taskType, input ≤ 50 KB}` and `GET /api/v1/agents/evals/{id}`, with statuses `QUEUED | PROCESSING | COMPLETED | FAILED`. The earlier `eval-requests` and `lite` endpoints now return 404. There is no `criteria` or `settlementMinutes` field. Evi puts the four criteria and the review context inside the `input` document. The adapter uses `taskType: "response"`. Local states: `created → submitting → pending → completed | failed`, plus `submission_unknown`. A crash or timeout during submission becomes `submission_unknown` and is never resubmitted automatically. No x402/wallet path is implemented.

## 2026-11-15 — SERV transport

`POST https://inference-api.openserv.ai/v1/chat/completions` with a system message and `response_format: {type: json_schema, strict: true}`, per docs.openserv.ai (read 2026-11-15). The default model is `gpt-5.4-mini`, the model used in the official structured-output example. It is configurable with `SERV_MODEL`. Output is validated again with Pydantic. Truncation (`finish_reason=length`), filtering, malformed JSON and schema failures are separate failure states. The raw response is kept.

## 2026-11-15 — Revision acceptance rule

A proposed change is accepted only if (a) it cites at least one supporting evidence ID, (b) every cited ID exists in the parse, (c) the changed fact has no failing deterministic check, and (d) it does not have fewer passing checks than the parent fact. Otherwise the parent fact is kept and the rejection is recorded in `change_decisions`. A child version is always stored, even when nothing changed.

## 2026-11-15 — Anonymous ownership

The server sets an HttpOnly, SameSite=Strict `evi_session` cookie. Jobs are readable only by the session that created them. Versions, evidence, runs and evaluations are public, immutable artifacts. Writes must be JSON, at most 4 KB, and come from an allowed Origin. There is no CORS, so cross-site browser writes are blocked. Budgets: a per-session hourly job count, a global daily SERV call count and a global daily Reppo evaluation count, kept in `budget_ledger`; plus per-run limits on evaluations and revisions.

## 2026-11-16 — Technical-depth extension

- **Corpus expanded to 5 USD reports** from issuer hosts: Verizon 3Q25 Financial Statements, AT&T 3Q25 and 2Q25 Financial and Operational Schedules (alongside the two Verizon 10-Ks). Split by issuer: Verizon = development, AT&T = holdout. The builder read all pages (disclosed in each manifest).
- **Targets-v1:** column identity = (interval months, fiscal-year column); annual = current + prior year, interim = current + prior year of the quarter and of the YTD group. 48 targets in total.
- **Owners of the parent** = the "Net income attributable to <parent>" line, before preferred dividends. "Attributable to common stock" is a different scope.
- **Start dates are application-derived** (R-CAL-MONTHEND), like normalization; the model is not required to emit them (binding-v2). Week-based calendars are unresolved.
- **AT&T schedules print no end date**: end and start dates stay null (P3 `end_date_not_stated`); this is a supported fact with an unknown exact interval.
- **binding-v3**: section scope reaches a Docling `row_section` heading directly above the first data row. This fixed 4 false alarms observed in exp-2026-11-16-a.
- **revision-v3**: diagnostics carry the resolver's source-derived reading (never reference labels).
- **Certificates are policy-versioned**; verification replays the recorded policy (v1/v2/v3 are kept executable).
- **Reppo**: `taskType=response`; the four criteria travel inside `input`; missing scores stay null; rubric scale 0–100.
- **Arm D reuse in exp-b**: the same completed real evaluation of the same parent version is reused under a new revision policy. This is legitimate because the evaluation judges the parent, not the revision policy. No new credits were spent.

## 2026-11-16 — Proof-integrity repair

- Experiment replay must use the manifest's binding policy and derived coverage; a historical policy never substitutes (replay-v2). Replay is read-only and never rewrites expected artifacts.
- scoring-v1 results stay as the frozen record. Corrected, non-circular metrics are published as analysis-v2 next to them; neither replaces the other.
- A dollar sign is not normalized to USD in scoring (frozen field definition); a sensitivity count is reported, not adopted.
- "Supported" alone is no longer shown when exact dates are not printed; coverage-v1 labels partial context.
- Reppo packets v1 contain only self-cited evidence. Any change (reppo-packet-v2) needs a new pre-declared experiment and budget approval.

## 2026-11-16 — Validation and release preparation

- Server execution is **off by default** (`EVI_EXECUTION_ENABLED`); provider adapters refuse independently of the API. Local development sets it explicitly.
- Experiment runs need an approval file bound to the manifest hash, with explicit caps, plus `EVI_ALLOW_PAID_RUNS=1`. Configured keys are not approval.
- Reference review imports create `references-r1-<sheet hash>` files; v1 is immutable; reviewer identity is self-declared and labelled as such; agent or builder reviews are labelled not independent.
- New sources and targets after a freeze are DATA (`EVI_SOURCE_REGISTRY`, `EVI_TARGET_REGISTRY`), so registration does not change frozen code; historical targets cannot be redefined.
- Holdout `holdout-2026-11-16-a` predeclares reppo-packet-v2 for arm D; the runner selects the packet from the manifest (v1 remains the historical default).
- Deployment: a single host, SQLite WAL on a local volume, API + worker sharing it, Caddy in front; the API serves the SPA same-origin. No database migration.

- 2026-11-16 Spending allowance: the owner-approved allowance (host variables `EVI_ALLOWANCE_*`) is the authority for every paid SERV request and Reppo submission, checked and reserved per request in one SQLite write transaction before sending. No allowance → no paid work. The owner removed the 7-day end date because judging lasts longer; the cumulative limits stay at the totals of the original approval (21 SERV, 7 Reppo), so the allowance was not expanded. SERV read timeouts are now unknown outcomes (counted, not retried), the same as Reppo submissions.
