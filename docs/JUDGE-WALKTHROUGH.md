# Judge walkthrough (supported claims only)

No login and no keys. Until a public deployment exists, run it locally (README "Backend") and open `http://127.0.0.1:5173/`.

1. **Home → Real data.** These are SEC source snapshots: real published data, not Evi extraction results. Row counts are observations, not a sample size or throughput.
2. **Workspace → Verizon 3Q 2025 Financial Statements.** These are **stored results** from earlier real runs, with their original timestamps. Open a fact:
   - Click the Value/Metric/Period/Unit tabs; the original PDF highlights the cell each one comes from.
   - The certificate panel lists the 12 obligations (row, column year, interval heading, unit note, per-share exceptions, …). "Re-verify from source" recomputes the certificate on the server from the PDF bytes and the Docling output.
3. **Workspace → AT&T 2Q 2025.** The facts read **"Supported · dates not printed"**: amount, interval length and year are supported, but the statement page prints no end date, so Evi doesn't invent one.
4. **Revision lineage.** Choose a later version in the Version selector. The panel shows the gate decision for that target (accepted / rejected / unchanged) with field transitions.
5. **Feedback.** Real Reppo evaluation records (all 100/100). See `docs/REPPO-PAYLOAD-AUDIT.md` for why that says little: the evaluated packet held only self-cited cells.
6. **Export CSV.** Includes source URL, hash, interval, and `context_coverage` / `exact_interval`.

## What the evidence supports

| Claim | Status | Where |
|---|---|---|
| Applicability binding catches period/unit/scope errors on these 5 statements | Executed; measured against **provisional** references: 34/34 model errors flagged, 6 false alarms under binding-v2 (0 under v3) | `docs/PROOF-INTEGRITY-REVIEW.md` |
| Real Reppo feedback improves results over the same revision without it | **Not supported**: C = D in both experiments | `docs/PROOF-REPORT.md` §9 |
| Accuracy figures | **Provisional**: human reference review is 0/48 | `docs/REFERENCE-REVIEW-PACKET.md` |
| Generalization to unseen layouts | **Not established**: the fresh holdout is frozen but not run | `artifacts/holdout/holdout-2026-11-16-a/` |
| Reproducibility | Read-only replay: 288/288 certificates per experiment under the manifest policy | `python -m evi.replay exp-2026-11-16-a` |
