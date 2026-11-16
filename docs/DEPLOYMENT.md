# Deployment runbook (prepared 2026-11-16; not deployed)

## Shape

One host, one persistent local volume, three processes from one image:

| Process | Command | Role |
|---|---|---|
| `api` | `entrypoint.sh api` → uvicorn `evi.api:app` | `/api/v1/*` plus the built SPA with deep-link fallback (`EVI_STATIC_DIR=/app/dist`), same origin |
| `worker` | `entrypoint.sh worker` → `python -m evi.worker` | Durable jobs (Docling, SERV, Reppo). Leases are reclaimed after a crash. SIGTERM stops it after the current job. |
| `caddy` | `caddy:2` | HTTPS, security headers, 64 KB request cap, reverse proxy to `api:8000` |

Files: `Dockerfile`, `deploy/docker-compose.yml`, `deploy/Caddyfile`, `deploy/entrypoint.sh`, `deploy/production.env.example`, `.dockerignore`, `backend/requirements.lock` (frozen from the verified environment; torch from the CPU index in the image).

**SQLite:** keep API and worker on the **same host and the same local volume** (WAL mode). Do not put `/data` on NFS/SMB or other network storage, do not run multiple replicas, and do not point several hosts at copies of the database. Moving to Postgres would be a separate, deliberate migration; it isn't needed at this scale.

## Measured and estimated resources

| Item | Value | Basis |
|---|---|---|
| Docling cold parse of one statement page (new process incl. model load) | 157 s wall, **1.1 GB peak working set, 2.3 GB peak commit** | Measured 2026-11-16, Windows, 16 CPUs, att-2q2025 |
| Warm parses (models already loaded) | 51–208 s per statement page | Recorded parse durations |
| Docling/HF model cache | ~0.5 GB (keep on the `evi-models` volume; not re-downloaded per request) | Measured cache size |
| Data (DB + immutable artifacts) | 28 MB for 5 reports, 56 versions, 618 certificates | Measured |
| Image size | Not measured (no Docker on the preparing machine); estimated 2–3 GB with CPU torch | **Estimate** |
| Suggested host | ≥ 2 vCPU, **≥ 4 GB RAM** (6 GB worker limit in compose), ≥ 10 GB disk | **Estimate** from the measured peak plus headroom |

A short-lived serverless function is **not** a suitable host for the worker (long CPU-bound Docling runs, a durable lease loop, a local SQLite volume).

## Steps on an authorized host (not performed)

```
git clone <repo> evi && cd evi/deploy
cp production.env.example production.env      # fill on the server only; keep EVI_EXECUTION_ENABLED=false initially
export EVI_DOMAIN=<authorized domain>
docker compose build && docker compose up -d
curl -fsS https://$EVI_DOMAIN/api/v1/health     # liveness (does not imply provider readiness)
curl -fsS https://$EVI_DOMAIN/api/v1/ready      # database, sources, artifact storage, worker
```

**Seeding existing results:** run `python -m evi.backup create <dir>` locally, copy the folder to the host, then run `python -m evi.backup restore <backup> /data/runs /data/sources` into the **empty** volume. Restore verifies every hash and rebases the Docling artifact paths.

**Backups:** `docker compose run --rm api backup` uses SQLite's online backup API (safe while running) and writes artifacts, sources and a SHA-256 manifest. `python -m evi.backup verify <dir>` re-checks the hashes. Restores only go into an empty directory.

**Enabling public processing** (a separate decision; see `docs/BUDGET-SHEET.md`): set the provider keys and `EVI_EXECUTION_ENABLED=true` on the server, set `EVI_ALLOWED_ORIGINS=https://<domain>`, keep the conservative caps from the example env, and restart. Reviewers never enter keys.

## Public-use controls (server-side, existing)

- Anonymous HttpOnly SameSite=Strict session cookie; jobs are readable only by their own session.
- Writes must be same-origin JSON ≤ 4 KB; there is no CORS.
- Only registered public sources, verified by hash.
- Per-session hourly job cap; global daily SERV and Reppo caps recorded in `budget_ledger`; per-run revision and evaluation caps.
- Idempotent job keys; `submission_unknown` is never resubmitted.
- `EVI_EXECUTION_ENABLED=false` refuses new jobs (HTTP 503 `execution_disabled`), and the provider adapters refuse to submit, independently of the browser.

## Local production smoke test (performed)

The test uses copied state (`python -m evi.backup create` → `restore` into a scratch directory), port 8100, `EVI_STATIC_DIR=dist`, execution disabled and keys blank. It runs `scripts/prod_smoke.py`. Results are in `artifacts/release-smoke/smoke.json` and `smoke-quick.json` (after an API and worker restart).
