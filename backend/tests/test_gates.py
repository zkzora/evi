"""Spending/execution gates: configured keys are not budget approval; disabled execution blocks providers and new jobs."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from evi import api, authorization, db, experiment, providers
from evi.config import settings


def test_execution_disabled_blocks_provider_calls_before_any_request(monkeypatch):
    monkeypatch.setattr(settings.__class__, "execution_enabled", property(lambda s: False))
    monkeypatch.setattr(settings.__class__, "serv_api_key", property(lambda s: "k"))
    monkeypatch.setattr(settings.__class__, "reppo_api_key", property(lambda s: "k"))
    sent = []
    monkeypatch.setattr(providers.httpx, "Client", lambda *a, **k: sent.append(1))
    c = db.connect()
    db.init(c)
    with pytest.raises(providers.ExecutionDisabled):
        providers.serv_chat(c, purpose="x", messages=[], schema_name="s", schema={}, run_id=None, job_id=None)
    with pytest.raises(providers.ExecutionDisabled):
        providers.reppo_submit(c, input_text="x", job_id="j")
    assert sent == []


def test_api_reports_and_enforces_disabled_execution(monkeypatch):
    monkeypatch.setattr(settings.__class__, "execution_enabled", property(lambda s: False))
    with TestClient(api.app) as client:
        h = client.get("/api/v1/health").json()
        assert h["execution_enabled"] is False and h["processing_enabled"] is False and h["live_execution_enabled"] is False
        r = client.post("/api/v1/documents/verizon-fy2024/parse", json={})
        assert r.status_code == 503 and r.json()["error"]["code"] == "execution_disabled"


def _exp(tmp_path, monkeypatch):
    d = tmp_path / "exp-x"
    d.mkdir()
    (d / "manifest.json").write_text(json.dumps({"caps": {"serv_calls": 4, "reppo_evals": 2}, "trial_plan": {"schedule": []}}))
    monkeypatch.setattr(experiment, "PROOF", tmp_path)
    monkeypatch.setattr(authorization, "APPROVALS", tmp_path / "approvals")
    return d


def test_experiment_run_refuses_without_flag_and_approval(tmp_path, monkeypatch):
    _exp(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="EVI_ALLOW_PAID_RUNS"):
        experiment.run("exp-x")
    monkeypatch.setenv("EVI_ALLOW_PAID_RUNS", "1")
    with pytest.raises(SystemExit, match="No approval file"):
        experiment.run("exp-x")


def test_unfilled_template_or_low_caps_or_other_manifest_rejected(tmp_path, monkeypatch):
    d = _exp(tmp_path, monkeypatch)
    monkeypatch.setenv("EVI_ALLOW_PAID_RUNS", "1")
    (tmp_path / "approvals").mkdir()
    ap = tmp_path / "approvals" / "exp-x.approval.json"
    t = authorization.template("exp-x", d)
    ap.write_text(json.dumps(t))
    with pytest.raises(authorization.NotAuthorized, match="unfilled"):
        authorization.require_approval("exp-x", d, json.loads((d / "manifest.json").read_text()))
    t.update(approved_by="Test Approver (TEST ONLY)", approved_at="2026-11-16", approval_text="test", max_reppo_credits=100)
    ap.write_text(json.dumps(t))
    with pytest.raises(authorization.NotAuthorized, match="max_reppo_credits"):
        authorization.require_approval("exp-x", d, json.loads((d / "manifest.json").read_text()))
    t.update(max_reppo_credits=880, manifest_sha256="0" * 64)
    ap.write_text(json.dumps(t))
    with pytest.raises(authorization.NotAuthorized, match="different manifest"):
        authorization.require_approval("exp-x", d, json.loads((d / "manifest.json").read_text()))


def test_dry_run_makes_no_calls(tmp_path, monkeypatch, capsys):
    _exp(tmp_path, monkeypatch)
    experiment.run("exp-x", dry_run=True)
    assert '"dry_run": true' in capsys.readouterr().out
