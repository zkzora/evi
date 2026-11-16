"""Server-boundary tests: anonymous ownership, same-origin writes, rate limits, contract shapes."""
import pytest
from fastapi.testclient import TestClient

from evi import api, db, jobs
from evi.config import settings


@pytest.fixture()
def client():
    with TestClient(api.app) as c:
        yield c


def test_health_does_not_claim_provider_readiness(client):
    h = client.get("/api/v1/health").json()
    assert h["status"] == "ok" and h["live_execution_enabled"] is False


def test_documents_are_registered_usd_sources_with_hashes(client):
    items = client.get("/api/v1/documents").json()["items"]
    assert {d["document_id"] for d in items} == {"verizon-fy2025", "verizon-fy2024", "verizon-3q2025", "att-3q2025", "att-2q2025"}
    assert all(len(d["sha256"]) == 64 and d["currency"] == "USD" for d in items)


def test_source_bytes_served_and_unknown_document_404(client):
    r = client.get("/api/v1/documents/verizon-fy2024/source")
    assert r.status_code == 200 and r.content[:5] == b"%PDF-"
    r = client.get("/api/v1/documents/..%2F..%2Fetc/source")
    assert r.status_code == 404 and "error" in r.json()


def test_cross_origin_and_non_json_writes_rejected(client):
    r = client.post("/api/v1/documents/verizon-fy2024/parse", json={}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    r = client.post("/api/v1/documents/verizon-fy2024/parse", content=b"x", headers={"Content-Type": "text/plain"})
    assert r.status_code == 415


def test_jobs_are_private_to_their_session(client):
    c = db.connect()
    with db.tx(c):
        j = jobs.enqueue(c, "process_document", {"document_id": "verizon-fy2024"}, session_id="someone-else")
    r = client.get(f"/api/v1/jobs/{j['job_id']}")
    assert r.status_code == 404


def test_process_without_worker_is_explicitly_unavailable(client):
    db.connect().execute("DELETE FROM worker_heartbeats")
    r = client.post("/api/v1/documents/verizon-fy2024/parse", json={})
    assert r.status_code == 503 and r.json()["error"]["message"]


def test_session_rate_limit(client, monkeypatch):
    c = db.connect()
    c.execute("INSERT OR REPLACE INTO worker_heartbeats VALUES ('w', ?)", (db.now(),))
    monkeypatch.setattr(settings.__class__, "serv_api_key", property(lambda s: "k"))
    monkeypatch.setattr(settings.__class__, "session_jobs_per_hour", property(lambda s: 1))
    first = client.post("/api/v1/documents/verizon-fy2024/parse", json={})
    assert first.status_code == 202 and first.json()["job_id"]
    again = client.post("/api/v1/documents/verizon-fy2024/parse", json={})  # duplicate click -> same in-flight job
    assert again.json()["job_id"] == first.json()["job_id"]
    other = client.post("/api/v1/documents/verizon-fy2025/parse", json={})
    assert other.status_code == 429


def test_invented_parse_id_rejected(client):
    c = db.connect()
    c.execute("INSERT OR REPLACE INTO worker_heartbeats VALUES ('w', ?)", (db.now(),))
    r = client.post("/api/v1/runs", json={"document_id": "verizon-fy2024", "parse_id": "parse_invented", "policy_version": "period-unit-v1",
                                         "metrics": ["revenue", "operating_profit", "profit_attributable_to_owners"], "mode": "live"})
    assert r.status_code == 409


def test_benchmarks_empty_until_measured(client):
    assert client.get("/api/v1/benchmarks").json() == {"items": []}
