"""Separate scorer (docs/20 §7). The ONLY module that reads reference labels. Run after inference is complete:

  python -m evi.scoring <exp_id>
Writes outcomes.jsonl, summary.json and report.md next to the frozen manifest.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from decimal import Decimal

from . import db
from .experiment import PROOF, REFERENCES

FIELDS = ["amount", "currency", "unit_scale", "duration_months", "fiscal_year", "end_date", "start_date"]


def load_refs(expected_sha: str, path=None) -> dict:
    raw = (path or REFERENCES).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise SystemExit("reference file changed after the manifest was frozen")
    return {r["target_key"]: r for r in json.loads(raw)["items"]}


def predicted(f: dict | None) -> dict:
    if not f:
        return {k: None for k in FIELDS}
    p = f.get("period") or {}
    return {"amount": f.get("reported_value"), "currency": f.get("currency"), "unit_scale": f.get("unit_scale"),
            "duration_months": p.get("duration_months"), "fiscal_year": f.get("fiscal_year"), "end_date": p.get("end_date"),
            "start_date": p.get("start_date") or p.get("derived_start_date")}


def eq(field: str, a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if field in ("amount", "unit_scale"):
        return Decimal(str(a)) == Decimal(str(b))
    return str(a) == str(b)


def score(exp_id: str) -> dict:
    """Compute and WRITE outcomes.jsonl, summary.json and report.md (scoring-v1 semantics, unchanged)."""
    base = PROOF / exp_id
    outcomes, summary, text = compute(exp_id)
    (base / "outcomes.jsonl").write_text("\n".join(json.dumps(o) for o in outcomes) + "\n", encoding="utf-8")
    (base / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    (base / "report.md").write_text(text, encoding="utf-8")
    return summary


def compute(exp_id: str, conn=None, base=None, refs_path=None) -> tuple[list, dict, str]:
    """Pure: computes scoring-v1 outcomes/summary/report in memory and writes nothing."""
    base = base or (PROOF / exp_id)
    m = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    from .config import ROOT
    refs = load_refs(m["reference"]["sha256"], refs_path or (ROOT / m["reference"]["path"]))
    conn = conn or db.connect()
    ledger = [json.loads(l) for l in (base / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
    branches = {(r["trial"], r["document_id"], r["arm"]): r for r in ledger}
    outcomes = []
    for (t, doc, arm), r in sorted(branches.items()):
        tks = [x["target_key"] for x in m["targets"] if x["document_id"] == doc]
        if not r.get("executed") or not r.get("version_id"):
            for tk in tks:
                outcomes.append({"trial": t, "document_id": doc, "arm": arm, "target_key": tk, "executed": False,
                                 "reason": r.get("reason") or r.get("error")})
            continue
        body = json.loads(db.row(conn, "SELECT body_json FROM versions WHERE version_id=?", r["version_id"])["body_json"])
        facts = {f.get("target_key"): f for f in body["facts"]}
        bodies = {c["target_key"]: json.loads(c["body_json"]) for c in
                  db.rows(conn, "SELECT target_key, body_json FROM certificates WHERE version_id=? AND policy_version=? ORDER BY created_at",
                          r["version_id"], m["policies"]["binding"])}
        certs = {c["target_key"]: c["claim_outcome"] for c in
                 db.rows(conn, "SELECT target_key, claim_outcome FROM certificates WHERE version_id=? AND policy_version=? ORDER BY created_at",
                         r["version_id"], m["policies"]["binding"])}
        for tk in tks:
            ref, f = refs[tk], facts.get(tk)
            pred = predicted(f)
            # Start dates are application-derived (binding-v2+): use the derivation of THIS experiment's checker policy,
            # not a value stored under an older policy (fixed 2026-11-16; affected 2 targets in exp-2026-11-16-b).
            cb = bodies.get(tk)
            if f and cb and cb["claim_outcome"] == "supported" and not (f.get("period") or {}).get("start_date"):
                pred["start_date"] = cb["claim_cell_reading"]["tuple"].get("start_date")
            elif f and not (f.get("period") or {}).get("start_date"):
                pred["start_date"] = None
            fm = {k: eq(k, pred[k], ref[k]) for k in FIELDS}
            outcomes.append({"trial": t, "document_id": doc, "arm": arm, "target_key": tk, "executed": True,
                             "version_id": r["version_id"], "execution_failed": bool(r.get("failed")),
                             "covered": pred["amount"] is not None, "field_match": fm, "semantic_correct": all(fm.values()),
                             "certificate": certs.get(tk, "missing"),
                             "strict_correct": all(fm.values()) and certs.get(tk) == "supported",
                             "split": "holdout" if doc in m["split"]["holdout"] else "development"})
    def agg(rows):
        ex = [o for o in rows if o["executed"]]
        return {"targets": len(rows), "executed": len(ex), "strict_correct": sum(o["strict_correct"] for o in ex),
                "semantic_correct": sum(o["semantic_correct"] for o in ex), "covered": sum(o["covered"] for o in ex),
                "certificate_supported": sum(o["certificate"] == "supported" for o in ex),
                "unexecuted": len(rows) - len(ex)}

    summary: dict = {"experiment_id": exp_id, "reference_provenance": m["reference"]["provenance"], "by_arm": {}, "by_arm_split": {},
                     "by_arm_document": {}, "field_errors_by_arm": {}, "paired": {}, "detection_B": {}, "costs": {}}
    for arm in "ABCD":
        rows = [o for o in outcomes if o["arm"] == arm]
        summary["by_arm"][arm] = agg(rows)
        summary["by_arm_split"][arm] = {sp: agg([o for o in rows if o.get("split") == sp or (not o["executed"] and sp in ("development", "holdout")
                                                 and (o["document_id"] in m["split"][sp]))]) for sp in ("development", "holdout")}
        summary["by_arm_document"][arm] = {d: agg([o for o in rows if o["document_id"] == d]) for d in m["split"]["development"] + m["split"]["holdout"]}
        summary["field_errors_by_arm"][arm] = dict(Counter(k for o in rows if o["executed"] for k, ok in o["field_match"].items() if not ok))
    idx = {(o["trial"], o["target_key"], o["arm"]): o for o in outcomes}
    for a, b in (("A", "C"), ("A", "D"), ("C", "D")):
        c = Counter()
        for (t, tk, arm), o in idx.items():
            if arm != a:
                continue
            p = idx.get((t, tk, b))
            if not (o["executed"] and p and p["executed"]):
                c["pair_not_executed"] += 1
                continue
            x, y = o["strict_correct"], p["strict_correct"]
            c["improvement" if (not x and y) else "regression" if (x and not y) else "preserved_correct" if x else "unchanged_incorrect"] += 1
            if o["covered"] and not p["covered"]:
                c["coverage_lost"] += 1
        summary["paired"][f"{a}->{b}"] = dict(c)
    det = Counter()
    for o in outcomes:
        if o["arm"] == "B" and o["executed"]:
            flagged = o["certificate"] != "supported"
            wrong = not o["semantic_correct"]
            det["true_detection" if flagged and wrong else "missed_error" if wrong else "false_alarm" if flagged else "correct_pass"] += 1
    summary["detection_B"] = dict(det)
    serv_tokens, serv_calls, latency = 0, 0, defaultdict(list)
    credits, waits = 0, []
    for r in ledger:
        if r.get("latency_s") is not None:
            latency[r["arm"]].append(r["latency_s"])
        if r.get("reppo"):
            credits += r["reppo"].get("credits_charged") or 0
            waits.append(r["reppo"].get("wait_s"))
    # Exact attribution (fixed 2026-11-16): the extraction call recorded in each A version this experiment created,
    # plus the revision call recorded in each receipt this experiment created. Reused baselines cost nothing here.
    call_ids = []
    for r in ledger:
        if r["arm"] == "A" and r.get("version_id") and not r.get("reused_from"):
            body = json.loads(db.row(conn, "SELECT body_json FROM versions WHERE version_id=?", r["version_id"])["body_json"])
            call_ids.append((body.get("provider") or {}).get("call_id"))
    for rc in db.rows(conn, "SELECT body_json FROM revision_receipts WHERE idempotency_key LIKE ?", f"{exp_id}:%"):
        call_ids.append(json.loads(rc["body_json"])["serv"]["call_id"])
    for cid in filter(None, call_ids):
        row = db.row(conn, "SELECT usage_json FROM provider_calls WHERE call_id=?", cid)
        serv_calls += 1
        if row and row["usage_json"]:
            serv_tokens += json.loads(row["usage_json"]).get("total_tokens") or 0
    summary["costs"] = {"serv_calls_recorded": serv_calls, "serv_total_tokens": serv_tokens,
                        "serv_usd": "unknown (per-call price not returned; token counts only)",
                        "reppo_credits_charged": credits, "reppo_wait_s": waits,
                        "latency_s_by_arm": {k: v for k, v in latency.items()}}
    return outcomes, summary, report(m, summary)


def report(m: dict, s: dict) -> str:
    L = [f"# Experiment {m['experiment_id']} — measured results", "",
         f"Reference provenance: **{s['reference_provenance']}**. Strict correctness requires every frozen field to equal the reference "
         "AND a `supported` binding certificate. Unexecuted branches are reported, not scored as 0%.", "",
         "| Arm | Targets | Executed | Strict correct | Semantic correct | Covered | Certificate supported |", "|---|---|---|---|---|---|---|"]
    for arm, a in s["by_arm"].items():
        L.append(f"| {arm} | {a['targets']} | {a['executed']} | {a['strict_correct']} | {a['semantic_correct']} | {a['covered']} | {a['certificate_supported']} |")
    L += ["", "## Split", "", "| Arm | Development strict/executed | Holdout strict/executed |", "|---|---|---|"]
    for arm, sp in s["by_arm_split"].items():
        L.append(f"| {arm} | {sp['development']['strict_correct']}/{sp['development']['executed']} | {sp['holdout']['strict_correct']}/{sp['holdout']['executed']} |")
    L += ["", "## Paired transitions (same trial, same target)", "", "| Pair | Improvement | Regression | Preserved correct | Unchanged incorrect | Coverage lost | Not executed |", "|---|---|---|---|---|---|---|"]
    for k, c in s["paired"].items():
        L.append(f"| {k} | {c.get('improvement', 0)} | {c.get('regression', 0)} | {c.get('preserved_correct', 0)} | {c.get('unchanged_incorrect', 0)} | {c.get('coverage_lost', 0)} | {c.get('pair_not_executed', 0)} |")
    L += ["", "## Arm B diagnostics vs reference", "", json.dumps(s["detection_B"]), "",
          "## Field errors by arm", "", json.dumps(s["field_errors_by_arm"]), "",
          "## Per document (strict/executed)", ""]
    for arm, docs in s["by_arm_document"].items():
        L.append(f"- {arm}: " + ", ".join(f"{d} {v['strict_correct']}/{v['executed']}" for d, v in docs.items()))
    L += ["", "## Costs and latency", "", "```json", json.dumps(s["costs"], indent=1), "```", "",
          "Targets within a document and repeated trials are correlated; 5 reports from 2 issuers support descriptive results only."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    print(json.dumps(score(sys.argv[1]), indent=1))
