# Evi — source-backed financial review

Evi helps analysts keep the reporting period and monetary unit attached to every financial figure. This folder contains the implemented English frontend and the specifications Claude Code needs to complete the live backend.

## Run the website

Use Node.js 22.12+ and npm. From this folder:

```powershell
npm ci
npm run dev
```

Open the local URL printed by Vite (normally http://127.0.0.1:5173). No login is required. For verification and a production build:

```powershell
npm test
npm run build
npm run preview
```

The development server proxies `/api` to `http://127.0.0.1:8000`. Configure a different backend using `.env.example`. Production hosting must serve the API and the frontend routes appropriately; no public deployment is included.

## What works now

- Public Home landing, responsive Workspace, Real data, Documents, Feedback, and Benchmark views, with top navigation.
- Two original Verizon USD reports with page navigation, zoom, provenance, publisher links, and SHA-256 references. Earlier Indonesian PDFs remain archived.
- Typed API adapters for processing jobs, extracted facts, immutable versions, evidence regions, Reppo feedback, revisions, and benchmarks.
- Evidence review, period/unit diagnostics, version differences, source validation, and CSV/JSON export when the backend supplies real results.
- Original Evi SVG logo, symbol, favicon, and light logo variant.

There is **no demo mode or fabricated financial output**. Until the processing backend is connected, sources remain readable and the result grid stays empty. Clicking processing actions explains the missing connection. SERV, Reppo, Docling parsing, and the full live workflow have not been run by this frontend delivery. The two public USD source reports are not a completed 4–6-report evaluation corpus. The real-data explorer contains 103,644 published USD observations (4,037 core-metric observations), separate from AI extraction results.

## Continue with Claude Code

```text
Read AGENTS.md, CLAUDE.md, docs/16-frontend-live-integration-handoff.md, docs/18-real-data-corpus-and-context-checks.md, and the domain specifications listed below.
The Evi frontend is already implemented. Preserve the approved design A, English UI, Evi branding, and public access without login.
Implement the backend and real Docling → SERV → deterministic period/unit checks → Reppo → immutable SERV revision workflow.
Use src/types.ts and src/api.ts as the current frontend wire contract, reconciling older domain contracts explicitly.
Configure provider secrets only on the server. Do not ask judges to supply keys.
Do not add demo mode, fabricated results, fake scores, annualization, or restatement propagation.
Run meaningful backend and real PDF tests; run live provider checks only when credentials are configured.
State precisely what was verified, which integrations ran, and what still requires configuration.
```

## Implementation map

| Path | Purpose |
| --- | --- |
| [src/Home.tsx](src/Home.tsx) | Public source-led landing and real reporting cases |
| [src/DataExplorer.tsx](src/DataExplorer.tsx) | Searchable USD source data and metadata checker |
| [src/App.tsx](src/App.tsx) | Four views, live actions, job polling, review workflow |
| [src/PdfViewer.tsx](src/PdfViewer.tsx) | Original PDF canvas and live source-region highlights |
| [src/types.ts](src/types.ts) | Validated frontend response schemas |
| [src/api.ts](src/api.ts) | Real HTTP API adapter; no mock fallback |
| [src/export.ts](src/export.ts) | Exact decimal display and evidence-linked export |
| [src/styles.css](src/styles.css) | Approved responsive visual system |
| [brand.md](brand.md) | Visual direction and brand usage |
| [public/evi-logo.svg](public/evi-logo.svg) | Primary Evi wordmark |
| [public/evi-symbol.svg](public/evi-symbol.svg) | Grid and verification symbol |
| [public/evi-logo-light.svg](public/evi-logo-light.svg) | Light version for dark backgrounds |
| [HANDOFF.md](HANDOFF.md) | Preserved original specification index; historical status statements |

## Specifications

| File | Purpose |
| --- | --- |
| [CLAUDE.md](CLAUDE.md) | Agent instructions and evidence boundaries |
| [01 — Product scope](docs/01-product-scope.md) | User, failure, alternatives, bounded scope |
| [02 — End-to-end workflows](docs/02-end-to-end-workflows.md) | Transitions and recovery |
| [03 — Architecture](docs/03-system-architecture.md) | Services, workers, storage |
| [04 — Data contracts](docs/04-data-contracts.md) | Domain objects |
| [05 — Verification engine](docs/05-verification-engine.md) | Period/unit checks |
| [06 — SERV agent](docs/06-serv-agent.md) | Extraction and revision constraints |
| [07 — Reppo loop](docs/07-reppo-feedback-loop.md) | Evaluation and unknown-outcome handling |
| [08 — Evaluation protocol](docs/08-evaluation-protocol.md) | Frozen labels and fair measurement |
| [09 — Dashboard](docs/09-dashboard-spec.md) | Original dashboard specification |
| [10 — API and jobs](docs/10-api-and-jobs.md) | Backend job design |
| [11 — Implementation plan](docs/11-implementation-plan.md) | Backend milestones and completion gates |
| [12 — Submission](docs/12-demo-and-submission.md) | Demonstration and claim boundaries |
| [13 — Research](docs/13-research-and-current-state.md) | Original research ledger |
| [14 — Dashboard priority](docs/14-dashboard-delivery-priority.md) | Prioritization rationale |
| [15 — Design references](docs/15-web-references-and-design-choice.md) | Approved reference direction A |
| [16 — Integration handoff](docs/16-frontend-live-integration-handoff.md) | Live API endpoints and backend continuation |
| [17 — Winner research](docs/17-winner-research-and-ui-decisions.md) | Primary artifacts and applied design decisions |
| [18 — Real USD data](docs/18-real-data-corpus-and-context-checks.md) | Actual corpus, provenance, context checker, latest scope |

The latest user decisions and document 16 supersede historical instructions to pause frontend implementation or use demo fixtures. This delivery is a frontend; completion of the project still requires real backend execution and evidence-based evaluation.

## November 15 update — public landing and real source data

Top navigation now contains Home (first), Workspace, Real data, Documents, Feedback, and Benchmark. Home is `/`; the PDF workspace is `/workspace`. The rejected workspace/organization selector has been removed. See AGENTS.md for the explicit design prohibition.

Real data contains 103,644 USD observations from six issuers (selected from 128,748 original observations), 4,037 observations across the core metrics, and a working browser-side period/unit context checker. These are real dated source snapshots, separate from future live AI runs. Two original USD PDFs are public; four earlier Indonesian PDFs remain archived. See docs/17-winner-research-and-ui-decisions.md and docs/18-real-data-corpus-and-context-checks.md for sources, audit definitions, and backend boundaries.

## Full Claude Code continuation prompt

Use [CLAUDE-CODE-FULL-PROMPT.md](CLAUDE-CODE-FULL-PROMPT.md) to continue this existing project through the real backend, provider integration, durable jobs, verification, benchmark, and deployment preparation. It preserves the latest Evi branding, top navigation, USD-only public presentation, no-login access, and no-demo rules while resolving obsolete handoff assumptions.

## Backend (live API + durable worker) — added 2026-11-15

```powershell
cd C:\Evidence\EvidenceGrid-Claude-Code-Handoff\backend
py -3.12 -m venv .venv; .venv\Scripts\python -m pip install docling fastapi "uvicorn[standard]" httpx pytest pypdf
copy .env.example .env   # then set SERV_API_KEY / REPPO_API_KEY locally (never VITE_ variables)
.venv\Scripts\python -m uvicorn evi.api:app --host 127.0.0.1 --port 8000   # terminal 1: API
.venv\Scripts\python -m evi.worker                                         # terminal 2: worker
cd ..; npm.cmd run dev                                                      # terminal 3: http://127.0.0.1:5173/
```

Tests: `backend\.venv\Scripts\python -m pytest -q backend\tests` (failure boundaries, job state, API access controls, and a real-artifact bbox check). Browser check: `backend\.venv\Scripts\python scripts\e2e_browser.py verizon-fy2025` (needs Playwright). Data and artifacts live in `data/runs/` (git-ignored). Status and evidence: `artifacts/backend-status.md`. Decisions: `docs/DECISIONS.md`.

## Technical-depth continuation

Use [CLAUDE-CODE-TECHNICAL-DEPTH-PROMPT.md](CLAUDE-CODE-TECHNICAL-DEPTH-PROMPT.md) after or alongside the full continuation prompt. It adds the executable requirements in [19 — Semantic binding and revision](docs/19-semantic-binding-and-revision-spec.md) and [20 — Ablation and proof](docs/20-ablation-and-proof-protocol.md). Current backend code now exists; inspect and extend it rather than repeating the old frontend-only setup. These documents define required work, not claims of completed implementation or measured improvement.

Latest execution checkpoint (November 16): artifacts/backend-status.md and the user report the real two-report Docling/SERV/check/highlight slice works. The technical-depth prompt incorporates that progress. Real Reppo feedback/revision, the completed 4–6-report evaluation, and public deployment remain separate unfinished milestones.

## Technical-depth proof (2026-11-16)

- Mechanisms: [docs/TECHNICAL-DEPTH-IMPLEMENTATION.md](docs/TECHNICAL-DEPTH-IMPLEMENTATION.md). Results and the claim ledger: [docs/PROOF-REPORT.md](docs/PROOF-REPORT.md).
- Replay without provider calls: `cd backend; .venv\Scripts\python -m evi.replay exp-2026-11-16-a` (and `exp-2026-11-16-b`).
- Verify one certificate: `.venv\Scripts\python -m evi.certify --verify <certificate_id>`; the Workspace fact panel has a "Re-verify from source" button.
- Experiment artifacts: `artifacts/technical-proof/<experiment_id>/` (manifest, ledger, outcomes, summary, report).

## Next task — proof integrity repair

Use [CLAUDE-CODE-PROOF-REPAIR-PROMPT.md](CLAUDE-CODE-PROOF-REPAIR-PROMPT.md) to continue after the real four-arm experiments. It addresses experiment-policy replay coverage, non-destructive re-scoring, metric/detector independence, partial context, an offline Reppo payload audit, and preparation of independent reference review. It requires preserving the original experiments and makes no new paid provider calls.

## Next phase — independent validation and release

Use [CLAUDE-CODE-VALIDATION-AND-RELEASE-PROMPT.md](CLAUDE-CODE-VALIDATION-AND-RELEASE-PROMPT.md) after the completed proof-integrity repairs. It continues the reference-review/import workflow, freezes fresh-test preparation, prepares full-context Reppo packets and separate budget gates, and builds/verifies a persistent production deployment package. It does not approve the 5,280-credit calibration, new paid holdout runs, or an unspecified public host. Existing experiments and their null Reppo result remain preserved.

## Public demo

**Start here:** press **Try Evi** on the home page, or follow [docs/JUDGE-WALKTHROUGH.md](docs/JUDGE-WALKTHROUGH.md). Availability is reported per capability: stored results, source re-verification, new extraction and new evaluation. Live processing status: [docs/LIVE-DEPLOYMENT-STATUS.md](docs/LIVE-DEPLOYMENT-STATUS.md).

**https://evi-lovat.vercel.app**: a no-login, read-only archive of the real stored runs (certificates, server-side re-verification, partial-context views, exports). New processing is disabled there: Vercel cannot run the Docling worker, and no provider keys are configured. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Validation and release (2026-11-16)

- Release status and remaining dependencies: [docs/RELEASE-READINESS.md](docs/RELEASE-READINESS.md). Judge path: [docs/JUDGE-WALKTHROUGH.md](docs/JUDGE-WALKTHROUGH.md).
- Deployment (Docker image, compose, Caddy, backups, resource measurements): [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). Production-mode local run: set `EVI_STATIC_DIR=<repo>\dist`, `EVI_EXECUTION_ENABLED=false`, then start uvicorn and the worker; check with `scripts/prod_smoke.py`.
- Reference review: [docs/REVIEWER-INSTRUCTIONS.md](docs/REVIEWER-INSTRUCTIONS.md); `python -m evi.review validate|import <sheet>`.
- Spending gates: `EVI_EXECUTION_ENABLED` (server switch, off by default) and, for experiments, `python -m evi.authorization template|check <id>` plus `EVI_ALLOW_PAID_RUNS=1`. Budgets: [docs/BUDGET-SHEET.md](docs/BUDGET-SHEET.md).
- Fresh holdout: `python -m evi.holdout preflight holdout-2026-11-16-a` (frozen; not run).
- Reppo packet v2 dry run: `backend\.venv\Scripts\python scripts\check_packet_v2.py`.
- Local development keeps processing enabled via `EVI_EXECUTION_ENABLED=true` in the ignored `backend/.env`.
