# Reviewer instructions — Evi reference labels (references-v1, 48 targets)

**Who can review:** a person who did **not** author the draft labels and who will inspect the issuer PDFs themselves. The project user may review if they did not write the labels. An AI pass, or the builder's own re-check, is recorded as such and is **not** independent human review.

**What you need:** `docs/REFERENCE-REVIEW-PACKET.md` (one table per report), the rendered pages with numbered boxes in `artifacts/reference-review/`, and the original PDFs (issuer URLs and SHA-256 hashes are in the packet). Allow roughly 1–2 hours.

## Steps

1. Make a copy of `data/references/review/review-sheet-references-v1.json` (for example `review-sheet-<your-name>.json`). Do not edit the draft values.
2. Fill in `review_provenance`:
   - `reviewer_name`
   - `reviewer_relation`: one of `independent_human`, `user_not_label_author`, `builder` or `agent`
   - `method`: e.g. "opened the issuer PDFs at the listed pages"
   - `declaration`: one sentence stating you did not author the labels (if true)
3. For **each** of the 48 items:
   - `review_status`: `confirmed` (the draft is right), `corrected` (give field-level `proposed_corrections`) or `ambiguous` (the page does not settle it — explain why; you are not forced to choose).
   - `reviewer`, `reviewed_at` (YYYY-MM-DD) and a target-specific `rationale`.
   - `source_evidence`: what you saw, e.g. "p.2 row 'Net Income Attributable to AT&T', column '2025' under 'Second Quarter', header 'Dollars in millions'".
   - Identical copied text across many items is rejected as a blanket approval.
4. Check the points flagged at the top of the packet. In particular: does "owners of the parent" mean the line attributable to AT&T, before preferred dividends? And should AT&T end dates stay null, because the statement page prints none?
5. Correction formats: `amount` as a plain decimal (`-174`, `4500`); `unit_scale` as `1`/`1000`/`1000000`/`1000000000`; dates as `YYYY-MM-DD` or `null`; `currency` as an ISO code (`USD`).

## Validate and import (run by the project owner)

```
cd backend
.venv\Scripts\python -m evi.review validate ..\data\references\review\review-sheet-<name>.json
.venv\Scripts\python -m evi.review import   ..\data\references\review\review-sheet-<name>.json [--adjudication adj.json]
.venv\Scripts\python -c "from evi import analysis; print(analysis.evaluate_reviewed('exp-2026-11-16-a', '<path printed by import>'))"
```

- `validate` writes nothing.
- `import` refuses incomplete sheets and creates `data/references/reviewed/references-r1-<hash>.json` plus a change log. `references-v1.json` is never edited.
- Ambiguous entries stay ambiguous unless an adjudication file records a decision (`keep_draft`, `apply_correction` or `unresolvable`) with the adjudicator, date and rationale.
- Reviewer identity is self-declared in the sheet; the import records that it is not independently authenticated.
