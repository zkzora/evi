# Live deployment status (updated 2026-11-16, Railway backend)

## Current topology

| Layer | Where | State |
|---|---|---|
| Public entry (frontend) | **https://evi-lovat.vercel.app** (Vercel `zkzoras-projects/evi`) | SPA; `/api/*` is an external rewrite to Railway (same origin for the browser; HttpOnly SameSite=strict session cookie verified) |
| Backend | **https://evi-production-0473d93e.up.railway.app** (Railway project `reasonable-benevolence`, service `evi`, created manually by the user) | Dockerfile image built by Railway (first real build of the image); `entrypoint.sh all` = API + Docling worker in one container; volume `evi-volume` at `/data` (DB, artifacts, sources, model cache `HF_HOME=/data/models`) |
| Stored results | Railway volume | Seeded once from the verified `data/release-snapshot` (56 versions, 618 certificates, 11 evaluations); certificate re-verification passes on the server |
| Execution policy | Railway variables | `EVI_EXECUTION_ENABLED=true` since 2026-11-16 (approved: 7 days, until 2026-11-23); SERV and Reppo keys set by the owner; caps SERV 3/day, Reppo 1/day, 1 active job, 2 jobs/session/hour |
| Readiness | `/api/v1/health`, `/api/v1/ready` | ready; worker **alive**; Docling **installed**; mode **live**; extraction and evaluation **available** within today's allowance |

Verified from a clean browser via the Vercel URL in live mode: **26/26**, three consecutive runs (`artifacts/judge-release/judge-e2e-evi-lovat_vercel_app.json`). Provider calls since go-live: **2 SERV extractions** (`artifacts/judge-release/live-1`, `live-2`), **0 Reppo evaluations**.

## Fixes made while bringing Railway up (all committed)

1. The image defaults to `all` (API + worker) on `$PORT`; `railway.toml` pins the Dockerfile build, the health check and 1 replica.
2. Seeding: the snapshot DB was excluded by `.dockerignore` (`**/*.sqlite3*`), which now has an exception. Seeding also runs when the DB has no stored results. Empty pre-seed state is moved aside to `/data/runs.preseed-*`, never deleted.
3. Line endings: hash-pinned evidence was stored LF by git but hashed as CRLF, so it failed verification on Linux. `.gitattributes` now stores `data/`, `artifacts/` and `public/evidence/` byte-for-byte. Without this, cloners could not replay either.
4. Cross-OS artifact paths: `backup.restore` did not split Windows paths on Linux. Fixed (`backup.rebase`, idempotent, runs on every boot), with a regression test. This changed frozen code, so the holdout freeze is now **holdout-2026-11-16-d** (a–c superseded; no source acquired).
5. PDF viewer: a cancelled load is released after it settles instead of terminating the PDF.js worker mid-parse (which threw "Worker was terminated" inside the worker).
6. Workspace restores an in-flight job after a page reload (found by the first live job).
7. `scripts/judge_e2e.py` no longer POSTs a parse when processing is live (it would have started a paid job).

## Still pending (needs your decision)

- **Live processing:** done (2026-11-16). Real job with reload recovery verified: `artifacts/judge-release/live-2/live-job.json`.
- **One Reppo evaluation from the public UI:** allowed (≤ 1/day) but not yet run.
- **End of allowance:** the server enforces daily caps but not the 7-day window. Set `EVI_EXECUTION_ENABLED=false` on or after 2026-11-23.
- Railway cost: usage-based on the account that owns `reasonable-benevolence`; measure after a few days (estimate in the previous section of this file's history: ~$7–8/month of usage).

## Rollback

- **Frontend API routing:** revert `vercel.json`'s `/api/(.*)` destination to `/api/index` (archive function, still in the repo) and push.
- **Backend:** the Railway volume keeps the state; `python -m evi.backup create` before risky changes; restores go only into an empty directory.
