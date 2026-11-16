# 05 — Period and unit verification engine

## Purpose and boundary

The engine checks whether an extracted financial fact faithfully represents its cited source context. It does not certify the issuer's accounting, discover fraud, or prove a PDF is economically truthful. It must expose unsupported interpretations rather than filling gaps.

Docling supplies structure and coordinates. Reuse that structure instead of implementing a second table parser. The engine's original work is binding a candidate fact to the right contextual meaning and checking deterministic constraints.

## Stage 1 — Source and anchor integrity

1. Confirm PDF bytes still match the registered hash.
2. Confirm referenced evidence IDs exist in the parsed source version.
3. Confirm the candidate value is actually in the cited cell and belongs to the selected column.
4. Confirm row-label support for the metric definition.
5. Keep the number, row label, period, and unit evidence separately addressable.
6. If coordinates are unavailable, expose text-only evidence with a limitation. Never render a fabricated highlight.

## Stage 2 — Parse the amount

- Preserve original text and use Decimal for parsed and normalized values.
- Determine numeric locale explicitly. English `1,234.5` and Indonesian `1.234,5` are not interchangeable.
- Parentheses indicate negatives when the table convention supports that reading.
- A dash can mean zero, not applicable, or missing; use the stated convention, otherwise mark unknown.
- Do not treat a footnote superscript or reference number as part of the amount.
- Missing values and actual zero must remain distinguishable.
- A percent, per-share amount, customer count, or ratio is not a monetary amount merely because the document has a currency header.

On ambiguous separators, do not let an automatic heuristic silently determine a billion-fold transformation. Record the ambiguity and source convention.

## Stage 3 — Unit and currency context

Find the most specific applicable explicit statement in this order:

1. Individual cell or column annotation.
2. Applicable table/merged header.
3. Caption or immediately associated unit note.
4. Section-level convention demonstrably applicable to this table.
5. Document-level default only when no local exception applies.

Specificity is not enough if association is uncertain. Conflicting evidence remains a conflict; the model cannot pick the convenient unit and call the conflict resolved.

### Unit examples

| Supported text | Currency | Scale |
| --- | --- | --- |
| “in millions of Rupiah” / “dalam jutaan Rupiah” | IDR | 1000000 |
| “in billions of Rupiah” / “dalam miliar Rupiah” | IDR | 1000000000 |
| “IDR billion” | IDR | 1000000000 |
| “Rp million” | IDR | 1000000 |
| “in thousands of U.S. Dollars” | USD | 1000 |

These are supported-language examples, not a license to apply every unit appearing on the page to every cell. A report may say IDR millions and, where specified, USD thousands. Bind the selected cell to the relevant currency/column.

Normalize through `parsed_amount * unit_scale`. Save both operands and the original text. Displaying every result in IDR billions is allowed, but the original scale remains visible. Do not use FX conversion in the core build.

## Stage 4 — Reporting period

The engine must distinguish document publication date, balance-sheet date, comparative column date, and the interval of an income statement.

Examples:

- “For the year ended December 31, 2024” -> 2024-01-01 through 2024-12-31, 12 months, annual.
- “For the nine months ended September 30, 2025” -> 2025-01-01 through 2025-09-30, 9 months, year-to-date.
- “For the three months ended September 30, 2025” -> 2025-07-01 through 2025-09-30, 3 months, quarter.
- “For the three months ended March 31, 2025” -> 2025-01-01 through 2025-03-31, 3 months, quarter.

Apply fiscal-calendar assumptions only when supported by the issuer/report. Do not universally assume calendar years for arbitrary future documents.

### Common traps to support

1. A PDF filename contains 2025 but the selected column is 2024.
2. A nine-month table is labeled annual because only its end year was extracted.
3. Three-month and nine-month columns share the same September end date.
4. A balance-sheet date on a neighboring page overwrites the income-statement interval.
5. A report contains a current nine-month column and a comparative nine-month column; each needs its own year.
6. An annual presentation contains a separate quarterly summary; document type cannot override the column heading.

If the model proposes annualization, preserve the reported interim value and flag the unsupported transformation. No `9m * 12 / 9` calculation belongs in the core extraction output.

## Stage 5 — Metric scope

Period and scale checks cannot rescue a wrong metric. Check that revenue is consolidated, operating profit is explicitly reported, and attributable profit excludes non-controlling interests as required by the target definition. A plausible nearby number is not enough.

Do not implement an expansive accounting ontology. A small alias dictionary may help retrieval, but source support decides whether an alias is valid for the specific fact.

## Stage 6 — Compatibility

Two facts are directly comparable only if:

- Metric definitions and consolidation scope match.
- Currencies match.
- Interval types and dates are appropriate for the intended comparison.
- Scale can be normalized with supported evidence.

Nine-month 2025 versus nine-month 2024 can support a like-for-like comparison. Nine-month 2025 versus full-year 2024 must be flagged as different durations. The display can show both but must not generate unqualified growth.

## Correction policy

A deterministic rule may compute normalization when its operands are supported. A semantic change to currency, metric, or interval needs evidence and produces a new fact version. Keep the initial prediction immutable so before/after evaluation remains meaningful.

Do not reject every difficult fact to improve precision. Unresolved facts count against strict task correctness as specified in the benchmark, and coverage is reported separately.

## Required mechanism tests

- Correctly anchored annual value passes without alteration.
- Same value with a 12-month claim against a nine-month heading fails.
- Correct nine-month value remains nine-month after an evaluator suggests annualization.
- Million/billion mismatch is detected; canonical Decimal normalization is exact.
- Correctly normalized zero and missing amount remain different.
- Ambiguous locale yields unknown rather than a guessed correction.
- A value from the wrong comparative column is rejected or flagged.
- A balance-sheet date cannot supply an income interval.
- A valid source hash with an invented evidence ID fails.
- Mixed currency notes do not automatically change every cell's currency.
- An unavailable source check is unknown, not pass.

Controlled corruptions verify mechanism behavior only. Their pass rates must never be merged into the headline natural-extraction benchmark.
