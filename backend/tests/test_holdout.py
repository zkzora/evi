"""Holdout freeze/preflight/stage gates (temporary directories; no source acquisition, no provider calls)."""
import json

import pytest

from evi import holdout


@pytest.fixture()
def tmp_holdout(tmp_path, monkeypatch):
    monkeypatch.setattr(holdout, "HOLDOUT", tmp_path / "holdout")
    monkeypatch.delenv("EVI_SOURCE_REGISTRY", raising=False)
    monkeypatch.delenv("EVI_TARGET_REGISTRY", raising=False)
    return tmp_path


def test_freeze_records_policy_hashes_and_opens_no_source(tmp_holdout):
    fr = holdout.freeze("h-test")
    assert fr["status"].startswith("frozen; no candidate source")
    assert "backend/evi/binding.py" in fr["code_sha256"] and fr["policies"]["reppo_packet"] == "reppo-packet-v2"
    assert "NOT a claim that the public reports are absent" in fr["exposure"]["claim"]
    with pytest.raises(SystemExit, match="already frozen"):
        holdout.freeze("h-test")


def test_preflight_detects_drift_and_unmet_gates(tmp_holdout):
    holdout.freeze("h-test")
    pf = holdout.preflight("h-test")
    assert pf["drifted_files"] == [] and pf["runnable"] is False and pf["gates"]["approval_file"] is False
    fp = tmp_holdout / "holdout" / "h-test" / "freeze.json"
    fr = json.loads(fp.read_text())
    fr["code_sha256"]["backend/evi/binding.py"] = "0" * 64     # simulate a policy change after freeze
    fp.write_text(json.dumps(fr))
    assert holdout.preflight("h-test")["drifted_files"] == ["backend/evi/binding.py"]
    with pytest.raises(SystemExit, match="policy changed since freeze"):
        holdout.stage_run("h-test")


def test_stage_run_refuses_without_registered_sources(tmp_holdout):
    holdout.freeze("h-test")
    with pytest.raises(SystemExit, match="source_registry"):
        holdout.stage_run("h-test")


def test_registries_cannot_redefine_historical_targets(tmp_path, monkeypatch):
    from evi import targets
    p = tmp_path / "t.json"
    p.write_text(json.dumps({"verizon-fy2025": [[12, 2030]]}))
    monkeypatch.setenv("EVI_TARGET_REGISTRY", str(p))
    with pytest.raises(ValueError, match="historical"):
        targets.targets_for("verizon-fy2025")
    p.write_text(json.dumps({"newco-fy2025": [[12, 2025], [12, 2024]]}))
    assert len(targets.targets_for("newco-fy2025")) == 6 and len(targets.all_targets()) == 48
