# 15 — Web references and approved frontend design

Prepared November 15, 2026. Status: **direction A approved by the user; product renamed Evi**.

## Current instruction and working directory

The user now wants Codex to implement the frontend and dashboard directly in:

```text
C:\Evidence\EvidenceGrid-Claude-Code-Handoff
```

The user explicitly requested web-reference research first, followed by approval of the selected direction before implementation. Do not treat a suggested or preselected design as approval. That research step is complete; the Evi frontend is now implemented.

This instruction supersedes the earlier Claude-Code-only handoff and frontend-after-backend sequencing for this frontend task. After the user selects a direction, implement the frontend in this directory, preserving the documentation. The user subsequently rejected demo mode. If the backend is absent, keep real source PDFs readable, leave results empty, and explain unavailable provider actions. Do not add illustrative financial fixtures or simulated provider results.

Do not build the full document-processing backend simply to satisfy an old sequencing note when the current request is specifically the frontend. Separate real UI interactions, local fixture behavior, and unavailable backend integrations in the delivery report.

## Research sources

Only public first-party pages were used for the reference shortlist. These products are references for interface patterns; the project does not need to purchase, embed, or integrate them.

| Reference | Inspected source | Pattern relevant to EvidenceGrid |
| --- | --- | --- |
| Rossum | [Validation-screen product update](https://updates.rossum.ai/en/a-new-validation-screen-for-a-more-intuitive-experience) | Connect extracted fields, field-level errors, document bounding boxes, and review state |
| Hex | [Table-display documentation](https://learn.hex.tech/docs/explore-data/cells/visualization-cells/table-display-cells) | Format financial columns, sort/filter data, control display density, and distinguish display formatting from underlying values |
| Linear | [Display options](https://linear.app/docs/display-options) and [product overview](https://linear.app/features) | Compact navigation, focused lists, visible filters, ordering/grouping, and restrained application chrome |

The Rossum reference is a dated product update containing example imagery, not a claim about every detail of its current interface. A separate Rossum getting-started page redirected and could not be opened fully. The Hex `/product/` route returned 404; its root site and table-display documentation were accessible. No logged-in customer applications were inspected.

Palette, layout proportions, and typography below are **proposed EvidenceGrid design decisions**, not exact copies of these products or claims about their current brand tokens.

## Option A — Light evidence-review workspace (recommended)

References: Rossum review workflow + Hex table organization.

### Appearance

- Light off-white application background and white work surfaces.
- Restrained navy/blue accent for selection and primary actions.
- Dark readable text, subtle dividers, small-radius controls.
- Amber/red issue labels with text; green checks only when the relevant check actually passed.
- Clean sans-serif UI; tabular numerals for amounts and dates.
- Original PDF stays on white paper with a neutral surrounding canvas.

### Layout

- Narrow sidebar with four main destinations: Workspace, Documents, Feedback, Benchmark.
- Compact header for report, run, and immutable version selection.
- Workspace divided between a financial grid and original source evidence.
- Selected fact details expand beside/below the source without losing the selected row.
- Relevant evidence tabs: Value, Metric, Period, Unit.
- Initial/revised field differences use a small comparison block, not a separate dashboard of charts.

### Why this fits

The document remains readable next to structured financial data. The central nine-month-versus-annual discrepancy can be understood in one view. Review status can be explicit without turning the interface into a trading terminal.

### Tradeoff

Less dramatic than a dark console; visual quality must come from typography, alignment, selection behavior, and source evidence rather than gradients.

## Option B — Dark compact workspace

Reference: Linear navigation and dense list organization, adapted to financial facts.

### Appearance and layout

- Graphite surfaces, subdued borders, restrained indigo accent.
- Compact row spacing and high-contrast selection.
- Persistent sidebar and minimal top toolbar.
- White original PDF sheet inside a dark evidence panel.
- Strong keyboard navigation and visible run/status badges.

### Why someone would choose it

It can make a dense tool feel focused and works well for comparing run history, issue lists, and revisions.

### Tradeoff

The bright PDF creates a strong contrast transition inside the dark workspace. The implementation must handle document readability and status contrast carefully. Do not add terminal-like animation or imply that extra visual complexity creates technical depth.

## Option C — Analyst table with document drawer

Reference: Hex table interactions, adapted to a small analyst workspace.

### Appearance and layout

- Light neutral palette with one subdued teal accent.
- The fact table occupies the main screen width.
- Sticky headers and explicit original/display units.
- A source drawer opens when a row is selected.
- Before/after is a table toggle; original and revised data remain immutable.

### Why someone would choose it

It prioritizes quick scanning across issuers and periods. Most space is dedicated to data rather than an always-open source page.

### Tradeoff

The PDF is less prominent until a fact is selected, so the core source-verification mechanism may be less immediately obvious in the opening demo frame.

## Common approved product scope, independent of visual choice

The design choice changes presentation, not the product's financial definitions or evidence rules.

1. **Workspace:** three-metric grid, period/unit diagnostics, source evidence, initial/revised differences, CSV/JSON export.
2. **Documents:** curated report list, original source identity, page/parse coverage, run readiness.
3. **Feedback:** live evaluation records and explicit pending/failure states, external-evaluation status, critiques, revision lineage.
4. **Benchmark:** actual measured counts and denominators when available; otherwise an honest empty state.

Review issues are filters/details in Workspace. Settings is a small header panel. Exports are contextual actions. Keep four primary navigation entries rather than the older eight-page list.

## Intended frontend behavior after approval

- Navigation changes actual views and preserves useful URL context.
- Row selection opens its corresponding evidence.
- Metric/status/document filters change the visible fact set.
- Initial/revised selection changes the displayed stored version without rewriting its parent.
- Evidence tabs identify which source statement supports the selected field.
- CSV/JSON exports reflect the currently selected stored live version and explicitly preserve its provenance mode.
- Unavailable live operations explain that the backend or credentials are not connected; do not simulate a paid provider success.
- Benchmark never displays invented uplift percentages.
- Empty, loading, failed, unknown, and pending states are distinct.
- Keyboard focus, responsive layout, and readable contrast are required.

## Recorded decision

The user explicitly selected A. The implemented frontend follows that direction and uses the Evi name and original Evi logo.


## Approved implementation scope

The user selected A and renamed the product Evi. The latest instruction is to implement the website/frontend here; Claude Code will implement the server, provider credentials, and end-to-end system. The user explicitly rejected demo mode. No synthetic results or simulated provider calls are permitted in the application. PDF source metadata is real; all extraction/evaluation/benchmark data must come from the live API. Reviewers must not face a login wall. See document 16 for the exact implemented frontend contract.

