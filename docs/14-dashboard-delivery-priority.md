# 14 — Focused dashboard delivery and frontend rationale

Decision date: November 15, 2026.

This is an English specification for Claude Code, not a frontend implementation. It refines the existing dashboard brief for the agreed period-and-unit verification product. Preserve any implementation the user has already built elsewhere; inspect its state before making changes.

## Priority over the earlier navigation plan

For the hackathon delivery, this document takes precedence over the eight-item sidebar in docs/09-dashboard-spec.md and the broad navigation requirement in Phase 7 of docs/11-implementation-plan.md. The detailed behaviors and evidence rules in those files still apply.

Use four main menus: **Workspace, Documents, Feedback, Benchmark**. Put review issues inside Workspace, exports in contextual actions, settings in a small configuration panel, and overview information in compact headers. No user workflow from the earlier brief needs to become a separate page solely to fill a navigation menu.

The corpus, metrics, verification mechanism, provider roles, benchmark protocol, and exclusion of restatement propagation remain unchanged.

## Is a frontend necessary?

### Official requirement versus product recommendation

The current event page requires SERV Reasoning, a public repository, demo link or video, a short write-up, and an X submission post. It does not explicitly require a browser frontend. Published judging dimensions include creativity, user readiness, and revenue potential.

Source checked November 15: [Edition 02 rules](https://www.openserv.ai/hackathon-2).

For EvidenceGrid, a compact frontend is recommended because the user needs to inspect a number alongside the PDF heading and unit statement that govern its meaning. A CLI remains useful for reproducibility, but a judge should be able to inspect one result without setting up the entire Python environment.

This is a workflow-based recommendation, not an organizer requirement or a prediction of an award.

### What previous winner artifacts actually show

| Project | Award evidence | Interface evidence | Useful lesson and limit |
| --- | --- | --- | --- |
| ASSAY | Organizer confirms Best Overall and Open Track | Pre-deadline demo instructions open the landing page and findings wall alongside terminal and chain evidence | A browser can make a concrete finding inspectable; the award does not prove interface polish caused the result |
| Payrun | Organizer confirms AgentKit track winner | Pre-deadline repository describes an application with recorded demo responses and source-linked decision evidence | A reviewer can inspect completed work without spending credits; recorded work must be labeled and cannot impersonate a fresh live run |

Sources:

- [Organizer-confirmed Edition 01 awards](https://www.openserv.ai/hackathon).
- [ASSAY demo plan at pre-deadline revision](https://github.com/OoJae/assay/blob/256aa19a79d420f96de492a3a885da65e57ccc68/docs/DEMO.md).
- [Payrun README at pre-deadline revision](https://github.com/nice-bills/payrun/blob/204056d7cbd2ed0b0e175b7c2be795644a554ddf/README.md).

These are inspected public artifacts, not independently rerun winner applications. A live request to ASSAY's website was unavailable during this check. Do not claim that every winner had the same UI structure or that number of pages correlates with winning.

## The single dashboard promise

**Select a financial number, see whether its reporting period and monetary unit match the PDF, inspect any correction, and export the evidence-backed result.**

Keep every visible feature tied to that task. A dashboard with decorative metrics cannot replace actual Docling provenance, real SERV output, a traceable Reppo critique, and an honest benchmark.

## Four-menu information architecture

| Menu | Route | Contents | Primary action |
| --- | --- | --- | --- |
| Workspace | `/` | Evidence Grid, source viewer, discrepancies, before/after comparison | Inspect evidence and review a selected fact |
| Documents | `/documents` | Curated reports, original source, parse coverage, extraction runs | Parse or extract a selected report |
| Feedback | `/feedback` | Real Reppo sessions, critiques, revision attempts and status | Read feedback and run a bounded SERV revision |
| Benchmark | `/benchmark` | Frozen baseline versus revised measurements and reproducibility artifacts | Inspect actual counts and errors |

Settings opens from the header as a panel. Export appears on Workspace and benchmark results. A review-issues filter belongs in Workspace. No separate Overview, Review Queue, Exports, or Settings navigation entry is required for this delivery.

## Workspace — the main screen

### Layout

Use a table-first analyst workspace with a source panel. On desktop, the table occupies approximately three-fifths of the main area and source evidence occupies the rest. On smaller screens, switch between Facts and Source tabs while preserving the selected fact.

```text
EvidenceGrid                         [Recorded run / Live run] [Settings]
Workspace | Documents | Feedback | Benchmark

Document [Select report]  Run [Select run]  Version [Initial / Revised]
[Run extraction] [Check period & unit] [Export CSV]

Showing: [All facts / Needs review]        Metric [All]

Facts                                        Source PDF
Metric | Amount | Unit | Period | Checks      [Page number / Open original]
Revenue | ... | IDR bn | Jan-Sep / 9M | Fail  [Highlight value]
...                                          [Highlight period heading]
                                             [Highlight unit statement]

Selected fact
Initial -> Revised | What changed | Source evidence | Remaining uncertainty
```

The wireframe is structural only. Ellipses are placeholders; do not seed fictional production rows or benchmark percentages.

### Feature 1 — Evidence-linked fact grid

Display issuer, requested metric, original amount, original currency/scale, explicit reporting interval and duration, normalized amount, and check summary. Support only the three agreed metrics. If normalized display uses IDR billions, label that column and retain the original printed scale on selection.

Selecting a row opens the corresponding source page and detail panel. It does not trigger an external paid call.

### Feature 2 — Period mismatch detection

Show an issue such as: "Candidate: full year. Source: nine months ended September 30."

Display exact start/end dates, duration, and the applicable source column. A publication year or balance-sheet date cannot establish an income interval. Distinguish comparative years and quarterly versus year-to-date columns.

Never annualize an interim value to resolve a mismatch. If the source remains ambiguous, show "Period unresolved" with its reason.

### Feature 3 — Unit mismatch detection

Show original printed amount, applicable currency/scale statement, scale multiplier, and canonical amount calculated by deterministic Decimal arithmetic.

An issue might say: "Candidate scale: billion. Source unit: million." Use synthetic numbers only in an explicitly labeled controlled example; real report rows must come from actual stored outputs.

Unknown scale or ambiguous number separators remain visible. A failed lookup does not become a passed check.

### Feature 4 — Source evidence viewer

Support four evidence selections: Value, Metric, Period, Unit. Highlight both the amount and the governing contextual text. Display physical PDF page number; keep any printed page label separate. Provide a link to the original publisher source.

Use Docling coordinates and document identity. If coordinates are missing, show text evidence and an explicit limitation; do not invent bounding boxes. Opening one original page beside the table is sufficient for the first functional UI; a sophisticated annotation editor is out of scope.

### Feature 5 — Initial/revised comparison

Show the original and revised field values, supporting evidence, revision time, and origin. Mark whether the change came from SERV or a manual fork. Preserve both immutable versions.

Use field-specific statuses such as "Period mismatch," "Unit checks passed," and "Source context missing." Do not combine provider confidence, passing checks, and actual correctness into one opaque verification score.

### Feature 6 — Export usable results

Export the selected run/version as CSV and JSON. Include metric, original amount/scale, normalized amount, interval, duration, issuer, original URL, source page, source hash, version, origin, and unresolved status.

CSV export should contain all selected facts, including unresolved ones, with explicit missing fields. Do not hide failures to make the export appear complete. Never include credentials or hidden reference labels.

### Button behavior

| Action | Behavior |
| --- | --- |
| Run extraction | Enqueue a real SERV extraction for an existing parsed report; record its model/policy and actual response |
| Check period & unit | Run deterministic source checks on the selected stored fact version; label unknown checks explicitly |
| Open feedback | Navigate to the feedback associated with this exact immutable version |
| Revise with SERV | Available from settled real Reppo feedback; enqueue the bounded revision and preserve the parent |
| Export CSV / JSON | Download selected stored version with provenance; no new model call |

Do not call an action "Run verification" if it silently performs several paid requests. Show the intended provider, budget, and asynchronous state where external evaluation is requested.

## Documents — input readiness

Use the curated 4–6-report corpus. Show report title, issuer, source link, source hash, physical page count, chosen parse coverage, status, and latest real run. Allow Parse, Retry parse, Run extraction, and Open in Workspace as appropriate.

Keep original PDFs and parsed output distinct. A successful download is not a successful parse. A successful parse is not a correct semantic extraction.

No drag-and-drop arbitrary PDF upload is needed for the submission. Prioritize a reliable, inspectable selected report over generalized ingestion.

## Feedback — sponsor mechanism made inspectable

Show the submitted fact version, source evidence packet, criteria, real external evaluation ID, status, relevant critiques, score/decision/confidence as returned, and revision lineage.

A score of 90/100 is a Reppo judgment, not 90% measured extraction accuracy. Display it separately from the benchmark.

Pending evaluation: show the earliest settlement time, latest status check, and "Awaiting Reppo settlement." The user may navigate away and return. Refresh reads the existing ID; it does not create another evaluation.

Revision result: show each accepted, rejected, and unresolved proposal. A critique must be checked against the PDF. Do not change an otherwise correct nine-month value simply because a reviewer asks for annual data.

Missing key, insufficient credit, failed result, and unknown submission outcome each get a distinct actionable state. Do not silently replace real evaluation with a sandbox score.

## Benchmark — proof of the improvement claim

Display only stored measured results. Required fields: corpus/split, document count, target count, label provenance, source/policy/scorer versions, baseline correct/total, revised correct/total, percentage-point change, period correctness, unit correctness, coverage, improvements, regressions, and elapsed/usage information.

If no run exists, show "No measured benchmark yet." If the revision regressed, show it. Keep development, holdout, post-inspection, manual, controlled-corruption, and sandbox artifacts separate.

The full evaluation protocol in docs/08-evaluation-protocol.md still governs. A chart alone does not establish a fair baseline or a held-out result.

## Live versus recorded demonstration

Offer a deterministic, read-only recorded-run view if real artifacts are available. It must show "Recorded run," original timestamps, source identity, and real provider/evaluation metadata. It can let judges inspect evidence without keys or new charges.

Offer fresh execution only when the backend/provider is configured and the intended operation is permitted. Display pending jobs honestly. Do not animate a recorded response as a fresh model call.

Standard Reppo evaluations are asynchronous. The demo can inspect a previously settled real evaluation while a new run remains pending; label those as separate runs. A static frontend cannot execute Docling or a Python worker by itself.

## Delivery sequence and cut line

1. Connect one real report and stored fact version to Workspace.
2. Make clicking a fact reveal its actual amount, period heading, and unit evidence.
3. Connect deterministic checks and initial/revised differences.
4. Expose real Reppo feedback and the bounded revision lineage.
5. Export the result and show the measured benchmark artifact.
6. Finish Documents, empty/error states, keyboard access, and layout responsiveness.

If time is tight, combine all four views as tabs in one page; keep their functions accessible. Reuse an existing frontend if one exists. Do not start a new framework migration for visual polish near the deadline.

Do not cut the real mechanism in order to finish a landing page. Cut animated charts, extra overview cards, a separate exports page, an elaborate settings system, custom annotation editing, authentication/team features, arbitrary uploads, and decorative agent traces first.

## Acceptance walkthrough

A reviewer can:

1. Open the main screen and identify the concrete period/unit problem.
2. Select one stored report and fact without entering an API key.
3. Inspect the exact amount and governing source context.
4. See an initial/revised difference or an honestly reported unresolved/no-change result.
5. Inspect the actual Reppo critique used by the revision.
6. Read measured counts with a visible denominator and split.
7. Export the versioned fact with period, unit, and source provenance.

If any item is unavailable, show the limitation rather than a clickable placeholder. Real source-backed results and a concise unaided judging path are the priority; frontend presence alone is not evidence of an award-winning product.

## Prompt to give Claude Code

```text
Read CLAUDE.md, docs/09-dashboard-spec.md, and docs/14-dashboard-delivery-priority.md.
Inspect the current application and preserve working code.
Build a compact English frontend around the actual EvidenceGrid backend and stored run artifacts.
Use four main views: Workspace, Documents, Feedback, Benchmark.
Treat document 14 as the priority override for navigation, while keeping the evidence rules in the full handoff.
Workspace must show the financial grid beside original PDF evidence for value, metric, period, and unit.
Include period/unit issues, immutable initial/revised differences, real Reppo critiques and asynchronous status, and CSV/JSON export.
Use existing measured benchmark outputs; never invent percentages or treat a Reppo score as accuracy.
Label recorded real runs, fresh live calls, controlled examples, and sandbox placeholders separately.
Do not implement restatement propagation, a general PDF chatbot, extra metrics, or decorative analytics.
Connect real behavior before polishing. Verify one complete source-to-fact-to-feedback-to-export journey and all honest empty/error/pending states.
If no application backend exists yet, implement the agreed core slice first rather than presenting invented UI data as working functionality.
```
