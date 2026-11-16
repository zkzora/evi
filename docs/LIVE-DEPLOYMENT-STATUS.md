# Live deployment status (updated 2026-11-16, Railway backend)

## Current topology

| Layer | Where | State |
|---|---|---|
| Public entry (frontend) | **https://evi-lovat.vercel.app** (Vercel `zkzoras-projects/evi`) | SPA; `/api/*` is an external rewrite to Railway (same origin for the browser; HttpOnly SameSite=strict session cookie verified) |
| Backend | **https://evi-production-0473d93e.up.railway.app** (Railway project `reasonable-benevolence`, service `evi`, created manually by the user) | Dockerfile image built by Railway (first real build of the image); `entrypoint.sh all` = API + Docling worker in one container; volume `evi-volume` at `/data` (DB, artifacts, sources, model cache `HF_HOME=/data/models`) |
| Stored results | Railway volume | Seeded once from the verified `data/release-snapshot` (56 versions, 618 certificates, 11 evaluations); certificate re-verification passes on the server |
| Execution policy | Railway variables | `EVI_EXECUTION_ENABLED=false`; no SERV/Reppo keys set; caps SERV 3/day, Reppo 0/day, 1 active job, 2 jobs/session/hour |
| Readiness | `/api/v1/health`, `/api/v1/ready` | ready; worker **alive**; Docling **installed**; extraction/evaluation **unavailable (execution policy)** |

Verified from a clean browser via the Vercel URL: **26/26** (`artifacts/judge-release/judge-e2e-evi-lovat_vercel_app.json`), and directly on the Railway URL: 26/26. **No new provider calls**; no credits spent.

## Fixes made while bringing Railway up (all committed)

1. The image defaults to `all` (API + worker) on `$PORT`; `railway.toml` pins the Dockerfile build, the health check and 1 replica.
2. Seeding: the snapshot DB was excluded by `.dockerignore` (`**/*.sqlite3*`), which now has an exception. Seeding also runs when the DB has no stored results. Empty pre-seed state is moved aside to `/data/runs.preseed-*`, never deleted.
3. Line endings: hash-pinned evidence was stored LF by git but hashed as CRLF, so it failed verification on Linux. `.gitattributes` now stores `data/`, `artifacts/` and `public/evidence/` byte-for-byte. Without this, cloners could not replay either.
4. Cross-OS artifact paths: `backup.restore` did not split Windows paths on Linux. Fixed (`backup.rebase`, idempotent, runs on every boot), with a regression test. This changed frozen code, so the holdout freeze is now **holdout-2026-11-16-d** (a–c superseded; no source acquired).
5. PDF viewer: a cancelled PDF load (frequent through the proxy) is no longer a browser error.

## Still pending (needs your decision)

- **Live processing (acceptance level 2):** set `SERV_API_KEY` (and optionally `REPPO_API_KEY`) in Railway's variables yourself, then approve an allowance, e.g. 7 days, SERV ≤ 3/day (≈ $0.45 total estimated), Reppo 0–1/day (≤ 440 credits each). Then set `EVI_EXECUTION_ENABLED=true` and `EVI_GLOBAL_REPPO_EVALS_PER_DAY` accordingly. After that I run one real Process job, a reload test and the judge check.
- Railway cost: usage-based on the account that owns `reasonable-benevolence`; measure after a few days (estimate in the previous section of this file's history: ~$7–8/month of usage).

## Rollback

- **Frontend API routing:** revert `vercel.json`'s `/api/(.*)` destination to `/api/index` (archive function, still in the repo) and push.
- **Backend:** the Railway volume keeps the state; `python -m evi.backup create` before risky changes; restores go only into an empty directory.
