"""Deployment configuration and same-origin production routing (no network, no Docker)."""
import os
import re
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


def test_build_context_excludes_secrets_and_runtime_state():
    ignore = (ROOT / ".dockerignore").read_text()
    for pat in ("**/.env", "backend/.venv", "data/runs", "data/references/review", "artifacts", "deploy/production.env", "**/*.sqlite3*"):
        assert pat in ignore, pat
    gi = (ROOT / ".gitignore").read_text()
    assert "backend/.env" in gi and "deploy/production.env" in gi


def test_production_env_example_is_blank_and_disabled():
    env = dict(l.split("=", 1) for l in (ROOT / "deploy" / "production.env.example").read_text().splitlines() if "=" in l and not l.startswith("#"))
    assert env["SERV_API_KEY"] == "" and env["REPPO_API_KEY"] == "" and env["EVI_EXECUTION_ENABLED"] == "false"


def test_image_and_bundle_carry_no_provider_secrets():
    df = (ROOT / "Dockerfile").read_text()
    assert "SERV_API_KEY" not in df and "REPPO_API_KEY" not in df and "EVI_EXECUTION_ENABLED=false" in df
    assert not re.search(r"VITE_[A-Z_]*(KEY|TOKEN|SECRET)", df)
    for p in (ROOT / "src").rglob("*.ts*"):
        assert "SERV_API_KEY" not in p.read_text(encoding="utf-8") and "REPPO_API_KEY" not in p.read_text(encoding="utf-8"), p


def test_same_origin_spa_routing(tmp_path, monkeypatch):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<!doctype html><title>Evi</title>")
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    monkeypatch.setenv("EVI_STATIC_DIR", str(tmp_path))
    from evi import api
    api._mount_static()
    with TestClient(api.app) as c:
        deep = c.get("/workspace?document=att-2q2025")
        assert deep.status_code == 200 and "<title>Evi</title>" in deep.text
        assert c.get("/assets/app.js").headers["cache-control"].startswith("public, max-age=31536000")
        r = c.get("/api/v1/does-not-exist")
        assert r.status_code == 404 and r.headers["content-type"].startswith("application/json")
        assert c.get("/api/other").headers["content-type"].startswith("application/json")
        assert c.get("/../backend/.env").status_code in (200, 404) and "SERV_API_KEY" not in c.get("/../backend/.env").text
        h = c.get("/api/v1/health").json()
        assert "execution_enabled" in h and h["status"] == "ok"
        rd = c.get("/api/v1/ready")
        assert rd.headers["content-type"].startswith("application/json") and "checks" in rd.json()


def test_backup_and_restore_roundtrip(tmp_path):
    import json
    import sqlite3

    from evi import backup
    data = tmp_path / "data"
    (data / "artifacts" / "parses").mkdir(parents=True)
    (data / "artifacts" / "parses" / "p1.docling.json").write_text("{}")
    c = sqlite3.connect(data / "evi.sqlite3")
    c.execute("CREATE TABLE parses (parse_id TEXT, artifact_path TEXT)")
    c.execute("INSERT INTO parses VALUES ('p1', ?)", (str(data / "artifacts" / "parses" / "p1.docling.json"),))
    c.commit(); c.close()
    src = tmp_path / "src"; src.mkdir(); (src / "a.pdf").write_bytes(b"%PDF-1")
    out = backup.create(tmp_path / "bk", data, src)
    bdir = Path(out["backup"])
    assert out["integrity_check"] == "ok" and backup.verify(bdir) == []
    res = backup.restore(bdir, tmp_path / "restored", tmp_path / "src2")
    assert res["integrity_check"] == "ok" and (tmp_path / "src2" / "a.pdf").exists()
    row = sqlite3.connect(tmp_path / "restored" / "evi.sqlite3").execute("SELECT artifact_path FROM parses").fetchone()[0]
    assert Path(row).exists()
    (bdir / "artifacts" / "parses" / "p1.docling.json").write_text('{"tampered": 1}')
    assert backup.verify(bdir)
    import pytest
    with pytest.raises(SystemExit):
        backup.restore(bdir, tmp_path / "restored2")
    with pytest.raises(SystemExit, match="not empty"):
        backup.restore(Path(backup.create(tmp_path / "bk2", data, src)["backup"]), tmp_path / "restored")


def test_rebase_handles_windows_paths_on_any_os(tmp_path):
    import sqlite3

    from evi import backup
    (tmp_path / "artifacts" / "parses").mkdir(parents=True)
    (tmp_path / "artifacts" / "parses" / "parse_x.docling.json").write_text("{}")
    c = sqlite3.connect(tmp_path / "evi.sqlite3")
    c.execute("CREATE TABLE parses (parse_id TEXT, artifact_path TEXT)")
    c.execute("INSERT INTO parses VALUES ('p', ?)", (r"C:\Evidence\repo\data\runs\artifacts\parses\parse_x.docling.json",))
    c.commit(); c.close()
    assert backup.rebase(tmp_path) == 1
    row = sqlite3.connect(tmp_path / "evi.sqlite3").execute("SELECT artifact_path FROM parses").fetchone()[0]
    assert row.endswith("parse_x.docling.json") and "Evidence" not in row
    assert backup.rebase(tmp_path) == 0          # idempotent
