# 04 — Data contracts

Implement these as validated contracts. Field names in this file are the canonical vocabulary for other specifications. JSON examples are illustrative and are not measured issuer data.

## Document

Required fields:

| Field | Type / meaning |
| --- | --- |
| `document_id` | Stable manifest ID |
| `issuer_id`, `issuer_name` | Canonical issuer identity |
| `title` | Publisher report title |
| `source_url` | Original public publisher URL |
| `sha256` | Hash of original PDF bytes |
| `downloaded_at` | UTC timestamp |
| `page_count` | Physical PDF pages |
| `page_ranges` | 1-based inclusive physical page ranges selected for parsing |
| `split` | `development` or `holdout` |
| `availability` | `registered`, `downloaded`, `unavailable`, `invalid` |
| `parse_status` | `not_started`, `queued`, `running`, `parsed`, `partial`, `failed` |

A parser cannot change `split`. A changed PDF hash is a new source version.

## Evidence cell and context

An `EvidenceCell` represents a value, row label, header, or text item returned by Docling:

```json
{
  "evidence_id": "ev_example_value_1",
  "document_id": "example-9m2025",
  "document_sha256": "<actual hash>",
  "kind": "value_cell",
  "table_id": "table_3",
  "row_index": 4,
  "column_index": 2,
  "text": "125",
  "page_number": 8,
  "printed_page_label": "3",
  "bbox": {"left": 300, "top": 190, "right": 350, "bottom": 210, "origin": "TOPLEFT"},
  "page_width": 595,
  "page_height": 842,
  "parser": "docling",
  "parser_version": "<actual version>"
}
```

Stable IDs derive from source hash, Docling item identity, table/row/column, and parser version. Save original coordinates before converting origin conventions for browser display. Do not invent a bbox when Docling provides none.

An `EvidenceWindow` groups IDs and text for:

- Value cell and metric row label.
- Applicable column headers, including merged parent headers.
- Caption and section heading.
- Unit/currency statement and the context where it applies.
- Relevant footnote, when required to disambiguate a supported field.

Save a hash for the exact window sent to a provider. Do not truncate the context silently to fit a token limit; report coverage and requested context retrieval.

## Fact

```json
{
  "fact_id": "fact_example_revenue_2025_9m",
  "document_id": "example-9m2025",
  "metric": "revenue",
  "metric_label": "Revenues",
  "scope": "consolidated",
  "reported_value": "125",
  "numeric_locale": "en",
  "currency": "IDR",
  "unit_scale": "1000000000",
  "normalized_value": "125000000000",
  "period": {
    "start_date": "2025-01-01",
    "end_date": "2025-09-30",
    "duration_months": 9,
    "kind": "year_to_date",
    "label": "Nine months ended September 30, 2025"
  },
  "evidence": {
    "value_ids": ["ev_example_value_1"],
    "metric_ids": ["ev_example_label_1"],
    "period_ids": ["ev_example_period_1"],
    "unit_ids": ["ev_example_unit_1"]
  },
  "origin": "serv_initial",
  "review_status": "unreviewed",
  "notes": []
}
```

Canonical monetary fields are decimal strings, not JSON floating-point numbers. `unit_scale` is one of `1`, `1000`, `1000000`, `1000000000`, `1000000000000`, or null. `normalized_value` is computed by application code; model-provided canonical arithmetic is ignored and recomputed.

Allowed metrics: `revenue`, `operating_profit`, `profit_attributable_to_owners`. Unknown/null fields are allowed with explicit issues. `reported_value` preserves original formatting, parentheses, and separators.

Allowed period kinds: `annual`, `quarter`, `half_year`, `year_to_date`, `unknown`. Start/end dates must agree with duration. A balance-sheet “as of” date alone does not establish an income-statement interval.

Allowed origins: `serv_initial`, `serv_revision`, `manual`. Controlled-corruption scenarios are stored in a separate test artifact with an explicit marker, not disguised as ordinary model predictions.

`review_status`: `unreviewed`, `needs_review`, `reviewed`, `excluded`. This is workflow status, not correctness. Scoring eligibility is frozen separately and cannot be changed to inflate a result.

## CheckResult

```json
{
  "check_id": "check_example_period",
  "fact_id": "fact_example_revenue_2025_9m",
  "check_type": "period_duration",
  "status": "fail",
  "message": "Candidate says 12 months; cited heading says nine months.",
  "evidence_ids": ["ev_example_period_1"],
  "observed": {"duration_months": 12},
  "supported": {"duration_months": 9},
  "checker_version": "period-unit-v1"
}
```

Check statuses: `pass`, `fail`, `unknown`, `not_applicable`. Unknown evidence is not a passing check. Supported values are emitted only when the rule can establish them from evidence.

Core check types: source integrity, evidence membership, numeric parse, metric support, currency, unit scale, period dates, period duration, normalization, and comparison compatibility.

## ExtractionRun and FactVersion

`ExtractionRun` contains `run_id`, `document_id`, `source_sha256`, `initial_packet_sha256`, `policy_version`, `model`, `mode`, `created_at`, `status`, `parent_run_id`, provider attempt IDs, usage/timing metadata, and artifact hashes.

`FactVersion` contains `version_id`, `run_id`, `parent_version_id`, `origin`, `facts[]`, `checks[]`, `change_set[]`, and a content hash. The initial and each revision are immutable. No manual version can be mistaken for an automated revision.

## RevisionProposal

Required fields: `parent_version_id`, `changes[]`, `unresolved[]`, `feedback_id`, `reason`, `supporting_evidence_ids`, and requested context IDs if any. Each change names `fact_id`, field path, old value, proposed value, evidence IDs, and reason. Only a documented allowlist of fact fields is editable. Unknown fields and attempts to mutate source identity are rejected.

## EvaluationAttempt and Evaluation

Record attempts before external POST: `attempt_id`, `run_id`, `version_id`, request hash, request artifact, provider, mode, timestamps, state, HTTP metadata, and optional `eval_id`.

Modes: `reppo_live`, `reppo_recorded`, `reppo_sandbox`, `local_contract_fixture`. Recorded real feedback must retain its original provider identifiers and cannot be presented as freshly obtained.

Provider statuses are preserved verbatim plus a normalized status. Expected Reppo statuses include `PENDING`, `SETTLED`, `FAILED`, and `DENIED`; an unrecognized status becomes `unknown_provider_status` and is never assumed successful.

Preserve overall verdict, criterion critiques, confidence, routing, evidence basis, contributor fields, credits charged, and raw response. Unknown fields should not be discarded from the raw artifact.

## GoldLabel and BenchmarkResult

Gold labels are maintained separately from inference artifacts. Each eligible gold item has document/issuer, metric, target column/interval, reported amount, currency/scale, normalized amount, supporting pages/regions, annotator, review status, label version, and source hash.

Benchmark results contain counts and denominators, field scores, strict semantic scores, coverage, regressions, per-document results, run/policy/source/label hashes, provider mode, timing, and usage. See docs/08-evaluation-protocol.md for exact scoring.

## Export invariants

Every exported fact carries source identity, evidence references, original and normalized amounts, exact interval, unit, version, origin, check statuses, and feedback mode. Unresolved values remain present. Secrets, hidden gold labels, and credentials are excluded from ordinary analyst exports.
