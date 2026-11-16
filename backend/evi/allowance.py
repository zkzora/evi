"""Spending allowance (2026-11-16): the owner-approved authority for every paid provider request.

Configured by the owner on the host, never by the app:
  EVI_ALLOWANCE_ID            e.g. public-2026-11-16
  EVI_ALLOWANCE_START         ISO-8601 UTC; no paid request before it
  EVI_ALLOWANCE_END           optional ISO-8601 UTC; empty = no time limit (the owner chose no automatic end; the
                              cumulative limits below still bound total spend)
  EVI_ALLOWANCE_SERV_CALLS    cumulative SERV requests for the whole allowance
  EVI_ALLOWANCE_REPPO_EVALS   cumulative Reppo evaluation submissions for the whole allowance

Rules:
- Every SERV request and every Reppo submission (jobs, revisions, smoke tests, experiments, retries) reserves one unit
  in a BEGIN IMMEDIATE transaction BEFORE the HTTP request. Concurrent reservations are serialised by SQLite, so the
  cumulative limit cannot be overshot by racing workers or processes.
- A reservation is released only when the request provably never left (connect error). Everything else counts,
  including HTTP errors and unknown outcomes.
- A reservation still open from an earlier attempt of the same job means the earlier submission's outcome is unknown
  (e.g. the worker died mid-request). It is never repeated automatically.
- No allowance configured = no paid work (fail closed). Reppo polling is free and not counted.
- Provider calls made inside the window before this ledger existed are backfilled once, so they count too.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

from . import db
from .jobs import BudgetExceeded

PROVIDERS = ("serv", "reppo")
_LIMIT_ENV = {"serv": "EVI_ALLOWANCE_SERV_CALLS", "reppo": "EVI_ALLOWANCE_REPPO_EVALS"}


class AllowanceRefused(BudgetExceeded):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


class UnknownPriorSubmission(Exception):
    """An earlier attempt of this job reserved a unit and never settled: its outcome is unknown."""


@dataclass(frozen=True)
class Allowance:
    allowance_id: str
    start: datetime
    end: datetime | None
    limits: dict


def _parse(ts: str) -> datetime:
    d = datetime.fromisoformat(ts.strip().replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def config() -> Allowance | None:
    """Read at call time (not import time) so the owner's host variables are the only authority."""
    aid = os.environ.get("EVI_ALLOWANCE_ID", "").strip()
    start = os.environ.get("EVI_ALLOWANCE_START", "").strip()
    if not aid or not start:
        return None
    try:
        end_raw = os.environ.get("EVI_ALLOWANCE_END", "").strip()
        limits = {p: int(os.environ.get(_LIMIT_ENV[p], "0")) for p in PROVIDERS}
        return Allowance(aid, _parse(start), _parse(end_raw) if end_raw else None, limits)
    except ValueError:
        return None   # malformed configuration fails closed


def _iso(d: datetime | None) -> str | None:
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if d else None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _backfill(conn, a: Allowance) -> None:
    """Once per allowance: count paid calls already made inside the window (before this ledger existed).
    Caller holds the write lock."""
    if db.row(conn, "SELECT 1 FROM allowance_backfills WHERE allowance_id=?", a.allowance_id):
        return
    calls = db.rows(conn, "SELECT call_id, provider, purpose, job_id, created_at FROM provider_calls WHERE created_at>=? AND "
                          "((provider='serv') OR (provider='reppo' AND purpose='submit' AND outcome!='connect_error')) "
                          "ORDER BY created_at", _iso(a.start).replace("Z", "+00:00"))
    n = 0
    for c in calls:
        if a.end and _parse(c["created_at"]) >= a.end:
            continue
        conn.execute("INSERT INTO allowance_reservations VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (db.new_id("res"), a.allowance_id, c["provider"], c["purpose"], c["job_id"], 1, "backfilled",
                      c["call_id"], c["created_at"], c["created_at"]))
        n += 1
    conn.execute("INSERT INTO allowance_backfills VALUES (?,?,?)", (a.allowance_id, n, db.now()))


def _used(conn, aid: str, provider: str) -> int:
    return db.row(conn, "SELECT COALESCE(SUM(units),0) n FROM allowance_reservations WHERE allowance_id=? AND provider=? "
                        "AND status!='released'", aid, provider)["n"]


def _check(a: Allowance | None, used: int, provider: str, now: datetime) -> tuple[str, str] | None:
    """(code, reason) when new paid work is not allowed, else None."""
    name = "SERV" if provider == "serv" else "Reppo"
    if a is None:
        return "no_allowance", "No approved spending allowance is configured on this server, so no paid work can start."
    if now < a.start:
        return "allowance_not_started", f"The approved spending allowance starts at {_iso(a.start)}."
    if a.end and now >= a.end:
        return "allowance_expired", f"The approved spending allowance ended at {_iso(a.end)}. Stored results remain available."
    if used >= a.limits[provider]:
        return "allowance_exhausted", (f"The approved {name} allowance ({a.limits[provider]} in total) has been used. "
                                       "Stored results remain available.")
    return None


def status(conn) -> dict:
    """Read-only view for /health and the UI. Never writes (the backfill happens at the first reservation)."""
    a, now = config(), _now()
    out = {"configured": a is not None}
    if a is None:
        out["reason"] = _check(None, 0, "serv", now)[1]
        for p in PROVIDERS:
            out[p] = {"state": "refused", "code": "no_allowance", "reason": out["reason"]}
        return out
    backfilled = db.row(conn, "SELECT 1 FROM allowance_backfills WHERE allowance_id=?", a.allowance_id) is not None
    out.update({"allowance_id": a.allowance_id, "start": _iso(a.start), "end": _iso(a.end)})
    for p in PROVIDERS:
        used = _used(conn, a.allowance_id, p)
        if not backfilled:   # estimate until the one-time backfill is written
            used += db.row(conn, "SELECT COUNT(*) n FROM provider_calls WHERE created_at>=? AND " +
                           ("provider='serv'" if p == "serv" else "provider='reppo' AND purpose='submit' AND outcome!='connect_error'"),
                           _iso(a.start).replace("Z", "+00:00"))["n"]
        refused = _check(a, used, p, now)
        out[p] = {"limit": a.limits[p], "used": used, "left": max(a.limits[p] - used, 0),
                  "state": "refused" if refused else "open", "code": refused[0] if refused else None,
                  "reason": refused[1] if refused else None}
    return out


def reserve(conn, provider: str, purpose: str, job_id: str | None) -> str:
    """Atomically reserve one unit before a paid request. Raises AllowanceRefused or UnknownPriorSubmission."""
    a = config()
    own_tx = not conn.in_transaction
    if own_tx:
        conn.execute("BEGIN IMMEDIATE")
    try:
        if a is None:
            raise AllowanceRefused(*_check(None, 0, provider, _now()))
        _backfill(conn, a)
        if job_id and db.row(conn, "SELECT 1 FROM allowance_reservations WHERE job_id=? AND provider=? AND status='reserved'",
                             job_id, provider):
            raise UnknownPriorSubmission(
                f"An earlier {provider.upper() if provider == 'serv' else 'Reppo'} request of this job never recorded an outcome "
                "(the worker stopped mid-request). It may have been charged, so it is not repeated automatically.")
        refused = _check(a, _used(conn, a.allowance_id, provider), provider, _now())
        if refused:
            raise AllowanceRefused(*refused)
        rid = db.new_id("res")
        conn.execute("INSERT INTO allowance_reservations VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (rid, a.allowance_id, provider, purpose, job_id, 1, "reserved", None, db.now(), None))
        if own_tx:
            conn.execute("COMMIT")
        return rid
    except BaseException:
        if own_tx:
            conn.execute("ROLLBACK")
        raise


def settle(conn, rid: str, call_id: str | None, *, sent: bool) -> None:
    """sent=True: the request may have reached the provider (counts). sent=False: it provably never left (released)."""
    conn.execute("UPDATE allowance_reservations SET status=?, call_id=?, settled_at=? WHERE reservation_id=?",
                 ("sent" if sent else "released", call_id, db.now(), rid))
