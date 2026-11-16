# Evi — Ship limited judge PDF upload

Work in `C:\Evidence\EvidenceGrid-Claude-Code-Handoff`.

Implement this feature now against the existing working app. Time is limited: deliver one complete, narrow upload-to-evidence path, not a new ingestion platform or a redesign. Inspect the actual current code before changing it. Complete implementation, relevant tests, build, and deployment through the existing authorized projects when available.

## Goal and scope

A judge can use their own public telecom financial-report PDF without logging in. They select ONE physical income-statement page, run the existing Docling → SERV → checker → certificate pipeline, and inspect the extracted facts on that original PDF page. Reloading must recover the same job without a duplicate charge.

Keep these constraints:

- English-language financial statements, USD, telecom sector.
- Existing three metrics: consolidated revenue, operating profit, profit attributable to owners of the reporting parent. Do not silently substitute EPS, comprehensive income, or a different attribution row.
- One PDF, one selected physical page per run. A conservative configurable default: maximum 10 MiB and 250 PDF pages. Validate what the deployed request path actually accepts; lower the advertised bound if necessary.
- Annual or interim statements; preserve each source interval and comparative column. "Three metrics" does not require exactly three facts when multiple legitimate periods are present.
- No arbitrary URL fetching, batch upload, OCR project, broad accounting support, chat, new provider, or new benchmark experiment.
- Reppo is not automatic. Upload processing is Docling + SERV + verification. Existing authorized evaluation controls remain separate.
- No fabricated outputs or claims that a new layout is verified when the current checker cannot establish its context.

This instruction explicitly extends the previous allowlisted-sources-only product scope to limited uploaded PDFs. It does NOT expand spending allowances, authorize new infrastructure purchases, or authorize unrestricted document ingestion.

## Read and preserve

Read applicable AGENTS.md, CLAUDE.md, brand.md, and current `docs/LIVE-DEPLOYMENT-STATUS.md`, `docs/JUDGE-WALKTHROUGH.md`, `docs/JUDGE-ACCEPTANCE-REPORT.md`, deployment and budget records. Prefer actual current behavior to old historical statements.

Current reported architecture is Vercel frontend with `/api/*` rewritten to the Railway API and durable Docling worker on a persistent volume. Preserve the functioning public URL, existing stored runs, the guided tour, immutable experiments, and ordinary registered-report processing.

Known code points to inspect:

- `backend/evi/api.py`: `session_and_origin`, document/source/parse routes, and public run/version/evidence routes.
- `backend/evi/corpus.py`, `db.py`, `jobs.py`, `worker.py`, parsing, capabilities, budget and certificate code.
- `src/api.ts`, `src/types.ts`, Workspace/Documents, PDF viewer and active-job recovery.
- `vercel.json`, Docker dependencies and any relevant proxy configuration.

The current write middleware expects JSON and limits declared request length to 4096 bytes. The prepared Caddy configuration also has a 64 KB body limit. Inspect the real deployed path; adding only a frontend file input will not work. Existing result/source routes are designed for public immutable corpus data, which is not a suitable default for arbitrary uploads.

## 1. Minimal user flow

Add "Upload your PDF" in Workspace and a clear entry from the guided path, alongside the registered report selector. Keep top navigation, Home first, current Evi design and English copy. No sidebar or workspace/account selector card.

1. Explain supported inputs and the size/page limits. State that the selected page and table context are sent to SERV when Process is clicked. Explain that results belong to this browser session and state the actual retention policy. Ask for no account or API key.
2. Accept a PDF through the same-origin backend upload route. Upload registers the source and reads its page count; it does not enqueue Docling or call SERV/Reppo.
3. Show the original PDF preview and a physical page-number selector, clearly distinguished from page numbers printed inside the PDF. Let the judge find and select the income-statement page. Default to page 1 for preview, but require an explicit selected-page confirmation before processing. Do not parse all pages to find it.
4. Optional issuer/title labels are user-supplied metadata, never evidence for dates, currency, attribution or scope. Do not invent an issuer publication URL for an uploaded file.
5. Process queues the existing pipeline for exactly that page. Show the actual job stage, selected-page coverage and whether the parse is fresh or reused.
6. On completion open the existing fact grid, original PDF anchors, context diagnostics, certificates and re-verification. Export retains source hash, physical page coverage, version/policy and source kind `user_upload`.

Show useful validation and failure states: too large, invalid/encrypted/unreadable PDF, invalid page, source unsupported, queue busy, execution disabled, budget exhausted, expired upload and unavailable layout. If the page has no usable financial table, stop before SERV where deterministically detectable; otherwise report unknown/unsupported honestly.

Do not claim automatic sector/language recognition unless actually implemented. Describe these as supported-input boundaries. Never relabel non-USD source amounts as USD or silently convert currencies.

## 2. Reuse the pipeline and source fidelity

Use additive, idempotent schema migrations. Preserve original bytes, SHA-256, physical page count and original filename as display metadata. Generate storage paths and internal IDs server-side; never use the client filename as a path.

Register uploaded sources with explicit source kind, session ownership, selected page and expiry. Avoid loading them into the globally public catalog. Extend current typed contracts deliberately; represent absent issuer URLs honestly instead of inserting a fictional external source link.

Reuse the worker, durable job chain, source-hash validation, Docling adapter, fact extraction, checker and certificate verifier. Cache identity must include source hash, selected page(s), parser/config and relevant policy, not just the document ID. A different selected page must not reuse the first page's parse. Avoid cross-session cache/result disclosure.

The original whole PDF remains the source. Do not replace it with a cropped PDF and accidentally shift physical page identity or bounding boxes. If an intermediate page extraction is necessary, preserve an explicit mapping back to original page coordinates.

Existing binding rules may be layout-specific. Apply their actual applicability criteria; do not hardcode the uploaded report's labels, values or expected answers to make it pass. Valid SERV output may remain unsupported by the checker. Emit unknown/conflicting/partial-context results as appropriate, and distinguish parse success, extraction success and source-support status.

PDF text and table content are untrusted model input, never instructions to change policies, reveal keys, fetch URLs, or execute tools. Keep existing revision safeguards.

## 3. Make upload access and resource limits real

Implement multipart upload as a narrow exception for the upload route only. Preserve origin checks, session cookies and the small JSON-body rule elsewhere. Do not globally relax the middleware or CORS. Bound bytes actually read, including chunked or false-length requests; reject oversized files without loading an unbounded body into RAM.

Validate PDF signature and successful bounded page-count inspection, not just extension or browser MIME. Reject encrypted/password-required PDFs for this release. Apply short validation limits, one active processing job as configured, and bounded Docling processing time. Rate-limit upload/storage separately so unused uploads cannot fill the disk. Add configurable per-session and global storage/file caps and show a useful refusal.

Use the existing same-origin Vercel-to-Railway route and verify its actual body limits and cookie behavior. Do not introduce object storage, direct browser provider credentials, base64 JSON, or a chunk-upload framework just to bypass an unverified proxy problem. If the supported size must be smaller for this route, implement a truthful lower limit and document it.

Ownership must cover EVERY path to an uploaded source or derivative: list/detail, PDF bytes, parses, runs, versions, evidence, certificates, re-verification, evaluation history, exports and job state. A second anonymous session guessing a document/fact/version ID must not retrieve it. Existing allowlisted public results remain public. Uploaded PDFs must never be placed in `public/`, git, public snapshots, benchmark exports or shared guided-tour records. Use private/no-store cache controls for session-protected responses.

Persist uploads on the existing volume outside web roots. Use a documented default retention of 24 hours, enforced by a bounded worker/startup cleanup path, with a message explaining expiry. Protect queued/running work from cleanup; expire related private data coherently. Cleanup must target only upload-owned records/files and must never touch the registered corpus or frozen experiments. Do not add a broad recursive deletion command.

Retain current paid-call gates, expiry/cumulative allowance rules where implemented, daily caps, atomic reservations and idempotency. New uploads share the SAME approved public budget; they do not create a new allowance. Upload itself uses no provider credits. A failed parse must not be reported as a completed SERV call. Unknown provider submissions must not be blindly repeated.

## 4. Verify the narrow end-to-end path

Run relevant existing backend/frontend tests and production build. Add focused tests for:

- A valid PDF, non-PDF, encrypted/malformed PDF, oversize request and selected page out of bounds.
- Route-specific multipart exception without weakening JSON/origin controls on other routes.
- Session isolation for sources AND derived results, plus unchanged access to public corpus results.
- Hash/page/config cache correctness, exactly one selected page passed to Docling, and no accidental paid call during upload.
- Upload/storage caps, scoped expiry cleanup and preservation of active jobs and original experiment artifacts.
- Reload/double-click idempotency and truthful unsupported/partial-context states.

For a real local integration check, upload a copy of an existing public report as an uploaded source and run a fresh local Docling page parse. Verify its source identity and page/coordinate mapping. Do not count this as an unseen benchmark or claim independent generalization from it. Use existing stubbed provider tests where appropriate; do not pass them off as live SERV evidence.

After deployment, use a clean browser on the public Vercel URL to upload and preview a real PDF, select a page, and verify ownership against a second session. A real uploaded-source SERV run is allowed ONLY if the existing explicit runtime approval covers it and budget remains. Use at most ONE such smoke run under that allowance; do not run Reppo automatically. If no valid allowance remains, complete all independent work and report the exact missing live-run verification rather than bypassing the gate.

For an authorized real run, reload mid-job and demonstrate the same job ID, one new provider submission, new immutable output, actual certificate states and highlights on the selected original page. An honest unsupported outcome is not verified accuracy; report it clearly. Do not keep spending until a pretty result appears.

Do not acquire planned holdout documents as upload test material. Preserve experimental freezes and record any newly inspected sources as development exposure. Do not rerun calibration or experiments.

## Deployment, delivery and finish

Reuse the existing authorized Vercel/Railway projects and persistent volume. Inspect and back up state before schema/deployment changes; use additive migrations and preserve rollback. Do not create a different account/project or buy infrastructure. Verify compatibility before routing traffic to the change.

Deliver working code, not just this plan. Update:

- `docs/JUDGE-UPLOAD.md`: limits, supported inputs, processing stages, ownership, retention and exact judge steps.
- Current judge walkthrough, acceptance report and deployment status.
- Config/env examples with non-secret upload limits.
- `artifacts/judge-upload/`: sanitized test results and screenshots, plus receipts only if a real paid run was authorized and completed.

Keep this release small. No new menus, framework migration, generic file manager, human-review project, new benchmark, or unrelated redesign. Implement the single-page upload slice, verify it, deploy using existing authorization, then stop.

Final report: public URL; exactly what judges can upload and test; fresh/reused Docling status; whether a real SERV run happened and its call count; Reppo usage; tests; evidence paths; current limits/retention; and any remaining blocker. Do not say judges can test their own files until the PUBLIC upload, preview and supported processing path have actually been verified, with any unpaid/unrun stage explicitly identified.
