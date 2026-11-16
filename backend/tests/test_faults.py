"""Operational fault matrix (docs/20 §10). Isolated temporary databases and bounded fake provider transports;
these are NOT real provider calls. Real provider receipts are kept separately in artifacts/technical-proof."""
import json
import shutil
import sqlite3
import threading
from pathlib import Path

import httpx
import pytest

from evi import db, jobs, providers, revision, worker
from evi.config import settings

REAL = Path(__file__).resolve().parents[2] / "data" / "runs" / "evi.sqlite3"
REAL_CLIENT = httpx.Client


def fake_http(monkeypatch, handler, seen=None):
    def client(*a, **kw):
        def h(req):
            if seen is not None:
                seen.append(str(req.url))
            return handler(req)
        kw["transport"] = httpx.MockTransport(h)
        return REAL_CLIENT(*a, **kw)
    monkeypatch.setattr(providers.httpx, "Client", client)


def test_two_workers_cannot_both_claim_one_job(tmp_path):
    path = tmp_path / "q.sqlite3"
    c0 = db.connect(path)
    db.init(c0)
    with db.tx(c0):
        jobs.enqueue(c0, "noop", {}, session_id="s")
    got, barrier = [], threading.Barrier(4)

    def claim(i):
        c = db.connect(path)
        barrier.wait()
        j = jobs.claim(c, f"w{i}")
        if j:
            got.append(j["job_id"])
    ts = [threading.Thread(target=claim, args=(i,)) for i in range(4)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(got) == 1


def test_pending_evaluation_survives_restart_and_polls_same_provider_id(tmp_path, monkeypatch):
    path = tmp_path / "e.sqlite3"
    c = db.connect(path)
    db.init(c)
    c.execute("INSERT INTO evaluations (evaluation_id, version_id, mode, status, eval_id, created_at, updated_at) VALUES "
              "('evl1','ver_x','reppo_live','pending','prov-123',?,?)", (db.now(), db.now()))
    with db.tx(c):
        jobs.enqueue(c, "poll_evaluation", {"evaluation_id": "evl1"}, session_id="s")
    jobs.claim(c, "dead-worker")                                     # worker dies mid-poll
    c.execute("UPDATE jobs SET lease_until='2000-01-01T00:00:00+00:00'")
    monkeypatch.setattr(settings.__class__, "reppo_api_key", property(lambda s: "k"))
    seen = []
    fake_http(monkeypatch, lambda r: httpx.Response(200, json={"id": "prov-123", "status": "PROCESSING"}), seen)
    c2 = db.connect(path)                                            # "restarted" process
    worker.run_one(c2, "new-worker")
    assert seen and all(u.endswith("/agents/evals/prov-123") for u in seen)
    assert db.row(c2, "SELECT COUNT(*) n FROM evaluations")["n"] == 1    # no fresh evaluation invented
    assert db.row(c2, "SELECT status FROM jobs")["status"] == "queued"  # re-scheduled poll, same job


@pytest.fixture()
def realcopy(tmp_path):
    if not REAL.exists():
        pytest.skip("no real database")
    dst = tmp_path / "copy.sqlite3"
    sqlite3.connect(REAL).backup(sqlite3.connect(dst))
    c = db.connect(dst)
    db.init(c)
    if not db.row(c, "SELECT 1 FROM versions WHERE version_id='ver_02d96b0afcce_1'"):
        pytest.skip("natural v2 version not present")
    return c


def test_revision_retry_with_same_key_yields_one_child_and_receipt(realcopy, monkeypatch):
    monkeypatch.setattr(settings.__class__, "serv_api_key", property(lambda s: "k"))
    calls = []
    fake_http(monkeypatch, lambda r: calls.append(1) or httpx.Response(200, json={
        "id": "x", "choices": [{"message": {"content": json.dumps({"patches": [], "mark_unresolved": [], "rejected_feedback": []})},
                                "finish_reason": "stop"}], "usage": {"total_tokens": 1}}))
    before = db.row(realcopy, "SELECT COUNT(*) n FROM versions")["n"]
    a = revision.run_revision_v2(realcopy, version_id="ver_02d96b0afcce_1", arm="C", evaluation_id=None, job_id=None, idempotency_key="k-1")
    b = revision.run_revision_v2(realcopy, version_id="ver_02d96b0afcce_1", arm="C", evaluation_id=None, job_id=None, idempotency_key="k-1")
    assert a["child_version_id"] == b["child_version_id"] and len(calls) == 1
    assert db.row(realcopy, "SELECT COUNT(*) n FROM versions")["n"] == before + 1


def test_wrong_parent_or_sandbox_feedback_rejected_before_child(realcopy):
    realcopy.execute("INSERT INTO evaluations (evaluation_id, version_id, mode, status, result_json, created_at, updated_at) VALUES "
                     "('e-other','ver_eb2ca88e293b_1','reppo_live','completed','{}',?,?), ('e-sand','ver_02d96b0afcce_1','reppo_sandbox','completed','{}',?,?)",
                     (db.now(), db.now(), db.now(), db.now()))
    before = db.row(realcopy, "SELECT COUNT(*) n FROM versions")["n"]
    for eid, msg in (("e-other", "different version"), ("e-sand", "real Reppo")):
        with pytest.raises(revision.RevisionRefused, match=msg):
            revision.run_revision_v2(realcopy, version_id="ver_02d96b0afcce_1", arm="D", evaluation_id=eid, job_id=None, idempotency_key=eid)
    with pytest.raises(revision.RevisionRefused, match="must not receive"):
        revision.run_revision_v2(realcopy, version_id="ver_02d96b0afcce_1", arm="C", evaluation_id="e-other", job_id=None, idempotency_key="c")
    assert db.row(realcopy, "SELECT COUNT(*) n FROM versions")["n"] == before


def test_historical_v1_version_cannot_enter_v2_gate(realcopy):
    with pytest.raises(revision.RevisionRefused, match="period-unit-v2"):
        revision.run_revision_v2(realcopy, version_id="ver_b9c64dad515d_1", arm="C", evaluation_id=None, job_id=None, idempotency_key="h")


def test_failed_provider_call_is_recorded_not_counted_as_success(realcopy, monkeypatch):
    monkeypatch.setattr(settings.__class__, "serv_api_key", property(lambda s: "k"))
    fake_http(monkeypatch, lambda r: httpx.Response(503, json={"error": "down"}))
    with pytest.raises(providers.ProviderError):
        revision.run_revision_v2(realcopy, version_id="ver_02d96b0afcce_1", arm="C", evaluation_id=None, job_id=None, idempotency_key="f")
    assert db.row(realcopy, "SELECT outcome FROM provider_calls ORDER BY created_at DESC LIMIT 1")["outcome"] == "http_error"
    assert not db.row(realcopy, "SELECT 1 FROM revision_receipts WHERE idempotency_key='f'")
