# README research and claim sources

Checked November 16, 2026. This note documents the source research for the judge-facing README rewrite; it is not a new product evaluation.

## Reference project

The [official OpenServ Edition 01 page](https://www.openserv.ai/hackathon) identifies **ASSAY** by OoJae as **Best Overall Build** and **Open Track winner**. Its [public repository](https://github.com/OoJae/assay) and [current README](https://raw.githubusercontent.com/OoJae/assay/main/README.md) were read directly.

The original user-supplied [X post](https://x.com/openservai/status/2107116454080581890) returned an access error in the web reader. Award attribution here relies on the organizer's website, not an inferred social association or the project's own claim.

Useful presentation patterns: immediate test instructions; explicit component responsibilities; links from claims to artifacts; reproducible measurements; candid limits, including null results. Evi adopts these general patterns with original prose and its own evidence. No ASSAY code, financial claims, provider configuration, proof receipts or award status is transferred to Evi.

The inspected README is the current version, not a verified submission-time snapshot. Neither its layout nor its technical choices are established as the cause of its award.

## Evi source of truth

| README content | Checked source |
| --- | --- |
| Source scope, page coverage and issuer hashes | `backend/evi/corpus.py`, `parsing.py` |
| Applicable-context obligations and certificate boundary | `backend/evi/binding.py`, `docs/TECHNICAL-DEPTH-IMPLEMENTATION.md` |
| Patch acceptance constraints | `backend/evi/revision.py` |
| Frozen/corrected experiment numbers | Both `artifacts/technical-proof/exp-2026-11-16-*/analysis-v2/summary.json` files; historical scores remain separate |
| Reppo packet limitation and null finding | `docs/REPPO-PAYLOAD-AUDIT.md`, proof-report correction addendum |
| Fresh hosted extraction, cached parse, reload recovery | `artifacts/judge-release/live-2/live-job.json` |
| Hosted acceptance and recorded test evidence | `docs/JUDGE-ACCEPTANCE-REPORT.md` |
| Public data counts and exact source dates | `src/data-manifest.json` |
| Cumulative budgets and optional end-time semantics | `backend/evi/allowance.py`; public health endpoint inspected read-only |

The public health endpoint returned processing enabled, live mode and a live worker during this rewrite. No processing, evaluation or revision POST was sent, and no provider calls were made by this documentation task. Availability and remaining quota are dynamic, so the README links to capability-aware UI rather than promising an unlimited always-on service.

The existing acceptance report contains historical updates that contradict newer ones (for example earlier execution-disabled notes). The README uses the current live-run artifact and later status rather than repeating the old frontend-only/archive-only opening. It links the original records instead of editing frozen evidence.

Judge upload now has an implementation, local fresh-parse evidence and a saved partial public check. `artifacts/judge-upload/local-integration.json` records a fresh local parse with no provider calls. `public-upload-attempt1-docling-disk.json` records a hosted upload/preview/session-isolation check whose Docling stage then failed before SERV. The README and evidence index distinguish these outcomes; full hosted upload-to-extraction is not claimed from a queued/running screenshot.

## Reviewer-oriented update

The README now opens with an evidence-linked project overview and maps Evi to the organizer's published creativity, user-readiness and revenue-potential criteria. The commercial case is explicitly a hypothesis. No scoring weights, placement prediction or customer evidence is invented.

`docs/EVIDENCE-INDEX.json` makes the same claims and limitations machine-readable. It contains factual evidence pointers and metric definitions, without grading instructions, suggested scores or hidden reviewer directives. Both human and automated reviewers can follow the source records.

## Maintenance

- Recompute table figures from the saved analysis artifacts when publishing a new analysis version; do not tune percentages for presentation.
- Keep baseline predictions, historical provider outputs, manifests and original scores immutable.
- Update reviewed-reference counts only from real imported review records.
- Record new public upload/live-run verification separately from historical experiments.
- Use actual workflow badges only when a matching workflow exists. No unsupported CI, accuracy, sponsor endorsement or award badges are added.
