"""Build the public, sanitized experiment export (schema evi.public-experiments/1) from frozen artifacts.

Usage: backend/.venv/Scripts/python scripts/build_public_evidence.py
Writes public/evidence/experiments.v1.json (served statically and by GET /api/v1/experiments).
Every number is read from the experiment artifacts; nothing is typed in. Explicit allowlist: no credentials, sessions,
cookies, prompts, SERV completion/call identifiers, account metadata or database files.
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
PROOF = ROOT / "artifacts" / "technical-proof"
OUT = ROOT / "public" / "evidence" / "experiments.v1.json"
REPO = "https://github.com/zkzora/evi/blob/main/"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    from evi.replay import connect_ro
    conn = connect_ro(ROOT / "data" / "runs" / "evi.sqlite3") if (ROOT / "data" / "runs" / "evi.sqlite3").exists() else \
        connect_ro(ROOT / "data" / "release-snapshot" / "evi.sqlite3")
    sheet = json.loads((ROOT / "data" / "references" / "review" / "review-sheet-references-v1.json").read_text())
    review = dict(Counter(i["review_status"] for i in sheet["items"]))
    docs = {r["document_id"]: dict(r) for r in conn.execute("SELECT document_id, issuer_name, title, source_url, sha256, parse_pages, page_count FROM documents")}
    exps = []
    for exp_id in ("exp-2026-11-16-a", "exp-2026-11-16-b"):
        d = PROOF / exp_id
        m = json.loads((d / "manifest.json").read_text())
        s1 = json.loads((d / "summary.json").read_text())
        a2 = json.loads((d / "analysis-v2" / "summary.json").read_text())
        rec = json.loads((d / "analysis-v2" / "reconciliation.json").read_text())
        ledger = [json.loads(l) for l in (d / "ledger.jsonl").read_text().splitlines()]
        evals = []
        for r in ledger:
            x = r.get("reppo")
            if not x:
                continue
            row = conn.execute("SELECT * FROM evaluations WHERE evaluation_id=?", (x["evaluation_id"],)).fetchone()
            res = json.loads(row["result_json"]) if row and row["result_json"] else {}
            evals.append({"evaluation_id": x["evaluation_id"], "reppo_eval_id": x["eval_id"], "trial": r["trial"], "document_id": r["document_id"],
                          "evaluated_version_id": r["parent_version_id"], "used_by_arm": "D", "packet": "reppo-packet-v1 (candidate-cited cells only)",
                          "status": x["status"], "score": (res.get("verdict") or {}).get("score"), "decision": (res.get("verdict") or {}).get("decision"),
                          "confidence": (res.get("verdict") or {}).get("confidence"), "route": res.get("route"),
                          "rubric": [{"criterion": v["criterion"], "score": v["score"]} for v in res.get("verdicts", [])],
                          "credits_charged": x.get("credits_charged"), "wait_s": x.get("wait_s"), "recorded_at": r["at"],
                          "workspace_link": None})
        if m.get("base_experiment"):   # experiment b reuses experiment a's evaluations
            evals = []
        for e in evals:
            run = conn.execute("SELECT run_id FROM versions WHERE version_id=?", (e["evaluated_version_id"],)).fetchone()
            if run:
                e["workspace_link"] = f"/workspace?document={e['document_id']}&run={run['run_id']}&version={e['evaluated_version_id']}"
        causes = Counter(x["cause"] for x in rec)
        exps.append({
            "experiment_id": exp_id, "created_at": m["created_at"],
            "kind": "post-hoc development branch (not a holdout)" if m.get("base_experiment") else "frozen four-arm experiment",
            "base_experiment": m.get("base_experiment"),
            "policies": m["policies"], "model": m["model"]["serv_model"],
            "corpus": [{"document_id": src["document_id"], "issuer": docs[src["document_id"]]["issuer_name"], "title": docs[src["document_id"]]["title"],
                        "source_url": src["source_url"], "sha256": src["sha256"], "physical_pages": src["physical_pages"],
                        "split": "holdout" if src["document_id"] in m["split"]["holdout"] else "development"} for src in m["sources"]],
            "targets": len(m["targets"]), "trials": m["trial_plan"]["trials"], "target_observations_per_arm": a2["by_arm"]["A"]["executed"],
            "exposure_notes": m["exposure_notes"],
            "reference": {"version": "references-v1", "sha256": m["reference"]["sha256"], "provenance": m["reference"]["provenance"],
                          "human_review_status": review, "independently_reviewed": False},
            "arms": {"A": "Docling + one SERV extraction (initial prediction)", "B": "A's prediction + source-binding checker (same prediction as A)",
                     "C": "A + checker diagnostics + one SERV revision, no Reppo", "D": "A + checker diagnostics + real Reppo evaluation + one SERV revision"},
            "measurements_analysis_v2": {arm: {k: v for k, v in a2["by_arm"][arm].items()} for arm in "ABCD"},
            "paired_analysis_v2": a2["paired"], "checker_detection_analysis_v2": a2["detector_B"],
            "historical_scoring_v1": {"by_arm": {arm: {k: s1["by_arm"][arm][k] for k in ("targets", "executed", "strict_correct", "semantic_correct", "covered", "certificate_supported")} for arm in "ABCD"},
                                      "detection": s1["detection_B"], "note": "scoring-v1 derived start dates only for checker-approved candidates; analysis-v2 removes that circularity"},
            "arm_A_error_causes_analysis_v2": dict(causes),
            "finding": ("Arm D equals arm C on every metric: no incremental benefit from real Reppo feedback is established."
                        if a2["by_arm"]["C"] == a2["by_arm"]["D"] else "Arms C and D differ; see paired counts."),
            "costs": {"reppo_credits_charged": s1["costs"]["reppo_credits_charged"], "serv_calls": s1["costs"]["serv_calls_recorded"],
                      "serv_total_tokens": s1["costs"]["serv_total_tokens"], "serv_usd": "estimate only; see docs/BUDGET-SHEET.md"},
            "evaluations": evals,
            "artifacts": {name: REPO + f"artifacts/technical-proof/{exp_id}/{name}" for name in
                          ("manifest.json", "ledger.jsonl", "summary.json", "report.md", "analysis-v2/summary.json", "analysis-v2/reconciliation.md")},
            "artifact_sha256": {name: sha(d / name) for name in ("manifest.json", "ledger.jsonl", "summary.json", "analysis-v2/summary.json")},
        })
    out = {"schema": "evi.public-experiments/1", "generated_from": "artifacts/technical-proof (frozen; unchanged)",
           "limitations": ["References are builder-drafted and provisional; independent human review is pending.",
                           "Five statements from two issuers; targets and trials are correlated, so results are descriptive only.",
                           "The AT&T 'holdout' was read by the builder while designing rules; experiment b is post-hoc development evidence.",
                           "A Reppo score is an evaluator opinion, not extraction accuracy. Packets v1 contained only candidate-cited cells.",
                           "The fuller reppo-packet-v2 was checked offline only; no paid calibration has run."],
           "docs": {"proof_report": REPO + "docs/PROOF-REPORT.md", "integrity_review": REPO + "docs/PROOF-INTEGRITY-REVIEW.md",
                    "reppo_audit": REPO + "docs/REPPO-PAYLOAD-AUDIT.md", "review_packet": REPO + "docs/REFERENCE-REVIEW-PACKET.md"},
           "experiments": exps}
    text = json.dumps(out, indent=1)
    for banned in ("session", "cookie", "SERV_API_KEY", "REPPO_API_KEY", "chatcmpl", "call_", "prompt_sha256"):
        assert banned not in text, f"public export contains forbidden token {banned!r}"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(OUT, len(text), "bytes", [e["finding"][:40] for e in exps])


if __name__ == "__main__":
    main()
