"""Published experiment export: derived from artifacts, sanitized, explicit failure when missing."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from evi import api

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public" / "evidence" / "experiments.v1.json"
pytestmark = pytest.mark.skipif(not PUB.exists(), reason="export not built")


def test_numbers_match_frozen_artifacts_and_null_finding_is_derived():
    pub = json.loads(PUB.read_text())
    for e in pub["experiments"]:
        d = ROOT / "artifacts" / "technical-proof" / e["experiment_id"]
        a2 = json.loads((d / "analysis-v2" / "summary.json").read_text())
        s1 = json.loads((d / "summary.json").read_text())
        assert e["measurements_analysis_v2"] == a2["by_arm"] and e["paired_analysis_v2"] == a2["paired"]
        assert e["historical_scoring_v1"]["by_arm"]["A"]["strict_correct"] == s1["by_arm"]["A"]["strict_correct"]
        assert (a2["by_arm"]["C"] == a2["by_arm"]["D"]) == e["finding"].startswith("Arm D equals arm C")
        assert e["reference"]["independently_reviewed"] is False and "pending" in e["reference"]["human_review_status"]


def test_export_is_sanitized():
    text = PUB.read_text()
    for banned in ("session", "cookie", "SERV_API_KEY", "REPPO_API_KEY", "chatcmpl", "Bearer", ".sqlite3", "prompt_sha256", "@"):
        assert banned not in text, banned


def test_missing_export_is_an_explicit_error(monkeypatch, tmp_path):
    monkeypatch.setenv("EVI_PUBLIC_EVIDENCE", str(tmp_path / "missing.json"))
    with TestClient(api.app) as c:
        r = c.get("/api/v1/experiments")
        assert r.status_code == 503 and r.json()["error"]["code"] == "evidence_unavailable"
