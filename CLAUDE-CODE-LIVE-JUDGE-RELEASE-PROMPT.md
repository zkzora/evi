# Evi — Complete the public judge experience and live deployment

Paste the prompt below into Claude Code from `C:\Evidence\EvidenceGrid-Claude-Code-Handoff`.

---

You are continuing the existing Evi application. Implement and verify the remaining public judge experience. Work in this repository; inspect the actual code and current deployment before choosing changes. Do not stop at a plan, recreate the application, or repeat completed proof-repair work.

## Outcome

A judge can open Evi without an account, understand the problem, run a bounded real extraction on an allowlisted public financial report, inspect period/unit/source checks on the original PDF, re-verify the certificate, and inspect the real evaluation history and published experiment results.

The product prevents an analyst from using a plausible financial number with the wrong reporting interval, monetary scale, or attribution row. The core proof is the source binding and period/unit check, not a generic document chatbot or a Reppo score.

There are two distinct acceptance levels:

1. **Inspectable public evidence:** real historical runs, original PDF highlights, live deterministic certificate verification, a source-metadata context challenge, and honest experiment reporting.
2. **Public live processing:** a newly queued job actually runs Docling and SERV on a durable worker, produces a new immutable result and receipt, and survives browser reloads.

Deliver both when the required host and explicit public-processing budget are available. Do not call level 1 a completed level 2. A new Reppo evaluation additionally requires its own permitted budget. An unchanged or already correct extraction is a valid outcome; do not manufacture an error or correction.

## Read first and resolve historical instructions

Read applicable AGENTS.md files, CLAUDE.md, brand.md, README.md, and these current records:

- `docs/16-frontend-live-integration-handoff.md` (some implementation descriptions are historical).
- `docs/RELEASE-READINESS.md`, `docs/DEPLOYMENT.md`, `docs/BUDGET-SHEET.md`.
- `docs/DECISIONS.md`, `docs/JUDGE-WALKTHROUGH.md`.
- `docs/PROOF-INTEGRITY-REVIEW.md`, `docs/PROOF-REPORT.md`, `docs/REPPO-PAYLOAD-AUDIT.md`.
- Existing spending-approval rules and `artifacts/technical-proof/` and `analysis-v2/` manifests wherever currently stored.

Verify installed tools, existing hosting configuration, current tests and actual API contracts. Later implemented behavior supersedes old statements such as "there is no backend." Preserve the original experiment and replay integrity rules.

## Observed public deployment: reproduce these findings

Public site: https://evi-lovat.vercel.app

Representative deep link:

https://evi-lovat.vercel.app/workspace?run=run_2137f9cebc4847dcaffd&fact=run_2137f9cebc4847dcaffd%3Averizon-fy2025%3Arevenue%3A12M%3A2025&document=verizon-fy2025&version=ver_2137f9cebc48_5

A browser inspection found:

- Guest access, source highlights and stored results work.
- Certificate re-verification succeeds from the registered PDF bytes and Docling artifact.
- Real data correctly rejects a nine-month observation when Full year is selected, then accepts the same observation when nine months is selected. This is a source-metadata rule check, not a new AI extraction.
- The green "Service connected" status and enabled-looking "Run extraction" button imply processing is available. Clicking the button only opens a connection dialog explaining that processing is disabled.
- Benchmark says no measured benchmark has been published.
- Feedback for the selected FY2025 report shows zero sessions. Existing experiment evaluations must not be falsely attached to this newer version.

The current Vercel archive adapter forces execution off, blanks provider credentials and has no Docling worker. A frontend change or enabling a flag in that adapter cannot make it a live worker deployment.

Screenshot evidence is in `artifacts/judge-review/`. Recheck the current deployment because it may have changed since inspection.

## 1. Make availability accurate and immediately understandable

Replace the ambiguous single connection state with capability-based readiness driven by the backend. Reuse and extend current contracts deliberately rather than inventing a parallel status system.

Distinguish:

- Stored results available.
- Source verification available.
- New extraction available, unavailable, temporarily busy, or budget exhausted.
- New external evaluation available or unavailable.

Connectivity alone never means processing readiness. Readiness must account for durable worker heartbeat, storage, enabled execution policy and configured provider access without making a paid health-check call or exposing secrets. Reppo unavailability must not block an otherwise permitted Docling/SERV extraction.

In archive mode, label historical outputs and their original timestamps, explain the unavailable action inline, and offer a useful inspection action. Do not present an enabled Run extraction button that only opens generic settings. In live mode, the action queues a real job and reports its actual state.

Keep English copy, Evi branding, USD, top navigation with Home first, and the existing visual direction. Never add the rejected avatar/organization/workspace selector or a sidebar. Avoid a wholesale visual redesign.

## 2. Build a short, working judge path

Add a visible entry point such as "Try Evi" on Home and Workspace. Guide visitors through the following meaningful actions without a login wall:

1. **Catch a period mismatch.** Open a real nine-month SEC observation, display its exact dates and source provenance, and let the visitor compare it with Full year. Explain the rejected context. Switching to the matching interval must pass. Include an actual unit mismatch and correct unit selection if the existing mechanism supports it.
2. **Run a real extraction.** Select from the existing 4–6-report telecom USD corpus and click Process. Show queued, parsing, extracting, checking and terminal states only when those stages actually occur. Display the report, physical page coverage and new job/run identity. If parsing is reused, say so and distinguish it from a fresh Docling parse.
3. **Inspect the evidence.** Open a fact and its value, metric, period and unit anchors on the correct original PDF page. Show complete context, partial context, conflict and unknown faithfully. Re-verification recomputes from registered source material.
4. **Inspect evaluation and revisions.** Show genuine Reppo records and exact evaluated version lineage. Permit a new evaluation only when that capability is enabled and budgeted. A revision may change nothing; show that outcome honestly.
5. **Inspect measured evidence.** Link to published experiments with the comparison arms, counts, limitations and downloadable public artifacts.

Use route/query parameters or existing application state for reproducible deep links; preserve state on reload and navigation. Offer a restart/reset for the walkthrough without deleting historical records. Visitors can inspect evidence while another job is queued.

If a controlled corruption is useful for teaching, clearly label it as an intentional mechanism test. Keep it separate from naturally occurring extraction failures, historical predictions and measured accuracy. Never edit stored model output to create the hook.

Do not add arbitrary uploads or URL ingestion in this release. Use registered public reports. Do not claim millions of processed documents or equate source-observation counts with verified facts, detected errors or benchmark targets.

## 3. Publish the existing technical proof correctly

Adapt the current Benchmark API/UI to expose actual frozen experiment artifacts. Use the corrected `analysis-v2` interpretation alongside clearly identified historical scores. Derive numbers and denominators from artifacts; do not hardcode promotional values into components.

Show:

- Experiment identity, date, policy, corpus, target count, trials and reference provenance.
- A: Docling + initial SERV; B: checker added; C: revision without Reppo; D: revision with real Reppo feedback. Explain shared predictions where appropriate.
- Reference match, checker detection/false alarms, interval completeness and strict/composite metrics as separate named measurements.
- Correct/total counts, paired changes and regressions. Unknown exact dates can be faithful to the source without being a complete interval.
- The null finding prominently: D equals C in both existing experiments; a Reppo benefit has not been established.
- Experiment b as post-hoc development evidence; current reports are not a genuinely unseen holdout.
- Builder-drafted labels and human-review status, loaded from the actual review records. Do not mark pending labels as independently reviewed.

A Reppo 100/100 opinion is not extraction accuracy. Existing generic-rubric evaluations used candidate-citation packets; the fuller v2 packet was checked offline and must not be described as a completed paid calibration. Do not silently revise the old packets, scores or manifests.

Expose recorded evaluation sessions in a separate experiment/history view when they do not belong to the currently selected production run. Every evaluation must link to its actual evaluated version. Show an honest zero-session state for a version with none.

Publish only an explicit safe export schema: source identity, version/policy, factual results, sanitized evaluation output, analysis and provenance needed for inspection. Exclude credentials, sessions, cookies, private prompts, account metadata, raw database files and unnecessary upstream identifiers. Provider failures or missing artifacts must produce explicit states rather than fabricated success or a blank benchmark.

## 4. Complete the existing durable deployment

Prefer the prepared same-origin API + worker + Caddy deployment with one host and persistent local storage, unless an already configured host justifies another approach. Keep SQLite API and worker on the same local volume; do not share SQLite across hosts or place it on ephemeral/network storage.

The existing Vercel frontend may remain the entry point only if its routing correctly reaches the durable API. Carefully preserve anonymous cookie ownership, source/evidence routes and same-origin write protections. A Vite development proxy does not work in production. Do not broadly enable CORS or weaken write protections to mask routing failures.

Inspect existing authorized host/project configuration first. Reuse available resources where authorization and cost are already established. Do not purchase a host, accept new paid terms, create accounts, configure paid infrastructure or invent credentials without the user's authorization. If the host is missing, finish implementation, image/config preparation, local validation and a concrete deployment runbook, then request only the exact missing host access/cost decision. Do not ask the user to paste secrets into chat.

Build and test the Docker image if Docker is available. If unavailable, state that it is unbuilt; do not call a non-container smoke test a container test. Align compose limits with actual host memory rather than calling a 6 GB worker limit suitable for a 4 GB machine. Treat resource sizing as an estimate until measured on the target.

Preserve backups and the working public archive until the live host passes readiness and read-only smoke tests. Seed or migrate via verified backups; do not overwrite original state. Keep models cached, honor worker leases, handle restarts, configure HTTPS, and document rollback and restore. Change public routing only when the destination is ready.

## 5. Keep guest execution bounded

Reuse the existing server-enforced controls and close gaps found in verification:

- Anonymous HttpOnly session ownership, allowlisted sources, same-origin writes and conservative concurrency.
- Durable idempotency for processing, evaluation and revision. Reloading/double-clicking cannot create duplicate charges.
- Global and per-session/run caps, including provider submissions and credits. Concurrent requests must reserve budgets atomically before calling providers. Reconcile actual use; unknown submissions must not be automatically resubmitted.
- A clear queue/busy/exhausted response, persisted job status and a server-side emergency processing switch.
- Read-only evidence inspection remains available when paid execution is disabled or exhausted.

Keys remain server-side; never use VITE_ provider keys or ship local `.env` files. Existing secrets being present does not authorize new charges. Do not create or sign an approval file on behalf of the user, remove spending gates, or treat this implementation prompt as an unlimited runtime budget.

Inspect existing valid approvals before requesting anything. If no public-run allowance exists, prepare one explicit small smoke-test/public-use plan with maximum SERV calls, Reppo evaluations/credits, duration and applicable run(s), then ask for that concrete allowance. Verify current provider/account pricing before proposing the allowance. Calibration and fresh holdout experiments remain separate; do not run them to fill the dashboard.

## 6. Verify the actual experience

Use meaningful automated tests at the capability, job, ownership, budget and export boundaries; reuse existing tests instead of duplicating implementation details. Run the affected backend/frontend suites and production build. Preserve replay as read-only and confirm original experiment artifacts remain unchanged.

Test from a clean browser on the public HTTPS URL when hosted:

- Home → Try Evi → intended context mismatch → matching context.
- Guest access, accurate readiness and useful disabled/busy/error states.
- New real Process job with observable timestamps, identities, stage outcomes and source page coverage, if explicitly budgeted.
- Reload during execution and recover the same job, with no duplicate calls.
- Actual PDF anchors across differently positioned source layouts, including FY2024's offset coordinates.
- Re-verify a certificate; retain partial-context warnings for AT&T rather than guessing dates.
- Exact run/version/fact deep links after reload and menu navigation.
- Existing experiment/evaluation records visible with correct lineage and the null Reppo finding.
- Export provenance, valid JSON API errors, no exposed secrets, no browser errors and a usable small-screen layout.
- Worker restart/resumption and budget enforcement on isolated test state without modifying original experiments or spending credits just to test refusal paths.

Record what actually ran. A passing mock, local test, image build, hosted read-only check and paid live run are different evidence. If no funded live run is authorized, mark that acceptance criterion pending instead of simulating success. Independent human label review is needed for independently validated accuracy claims, not as a blanket blocker for serving the application.

## Deliverables and stopping condition

Update or create:

- `docs/JUDGE-WALKTHROUGH.md`: a concrete 2–3 minute path with working public deep links, expected observations and availability limitations.
- `docs/LIVE-DEPLOYMENT-STATUS.md`: actual host/routing, image status, readiness, execution policy, remaining dependencies and rollback.
- `docs/JUDGE-ACCEPTANCE-REPORT.md`: acceptance matrix with evidence paths, URLs, test results, original-artifact integrity and any authorized real-call costs.
- README, RELEASE-READINESS and deployment/env documentation where behavior changed.
- Browser screenshots and sanitized verification artifacts under `artifacts/judge-release/`.

First inspect and implement all work possible without missing external dependencies. Report blockers only after making the work concrete and reviewable. Do not stop repeatedly to ask about routine implementation choices.

Your final report must state: what judges can actually do now; which URL serves it; whether new Docling/SERV/Reppo calls truly ran; exact paid usage if any; what passed; what remains unavailable; and the smallest remaining user action. Do not say "end to end live" until the deployed job has genuinely completed and its source evidence can be inspected from a clean browser.
