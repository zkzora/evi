# Technical depth — implemented mechanisms (2026-11-16)

Status labels: **implemented** (code exists and is covered by tests), **executed** (ran on real sources and providers), **measured** (scored against frozen references). Results are in [PROOF-REPORT.md](PROOF-REPORT.md).

## 1. Gap audit at the start of this work

| Area | Evidence before the change | Gap against docs/19 | Resolution |
|---|---|---|---|
| `checks.py` `run_checks` | Period check read *all* cited period texts together; IDs only had to exist in the parse | A valid ID from another column, or "millions" anywhere in the packet, could satisfy a check | `binding.py` derives applicability from table structure. A cited ID that is not on an applicable path fails (`period_evidence` / `unit_evidence` field verdicts) |
| `extraction.py` v1 | Fixed target "most recent fiscal year presented" | Interim and comparative columns could not be addressed | `targets.py` freezes 48 targets as (interval months × fiscal-year column); `run_extraction_v2` asks for each target_key |
| `extraction.py` `apply_changes` | Accepted a change if it had no failures and no fewer passes | Pass counting allowed dropping evidence or abstaining to "win" | `revision.py` `gate`: field-by-field comparison with a fixed field universe; abstention only when the resolver finds no supported reading |
| `evaluation.py` `map_result` | A missing score became `0.0` | Missing data turned into a number | Missing scores stay `null`; the UI shows "not returned"; the rubric scale is 0–100 |
| `parsing.py` | Evidence rows hold non-empty cells only | Spans, empty structure and table bounds were needed | `binding.load_structure` reads the stored Docling JSON (full grid, half-open spans, `column_header`/`row_section`, table bbox). Its SHA-256 goes into every certificate. No reparse was needed |
| Page mapping | Not validated | Doc 19 §2 | Docling `page_no` equals the physical 1-based page under `page_range`. Validated with real bbox↔pdfium text matches (96/96 target cells, `tests/test_integration_real.py`) |
| CropBox | Fixed earlier | — | The audit keeps the CropBox offset; 4 documented non-target AT&T box exceptions are listed by name |

## 2. Source nodes and applicability relations — `backend/evi/binding.py`

Nodes: `Structure` (source SHA-256, parse ID and cache key, Docling artifact SHA-256, pages), `Table` (page, grid size, TOPLEFT bounds), `Cell` (half-open `[r0,r1)×[c0,c1)`, header flags), `Text` (label, page, TOPLEFT geometry). Evidence IDs are derived exactly as `parsing._evidence_id` derives them.

Each relation edge records its rule:

| Relation | Rule | Meaning |
|---|---|---|
| `row_label_for` | R-ROW-LEFTMOST | The column-0 cell on the value's row |
| `section_scope_for` | R-SECTION-PRECEDING | The nearest label-only row above, inside the data region (e.g. "Basic Earnings Per Common Share") |
| `section_scope_for` | R-SCOPE-TITLE | A statement title ("Consolidated Statements of Income") above the table on the same page |
| `column_header_for` | R-HDR-SPAN | A header cell whose half-open span covers the value column |
| `duration_heading_for` | R-DUR-COLUMN | The smallest-span covering header that states a duration ("3 Mos. Ended", "Third Quarter", "Nine-Month Period") |
| `duration_heading_for` | R-DUR-TABLE-ROWLABEL | A duration stated in a header-row label ("Years Ended December 31,") applies table-wide, only when no covering header states one |
| `year_header_for` | R-YEAR-SPECIFIC | The most specific covering header naming exactly one year. A parent naming several years is disambiguated by its child |
| `unit_applies_to` | R-UNIT-COLUMN > R-UNIT-TABLE > R-UNIT-CAPTION | Specificity order. A caption counts only if no other table lies between it and the target table. Equally specific conflicting scales are a conflict, never a tie-break |
| exception | per-share | An "except per share" statement plus a per-share row or section means the scale does not apply (U2 fails, M2 fails) |
| non-monetary | percent column | A "% Change" / "Percent Change" header covering the column means U2 fails |

Calendar rule R-CAL-MONTHEND: a stated N-month interval ending on the last day of a month starts on the first day of the month N−1 months earlier. Week-based language and non-month-end dates make P3 unknown, and the fact is then not supported. If no end date is printed (AT&T schedules), P3 is `unknown/end_date_not_stated` and both dates stay null.

## 3. Obligations, candidates and resolution

`evaluate_cell` produces S1, S2, M1, M2, P1, P2, P3, U1, U2, N1, N2 and C1, each with a status (`pass`/`fail`/`unknown`), a reason code and evidence. `resolve_target` enumerates the value cells whose row matches the metric definition and whose derived (duration, year) equals the target. It caps candidates at 12; above that the target is unresolved. Supported candidates are grouped by the full semantic tuple: one class means supported, more than one means `ambiguous_context` (unresolved), none means unresolved with the reasons. Equivalent cells with the same semantics are one class.

Owners of the parent = the "Net income … attributable to <parent>" line, before preferred dividends. "Attributable to common stock" and "noncontrolling" are different scopes.

## 4. Certificates and verifier — `binding.build_certificate`, `binding.verify_certificate`, `evi/certify.py`

Each certificate holds: source and parse identities, the Docling artifact hash, the target, the claim, field verdicts (claimed versus applicable reading of the claim's own cell), the claim cell's full reading (tuple, obligations, edges), the target resolution (all candidates) and a boundary statement. It is serialized as canonical JSON, with a SHA-256 content hash and money as decimal strings.

The verifier recomputes the whole certificate from the registered PDF bytes and the Docling artifact. It does not just check the hash, so edited amounts, dates, scales, edges or evidence IDs fail even after the hash is recomputed.

```
backend\.venv\Scripts\python -m evi.certify <version_id>          # new check run; the version is untouched
backend\.venv\Scripts\python -m evi.certify --verify <cert_id|file.json>
GET /api/v1/versions/{id}/certificates · GET /api/v1/certificates/{id} · GET /api/v1/certificates/{id}/verification
```

The historical versions (`ver_b76…`, `ver_b9c…`, `ver_eb2…`) were re-checked as new `check_runs`. Their stored checks are unchanged.

## 5. Revision gate — `backend/evi/revision.py`

- Patchable fields only: value cell, amount text, currency, scale, duration, fiscal year, dates, and the evidence-ID groups. Target key, metric, document and source are immutable.
- A patch is rejected if it uses a forbidden field, cites foreign or invented IDs, or has no supporting evidence.
- Accepted only if the patched candidate's certificate is `supported` and the parent's was not.
- Rejected if any parent field that passed would stop passing (`regression_on_supported_fields`), or if it swaps one supported reading for another.
- Abstention (`mark_unresolved`) is accepted only when the deterministic resolver also finds no supported reading; the coverage loss is recorded.
- Every target stays in the child. A child version and a receipt are stored even when every decision is unchanged or rejected.
- Arm C (no feedback) and arm D (completed real Reppo evaluation of exactly this parent) share the prompt skeleton, packet, model, single call and gate. Retrying with the same idempotency key returns the stored receipt.

## 6. Experiment and scoring — `backend/evi/experiment.py`, `backend/evi/scoring.py`

`freeze` writes the manifest (sources, parses, Docling artifact hashes, targets, reference hash and provenance, policy, prompt and code hashes, model, arms, schedule with seed, caps, stopping and failure rules). `run` executes A/B/C/D and appends to `ledger.jsonl`. `scoring` is the only module that reads `data/references/references-v1.json`; `tests/test_leakage.py` enforces this.

## 7. Supported and unsupported cases

Supported: single-table income statements whose headers span value columns; annual "Years Ended" row-label headings; interim "3 Mos. Ended m/d/yy", "Third Quarter", "Six/Nine-Month Period" groups; a unit caption in the table or above it; per-share sections; percent-change columns; negative amounts in parentheses.

Unsupported (returned as unknown or unresolved, never guessed): 52/53-week calendars; tables continued across pages (no `continuation_of` edge is built); statements whose title or unit note sits outside the parsed page range; non-USD sources; footnote markers attached to amounts; multi-row wrapped labels in the value row.

## 8. Proof-integrity additions (2026-11-16)

- **replay-v2** (`evi/replay.py`): read-only (`sqlite mode=ro`). The required binding policy comes from the manifest. Coverage is derived from expected branches × frozen targets × actual versions. It fails on missing, conflicting, wrong-policy and unknown-policy certificates, missing branches, identity, content or receipt mismatches, and source, parse or reference hash changes. The score is recomputed in memory (`scoring.compute`). `--all-certificates` is a separate all-history audit.
- **analysis-v2** (`evi/analysis.py`): raw field status (match/mismatch/missing/null_both/spurious); the application-derived start date comes from the model's own end date and duration; reference match, complete interval, certificate outcome, composite and detector TP/FP/FN are reported separately; target-level reconciliation.
- **coverage-v1** (`binding.coverage_view`): an additive view separating a unique supported reading, complete required context and unknown fields. It appears in `GET /versions/{id}` (`facts[].context_coverage`), `/versions/{id}/certificates`, `/certificates/{id}`, the Workspace chips and badge, and the CSV export. Stored certificates are unchanged.
