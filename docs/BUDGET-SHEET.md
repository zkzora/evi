# Budget sheet (2026-11-16) — nothing on this sheet is approved

Prices were re-read on 2026-11-16 from the providers' public docs.
- **Reppo** (`eval.reppo.xyz/agents.md`): 440 credits per text-only evaluation, 1,000 with an attachment. Charged only on COMPLETED; reserved while in flight. No idempotency key.
- **SERV** (`docs.openserv.ai` models page): `gpt-5.4-mini` costs $1.00 per million input tokens and $6.00 per million output tokens, including SERV Reasoning.

Credits and USD are different units. Reppo's USD price for account credits is not published on that page; x402 credits are quoted at about $0.22 per evaluation. SERV figures below are **estimates** from published prices and recorded token counts; no invoice was observed.

| Operation | Current authorization | Execution gate | Max provider use | Estimated cost |
|---|---|---|---|---|
| Local replay, tests, certificate/source verification, packet dry runs | **Within this task** | None needed (no provider submission; `replay` uses a read-only DB) | 0 calls | 0 |
| Controlled Reppo packet calibration (`docs/REPPO-PAYLOAD-AUDIT.md` §5: 6 controls × packet v1/v2) | **Not approved** | Explicit approval of the evaluation count and credit cap | 12 Reppo evaluations | **≤ 5,280 credits**; 0 SERV calls |
| Fresh holdout run (`artifacts/holdout/<id>/manifest-dryrun.json`; 4 reports × 2 trials, arms A–D) | **Not approved** | Reviewed and frozen plan + registered sources + reference hash + a **separate** approval file (`python -m evi.authorization template <id>`) + `EVI_ALLOW_PAID_RUNS=1` | ≤ 26 SERV calls, ≤ 8 Reppo evaluations | **≤ 3,520 credits**; SERV ≈ $0.31 estimated (8 × ~5.6k in/2.1k out + 16 × ~8.4k in/0.3k out) |
| Public production writes / compute | **Not enabled** | Authorized deployment + `EVI_EXECUTION_ENABLED=true` + public-use limits configured | Per-day caps: SERV 40 calls, Reppo 10 evaluations (server defaults) | ≤ 4,400 credits/day at the defaults if enabled |

These are separate decisions. Approving one does not approve another; configured API keys are not approval.

Spent so far (recorded, all before this sheet): 4,840 Reppo credits (11 evaluations); 56 SERV calls, 426,293 input + 35,970 output tokens ≈ **$0.64 estimated**.
