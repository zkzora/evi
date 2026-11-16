# Experiment exp-2026-11-16-b — measured results

Reference provenance: **builder-drafted, source-reviewed, provisional (not independent human gold)**. Strict correctness requires every frozen field to equal the reference AND a `supported` binding certificate. Unexecuted branches are reported, not scored as 0%.

| Arm | Targets | Executed | Strict correct | Semantic correct | Covered | Certificate supported |
|---|---|---|---|---|---|---|
| A | 96 | 96 | 62 | 62 | 96 | 62 |
| B | 96 | 96 | 62 | 62 | 96 | 62 |
| C | 96 | 96 | 74 | 74 | 96 | 74 |
| D | 96 | 96 | 74 | 74 | 96 | 74 |

## Split

| Arm | Development strict/executed | Holdout strict/executed |
|---|---|---|
| A | 30/48 | 32/48 |
| B | 30/48 | 32/48 |
| C | 42/48 | 32/48 |
| D | 42/48 | 32/48 |

## Paired transitions (same trial, same target)

| Pair | Improvement | Regression | Preserved correct | Unchanged incorrect | Coverage lost | Not executed |
|---|---|---|---|---|---|---|
| A->C | 12 | 0 | 62 | 22 | 0 | 0 |
| A->D | 12 | 0 | 62 | 22 | 0 | 0 |
| C->D | 0 | 0 | 74 | 22 | 0 | 0 |

## Arm B diagnostics vs reference

{"correct_pass": 62, "true_detection": 34}

## Field errors by arm

{"A": {"amount": 4, "currency": 24, "end_date": 6, "start_date": 18}, "B": {"amount": 4, "currency": 24, "end_date": 6, "start_date": 18}, "C": {"amount": 4, "currency": 12, "end_date": 6, "start_date": 6}, "D": {"amount": 4, "currency": 12, "end_date": 6, "start_date": 6}}

## Per document (strict/executed)

- A: verizon-fy2025 12/12, verizon-fy2024 6/12, verizon-3q2025 12/24, att-3q2025 12/24, att-2q2025 20/24
- B: verizon-fy2025 12/12, verizon-fy2024 6/12, verizon-3q2025 12/24, att-3q2025 12/24, att-2q2025 20/24
- C: verizon-fy2025 12/12, verizon-fy2024 6/12, verizon-3q2025 24/24, att-3q2025 12/24, att-2q2025 20/24
- D: verizon-fy2025 12/12, verizon-fy2024 6/12, verizon-3q2025 24/24, att-3q2025 12/24, att-2q2025 20/24

## Costs and latency

```json
{
 "serv_calls_recorded": 20,
 "serv_total_tokens": 166431,
 "serv_usd": "unknown (per-call price not returned; token counts only)",
 "reppo_credits_charged": 0,
 "reppo_wait_s": [],
 "latency_s_by_arm": {
  "C": [
   4.3,
   3.2,
   3.1,
   8.1,
   3.8,
   3.4,
   3.1,
   12.6,
   98.0,
   8.0
  ],
  "D": [
   2.7,
   4.0,
   4.3,
   7.1,
   4.5,
   5.2,
   7.3,
   18.7,
   17.3,
   11.1
  ]
 }
}
```

Targets within a document and repeated trials are correlated; 5 reports from 2 issuers support descriptive results only.
