# Live deployment status (2026-11-16)

## What is deployed

| Item | State |
|---|---|
| Public URL | **https://evi-lovat.vercel.app** (Vercel project `zkzoras-projects/evi`, Git-connected to `zkzora/evi`; every push to `main` deploys) |
| Routing | Vercel static SPA (deep-link fallback to `index.html`) + `/api/*` → Python function `api/index.py` (same origin; HttpOnly session cookie and same-origin write checks unchanged) |
| Backend mode | **Archive (acceptance level 1 only):** stored results from `data/release-snapshot` (verified backup), certificate re-verification, published experiments. `EVI_EXECUTION_ENABLED` is forced off; no provider keys; **no Docling worker** |
| Readiness | `/api/v1/health` → `capabilities`: stored results available; source verification available; extraction and evaluation **unavailable** ("read-only archive: no Docling worker and no provider keys"). `/api/v1/ready` → ready |
| Container image | **Not built** on the preparing machine (Docker is not installed). `Dockerfile` + `deploy/` are prepared; a host that builds Dockerfiles (e.g. Railway) would build it remotely. A non-container production-mode smoke test passed earlier and is not a container test. |
| New provider calls during this release | **0** (provider-call count 162 before and after; no credits spent) |

## Live processing (acceptance level 2): not yet possible

This needs a host that runs the Docling worker next to the API with one persistent local volume, plus an explicit public-use allowance. No authorized durable host exists:
- **Railway:** the CLI on this machine is logged in to a different account (not `zkzora`), with one existing project, `steadfast-truth`, of unknown purpose. Nothing was created or changed there.
- **Docker:** not installed locally.
- **Vercel:** cannot host the worker.

### Proposed host (needs your approval; nothing purchased)

Railway (Dockerfile build, one service, one volume), using `deploy/entrypoint.sh all`, which runs API and worker in one container so they share the SQLite volume. A Railway volume attaches to one service.
- **Pricing** (docs.railway.com, read 2026-11-16): Hobby $5/month including $5 of usage; RAM $10/GB-month; CPU $20/vCPU-month; volume $0.15/GB-month.
- **Estimate:** about 0.6 GB average RAM and a 2 GB volume, roughly **$7–8/month** of usage, so ~$2–3 above the $5 included. This is an estimate until measured on the host; a parse peaks at ~2.3 GB committed for a few minutes.
- Any other single VM (≥ 4 GB RAM, local disk) with `deploy/docker-compose.yml` works equally.

### Proposed public-use allowance (needs your approval; nothing configured)

| Parameter | Proposed |
|---|---|
| Duration | 7 days from enablement, then `EVI_EXECUTION_ENABLED=false` |
| SERV calls | `EVI_GLOBAL_SERV_CALLS_PER_DAY=3` (≤ 21 total) — ≈ $0.02 per extraction at the published gpt-5.4-mini price (~5.6k input / 2.1k output tokens): **≤ $0.45 estimated** |
| Reppo evaluations | `EVI_GLOBAL_REPPO_EVALS_PER_DAY=1` (≤ 7 × 440 = **≤ 3,080 credits**), packet v2 — or 0 if you prefer no new Reppo spend |
| Concurrency and per-session limits | `EVI_MAX_ACTIVE_JOBS=1`, `EVI_SESSION_JOBS_PER_HOUR=2`, `EVI_MAX_REVISIONS_PER_RUN=1`, `EVI_MAX_EVALUATIONS_PER_RUN=1` |
| Verification run (by me, after deploy) | 1 Process job on a registered report (1 SERV call; cached parse reused unless the volume is fresh) + reload/duplicate-click check; optionally 1 evaluation (440 credits) |

Keys stay in the host's secret store (never in chat, `VITE_` variables or the repo). This allowance is separate from the unexecuted Reppo calibration (≤ 5,280 credits) and the holdout run (≤ 3,520 credits).

## Steps once host and allowance are approved

1. Create the service from `zkzora/evi` (Dockerfile), attach a volume at `/data`, set the start command to `all`, set the secrets and the limits above, and keep `EVI_EXECUTION_ENABLED=false` at first.
2. Seed state: `python -m evi.backup restore <data/release-snapshot> /data/runs /data/sources` into the empty volume (hash-verified).
3. Read-only smoke test against the host URL: `scripts/prod_smoke.py`, `scripts/judge_e2e.py`.
4. Enable execution with the limits; run one Process job; verify stages, reload recovery and no duplicate calls; re-run `judge_e2e.py`.
5. Routing: either point judges at the host URL, or add a Vercel external rewrite of `/api/(.*)` to the host (`EVI_ALLOWED_ORIGINS` must include `https://evi-lovat.vercel.app`). Change public routing **only after** steps 3–4 pass.

**Rollback:** remove the rewrite or link. The Vercel archive keeps working independently. Backups are created with `python -m evi.backup create` and restored only into an empty directory.
