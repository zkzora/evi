# 11 — Implementation plan for Claude Code

## Execution policy

Build a working vertical slice before broadening the UI. Follow the locked scope and use the actual repository state. This plan does not require asking permission for routine reversible implementation decisions already authorized by the user. Ask only for genuinely missing information or access, and continue independent work.

Do not implement application code until the user starts the separate Claude Code build. This handoff itself is Markdown documentation only.

## Phase 0 — Inspect, bootstrap, and record decisions

Tasks:

- Read this handoff and applicable AGENTS.md instructions.
- Inspect existing files; preserve the two downloaded PDFs.
- Confirm Python/Docling versions and runtime imports. The prepared venv used system site packages, so a portable lockfile still needs to be created and tested.
- Create pyproject.toml, an appropriate lockfile, .gitignore, a safe .env.example, and documented local commands.
- Select concrete model/settings from current official SERV docs.
- Document the architecture and any necessary deviations in docs/DECISIONS.md.
- Check API-key presence without exposing values. Missing credentials are explicit prerequisites for live phases, not an excuse to stop local work.

Deliverable: reproducible environment and skeleton domain/API/worker entry points.

Gate: clean setup/import smoke check, safe secret handling, and a written actual-state note. No claimed extraction results yet.

## Phase 1 — Curate the small corpus

Tasks:

- Use the two downloaded originals as candidate sources, not verified fact datasets.
- Locate and download their annual counterparts from official publisher URLs where available.
- Prefer four reports total: Telkom annual/interim for development, XL annual/interim for holdout. Verify the exact metric availability before freezing this choice.
- If a source is unavailable or cannot support a requested metric, choose another public report in the same sector before freezing; stay at 4–6 reports.
- Register URL, bytes/hash, source title, physical page count, page coverage, and split.
- Render the relevant statement pages and confirm the number, metric label, period, unit, and comparative columns visually.
- Create source-reviewed human labels independently from model predictions.
- Freeze eligibility, targets, labels, and hashes. Record annotation limitations.

Deliverable: corpus manifest, source ledger, rendered source evidence, and frozen label set.

Gate: source-supported current/comparative targets exist for the three metrics. Unknowns and exclusions are explicit. Gold values are outside inference packets.

## Phase 2 — Real Docling parsing and provenance

Tasks:

- Convert selected relevant pages from one real PDF using Docling.
- Preserve raw JSON, actual parser settings/version, table structure, and coordinates.
- Build evidence cells and context windows from value, row label, merged headers, caption, period, and unit statement.
- Maintain physical page numbers despite partial-page-range parsing.
- Produce source preview assets/highlight coordinates for the future dashboard.
- Cache by complete source/parser/settings/coverage identity.

Deliverable: one real PDF -> raw Docling artifact -> source-linked evidence packet.

Gate: a developer can inspect a real number and its governing period/unit context. If Docling loses a required header, document the issue and recover context from its text items; do not invent a hidden custom parser or prefill source labels as an extraction result.

## Phase 3 — Deterministic domain engine

Tasks:

- Implement typed contracts from docs/04-data-contracts.md.
- Implement Decimal numeric interpretation, currency/scale association, interval validation, evidence membership, and comparison compatibility.
- Preserve explicit unknowns and check statuses.
- Implement immutable initial/revision/manual version storage and field diffs.
- Add the controlled mechanism suite, clearly separated from natural extraction evaluation.

Deliverable: candidate facts can be checked, normalized, versioned, and exported independently of the UI.

Gate: positive controls pass; wrong duration/scale/column/anchor cases fail or remain unknown appropriately. Legitimate interim values remain interim; a system that rejects everything does not pass.

## Phase 4 — Real SERV one-shot extraction

Tasks:

- Implement actual SERV transport and validated structured outputs.
- Build a competent baseline prompt using the complete initial evidence packet.
- Persist request/response artifacts, model/prompt hashes, provider request IDs when returned, finish reasons, latency, and usage.
- Produce a real extraction for a development report.
- Feed the result through deterministic checks and show a useful CLI/API summary.

Deliverable: source PDF -> Docling -> live SERV -> typed facts -> checks.

Gate: at least one real provider response is linked to real source evidence. Errors are visible. No silent fixture output when a key is missing.

If key is absent: finish transport contract tests and the rest of the independent app; identify this gate as pending real verification.

## Phase 5 — Real Reppo feedback and bounded revision

Tasks:

- Implement API-key submit/read, byte-aware packet limits, required criteria, durable IDs, polling, budgets, and in-flight serialization.
- Test the transport shape with fixtures and optionally the clearly labeled official sandbox.
- Submit one actual development artifact using the configured account.
- Wait asynchronously for its real result; preserve failed/denied/missed critiques honestly.
- Send settled critique to SERV along with source evidence and diagnostics.
- Validate, recheck, and store the resulting revision, including unsupported/rejected proposals.
- Demonstrate restart/resumption without duplicate submission.

Deliverable: real feedback -> actual revision attempt -> source-checked child version.

Gate: the exact real critique is traceable to changes or an explicit justified no-change result. A sandbox placeholder does not pass this gate. Improvement is not assumed.

## Phase 6 — Evaluation harness and frozen holdout run

Tasks:

- Implement strict target-based scoring and missing-target denominators.
- Verify scorer behavior with hand-derived positive, wrong-period, wrong-scale, missing, duplicate-target, and regression cases.
- Complete development tuning without inspecting holdout outcomes.
- Freeze extraction/revision policy, model, budgets, parser config, target manifest, and scorer.
- Run baseline and predefined feedback-assisted inference on holdout documents without labels.
- Freeze outputs, then score.
- Publish counts, percentages, per-document results, regressions, coverage, costs/usage, and timing.

Deliverable: reproducible measured report with evidence artifacts.

Gate: results are numerically correct and honestly reported even when uplift is zero or negative. “70% to 90%” is not a gate.

## Phase 7 — Dashboard implementation

Tasks:

- Implement the eight main menus in docs/09-dashboard-spec.md.
- Build the Evidence Grid and source detail panel first, then Documents and Feedback; wire them to actual backend state.
- Add Review Queue, Benchmark, Exports, Overview, and Settings using the same data contracts.
- Cover empty/loading/error/pending/partial/unknown states.
- Keep API keys server-side. Preserve run/version context in routes.
- Add responsive layouts and keyboard/focus accessibility.

Deliverable: a functional analyst workflow, not a visual mockup.

Gate: selecting a fact opens both its amount and applicable period/unit evidence; real feedback can be resumed after reload; absent results are never replaced by decorative metrics.

## Phase 8 — Exports, operations, and submission evidence

Tasks:

- Implement CSV/JSON/Markdown exports with source/version provenance.
- Document API/worker startup, configuration, source acquisition, parsing, live runs, polling, benchmark commands, and common errors.
- Test a fresh restart using stored artifacts and existing pending jobs.
- Prepare a concise English demo narrative and evidence bundle from actual outputs.
- Prepare submission copy; clearly separate completed work, real integrations, recorded replay, and outstanding verification.

Deliverable: runnable local product plus reproducible handoff and submission materials.

Gate: a new reviewer can follow documented commands, inspect the central result, and identify all limits without reading the entire repository.

## Proposed CLI surface

These are future command contracts, not commands that already work:

```text
evidencegrid corpus validate
evidencegrid corpus fetch <document-id>
evidencegrid parse <document-id>
evidencegrid extract <document-id> --policy <version>
evidencegrid evaluate <version-id>
evidencegrid evaluation status <evaluation-id>
evidencegrid revise <version-id> --evaluation <evaluation-id>
evidencegrid benchmark freeze <config-id>
evidencegrid benchmark run <config-id> --split holdout
evidencegrid export <version-id> --format csv
evidencegrid worker
evidencegrid serve
```

Implement a small consistent surface rather than many aliases. CLI and dashboard call the same domain services.

## Meaningful verification matrix

| Area | Essential evidence |
| --- | --- |
| Parser | Real PDF integration and correct physical-page provenance |
| Units | Exact Decimal million/billion cases, mixed-currency exception, ambiguous locale |
| Periods | Annual, three-month, nine-month, comparative year, neighboring balance-sheet trap |
| Anchors | Wrong document/hash/cell/column and missing coordinates |
| Revision | Parent immutability, unsupported evaluator advice, budget stop, manual-origin exclusion |
| Reppo | Actual contract, status variants, missing ID, 409, unknown submit timeout, resumed polling |
| Benchmark | Missing target denominator, duplicate predictions, strict tuple correctness, regressions |
| Dashboard | Real routes, source inspection, no fake results, reload of pending state, responsive keyboard use |
| Exports | Round-trip provenance and absence of secrets/hidden gold in normal analyst exports |

Do not generate tests that simply echo implementation constants. Expected outcomes should come from hand-derived cases or source-reviewed references.

## Cut line

Keep: Docling provenance, period/unit checks, real SERV extraction, real Reppo feedback use, immutable versions, honest measurement, a usable grid/source view, and exports.

Cut first: decorative charts, extra issuers beyond the small corpus, arbitrary uploads, extra metrics, extra agent roles, an ablation UI, image attachments, theme polish beyond accessibility, and deployment automation.

Restatement propagation remains out of scope regardless of spare time until the agreed core is complete.

## Completion report template

```text
Built:
Real source documents and parsed coverage:
Real SERV requests verified:
Real Reppo evaluations and modes:
Measured baseline/revised result and denominator:
Controlled tests (separate):
Commands to reproduce:
Dashboard URL if running:
Remaining access or verification gaps:
```

Do not describe scaffolding, contract mocks, or a recorded response as a freshly executed end-to-end integration.
