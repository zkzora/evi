"""Read-only replay/verification of an executed experiment (replay-v2, 2026-11-16).

  python -m evi.replay <exp_id>            # experiment-specific replay
  python -m evi.replay --all-certificates  # separate all-history audit of every stored certificate

Coverage is DERIVED from the frozen manifest, the expected ledger branches, the frozen target set and the actual
version contents. Every expected (version, target) must carry a certificate issued under the binding policy the
manifest names; certificates under other policies never substitute. Missing, duplicate-conflicting, wrong-policy and
unknown-policy certificates, missing branches, identity mismatches and score differences all FAIL. The database is
opened read-only; nothing is written; no provider is called. replay-v1 (which filtered binding-v2 for every experiment
and re-wrote summary files before comparing) is superseded.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

from . import binding
from .config import settings
from .corpus import sha256_file, source_path
from .experiment import PROOF
from .targets import targets_for

REPLAY_VERSION = "replay-v2"
ARMS = ("A", "B", "C", "D")


def connect_ro(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{(path or settings.db_path).as_posix()}?mode=ro", uri=True, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def _rows(conn, sql, *a):
    return conn.execute(sql, a).fetchall()


def _row(conn, sql, *a):
    return conn.execute(sql, a).fetchone()


def expected_branches(m: dict) -> list[tuple[int, str]]:
    if m.get("branches"):
        return [(b["trial"], b["document_id"]) for b in m["branches"]]
    return [(s["trial"], s["document_id"]) for s in m["trial_plan"]["schedule"]]


def _semantic(cert: dict) -> str:
    return binding.canonical({k: cert.get(k) for k in ("claim", "claim_outcome", "field_verdicts", "claim_cell_reading", "resolution")})


def replay(exp_id: str, conn: sqlite3.Connection | None = None, proof_dir: Path | None = None,
           refs_path: Path | None = None, verify_certificates: bool = True) -> dict:
    base = (proof_dir or PROOF) / exp_id
    conn = conn or connect_ro()
    P: list[str] = []
    rep: dict = {"experiment_id": exp_id, "replay_version": REPLAY_VERSION}
    m = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    rep["manifest_sha256"] = hashlib.sha256((base / "manifest.json").read_bytes()).hexdigest()
    policy = m.get("policies", {}).get("binding")
    rep["required_policy"] = policy
    if policy not in binding.SUPPORTED_POLICIES:
        P.append(f"manifest names unknown binding policy {policy!r}")
    calls_before = _row(conn, "SELECT COUNT(*) n FROM provider_calls")["n"]
    budget_before = _row(conn, "SELECT COUNT(*) n FROM budget_ledger")["n"]

    # references
    rp = refs_path or (Path(__file__).resolve().parents[2] / m["reference"]["path"])
    ref_sha = hashlib.sha256(rp.read_bytes()).hexdigest() if rp.exists() else None
    if ref_sha != m["reference"]["sha256"]:
        P.append("reference file hash differs from the manifest")
    if "provisional" not in (m["reference"].get("provenance") or ""):
        P.append("reference provenance label missing or changed")

    # sources and parses
    for src in m["sources"]:
        d = _row(conn, "SELECT * FROM documents WHERE document_id=?", src["document_id"])
        if d is None or d["sha256"] != src["sha256"] or sha256_file(source_path(d)) != src["sha256"]:
            P.append(f"source {src['document_id']} missing or changed")
    parse_of = {}
    for p in m["parses"]:
        r = _row(conn, "SELECT * FROM parses WHERE parse_id=?", p["parse_id"])
        if r is None or r["cache_key"] != p["cache_key"] or r["document_id"] != p["document_id"] or \
                hashlib.sha256(Path(r["artifact_path"]).read_bytes()).hexdigest() != p["docling_artifact_sha256"]:
            P.append(f"parse {p['parse_id']} missing or changed")
        parse_of[p["document_id"]] = p["parse_id"]

    # ledger branches
    lp = base / "ledger.jsonl"
    ledger = [json.loads(l) for l in lp.read_text(encoding="utf-8").splitlines()] if lp.exists() else []
    by_key: dict = defaultdict(list)
    for r in ledger:
        by_key[(r["trial"], r["document_id"], r["arm"])].append(r)
    exp_br = expected_branches(m)
    counts = {"expected_branches": len(exp_br) * len(ARMS), "ledger_records": len(ledger), "missing_branches": 0,
              "duplicate_branches": 0, "executed_branches": 0}
    executed: list[dict] = []
    for t, doc in exp_br:
        for arm in ARMS:
            recs = by_key.get((t, doc, arm), [])
            if not recs:
                counts["missing_branches"] += 1
                P.append(f"ledger has no record for trial {t} {doc} arm {arm}")
                continue
            if len(recs) > 1:
                counts["duplicate_branches"] += 1
                P.append(f"ledger has {len(recs)} records for trial {t} {doc} arm {arm}")
            r = recs[-1]
            if r.get("executed") and r.get("version_id") and not r.get("failed"):
                counts["executed_branches"] += 1
                executed.append({**r, "trial": t, "document_id": doc, "arm": arm})
    rep["branches"] = counts

    # versions: identity, ownership, target set
    versions: dict[str, dict] = {}
    for r in executed:
        vid = r["version_id"]
        if vid in versions:
            continue
        v = _row(conn, "SELECT * FROM versions WHERE version_id=?", vid)
        if v is None:
            P.append(f"version {vid} missing"); continue
        if hashlib.sha256(v["body_json"].encode()).hexdigest() != v["content_sha256"]:
            P.append(f"version {vid} content hash mismatch")
        run = _row(conn, "SELECT * FROM runs WHERE run_id=?", v["run_id"])
        if run is None or run["document_id"] != r["document_id"] or run["parse_id"] != parse_of.get(r["document_id"]):
            P.append(f"version {vid} does not belong to {r['document_id']} / manifest parse")
        body = json.loads(v["body_json"])
        keys = [f.get("target_key") for f in body["facts"]]
        want = [t["target_key"] for t in targets_for(r["document_id"])]
        if sorted(keys) != sorted(want) or len(set(keys)) != len(keys):
            P.append(f"version {vid} target set differs from the frozen targets (missing/extra/duplicate)")
        versions[vid] = {"doc": r["document_id"], "facts": {f.get("target_key"): f for f in body["facts"]}, "body": body}
    rep["unique_versions"] = len(versions)
    rep["branch_version_sharing"] = "A and B share one version per branch (B = certificates over A); C and D are distinct children"

    # required certificates
    cc = {"expected": 0, "found": 0, "verified": 0, "missing": 0, "conflicting": 0, "consistent_duplicates": 0,
          "wrong_policy_only": 0, "unknown_policy_rows": 0, "identity_mismatch": 0, "verification_failed": 0}
    for vid, info in versions.items():
        rows = _rows(conn, "SELECT certificate_id, fact_id, target_key, policy_version, body_json FROM certificates WHERE version_id=?", vid)
        for r in rows:
            if r["policy_version"] not in binding.SUPPORTED_POLICIES:
                cc["unknown_policy_rows"] += 1
                P.append(f"certificate {r['certificate_id']} has unknown policy {r['policy_version']}")
        for tk, fact in info["facts"].items():
            cc["expected"] += 1
            mine = [r for r in rows if r["target_key"] == tk and r["policy_version"] == policy]
            if not mine:
                cc["missing"] += 1
                if any(r["target_key"] == tk for r in rows):
                    cc["wrong_policy_only"] += 1
                    P.append(f"{vid} {tk}: only certificates under other policies ({sorted({r['policy_version'] for r in rows if r['target_key'] == tk})}); {policy} required")
                else:
                    P.append(f"{vid} {tk}: no certificate")
                continue
            cc["found"] += 1
            bodies = [json.loads(r["body_json"]) for r in mine]
            if len({_semantic(b) for b in bodies}) > 1:
                cc["conflicting"] += 1
                P.append(f"{vid} {tk}: {len(bodies)} conflicting {policy} certificates")
                continue
            if len(bodies) > 1:
                cc["consistent_duplicates"] += 1
            cert = bodies[-1]
            if cert.get("policy_version") != policy or cert["target"]["target_key"] != tk or \
                    binding.canonical(cert.get("claim")) != binding.canonical(binding.claim_from_fact(fact)) or \
                    any(r["fact_id"] not in (None, fact["fact_id"]) for r in mine):
                cc["identity_mismatch"] += 1
                P.append(f"{vid} {tk}: certificate claim/policy/fact identity does not match the version")
                continue
            if verify_certificates:
                ok, why = binding.verify_certificate(conn, cert)
                if not ok:
                    cc["verification_failed"] += 1
                    P.append(f"{vid} {tk}: re-verification failed: {why[:2]}")
                    continue
            cc["verified"] += 1
    rep["certificates"] = cc

    # receipts and evaluations
    rc = {"expected": 0, "ok": 0, "problems": 0}
    a_of = {(r["trial"], r["document_id"]): r["version_id"] for r in executed if r["arm"] == "A"}
    for r in executed:
        if r["arm"] not in ("C", "D"):
            continue
        rc["expected"] += 1
        key = f"{exp_id}:t{r['trial']}:{r['document_id']}:{r['arm']}"
        x = _row(conn, "SELECT * FROM revision_receipts WHERE idempotency_key=?", key)
        bad = []
        if x is None:
            bad.append("missing receipt")
        else:
            body = json.loads(x["body_json"])
            claimed = body.pop("content_sha256", None)
            if hashlib.sha256(binding.canonical(body).encode()).hexdigest() != claimed or claimed != x["content_sha256"]:
                bad.append("receipt hash")
            if x["child_version_id"] != r["version_id"] or x["parent_version_id"] != a_of.get((r["trial"], r["document_id"])):
                bad.append("receipt parent/child differ from ledger")
            child = _row(conn, "SELECT parent_version_id FROM versions WHERE version_id=?", x["child_version_id"])
            if child is None or child["parent_version_id"] != x["parent_version_id"]:
                bad.append("child version parent link")
            if r["arm"] == "D":
                ev = _row(conn, "SELECT * FROM evaluations WHERE evaluation_id=?", x["evaluation_id"] or "")
                if ev is None or ev["version_id"] != x["parent_version_id"] or ev["mode"] != "reppo_live" or ev["status"] != "completed":
                    bad.append("arm D evaluation does not belong to the parent or is not a completed live evaluation")
            elif x["evaluation_id"]:
                bad.append("arm C receipt carries an evaluation")
        if bad:
            rc["problems"] += 1
            P.append(f"receipt {key}: {', '.join(bad)}")
        else:
            rc["ok"] += 1
    rep["receipts"] = rc

    # score recomputed in memory, compared with saved expected artifacts
    from .scoring import compute
    try:
        outcomes, summary, text = compute(exp_id, conn=conn, base=base, refs_path=rp)
        saved_s = json.loads((base / "summary.json").read_text(encoding="utf-8"))
        saved_o = [json.loads(l) for l in (base / "outcomes.jsonl").read_text(encoding="utf-8").splitlines()]
        rep["score"] = {"summary_identical": binding.canonical(saved_s) == binding.canonical(summary),
                        "outcomes_identical": saved_o == outcomes,
                        "report_identical": (base / "report.md").read_text(encoding="utf-8") == text}
        for k, v in rep["score"].items():
            if not v:
                P.append(f"recomputed score: {k} is False")
    except Exception as e:  # noqa: BLE001
        P.append(f"score recomputation failed: {type(e).__name__}: {e}")

    rep["provider_calls_unchanged"] = _row(conn, "SELECT COUNT(*) n FROM provider_calls")["n"] == calls_before
    rep["budget_ledger_unchanged"] = _row(conn, "SELECT COUNT(*) n FROM budget_ledger")["n"] == budget_before
    rep["problems"] = P
    rep["result"] = "VERIFIED" if not P else "FAILED"
    return rep


def audit_all_certificates(conn: sqlite3.Connection | None = None) -> dict:
    """All-history audit: every stored certificate re-verified under its own issued policy. Separate from, and not a
    substitute for, experiment-specific coverage."""
    conn = conn or connect_ro()
    out: dict = defaultdict(lambda: {"verified": 0, "failed": 0})
    fails = []
    for r in _rows(conn, "SELECT certificate_id, policy_version, body_json FROM certificates"):
        ok, why = binding.verify_certificate(conn, json.loads(r["body_json"]))
        out[r["policy_version"]]["verified" if ok else "failed"] += 1
        if not ok:
            fails.append((r["certificate_id"], why[:2]))
    return {"by_policy": dict(out), "failures": fails}


def main(argv: list[str]) -> int:
    if argv[:1] == ["--all-certificates"]:
        res = audit_all_certificates()
        print(json.dumps(res, indent=1))
        return 0 if not res["failures"] else 1
    rep = replay(argv[0])
    print(f"REPLAY {rep['replay_version']} of {rep['experiment_id']} (read-only, no provider calls); manifest {rep['manifest_sha256']}")
    print(f"  required binding policy: {rep['required_policy']}")
    print(f"  branches: {json.dumps(rep['branches'])}; unique versions: {rep.get('unique_versions')}")
    print(f"  certificates: {json.dumps(rep['certificates'])}")
    print(f"  receipts: {json.dumps(rep['receipts'])}")
    print(f"  score: {json.dumps(rep.get('score'))}")
    print(f"  provider calls unchanged: {rep['provider_calls_unchanged']}; budget ledger unchanged: {rep['budget_ledger_unchanged']}")
    print("RESULT:", rep["result"])
    for p in rep["problems"][:40]:
        print("  -", p)
    if len(rep["problems"]) > 40:
        print(f"  ... {len(rep['problems']) - 40} more")
    return 0 if rep["result"] == "VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
