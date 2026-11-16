# 09 — Dashboard and main menu specification

> This file specifies screens and behavior only. No frontend has been implemented. Claude Code should build these screens after the core document-to-fact slice is working.

## Product entry point

The analyst's main job is to inspect a financial fact, understand its period and unit, and verify the source. Make the Evidence Grid the primary working screen. The Overview is a summary and next-action screen, not a wall of decorative charts.

All labels, help text, errors, exports, and demo copy are English. The product name is EvidenceGrid.

## Persistent navigation

| Order | Main menu | Route | Primary task |
| --- | --- | --- | --- |
| 1 | Overview | `/` | See corpus/run readiness and continue the next useful task |
| 2 | Documents | `/documents` | Select a source report, inspect provenance, parse it |
| 3 | Evidence Grid | `/grid` | Inspect and compare extracted financial facts |
| 4 | Review Queue | `/review` | Resolve period/unit issues with source evidence |
| 5 | Feedback | `/feedback` | Submit/read Reppo evaluations and run revisions |
| 6 | Benchmark | `/benchmark` | Inspect measured baseline/revised results |
| 7 | Exports | `/exports` | Download versioned analyst and evidence artifacts |
| 8 | Settings | `/settings` | See provider readiness and bounded run configuration |

Do not add trading, wallets, generic chatbot, team management, billing administration, model marketplace, or unrelated analytics menus.

## Shared shell

- Desktop: compact left sidebar, page title and context bar, main workspace.
- Context bar: selected document/run/version, source issuer, and explicit provider mode when relevant.
- Preserve document ID, run ID, version ID, and supported filters in the URL so a copied local link reopens the same context.
- A background job indicator shows real active jobs; it is not an animated simulation of agent work.
- Notifications show outcomes such as parse complete, evaluation settled, revision unsupported, or export ready.
- Display each fact's reporting period in its own row. A global filter must not silently relabel all numbers as annual.
- Never show API key values or hidden gold-label contents in the shared shell.

## 1. Overview

### Content

- Heading: “Financial facts, with their context intact.”
- Corpus readiness: registered/downloaded/parsed document counts.
- Extraction readiness: documents with initial outputs and unresolved issues.
- Feedback status: pending, settled, failed, or unavailable real Reppo evaluations.
- Latest measured benchmark summary only if a benchmark artifact exists. Otherwise show “No benchmark run yet.”
- Recent activity with actual timestamps and links to the relevant document/run.
- A single useful next action determined by current state: Parse a document, Run extraction, Inspect flagged facts, or Read settled feedback.

### Interactions

Clicking a count opens its corresponding filtered list. “Continue review” opens the first unresolved fact in the selected run. Do not invent a health score by combining parsing, model confidence, and evaluator scores.

### Empty and error states

No corpus: explain that reports must be registered through the corpus workflow. Provider unavailable: retain document inspection and display the unavailable next step. Job failures link to a recoverable detail view.

## 2. Documents

### List columns

Issuer; report title; source period label if human catalog metadata exists; development/holdout split; original PDF pages; parse coverage; download status; parse status; latest run; action.

Catalog metadata is not an extracted semantic answer. Label it as report metadata and keep it out of automatic expected-value prefilling.

### Document detail

Tabs: Source, Parse, Runs.

- Source: original publisher link, SHA-256, download timestamp, byte size, physical pages, source availability, selected page coverage.
- Parse: Docling version/settings, parse warnings, tables/text items, source page preview.
- Runs: immutable initial/revised/manual versions, model/policy versions, feedback links.

### Actions

- Open original PDF.
- Parse or retry a failed parse, creating a durable job.
- Run extraction after a usable parse exists.
- Open Evidence Grid for a chosen run.

Initial app uses a curated corpus. No arbitrary URL field or public file-upload flow is required. If a source is unavailable, show its reason and keep the failure in the registry.

### States

Downloading/queued/running/parsed/partial/failed are visibly different. A partial parse shows exact missing coverage. Never offer “Run extraction” on nonexistent evidence without a clear failure result.

## 3. Evidence Grid — primary screen

### Text wireframe

```text
EvidenceGrid   / Evidence Grid
Document: [Telkom 9M 2025 v]   Run: [Initial extraction v]   [Export]

Issuer [All v]  Metric [All v]  Period [All v]  Checks [All v]

Metric             Reported amount  Original unit  Reporting period    Checks
Revenue            ...              IDR billion    Jan-Sep 2025 / 9M   Review
Operating profit   ...              IDR billion    Jan-Sep 2025 / 9M   Pass
Owner profit       ...              IDR billion    Jan-Sep 2025 / 9M   Unknown

Selected fact                                Source evidence
Original amount: ...                         [PDF page with highlights]
Normalized amount: ...
Period: ...                                  Value / Metric / Period / Unit
Checks: ...                                  [Open full page]
Version history: ...
```

Ellipses are wireframe placeholders, not seeded production data. Actual rows come from stored run artifacts.

### Required columns

Issuer; metric; original amount; original currency/scale; normalized amount; interval label; duration; physical source page; check summary; version origin.

Default display may use IDR billions for readability, but name the display unit explicitly. Show the original printed number/scale on selection. Never mix raw millions and raw billions under one unqualified column.

### Selecting a row

Open a persistent detail panel rather than navigating away from the selected context. Show:

1. Metric definition and original source label.
2. Original text, parsed Decimal, scale multiplier, and normalized result.
3. Period start/end/duration and the source heading.
4. Each deterministic check with pass/fail/unknown/not-applicable status.
5. Source PDF page and original Docling coordinates.
6. Tabs or highlight toggles for Value, Metric, Period, Unit.
7. Initial/revised field diff and supporting evidence for each change.
8. Real Reppo critique, when available, with its separate evaluator score.

Highlight both the number and the contextual heading; a highlight of only the number cannot establish whether it is annual or nine-month.

### Comparisons

Allow selection of compatible facts. If duration, scope, or currency differs, show the incompatibility and disable unqualified growth calculation. Do not silently annualize. Unit normalization is allowed when supported.

### Status vocabulary

- “Checks passed” means the applicable source-fidelity checks passed.
- “Needs review” means a concrete discrepancy is present.
- “Source context missing” means a check is unknown.
- “Reppo: 78/100” is a separate evaluator field, never “78% accurate.”
- “Human reviewed” is separate from automated origin and benchmark correctness.

Avoid one blanket “Verified” badge that hides what was checked.

## 4. Review Queue

### Purpose

Prioritize specific discrepancies, not every fact indiscriminately.

### List content

Issue type; issuer/document; metric; short reason; original versus source-supported reading; source page; run/version; age/status.

Issue types include period duration mismatch, comparative-year mismatch, unit scale mismatch, ambiguous locale, unsupported metric, currency conflict, and missing source context.

### Detail actions

- Inspect evidence.
- Open related feedback session.
- Request a bounded SERV investigation/revision when real feedback requirements are met.
- Create a manual correction with reason and citation.
- Mark the issue reviewed without pretending the underlying fact is correct.

Manual changes create a manual fork and are excluded from automated benchmark results. Never put a “Mark correct” button that silently edits gold labels.

## 5. Feedback

### Session list

Document/run/version; mode; submitted time; provider status; earliest settlement time; overall verdict if settled; revision status.

### Detail layout

- Submitted artifact: exact facts, criteria, source excerpts, and packet hash.
- Evaluation: pending timeline or returned criterion critiques, overall score/decision/confidence, evidence basis, contributor counts as actually returned.
- Revision: proposed changes, accepted/rejected edits, unresolved items, before/after source support.

### Actions

- “Submit to Reppo” only when prerequisites and budget permit.
- “Refresh status” schedules/read-refreshes an existing evaluation; it does not resubmit.
- “Revise with SERV” only for settled real feedback linked to the selected version.
- “Evaluate revised version” only if budget remains.

### Long-running states

Explain “Awaiting Reppo settlement” and show the earliest eligible time plus latest successful poll. The user can leave and return. Do not display a fake percentage-progress bar for external judging.

### Sandbox state

Use “Sandbox contract test — no judge ran.” Show the placeholder response for inspection. Disable the normal feedback-improvement action. Do not include sandbox scores in benchmark charts or sponsor-integration counts.

### Failures

Handle missing key, unauthorized, insufficient credits, account in-flight conflict, denied/failed result, overdue pending result, unknown submission outcome, and unknown provider status separately. “Try again” must not blindly create a duplicate paid evaluation.

## 6. Benchmark

### Initial state

“No measured results yet.” Describe the next required step and show freeze readiness. Never seed 70% or 90% as illustrative chart values in the production UI.

### Result layout

- Run ID, source/label/policy hashes, split, number of documents and target facts.
- Baseline versus feedback-assisted strict semantic correctness, as counts and percentages.
- Period correctness, unit correctness, numeric correctness, evidence correctness, and coverage.
- Improvement and regression counts.
- Per-document breakdown.
- Cost/usage and wall-clock time, including external settlement waits.
- Clear separation of development, holdout, post-inspection, manual, controlled-test, and sandbox records.

### Interactions

Click a result to see target/prediction comparison in the benchmark context after scoring. Normal extraction tools never receive these labels. Record when holdout outcomes are inspected. Download a reproducibility report.

No leaderboard, winning probability, generic confidence gauge, or fabricated statistical significance is needed.

## 7. Exports

### Export types

- Analyst CSV: facts with explicit units/periods/source references.
- Reproducibility JSON: exact versions, checks, evidence links, and feedback metadata.
- Markdown summary: readable findings, limitations, and measured results when available.

### Actions and states

Choose a run/version and export type. Preview coverage and unresolved counts. Generate through a durable job if needed, then download a named immutable artifact. Show no-results, generating, ready, failed, and expired/missing-artifact states.

Do not export hidden labels in ordinary analyst bundles. Provider secrets and private account metadata are excluded.

## 8. Settings

### Content

- SERV configured/unconfigured, base URL, current model, last verified request time.
- Reppo configured/unconfigured, endpoint, last verified real evaluation, pending count.
- Run limits: revision calls, extra context retrievals, evaluations per run, polling deadline.
- Corpus/policy versions and local storage status.
- Optional system/dark/light theme preference.

### Rules

Configure secrets through the server environment or ignored local .env, not a browser storage field. Provider status is based on real evidence; a configured key is not the same as a verified live integration. A connectivity test must explain whether it makes a billable request.

Changing settings creates a version for future runs. Existing runs retain their original settings and evidence.

## Shared accessibility and responsiveness

- Use real links/buttons with keyboard operation and visible focus.
- All controls have accessible names. Table headers are semantic and reading order is logical.
- Status uses text/icons in addition to color.
- Touch targets are at least 40px; density must not make review controls unusable.
- Loading uses meaningful skeleton/text states; errors provide a recovery action.
- Respect reduced motion. Avoid decorative agent animations.
- Desktop supports a grid and evidence panel; tablet can use tabs; mobile opens source detail as a full-screen view with a clear return action.
- Test 375px, 768px, and 1280px layouts.

## Dashboard acceptance criteria

Every navigation item opens a functional route. Counts come from actual stored state. A selected fact can reach its original value and governing period/unit evidence. Pending feedback survives a reload. Baseline and revised outputs remain separate. A missing key or empty benchmark displays an honest, actionable state. No frontend screen claims a capability absent from the backend.
