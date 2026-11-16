"""Issue support certificates for an immutable version WITHOUT modifying it (a new check-run artifact).

CLI:
  python -m evi.certify <version_id>            # issue/refresh certificates for every fact of a version
  python -m evi.certify --verify <certificate_id|path.json>   # re-verify from registered source + Docling artifact
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from . import binding, db
from .config import settings
from .targets import target_for_fact

CERT_DIR = settings.artifacts_dir / "certificates"


def fact_hash(fact: dict) -> str:
    return hashlib.sha256(binding.canonical(fact).encode()).hexdigest()


def certify_version(conn, version_id: str) -> dict:
    v = db.row(conn, "SELECT * FROM versions WHERE version_id=?", version_id)
    if v is None:
        raise KeyError(version_id)
    body = json.loads(v["body_json"])
    run = db.row(conn, "SELECT * FROM runs WHERE run_id=?", v["run_id"])
    check_run_id = db.new_id("chk")
    issued, summary = [], {}
    for f in body["facts"]:
        target = target_for_fact(run["document_id"], f)
        if target is None:
            summary[f["fact_id"]] = {"claim_outcome": "no_frozen_target", "detail": "fact does not map to a targets-v1 column"}
            continue
        cert = binding.build_certificate(conn, document_id=run["document_id"], parse_id=run["parse_id"], target=target, fact=f,
                                         fact_ref={"version_id": version_id, "fact_id": f["fact_id"], "fact_sha256": fact_hash(f),
                                                   "version_content_sha256": v["content_sha256"]})
        cid = "cert_" + cert["content_sha256"][:20]
        CERT_DIR.mkdir(parents=True, exist_ok=True)
        path = CERT_DIR / f"{cid}.json"
        path.write_text(json.dumps(cert, indent=1, ensure_ascii=False), encoding="utf-8")
        conn.execute("INSERT OR IGNORE INTO certificates VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (cid, version_id, f["fact_id"], fact_hash(f), run["document_id"], run["parse_id"], target["target_key"],
                      binding.POLICY_VERSION, cert["claim_outcome"], cert["resolution"]["outcome"], cert["content_sha256"],
                      json.dumps(cert, ensure_ascii=False), check_run_id, db.now()))
        issued.append(cid)
        summary[f["fact_id"]] = {"certificate_id": cid, "target_key": target["target_key"], "claim_outcome": cert["claim_outcome"],
                                 "resolution": cert["resolution"]["outcome"],
                                 "failed_fields": [x["field"] for x in cert["field_verdicts"] if x["status"] == "fail"]}
    orig = hashlib.sha256(binding.canonical(body["checks"]).encode()).hexdigest()
    conn.execute("INSERT INTO check_runs VALUES (?,?,?,?,?,?,?)",
                 (check_run_id, version_id, v["content_sha256"], binding.POLICY_VERSION, orig,
                  json.dumps({"facts": summary, "note": "Re-evaluation under a new policy; the version and its original "
                              "checks are unchanged."}), db.now()))
    return {"check_run_id": check_run_id, "certificates": issued, "facts": summary}


def load_cert(conn, ref: str) -> dict:
    p = Path(ref)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    r = db.row(conn, "SELECT body_json FROM certificates WHERE certificate_id=?", ref)
    if r is None:
        raise KeyError(ref)
    return json.loads(r["body_json"])


def main(argv: list[str]) -> int:
    conn = db.connect()
    db.init(conn)
    if argv[:1] == ["--verify"]:
        ok_all = True
        for ref in argv[1:]:
            ok, problems = binding.verify_certificate(conn, load_cert(conn, ref))
            ok_all &= ok
            print(f"{ref}: {'VERIFIED' if ok else 'FAILED'}")
            for pr in problems:
                print(f"  - {pr}")
        return 0 if ok_all else 1
    for vid in argv:
        out = certify_version(conn, vid)
        print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
