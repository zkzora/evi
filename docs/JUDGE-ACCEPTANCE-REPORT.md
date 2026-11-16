# Judge acceptance report (2026-11-16)

Evidence levels:
- **public** — verified on https://evi-lovat.vercel.app from a clean headless browser;
- **local** — automated tests (isolated state; fakes where noted);
- **pending** — not executed.

**Provider calls since processing went live (2026-11-16): 2 SERV extractions (Docling parse reused), 0 Reppo evaluations.** The stored results and experiments below are unchanged.

| Criterion | Status | Evidence |
|---|---|---|
| Home → Try Evi → nine-month observation checked as Full year → mismatch | public ✅ | `artifacts/judge-release/01-period-mismatch.png`; judge-e2e "Try Evi opens…": "The source reports 9 months, while you selected a full year." |
| Same observation with 9 months → match; unit mismatch (USD millions) → mismatch | public ✅ | `02-period-match.png`, `03-unit-mismatch.png` |
| Guest access; accurate readiness; useful disabled state | public ✅ | Archive mode verified before go-live ("Archive · stored results", Process disabled with inline reason); now `/health` mode=live and the pill reads "Live processing available" (`04-processing-availability.png`) |
| Server refuses new processing when unavailable (JSON error) | public ✅ (archive mode) | judge-e2e before go-live: `503 execution_disabled`. When live, the check no longer POSTs (it would start a paid job). Unknown API route → JSON 404 |
| Busy / budget-exhausted / own-job-returned / Reppo-down-doesn't-block-extraction | local ✅ | `backend/tests/test_capabilities.py` (5) |
| Stored results labelled with original UTC timestamps (not presented as re-runs) | public ✅ | judge-e2e: "Stored result · run created 2026-11-15 22:59 UTC · version ver_3f60316ec62f_5 created 2026-11-15 23:10 UTC … not re-run" |
| PDF anchors across layouts incl. FY2024 offset coordinates | public ✅ | `05-verizon-3q-evidence.png`, `06-verizon-fy2024-offset.png` (highlight at 0.654, 0.192 of page = revenue cell) |
| Certificate re-verification from registered source | public ✅ | judge-e2e "certificate re-verifies…" |
| AT&T partial context, no guessed dates | public ✅ | `07-att-partial-context.png`: "Supported · dates not printed" |
| Deep links survive reload and menu navigation | public ✅ | judge-e2e checks |
| Export provenance (source URL, version, coverage) | public ✅ | judge-e2e CSV check |
| Evaluation lineage; honest zero state for an unevaluated version | public ✅ | `08-feedback-history.png`: 11 rows, 11 evaluated-version links |
| Published experiments with null Reppo finding, provisional labels, 0/48 review, exp-b as development evidence | public ✅ | `09-benchmark.png`; `/api/v1/experiments` (schema `evi.public-experiments/1`, derived from artifacts; `backend/tests/test_public_evidence.py`) |
| No secrets in served HTML/JS | public ✅ | judge-e2e bundle scan |
| No browser errors; usable small screen | public ✅ | judge-e2e; `10-mobile-*.png` (no horizontal scroll) |
| Original experiments unchanged; replay read-only | local ✅ | replay-v2: exp-a 288/288 (binding-v2), exp-b 288/288 (binding-v3), VERIFIED; versions identical to snapshot; provider-call count 162 |
| Worker restart/resumption, idempotent clicks, unknown Reppo submission not resubmitted | local ✅ | `test_faults.py`, `test_pipeline.py`, `test_capabilities.py` (fakes; no provider calls) |
| New real Process job on a public host (Docling + SERV, stages, reload recovery) | public ✅ | `artifacts/judge-release/live-2/live-job.json`: job `job_db0f4f9931a94bb18874` on att-3q2025, reload mid-job restored the same job, one POST only, run `run_8c37343f480e4b37b967` → version `ver_8c37343f480e_1` (12 facts, 12 certificates). Docling parse **reused** (cached parse of page 2); SERV extraction new. First attempt `live-1` (job `job_4edfcff91b434e92b56e`) found the UI did not restore a job after reload; fixed in `6415e04` |
| **New Reppo evaluation from the public UI** | **pending** | Allowed (≤ 1/day, ≤ 7 in total, 440 credits each); not yet executed |
| Spending allowance enforced server-side (window, cumulative SERV/Reppo limits, atomic reservation, unknown outcomes never repeated, restart-safe) | local ✅ + public ✅ | `backend/tests/test_allowance.py` (10 tests, fake transports, no provider calls; `artifacts/allowance/test-allowance.txt`): no allowance → refused before any request; not-started and expired windows refused; no end date → only cumulative limits; retries count, connect errors released; SERV read timeout = unknown, counted, not retried; open reservation after a crash blocks a repeat; 24 concurrent reservers vs limit 5 → exactly 5; usage survives restart; pre-ledger calls backfilled once; API refuses with 403 `allowance_expired` / `allowance_exhausted` while documents stay readable. Production `/health` (`artifacts/allowance/health-after-deploy.json`): allowance `public-2026-11-16`, SERV 2/21 used, Reppo 0/7 |
| Docker image build | done (Railway remote build) | Railway deployment `04b6a10`+ SUCCESS; API + worker running; Docling installed |
| Independent human reference review | **pending** | 0/48 (`data/references/review/review-sheet-references-v1.json`) |

Test totals in this release: backend **151 passed**; frontend **19 passed**; production build OK; public judge-e2e **26/26** in live mode, three consecutive runs (`artifacts/judge-release/judge-e2e-evi-lovat_vercel_app.json`).

Holdout: `holdout-2026-11-16-e` is the current freeze (a–d superseded by code changes before any source was acquired; see `artifacts/holdout/*/SUPERSEDED.md` and `exposure-addendum.md`).

## Update — Railway backend (2026-11-16)

https://evi-lovat.vercel.app now proxies `/api` to the Railway backend (API + Docling worker + persistent volume). Judge e2e 26/26 on the Vercel URL (two consecutive runs) and 26/26 on the Railway URL. Execution remains disabled; level 2 (a new real job) is still **pending** keys and an allowance.

## Update — live processing (2026-11-16)

The owner set `SERV_API_KEY` and `REPPO_API_KEY` in Railway and approved the allowance: 7 days, SERV ≤ 3/day, Reppo ≤ 1/day, 2 jobs/session/hour. `EVI_EXECUTION_ENABLED=true`. Two real SERV extractions ran from the public UI (above). The owner then removed the 7-day end date (judging lasts more than a week); total spend stays bounded by the totals of the original approval (7 × 3 = 21 SERV, 7 × 1 = 7 Reppo); see the next section.

## Update — spending allowance enforcement (2026-11-16)

The approved allowance is now the server-side authority for every paid request (public jobs, revisions, evaluations, smoke tests, experiments and retries). The owner's values, set as Railway variables:

| Variable | Value |
|---|---|
| `EVI_ALLOWANCE_ID` | `public-2026-11-16` |
| `EVI_ALLOWANCE_START` | `2026-11-16T08:00:00Z` (before the first live job, so both live SERV calls count) |
| `EVI_ALLOWANCE_END` | empty: no automatic end (owner's decision; judging lasts more than a week) |
| `EVI_ALLOWANCE_SERV_CALLS` | 21 in total (the approved 3/day × 7 days; not expanded) |
| `EVI_ALLOWANCE_REPPO_EVALS` | 7 in total (1/day × 7 days; at most 3,080 credits) |

The daily caps (SERV 3, Reppo 1) still apply. Each SERV request and Reppo submission reserves one unit in a `BEGIN IMMEDIATE` SQLite transaction **before** the HTTP request. Only a provable connect failure releases it. A read timeout, a dropped connection, or a reservation left open by a crash is an unknown outcome: it counts, and the job ends `outcome_unknown` without being repeated. When the allowance is used up (or a future end date passes), new paid work is refused with 403 and the UI shows "Processing allowance used / ended · stored results available" with the reason. Stored results and source re-verification are unaffected. Provider calls made in this step: **0**.
