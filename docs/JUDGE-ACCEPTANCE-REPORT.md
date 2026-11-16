# Judge acceptance report (2026-11-16)

Evidence levels:
- **public** — verified on https://evi-lovat.vercel.app from a clean headless browser;
- **local** — automated tests (isolated state; fakes where noted);
- **pending** — not executed.

**New provider calls made in this release: 0. Credits spent: 0.**

| Criterion | Status | Evidence |
|---|---|---|
| Home → Try Evi → nine-month observation checked as Full year → mismatch | public ✅ | `artifacts/judge-release/01-period-mismatch.png`; judge-e2e "Try Evi opens…": "The source reports 9 months, while you selected a full year." |
| Same observation with 9 months → match; unit mismatch (USD millions) → mismatch | public ✅ | `02-period-match.png`, `03-unit-mismatch.png` |
| Guest access; accurate readiness; useful disabled state | public ✅ | `04-processing-availability.png`: "Archive · stored results", Process disabled with inline reason; `/health` capabilities = archive/unavailable |
| Server refuses new processing when unavailable (JSON error) | public ✅ | judge-e2e: `503 execution_disabled`; unknown API route → JSON 404 |
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
| **New real Process job on a public host** (Docling + SERV, stages, reload recovery) | **pending** | Needs an approved durable host and public-use allowance (`docs/LIVE-DEPLOYMENT-STATUS.md`) |
| **New Reppo evaluation from the public UI** | **pending** | Needs a separate allowance (≤ 440 credits per evaluation) |
| Docker image build | done (Railway remote build) | Railway deployment `04b6a10`+ SUCCESS; API + worker running; Docling installed |
| Independent human reference review | **pending** | 0/48 (`data/references/review/review-sheet-references-v1.json`) |

Test totals in this release: backend **140 passed**; frontend **18 passed**; production build OK; public judge-e2e **26/26** (`artifacts/judge-release/judge-e2e-evi-lovat_vercel_app.json`).

Holdout: `holdout-2026-11-16-c` is the current freeze (a and b superseded by code changes before any source was acquired; see `artifacts/holdout/*/SUPERSEDED.md` and `exposure-addendum.md`).

## Update — Railway backend (2026-11-16)

https://evi-lovat.vercel.app now proxies `/api` to the Railway backend (API + Docling worker + persistent volume). Judge e2e 26/26 on the Vercel URL (two consecutive runs) and 26/26 on the Railway URL. Execution remains disabled; level 2 (a new real job) is still **pending** keys and an allowance.
