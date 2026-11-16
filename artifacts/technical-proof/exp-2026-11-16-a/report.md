# Experiment exp-2026-11-16-a — measured results

Reference provenance: **builder-drafted, source-reviewed, provisional (not independent human gold)**. Strict correctness requires every frozen field to equal the reference AND a `supported` binding certificate. Unexecuted branches are reported, not scored as 0%.

| Arm | Targets | Executed | Strict correct | Semantic correct | Covered | Certificate supported |
|---|---|---|---|---|---|---|
| A | 96 | 96 | 56 | 60 | 96 | 56 |
| B | 96 | 96 | 56 | 60 | 96 | 56 |
| C | 96 | 96 | 56 | 60 | 96 | 56 |
| D | 96 | 96 | 56 | 60 | 96 | 56 |

## Split

| Arm | Development strict/executed | Holdout strict/executed |
|---|---|---|
| A | 28/48 | 28/48 |
| B | 28/48 | 28/48 |
| C | 28/48 | 28/48 |
| D | 28/48 | 28/48 |

## Paired transitions (same trial, same target)

| Pair | Improvement | Regression | Preserved correct | Unchanged incorrect | Coverage lost | Not executed |
|---|---|---|---|---|---|---|
| A->C | 0 | 0 | 56 | 40 | 0 | 0 |
| A->D | 0 | 0 | 56 | 40 | 0 | 0 |
| C->D | 0 | 0 | 56 | 40 | 0 | 0 |

## Arm B diagnostics vs reference

{"false_alarm": 4, "correct_pass": 56, "true_detection": 36}

## Field errors by arm

{"A": {"amount": 4, "currency": 24, "end_date": 6, "start_date": 20}, "B": {"amount": 4, "currency": 24, "end_date": 6, "start_date": 20}, "C": {"amount": 4, "currency": 24, "end_date": 6, "start_date": 20}, "D": {"amount": 4, "currency": 24, "end_date": 6, "start_date": 20}}

## Per document (strict/executed)

- A: verizon-fy2025 10/12, verizon-fy2024 6/12, verizon-3q2025 12/24, att-3q2025 12/24, att-2q2025 16/24
- B: verizon-fy2025 10/12, verizon-fy2024 6/12, verizon-3q2025 12/24, att-3q2025 12/24, att-2q2025 16/24
- C: verizon-fy2025 10/12, verizon-fy2024 6/12, verizon-3q2025 12/24, att-3q2025 12/24, att-2q2025 16/24
- D: verizon-fy2025 10/12, verizon-fy2024 6/12, verizon-3q2025 12/24, att-3q2025 12/24, att-2q2025 16/24

## Costs and latency

```json
{
 "serv_calls_recorded": 30,
 "serv_total_tokens": 255312,
 "serv_usd": "unknown (per-call price not returned; token counts only)",
 "reppo_credits_charged": 4400,
 "reppo_wait_s": [
  97.1,
  130.5,
  85.2,
  92.7,
  92.9,
  134.5,
  123.5,
  113.0,
  35.7,
  134.2
 ],
 "latency_s_by_arm": {
  "A": [
   8.5,
   11.7,
   11.3,
   11.3,
   6.2,
   6.9,
   6.3,
   10.2,
   9.8,
   12.0
  ],
  "C": [
   2.8,
   7.0,
   4.2,
   6.0,
   5.7,
   4.0,
   3.6,
   5.5,
   2.0,
   4.8
  ],
  "D": [
   102.9,
   134.1,
   90.3,
   98.6,
   96.6,
   136.2,
   127.2,
   119.4,
   38.4,
   137.2
  ]
 }
}
```

Targets within a document and repeated trials are correlated; 5 reports from 2 issuers support descriptive results only.
