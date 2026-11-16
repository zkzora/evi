"""Local integration check for the judge upload path (no provider call; no paid work).

Uploads a COPY of an already-registered public report through the real API route into an ISOLATED data dir, then runs
a FRESH Docling parse of exactly one physical page and the upload column derivation. Checks source identity, page and
coordinate mapping, and that derived columns match the frozen targets for that report. This is a development check on
known material, not an unseen benchmark and not evidence of generalisation.

Usage: PYTHONIOENCODING=utf-8 backend/.venv/Scripts/python scripts/upload_local_integration.py
Writes artifacts/judge-upload/local-integration.json
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["EVI_DATA_DIR"] = tempfile.mkdtemp(prefix="evi-upload-it-")
os.environ["EVI_EXECUTION_ENABLED"] = "false"            # no provider can be reached from this check
os.environ["SERV_API_KEY"] = ""
os.environ["REPPO_API_KEY"] = ""
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from evi import api, db, uploads  # noqa: E402
from evi.corpus import REGISTERED  # noqa: E402
from evi.parsing import parse_document  # noqa: E402
from evi.targets import COLUMNS  # noqa: E402

SRC = "verizon-3q2025"
entry = next(r for r in REGISTERED if r["document_id"] == SRC)
pdf = (ROOT / "public" / "sources" / entry["file_name"]).read_bytes()
page = entry["source_page"]
out = {"source_copy_of": SRC, "selected_physical_page": page, "provider_calls_before": None}

with TestClient(api.app) as cl:
    r = cl.post("/api/v1/uploads", files={"file": ("my-telecom-report.pdf", pdf, "application/pdf")},
                headers={"Origin": "http://127.0.0.1:5173"})
    d = r.json()
    out["upload_status"] = r.status_code
    did = d["document_id"]
    c = db.connect()
    out["provider_calls_before"] = c.execute("SELECT COUNT(*) FROM provider_calls").fetchone()[0]
    out["jobs_after_upload"] = c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    parse_id = parse_document(c, did, [page])                       # fresh Docling parse of ONE page
    p = db.row(c, "SELECT * FROM parses WHERE parse_id=?", parse_id)
    ev = db.rows(c, "SELECT page_number, bbox_json, page_width, page_height FROM evidence WHERE parse_id=?", parse_id)
    cols, derivation = uploads.derive_columns(c, did, parse_id)
    in_page = all(json.loads(e["bbox_json"])["right"] <= e["page_width"] + 1 and json.loads(e["bbox_json"])["top"] <= e["page_height"] + 1
                  for e in ev if e["bbox_json"])
    out.update({
        "uploaded_document_id_prefix": did[:4],
        "sha256_matches_registered_source": d["sha256"] == entry["sha256"],
        "page_count": d["page_count"], "registered_page_count": entry["page_count"],
        "parse_pages": json.loads(p["pages_json"]), "parse_fresh": True,
        "parse_duration_ms": p["duration_ms"], "tables": p["table_count"], "evidence_items": p["evidence_count"],
        "evidence_pages": sorted({e["page_number"] for e in ev}),
        "evidence_bboxes_inside_page": in_page,
        "derived_columns": cols, "frozen_columns_for_this_report": [list(x) for x in COLUMNS[SRC]],
        "derived_equals_frozen": sorted(map(tuple, cols)) == sorted(COLUMNS[SRC]),
        "derivation": derivation,
        "provider_calls_after": c.execute("SELECT COUNT(*) FROM provider_calls").fetchone()[0],
        "other_session_source_status": TestClient(api.app).get(f"/api/v1/documents/{did}/source").status_code,
    })

dest = ROOT / "artifacts" / "judge-upload"
dest.mkdir(parents=True, exist_ok=True)
(dest / "local-integration.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out, indent=1))
ok = (out["upload_status"] == 201 and out["sha256_matches_registered_source"] and out["evidence_pages"] == [page]
      and out["evidence_bboxes_inside_page"] and out["provider_calls_after"] == out["provider_calls_before"] == 0
      and out["other_session_source_status"] == 404)
sys.exit(0 if ok else 1)
