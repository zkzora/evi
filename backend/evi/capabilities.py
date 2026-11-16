"""Capability-based readiness (2026-11-16). Connectivity alone never means processing readiness.

Computed from: database, registered source bytes and Docling artifacts, the server execution switch, a recent worker
heartbeat, configured provider access (presence only; no paid health-check call), the active job queue, and today's
durable budget ledger. Reppo availability never blocks a permitted Docling/SERV extraction. The same function drives
the /health response and the server-side refusal of new jobs, so the UI cannot claim more than the server allows.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import db
from .config import settings
from .corpus import source_path

REPPO_CREDITS_PER_EVAL = 440   # agents.md, read 2026-11-16


def max_active_jobs() -> int:
    try:
        return int(os.environ.get("EVI_MAX_ACTIVE_JOBS", "2"))
    except ValueError:
        return 2


def _worker_alive(c) -> bool:
    r = db.row(c, "SELECT MAX(seen_at) t FROM worker_heartbeats")
    return bool(r and r["t"] and datetime.fromisoformat(r["t"]) > datetime.now(timezone.utc) - timedelta(seconds=30))


def _used_today(c, scope: str) -> int:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return db.row(c, "SELECT COALESCE(SUM(units),0) n FROM budget_ledger WHERE scope=? AND key=?", scope, day)["n"]


def active_jobs(c) -> int:
    return db.row(c, "SELECT COUNT(*) n FROM jobs WHERE status IN ('queued','running') AND parent_job_id IS NULL")["n"]


def compute(c) -> dict:
    docs = db.rows(c, "SELECT * FROM documents")
    parses = db.rows(c, "SELECT artifact_path FROM parses")
    sources_ok = bool(docs) and all(source_path(d).exists() for d in docs)
    artifacts_ok = bool(parses) and all(Path(p["artifact_path"]).exists() for p in parses)
    versions = db.row(c, "SELECT COUNT(*) n FROM versions")["n"]
    worker = _worker_alive(c)
    ex = settings.execution_enabled
    serv, reppo = bool(settings.serv_api_key), bool(settings.reppo_api_key)
    active = active_jobs(c)
    serv_used, reppo_used = _used_today(c, "serv_calls_global"), _used_today(c, "reppo_evals_global")
    serv_left = max(settings.global_serv_calls_per_day - serv_used, 0)
    reppo_left = max(settings.global_reppo_evals_per_day - reppo_used, 0)

    def state(provider_ok: bool, provider: str, left: int) -> tuple[str, str]:
        if not ex:
            return "unavailable", "New processing is disabled on this server (execution policy)."
        if not worker:
            return "unavailable", "No processing worker is running."
        if not provider_ok:
            return "unavailable", f"{provider} access is not configured on the server."
        if left <= 0:
            return "budget_exhausted", f"Today's {provider} allowance on this server has been used."
        if active >= max_active_jobs():
            return "busy", "Other jobs are running; try again shortly. Stored results remain available."
        return "available", f"{provider} calls are allowed within today's server allowance."

    ext_state, ext_reason = state(serv, "SERV", serv_left)
    ev_state, ev_reason = state(reppo, "Reppo", reppo_left)
    return {
        "mode": "live" if ex else "archive",
        "stored_results": {"available": versions > 0, "versions": versions},
        "source_verification": {"available": sources_ok and artifacts_ok,
                                "reason": "Recomputes certificates from registered PDF bytes and Docling artifacts; no provider call."
                                if sources_ok and artifacts_ok else "Registered source or Docling artifact files are missing."},
        "extraction": {"state": ext_state, "reason": ext_reason, "active_jobs": active, "max_active_jobs": max_active_jobs(),
                       "serv_calls_left_today": serv_left},
        "evaluation": {"state": ev_state, "reason": ev_reason, "reppo_evaluations_left_today": reppo_left,
                       "credits_per_evaluation": REPPO_CREDITS_PER_EVAL},
    }


def require(c, which: str) -> None:
    """Server-side gate for new paid work. Raises (status, code, message) via ValueError tuple semantics."""
    cap = compute(c)[which]
    if cap["state"] != "available":
        code = {"busy": "busy", "budget_exhausted": "budget_exhausted"}.get(cap["state"], "execution_disabled")
        status = 429 if code in ("busy", "budget_exhausted") else 503
        raise CapabilityRefused(status, code, cap["reason"])


class CapabilityRefused(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def dumps(x) -> str:
    return json.dumps(x)
