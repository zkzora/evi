# 12 — Demo, evidence bundle, and submission

## Event facts to recheck before submission

The official Edition 02 page lists November 2–15, 2026, requires SERV Reasoning, describes the Reppo track as reliable agents using feedback for measurable improvement, and requests a public repository, demo, short write-up, and submission post on X. Existing projects may receive meaningful new features with clear disclosure. Listed judging dimensions are creativity, user readiness, and revenue potential.

The published deadline is November 15, 2026 at 23:59 UTC, equivalent to November 16 at 06:59 WIB. Recheck the form and any later organizer updates before submitting; do not apply Edition 01-only requirements automatically.

Source: [official Edition 02 page](https://www.openserv.ai/hackathon-2).

## Demo promise

“EvidenceGrid keeps the meaning of a financial number attached to its source: what it measures, which period it covers, and how its unit is scaled. Real evaluator feedback can trigger an evidence-backed correction, and the benchmark measures whether that correction helps.”

Do not pitch it as an accounting auditor, investment advisor, fraud detector, or guaranteed-accuracy system.

## Three-minute English demo script

### 0:00–0:25 — Establish the failure

Show a real income-statement page with the applicable period heading and unit note. Explain: “This number covers nine months. Calling it a full-year figure changes its meaning even when every digit is transcribed correctly.”

Use an actual natural failure if one was observed. Otherwise label the wrong version prominently as a controlled example and keep it out of benchmark results.

### 0:25–0:55 — Show the source-linked grid

Open the corresponding document/run in Evidence Grid. Select the fact and reveal amount, metric, period, and unit evidence. Show original amount and canonical normalization. Explain that Docling supplies parsing and coordinates; EvidenceGrid adds semantic checks.

### 0:55–1:35 — Show feedback and revision

Open a previously settled real Reppo evaluation. Show criteria, a relevant critique, provider mode/ID, and timestamp. Then show the SERV revision proposal and its supporting source heading. Explain the deterministic recheck and immutable initial version.

Standard API evaluations are asynchronous. Do not pretend a recorded settled evaluation returned instantly during the demo. A live status refresh may be shown, but the demo must not depend on a new ten-minute settlement completing within three minutes.

If no real verdict is available, state the limitation and demonstrate the independent mechanism with its correct fixture/sandbox label. Do not call that a completed Reppo integration.

### 1:35–2:15 — Show honest before/after measurement

Open the benchmark artifact. State number of reports, target facts, split, and label provenance. Show strict semantic correctness as actual counts and percentages, plus period/unit scores, improvements, and regressions.

If results are unchanged, say so and explain which mechanism cases were demonstrated separately. If results regress, show that rather than substituting development results as unseen holdout performance.

### 2:15–2:45 — Complete the analyst task

Export CSV and inspect one row's interval, currency/scale, source URL/page, and version. This establishes that the useful result leaves the dashboard with its context intact.

### 2:45–3:00 — State scope and limits

“The current build covers a small set of Indonesian telecom reports and three metrics. It checks fidelity to source context. Restatement propagation is a future direction, and broader accuracy and demand still need validation.”

## Evidence bundle

Prepare a reproducibility folder containing:

1. Corpus manifest and source hashes/URLs.
2. Relevant rendered source regions with page mapping.
3. Docling version, settings, coverage, and raw parse artifacts or instructions to regenerate them.
4. Initial evidence packets and prediction artifacts.
5. Real SERV transport metadata with secrets removed.
6. Real Reppo evaluation IDs, status, criteria, verdicts, critiques, and actual evidence basis.
7. Revision proposals, accepted/rejected changes, source support, and immutable output versions.
8. Frozen scorer/label/policy hashes, split, and measured result files.
9. Separate controlled-mechanism-test report.
10. Analyst export and complete reproduction instructions.

Check source redistribution rights before committing full issuer PDFs or large rendered corpora to a public repo. URLs, hashes, limited necessary evidence, and reproducible acquisition commands may be preferable. Never commit .env, account keys, raw secret-bearing headers, local caches, or the venv.

## What the write-up must distinguish

| Layer | Permitted statement |
| --- | --- |
| Product hypothesis | Analysts may benefit from less manual period/unit checking |
| Implemented behavior | Name only working flows and actual supported documents |
| Verified evidence | List real parses, provider calls, verdicts, exports, and measured outputs |
| Assumptions/limits | Small sample, annotation provenance, unverified demand, source truth boundary |

A paid provider call proves integration execution, not user demand. A favorable Reppo verdict proves an evaluation occurred, not extraction accuracy. A source check proves fidelity within its boundary, not company financial truth.

## Draft write-up structure

```text
Name: EvidenceGrid
Track: Reppo

User and concrete failure:
[Who copies which figures, and how period/unit confusion changes the result.]

Mechanism:
[Docling provenance -> SERV extraction -> deterministic checks -> real Reppo critique -> bounded SERV revision -> source recheck.]

What we built during the event:
[Actual implemented contributions, versions, dates, and dependencies.]

Measured result:
[Actual correct/total, split, before/after, regressions, cost and timing.]

Try it:
[Verified demo URL or runnable local commands, repository, short video.]

Limitations:
[Scope, labeling, missing integrations, and evidence boundaries.]
```

## Optional roadmap explanation only

Restatement propagation could later link revised source facts to dependent spreadsheet calculations and identify affected outputs. This requires reliable source-version matching and calculation lineage. Explain the idea in a short roadmap paragraph; do not implement or imply it exists in the hackathon build.

## Submission preparation checklist

- All claimed flows work or are explicitly labeled recorded/limited.
- Real SERV usage and Reppo feedback use are inspectable.
- Dependency attribution and work completed during the event are clear.
- Accuracy numbers have denominators, source/label/policy versions, and honest split labels.
- Demo and repository are accessible in the intended environment.
- README contains setup, required keys, sources, expected runtime, and limitations.
- Screenshot/video text is English and matches actual product behavior.
- Secret and artifact review completed before publication.
- Final write-up and X post are drafted for the user.

Preparing drafts is within build work. Posting to X, submitting a form, publishing a repository, or deploying to a public service requires the user's corresponding authorization; do not infer it from this documentation handoff.
