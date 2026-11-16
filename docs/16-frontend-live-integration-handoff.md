# 16 — Evi frontend: implementation and live backend handoff

## Latest user decisions

- Product name: **Evi**. The project folder remains EvidenceGrid-Claude-Code-Handoff.
- Approved design: A, a light source-review workspace with navy/blue accents.
- Four main views: Workspace, Documents, Feedback, Benchmark.
- Public judge access without a sign-in wall.
- **No demo mode, synthetic financial results, or simulated provider success.**
- Codex builds the frontend; Claude Code will complete the backend, provider credentials, live end-to-end execution, and deployment.
- This file supersedes outdated statements that no frontend exists or that frontend work must wait for the backend. Earlier source-fidelity rules still apply.

## What is implemented

React + TypeScript + Vite application, with a local development API proxy and a PDF.js canvas viewer. The UI is English and uses the approved Evi identity. There is no account/login flow.

### Workspace

Source report selection, original PDF page navigation and zoom, source provenance dialog, metric/review/search filters, typed fact grid, immutable version selection, parent/revised field differences, check diagnostics, evidence tabs, CSV/JSON export, processing-job status and polling, real API actions for parsing/extraction.

Without a backend, original public source PDFs remain viewable but financial facts are empty. Process actions explain the unavailable connection rather than pretending to run.

### Documents

Two actual downloaded publisher PDFs with source URLs, source hashes, physical page counts, and source-page entry points. They are a local source catalog, not cached extraction results. Live server documents replace this catalog when available.

### Feedback

Reads live Reppo evaluation records from the backend, displays actual scores and critiques, and submits evaluation refreshes/revisions through server endpoints. No mock evaluation or placeholder numeric score is included.

### Benchmark

Displays measured benchmark artifacts with counts/denominators, split, label provenance, regressions, and export. Shows an empty state until a real artifact is returned. It never synthesizes an accuracy uplift.

### Identity assets

- `public/evi-symbol.svg`: grid/check symbol.
- `public/evi-logo.svg`: primary wordmark, vector paths rather than font-dependent text.
- `public/evi-logo-light.svg`: inverse mark for dark backgrounds.
- `public/favicon.svg`: symbol used by the app.

## Run locally

```powershell
cd C:\Evidence\EvidenceGrid-Claude-Code-Handoff
npm.cmd ci
npm.cmd run dev
```

Default development URL: `http://127.0.0.1:5173/`.

```powershell
npm.cmd run test
npm.cmd run build
npm.cmd run preview
```

Source files are in `src/`. Production static output is in `dist/`. The app currently has no Python service.

`.env.example` contains only a public API URL and local development proxy target. **Never put SERV_API_KEY or REPPO_API_KEY into VITE_ variables.** Vite variables are bundled into browser code. All provider secrets belong to the future server.

## API integration

Base path defaults to `/api/v1`. Vite forwards `/api` to `http://127.0.0.1:8000` in development. Override with `BACKEND_PROXY_TARGET`. A production reverse proxy must route the same API path to the actual Python service; Vite's development proxy does not exist in `dist/`.

Requests send `credentials: same-origin`, enabling an anonymous secure server cookie if the backend needs session ownership. No authentication UI is required for reviewers.

### Wire-format rule

List endpoints return `{ "items": [...] }`. Individual endpoints return the object directly. Long-running POSTs return a job object directly, with `job_id` and `status`. Errors use `{ "error": { "message": "..." } }` and a non-2xx HTTP status.

All successful responses must use `Content-Type: application/json`. An SPA HTML fallback is rejected as an unavailable service, not accepted as a successful API call. Responses are validated with Zod in `src/types.ts`; align the backend with those contracts or deliberately update the adapter and tests together.

### Readiness

```json
{
  "status": "ok",
  "live_execution_enabled": false
}
```

`GET /health` must not assert provider readiness merely because a process is running. Set `live_execution_enabled: true` only after server credentials, public-use limits, job execution, and permitted live routes are ready. The UI can read results with execution disabled.

### Endpoints the UI calls

| Endpoint | Expected response / purpose |
| --- | --- |
| `GET /health` | Readiness object above |
| `GET /documents` | `{items: Report[]}` |
| `GET /documents/{id}/source` | Original PDF bytes, not JSON; used for server-owned sources |
| `POST /documents/{id}/parse` | Job for a real Docling parse |
| `GET /runs?document_id={id}` | `{items: Run[]}`; `mode: live` |
| `POST /runs` | Job; input includes document_id, parse_id, policy_version, three requested metrics, mode: live |
| `GET /versions/{id}` | Immutable FactVersion object, including facts/checks/lineage |
| `GET /evidence/{id}` | Evidence object with source identity/text/page and optional actual bbox |
| `GET /jobs/{id}` | Job state/message/error |
| `GET /evaluations` | `{items: Evaluation[]}`; backend records use mode: reppo_live |
| `POST /versions/{id}/evaluations` | Job for a real Reppo submission |
| `POST /evaluations/{id}/refresh` | Job to poll the existing evaluation ID; no duplicate submission |
| `POST /versions/{id}/revisions` | Job; body names evaluation_id |
| `GET /benchmarks` | `{items: Benchmark[]}`; measured artifacts only |

The full intended domain API remains documented in file 10. This file fixes the exact subset currently consumed by the frontend.

### Report object

Required: `document_id`, `issuer_name`, `title`, `source_url`, `sha256`, `page_count`.

Recommended: `source_page` (physical 1-based statement page), `period_label` (catalog label only), `parse_status`, `parse_id`, `availability`.

Optional `source_path` points to an already served local PDF, such as the two shipped originals. Omit it for documents served through `/documents/{id}/source`. Ensure source identity cannot change without a new source version/hash.

The current process button requests a parse until `parse_status: parsed` and a valid `parse_id` are returned, then it requests extraction. Those are explicit separate stages. Do not invent a parse ID in the frontend.

### Run object

Required: `run_id`, `document_id`, `status`, `mode: live`, `created_at`, `version_ids: string[]` ordered from initial to latest child. Include empty `version_ids` while no output exists.

### FactVersion object

Required: `version_id`, `run_id`, `origin`, `facts`, `checks`. Optional `parent_version_id` links the previous immutable version. Supported origin labels are `serv_initial`, `serv_revision`, and `manual`; manual edits must stay separate from automated evaluation.

Facts use the canonical definitions in file 04 and the exact required fields in `src/types.ts`: fact/document IDs, metric, original metric label, scope, nullable string monetary values, currency/scale, reporting interval, evidence ID groups, and origin. Keep Decimal money as strings. Do not convert money to JavaScript floating point before transmitting it.

Checks name `check_id`, `fact_id`, `check_type`, `status`, `message`, and `evidence_ids`. A fact without completed checks is unchecked. A missing value or context is not a passed check.

### Evidence object

Required: `evidence_id`, `document_id`, `document_sha256`, `text`, `page_number`.

For source highlighting, include original `bbox` and `page_width`, `page_height`. `bbox` contains left/top/right/bottom plus `origin: TOPLEFT` or `BOTTOMLEFT`. Coordinate meaning must follow the source PDF/Docling adapter. Do not include fabricated rectangles. Missing rectangles result in text-only evidence.

The frontend refuses to highlight an anchor whose document ID or hash does not match the selected source. An incomplete/unreadable source remains unknown.

### Evaluation object

Required: `evaluation_id` (local stable ID), `version_id`, `mode: reppo_live`, `status`, `created_at`. Optional `eval_id` stores the real external Reppo ID. `result` is null while pending, otherwise contains `verdict: {score, decision, confidence}` and `verdicts: [{criterion, score, critique}]`.

Map provider status faithfully. The revision route must independently enforce settled status, exact parent version, real evaluation mode, budget, and source-backed constraints. The browser is not the enforcement boundary.

### Benchmark object

Required: `benchmark_id`, `split`, `created_at`, `document_count`, `label_provenance`, `baseline: {correct, total}`, `revised: {correct, total}`, and `regressions`.

The UI validates positive denominators and correct <= total. Follow file 08 for actual freeze, scoring, leakage prevention, coverage, period/unit details, and scientific limitations. The present result component does not replace that scorer.

### Job object

Required: `job_id`, `status`; optional `message`, nullable `error: {message}`. UI polls every four seconds while this process is open. Terminal states: succeeded, failed, cancelled, blocked, outcome_unknown. Jobs and upstream evaluation IDs must be durable on the server. Closing the tab must not lose them.

## Anonymous judge access

The frontend opens directly into Workspace. There is no login/signup gate or request for a reviewer API key. A published static build alone will let reviewers inspect the public PDF files, but **live processing requires the deployed backend**.

Claude Code should implement anonymous session ownership, allowlisted public corpus operations, server-side limits, bounded concurrency, capped provider calls per run/day, and durable jobs. Apply controls to write/compute routes, not a login wall in front of the whole application. Never expose an unbounded public proxy to a funded provider account.

Use deployment-level protections and a modest global public budget where appropriate. Do not silently share one reviewer's mutable edits with every other visitor. Existing immutable public results may be inspectable by all; new jobs should have explicit ownership and permitted visibility.

The user has not asked Codex to configure keys, build the backend, publish a repository, or deploy this frontend publicly. Those tasks remain for the next implementation stage.

## What is deliberately absent

- No live Docling service, SERV key, Reppo key, or provider calls.
- No fabricated financial figures, fake benchmark, fake evaluation trace, or simulated run.
- No app authentication or login screen.
- No general file upload, arbitrary remote fetch, extra financial metrics, or restatement propagation.
- No assumption that a local dev URL is reachable by judges elsewhere.

## Integration acceptance checks for Claude Code

1. Start the real API and return readiness; the UI must show connected state.
2. Parse an actual registered source and return its real parse_id.
3. Execute SERV extraction, store the immutable output, and expose its version_ids.
4. Confirm selecting a fact fetches source-matching evidence and real bounding boxes.
5. Submit/read an actual Reppo evaluation; show pending and settled states separately.
6. Execute a source-backed revision and expose its parent/version diff.
7. Run the independent frozen-label benchmark; return measured counts only.
8. Export a version and verify original unit, interval, missing fields, and provenance survive.
9. Deploy frontend + backend without a reviewer login wall; test from an unrelated browser/network.
10. Confirm public compute limits and server-side secret handling are effective.
