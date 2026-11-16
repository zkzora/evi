"""SERV Reasoning and Reppo HTTP clients. Every call is recorded (redacted) in provider_calls."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Any

import httpx

from . import allowance, db
from .config import settings

# Request provably never left the machine: the reserved allowance unit is released and a retry is safe.
NOT_SENT = (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout)


def _reserve(conn, provider: str, purpose: str, job_id: str | None) -> str:
    try:
        return allowance.reserve(conn, provider, purpose, job_id)
    except allowance.UnknownPriorSubmission as e:
        raise ProviderError(str(e), retryable=False, code="submission_unknown", outcome_unknown=True) from e


class ProviderError(Exception):
    def __init__(self, message: str, *, retryable: bool, code: str, outcome_unknown: bool = False):
        super().__init__(message)
        self.retryable, self.code, self.outcome_unknown = retryable, code, outcome_unknown


class ExecutionDisabled(ProviderError):
    def __init__(self):
        super().__init__("Provider execution is disabled on this server (EVI_EXECUTION_ENABLED is not true).",
                         retryable=False, code="provider_not_configured")


def _execution_allowed() -> bool:
    import os
    return settings.execution_enabled or os.environ.get("EVI_ALLOW_PAID_RUNS") == "1"


class NotConfigured(ProviderError):
    def __init__(self, provider: str):
        super().__init__(f"{provider} API key is not configured on the server.", retryable=False, code="provider_not_configured")


def _save_raw(name: str, body: Any) -> str:
    path = settings.artifacts_dir / "provider" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return str(path)


def _record(conn, **kw) -> str:
    call_id = db.new_id("call")
    conn.execute("INSERT INTO provider_calls VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                 (call_id, kw["provider"], kw["purpose"], kw.get("run_id"), kw.get("job_id"), kw.get("request_sha256"),
                  kw.get("http_status"), kw["outcome"], kw.get("upstream_id"), kw.get("finish_reason"),
                  db.dumps(kw.get("usage")) if kw.get("usage") is not None else None, kw.get("latency_ms"),
                  kw.get("response_path"), db.now()))
    return call_id


# ---------------------------------------------------------------- SERV

@dataclass
class ServResult:
    call_id: str
    content: str | None
    finish_reason: str | None
    usage: dict | None
    upstream_id: str | None
    latency_ms: int
    model: str


def serv_chat(conn: sqlite3.Connection, *, purpose: str, messages: list[dict], schema_name: str, schema: dict,
              run_id: str | None, job_id: str | None, transport=None) -> ServResult:
    if not _execution_allowed():
        raise ExecutionDisabled()
    if not settings.serv_api_key:
        raise NotConfigured("SERV")
    body = {"model": settings.serv_model, "messages": messages,
            "max_completion_tokens": settings.serv_max_completion_tokens,
            "response_format": {"type": "json_schema", "json_schema": {"name": schema_name, "strict": True, "schema": schema}}}
    raw_body = json.dumps(body, ensure_ascii=False)
    req_hash = hashlib.sha256(raw_body.encode()).hexdigest()
    rid = _reserve(conn, "serv", purpose, job_id)
    sent, call_id = True, None
    started = time.monotonic()
    try:
        try:
            with httpx.Client(timeout=settings.serv_timeout_s, transport=transport) as client:
                resp = client.post(f"{settings.serv_base_url}/chat/completions", content=raw_body.encode(),
                                   headers={"Authorization": f"Bearer {settings.serv_api_key}", "Content-Type": "application/json"})
        except NOT_SENT as e:
            sent = False
            call_id = _record(conn, provider="serv", purpose=purpose, run_id=run_id, job_id=job_id, request_sha256=req_hash,
                              outcome="connect_error", latency_ms=int((time.monotonic() - started) * 1000))
            raise ProviderError(f"SERV connection failed: {type(e).__name__}.", retryable=True, code="provider_transport") from e
        except httpx.HTTPError as e:   # read/write timeout or dropped connection: SERV may have processed and charged it
            call_id = _record(conn, provider="serv", purpose=purpose, run_id=run_id, job_id=job_id, request_sha256=req_hash,
                              outcome="outcome_unknown", latency_ms=int((time.monotonic() - started) * 1000))
            raise ProviderError(f"SERV request outcome unknown ({type(e).__name__}); it may have been charged, so it is not "
                                "repeated automatically.", retryable=False, code="submission_unknown", outcome_unknown=True) from e
        result = _serv_finish(conn, resp, purpose=purpose, run_id=run_id, job_id=job_id, req_hash=req_hash, started=started)
        call_id = result.call_id
        return result
    finally:   # always settle: a reservation left open would (correctly) block this job as an unknown outcome
        allowance.settle(conn, rid, call_id, sent=sent)


def _serv_finish(conn, resp, *, purpose, run_id, job_id, req_hash, started) -> ServResult:
    latency = int((time.monotonic() - started) * 1000)
    try:
        data = resp.json()
    except ValueError:
        data = {"non_json_body": resp.text[:2000]}
    path = _save_raw(f"serv-{req_hash[:16]}-{int(time.time())}.json", {"request_sha256": req_hash, "model": settings.serv_model,
                                                                       "http_status": resp.status_code, "response": data})
    if resp.status_code >= 400:
        _record(conn, provider="serv", purpose=purpose, run_id=run_id, job_id=job_id, request_sha256=req_hash,
                http_status=resp.status_code, outcome="http_error", latency_ms=latency, response_path=path)
        # A known HTTP error is a known outcome; a retry is a NEW request and reserves its own allowance unit.
        retry = resp.status_code in (408, 429) or resp.status_code >= 500
        raise ProviderError(f"SERV returned HTTP {resp.status_code}.", retryable=retry,
                            code="provider_auth" if resp.status_code in (401, 403) else "provider_http")
    choice = (data.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    finish = choice.get("finish_reason")
    outcome = "ok" if finish == "stop" else f"finish_{finish}"
    if msg.get("refusal"):
        outcome = "refused"
    call_id = _record(conn, provider="serv", purpose=purpose, run_id=run_id, job_id=job_id, request_sha256=req_hash,
                      http_status=resp.status_code, outcome=outcome, upstream_id=data.get("id"), finish_reason=finish,
                      usage=data.get("usage"), latency_ms=latency, response_path=path)
    return ServResult(call_id, msg.get("content"), finish, data.get("usage"), data.get("id"), latency, data.get("model") or settings.serv_model)


# ---------------------------------------------------------------- Reppo
# Current API (eval.reppo.xyz/agents.md, read 2026-11-15): POST /agents/evals {taskType, input<=50KB},
# GET /agents/evals/{id}; statuses QUEUED, PROCESSING, COMPLETED, FAILED.

REPPO_MAX_INPUT_BYTES = 50 * 1000
REPPO_TERMINAL = {"COMPLETED", "FAILED"}


def reppo_submit(conn, *, input_text: str, job_id: str, transport=None) -> dict:
    if not _execution_allowed():
        raise ExecutionDisabled()
    if not settings.reppo_api_key:
        raise NotConfigured("Reppo")
    size = len(input_text.encode("utf-8"))
    if size > REPPO_MAX_INPUT_BYTES:
        raise ProviderError(f"Evaluation input is {size} bytes; Reppo accepts at most {REPPO_MAX_INPUT_BYTES}.",
                            retryable=False, code="payload_too_large")
    body = {"taskType": "response", "input": input_text}
    req_hash = hashlib.sha256(json.dumps(body, ensure_ascii=False).encode()).hexdigest()
    rid = _reserve(conn, "reppo", "submit", job_id)
    sent, call_id = True, None
    started = time.monotonic()
    try:
        try:
            with httpx.Client(timeout=settings.reppo_timeout_s, transport=transport) as client:
                resp = client.post(f"{settings.reppo_base_url}/agents/evals", json=body,
                                   headers={"Authorization": f"Bearer {settings.reppo_api_key}"})
        except NOT_SENT as e:  # request never left
            sent = False
            call_id = _record(conn, provider="reppo", purpose="submit", job_id=job_id, request_sha256=req_hash, outcome="connect_error")
            raise ProviderError(f"Reppo connection failed: {type(e).__name__}.", retryable=True, code="provider_transport") from e
        except httpx.HTTPError as e:
            call_id = _record(conn, provider="reppo", purpose="submit", job_id=job_id, request_sha256=req_hash, outcome="outcome_unknown",
                              latency_ms=int((time.monotonic() - started) * 1000))
            raise ProviderError("The Reppo submission may have reached the provider; its outcome is unknown and it will not be resubmitted automatically.",
                                retryable=False, code="submission_unknown", outcome_unknown=True) from e
        latency = int((time.monotonic() - started) * 1000)
        data = _json(resp)
        path = _save_raw(f"reppo-submit-{req_hash[:16]}-{int(time.time())}.json", {"http_status": resp.status_code, "response": data})
        if resp.status_code >= 400:
            call_id = _record(conn, provider="reppo", purpose="submit", job_id=job_id, request_sha256=req_hash, http_status=resp.status_code,
                              outcome="http_error", latency_ms=latency, response_path=path)
            raise ProviderError(f"Reppo returned HTTP {resp.status_code}.", retryable=resp.status_code == 502,
                                code={401: "provider_auth", 402: "insufficient_credits"}.get(resp.status_code, "provider_http"))
        call_id = _record(conn, provider="reppo", purpose="submit", job_id=job_id, request_sha256=req_hash, http_status=resp.status_code,
                          outcome="ok", upstream_id=data.get("id"), latency_ms=latency, response_path=path)
    finally:
        allowance.settle(conn, rid, call_id, sent=sent)
    if not data.get("id"):
        raise ProviderError("Reppo accepted the request but returned no evaluation id.", retryable=False,
                            code="submission_unknown", outcome_unknown=True)
    return {"data": data, "payload_sha256": req_hash, "payload_bytes": size, "raw_path": path}


def reppo_get(conn, eval_id: str, *, job_id: str | None, transport=None) -> dict:
    if not _execution_allowed():
        raise ExecutionDisabled()
    if not settings.reppo_api_key:
        raise NotConfigured("Reppo")
    try:
        with httpx.Client(timeout=settings.reppo_timeout_s, transport=transport) as client:
            resp = client.get(f"{settings.reppo_base_url}/agents/evals/{eval_id}",
                              headers={"Authorization": f"Bearer {settings.reppo_api_key}"})
    except httpx.HTTPError as e:
        raise ProviderError(f"Reppo poll failed: {type(e).__name__}.", retryable=True, code="provider_transport") from e
    data = _json(resp)
    path = _save_raw(f"reppo-eval-{eval_id}-{int(time.time())}.json", {"http_status": resp.status_code, "response": data})
    _record(conn, provider="reppo", purpose="poll", job_id=job_id, http_status=resp.status_code,
            outcome="ok" if resp.status_code < 400 else "http_error", upstream_id=eval_id, response_path=path)
    if resp.status_code >= 400:
        raise ProviderError(f"Reppo poll returned HTTP {resp.status_code}.", retryable=resp.status_code >= 500, code="provider_http")
    return {"data": data, "raw_path": path}


def _json(resp: httpx.Response) -> dict:
    try:
        d = resp.json()
        return d if isinstance(d, dict) else {"body": d}
    except ValueError:
        return {"non_json_body": resp.text[:2000]}
