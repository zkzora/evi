"""Separate durable worker process: `python -m evi.worker`. Safe to kill and restart at any time."""
from __future__ import annotations

import json
import logging
import os
import signal
import socket
import threading
import time

from . import db, jobs
from .config import settings
from .corpus import SourceIntegrityError, register_all
from .evaluation import build_input, map_result
from .extraction import OutputRejected, RevisionNotAllowed, run_extraction, run_extraction_v2
from .revision import RevisionRefused, run_revision_v2
from .parsing import parse_document
from .providers import ProviderError, reppo_get, reppo_submit

log = logging.getLogger("evi.worker")
STOP = threading.Event()
POLL_BACKOFF_S = [15, 30, 60, 120, 300]


def _beat(conn, worker_id):
    conn.execute("INSERT INTO worker_heartbeats VALUES (?,?) ON CONFLICT(worker_id) DO UPDATE SET seen_at=excluded.seen_at",
                 (worker_id, db.now()))


def handle(conn, job) -> None:
    payload = json.loads(job["payload_json"])
    kind = job["kind"]
    jid = job["job_id"]

    if kind == "process_document":
        from .parsing import cache_key
        drow = db.row(conn, "SELECT sha256, parse_pages FROM documents WHERE document_id=?", payload["document_id"])
        pages = json.loads(drow["parse_pages"])
        reused = db.row(conn, "SELECT parse_id FROM parses WHERE cache_key=?", cache_key(drow["sha256"], pages)) is not None
        jobs.heartbeat(conn, jid, f"Reusing the existing Docling parse of physical page(s) {pages}." if reused
                       else f"Parsing physical page(s) {pages} with Docling.")
        stop = threading.Event()

        def keep_alive():  # Docling can take minutes; keep the lease alive while this process is healthy
            c2 = db.connect()
            while not stop.wait(20):
                jobs.heartbeat(c2, jid)
            c2.close()
        t = threading.Thread(target=keep_alive, daemon=True)
        t.start()
        try:
            parse_id = parse_document(conn, payload["document_id"])
        finally:
            stop.set()
        p = db.row(conn, "SELECT * FROM parses WHERE parse_id=?", parse_id)
        with db.tx(conn):
            nxt = _create_run_and_job(conn, payload["document_id"], parse_id, job["session_id"], parent=jid)
            jobs.finish(conn, jid, "succeeded", (f"Reused Docling parse {parse_id}" if reused else f"Fresh Docling parse {parse_id}")
                        + f" of page(s) {pages}: {p['evidence_count']} evidence items, {p['table_count']} tables. Extraction queued.",
                        result={"parse_id": parse_id, "parse_reused": reused, "pages": pages, "document_id": payload["document_id"],
                                "run_id": json.loads(nxt["payload_json"])["run_id"]},
                        next_job_id=nxt["job_id"])
        return

    if kind == "extract_facts":
        if job["attempts"] > 1 and db.row(conn, "SELECT 1 FROM versions WHERE run_id=?", payload["run_id"]):
            v = db.row(conn, "SELECT version_id FROM versions WHERE run_id=? ORDER BY seq LIMIT 1", payload["run_id"])
            jobs.finish(conn, jid, "succeeded", "Extraction had already been stored.", result={"version_id": v["version_id"]})
            return
        with db.tx(conn):
            jobs.spend(conn, "serv_calls_global", jobs.daily_key(), settings.global_serv_calls_per_day)
        jobs.heartbeat(conn, jid, f"Calling SERV ({settings.serv_model}) with the Docling evidence packet.")
        from .targets import targets_for
        run_doc = db.row(conn, "SELECT document_id FROM runs WHERE run_id=?", payload["run_id"])["document_id"]
        if targets_for(run_doc):
            vid = run_extraction_v2(conn, run_id=payload["run_id"], job_id=jid)
        else:
            vid = run_extraction(conn, run_id=payload["run_id"], job_id=jid)
        jobs.finish(conn, jid, "succeeded", "Extraction stored as an immutable version; support certificates issued.",
                    result={"run_id": payload["run_id"], "version_id": vid})
        return

    if kind == "submit_evaluation":
        ev = db.row(conn, "SELECT * FROM evaluations WHERE evaluation_id=?", payload["evaluation_id"])
        if ev["status"] == "submitting":  # we crashed mid-POST: the provider may have it
            conn.execute("UPDATE evaluations SET status='submission_unknown', updated_at=? WHERE evaluation_id=?",
                         (db.now(), ev["evaluation_id"]))
            jobs.finish(conn, jid, "outcome_unknown", "The worker stopped during submission. The provider may have accepted it; "
                        "it will not be resubmitted automatically.")
            return
        if ev["status"] != "created":
            jobs.finish(conn, jid, "succeeded", f"Evaluation already {ev['status']}.", result={"evaluation_id": ev["evaluation_id"]})
            return
        # Public evaluations use the full-context packet by default (v1 omitted alternative rows; docs/REPPO-PAYLOAD-AUDIT.md).
        packet = os.environ.get("EVI_REPPO_PACKET", "reppo-packet-v2")
        from .evaluation import build_input_v2
        text = build_input_v2(conn, ev["version_id"]) if packet == "reppo-packet-v2" else build_input(conn, ev["version_id"])
        with db.tx(conn):
            jobs.spend(conn, "reppo_evals_global", jobs.daily_key(), settings.global_reppo_evals_per_day)
            conn.execute("UPDATE evaluations SET status='submitting', updated_at=? WHERE evaluation_id=?", (db.now(), ev["evaluation_id"]))
        try:
            sub = reppo_submit(conn, input_text=text, job_id=jid)
        except ProviderError as e:
            conn.execute("UPDATE evaluations SET status=?, updated_at=? WHERE evaluation_id=?",
                         ("submission_unknown" if e.outcome_unknown else "failed" if not e.retryable else "created", db.now(), ev["evaluation_id"]))
            raise
        d = sub["data"]
        conn.execute("UPDATE evaluations SET status='pending', eval_id=?, provider_status=?, payload_sha256=?, payload_bytes=?, "
                     "raw_path=?, updated_at=? WHERE evaluation_id=?",
                     (d["id"], d.get("status"), sub["payload_sha256"], sub["payload_bytes"], sub["raw_path"], db.now(), ev["evaluation_id"]))
        with db.tx(conn):
            poll = jobs.enqueue(conn, "poll_evaluation", {"evaluation_id": ev["evaluation_id"]}, session_id=job["session_id"],
                                parent_job_id=jid, message="Waiting for the Reppo evaluation to complete.")
            conn.execute("UPDATE jobs SET not_before=? WHERE job_id=?", (jobs._ts(POLL_BACKOFF_S[0]), poll["job_id"]))
            jobs.finish(conn, jid, "succeeded", f"Submitted to Reppo as {d['id']}.", result={"eval_id": d["id"]}, next_job_id=poll["job_id"])
        return

    if kind == "poll_evaluation":
        ev = db.row(conn, "SELECT * FROM evaluations WHERE evaluation_id=?", payload["evaluation_id"])
        got = reppo_get(conn, ev["eval_id"], job_id=jid)
        local, result = map_result(got["data"])
        conn.execute("UPDATE evaluations SET status=?, provider_status=?, result_json=?, credits_charged=?, raw_path=?, updated_at=? "
                     "WHERE evaluation_id=?",
                     (local, got["data"].get("status"), db.dumps(result) if result else None, got["data"].get("creditsCharged"),
                      got["raw_path"], db.now(), ev["evaluation_id"]))
        if local == "pending":
            polls = payload.get("polls", 0) + 1
            if polls > 40:
                jobs.finish(conn, jid, "blocked", "The evaluation is still pending after the polling deadline; refresh later.")
                return
            payload["polls"] = polls
            conn.execute("UPDATE jobs SET payload_json=? WHERE job_id=?", (db.dumps(payload), jid))
            jobs.retry_later(conn, jid, f"Reppo status {got['data'].get('status')}; polling again.",
                             POLL_BACKOFF_S[min(polls, len(POLL_BACKOFF_S) - 1)])
            return
        status = "succeeded" if local == "completed" else "failed"
        jobs.finish(conn, jid, status, f"Reppo evaluation {got['data'].get('status')}.", result={"evaluation_id": ev["evaluation_id"]},
                    error=None if status == "succeeded" else {"message": f"Reppo reported {got['data'].get('status')}."})
        return

    if kind == "revise_facts":
        with db.tx(conn):
            jobs.spend(conn, "serv_calls_global", jobs.daily_key(), settings.global_serv_calls_per_day)
        jobs.heartbeat(conn, jid, "Calling SERV for a bounded, evidence-checked revision.")
        arm = payload.get("arm") or ("D" if payload.get("evaluation_id") else "C")
        try:
            receipt = run_revision_v2(conn, version_id=payload["version_id"], arm=arm, evaluation_id=payload.get("evaluation_id"),
                                      job_id=jid, idempotency_key=f"job:{jid}", max_revisions=settings.max_revisions_per_run)
        except RevisionRefused as e:
            raise RevisionNotAllowed(str(e))
        c = receipt["counts"]
        jobs.finish(conn, jid, "succeeded", f"Revision receipt stored: {c['accepted']} accepted, {c['rejected']} rejected, "
                    f"{c['unchanged']} unchanged, {c['unresolved']} unresolved. Child version {receipt['child_version_id']}.",
                    result={"version_id": receipt["child_version_id"], "receipt_sha256": receipt["content_sha256"]})
        return

    jobs.finish(conn, jid, "failed", f"Unknown job kind {kind}.", error={"message": "Unknown job kind."})


def _create_run_and_job(conn, document_id, parse_id, session_id, parent):
    run_id = db.new_id("run")
    conn.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (run_id, document_id, parse_id, "queued", "live", "period-unit-v1", settings.serv_model,
                  db.dumps({"max_revisions": settings.max_revisions_per_run, "max_evaluations": settings.max_evaluations_per_run}),
                  session_id, db.now()))
    return jobs.enqueue(conn, "extract_facts", {"run_id": run_id}, session_id=session_id, parent_job_id=parent,
                        message="Queued for SERV extraction.")


def run_one(conn, worker_id: str) -> bool:
    job = jobs.claim(conn, worker_id)
    if not job:
        return False
    try:
        handle(conn, job)
    except ProviderError as e:
        if e.outcome_unknown:
            jobs.finish(conn, job["job_id"], "outcome_unknown", str(e), error={"code": e.code, "message": str(e)})
        elif e.code == "provider_not_configured":
            jobs.finish(conn, job["job_id"], "blocked", str(e), error={"code": e.code, "message": str(e)})
            _mark_run(conn, job, "blocked")
        elif e.retryable and job["attempts"] < settings.job_max_attempts:
            jobs.retry_later(conn, job["job_id"], f"{e} Retrying.", 10 * 2 ** job["attempts"])
        else:
            jobs.finish(conn, job["job_id"], "failed", str(e), error={"code": e.code, "message": str(e)})
            _mark_run(conn, job, "failed")
    except (jobs.BudgetExceeded, RevisionNotAllowed) as e:
        jobs.finish(conn, job["job_id"], "blocked", str(e), error={"message": str(e)})
        _mark_run(conn, job, "blocked")
    except OutputRejected as e:
        jobs.finish(conn, job["job_id"], "failed", f"SERV output rejected ({e.status}): {e}", error={"code": e.status, "message": str(e)})
    except SourceIntegrityError as e:
        jobs.finish(conn, job["job_id"], "failed", str(e), error={"code": "source_integrity", "message": str(e)})
    except Exception as e:  # noqa: BLE001 - classify unknown errors as failed with a redacted message
        log.exception("job %s failed", job["job_id"])
        jobs.finish(conn, job["job_id"], "failed", f"Internal error: {type(e).__name__}.", error={"message": f"Internal error: {type(e).__name__}."})
        _mark_run(conn, job, "failed")
    return True


def _mark_run(conn, job, status):
    payload = json.loads(job["payload_json"])
    if job["kind"] == "extract_facts" and payload.get("run_id"):
        conn.execute("UPDATE runs SET status=? WHERE run_id=? AND status IN ('queued','running')", (status, payload["run_id"]))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    worker_id = f"{socket.gethostname()}-{os.getpid()}"
    conn = db.connect()
    db.init(conn)
    register_all(conn)
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: STOP.set())
    log.info("worker %s started (db=%s)", worker_id, settings.db_path)
    while not STOP.is_set():
        _beat(conn, worker_id)
        if not run_one(conn, worker_id):
            STOP.wait(2)
    log.info("worker stopped")


if __name__ == "__main__":
    main()
