"""State-machine tests for jobs, budgets, evaluations and revisions.

These use an in-test HTTP transport for providers. They verify durable state handling at our boundary;
they are NOT evidence of a real SERV/Reppo integration.
"""
import json

import httpx
import pytest

from evi import db, extraction, jobs, providers, worker
from evi.config import settings
from evi.extraction import Change, ModelFact, RevisionNotAllowed, apply_changes, assert_revision_allowed

SHA = "c" * 64


@pytest.fixture()
def conn(tmp_path):
    c = db.connect(tmp_path / "t.sqlite3")
    db.init(c)
    c.execute("INSERT INTO documents VALUES ('d1','Issuer','T','https://example.org/r.pdf',?,10,1,'FY','USD','r.pdf',1,1,'[1]',?)",
              (SHA, db.now()))
    c.execute("INSERT INTO parses VALUES ('p1','d1',?,'k','docling','x','{}','[1]','n','a',1,6,1,?)", (SHA, db.now()))
    cells = [("unit", "text", "(dollars in millions, except per share amounts)", None, None, None, 1, 0),
             ("head", "table_cell", "Years Ended December 31,", 0, 0, 1, 2, 1),
             ("y25", "table_cell", "2025", 0, 1, 1, 1, 1),
             ("lbl", "table_cell", "Total Operating Revenues", 0, 2, 0, 1, 0),
             ("v25", "table_cell", "138,191", 0, 2, 1, 1, 0),
             ("v24", "table_cell", "134,788", 0, 2, 2, 1, 0)]
    for eid, kind, text, t, r, col, span, hdr in cells:
        c.execute("INSERT INTO evidence VALUES (?,?,?,?,?,1,?,?,?,?,1,?,?,0,NULL,612,792,NULL)",
                  (eid, "p1", "d1", SHA, kind, text, t, r, col, span, hdr))
    c.execute("INSERT INTO runs VALUES ('run_aaaaaaaaaaaaaaaa','d1','p1','queued','live','period-unit-v1','m','{}','s1',?)", (db.now(),))
    yield c
    c.close()


def mf(**over):
    d = dict(metric="revenue", metric_label="Total Operating Revenues", scope="consolidated", amount_text="138,191", currency="USD",
             unit_scale="1000000", period_kind="full_year", period_label="FY2025", start_date="2025-01-01", end_date="2025-12-31",
             duration_months=12, value_evidence_id="v25", metric_evidence_ids=["lbl"], period_evidence_ids=["head", "y25"],
             unit_evidence_ids=["unit"], unresolved_reason=None)
    d.update(over)
    return ModelFact(**d)


def fake_transport(handler):
    return httpx.MockTransport(handler)


REAL_CLIENT = httpx.Client


def patch_http(monkeypatch, handler):
    def client(*a, **kw):
        kw["transport"] = fake_transport(handler)
        return REAL_CLIENT(*a, **kw)
    monkeypatch.setattr(providers.httpx, "Client", client)


def test_missing_key_blocks_extraction_explicitly(conn, monkeypatch):
    monkeypatch.setattr(settings.__class__, "serv_api_key", property(lambda s: ""))
    with db.tx(conn):
        jobs.enqueue(conn, "extract_facts", {"run_id": "run_aaaaaaaaaaaaaaaa"}, session_id="s1")
    worker.run_one(conn, "w")
    j = db.row(conn, "SELECT * FROM jobs")
    assert j["status"] == "blocked" and "not configured" in j["message"]
    assert db.row(conn, "SELECT COUNT(*) n FROM versions")["n"] == 0


def test_malformed_and_truncated_outputs_are_preserved_as_failures(conn, monkeypatch):
    monkeypatch.setattr(settings.__class__, "serv_api_key", property(lambda s: "k"))
    for finish, content, expected in [("length", "{", "truncated"), ("stop", "not json", "malformed_json"),
                                      ("stop", json.dumps({"facts": [{"metric": "ebitda"}]}), "schema_invalid")]:
        patch_http(monkeypatch, lambda r, f=finish, c=content: httpx.Response(200, json={
            "id": "x", "choices": [{"message": {"content": c}, "finish_reason": f}], "usage": {}}))
        conn.execute("DELETE FROM jobs")
        with db.tx(conn):
            jobs.enqueue(conn, "extract_facts", {"run_id": "run_aaaaaaaaaaaaaaaa"}, session_id="s1")
        worker.run_one(conn, "w")
        j = db.row(conn, "SELECT * FROM jobs")
        assert j["status"] == "failed" and expected in j["message"]
    assert db.row(conn, "SELECT COUNT(*) n FROM provider_calls WHERE provider='serv'")["n"] == 3
    assert db.row(conn, "SELECT COUNT(*) n FROM versions")["n"] == 0


def test_extraction_creates_checked_immutable_version_and_missing_targets(conn, monkeypatch):
    monkeypatch.setattr(settings.__class__, "serv_api_key", property(lambda s: "k"))
    out = {"facts": [json.loads(mf().model_dump_json())]}
    patch_http(monkeypatch, lambda r: httpx.Response(200, json={"id": "cmpl", "choices": [{"message": {"content": json.dumps(out)},
                                                                                        "finish_reason": "stop"}], "usage": {"total_tokens": 9}}))
    with db.tx(conn):
        jobs.enqueue(conn, "extract_facts", {"run_id": "run_aaaaaaaaaaaaaaaa"}, session_id="s1")
    worker.run_one(conn, "w")
    v = json.loads(db.row(conn, "SELECT body_json FROM versions")["body_json"])
    rev = next(f for f in v["facts"] if f["metric"] == "revenue")
    assert rev["normalized_value"] == "138191000000" and rev["reported_value"] == "138191"
    missing = [f for f in v["facts"] if f["metric"] != "revenue"]
    assert len(missing) == 2 and all(f["reported_value"] is None for f in missing)
    assert all(c["status"] == "unknown" for c in v["checks"] if c["fact_id"] in {f["fact_id"] for f in missing})


def test_worker_restart_recovers_expired_lease_and_does_not_duplicate_version(conn, monkeypatch):
    with db.tx(conn):
        j = jobs.enqueue(conn, "extract_facts", {"run_id": "run_aaaaaaaaaaaaaaaa"}, session_id="s1")
    jobs.claim(conn, "w1")  # worker 1 dies holding the lease
    conn.execute("UPDATE jobs SET lease_until='2000-01-01T00:00:00+00:00'")
    claimed = jobs.claim(conn, "w2")
    assert claimed["job_id"] == j["job_id"] and claimed["attempts"] == 2


def test_duplicate_click_returns_same_job(conn):
    with db.tx(conn):
        a = jobs.enqueue(conn, "revise_facts", {}, session_id="s1", idempotency_key="k1")
        b = jobs.enqueue(conn, "revise_facts", {}, session_id="s1", idempotency_key="k1")
    assert a["job_id"] == b["job_id"]


def test_reppo_crash_mid_submit_becomes_unknown_not_resubmitted(conn, monkeypatch):
    calls = []
    patch_http(monkeypatch, lambda r: calls.append(r) or httpx.Response(201, json={"id": "e1", "status": "QUEUED"}))
    monkeypatch.setattr(settings.__class__, "reppo_api_key", property(lambda s: "k"))
    _version(conn)
    conn.execute("INSERT INTO evaluations (evaluation_id, version_id, mode, status, created_at, updated_at) VALUES "
                 "('evl1','ver_1','reppo_live','submitting',?,?)", (db.now(), db.now()))
    with db.tx(conn):
        jobs.enqueue(conn, "submit_evaluation", {"evaluation_id": "evl1"}, session_id="s1")
    worker.run_one(conn, "w")
    assert db.row(conn, "SELECT status FROM jobs")["status"] == "outcome_unknown"
    assert db.row(conn, "SELECT status FROM evaluations")["status"] == "submission_unknown"
    assert calls == []


def test_reppo_timeout_is_unknown_outcome(conn, monkeypatch):
    monkeypatch.setenv("EVI_REPPO_PACKET", "reppo-packet-v1")   # minimal fixture has no Docling artifact for packet v2
    def boom(r):
        raise httpx.ReadTimeout("t", request=r)
    patch_http(monkeypatch, boom)
    monkeypatch.setattr(settings.__class__, "reppo_api_key", property(lambda s: "k"))
    _version(conn)
    conn.execute("INSERT INTO evaluations (evaluation_id, version_id, mode, status, created_at, updated_at) VALUES "
                 "('evl1','ver_1','reppo_live','created',?,?)", (db.now(), db.now()))
    with db.tx(conn):
        jobs.enqueue(conn, "submit_evaluation", {"evaluation_id": "evl1"}, session_id="s1")
    worker.run_one(conn, "w")
    assert db.row(conn, "SELECT status FROM jobs")["status"] == "outcome_unknown"
    assert db.row(conn, "SELECT status FROM evaluations")["status"] == "submission_unknown"
    assert db.row(conn, "SELECT COUNT(*) n FROM budget_ledger WHERE scope='reppo_evals_global'")["n"] == 1


def _version(conn, vid="ver_1"):
    facts = [extraction.to_fact(mf(), "d1", "serv_initial", "run_aaaaaaaaaaaaaaaa:revenue")]
    body = {"version_id": vid, "run_id": "run_aaaaaaaaaaaaaaaa", "origin": "serv_initial", "facts": facts, "checks": [], "target": {}}
    conn.execute("INSERT INTO versions VALUES (?,?,NULL,NULL,'serv_initial',1,'h',?,?)", (vid, "run_aaaaaaaaaaaaaaaa", json.dumps(body), db.now()))


@pytest.mark.parametrize("mode,status,for_version,msg", [
    ("reppo_live", "pending", "ver_1", "not completed"),
    ("reppo_sandbox", "completed", "ver_1", "real Reppo"),
    ("reppo_live", "completed", "ver_other", "different version"),
])
def test_unsettled_sandbox_or_wrong_parent_feedback_cannot_authorize_revision(conn, mode, status, for_version, msg):
    _version(conn)
    conn.execute("INSERT INTO evaluations (evaluation_id, version_id, mode, status, result_json, created_at, updated_at) VALUES "
                 "('evl1',?,?,?,?,?,?)", (for_version, mode, status, json.dumps({"verdict": {}}), db.now(), db.now()))
    with pytest.raises(RevisionNotAllowed, match=msg):
        assert_revision_allowed(conn, "ver_1", "evl1", 2)


def test_unsupported_critique_induced_change_is_rejected(conn):
    ev = extraction.load_evidence(conn, "p1")
    doc = db.row(conn, "SELECT * FROM documents")
    parent = [extraction.to_fact(mf(), "d1", "serv_initial", "f")]
    # Critique "says" revenue should be 134,788 (the comparative column) and annualized scale in billions.
    bad = [Change(fact=mf(amount_text="134,788", value_evidence_id="v24"), reason="evaluator says", supporting_evidence_ids=["v24"]),
           Change(fact=mf(unit_scale="1000000000"), reason="evaluator says", supporting_evidence_ids=["unit"]),
           Change(fact=mf(), reason="invented", supporting_evidence_ids=["ev_invented"])]
    for ch in bad:
        facts, decisions = apply_changes(parent, [ch], ev, doc, "run_aaaaaaaaaaaaaaaa", 2)
        assert decisions[0]["decision"] == "rejected"
        assert facts[0]["reported_value"] == "138191" and facts[0]["unit_scale"] == "1000000"


def test_supported_change_is_accepted(conn):
    ev = extraction.load_evidence(conn, "p1")
    doc = db.row(conn, "SELECT * FROM documents")
    parent = [extraction.to_fact(mf(unit_scale="1"), "d1", "serv_initial", "f")]  # parent had the wrong scale
    facts, decisions = apply_changes(parent, [Change(fact=mf(), reason="unit note says millions", supporting_evidence_ids=["unit"])],
                                     ev, doc, "run_aaaaaaaaaaaaaaaa", 2)
    assert decisions[0]["decision"] == "accepted" and facts[0]["unit_scale"] == "1000000"


def test_budget_is_durable_and_enforced(conn):
    for _ in range(2):
        with db.tx(conn):
            jobs.spend(conn, "serv_calls_global", "day", 2)
    with pytest.raises(jobs.BudgetExceeded):
        with db.tx(conn):
            jobs.spend(conn, "serv_calls_global", "day", 2)
