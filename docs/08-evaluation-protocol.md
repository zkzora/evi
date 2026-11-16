# 08 — Frozen evaluation protocol

## Claims this protocol can support

Measure extraction fidelity on this small, explicitly named corpus. Do not present it as a population-wide financial-document accuracy estimate. The goal is a reproducible before/after result whose denominator and inputs are visible.

The user's example “70% to 90%” is a possible presentation format, not a result, promise, tuning objective, or completion gate.

## Corpus and split

- Begin with 4 public reports from one sector; expand to at most 6 only if needed for source availability or meaningful period/unit coverage.
- Prefer annual and interim reports with real differences in duration and unit conventions.
- Suggested initial design: two Telkom reports for development and two XL Axiata reports for holdout. Verify source contents and availability before committing this split.
- Keep all reports from an issuer in the same split where feasible. Do not distribute near-identical templates across development and holdout merely to obtain an easier result.
- Define the target columns before model runs. Usually current and comparative columns yield six facts per document: 3 metrics x 2 columns.
- Four such reports yield up to 24 fact targets; six yield up to 36. These are planning counts. Actual eligible counts come from the frozen manifest/labels.
- If a metric is not explicitly available, determine eligibility before inference. Document exclusions; never remove a failed target after seeing predictions.

## Human reference labels

For each target, a human annotator reads the original rendered source page and records:

1. Source hash and physical PDF page.
2. Requested metric and exact source row label.
3. Column/year and reporting interval start/end/duration.
4. Original printed amount and numeric convention.
5. Currency and scale with supporting heading/note.
6. Canonical Decimal amount.
7. Consolidation and attributable-profit scope.
8. Evidence regions and annotation rationale.

Use a second review where possible. If labels are checked only by the builder, disclose “builder-annotated, source-reviewed,” not independent annotation. An AI-generated label is not an independent gold label just because a different prompt produced it.

Freeze labels and target manifest with hashes. Keep them separate from inference inputs. Do not preload a dashboard response with labels disguised as extraction output.

## Arms

### Arm A — One-shot baseline

Use real Docling output plus a competent SERV extraction prompt. Include all initially available relevant headings, unit notes, and column context. Use the same model and schema as the initial step in Arm B. Preserve invalid/missing outputs and the complete original artifact.

### Arm B — Feedback-assisted pipeline

Start from the exact Arm A prediction and initial packet. Add deterministic checks, a real Reppo evaluation, and a bounded SERV revision. Any extra context retrieval is logged. Score the final automated child version without cherry-picking the best intermediate result using gold labels.

This is an end-to-end pipeline comparison. It does not isolate Reppo's causal contribution from deterministic checks, extra model calls, and additional context.

### Optional ablation — Checks plus SERV revision without Reppo

Use the same source packet, model, call/retrieval budget, and deterministic diagnostics but no Reppo critique. Compare it with Arm B if making a claim that external feedback itself adds value. Do not implement this before the core loop works.

## Primary metric: strict semantic correctness

Match predictions to a frozen target key: document + requested metric + target column identity. The target key is scoring metadata, not a prefilled semantic answer in the model prompt.

A fact is strictly correct only when all required fields match the reference:

- Metric definition and consolidated/attributable scope.
- Currency and source unit scale.
- Reported amount interpretation and canonical normalized amount.
- Start date, end date, duration, and period kind.
- Evidence anchoring identifies the supporting value cell and applicable source context.

```text
Strict semantic correctness = correct eligible target facts / all eligible target facts
```

Missing, unresolved, malformed, refused, or unsupported facts remain in the denominator and count as incorrect for the primary task metric. Also report coverage so an always-abstaining system cannot appear successful.

If multiple predictions compete for one target without an unambiguous selected result, count the target as unresolved rather than choosing whichever matches gold.

## Secondary metrics

| Metric | Definition |
| --- | --- |
| Period correctness | Exact interval fields correct, over all eligible targets |
| Unit correctness | Currency and source scale correct, over all eligible targets |
| Numeric correctness | Canonical amount correct under frozen tolerance, over all eligible targets |
| Evidence correctness | Value and governing context citations support the fact |
| Coverage | Targets with a complete prediction, regardless of whether correct |
| Improvement count | Incorrect baseline targets that become correct |
| Regression count | Correct baseline targets that become incorrect |
| Unchanged incorrect | Incorrect in both arms |
| Latency and usage | Per arm and document, including feedback settlement waiting time |

Use exact Decimal equality when the source number is exact at its reported precision. If rounding tolerance is needed, define it from displayed precision before runs and apply it identically to both arms. No after-the-fact tolerance changes.

## Reporting format

Always show counts next to percentages. Example layout with placeholders:

| Split | Arm | Strict correct | Period correct | Unit correct | Coverage |
| --- | --- | --- | --- | --- | --- |
| Development | Baseline | pending | pending | pending | pending |
| Development | Feedback-assisted | pending | pending | pending | pending |
| Holdout | Baseline | pending | pending | pending | pending |
| Holdout | Feedback-assisted | pending | pending | pending | pending |

Show absolute percentage-point change, not an ambiguous “percent improvement.” Report unchanged or worse performance honestly. No results appear until a real benchmark artifact exists.

Provide per-document and per-metric details. Targets within a document are correlated; do not manufacture strong statistical significance from a few PDFs. Broad reliability claims need a larger independent corpus.

## Freeze procedure

1. Finalize sources, requested columns, eligibility, and human labels.
2. Work only on development documents to implement/tune extraction, rules, and feedback use.
3. Freeze parser settings, evidence-building rules, model, prompts, revision budget, and scorer version.
4. Record hashes and a freeze timestamp.
5. Run inference on holdout sources without exposing labels.
6. Save predictions; only then invoke the scorer.
7. Record the first result. Do not discard it because the baseline performs too well or the revision underperforms.
8. If code/prompt changes after reviewing holdout outcomes, label the subsequent run as post-inspection. Obtain new untouched reports for a fresh holdout claim.

Reading holdout labels to implement a generic schema is unnecessary and should be avoided. Any existing developer inspection must be disclosed; do not describe an internally prepared dataset as independently blind.

## Feedback learning and leakage

Development feedback can improve a policy used on holdout. Holdout Reppo feedback may be used for the predefined within-document revision algorithm; that is allowed test-time feedback, not gold-label access. Do not manually tune the shared policy based on holdout critiques before scoring the remaining holdout documents.

Manual edits, source labels, Reppo sandbox placeholders, and deliberately injected wrong periods must not enter natural-extraction accuracy calculations.

## Controlled mechanism suite

Maintain a separate suite with known injected faults: nine months mislabeled annual, million interpreted billion, wrong comparative column, wrong currency from a neighboring note, and invalid evidence ID. These verify that checks and revisions behave as intended. Report them under “controlled mechanism tests,” not the headline extraction accuracy.

## Reproducibility artifacts

Save corpus manifest/hash, source hashes, parser versions/config, Docling/evidence packets, policy/model settings, raw predictions, real evaluation IDs/results, revision trace, frozen label/scorer hashes, final metrics JSON, and human-readable report. Include all failed attempts and actual budget use.

## Acceptance gate

The evaluation harness produces correct counts on independently hand-derived scoring cases, preserves missing targets, detects regressions, and runs on frozen real outputs. A null or negative uplift is a valid measurement; the product should then present the evidence and reassess the mechanism rather than invent a success.
