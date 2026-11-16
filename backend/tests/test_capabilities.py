"""Capability-based readiness and server-side refusal of new paid work (isolated DB; no provider calls)."""
import pytest
from fastapi.testclient import TestClient

from evi import api, capabilities, db, jobs
from evi.config import settings


def _set(monkeypatch, **kw):
    for k, v in kw.items():
        monkeypatch.setattr(settings.__class__, k, property(lambda s, v=v: v))


def _worker(c, alive=True):
    c.execute("DELETE FROM worker_heartbeats")
    if alive:
        c.execute("INSERT INTO worker_heartbeats VALUES ('w', ?)", (db.now(),))


@pytest.fixture()
def client():
    with TestClient(api.app) as c:
        yield c


def test_capability_states_cover_policy_worker_keys_busy_budget(client, monkeypatch):
    c = db.connect()
    c.execute("DELETE FROM jobs")            # start from an empty queue (other tests share this temp DB)
    _worker(c, alive=True)
    _set(monkeypatch, execution_enabled=False, serv_api_key="k", reppo_api_key="")
    caps = client.get("/api/v1/health").json()["capabilities"]
    assert caps["mode"] == "archive" and caps["extraction"]["state"] == "unavailable" and "policy" in caps["extraction"]["reason"]
    assert caps["stored_results"]["available"] in (True, False) and "source_verification" in caps
    _set(monkeypatch, execution_enabled=True)
    caps = client.get("/api/v1/health").json()["capabilities"]
    assert caps["extraction"]["state"] == "available"
    assert caps["evaluation"]["state"] == "unavailable"            # Reppo missing does NOT block extraction
    _worker(c, alive=False)
    assert client.get("/api/v1/health").json()["capabilities"]["extraction"]["reason"].startswith("No processing worker")
    _worker(c, alive=True)
    _set(monkeypatch, global_serv_calls_per_day=0)
    assert client.get("/api/v1/health").json()["capabilities"]["extraction"]["state"] == "budget_exhausted"


def test_busy_and_exhausted_are_refused_before_queueing(client, monkeypatch):
    c = db.connect()
    _worker(c)
    _set(monkeypatch, execution_enabled=True, serv_api_key="k", session_jobs_per_hour=99, global_serv_calls_per_day=40)
    monkeypatch.setenv("EVI_MAX_ACTIVE_JOBS", "1")
    c.execute("DELETE FROM jobs")
    with db.tx(c):
        jobs.enqueue(c, "process_document", {"document_id": "verizon-fy2025"}, session_id="someone-else")
    n_before = c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    r = client.post("/api/v1/documents/verizon-fy2024/parse", json={})
    assert r.status_code == 429 and r.json()["error"]["code"] == "busy"
    assert c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == n_before
    c.execute("DELETE FROM jobs")
    _set(monkeypatch, global_serv_calls_per_day=0)
    r = client.post("/api/v1/documents/verizon-fy2024/parse", json={})
    assert r.status_code == 429 and r.json()["error"]["code"] == "budget_exhausted"


def test_own_running_job_is_returned_even_when_busy(client, monkeypatch):
    c = db.connect()
    _worker(c)
    _set(monkeypatch, execution_enabled=True, serv_api_key="k", session_jobs_per_hour=99, global_serv_calls_per_day=40)
    monkeypatch.setenv("EVI_MAX_ACTIVE_JOBS", "1")
    c.execute("DELETE FROM jobs")
    first = client.post("/api/v1/documents/verizon-fy2024/parse", json={})
    assert first.status_code == 202
    again = client.post("/api/v1/documents/verizon-fy2024/parse", json={})   # reload / double click while queue is full
    assert again.status_code == 202 and again.json()["job_id"] == first.json()["job_id"]
    assert c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 1


def test_disabled_execution_keeps_read_only_inspection(client, monkeypatch):
    _set(monkeypatch, execution_enabled=False)
    assert client.get("/api/v1/documents").status_code == 200
    assert client.get("/api/v1/evaluations").status_code == 200
    r = client.post("/api/v1/documents/verizon-fy2024/parse", json={})
    assert r.status_code == 503 and r.json()["error"]["code"] == "execution_disabled"


def test_real_evaluations_carry_exact_lineage():
    from pathlib import Path
    from evi.replay import connect_ro
    real = Path(__file__).resolve().parents[2] / "data" / "runs" / "evi.sqlite3"
    if not real.exists():
        pytest.skip("no real database")
    c = connect_ro(real)
    views = [api._eval_view(e, c) for e in c.execute("SELECT * FROM evaluations").fetchall()]
    assert len(views) == 11
    for v in views:
        assert v["document_id"] and v["run_id"] and v["version_origin"] == "serv_initial"
        assert v["context"].startswith("experiment ") and v["packet"].startswith("reppo-packet-v1")
