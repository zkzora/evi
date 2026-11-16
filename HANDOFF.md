# EvidenceGrid — Claude Code handoff

> Documentation package only. Application implementation is intentionally paused. All product copy, code identifiers, documentation, evaluation criteria, and demo material must be in English.

EvidenceGrid turns public telecom reports into a small evidence-linked financial grid. Its original contribution is interpreting and checking **reporting periods and monetary units** on top of Docling, then using SERV Reasoning and Reppo feedback to revise extraction results. Docling is a dependency, not a competitor or an original contribution.

## Start here

Give Claude Code this instruction:

```text
Read CLAUDE.md and all documents linked from README.md before implementation.
Build EvidenceGrid according to this handoff, starting with the real document-to-evidence slice.
Use Docling for parsing, SERV Reasoning for semantic extraction and revision, and Reppo for evaluation feedback.
Follow the phase order in docs/11-implementation-plan.md. Build the dashboard from docs/09-dashboard-spec.md only after the core slice works.
Keep all UI and documentation in English. Do not implement restatement propagation.
Do not invent benchmark results, represent sandbox feedback as real judgments, or silently substitute a different provider.
Continue all independent work if API credentials are unavailable, and report exactly which live steps remain unverified.
```

## Reading order and document map

| File | Purpose |
| --- | --- |
| [CLAUDE.md](CLAUDE.md) | Agent working contract, scope, non-negotiable evidence rules |
| [01 — Product scope](docs/01-product-scope.md) | User, failure, solution, competitive baseline, bounded scope |
| [02 — End-to-end workflows](docs/02-end-to-end-workflows.md) | Complete user and agent flows, transitions, recovery |
| [03 — Architecture](docs/03-system-architecture.md) | Services, worker, storage, trust boundaries, proposed repository |
| [04 — Data contracts](docs/04-data-contracts.md) | Documents, cells, facts, checks, revisions, feedback, runs |
| [05 — Verification engine](docs/05-verification-engine.md) | Detailed period/unit rules and evidence checks |
| [06 — SERV agent](docs/06-serv-agent.md) | Extraction, investigation, revision, prompts and boundaries |
| [07 — Reppo loop](docs/07-reppo-feedback-loop.md) | Real API contract, asynchronous jobs, feedback use, sandbox limits |
| [08 — Evaluation protocol](docs/08-evaluation-protocol.md) | Gold labels, splits, fair before/after measurement, leakage controls |
| [09 — Dashboard](docs/09-dashboard-spec.md) | Main menus, routes, screen behavior, text wireframes, all states; no frontend code |
| [10 — API and jobs](docs/10-api-and-jobs.md) | Backend endpoints, durable jobs, errors, idempotency |
| [11 — Implementation plan](docs/11-implementation-plan.md) | Dependency-ordered tasks, meaningful tests, completion gates |
| [12 — Demo and submission](docs/12-demo-and-submission.md) | Demo script, evidence bundle, hackathon checklist, claim boundaries |
| [13 — Research and current state](docs/13-research-and-current-state.md) | Source ledger, inspected environment, actual files, known unknowns |

## Locked decisions

- Event: SERV Hackathon Edition 02; intended track: Reppo.
- Audience: analysts collecting comparable financial figures from public reports.
- Sector: Indonesian telecommunications.
- Corpus: **4 reports initially; at most 6**. Freeze exact sources and splits before tuning.
- Metrics: consolidated revenue, operating profit, profit attributable to owners of the parent.
- Core failure: a nine-month number presented as a full-year number; a million/billion scale misinterpreted.
- Core output: a fact grid with source evidence, explicit period and unit, revision history, and measured before/after results.
- Restatement propagation: explanation and roadmap only, not implementation.
- No assumed accuracy uplift: “70% to 90%” is an illustration, not a result or acceptance requirement.
- Initial delivery: a complete locally runnable app and reproducible evidence. A public deployment is a later environment-specific task, not a claim this handoff has completed.

## Current status

Only research, environment preparation, two source PDF downloads, and this handoff exist. There is no application, parsed corpus, gold dataset, live SERV run, real Reppo verdict, or measured benchmark yet. See the current-state ledger before reusing anything.

## Completion definition

The project is complete when an analyst can select a real report, inspect extracted facts and their source regions, see period/unit discrepancies, obtain a real Reppo evaluation, execute a bounded SERV revision, compare immutable versions, and export results. A separate benchmark must score baseline and revised outputs against pre-frozen human labels without exposing those labels to the agents.

If credentials or external access prevent live completion, deliver the working independent components and identify the precise remaining dependency. Never relabel partial evidence as complete.


## Latest frontend instruction — November 15, 2026

The user has asked Codex to build the frontend directly in this directory after approval of a web-reference design direction. Read [14 — Dashboard priority](docs/14-dashboard-delivery-priority.md) and [15 — Web references and design choice](docs/15-web-references-and-design-choice.md). The four-view layout supersedes the older eight-item sidebar. The frontend-first user instruction supersedes the earlier backend-first gate for this UI task. Design approval is pending; no frontend has been implemented in this step.
