"""Judge PDF upload: validation, narrow multipart exception, session isolation of sources AND derivatives, page-exact
cache keys, quotas, scoped expiry cleanup, idempotent processing and the deterministic pre-SERV stop.
Isolated DB; no provider calls (asserted)."""
import asyncio
import io
import json
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from evi import api, db, jobs, uploads
from evi.config import settings
from evi.parsing import cache_key, doc_cache_key

ORIGIN = "http://127.0.0.1:5173"


def _set(monkeypatch, **kw):
    for k, v in kw.items():
        monkeypatch.setattr(settings.__class__, k, property(lambda s, v=v: v))


def pdf_bytes(pages=3, password=None) -> bytes:
    w = PdfWriter()
    for _ in range(pages):
        w.add_blank_page(width=612, height=792)
    if password:
        w.encrypt(user_password=password, owner_password=password)
    b = io.BytesIO()
    w.write(b)
    return b.getvalue()


def client():
    return TestClient(api.app, base_url="http://testserver")


def upload(cl, data, name="report.pdf", label=None, origin=ORIGIN):
    files = {"file": (name, data, "application/pdf")}
    return cl.post("/api/v1/uploads", files=files, data={"label": label} if label else None, headers={"Origin": origin})


@pytest.fixture(autouse=True)
def _limits(monkeypatch):
    _set(monkeypatch, upload_per_session_active=50, upload_per_session_per_hour=50, upload_global_files=1000,
         upload_global_bytes=10 ** 9)


def provider_calls():
    c = db.connect()
    return c.execute("SELECT COUNT(*) FROM provider_calls").fetchone()[0]


# ---------------------------------------------------------------- validation

def test_valid_pdf_registers_page_count_without_jobs_or_provider_calls():
    with client() as cl:
        c = db.connect()
        jobs_before, calls_before = c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], provider_calls()
        r = upload(cl, pdf_bytes(4), name="../../etc/My Report.pdf", label="Example Telecom")
        assert r.status_code == 201, r.text
        d = r.json()
        assert d["document_id"].startswith("upl_") and d["page_count"] == 4 and d["source_kind"] == "user_upload"
        assert d["source_url"] is None and d["availability"] == "uploaded" and d["issuer_name"] == "Example Telecom"
        assert d["title"] == "My Report.pdf" and d["expires_at"]                      # client path components dropped
        row = db.row(c, "SELECT * FROM documents WHERE document_id=?", d["document_id"])
        assert row["file_name"] == f"{d['document_id']}.pdf" and (settings.uploads_dir / row["file_name"]).exists()
        assert "public" not in str(settings.uploads_dir).replace("\\", "/").split("/")
        assert c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == jobs_before and provider_calls() == calls_before
        src = cl.get(f"/api/v1/documents/{d['document_id']}/source")
        assert src.status_code == 200 and src.content.startswith(b"%PDF-") and src.headers["cache-control"] == "private, no-store"


@pytest.mark.parametrize("data,status,code", [
    (b"GIF89a not a pdf", 415, "not_a_pdf"),
    (b"%PDF-1.7\n garbage that is not a pdf", 422, "unreadable_pdf"),
    (pdf_bytes(2, password="secret"), 422, "encrypted_pdf"),
])
def test_invalid_inputs_are_rejected(data, status, code):
    with client() as cl:
        r = upload(cl, data)
        assert r.status_code == status and r.json()["error"]["code"] == code, r.text


def test_too_many_pages_and_oversize(monkeypatch):
    _set(monkeypatch, upload_max_pages=2)
    with client() as cl:
        r = upload(cl, pdf_bytes(3))
        assert r.status_code == 413 and r.json()["error"]["code"] == "too_many_pages"
    _set(monkeypatch, upload_max_pages=250, upload_max_bytes=2000)
    with client() as cl:
        r = upload(cl, b"%PDF-" + b"0" * 200_000)                 # declared length over the cap: refused by the middleware
        assert r.status_code == 413 and r.json()["error"]["code"] == "payload_too_large"


def test_stream_is_bounded_even_without_a_declared_length():
    from starlette.requests import Request
    chunks = [b"x" * 1000] * 50

    async def receive():
        return {"type": "http.request", "body": chunks.pop() if chunks else b"", "more_body": bool(chunks)}
    req = Request({"type": "http", "method": "POST", "path": "/api/v1/uploads", "headers": []}, receive)
    with pytest.raises(api.ApiFailure) as e:
        asyncio.run(api._read_bounded(req, 5000))
    assert e.value.code == "payload_too_large"


def test_multipart_exception_is_route_specific():
    with client() as cl:
        # Other write routes still require small JSON.
        r = cl.post("/api/v1/documents/verizon-fy2024/parse", files={"file": ("a.pdf", b"%PDF-", "application/pdf")})
        assert r.status_code == 415
        r = cl.post("/api/v1/documents/verizon-fy2024/parse", content=b"{" + b" " * 5000 + b"}",
                    headers={"Content-Type": "application/json"})
        assert r.status_code == 413
        # The upload route rejects JSON and cross-origin writes.
        assert cl.post("/api/v1/uploads", json={"x": 1}).status_code == 415
        r = upload(cl, pdf_bytes(1), origin="https://evil.example")
        assert r.status_code == 403 and r.json()["error"]["code"] == "forbidden_origin"


# ---------------------------------------------------------------- ownership

def _derive_rows(c, did, sha):
    """Minimal parse/run/version/evidence/certificate rows for an uploaded document (as the worker would write)."""
    c.execute("INSERT INTO parses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (f"parse_{did}", did, sha, f"key-{did}", "docling", "x", "{}", "[1]", "n", "/nonexistent", 0, 1, 1, db.now()))
    c.execute("INSERT INTO evidence (evidence_id, parse_id, document_id, document_sha256, kind, page_number, text) VALUES (?,?,?,?,?,?,?)",
              (f"ev_{did}", f"parse_{did}", did, sha, "text", 1, "Total operating revenues"))
    c.execute("INSERT INTO runs (run_id, document_id, parse_id, status, mode, policy_version, model, budget_json, session_id, created_at) "
              "VALUES (?,?,?,?,?,?,?,?,?,?)", (f"run_{did}", did, f"parse_{did}", "succeeded", "live", "p", "m", "{}", None, db.now()))
    c.execute("INSERT INTO versions VALUES (?,?,?,?,?,?,?,?,?)",
              (f"ver_{did}", f"run_{did}", None, None, "serv_initial", 1, "h", json.dumps({"facts": [], "version_id": f"ver_{did}"}), db.now()))
    c.execute("INSERT INTO certificates VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (f"cert_{did}", f"ver_{did}", "f", "", did, f"parse_{did}", "t", "binding-v3", "unknown", "unresolved", "h", "{}", None, db.now()))
    c.execute("INSERT INTO evaluations (evaluation_id, version_id, mode, status, session_id, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
              (f"evl_{did}", f"ver_{did}", "reppo_live", "completed", "s", db.now(), db.now()))


def test_second_session_cannot_reach_upload_or_any_derivative():
    with client() as a, client() as b:
        d = upload(a, pdf_bytes(2)).json()
        did = d["document_id"]
        c = db.connect()
        _derive_rows(c, did, d["sha256"])
        a_paths = [f"/api/v1/documents/{did}/source", f"/api/v1/documents/{did}/parses", f"/api/v1/runs?document_id={did}",
                   f"/api/v1/versions/ver_{did}", f"/api/v1/evidence/ev_{did}", f"/api/v1/versions/ver_{did}/certificates",
                   f"/api/v1/certificates/cert_{did}"]
        for path in a_paths:
            assert a.get(path).status_code == 200, path
            assert b.get(path).status_code == 404, path                        # indistinguishable from "does not exist"
        assert b.get(f"/api/v1/certificates/cert_{did}/verification").status_code == 404
        assert b.get(f"/api/v1/versions/ver_{did}/receipt").status_code == 404
        assert did in [x["document_id"] for x in a.get("/api/v1/documents").json()["items"]]
        assert did not in [x["document_id"] for x in b.get("/api/v1/documents").json()["items"]]
        assert f"evl_{did}" in [e["evaluation_id"] for e in a.get("/api/v1/evaluations").json()["items"]]
        assert f"evl_{did}" not in [e["evaluation_id"] for e in b.get("/api/v1/evaluations").json()["items"]]
        r = b.post(f"/api/v1/uploads/{did}/process", json={"page": 1, "confirmed": True}, headers={"Origin": ORIGIN})
        assert r.status_code == 404
        r = b.post(f"/api/v1/versions/ver_{did}/evaluations", json={"mode": "reppo_live"}, headers={"Origin": ORIGIN})
        assert r.status_code == 404
        # Public corpus results stay public for everyone.
        docs_b = [x["document_id"] for x in b.get("/api/v1/documents").json()["items"]]
        assert "verizon-fy2024" in docs_b and b.get("/api/v1/documents/verizon-fy2024/source").status_code == 200
        assert b.get("/api/v1/documents/verizon-fy2024/source").headers["cache-control"].startswith("public")


# ---------------------------------------------------------------- cache identity and Docling page range

def test_cache_key_includes_page_and_upload_identity():
    with client() as a, client() as b:
        data = pdf_bytes(3)
        d1, d2 = upload(a, data).json(), upload(b, data).json()
        c = db.connect()
        r1 = db.row(c, "SELECT * FROM documents WHERE document_id=?", d1["document_id"])
        r2 = db.row(c, "SELECT * FROM documents WHERE document_id=?", d2["document_id"])
        assert r1["sha256"] == r2["sha256"]
        assert doc_cache_key(r1, [1]) != doc_cache_key(r1, [2])                 # another page never reuses page 1
        assert doc_cache_key(r1, [1]) != doc_cache_key(r2, [1])                 # same bytes, other session: no reuse
        reg = db.row(c, "SELECT * FROM documents WHERE document_id='verizon-fy2024'")
        assert doc_cache_key(reg, [54]) == cache_key(reg["sha256"], [54])       # registered keys unchanged


def test_docling_receives_exactly_the_selected_page(monkeypatch):
    import docling.document_converter as dc
    seen = {}

    class FakeConverter:
        def __init__(self, *a, **k):
            pass

        def convert(self, path, page_range):
            seen["page_range"] = page_range
            raise RuntimeError("stop after recording the page range")
    monkeypatch.setattr(dc, "DocumentConverter", FakeConverter)
    from evi.parsing import parse_document
    with client() as a:
        did = upload(a, pdf_bytes(5)).json()["document_id"]
    with pytest.raises(RuntimeError):
        parse_document(db.connect(), did, [4])
    assert seen["page_range"] == (4, 4)
    with pytest.raises(ValueError):
        parse_document(db.connect(), did, [6])                                  # beyond the physical page count


# ---------------------------------------------------------------- processing route

def _live(monkeypatch):
    _set(monkeypatch, execution_enabled=True, serv_api_key="k", session_jobs_per_hour=99, global_serv_calls_per_day=40)
    monkeypatch.setenv("EVI_MAX_ACTIVE_JOBS", "99")
    c = db.connect()
    c.execute("DELETE FROM worker_heartbeats")
    c.execute("INSERT INTO worker_heartbeats VALUES ('w', ?)", (db.now(),))


def test_process_requires_confirmed_valid_page_and_is_idempotent(monkeypatch):
    _live(monkeypatch)
    with client() as a:
        did = upload(a, pdf_bytes(3)).json()["document_id"]
        h = {"Origin": ORIGIN}
        assert a.post(f"/api/v1/uploads/{did}/process", json={"page": 2, "confirmed": False}, headers=h).json()["error"]["code"] == "page_not_confirmed"
        r = a.post(f"/api/v1/uploads/{did}/process", json={"page": 9, "confirmed": True}, headers=h)
        assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_page"
        assert a.post(f"/api/v1/documents/{did}/parse", json={}, headers=h).json()["error"]["code"] == "page_required"
        calls = provider_calls()
        j1 = a.post(f"/api/v1/uploads/{did}/process", json={"page": 2, "confirmed": True}, headers=h).json()
        j2 = a.post(f"/api/v1/uploads/{did}/process", json={"page": 2, "confirmed": True}, headers=h).json()
        assert j1["job_id"] == j2["job_id"]                                      # double click / reload: same job
        payload = json.loads(db.row(db.connect(), "SELECT payload_json FROM jobs WHERE job_id=?", j1["job_id"])["payload_json"])
        assert payload == {"document_id": did, "pages": [2]}
        j3 = a.post(f"/api/v1/uploads/{did}/process", json={"page": 3, "confirmed": True}, headers=h).json()
        assert j3["job_id"] != j1["job_id"] and provider_calls() == calls       # queuing calls no provider
        assert a.get(f"/api/v1/jobs/{j1['job_id']}").status_code == 200
        db.connect().execute("DELETE FROM jobs WHERE job_id IN (?,?)", (j1["job_id"], j3["job_id"]))


def test_processing_shares_the_same_spending_gates(monkeypatch):
    _live(monkeypatch)
    monkeypatch.setenv("EVI_ALLOWANCE_SERV_CALLS", "0")
    with client() as a:
        did = upload(a, pdf_bytes(1)).json()["document_id"]
        r = a.post(f"/api/v1/uploads/{did}/process", json={"page": 1, "confirmed": True}, headers={"Origin": ORIGIN})
        assert r.status_code == 403 and r.json()["error"]["code"] == "allowance_exhausted"
    _set(monkeypatch, execution_enabled=False)
    with client() as a:
        did = upload(a, pdf_bytes(1)).json()["document_id"]                     # upload itself still works (no provider)
        r = a.post(f"/api/v1/uploads/{did}/process", json={"page": 1, "confirmed": True}, headers={"Origin": ORIGIN})
        assert r.status_code == 503 and r.json()["error"]["code"] == "execution_disabled"


def test_page_without_bindable_rows_stops_before_serv(monkeypatch):
    """Worker: after the parse, no derivable (interval, year) column on a metric row -> failed unsupported_layout,
    no extraction job and no provider call."""
    from evi import worker
    with client() as a:
        did = upload(a, pdf_bytes(2)).json()["document_id"]
    c = db.connect()
    sha = db.row(c, "SELECT sha256 FROM documents WHERE document_id=?", did)["sha256"]

    art = settings.artifacts_dir / "parses" / f"parse_fake_{did}.docling.json"
    art.parent.mkdir(parents=True, exist_ok=True)
    # A cover-like page: text only, no table -> nothing the binding policy can read as a metric row.
    art.write_text(json.dumps({"pages": {"2": {"size": {"width": 612, "height": 792}}}, "tables": [],
                               "texts": [{"text": "Annual Report", "label": "title",
                                          "prov": [{"page_no": 2, "bbox": {"l": 1, "t": 700, "r": 200, "b": 680, "coord_origin": "BOTTOMLEFT"}}]}]}),
                   encoding="utf-8")

    def fake_parse(conn, document_id, pages=None):
        pid = f"parse_fake_{document_id}"
        conn.execute("INSERT OR IGNORE INTO parses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (pid, document_id, sha, f"k-{pid}", "docling", "x", "{}", json.dumps(pages), "n", str(art), 0, 1, 1, db.now()))
        return pid
    monkeypatch.setattr(worker, "parse_document", fake_parse)
    with db.tx(c):
        j = jobs.enqueue(c, "process_document", {"document_id": did, "pages": [2]}, session_id="s-test")
    calls = provider_calls()
    worker.handle(c, db.row(c, "SELECT * FROM jobs WHERE job_id=?", j["job_id"]))
    done = db.row(c, "SELECT * FROM jobs WHERE job_id=?", j["job_id"])
    assert done["status"] == "failed" and json.loads(done["error_json"])["code"] == "unsupported_layout"
    assert "no SERV call was made" in done["message"]
    assert db.row(c, "SELECT COUNT(*) n FROM jobs WHERE kind='extract_facts' AND json_extract(payload_json,'$.run_id') IN "
                     "(SELECT run_id FROM runs WHERE document_id=?)", did)["n"] == 0
    assert provider_calls() == calls


# ---------------------------------------------------------------- quotas and retention

def test_session_and_global_caps(monkeypatch):
    _set(monkeypatch, upload_per_session_active=1)
    with client() as a:
        assert upload(a, pdf_bytes(1)).status_code == 201
        r = upload(a, pdf_bytes(1))
        assert r.status_code == 429 and r.json()["error"]["code"] == "upload_limit"
    _set(monkeypatch, upload_per_session_active=50, upload_global_bytes=1)
    with client() as b:
        r = upload(b, pdf_bytes(1))
        assert r.status_code == 507 and r.json()["error"]["code"] == "upload_storage_full"
    assert not list(settings.uploads_dir.glob("*.part"))                        # refused bytes are not left behind


def test_expiry_cleanup_is_scoped_and_spares_active_work():
    with client() as a:
        d_old = upload(a, pdf_bytes(1)).json()["document_id"]
        d_busy = upload(a, pdf_bytes(1)).json()["document_id"]
        d_new = upload(a, pdf_bytes(1)).json()["document_id"]
    c = db.connect()
    for did in (d_old, d_busy):
        c.execute("UPDATE documents SET expires_at=? WHERE document_id=?", ("2001-01-01T00:00:00.000+00:00", did))
    _derive_rows(c, d_old, db.row(c, "SELECT sha256 FROM documents WHERE document_id=?", d_old)["sha256"])
    with db.tx(c):
        jobs.enqueue(c, "process_document", {"document_id": d_busy, "pages": [1]}, session_id="s-busy")
    registered_before = c.execute("SELECT COUNT(*) FROM documents WHERE source_kind='registered'").fetchone()[0]
    versions_before = c.execute("SELECT COUNT(*) FROM versions").fetchone()[0]
    removed = uploads.cleanup(c)
    assert d_old in removed and d_busy not in removed and d_new not in removed
    for table, col in (("documents", "document_id"), ("parses", "document_id"), ("runs", "document_id"),
                       ("evidence", "document_id"), ("certificates", "document_id")):
        assert c.execute(f"SELECT COUNT(*) FROM {table} WHERE {col}=?", (d_old,)).fetchone()[0] == 0, table
    assert c.execute("SELECT COUNT(*) FROM versions").fetchone()[0] == versions_before - 1
    assert c.execute("SELECT COUNT(*) FROM evaluations WHERE evaluation_id=?", (f"evl_{d_old}",)).fetchone()[0] == 0
    assert not (settings.uploads_dir / f"{d_old}.pdf").exists() and (settings.uploads_dir / f"{d_busy}.pdf").exists()
    assert c.execute("SELECT COUNT(*) FROM documents WHERE source_kind='registered'").fetchone()[0] == registered_before
    with client() as a2:                                                         # expired upload: refused with a reason
        assert a2.get(f"/api/v1/documents/{d_busy}/source").status_code == 404   # (other session)
    c.execute("DELETE FROM jobs WHERE json_extract(payload_json,'$.document_id')=?", (d_busy,))


def test_expired_upload_tells_its_owner():
    with client() as a:
        did = upload(a, pdf_bytes(1)).json()["document_id"]
        db.connect().execute("UPDATE documents SET expires_at=? WHERE document_id=?", ("2001-01-01T00:00:00.000+00:00", did))
        r = a.get(f"/api/v1/documents/{did}/source")
        assert r.status_code == 410 and r.json()["error"]["code"] == "upload_expired" and "24 h" in r.json()["error"]["message"]
        assert did not in [x["document_id"] for x in a.get("/api/v1/documents").json()["items"]]
