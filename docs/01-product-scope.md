# 01 — Product scope and reasoning checkpoint

## User and task

The initial user is an analyst or research associate comparing telecom companies in a spreadsheet. They collect a small set of financial metrics from public annual and interim reports. They need to know what each figure measures, which period it covers, how it is scaled, and where the supporting evidence appears.

The first corpus uses Indonesian telecommunications issuers because English/bilingual reports expose real million-versus-billion conventions and annual-versus-interim reporting periods.

## Concrete failure

A parser can correctly transcribe 125 while an extraction agent labels it as annual revenue even though the heading says “nine months ended September 30.” Similarly, an amount stated in millions can be normalized as billions. The spreadsheet looks tidy, but comparisons and downstream calculations are wrong.

The analyst bears rework and review time; recipients of the analysis bear the consequences of wrong comparisons. Neither time savings nor monetary losses have been quantified for this product. Do not invent them.

## Mechanism

Docling extracts tables and source positions. SERV produces structured candidate facts and reasons over ambiguous headers, captions, and period descriptions. EvidenceGrid checks evidence anchoring, numeric interpretation, units, reporting intervals, and comparison compatibility. Reppo critiques the evidence-backed extraction. A bounded SERV revision can use that feedback to propose a corrected version. The application rechecks every proposal against source evidence before including it in the grid.

## Strongest practical alternatives

1. A careful analyst using PDF search, spreadsheets, and a checklist.
2. Docling plus a competent one-shot model prompt with the same source context.
3. A domain-specific financial data provider with normalized values.

EvidenceGrid must show useful additional semantic accuracy or less review effort against alternative 2. A source-link badge or a generic PDF chat interface does not establish that advantage. Alternative 3 may be better when it covers the exact required issuers, definitions, and periods affordably.

## Value proposition to test

“Extract three telecom metrics while preserving their original reporting period and monetary scale, surface mismatches, and show exactly which source evidence supports each correction.”

This is a hypothesis. Existing parsing libraries and a working demo do not establish paying demand.

## Locked scope

| Dimension | Decision |
| --- | --- |
| Sector | Indonesian telecommunications |
| Documents | 4 initially; maximum 6 public PDF reports |
| Metrics | Consolidated revenue; operating profit; profit attributable to owners of the parent |
| Initial output | Source-linked fact grid, normalized values, period/unit checks, immutable revisions |
| Feedback | Real Reppo critique consumed by a bounded SERV revision |
| Evaluation | Frozen human labels and a document-level holdout split |
| Language | English product and documentation; bilingual source evidence allowed |

### Metric definitions

- `revenue`: consolidated reported revenue, not one segment's revenue.
- `operating_profit`: the issuer's explicitly reported consolidated operating profit/income. Do not replace it with EBITDA, EBIT calculated by us, or profit before tax.
- `profit_attributable_to_owners`: profit attributed to owners of the parent. Do not substitute total profit including non-controlling interests.

If a report does not support a requested definition, record missing or needs review. Do not fabricate a mapping to fill the grid. Corpus selection should prefer reports with the required definitions; freeze eligibility before scoring.

## Non-goals

- General investment advice, valuation, stock recommendations, or forecasts.
- FX conversion or comparison across currencies through invented rates.
- Automatic annualization of interim values.
- Reconstructing a quarter by subtracting YTD values in the core build.
- Restatement propagation or recalculating dependent models. The roadmap may explain this idea only.
- Arbitrary document categories, full accounting compliance, unlimited metrics, or a production data warehouse.
- Multi-agent theater, model fine-tuning, wallets, or token economics.

## Validation plan

First verify that real Docling output retains enough table context and coordinates to distinguish annual from nine-month facts. Then measure a fair one-shot baseline against the feedback-assisted pipeline. Separately ask reachable analysts to complete a source-checking task and observe where they spend time; do not claim interviews unless they happened.

Reasons to narrow or abandon the proposed advantage:

- A fair baseline already handles all selected cases.
- Most errors come from missing OCR rather than period/unit interpretation.
- Reppo critiques are too generic to change useful behavior.
- The correction loop increases apparent confidence without improving correctness.
- An analyst spends more time configuring evidence than checking a few numbers manually.

## Minimal working demonstration

One real interim PDF produces a candidate fact. If a natural extraction mislabels its period or scale, the source heading and corrected fact are shown together. The original output remains inspectable. A second demonstration uses an explicitly labeled controlled corruption if no natural failure occurs. Only natural extraction results count in the primary benchmark.

## Complete submission target

A local analyst can select a corpus report, run parsing and extraction, inspect source regions, review a real asynchronous Reppo verdict, run a constrained revision, compare original and revised versions, and export the evidence. A benchmark view separately reports measured semantic correctness, coverage, regressions, latency, and provider usage.
