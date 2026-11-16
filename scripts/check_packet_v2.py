"""Offline completeness check of reppo-packet-v2 for every version Reppo evaluated (no provider calls).
The check (not the packet builder) reads references to test that the CORRECT value would be discoverable.

Usage: backend/.venv/Scripts/python scripts/check_packet_v2.py
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from evi import binding, evaluation, targets  # noqa: E402
from evi.replay import connect_ro  # noqa: E402

OUT = ROOT / "artifacts" / "reppo-packet-v2"
conn = connect_ro()
refs = {r["target_key"]: r for r in json.loads((ROOT / "data" / "references" / "references-v1.json").read_text())["items"]}
report, ok_all = [], True
(OUT / "dry-run").mkdir(parents=True, exist_ok=True)
for ev in conn.execute("SELECT evaluation_id, eval_id, version_id FROM evaluations ORDER BY created_at").fetchall():
    vid = ev["version_id"]
    text = evaluation.build_input_v2(conn, vid)
    pk = json.loads(text)
    (OUT / "dry-run" / f"{vid}.packet-v2.json").write_text(text, encoding="utf-8")
    flat = json.dumps(pk["full_statement_tables"])
    doc = pk["candidate_response"]["facts"][0]["target_key"].split(":")[0]
    run = conn.execute("SELECT parse_id FROM runs WHERE run_id=(SELECT run_id FROM versions WHERE version_id=?)", (vid,)).fetchone()
    s = binding.load_structure(conn, run["parse_id"])
    n_cells = sum(1 for t in s.tables for c in t.cells if c.text)
    n_in = sum(len(r["cells"]) for t in pk["full_statement_tables"] for r in t["rows"])
    checks = {
        "bytes": len(text.encode("utf-8")), "within_50KB": len(text.encode("utf-8")) <= 50_000,
        "all_table_cells_included": n_in == n_cells, "cells": f"{n_in}/{n_cells}",
        "all_targets_listed": sorted(t["target_key"] for t in pk["requested_targets"]) == sorted(t["target_key"] for t in targets.targets_for(doc)),
        "candidate_separate": pk["candidate_response"]["version_id"] == vid,
        "correct_row_label_and_value_present_for_every_target": all(
            refs[k]["row_label"].lower() in flat.lower() and refs[k]["printed_amount"] in flat for k in (t["target_key"] for t in targets.targets_for(doc))),
        "unit_statement_present": "in millions" in text.lower(),
        "no_reference_fields_in_packet": "references-v1" not in text and "date_basis" not in text,
    }
    good = all(v for k, v in checks.items() if isinstance(v, bool))
    ok_all &= good
    report.append({"evaluation_id": ev["evaluation_id"], "reppo_eval_id_v1": ev["eval_id"], "version_id": vid, "document": doc,
                   "packet_sha256": hashlib.sha256(text.encode()).hexdigest(), "checks": checks, "pass": good,
                   "note": "dry run only; never submitted; the v1 evaluation of this version is NOT reused for v2"})
    print(vid, doc, checks["bytes"], checks["cells"], "PASS" if good else "FAIL")
(OUT / "completeness-report.json").write_text(json.dumps({"packet_version": evaluation.PACKET_V2, "provider_calls": 0, "items": report}, indent=1))
print("ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)
