# Release readiness (2026-11-16)

Legend: ✅ done · ⏳ pending an external dependency · — not applicable. "Locally verified" means it ran on this machine; it does not mean publicly deployed or independently reviewed.

| Item | Implemented | Locally verified | Independently reviewed | Paid run approved / executed | Publicly deployed / verified |
|---|---|---|---|---|---|
| Docling → SERV → certificates → revision → Reppo pipeline | ✅ | ✅ (earlier real runs) | ⏳ | Historical runs executed (4,840 credits; ~$0.64 SERV, estimated) | ⏳ |
| Replay-v2 (policy-aware, read-only, coverage-derived) | ✅ | ✅ exp-a 288/288 v2, exp-b 288/288 v3; 20/20 receipts each | — | — | — |
| Analysis-v2 (non-circular metrics) + reconciliation | ✅ | ✅ | ⏳ (depends on references) | — | — |
| Partial-context coverage (API/UI/CSV) | ✅ | ✅ browser + production smoke | — | — | ⏳ |
| Reference review importer (`evi.review`) | ✅ | ✅ 20 tests on TEST sheets | — | — | — |
| Human reference review | — | — | ⏳ **0/48 reviewed** (sheet validated, pending) | — | — |
| Reppo packet v2 (full statement table) | ✅ | ✅ dry run: 11/11 packets complete, 14–24 KB | — | ⏳ **not approved** (calibration ≤ 5,280 credits) | — |
| Spending gates (approval file + flag; execution switch) | ✅ | ✅ tests; historical runner refuses | — | — | — |
| Fresh holdout freeze | ✅ | ✅ frozen 2026-11-16T02:45:47Z, no drift | ⏳ (registration and labels by a non-builder) | ⏳ **not approved** (≤ 3,520 credits + ~26 SERV calls) | — |
| Production package (image, compose, Caddy, env, backups) | ✅ | ✅ production-mode smoke (18/18) + restart + backup/restore on copied state; ⚠️ **Docker image not built here** (Docker unavailable) | — | — | ⏳ **no authorized host** |

## Facts at this checkpoint

- Original experiments, predictions, references, provider records, manifests, ledgers and scores are byte-identical to the pre-repair snapshot (`artifacts/proof-integrity/`). **Arm D = arm C in both experiments; no Reppo benefit is established.**
- New provider calls during this task: **0**. Credits spent: **0**. Provider-call count: 162 before and after.
- The review sheet now has empty `review_provenance` and `source_evidence` fields added to its template; every status is still `pending`.
- Tests: 132 backend, 16 frontend; production build OK; `scripts/e2e_partial_context.py`, `scripts/e2e_browser.py` and `scripts/prod_smoke.py` pass.

## Dependencies still needed (in order)

1. **A human reviewer** (not the label author) completes `data/references/review/review-sheet-references-v1.json` per `docs/REVIEWER-INSTRUCTIONS.md`. Then `python -m evi.review import …` and `analysis.evaluate_reviewed(…)` produce a new reference/analysis version.
2. **An authorized hosting target** (domain + host with ≥ 4 GB RAM and a local persistent volume) and approval of its cost. Then build the image, deploy with `EVI_EXECUTION_ENABLED=false`, and verify from a clean browser.
3. **Optional, separate budget approvals** (`docs/BUDGET-SHEET.md`): (a) Reppo packet calibration, ≤ 5,280 credits; (b) the holdout run, ≤ 3,520 credits and ~26 SERV calls, after holdout sources are acquired and registered and references are labelled by someone outside the build loop.
