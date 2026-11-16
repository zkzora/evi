# Upload your own PDF (judges)

> **Status 2026-11-16 (VPS backend):** verified end to end on the public site: upload → fresh Docling parse of the selected page → one SERV extraction → 6/6 supported certificates, highlights on the original page, re-verification, reload recovery and second-session isolation (`artifacts/judge-upload/public-upload.json`). The earlier Railway attempts failed on its 1 GB memory limit (`public-upload-attempt*.json`).

Public site: **https://evi-lovat.vercel.app**. No login and no API key.

## What you can upload

| | |
|---|---|
| Input | One PDF of a public, English-language **telecom** financial report in **USD** that contains an income statement (annual or interim) |
| Size | At most **10 MiB** (verified through the public Vercel → Railway route: 9.5 MiB accepted, 12 MiB refused with a clear message) |
| Pages | At most **250** physical pages |
| Not accepted | Encrypted or password-protected PDFs, non-PDF files, scanned pages that need OCR |
| Per browser session | 3 active uploads, 5 uploads per hour; server-wide storage is capped and refused clearly when full |
| Metrics | Consolidated revenue, operating profit (operating income), net income attributable to the reporting parent. No EPS, comprehensive income or other substitutes |

These are supported-input **boundaries**, not automatic detection: Evi does not detect sector or language, does not OCR, and never converts or relabels currencies.

## Steps (about 2 minutes plus processing time)

1. Open https://evi-lovat.vercel.app/workspace?upload=1 (or **Workspace → Upload your PDF**, or the guided tour's step 2 link). Read the limits, choose the PDF, optionally add a label. The label is shown only to you and is never used as evidence.
2. Upload. The server checks the `%PDF-` signature, size and encryption, counts the physical pages and stores the file. **Upload calls no provider and starts no job.**
3. In **Physical page**, enter the PDF's own page index of the income statement (what the viewer shows as "Physical page N"), not the number printed on the page. The preview jumps to that page so you can check it.
4. Tick **"Page N is the income statement"** and press **Process page N**. The job shows its real stages:
   - **Parse (Docling)**: exactly that one page, fresh or reused (labelled);
   - **columns**: Evi reads the interval length and year of each column from the parsed header cells with its existing binding rules (`upload-columns-v1`: current and prior year per interval). If none can be read on a metric row, the job **stops before SERV** with "Unsupported layout or wrong page: no SERV call was made";
   - **Extract (SERV) + checks**: one SERV call with that page's text and table cells, then the support certificates.
   Reloading the page brings back the same job; nothing is resubmitted.
5. Inspect the result: fact grid, highlights on the original page, certificate states (supported / unresolved / contradicted), **Re-verify from source**, and CSV/JSON export (with `source_kind=user_upload`, source SHA-256, physical page and policy version). An unresolved or partial-context result is reported as such; it is not a failure of the upload and is not counted as accuracy.

Reppo is never called automatically. The separate **Evaluate this version** control on Feedback works for your own upload under the same allowance.

## Privacy, ownership and retention

- The PDF and everything derived from it (parses, runs, versions, evidence, certificates, evaluations, job state, exports) belong to the uploading browser session. Any other session gets **404** for every one of those IDs. Responses are `Cache-Control: private, no-store`.
- Files are stored on the server's persistent volume outside every web root, never in `public/`, git, snapshots or benchmark exports.
- **Retention: 24 hours** after upload. The worker deletes expired uploads and only their own records and files every 5 minutes (skipping uploads with queued or running jobs). After expiry the owner sees "This uploaded PDF expired (24 h retention)".
- What leaves the server: when you press Process, the selected page's Docling text and table cells are sent to SERV (`gpt-5.4-mini`).

## Cost and limits

Processing an upload uses the **same approved public allowance** as every other paid request (no new budget): per-request reservation before sending, 21 SERV calls in total for the allowance `public-2026-11-16`, at most 3 per day site-wide, 1 active job, 2 jobs per browser session per hour. When the allowance is used, Process is disabled with the reason; uploading, previewing and stored results keep working.

## Configuration (non-secret)

`EVI_UPLOAD_MAX_BYTES` (10485760), `EVI_UPLOAD_MAX_PAGES` (250), `EVI_UPLOAD_RETENTION_HOURS` (24), `EVI_UPLOAD_PER_SESSION_ACTIVE` (3), `EVI_UPLOAD_PER_SESSION_PER_HOUR` (5), `EVI_UPLOAD_GLOBAL_FILES` (100), `EVI_UPLOAD_GLOBAL_BYTES` (104857600), `EVI_UPLOAD_MIN_FREE_BYTES` (67108864). See `backend/.env.example`.

## Implementation notes

- Route: `POST /api/v1/uploads` (multipart, the only non-JSON write; origin check kept; body read with a hard cap even for chunked or mis-declared requests), `POST /api/v1/uploads/{id}/process` with `{page, confirmed: true}`.
- Cache identity for uploads = source SHA-256 + selected page + parser/config + the upload's own ID, so another page or another session never reuses a parse. Registered-corpus cache keys are unchanged.
- The original whole PDF stays the source: Docling receives `page_range=(N, N)` on the original file, so physical page numbers and coordinates map back directly (no cropped copy).
- Schema changes are additive (`documents.source_kind/owner_session/expires_at/original_name`, `upload_targets`). The container takes a one-time backup on the volume (`/data/backups`) before the first boot of this schema.
