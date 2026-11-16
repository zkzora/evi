"""analysis-v2 (2026-11-16): non-circular metrics over SAVED predictions. Reads references (scoring side only).

  python -m evi.analysis <exp_id>     # writes artifacts/technical-proof/<exp_id>/analysis-v2/ (originals untouched)

Metrics, each over the same stable denominator (every frozen target of every executed branch):
- raw field match: the model's own fields vs the frozen reference; per field: match / mismatch / missing (model null,
  reference known) / null_both (both null: faithful absence) / spurious (model value, reference null).
- application-derived field match: start_date from the frozen calendar rule R-CAL-MONTHEND applied to the MODEL'S OWN
  claimed end date and duration (never to the checker's verdict); normalized = amount x scale.
- reference_match: all frozen fields match, with derived start date. Null == null counts (faithful source
  representation); this is NOT complete interval recovery.
- complete_interval: start and end both known AND equal to the reference (impossible for AT&T: the page prints no date).
- certificate: claim outcome under the experiment's binding policy (checker output, never used to decide truth).
- composite: reference_match AND certificate supported (= the old 'strict' idea, recomputed without circularity).
- detector confusion: flag = certificate not supported; truth = NOT reference_match (independent of the flag).
scoring-v1 (summary.json) used the certificate's derivation for start dates only when the certificate was 'supported',
which made 'semantic_correct' depend on the detector; analysis-v2 removes that dependence.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from decimal import Decimal

from . import db
from .binding import derive_start
from .experiment import PROOF
from .scoring import load_refs

FIELDS = ["amount", "currency", "unit_scale", "duration_months", "fiscal_year", "end_date", "start_date"]
VERSION = "analysis-v2"


def _eq(field, a, b):
    if field in ("amount", "unit_scale"):
        return Decimal(str(a)) == Decimal(str(b))
    return str(a) == str(b)


def field_status(field, pred, ref) -> str:
    if pred is None and ref is None:
        return "null_both"
    if pred is None:
        return "missing"
    if ref is None:
        return "spurious"
    return "match" if _eq(field, pred, ref) else "mismatch"


def derived_start(fact: dict) -> tuple[str | None, str]:
    p = fact.get("period") or {}
    if p.get("start_date"):
        return p["start_date"], "claimed"
    end, dur = p.get("end_date"), p.get("duration_months")
    if not (end and dur):
        return None, "no_claimed_end_or_duration"
    try:
        s, rule = derive_start(end, int(dur), False)
    except (ValueError, TypeError):
        return None, "underivable"
    return s, rule


def evaluate(exp_id: str, conn=None, base=None, refs_path=None) -> tuple[list[dict], dict]:
    base = base or (PROOF / exp_id)
    m = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    from .config import ROOT
    refs = load_refs(m["reference"]["sha256"], refs_path or (ROOT / m["reference"]["path"]))
    conn = conn or db.connect()
    policy = m["policies"]["binding"]
    ledger = [json.loads(l) for l in (base / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
    rows = []
    for r in sorted(ledger, key=lambda r: (r["trial"], r["document_id"], r["arm"])):
        tks = [x["target_key"] for x in m["targets"] if x["document_id"] == r["document_id"]]
        if not (r.get("executed") and r.get("version_id")):
            rows += [{"trial": r["trial"], "document_id": r["document_id"], "arm": r["arm"], "target_key": tk, "executed": False} for tk in tks]
            continue
        facts = {f.get("target_key"): f for f in json.loads(db.row(conn, "SELECT body_json FROM versions WHERE version_id=?", r["version_id"])["body_json"])["facts"]}
        certs = {}
        for c in db.rows(conn, "SELECT target_key, body_json FROM certificates WHERE version_id=? AND policy_version=? ORDER BY created_at", r["version_id"], policy):
            certs[c["target_key"]] = json.loads(c["body_json"])
        for tk in tks:
            f, ref = facts.get(tk) or {}, refs[tk]
            p = f.get("period") or {}
            raw = {"amount": f.get("reported_value"), "currency": f.get("currency"), "unit_scale": f.get("unit_scale"),
                   "duration_months": p.get("duration_months"), "fiscal_year": f.get("fiscal_year"), "end_date": p.get("end_date"),
                   "start_date": p.get("start_date")}
            raw_status = {k: field_status(k, raw[k], ref[k]) for k in FIELDS}
            ds, how = derived_start(f) if f else (None, "no_fact")
            derived_status = dict(raw_status, start_date=field_status("start_date", ds, ref["start_date"]))
            ok = lambda st: st in ("match", "null_both")
            ref_match = all(ok(v) for v in derived_status.values())
            cert = certs.get(tk)
            outcome = cert["claim_outcome"] if cert else "missing"
            reading = (cert or {}).get("claim_cell_reading") or {}
            p3 = next((o for o in reading.get("obligations", []) if o["id"] == "P3"), None)
            rows.append({
                "trial": r["trial"], "document_id": r["document_id"], "arm": r["arm"], "target_key": tk, "executed": True,
                "version_id": r["version_id"], "split": "holdout" if r["document_id"] in m["split"]["holdout"] else "development",
                "raw": raw, "raw_status": raw_status, "derived_start": ds, "derived_start_basis": how, "derived_status": derived_status,
                "raw_field_match_all": all(ok(v) for v in raw_status.values()),
                "reference_match": ref_match,
                "complete_interval": derived_status["end_date"] == "match" and derived_status["start_date"] == "match",
                "reference_interval_known": ref["end_date"] is not None,
                "certificate": outcome, "certificate_exact_dates": (p3 or {}).get("status"),
                "composite": ref_match and outcome == "supported",
                "currency_symbol_only": raw["currency"] == "$" and ref["currency"] == "USD",
            })
    return rows, summarize(exp_id, m, rows)


def summarize(exp_id: str, m: dict, rows: list[dict]) -> dict:
    s: dict = {"experiment_id": exp_id, "analysis_version": VERSION, "binding_policy": m["policies"]["binding"],
               "reference_provenance": m["reference"]["provenance"], "by_arm": {}, "paired": {}, "detector_B": {}, "field_status_A": {}}
    for arm in "ABCD":
        ex = [r for r in rows if r["arm"] == arm and r["executed"]]
        s["by_arm"][arm] = {
            "targets": sum(1 for r in rows if r["arm"] == arm), "executed": len(ex),
            "raw_field_match_all": sum(r["raw_field_match_all"] for r in ex),
            "reference_match": sum(r["reference_match"] for r in ex),
            "complete_interval": sum(r["complete_interval"] for r in ex),
            "reference_interval_known": sum(r["reference_interval_known"] for r in ex),
            "certificate_supported": sum(r["certificate"] == "supported" for r in ex),
            "certificate_supported_exact_dates_unknown": sum(r["certificate"] == "supported" and r["certificate_exact_dates"] == "unknown" for r in ex),
            "composite": sum(r["composite"] for r in ex),
            "sensitivity_reference_match_if_dollar_sign_accepted_as_USD": sum(
                r["reference_match"] or (r["currency_symbol_only"] and all(v in ("match", "null_both") for k, v in r["derived_status"].items() if k != "currency"))
                for r in ex),
        }
    s["field_status_A"] = {k: dict(Counter(r["derived_status"][k] for r in rows if r["arm"] == "A" and r["executed"])) for k in FIELDS}
    idx = {(r["trial"], r["target_key"], r["arm"]): r for r in rows}
    for metric in ("reference_match", "composite"):
        for a, b in (("A", "C"), ("A", "D"), ("C", "D")):
            c = Counter()
            for (t, tk, arm), x in idx.items():
                if arm != a:
                    continue
                y = idx.get((t, tk, b))
                if not (x["executed"] and y and y["executed"]):
                    c["pair_not_executed"] += 1
                    continue
                u, v = x[metric], y[metric]
                c["improvement" if (not u and v) else "regression" if (u and not v) else "preserved_correct" if u else "unchanged_incorrect"] += 1
            s["paired"][f"{metric}:{a}->{b}"] = dict(c)
    det = Counter()
    for r in rows:
        if r["arm"] == "B" and r["executed"]:
            flag, err = r["certificate"] != "supported", not r["reference_match"]
            det["TP" if flag and err else "FP" if flag else "FN" if err else "TN"] += 1
    s["detector_B"] = dict(det)
    return s


def write(exp_id: str) -> dict:
    rows, s = evaluate(exp_id)
    out = PROOF / exp_id / VERSION
    out.mkdir(exist_ok=True)
    (out / "outcomes.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
    return s


if __name__ == "__main__":
    print(json.dumps(write(sys.argv[1]), indent=1))


def reconcile(exp_id: str, conn=None) -> list[dict]:
    """Target-level reconciliation of scoring-v1 (saved) vs analysis-v2 for arm A (B shares A's version)."""
    conn = conn or db.connect()
    base = PROOF / exp_id
    rows, _ = evaluate(exp_id, conn=conn)
    v1 = {(o["trial"], o["target_key"], o["arm"]): o for o in
          (json.loads(l) for l in (base / "outcomes.jsonl").read_text(encoding="utf-8").splitlines())}
    out = []
    for r in rows:
        if r["arm"] != "A" or not r["executed"]:
            continue
        o = v1[(r["trial"], r["target_key"], "A")]
        if o["semantic_correct"] == r["reference_match"] and o["strict_correct"] == r["composite"] and r["composite"]:
            continue
        cert = json.loads(db.row(conn, "SELECT body_json FROM certificates WHERE version_id=? AND target_key=? AND policy_version=? "
                                       "ORDER BY created_at DESC", r["version_id"], r["target_key"],
                                 json.loads((base / "manifest.json").read_text())["policies"]["binding"])["body_json"])
        failed = [f"{v['field']}:{v['reason']}" for v in cert["field_verdicts"] if v["status"] == "fail"]
        bad = [k for k, v in r["derived_status"].items() if v not in ("match", "null_both")]
        if r["currency_symbol_only"]:
            cause = "model output: currency '$' instead of 'USD'"
        elif "amount" in bad:
            cause = "model output: wrong attribution row (common stock instead of parent)"
        elif "end_date" in bad:
            cause = "model output: printed end date omitted"
        elif r["reference_match"] and r["certificate"] != "supported":
            cause = "checker false alarm: section heading cited as metric context not counted as applicable (binding-v2 rule)"
        else:
            cause = "other"
        out.append({"trial": r["trial"], "target_key": r["target_key"], "version_id": r["version_id"],
                    "prediction": {k: r["raw"][k] for k in ("amount", "currency", "end_date", "start_date")},
                    "derived_start": r["derived_start"], "derived_start_basis": r["derived_start_basis"],
                    "fields_not_matching_reference": bad, "certificate": r["certificate"], "certificate_failed_fields": failed,
                    "v1_semantic_correct": o["semantic_correct"], "v1_strict_correct": o["strict_correct"],
                    "v2_reference_match": r["reference_match"], "v2_composite": r["composite"],
                    "v1_v2_change": ("scorer correction: start date derived independently of checker verdict"
                                     if o["semantic_correct"] != r["reference_match"] else "none"),
                    "cause": cause})
    return out


def write_reconciliation(exp_id: str) -> list[dict]:
    rec = reconcile(exp_id)
    out = PROOF / exp_id / VERSION
    out.mkdir(exist_ok=True)
    (out / "reconciliation.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    L = [f"# {exp_id} — target-level reconciliation, arm A (scoring-v1 saved vs {VERSION})", "",
         "Arm B shares arm A's version. Predictions are the saved originals; nothing was re-run.", "",
         "| Trial | Target | Prediction (amount, currency, end, start) | Derived start | Not matching reference | Certificate (failed fields) | v1 semantic/strict | v2 ref-match/composite | Cause |",
         "|---|---|---|---|---|---|---|---|---|"]
    for x in rec:
        p = x["prediction"]
        L.append(f"| {x['trial']} | {x['target_key']} | {p['amount']}, {p['currency']}, {p['end_date']}, {p['start_date']} | "
                 f"{x['derived_start']} ({x['derived_start_basis']}) | {', '.join(x['fields_not_matching_reference']) or '—'} | "
                 f"{x['certificate']} ({'; '.join(x['certificate_failed_fields']) or '—'}) | {x['v1_semantic_correct']}/{x['v1_strict_correct']} | "
                 f"{x['v2_reference_match']}/{x['v2_composite']} | {x['cause']} |")
    (out / "reconciliation.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return rec


def evaluate_reviewed(exp_id: str, reviewed_path, conn=None, write_out: bool = True) -> dict:
    """Re-run analysis-v2 metrics against a REVIEWED reference version (review-v1 import), into a new folder
    analysis-v2-<reference version>/. The reviewed file must derive from the exact reference hash this experiment froze.
    Targets whose reviewed reference is ambiguous stay in the denominator under 'reference_ambiguous'."""
    import hashlib
    from pathlib import Path
    reviewed_path = Path(reviewed_path)
    base = PROOF / exp_id
    m = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    rv = json.loads(reviewed_path.read_text(encoding="utf-8"))
    if rv.get("derived_from", {}).get("sha256") != m["reference"]["sha256"]:
        raise SystemExit("reviewed reference does not derive from this experiment's frozen reference")
    rows, _ = evaluate(exp_id, conn=conn)
    refs = {r["target_key"]: r for r in rv["items"]}
    v1 = {r["target_key"]: r for r in json.loads((Path(__file__).resolve().parents[2] / m["reference"]["path"]).read_text())["items"]}
    out_rows = []
    for r in rows:
        if not r["executed"]:
            out_rows.append(r); continue
        ref = refs[r["target_key"]]
        amb = ref.get("status") in ("ambiguous_unadjudicated", "ambiguous_unresolvable")
        pred = dict(r["raw"], start_date=r["derived_start"])
        st = {k: field_status(k, pred[k], ref.get(k)) for k in FIELDS}
        ok = all(v in ("match", "null_both") for v in st.values())
        out_rows.append({**r, "reviewed_status": st, "reference_ambiguous": amb, "reference_changed_by_review":
                         any(str(ref.get(k)) != str(v1[r["target_key"]].get(k)) for k in FIELDS),
                         "reviewed_reference_match": (not amb) and ok,
                         "reviewed_composite": (not amb) and ok and r["certificate"] == "supported"})
    s = {"experiment_id": exp_id, "analysis_version": f"{VERSION}+{rv['version']}", "reference_version": rv["version"],
         "reference_provenance": rv["provenance"], "independent_human_review": rv.get("independent_human_review"), "by_arm": {}}
    for arm in "ABCD":
        ex = [r for r in out_rows if r["arm"] == arm and r["executed"]]
        s["by_arm"][arm] = {"executed": len(ex), "reference_ambiguous": sum(r["reference_ambiguous"] for r in ex),
                            "targets_whose_reference_changed": sum(r["reference_changed_by_review"] for r in ex),
                            "reviewed_reference_match": sum(r["reviewed_reference_match"] for r in ex),
                            "v1_reference_match": sum(r["reference_match"] for r in ex),
                            "reviewed_composite": sum(r["reviewed_composite"] for r in ex)}
    s["note"] = "Predictions are unchanged saved originals; differences from v1 come only from reference review."
    if write_out:
        out = base / f"{VERSION}-{rv['version']}"
        if out.exists():
            raise SystemExit(f"{out} exists; refusing to overwrite")
        out.mkdir()
        (out / "summary.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
        (out / "outcomes.jsonl").write_text("\n".join(json.dumps(r) for r in out_rows) + "\n", encoding="utf-8")
    return s
