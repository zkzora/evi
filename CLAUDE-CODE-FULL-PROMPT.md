# Evi — Full Claude Code continuation prompt

Copy everything below the separator into Claude Code, or tell Claude Code to read this file and execute it. Open the existing project directory first:

`C:\Evidence\EvidenceGrid-Claude-Code-Handoff`

---

You are the implementation engineer responsible for completing **Evi** from its existing frontend to a working, verifiable end-to-end product.

**Implement the work. Do not stop at a plan, a scaffold, mock endpoints, or another handoff document.** Inspect the repository, make the changes, run appropriate checks, connect the actual services when credentials are available, and verify the result through the browser. Continue independent work while a genuine external dependency is unavailable. Never claim completion of a step that did not run.

## 1. Establish the current source of truth

Work in `C:\Evidence\EvidenceGrid-Claude-Code-Handoff`. Inspect applicable ancestor/project AGENTS.md files and preserve existing user work.

Read in this order:

1. `AGENTS.md` — explicit interface and currency constraints.
2. This prompt — the complete continuation objective.
3. `README.md`, `brand.md`, and the **latest sections** of `CLAUDE.md`.
4. `docs/18-real-data-corpus-and-context-checks.md` — actual data, USD scope, provenance, and current routes.
5. `docs/16-frontend-live-integration-handoff.md` — frontend/backend wire contract.
6. `src/types.ts`, `src/api.ts`, `src/App.tsx`, `src/catalog.ts`, `src/source-data.ts`, `src/DataExplorer.tsx`, and `public/datasets/manifest.json`.
7. `docs/01-product-scope.md` through `docs/12-demo-and-submission.md` for the detailed domain mechanism, evidence rules, jobs, and evaluation protocol.
8. `docs/13-research-and-current-state.md`, `docs/17-winner-research-and-ui-decisions.md`, and `artifacts/verification.md` for research and previous verification evidence.

Some older files still describe EvidenceGrid, an Indonesian-only corpus, a sidebar, four/eight menus, or a documentation-only package with no frontend. **Those historical statements are superseded by the user's latest decisions below.** Do not rebuild from those obsolete assumptions. Domain evidence rules still apply. Record necessary contract/architecture decisions in `docs/DECISIONS.md`.

## 2. Product and failure to solve

Target user: a financial analyst collecting comparable monetary figures from public telecom/connectivity reports.

Concrete failure: an extracted amount loses the reporting interval or monetary scale that gives it meaning. A nine-month revenue figure becomes labeled as a full year, or a figure expressed in USD millions is treated as base USD. The analyst carries the mismatch into a comparison or model.

Mechanism: use **Docling** to parse source structure and provenance, **SERV Reasoning** to interpret the applicable metric/column/period/unit context, deterministic checks to validate supported interpretations, and **real Reppo feedback** to guide a bounded, evidence-backed SERV revision. Preserve immutable initial and revised versions and measure the result against a frozen reference protocol.

The practical alternative is a competent extraction workflow, not a deliberately broken model. Structured SEC records already contain useful context. Evi must demonstrate its unstructured-PDF interpretation and revision mechanism; a large record count or a polished UI alone does not prove that advantage.

The smallest complete proof is one real PDF processed into three real metrics, four kinds of source evidence, deterministic checks, a real Reppo evaluation, an immutable SERV revision, and an inspectable before/after export. Extend that working slice into the bounded evaluation corpus.

## 3. Locked user decisions

- Brand name: **Evi**. Preserve the original SVG logos and favicon.
- All product UI, code-facing documentation, prompts, and submission material are English.
- International presentation: **USD only**. Use actual USD-denominated source reports/observations. No fabricated FX conversion and no relabeling IDR/EUR amounts as USD.
- Three core metrics only: consolidated revenue; explicitly reported operating profit; profit attributable to owners of the parent. Do not substitute EBITDA, segment revenue, total profit including noncontrolling interests, or a computed proxy without changing scope explicitly.
- One sector: telecom/connectivity. Finalize **4–6 actual USD reports** for the PDF evaluation; the two public PDFs currently present are a starting point, not a completed corpus.
- Preserve **top navigation** in this order: **Home, Workspace, Real data, Documents, Feedback, Benchmark**. Home is the first menu item; `/` is the landing page and `/workspace` is the PDF workspace.
- **Never restore the rejected workspace/organization card** with an initial avatar, “Research workspace,” “Public access,” and a checkmark, or a cosmetic equivalent. No sidebar, fake organization selector, or decorative account avatar.
- Judges must be able to open and use the application **without login/signup, wallet connection, provider keys, or account setup**.
- **No demo mode. No synthetic financial results. No simulated successful provider calls.** Genuine dated source snapshots remain available and clearly labeled as such.
- No general PDF chat, arbitrary web crawler, wallet/token/blockchain feature, custom OCR engine, restatement-propagation engine, or additional financial metrics.
- Reuse Docling; do not compete with or reimplement it.

## 4. What already exists — verify before changing

The repository already contains React + TypeScript + Vite, a responsive English frontend, PDF.js viewing, original logo assets, API adapters and Zod schemas, precision-preserving exports, and working browser-side checks of published SEC metadata.

Current routes:

- `/`: public landing with real reporting-period and USD scale cases.
- `/data?company=verizon`: source explorer with company/metric/year/search filters, pagination, source inspection, context checks, and JSON export.
- `/workspace`: PDF/fact/evidence review and processing actions.
- `/documents`: original report library.
- `/feedback`: Reppo sessions and revision flow.
- `/benchmark`: measured artifacts only; no invented percentages.

Real data currently includes:

- **128,748 original SEC observations** across all original units in the downloaded responses.
- **103,644 actual USD observations** in public normalized shards.
- **4,037 observations across the three core metrics**.
- Six issuers: Verizon, AT&T, T-Mobile US, Comcast, Vodafone, Telkom Indonesia.
- **861 qualifying multi-interval contexts**, not 861 detected errors.
- Counts include comparative disclosures repeated across filings. They are not unique economic facts, reports, or benchmark targets. Do not claim two million records.
- Vodafone has few USD observations and no mapped core-metric observations; never fill the missing data through invented conversion.

Current default public PDFs:

- Verizon FY2025: 329 physical pages; income statement at page 52.
- Verizon FY2024: 116 pages; income statement at page 54.

Four earlier Indonesian PDFs remain archived. Preserve them, but do not reintroduce their native-currency amounts into the USD presentation.

The previous frontend delivery passed a production build and 15 tests. Re-run the relevant checks on your actual checkout; prior results are not verification of your new backend.

**Updated execution baseline, November 16:** artifacts/backend-status.md and the user report real Docling parses plus SERV extraction/checks/highlights for both Verizon PDFs, 41 backend tests and 15 frontend tests. Preserve and inspect those real outputs; do not rebuild the working slice or overwrite historical check snapshots. Real Reppo feedback/revision, the 4–6-report benchmark, and public deployment remain unfinished. Read CLAUDE-CODE-TECHNICAL-DEPTH-PROMPT.md for the current continuation. The SEC source explorer remains distinct from live PDF outputs and benchmark results.

## 5. First actions and working behavior

1. Inspect files, installed runtimes, dependencies, git state, existing local services, ignored configuration, and any pre-existing backend work. Do not print secrets or overwrite another process's work.
2. Run the current frontend tests/build once as a baseline. Inspect a representative page in the browser when supported.
3. State a short implementation plan and the first real vertical slice. Then implement immediately.
4. Keep a concise execution log and status checklist, including real artifacts, tests, provider status, and unresolved dependencies. Keep working until the completion criteria are met or an actual external input is indispensable.
5. Make routine reversible implementation choices autonomously. Do not ask the user to select every package or approve every file.
6. Do not replace the frontend stack or redesign the approved site. Adjust frontend integration behavior where necessary and preserve its visual language.

## 6. Backend foundation and durable execution

Prefer the specified Python/FastAPI/Pydantic approach, Decimal money, a durable database, and a separate worker. SQLite is suitable for the first local complete build; choose a production-appropriate persistent deployment model and explain any migration. Match an existing sound backend if one already exists instead of scaffolding a duplicate.

Implement:

- Source registration with original URL, bytes, SHA-256, issuer, currency, physical page count, and immutable source version.
- Durable parse jobs, extraction runs, fact versions, evidence records, deterministic checks, Reppo submissions, revisions, and benchmark artifacts.
- Worker leases, bounded concurrency, retry classification, process restart recovery, and status read-back.
- Explicit pending, running, succeeded, failed, cancelled, blocked, and unknown-outcome handling where applicable.
- Timeouts, cancellation/shutdown behavior, safe artifact paths, structured errors, and redacted logs.
- Stable identifiers and idempotency for expensive or external POST operations. Persist upstream IDs as soon as they are known.
- Real progress/status derived from actual stages; no timer-driven fake progress.

Do not keep long-running Docling/model/evaluation work inside a blocking API request. A browser reload must not lose the job or resubmit an existing provider evaluation.

## 7. Match the actual frontend API contract

Default base path is `/api/v1`; development Vite proxies `/api` to `http://127.0.0.1:8000`.

Read `src/api.ts` and `src/types.ts` as the current wire-format contract. Preserve existing field names unless you deliberately update both the frontend adapter/schema and backend with appropriate checks. Older domain contracts may contain additional useful fields.

List responses: `{ "items": [...] }`.
Individual responses: the object directly.
Long-running POST responses: a durable job object with at least `job_id` and `status`.
Errors: non-2xx JSON, `{ "error": { "message": "..." } }`.

Required frontend routes:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Service readiness and `live_execution_enabled` |
| GET | `/documents` | Registered source reports |
| GET | `/documents/{id}/source` | Original PDF bytes |
| POST | `/documents/{id}/parse` | Real Docling parsing job |
| GET | `/runs?document_id={id}` | Real runs and ordered version IDs |
| POST | `/runs` | Real extraction job using a valid parse_id |
| GET | `/versions/{id}` | Immutable facts/checks/lineage |
| GET | `/evidence/{id}` | Source-matching evidence/text/page/bbox |
| GET | `/jobs/{id}` | Durable status and error/message |
| GET | `/evaluations` | Permitted real evaluation records |
| POST | `/versions/{id}/evaluations` | Submit a real Reppo evaluation |
| POST | `/evaluations/{id}/refresh` | Reconcile/poll the existing provider evaluation |
| POST | `/versions/{id}/revisions` | Bounded revision for the named evaluation |
| GET | `/benchmarks` | Actual measured benchmark artifacts |

Money crosses JSON boundaries as decimal strings. Evidence includes `document_id`, `document_sha256`, physical 1-based `page_number`, text, and actual bbox/page dimensions when available.

Run mode is `live`; supported version origins are `serv_initial`, `serv_revision`, and separately identified `manual`. Real Reppo records use `mode: reppo_live`. Preserve real provider metadata without inventing evaluator IDs or scores.

Set `live_execution_enabled: true` only when credentials, workers, permitted live routes, and server-side budgets are actually configured. A healthy HTTP process does not prove provider readiness.

Make the process flow coherent: selecting a source and choosing Process report should reach a real extraction through actual parsing and a valid parse_id. The present UI requests parsing first and extraction after parsed status; wire the stages clearly, preferably with bounded automatic continuation under the same explicit user action. Never invent a parse_id or claim extraction success after parsing alone.

## 8. Implement real Docling evidence

Inspect the installed Docling version and current official documentation. Install only what is needed; reuse downloaded model artifacts and caches.

- Parse actual original PDFs; retain original bytes and hashes.
- Preserve table structure, cells, column/row relationships, merged headers, page text, and provenance.
- Identify relevant statement pages transparently. If using page-limited parsing for long annual reports, record coverage and prove the applicable headings/unit notes are included; do not represent a partial parse as complete coverage.
- Build stable evidence windows containing the amount, metric row, applicable period heading, and monetary unit note.
- Preserve printed page labels separately from physical PDF page indices.
- Use actual source coordinates and documented coordinate origins; verify PDF.js highlights against rendered pages.
- If a bbox cannot be obtained, show text-only evidence with an explicit limitation. Never invent highlight rectangles.
- Cache by source hash, parser version/configuration, and page coverage. Reuse across initial/revised runs fairly.

## 9. SERV extraction and deterministic verification

Verify current SERV model availability, request format, structured-output behavior, and supported options against official docs before implementing the adapter. Historical model suffixes, pricing, feature flags, or example parameters are not assumed current.

SERV interprets source context. Application code validates references, computes arithmetic, enforces budgets, and scores outputs.

Initial extraction must:

- Use real Docling evidence and the three requested metric/column targets.
- Include applicable headings and unit notes in a competent initial evidence packet.
- Distinguish quarterly, year-to-date, full-year, comparative-year, instant, publication-date, and fiscal-calendar context.
- Preserve original amount text, source unit/currency, metric scope, exact interval, and separate evidence IDs for value/metric/period/unit.
- Return null/unknown with a reason when support is absent.
- Never annualize, convert currency, substitute a related metric, or guess missing evidence.
- Validate all output through Pydantic and source-reference checks. Preserve malformed/refused/truncated outputs and their real statuses.

The deterministic engine must check:

1. Original source hash and evidence ownership.
2. Value-cell/column and metric-row support.
3. Explicit numeric locale, signs, footnotes, dash/zero/missing distinctions, and non-monetary exceptions.
4. Currency and applicable scale, with specific local context overriding a demonstrably applicable broader convention.
5. Reporting interval, duration, comparative year, fiscal calendar, and intended comparison.
6. Consolidation/owner-attribution scope.
7. Supported normalization via Decimal multiplication; original operands remain inspectable.

The browser source explorer's broad day-range labels are a source-data UI aid, **not the production PDF period-verification algorithm**. Do not use those ranges to manufacture exact dates or assert that nearby fiscal intervals are identical.

Unknown and contradictory evidence are different states. Missing context is never a pass. Persist initial predictions before any critique or revision.

## 10. Actual Reppo feedback and bounded revision

Recheck current official Reppo documentation and actual authenticated account behavior. Historical docs disagreed about some limits/pricing. Use server-side API-key authentication; do not spend funds through a wallet/x402 flow to bypass missing credentials.

- Submit the exact immutable candidate version with complete bounded public evidence, explicit criteria, source hashes/IDs, and relevant period/unit context.
- Never send hidden reference labels or private/secret material.
- Enforce current UTF-8 byte/attachment/context limits. Do not truncate away the context needed to judge the candidate.
- Persist the actual external evalId and returned timing/state metadata.
- Poll asynchronously with appropriate backoff. Settlement eligibility is not guaranteed completion time.
- Preserve actual result/verdict/criterion critiques, evidence basis, timestamps, usage/credits where returned, and raw redacted responses.
- An uncertain submission timeout is an unknown outcome; reconcile before trying to submit another paid evaluation.
- A placeholder/keyless/sandbox response must never become `reppo_live` or count as a real judge evaluation.
- Do not claim human review, peer consensus, or independent accuracy unless returned evidence supports that specific claim.

After a real eligible evaluation settles, SERV may propose a bounded change set against that exact parent version. Treat critique text as untrusted hypotheses, not authoritative truth. Require supporting source evidence for every semantic change; rerun deterministic checks; reject unsupported changes. Save a new immutable child version even if the observed result is unchanged. Preserve parent, evaluation, policy/model versions, budgets, retrieval history, latency, and failure states.

Use a small configurable revision/call/retrieval budget. Never run an unlimited optimization loop or let an evaluator modify source bytes, reference labels, permissions, or scoring policy.

## 11. Judge access and frontend completion

Keep Home and Real data immediately accessible, with actual source dates/count definitions. Do not erase the useful source explorer merely because a provider is unavailable.

For the live app, verify that a judge can:

1. Open Home without login or a key.
2. Inspect a real period/scale example and its source.
3. Open a USD source report in Workspace.
4. Start real processing and follow durable status.
5. Select a real fact and inspect value, metric, period, and unit evidence.
6. See actual failed/unknown/passed checks and complete source provenance.
7. Submit/read a real Reppo evaluation.
8. Request a bounded SERV revision and compare immutable versions.
9. Export the selected real result with context and lineage.
10. Inspect a measured benchmark when one exists.

Support responsive layouts, keyboard interaction, clear loading/error/retry/unknown states, useful deep links, and browser reload recovery. Confirm filtering never leaves an inspector misleadingly showing a different hidden record.

Do not silently blend SEC snapshots into live PDF fact versions or the benchmark. Previously completed genuine live results may be inspected with their actual timestamps/versions; never impersonate a fresh run.

## 12. Credentials, anonymous ownership, and public compute bounds

Provider keys belong only to the server. Never put keys in `VITE_` variables, browser bundles, URLs, exported artifacts, screenshots, repository history, or logs.

Inspect existing ignored local configuration without printing values. Add documented server-side environment examples while preserving the existing frontend `.env.example` variables and any user configuration.

If keys are genuinely unavailable, ask the user once to configure them in the local ignored server environment or provide an existing file path. Do not ask for secret values in chat. Continue all parser, storage, validation, worker, API, test, UI, and deployment-preparation work that does not require the keys. Never substitute another provider silently.

No login wall does not mean unbounded shared compute. Implement anonymous session/job ownership, same-origin protections, input/schema limits, registered-public-source allowlists, per-session and global rate/concurrency/provider budgets, idempotency, and durable budget accounting. Keep public immutable artifacts separate from session-owned operations. Do not expose other users' mutable jobs or an arbitrary paid provider proxy.

Avoid scope creep into enterprise identity. The judge's experience remains direct access without accounts.

## 13. Freeze and execute a fair benchmark

Finalize 4–6 real USD reports with annual/interim, duration, unit-scale, and comparative-column coverage. Record exact issuer URLs, file hashes, target columns, eligibility decisions, and split. Keep issuers/templates separated across development/holdout where feasible.

Use the original PDFs for reference annotation. Do not treat a convenient SEC observation as an automatically interchangeable accounting reference for a different report, year, or accounting standard.

Prepare source-reviewed reference packets with exact printed values, Decimal normalization, metric scope, start/end/duration, currency/scale, and source regions. Freeze target manifest, labels, and scoring policy before holdout inference. Store labels outside every parser/model/evaluator/retrieval input path.

Follow document 08:

- Baseline: a competent one-shot SERV extraction over the initial Docling evidence.
- Revised arm: starts from the **same saved baseline**, then deterministic diagnostics, real Reppo feedback, and the bounded automated revision.
- Missing, malformed, unresolved, refused, and unsupported targets remain in the denominator.
- Report strict semantic correctness, period/unit/numeric/evidence correctness, coverage, improvements, regressions, unchanged incorrect cases, latency, model usage, and actual evaluation cost where available.
- Use the same frozen targets and precision policy across arms. Never select an intermediate result because it matches hidden labels.
- Separate development from holdout results and manual corrections from autonomous results.
- Report unchanged/worse performance honestly. No desired “70% → 90%” target.
- Controlled corruptions are labeled mechanism tests, not natural extraction errors or natural benchmark improvements.
- Do not attribute an end-to-end improvement specifically to Reppo unless a fair checks/revision-without-Reppo ablation supports that stronger claim.

Reference-label provenance must be truthful. Agent-created drafts are not independent human gold labels. If human review is still required by the evaluation protocol, prepare a concrete reviewable annotation packet, continue all independent work, and request that specific review. Keep any provisional agent-annotated scores separate and explicitly labeled; do not publish them as the required verified benchmark.

## 14. Required tests and actual verification

Add meaningful backend tests for the failure boundaries, not a large collection of implementation-mirroring mocks.

At minimum verify:

- A genuine nine-month source requested as annual fails; the same source with the correct requested period passes.
- Three-month versus nine-month columns sharing an end date remain distinct.
- Comparative year and fiscal-year boundaries are not inferred from filenames.
- USD millions/billions normalize exactly; missing scale, conflicting scope, and per-share exceptions remain unresolved/rejected as appropriate.
- Large/negative monetary values retain precision.
- Missing metrics/zero/unknown are distinguishable.
- Missing/cross-document/hash-mismatched anchors cannot be accepted.
- Real source bboxes match actual rendered regions.
- Unsettled/sandbox/wrong-parent feedback cannot authorize a claimed live revision.
- Unsupported critique-induced changes are rejected.
- Worker restart, duplicate clicks, unknown submission outcomes, and provider failures preserve durable state and budgets.
- Anonymous access controls/rate limits work at the server boundary.
- Benchmark leakage controls, denominators, regressions, and coverage are correct.

Run an actual PDF parse integration test, actual service/API read-back, frontend/backend contract checks, frontend tests and production build, and browser end-to-end verification. Run bounded real SERV and Reppo smoke tests when configured; preserve their actual IDs/artifacts without secrets.

Do not report an integration as verified because a mock returned the expected JSON. Distinguish automated tests, real local integration, provider calls, browser flow, and public-deployment verification.

## 15. Deployment and operational delivery

Prepare a reproducible local startup path and production setup with frontend, API, durable worker, persistent database/artifact storage, appropriate SPA routing, same-origin `/api` routing, HTTPS, and server-side secrets.

Vite's development proxy is not a production API gateway. Verify that the chosen host can run Docling and durable workers; do not put an unsupported long-running parser/worker into a short-lived function and declare deployment complete.

Use an existing authorized deployment target when the session supplies one. Do not create paid services, publish a repository, post on X, submit the hackathon form, send messages, or make an unrelated account/security change merely because this prompt mentions delivery. If the deployment destination/authorization is still missing, finish the runnable package, environment requirements, deployment commands, cost/runtime implications, and reviewable artifacts first; then ask one specific final question for the missing target/approval.

A localhost URL is not publicly accessible to judges. A successful static frontend deploy does not establish a working live backend. If public deployment is performed, verify the real shared URL from a clean browser context and document the actual API/worker/persistence/provider state.

Do not stop after writing a Dockerfile or deployment guide if an authorized configured target is available and required verification can proceed.

## 16. Final deliverables and completion gate

Deliver the actual integrated implementation, not just documentation. Include:

- Backend/API/worker code and versioned configuration/migrations as needed.
- Functional existing frontend connected to the live backend.
- Real Docling source/evidence artifacts and an inspectable real extraction.
- Actual Reppo evaluation and immutable SERV revision artifacts when credentials allow.
- Frozen corpus/target/reference/scoring manifests and honest measured results at the verified provenance level.
- Reproducible startup/test/benchmark commands and a documented deployment path.
- English architecture/API/runbook notes that reflect the final implementation.
- A concise judge walkthrough, source-linked evidence bundle, and submission write-up draft. Preparing material does not authorize posting or submission.
- Browser screenshots of the completed current UI, without secrets or the rejected workspace-card design.
- A final status report showing exactly which steps actually ran and any indispensable missing dependency.

Do not mark the full project complete until a reviewer can use the real document → extraction → evidence/checks → real feedback → revision → export loop and the required benchmark/deployment claims are supported by actual execution. If an external key, settlement, annotation review, or deployment target prevents a required step, state that precise limitation rather than fabricating success or treating a scaffold as complete.

In your final response, give the working URL or exact local startup commands, completed behavior, meaningful test results, real provider/artifact IDs where safe, measured results with counts, and remaining limitations. Do not guarantee a hackathon award.

**Start now: inspect the existing project, state the first real end-to-end milestone briefly, and implement it.**

## Technical-depth extension — read before resuming

The user subsequently requested deeper technical mechanisms and proof. Read CLAUDE-CODE-TECHNICAL-DEPTH-PROMPT.md and its mandatory documents 19–20 together with this prompt. Backend code now exists in backend/evi/; earlier statements that no backend exists describe the previous handoff, not the current checkout. Inspect and extend the latest code/provider contracts and DECISIONS.md. The extension makes context-applicability binding, field-aware revision acceptance, and the no-Reppo ablation explicit; it does not authorize a rewrite, extra menus, fake results, or unbounded provider spending.
