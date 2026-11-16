# Judge walkthrough (2–3 minutes, no login)

Public site: **https://evi-lovat.vercel.app** (read-only archive of real stored runs; see `docs/LIVE-DEPLOYMENT-STATUS.md`). Press **Try Evi** on Home or any page to follow the same path with a guided card (`?tour=1…5`; reload-safe; *Restart* changes no records).

| What you see | Kind of evidence |
|---|---|
| Real data context check | A rule check on published SEC metadata, run in your browser. Not an AI extraction. |
| Workspace facts and versions | **Stored** results of earlier real Docling + SERV runs, shown with their original UTC timestamps. Nothing is re-run. |
| "Re-verify from source" | **Recomputed now** on the server from the registered PDF bytes and Docling artifact. No provider call. |
| Reppo evaluations | **Stored** real evaluations (all made 2026-11-15), each linked to the exact version it judged. |
| New extraction or evaluation | **Not available on this deployment**: no Docling worker and no provider keys. Shown as "Archive · stored results" with the reason. |

## 1. Catch a period mismatch (30 s)

- Open https://evi-lovat.vercel.app/data?company=verizon&source_case=verizon-period&expect_period=12&expect_unit=USD&check=1 — Verizon revenue for **2026-01-01 → 2026-09-30** (SEC filing 0000732712-26-000052). Expected: **"Context does not match — The source reports 9 months, while you selected a full year."**
- Same observation with 9 months: …&expect_period=9… → **"Context matches your selection."**
- Unit mismatch: …&expect_period=9&expect_unit=USD+millions… → mismatch, because the SEC value is in base USD.

## 2. Processing availability (15 s)

- Open https://evi-lovat.vercel.app/workspace?document=verizon-3q2025 — the status reads **"Archive · stored results"**, *Process report* is disabled, and an inline note gives the reason. On a live host the same button queues a real job and shows its actual stages (parse reused or fresh, extraction, checks) with job, run and version IDs.

## 3. Inspect the evidence (60 s)

- **Verizon 3Q 2025, complete context:** https://evi-lovat.vercel.app/workspace?document=verizon-3q2025&run=run_3f60316ec62f4d0bb449&version=ver_3f60316ec62f_5&fact=run_3f60316ec62f4d0bb449%3Ar5%3Averizon-3q2025%3Arevenue%3A3M%3A2025 — the Value/Metric/Period/Unit tabs highlight cells on physical page 1. The certificate shows 12 obligations and the interval 2025-07-01 → 2025-09-30 (start derived). The revision decision reads "currency fail → pass" ("$" → "USD", accepted with source support). Press **Re-verify from source**: "Verified".
- **Verizon FY2024, offset page coordinates:** https://evi-lovat.vercel.app/workspace?document=verizon-fy2024&run=run_b15ed73528114efe9b3e&version=ver_b15ed7352811_5&fact=run_b15ed73528114efe9b3e%3Averizon-fy2024%3Arevenue%3A12M%3A2024 — the highlight sits on 134,788 on physical page 54 (CropBox offset handled).
- **AT&T 2Q 2025, partial context:** https://evi-lovat.vercel.app/workspace?document=att-2q2025&run=run_325e06e62b8c46e58b4d&version=ver_325e06e62b8c_5&fact=run_325e06e62b8c46e58b4d%3Aatt-2q2025%3Arevenue%3A3M%3A2025 — **"Supported · dates not printed"**. The page prints "Second Quarter" / "Six-Month Period" without an end date, so Evi doesn't guess one.

## 4. Evaluations and revisions (20 s)

- https://evi-lovat.vercel.app/feedback — "This version" honestly shows **no evaluation** for a revision version. **Recorded evaluation history** lists all 11 real Reppo evaluations (all 100/100, packet v1 with candidate-cited cells), each linking to the exact version it judged.

## 5. Measured evidence (30 s)

- https://evi-lovat.vercel.app/benchmark — two experiments from the frozen artifacts, with the four arms A–D:
  - **exp-2026-11-16-a:** reference match 62/96 in every arm; composite 56/96; checker caught 34 errors with 6 false alarms and 0 misses.
  - **exp-2026-11-16-b** (post-hoc development evidence): A 62 → C 74 = D 74.
  - **Arm D equals arm C in both.**
  - References are provisional (human review 0/48). Download JSON or open the raw artifacts on GitHub.

Code: https://github.com/zkzora/evi
