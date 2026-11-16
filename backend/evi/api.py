"""FastAPI service. Run: `uvicorn evi.api:app --host 127.0.0.1 --port 8000` from backend/."""
from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import db, jobs
from .config import settings
from .corpus import register_all, source_path, verify_bytes
from .extraction import METRICS, POLICY_VERSION

app = FastAPI(title="Evi API", version="0.1.0", docs_url="/api/v1/docs", openapi_url="/api/v1/openapi.json")
P = "/api/v1"
SESSION_COOKIE = "evi_session"


class ApiFailure(Exception):
    def __init__(self, status: int, message: str, code: str = "error"):
        self.status, self.message, self.code = status, message, code


def err(status: int, message: str, code: str = "error") -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


@app.exception_handler(ApiFailure)
async def _api_failure(_, e: ApiFailure):
    return err(e.status, e.message, e.code)


@app.exception_handler(StarletteHTTPException)
async def _http(_, e: StarletteHTTPException):
    return err(e.status_code, str(e.detail), "http_error")


@app.exception_handler(RequestValidationError)
async def _validation(_, e: RequestValidationError):
    return err(422, f"Invalid request: {len(e.errors())} validation error(s).", "invalid_request")


def conn():
    c = db.connect()
    return c


@app.on_event("startup")
def _startup():
    c = conn()
    db.init(c)
    register_all(c)
    c.close()


@app.middleware("http")
async def session_and_origin(request: Request, call_next):
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin and origin not in settings.allowed_origins:
            return err(403, "Cross-origin writes are not permitted.", "forbidden_origin")
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            return err(415, "Write requests must be JSON.", "unsupported_media_type")
        if int(request.headers.get("content-length") or 0) > 4096:
            return err(413, "Request body is too large.", "payload_too_large")
    sid = request.cookies.get(SESSION_COOKIE)
    new = not sid or len(sid) != 43
    if new:
        sid = secrets.token_urlsafe(32)
    request.state.session_id = sid
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    if new:
        response.set_cookie(SESSION_COOKIE, sid, httponly=True, samesite="strict", secure=request.url.scheme == "https",
                            max_age=60 * 60 * 24 * 30, path="/")
    return response


def _session(request: Request, c) -> str:
    sid = request.state.session_id
    c.execute("INSERT OR IGNORE INTO sessions VALUES (?,?)", (sid, db.now()))
    return sid


def _worker_alive(c) -> bool:
    r = db.row(c, "SELECT MAX(seen_at) t FROM worker_heartbeats")
    if not r or not r["t"]:
        return False
    return datetime.fromisoformat(r["t"]) > datetime.now(timezone.utc) - timedelta(seconds=30)


# ---------------------------------------------------------------- health / documents

@app.get(f"{P}/health")
def health():
    import importlib.util
    from .capabilities import compute
    c = conn()
    worker = _worker_alive(c)
    serv, reppo = bool(settings.serv_api_key), bool(settings.reppo_api_key)
    ex = settings.execution_enabled
    return {"status": "ok", "live_execution_enabled": ex and worker and serv and reppo,
            "processing_enabled": ex and worker and serv, "execution_enabled": ex,
            "components": {"execution": "enabled" if ex else "disabled", "database": "ok", "worker": "alive" if worker else "not_running",
                           "docling": "installed" if importlib.util.find_spec("docling") else "not installed",
                           "serv": "configured" if serv else "not_configured",
                           "reppo": "configured" if reppo else "not_configured", "serv_model": settings.serv_model},
            "limits": {"session_jobs_per_hour": settings.session_jobs_per_hour,
                       "global_serv_calls_per_day": settings.global_serv_calls_per_day,
                       "global_reppo_evals_per_day": settings.global_reppo_evals_per_day,
                       "max_revisions_per_run": settings.max_revisions_per_run},
            "capabilities": compute(c)}


def _doc_view(c, d) -> dict:
    p = db.row(c, "SELECT * FROM parses WHERE document_id=? AND document_sha256=? ORDER BY created_at DESC LIMIT 1",
               d["document_id"], d["sha256"])
    return {"document_id": d["document_id"], "issuer_name": d["issuer_name"], "title": d["title"], "source_url": d["source_url"],
            "sha256": d["sha256"], "page_count": d["page_count"], "source_page": d["source_page"], "period_label": d["period_label"],
            "currency": d["currency"], "source_version": d["source_version"], "byte_size": d["byte_size"],
            "parse_status": "parsed" if p else "not_started", "parse_id": p["parse_id"] if p else None,
            "parse_coverage": p["coverage_note"] if p else None, "parser": f"docling {p['parser_version']}" if p else None,
            "availability": "registered"}


@app.get(f"{P}/documents")
def documents():
    c = conn()
    return {"items": [_doc_view(c, d) for d in db.rows(c, "SELECT * FROM documents ORDER BY document_id DESC")]}


def _doc(c, document_id):
    d = db.row(c, "SELECT * FROM documents WHERE document_id=?", document_id)
    if not d:
        raise ApiFailure(404, "This document is not in the registered public corpus.", "not_found")
    return d


@app.get(f"{P}/documents/{{document_id}}/source")
def document_source(document_id: str):
    c = conn()
    d = _doc(c, document_id)
    verify_bytes(d)
    return FileResponse(source_path(d), media_type="application/pdf", filename=d["file_name"],
                        headers={"X-Source-SHA256": d["sha256"], "Cache-Control": "public, max-age=86400, immutable"})


@app.get(f"{P}/documents/{{document_id}}/parses")
def document_parses(document_id: str):
    c = conn()
    _doc(c, document_id)
    return {"items": [dict(r) for r in db.rows(c, "SELECT parse_id, document_id, document_sha256, parser, parser_version, config_json, "
                                                   "pages_json, coverage_note, table_count, evidence_count, duration_ms, created_at "
                                                   "FROM parses WHERE document_id=?", document_id)]}


class Empty(BaseModel):
    model_config = ConfigDict(extra="ignore")


def _start(request: Request, c, kind: str, payload: dict, idem: str, message: str) -> dict:
    sid = _session(request, c)
    try:
        with db.tx(c):
            existing = db.row(c, "SELECT * FROM jobs WHERE idempotency_key=?", idem)
            if not (existing and existing["status"] not in ("failed", "cancelled")):
                jobs.session_rate_check(c, sid)
            j = jobs.enqueue(c, kind, payload, session_id=sid, idempotency_key=idem, message=message)
    except jobs.BudgetExceeded as e:
        raise ApiFailure(429, str(e), "rate_limited")
    return jobs.public_view(c, db.row(c, "SELECT * FROM jobs WHERE job_id=?", j["job_id"]))


def _require_capability(c, which: str) -> None:
    """Server-side gate for NEW paid work (extraction or evaluation): policy, worker, provider access, queue, budget."""
    from .capabilities import CapabilityRefused, require
    try:
        require(c, which)
    except CapabilityRefused as e:
        raise ApiFailure(e.status, e.message, e.code)


def _require_worker(c, need_serv=True):
    if not settings.execution_enabled:
        raise ApiFailure(503, "New processing is disabled on this server. Existing results remain available.", "execution_disabled")
    if not _worker_alive(c):
        raise ApiFailure(503, "The processing worker is not running.", "worker_unavailable")
    if need_serv and not settings.serv_api_key:
        raise ApiFailure(503, "SERV_API_KEY is not configured on the server.", "provider_not_configured")


@app.post(f"{P}/documents/{{document_id}}/parse", status_code=202)
def parse(document_id: str, request: Request, _: Empty):
    """Process report: Docling parse (cached by hash/parser/config/pages) then automatic SERV extraction."""
    c = conn()
    _doc(c, document_id)
    # One in-flight process per session+document; a reload or double click returns the same job (checked BEFORE any
    # capability refusal so a busy queue never hides the visitor's own running job).
    active = db.row(c, "SELECT j.* FROM jobs j WHERE j.kind='process_document' AND j.session_id=? AND "
                       "json_extract(j.payload_json,'$.document_id')=? ORDER BY created_at DESC LIMIT 1",
                    request.state.session_id, document_id)
    if active and jobs.public_view(c, active)["status"] not in jobs.TERMINAL:
        return jobs.public_view(c, active)
    _require_worker(c)
    _require_capability(c, "extraction")
    return _start(request, c, "process_document", {"document_id": document_id},
                  f"process:{request.state.session_id}:{document_id}:{db.new_id('p')}", "Queued for Docling parsing.")


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_id: str = Field(max_length=64)
    parse_id: str = Field(max_length=64)
    policy_version: str = Field(max_length=32)
    metrics: list[str] = Field(max_length=3)
    mode: str


@app.post(f"{P}/runs", status_code=202)
def create_run(body: RunRequest, request: Request):
    c = conn()
    _doc(c, body.document_id)
    if body.mode != "live" or body.policy_version != POLICY_VERSION or sorted(body.metrics) != sorted(METRICS):
        raise ApiFailure(400, "Only the live period-unit-v1 extraction of the three core metrics is supported.", "invalid_request")
    p = db.row(c, "SELECT * FROM parses WHERE parse_id=? AND document_id=?", body.parse_id, body.document_id)
    if not p:
        raise ApiFailure(409, "The parse_id does not belong to a completed parse of this document.", "invalid_parse")
    _require_worker(c)
    _require_capability(c, "extraction")
    sid = _session(c=c, request=request)
    with db.tx(c):
        jobs.session_rate_check(c, sid)
        from .worker import _create_run_and_job
        j = _create_run_and_job(c, body.document_id, body.parse_id, sid, parent=None)
        c.execute("UPDATE jobs SET parent_job_id=NULL WHERE job_id=?", (j["job_id"],))
    return jobs.public_view(c, db.row(c, "SELECT * FROM jobs WHERE job_id=?", j["job_id"]))


@app.get(f"{P}/jobs/{{job_id}}")
def get_job(job_id: str, request: Request):
    c = conn()
    j = db.row(c, "SELECT * FROM jobs WHERE job_id=?", job_id)
    if not j or j["session_id"] != request.state.session_id:
        raise ApiFailure(404, "No job with this ID belongs to this browser session.", "not_found")
    return jobs.public_view(c, j)


# ---------------------------------------------------------------- runs / versions / evidence (public immutable)

@app.get(f"{P}/runs")
def list_runs(document_id: str):
    c = conn()
    out = []
    for r in db.rows(c, "SELECT * FROM runs WHERE document_id=? ORDER BY created_at DESC LIMIT 50", document_id):
        vids = [v["version_id"] for v in db.rows(c, "SELECT version_id FROM versions WHERE run_id=? ORDER BY seq", r["run_id"])]
        if not vids and r["status"] in ("queued", "running"):
            pass
        out.append({"run_id": r["run_id"], "document_id": r["document_id"], "parse_id": r["parse_id"], "status": r["status"],
                    "mode": r["mode"], "policy_version": r["policy_version"], "model": r["model"], "created_at": r["created_at"],
                    "version_ids": vids})
    return {"items": out}


@app.get(f"{P}/versions/{{version_id}}")
def get_version(version_id: str):
    c = conn()
    v = db.row(c, "SELECT * FROM versions WHERE version_id=?", version_id)
    if not v:
        raise ApiFailure(404, "Version not found.", "not_found")
    body = json.loads(v["body_json"])
    # Additive coverage-v1 view per fact from its newest-policy certificate; the stored version is unchanged.
    from .binding import coverage_view
    newest: dict = {}
    for r in db.rows(c, "SELECT fact_id, policy_version, body_json FROM certificates WHERE version_id=?", version_id):
        if r["fact_id"] and (r["fact_id"] not in newest or r["policy_version"] > newest[r["fact_id"]][0]):
            newest[r["fact_id"]] = (r["policy_version"], r["body_json"])
    for f in body["facts"]:
        if f["fact_id"] in newest:
            f["context_coverage"] = {**coverage_view(json.loads(newest[f["fact_id"]][1])), "policy_version": newest[f["fact_id"]][0]}
    body["content_sha256"] = v["content_sha256"]
    body["created_at"] = v["created_at"]
    return body


@app.get(f"{P}/evidence/{{evidence_id}}")
def get_evidence(evidence_id: str):
    c = conn()
    e = db.row(c, "SELECT * FROM evidence WHERE evidence_id=?", evidence_id)
    if not e:
        raise ApiFailure(404, "Evidence not found.", "not_found")
    out = {k: e[k] for k in ("evidence_id", "parse_id", "document_id", "document_sha256", "kind", "page_number", "text",
                             "table_index", "row_index", "col_index", "label")}
    if e["bbox_json"] and e["page_width"]:
        out.update(bbox=json.loads(e["bbox_json"]), page_width=e["page_width"], page_height=e["page_height"])
    else:
        out["bbox"] = None
        out["limitation"] = "No source coordinates were available for this item; text-only evidence."
    return out


# ---------------------------------------------------------------- evaluations / revisions

def _eval_view(e, c=None) -> dict:
    lineage = {}
    if c is not None:
        r = db.row(c, "SELECT v.run_id, v.origin, r.document_id FROM versions v JOIN runs r ON r.run_id=v.run_id WHERE v.version_id=?",
                   e["version_id"])
        sess = e["session_id"] or ""
        lineage = {"document_id": r["document_id"] if r else None, "run_id": r["run_id"] if r else None,
                   "version_origin": r["origin"] if r else None,
                   "context": (f"experiment {sess.split(':', 1)[1]}" if sess.startswith("experiment:") else "public session"),
                   "packet": "reppo-packet-v1 (candidate-cited cells)"}
    return {**lineage, "evaluation_id": e["evaluation_id"], "version_id": e["version_id"], "mode": e["mode"], "status": e["status"],
            "eval_id": e["eval_id"], "provider_status": e["provider_status"], "created_at": e["created_at"],
            "updated_at": e["updated_at"], "credits_charged": e["credits_charged"], "payload_bytes": e["payload_bytes"],
            "result": json.loads(e["result_json"]) if e["result_json"] else None}


@app.get(f"{P}/evaluations")
def list_evaluations():
    c = conn()
    return {"items": [_eval_view(e, c) for e in db.rows(c, "SELECT * FROM evaluations ORDER BY created_at DESC LIMIT 100")]}


@app.post(f"{P}/versions/{{version_id}}/evaluations", status_code=202)
def evaluate(version_id: str, request: Request, _: Empty):
    c = conn()
    v = db.row(c, "SELECT * FROM versions WHERE version_id=?", version_id)
    if not v:
        raise ApiFailure(404, "Version not found.", "not_found")
    _require_worker(c, need_serv=False)
    if not settings.reppo_api_key:
        raise ApiFailure(503, "REPPO_API_KEY is not configured on the server.", "provider_not_configured")
    sid = _session(request, c)
    with db.tx(c):
        existing = db.row(c, "SELECT * FROM evaluations WHERE version_id=? AND status NOT IN ('failed') ORDER BY created_at DESC LIMIT 1", version_id)
        if existing:
            j = db.row(c, "SELECT * FROM jobs WHERE idempotency_key=?", f"eval:{existing['evaluation_id']}")
            if existing["status"] == "submission_unknown":
                raise ApiFailure(409, "A previous submission for this version has an unknown outcome; reconcile it before submitting again.",
                                 "submission_unknown")
            if j and j["session_id"] == sid:
                return jobs.public_view(c, j)
            raise ApiFailure(409, "This version already has a Reppo evaluation.", "duplicate_evaluation")
        _require_capability(c, "evaluation")
        n = db.row(c, "SELECT COUNT(*) n FROM evaluations e JOIN versions v ON v.version_id=e.version_id WHERE v.run_id=?", v["run_id"])["n"]
        if n >= settings.max_evaluations_per_run:
            raise ApiFailure(429, f"Evaluation budget exhausted ({settings.max_evaluations_per_run} per run).", "budget_exhausted")
        try:
            jobs.session_rate_check(c, sid)
        except jobs.BudgetExceeded as e:
            raise ApiFailure(429, str(e), "rate_limited")
        eid = db.new_id("evl")
        c.execute("INSERT INTO evaluations (evaluation_id, version_id, mode, status, session_id, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                  (eid, version_id, "reppo_live", "created", sid, db.now(), db.now()))
        j = jobs.enqueue(c, "submit_evaluation", {"evaluation_id": eid}, session_id=sid, idempotency_key=f"eval:{eid}",
                         message="Queued for Reppo submission.")
    return jobs.public_view(c, db.row(c, "SELECT * FROM jobs WHERE job_id=?", j["job_id"]))


@app.post(f"{P}/evaluations/{{evaluation_id}}/refresh", status_code=202)
def refresh_evaluation(evaluation_id: str, request: Request, _: Empty):
    c = conn()
    e = db.row(c, "SELECT * FROM evaluations WHERE evaluation_id=?", evaluation_id)
    if not e:
        raise ApiFailure(404, "Evaluation not found.", "not_found")
    if not e["eval_id"]:
        raise ApiFailure(409, f"The evaluation has no provider ID (status {e['status']}); there is nothing to poll.", "no_provider_id")
    _require_worker(c, need_serv=False)
    sid = _session(request, c)
    with db.tx(c):
        j = jobs.enqueue(c, "poll_evaluation", {"evaluation_id": evaluation_id}, session_id=sid,
                         idempotency_key=f"refresh:{evaluation_id}:{sid}:{int(datetime.now().timestamp() // 30)}",
                         message="Reading the existing Reppo evaluation.")
    return jobs.public_view(c, db.row(c, "SELECT * FROM jobs WHERE job_id=?", j["job_id"]))


class ReviseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evaluation_id: str | None = Field(default=None, max_length=64)
    arm: str | None = Field(default=None, pattern="^(C|D)$")


@app.post(f"{P}/versions/{{version_id}}/revisions", status_code=202)
def revise(version_id: str, body: ReviseRequest, request: Request):
    """Arm D (default with evaluation_id): real completed Reppo evaluation of exactly this version.
    Arm C: no external feedback. Both use the same field-aware gate (revision-v2)."""
    c = conn()
    v = db.row(c, "SELECT * FROM versions WHERE version_id=?", version_id)
    if not v:
        raise ApiFailure(404, "Version not found.", "not_found")
    if json.loads(v["body_json"]).get("policy_version") != "period-unit-v2":
        raise ApiFailure(409, "This historical version predates target-bound extraction; process the report again to revise.", "revision_not_allowed")
    arm = body.arm or ("D" if body.evaluation_id else "C")
    if arm == "D":
        ev = db.row(c, "SELECT * FROM evaluations WHERE evaluation_id=?", body.evaluation_id or "")
        reasons = [] if ev else ["Unknown evaluation."]
        if ev:
            if ev["version_id"] != version_id: reasons.append("The evaluation was made for a different version.")
            if ev["mode"] != "reppo_live": reasons.append("Only a real Reppo evaluation can drive a feedback revision.")
            if ev["status"] != "completed": reasons.append("The evaluation has not completed.")
        if reasons:
            raise ApiFailure(409, " ".join(reasons), "revision_not_allowed")
    elif body.evaluation_id:
        raise ApiFailure(400, "Arm C must not receive an evaluation.", "invalid_request")
    key = f"revise:{version_id}:{arm}:{body.evaluation_id}"
    existing = db.row(c, "SELECT * FROM jobs WHERE idempotency_key=? AND status NOT IN ('failed','cancelled')", key)
    if existing:                                   # duplicate click / reload: same job, no new charge
        return jobs.public_view(c, existing)
    _require_worker(c)
    _require_capability(c, "extraction")
    return _start(request, c, "revise_facts", {"version_id": version_id, "evaluation_id": body.evaluation_id, "arm": arm},
                  key, f"Queued for SERV revision (arm {arm}).")


@app.get(f"{P}/versions/{{version_id}}/certificates")
def version_certificates(version_id: str):
    c = conn()
    from .binding import coverage_view
    rows = db.rows(c, "SELECT certificate_id, fact_id, target_key, policy_version, claim_outcome, resolution_outcome, content_sha256, "
                      "check_run_id, created_at, body_json FROM certificates WHERE version_id=? ORDER BY created_at", version_id)
    items = []
    for r in rows:
        d = dict(r)
        d["coverage"] = coverage_view(json.loads(d.pop("body_json")))   # additive view; stored certificate unchanged
        items.append(d)
    return {"items": items}


@app.get(f"{P}/certificates/{{certificate_id}}")
def get_certificate(certificate_id: str):
    c = conn()
    r = db.row(c, "SELECT body_json FROM certificates WHERE certificate_id=?", certificate_id)
    if not r:
        raise ApiFailure(404, "Certificate not found.", "not_found")
    from .binding import coverage_view
    body = json.loads(r["body_json"])
    return {**body, "coverage": coverage_view(body)}  # 'coverage' is a derived view outside the hashed certificate


@app.get(f"{P}/certificates/{{certificate_id}}/verification")
def verify_certificate(certificate_id: str):
    """Recompute from the registered source bytes + Docling artifact (no provider call)."""
    from .binding import verify_certificate as verify
    c = conn()
    r = db.row(c, "SELECT body_json FROM certificates WHERE certificate_id=?", certificate_id)
    if not r:
        raise ApiFailure(404, "Certificate not found.", "not_found")
    ok, problems = verify(c, json.loads(r["body_json"]))
    return {"certificate_id": certificate_id, "verified": ok, "problems": problems, "checked_at": db.now()}


@app.get(f"{P}/versions/{{version_id}}/receipt")
def version_receipt(version_id: str):
    c = conn()
    r = db.row(c, "SELECT body_json FROM revision_receipts WHERE child_version_id=?", version_id)
    if not r:
        raise ApiFailure(404, "No revision receipt names this version as its child.", "not_found")
    return json.loads(r["body_json"])


@app.get(f"{P}/experiments")
def experiments():
    """Published, sanitized experiment export (schema evi.public-experiments/1) built from frozen artifacts by
    scripts/build_public_evidence.py. Missing artifacts produce an explicit error, never an empty benchmark."""
    from pathlib import Path

    from .config import ROOT
    path = Path(os.environ.get("EVI_PUBLIC_EVIDENCE", str(ROOT / "public" / "evidence" / "experiments.v1.json")))
    if not path.exists():
        raise ApiFailure(503, "The published experiment export is not available on this server.", "evidence_unavailable")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "evi.public-experiments/1":
        raise ApiFailure(500, "The published experiment export has an unexpected schema.", "evidence_invalid")
    return data


@app.get(f"{P}/benchmarks")
def benchmarks():
    c = conn()
    return {"items": [json.loads(b["body_json"]) for b in db.rows(c, "SELECT * FROM benchmarks ORDER BY created_at DESC")]}


@app.get(f"{P}/ready")
def ready():
    """Readiness, separate from liveness (/health): database, registered sources, writable artifact storage, worker.
    200 only if the service can serve existing results; worker/provider readiness is reported, not required."""
    import os
    checks = {}
    try:
        c = conn()
        c.execute("SELECT 1").fetchone()
        docs = db.rows(c, "SELECT * FROM documents")
        checks["database"] = "ok"
        checks["sources"] = "ok" if docs and all(source_path(d).exists() for d in docs) else "missing"
        checks["worker"] = "alive" if _worker_alive(c) else "not_running"
    except Exception as e:  # noqa: BLE001
        checks["database"] = f"error: {type(e).__name__}"
    art = settings.artifacts_dir
    checks["artifact_storage"] = "writable" if art.exists() and os.access(art, os.W_OK) else "not_writable"
    checks["execution"] = "enabled" if settings.execution_enabled else "disabled"
    ok = checks.get("database") == "ok" and checks.get("sources") == "ok" and checks["artifact_storage"] == "writable"
    return JSONResponse({"ready": ok, "checks": checks}, status_code=200 if ok else 503)


@app.get(f"{P}/{{rest:path}}")
def not_found(rest: str):
    raise ApiFailure(404, "Unknown API route.", "not_found")


# ---------------------------------------------------------------- production static frontend (same origin)
# Enabled only when EVI_STATIC_DIR points at the built Vite output. /api/* never falls back to HTML.
def _mount_static() -> None:
    import os
    from pathlib import Path as _P
    static = os.environ.get("EVI_STATIC_DIR")
    if not static or not (_P(static) / "index.html").exists():
        return
    root = _P(static).resolve()

    @app.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    def spa(path: str, request: Request):
        if path.startswith("api/"):
            raise ApiFailure(404, "Unknown API route.", "not_found")
        target = (root / path).resolve()
        if path and target.is_file() and root in target.parents:
            cache = "public, max-age=31536000, immutable" if path.startswith("assets/") else "public, max-age=3600"
            return FileResponse(target, headers={"Cache-Control": cache})
        return FileResponse(root / "index.html", headers={"Cache-Control": "no-cache"})


_mount_static()
