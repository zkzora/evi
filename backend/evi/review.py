"""Reference-review validation and import (review-v1, 2026-11-16).

  python -m evi.review validate <sheet.json>                       # report only; writes nothing
  python -m evi.review import <sheet.json> [--adjudication adj.json] # writes a NEW candidate reference + change log

references-v1.json is never modified. Imports go to data/references/reviewed/ under a new identifier derived from the
sheet hash; an existing file is never overwritten. Reviewer identity is SELF-DECLARED in the sheet and is not
independently authenticated; the imported provenance says exactly that.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .config import ROOT

REFS = ROOT / "data" / "references" / "references-v1.json"
REVIEWED = ROOT / "data" / "references" / "reviewed"
STATUSES = {"pending", "confirmed", "corrected", "ambiguous"}
RELATIONS = {"independent_human": "independent human reviewer (not a label author)",
             "user_not_label_author": "project user who did not author the draft labels",
             "builder": "builder self-review (NOT independent)",
             "agent": "AI/agent annotation (NOT human review)"}
INDEPENDENT = {"independent_human", "user_not_label_author"}
CORRECTABLE = {"row_label", "printed_amount", "amount", "currency", "unit_scale", "duration_months", "fiscal_year",
               "end_date", "start_date", "scope"}
DRAFT_KEYS = ["row_label", "printed_amount", "amount", "currency", "unit_scale", "normalized_value", "duration_months",
              "fiscal_year", "end_date", "start_date", "scope", "date_basis"]


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _date_ok(v) -> bool:
    if v is None:
        return True
    try:
        return dt.date.fromisoformat(v).isoformat() == v
    except (TypeError, ValueError):
        return False


def check_value(field: str, v) -> str | None:
    if field == "amount":
        try:
            Decimal(str(v))
            return None if re.fullmatch(r"-?\d+(\.\d+)?", str(v)) else "amount must be a plain decimal string"
        except (InvalidOperation, TypeError):
            return "amount is not a decimal"
    if field == "unit_scale":
        return None if str(v) in {"1", "1000", "1000000", "1000000000"} else "unit_scale must be 1, 1000, 1000000 or 1000000000"
    if field in ("end_date", "start_date"):
        return None if _date_ok(v) else f"{field} must be YYYY-MM-DD or null"
    if field == "currency":
        return None if isinstance(v, str) and re.fullmatch(r"[A-Z]{3}", v) else "currency must be an ISO 4217 code"
    if field == "duration_months":
        return None if v in (3, 6, 9, 12) else "duration_months must be 3, 6, 9 or 12"
    if field == "fiscal_year":
        return None if isinstance(v, int) and 1990 <= v <= 2100 else "fiscal_year must be an integer year"
    if field in ("row_label", "printed_amount", "scope"):
        return None if isinstance(v, str) and v.strip() else f"{field} must be non-empty text"
    return f"{field} is not a correctable field"


def validate(sheet: dict, refs_path: Path = REFS, today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    raw = refs_path.read_bytes()
    refs = {r["target_key"]: r for r in json.loads(raw)["items"]}
    E, W = [], []
    if sheet.get("reference_sha256") != _sha(raw):
        E.append("sheet is bound to a different reference file hash")
    if sheet.get("reference_file") != refs_path.name:
        E.append("sheet names a different reference file")
    prov = sheet.get("review_provenance") or {}
    rel = prov.get("reviewer_relation")
    items = sheet.get("items") or []
    keys = [i.get("target_key") for i in items]
    dup = [k for k, n in Counter(keys).items() if n > 1]
    unknown = sorted(set(keys) - set(refs))
    missing = sorted(set(refs) - set(keys))
    if dup:
        E.append(f"duplicate targets: {dup}")
    if unknown:
        E.append(f"unknown targets: {unknown}")
    if missing:
        E.append(f"missing targets: {missing}")
    status = Counter(i.get("review_status") for i in items)
    reviewed = [i for i in items if i.get("review_status") in STATUSES - {"pending"}]
    if reviewed and rel not in RELATIONS:
        E.append(f"review_provenance.reviewer_relation must be one of {sorted(RELATIONS)}")
    if reviewed and not (prov.get("reviewer_name") and prov.get("method")):
        E.append("review_provenance needs reviewer_name and method (how sources were inspected)")
    for i in items:
        k = i.get("target_key")
        st = i.get("review_status")
        if st not in STATUSES:
            E.append(f"{k}: invalid review_status {st!r}")
            continue
        if k in refs and any(str(i.get("draft", {}).get(f)) != str(refs[k].get(f)) for f in DRAFT_KEYS):
            E.append(f"{k}: draft fields differ from references-v1 (changed reference identity)")
        if st == "pending":
            if i.get("reviewer") or i.get("reviewed_at") or i.get("proposed_corrections"):
                E.append(f"{k}: pending entry carries reviewer/date/corrections")
            continue
        if not (i.get("reviewer") and isinstance(i.get("reviewer"), str)):
            E.append(f"{k}: reviewer missing")
        if not _date_ok(i.get("reviewed_at")) or i.get("reviewed_at") is None:
            E.append(f"{k}: reviewed_at must be a YYYY-MM-DD date")
        elif dt.date.fromisoformat(i["reviewed_at"]) > today:
            E.append(f"{k}: reviewed_at is in the future")
        if not (i.get("rationale") or "").strip():
            E.append(f"{k}: rationale missing")
        if not (i.get("source_evidence") or "").strip():
            E.append(f"{k}: source_evidence missing (what was inspected on the page)")
        corr = i.get("proposed_corrections") or {}
        if st == "confirmed" and corr:
            E.append(f"{k}: confirmed entry must not propose corrections")
        if st == "corrected" and not corr:
            E.append(f"{k}: corrected entry has no field-level corrections")
        for f, v in corr.items():
            msg = check_value(f, v)
            if msg:
                E.append(f"{k}: {msg}")
    # Blanket/synthetic approval: identical justification copied across many targets carries no per-target review.
    for fld in ("rationale", "source_evidence"):
        c = Counter((i.get(fld) or "").strip().lower() for i in reviewed)
        common, n = (c.most_common(1) or [("", 0)])[0]
        if common and n >= 10:
            E.append(f"blanket review: {n} entries share the identical {fld} {common[:60]!r}; per-target review evidence is required")
    if reviewed and rel in ("builder", "agent"):
        W.append(f"provenance is '{RELATIONS[rel]}'; an import is allowed but is NOT independent human review")
    if reviewed and rel in INDEPENDENT:
        W.append("reviewer identity is self-declared in the sheet and not independently authenticated")
    return {"errors": E, "warnings": W, "counts": dict(status), "reviewed": len(reviewed), "targets": len(items),
            "complete": not E and status.get("pending", 0) == 0 and len(items) == len(refs),
            "independent": rel in INDEPENDENT, "reference_sha256": _sha(raw)}


def import_sheet(sheet_path: Path, adjudication_path: Path | None = None, refs_path: Path = REFS, out_dir: Path = REVIEWED,
                 today: dt.date | None = None) -> dict:
    sheet_raw = sheet_path.read_bytes()
    sheet = json.loads(sheet_raw)
    v = validate(sheet, refs_path, today)
    if v["errors"]:
        raise SystemExit("REJECTED: " + "; ".join(v["errors"][:10]))
    if not v["complete"]:
        raise SystemExit(f"REJECTED: review incomplete ({v['counts']}); every target needs confirmed/corrected/ambiguous")
    adj = json.loads(adjudication_path.read_text(encoding="utf-8")) if adjudication_path else {}
    refs_raw = refs_path.read_bytes()
    refs = json.loads(refs_raw)
    by_key = {i["target_key"]: i for i in sheet["items"]}
    prov = sheet["review_provenance"]
    new_items, log = [], []
    for r in refs["items"]:
        it = by_key[r["target_key"]]
        st, corr = it["review_status"], it.get("proposed_corrections") or {}
        item = dict(r)
        entry = {"target_key": r["target_key"], "review_status": st, "reviewer": it["reviewer"], "reviewed_at": it["reviewed_at"],
                 "rationale": it["rationale"], "source_evidence": it["source_evidence"]}
        if st == "corrected":
            entry["changes"] = {f: {"from": r.get(f), "to": val} for f, val in corr.items()}
            item.update(corr)
            if "amount" in corr or "unit_scale" in corr:
                item["normalized_value"] = format((Decimal(str(item["amount"])) * Decimal(str(item["unit_scale"]))).quantize(Decimal(1)), "f")
        elif st == "ambiguous":
            a = adj.get(r["target_key"])
            if not a:
                item["status"] = "ambiguous_unadjudicated"   # stays in the denominator; scored only as 'ambiguous'
                entry["adjudication"] = None
            else:
                for f in ("decision", "adjudicator", "adjudicated_at", "rationale"):
                    if not a.get(f):
                        raise SystemExit(f"REJECTED: adjudication for {r['target_key']} lacks {f}")
                if a["decision"] not in {"keep_draft", "apply_correction", "unresolvable"}:
                    raise SystemExit(f"REJECTED: adjudication decision {a['decision']!r} unknown")
                if a["decision"] == "apply_correction":
                    for f, val in (a.get("corrections") or {}).items():
                        msg = check_value(f, val)
                        if msg:
                            raise SystemExit(f"REJECTED: adjudication {r['target_key']}: {msg}")
                    item.update(a.get("corrections") or {})
                item["status"] = {"keep_draft": "adjudicated_keep", "apply_correction": "adjudicated_corrected",
                                  "unresolvable": "ambiguous_unresolvable"}[a["decision"]]
                entry["adjudication"] = a
        item["review"] = {"status": st, "reviewer": it["reviewer"], "reviewed_at": it["reviewed_at"]}
        new_items.append(item)
        log.append(entry)
    ident = "references-r1-" + _sha(sheet_raw)[:12]
    out_dir.mkdir(parents=True, exist_ok=True)
    ref_out, log_out = out_dir / f"{ident}.json", out_dir / f"{ident}.changelog.json"
    if ref_out.exists() or log_out.exists():
        raise SystemExit(f"REJECTED: {ref_out.name} already exists; refusing to overwrite")
    independent = prov["reviewer_relation"] in INDEPENDENT
    doc = {"schema": "evi.references/1", "version": ident, "derived_from": {"file": refs_path.name, "sha256": _sha(refs_raw)},
           "review_sheet_sha256": _sha(sheet_raw), "review_provenance": prov,
           "provenance": ("human-reviewed (self-declared reviewer, not independently authenticated): " if independent else
                          f"{RELATIONS[prov['reviewer_relation']]}: ") + f"{v['counts']}",
           "independent_human_review": independent,
           "source_hashes": {r["document_id"]: None for r in refs["items"]}, "items": new_items}
    from .corpus import REGISTERED, sha256_file, source_path
    reg = {r["document_id"]: r for r in REGISTERED}
    for d in doc["source_hashes"]:
        r = reg.get(d)
        if r is None or sha256_file(source_path(r)) != r["sha256"]:
            raise SystemExit(f"REJECTED: registered source {d} missing or its bytes changed")
        doc["source_hashes"][d] = r["sha256"]
    ref_out.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    log_out.write_text(json.dumps({"version": ident, "entries": log, "adjudication_sha256": _sha(adjudication_path.read_bytes()) if adjudication_path else None}, indent=1), encoding="utf-8")
    return {"version": ident, "reference": str(ref_out), "changelog": str(log_out), "counts": v["counts"], "independent": independent,
            "warnings": v["warnings"]}


def main(argv: list[str]) -> int:
    if argv[:1] == ["validate"]:
        res = validate(json.loads(Path(argv[1]).read_text(encoding="utf-8")))
        print(json.dumps(res, indent=1))
        return 0 if not res["errors"] else 1
    if argv[:1] == ["import"]:
        adj = Path(argv[argv.index("--adjudication") + 1]) if "--adjudication" in argv else None
        print(json.dumps(import_sheet(Path(argv[1]), adj), indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
