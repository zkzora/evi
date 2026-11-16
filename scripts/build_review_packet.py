"""Build the human reference-review packet (docs/REFERENCE-REVIEW-PACKET.md, page images, review sheet).
Read-only with respect to references-v1.json; no provider calls.

Usage: backend/.venv/Scripts/python scripts/build_review_packet.py
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import pypdfium2 as pdfium  # noqa: E402
from PIL import ImageDraw, ImageFont  # noqa: E402

from evi import binding, db, targets  # noqa: E402

REF = ROOT / "data" / "references" / "references-v1.json"
OUT_IMG = ROOT / "artifacts" / "reference-review"
SHEET = ROOT / "data" / "references" / "review" / "review-sheet-references-v1.json"
EXPOSURE = {"development": "development; builder-exposed; featured in demos (Verizon)",
            "holdout": "issuer-separated holdout; builder read these pages while designing rules and transcribing references (not unseen)"}


def main():
    ref_raw = REF.read_bytes()
    ref = json.loads(ref_raw)
    conn = db.connect()
    OUT_IMG.mkdir(parents=True, exist_ok=True)
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    items = {r["target_key"]: r for r in ref["items"]}
    L = ["# Reference review packet — references-v1 (48 targets)", "",
         f"Reference file: `data/references/references-v1.json`, sha256 `{hashlib.sha256(ref_raw).hexdigest()}`, "
         f"provenance: **{ref['provenance']}**. Independent review: **not performed**.", "",
         "How to review: for each target, open the issuer PDF at the physical page (or the rendered page image with numbered boxes), "
         "confirm the printed amount, row, column year and interval heading, unit statement and scope, then record the outcome in "
         "`data/references/review/review-sheet-references-v1.json` (status `confirmed` / `corrected` / `ambiguous`, reviewer name, date, "
         "rationale, and proposed corrected fields). Corrections go into a NEW file `references-v2.json` with a change log; "
         "references-v1 is never edited. Machine re-verification of certificates is not a substitute for this review.", "",
         "Known points needing a reviewer's judgment:",
         "- **AT&T owner-attributable profit**: the draft uses \"Net Income (Loss) Attributable to AT&T\" (before preferred dividends), "
         "not \"…Attributable to Common Stock\". Confirm this policy is the intended definition of 'owners of the parent'.",
         "- **AT&T exact dates**: the statement page prints \"Third Quarter\"/\"Nine-Month Period\" (\"Second Quarter\"/\"Six-Month Period\") "
         "and years but no end date. The draft sets end/start = null. Dates from the cover page or other pages would be outside "
         "the parsed statement-page coverage.",
         "- **Verizon start dates**: printed headings state only the end; start dates are derived (month-end calendar rule). "
         "A reviewer should confirm Verizon reports calendar quarters/years (no 52/53-week convention).",
         "- **Currency**: references use the code `USD`; the page prints \"$\" and \"dollars\".", ""]
    sheet = []
    for doc in targets.COLUMNS:
        d = db.row(conn, "SELECT * FROM documents WHERE document_id=?", doc)
        p = db.row(conn, "SELECT * FROM parses WHERE document_id=? ORDER BY created_at DESC LIMIT 1", doc)
        s = binding.load_structure(conn, p["parse_id"])
        split = "holdout" if doc in targets.SPLIT["holdout"] else "development"
        page_no = json.loads(d["parse_pages"])[0]
        pdf = pdfium.PdfDocument(str(ROOT / "public" / "sources" / d["file_name"]))
        scale = 2.0
        img = pdf[page_no - 1].render(scale=scale).to_pil()
        draw = ImageDraw.Draw(img)
        L += [f"## {doc} — {d['title']}", "",
              f"- Issuer URL: {d['source_url']}", f"- SHA-256: `{d['sha256']}`", f"- Physical page: {page_no} of {d['page_count']}",
              f"- Split / exposure: {EXPOSURE[split]}", f"- Rendered page with numbered target boxes: `artifacts/reference-review/{doc}-p{page_no}.png`", "",
              "| # | Target | Printed row label | Printed amount | Scope | Unit / scale | Interval heading | Year header | Draft end / start | Date basis | Value-cell region (PDF pt, top-left origin) |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for n, t in enumerate(targets.targets_for(doc), 1):
            r = items[t["target_key"]]
            res = binding.resolve_target(s, t, True, s.source_sha256)
            region, dur_txt, year_txt, unit_txt = "—", "—", "—", "—"
            if res["classes"]:
                vid = res["classes"][0]["value_cells"][0]
                cand = next(c for c in res["candidates"] if c["value_cell"] == vid)
                e = conn.execute("SELECT bbox_json, page_height FROM evidence WHERE evidence_id=?", (vid,)).fetchone()
                bb = json.loads(e["bbox_json"])
                top, bottom = (bb["top"], bb["bottom"]) if bb["origin"] == "TOPLEFT" else (e["page_height"] - bb["top"], e["page_height"] - bb["bottom"])
                region = f"l {bb['left']:.0f}, t {top:.0f}, r {bb['right']:.0f}, b {bottom:.0f}"
                draw.rectangle([bb["left"] * scale, top * scale, bb["right"] * scale, bottom * scale], outline=(220, 40, 40), width=2)
                draw.text((bb["right"] * scale + 3, top * scale - 2), str(n), fill=(220, 40, 40))
                notes = {x["rel"]: x["note"] for x in cand["edges"]}
                dur_txt, year_txt, unit_txt = notes.get("duration_heading_for", "—"), notes.get("year_header_for", "—"), notes.get("unit_applies_to", "—")
            L.append(f"| {n} | `{t['target_key']}` | {r['row_label']} | {r['printed_amount']} | {r['scope']} | {r['currency']} × {r['unit_scale']} "
                     f"(\"{unit_txt}\") | {dur_txt} | {year_txt} | {r['end_date'] or 'null'} / {r['start_date'] or 'null'} | {r['date_basis']} | {region} |")
            sheet.append({"target_key": t["target_key"], "box_number": n, "draft": {k: r[k] for k in (
                "row_label", "printed_amount", "amount", "currency", "unit_scale", "normalized_value", "duration_months", "fiscal_year",
                "end_date", "start_date", "scope", "date_basis")}, "review_status": "pending", "reviewer": None, "reviewed_at": None,
                "proposed_corrections": {}, "rationale": None})
        img.save(OUT_IMG / f"{doc}-p{page_no}.png")
        L.append("")
    L += ["## Review status", "", f"0 of {len(sheet)} targets reviewed. No reviewer has been assigned. This packet does not mark any reference as verified.", ""]
    (ROOT / "docs" / "REFERENCE-REVIEW-PACKET.md").write_text("\n".join(L), encoding="utf-8")
    if not SHEET.exists():
        SHEET.write_text(json.dumps({"schema": "evi.reference-review/1", "reference_file": "references-v1.json",
                                     "reference_sha256": hashlib.sha256(ref_raw).hexdigest(), "items": sheet}, indent=1), encoding="utf-8")
    print(len(sheet), "targets;", "images in", OUT_IMG)


if __name__ == "__main__":
    main()
