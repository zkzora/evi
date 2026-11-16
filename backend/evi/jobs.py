"""Durable job queue (SQLite) with leases, bounded retries, restart recovery and budget accounting."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone

from . import db
from .config import settings

TERMINAL = {"succeeded", "failed", "cancelled", "blocked", "outcome_unknown"}


class Conflict(Exception):
    pass


class BudgetExceeded(Exception):
    pass


def _ts(offset_s: float = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat(timespec="milliseconds")


def enqueue(conn: sqlite3.Connection, kind: str, payload: dict, *, session_id: str | None,
            idempotency_key: str | None = None, parent_job_id: str | None = None, message: str = "Queued.") -> dict:
    if idempotency_key:
        existing = db.row(conn, "SELECT * FROM jobs WHERE idempotency_key=?", idempotency_key)
        if existing and existing["status"] not in ("failed", "cancelled"):
            return dict(existing)
        if existing:  # a failed attempt may be retried explicitly under a fresh key
            idempotency_key = f"{idempotency_key}#retry-{db.new_id('r')}"
    job_id = db.new_id("job")
    conn.execute("INSERT INTO jobs (job_id, kind, status, session_id, payload_json, idempotency_key, message, created_at, updated_at, parent_job_id) "
                 "VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (job_id, kind, "queued", session_id, db.dumps(payload), idempotency_key, message, db.now(), db.now(), parent_job_id))
    return dict(db.row(conn, "SELECT * FROM jobs WHERE job_id=?", job_id))


def claim(conn: sqlite3.Connection, worker_id: str) -> sqlite3.Row | None:
    """Atomically lease the oldest runnable job. Expired leases (crashed worker) become runnable again."""
    with db.tx(conn):
        j = db.row(conn, "SELECT * FROM jobs WHERE (status='queued' AND (not_before IS NULL OR not_before<=?)) "
                         "OR (status='running' AND lease_until<?) ORDER BY created_at LIMIT 1", _ts(), _ts())
        if not j:
            return None
        recovered = j["status"] == "running"
        if recovered and j["attempts"] >= settings.job_max_attempts:
            # The worker died while holding this job repeatedly (e.g. killed for memory during a Docling parse).
            # Stop the crash loop: fail it with an honest reason instead of leasing it again.
            msg = ("The processing worker stopped repeatedly while running this job (likely out of memory on this server). "
                   "It was not retried again. Stored results remain available.")
            conn.execute("UPDATE jobs SET status='failed', message=?, error_json=?, lease_until=NULL, updated_at=? WHERE job_id=?",
                         (msg, db.dumps({"code": "worker_crash_loop", "message": msg}), db.now(), j["job_id"]))
            return None
        conn.execute("UPDATE jobs SET status='running', attempts=attempts+1, lease_until=?, updated_at=?, message=? WHERE job_id=?",
                     (_ts(settings.worker_lease_s), db.now(),
                      "Recovered after a worker restart." if recovered else "Running.", j["job_id"]))
        return db.row(conn, "SELECT * FROM jobs WHERE job_id=?", j["job_id"])


def heartbeat(conn, job_id: str, message: str | None = None) -> None:
    conn.execute("UPDATE jobs SET lease_until=?, updated_at=?, message=COALESCE(?, message) WHERE job_id=? AND status='running'",
                 (_ts(settings.worker_lease_s), db.now(), message, job_id))


def finish(conn, job_id: str, status: str, message: str, *, result: dict | None = None, error: dict | None = None,
           next_job_id: str | None = None) -> None:
    conn.execute("UPDATE jobs SET status=?, message=?, result_json=?, error_json=?, lease_until=NULL, updated_at=?, "
                 "next_job_id=COALESCE(?, next_job_id) WHERE job_id=?",
                 (status, message, db.dumps(result) if result else None, db.dumps(error) if error else None, db.now(),
                  next_job_id, job_id))


def retry_later(conn, job_id: str, message: str, delay_s: float) -> None:
    conn.execute("UPDATE jobs SET status='queued', lease_until=NULL, not_before=?, message=?, updated_at=? WHERE job_id=?",
                 (_ts(delay_s), message, db.now(), job_id))


def public_view(conn, job: sqlite3.Row) -> dict:
    """Follow automatic continuations so one user action reports its real current stage."""
    chain = [job]
    while chain[-1]["next_job_id"]:
        nxt = db.row(conn, "SELECT * FROM jobs WHERE job_id=?", chain[-1]["next_job_id"])
        if not nxt:
            break
        chain.append(nxt)
    tail = chain[-1]
    return {"job_id": job["job_id"], "kind": job["kind"], "status": tail["status"], "stage": tail["kind"],
            "message": tail["message"], "error": json.loads(tail["error_json"]) if tail["error_json"] else None,
            "result": json.loads(tail["result_json"]) if tail["result_json"] else None,
            "stages": [{"job_id": c["job_id"], "kind": c["kind"], "status": c["status"], "message": c["message"],
                        "updated_at": c["updated_at"]} for c in chain],
            "document_id": json.loads(job["payload_json"]).get("document_id"),
            "first_stage_result": json.loads(job["result_json"]) if job["result_json"] else None,
            "attempts": tail["attempts"], "created_at": job["created_at"], "updated_at": tail["updated_at"]}


# ---------------------------------------------------------------- budgets

def _day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def spend(conn, scope: str, key: str, limit: int, units: int = 1) -> None:
    """Durable budget accounting. Call inside a transaction before the expensive operation."""
    used = db.row(conn, "SELECT COALESCE(SUM(units),0) n FROM budget_ledger WHERE scope=? AND key=?", scope, key)["n"]
    if used + units > limit:
        raise BudgetExceeded(f"The {scope.replace('_', ' ')} budget ({limit}) is exhausted for {key}.")
    conn.execute("INSERT INTO budget_ledger VALUES (?,?,?,?,?)", (db.new_id("bud"), scope, key, units, db.now()))


def daily_key() -> str:
    return _day()


def session_rate_check(conn, session_id: str) -> None:
    since = _ts(-3600)
    n = db.row(conn, "SELECT COUNT(*) n FROM jobs WHERE session_id=? AND created_at>=? AND parent_job_id IS NULL", session_id, since)["n"]
    if n >= settings.session_jobs_per_hour:
        raise BudgetExceeded(f"This browser session started {n} jobs in the last hour (limit {settings.session_jobs_per_hour}).")
