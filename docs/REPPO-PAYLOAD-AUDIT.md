# Reppo payload audit (offline, 2026-11-16)

Scope: the 11 real Reppo evaluations Evi submitted (1 development smoke test + 10 in exp-2026-11-16-a). This audit made **no new provider calls**. Machine-readable output: `artifacts/proof-integrity/reppo-payload-audit.json`. Raw provider records: `data/runs/artifacts/provider/reppo-eval-<id>-*.json`. Each holds the provider's echoed `input`, its `result` and its `trace`.

## 1. Confirmed observations

| Check | Finding |
|---|---|
| Provider status / source / mode | All 11 `status: COMPLETED`, `source: API`, `taskType: response`, `creditsCharged: 440`. Stored locally as `mode: reppo_live`, `status: completed`. |
| Evaluated version identity | In all 11, the packet's `candidate_version.version_id` equals the evaluation record's `version_id`. In every arm D receipt, `evaluation.version_id` equals the receipt's parent (checked by replay-v2). |
| Packet integrity | All 11 inputs are complete, valid JSON of 9,196–15,675 bytes (limit 50 KB). Nothing was truncated. Every fact of the version is present (6 or 12), each with its four evidence groups, as are the 4 criteria, the source URL and SHA-256, and the parsed page numbers. |
| Scores | Every evaluation: `score: 100`, `decision: accept`, `confidence: high`, `route: ship`. `rubric_scores` = `{safety, completeness, factual_accuracy, instruction_adherence}`, all 100. |
| Rubric | The returned dimensions are the provider's generic rubric, **not** the four criteria Evi embedded in the JSON input. agents.md (read 2026-11-16) documents only `taskType`, `input` and `attachments`; no custom-criteria field. Evi's criteria are therefore just text inside the evaluated input. **They are not a provider-level rubric setting.** |
| Critiques | Evi's normalized `verdicts[]` have empty critique strings, because `rubric_scores` carries numbers only. The evaluators' reasoning exists in `trace.evaluations[].reasoning/evidence`; Evi's UI and revision prompt did not surface it. |
| Evaluators | 3–4 evaluator models per evaluation (e.g. glm-5-2, claude-sonnet-4-5, deepseek-chat, gpt-4o, gemini-2.5-flash), with economic weighting by stake. Each `explain.confidence_checks` reports agreement (std-dev 0). |

## 2. What the evaluator could and could not see

The packet (`evaluation.build_input`) contained:
- the candidate facts;
- **only the evidence cells the candidate itself cited** (13–23 items);
- the page *text* items (3–5 items, e.g. `["AT&T Inc.", "Financial Data", "1"]` for AT&T).

It did **not** contain the rest of the statement table.

| Natural error in the evaluated baseline | Judgeable from the packet? | Evaluator behaviour (stored trace) |
|---|---|---|
| AT&T 2Q t1 (`cmwiff4re000608ifru1paguu`): owner-attributable profit taken from "Net Income Attributable to **Common Stock**" ($4,464M) instead of "…to AT&T" ($4,500M) | **Partly.** The wrong label was visible and the requested definition said "profit attributable to owners of the parent". The correct row label and value were **absent** (`reference_row_label_in_packet: false`, `reference_value_in_packet: false`). | Accepted. Trace: "row labels (… Net Income Attributable to Common Stock) … all align with the cited evidence"; "Net Income Attributable to Common Stock values correctly extracted for all four periods". |
| AT&T 3Q t1 (`cmwif9pp2000408ify1gumwm7`): currency "$" instead of "USD" | Yes. The candidate's currency field and the "Dollars in millions" note were both present. | Accepted. The evaluators treated currency as consistent with the note. |
| Verizon FY2024 t1 (`cmwifhh7w000708if3k6rawyb`): end dates omitted although "Years Ended December 31," and the year headers were cited | Yes. Null dates were visible next to the cited headings. | Accepted. The trace never mentions end dates. |

## 3. Plausible explanations for the uniform 100/100 (not established as causes)

1. **Self-citation framing (Evi's packet design).** The task read "Evaluate this financial-fact extraction against the cited public source evidence." The evaluators did exactly that: the stored reasoning checks agreement between each fact and *its own citations*. A wrong row cited consistently is internally consistent.
2. **Missing alternatives (Evi's packet design).** Without the full table, a "wrong row" cannot be discovered by comparison.
3. **Generic rubric.** The provider scores generic dimensions. Evi's period/unit/scope criteria are text inside the input, not a scoring rubric.
4. **Format tolerance.** "$" versus "USD" and null-versus-printed end dates may be read as acceptable representations by a general-purpose judge.

None of this shows a defect in Reppo. It shows that **this payload design** did not give the evaluator a fair chance to find the wrong-row error, and that the evaluator did not penalize the visible format and completeness issues. The result must not be generalized to other Reppo tasks.

## 4. Implications for the existing results

- The null C-versus-D result stands as measured. It is also partly explained by the packet design: with uniform acceptance and empty critiques, arm D received little information beyond what arm C had.
- Reppo scores remain evaluator opinions and are never used as accuracy.

## 5. Calibration plan (prepared, NOT executed)

Purpose: test whether a revised packet lets the evaluator detect known period/unit/scope faults. This is a **controlled** test, kept separate from natural extraction accuracy.

| Item | Plan |
|---|---|
| Packet change (to be versioned as `reppo-packet-v2`) | Include the full statement table (every row label and value cell with IDs), state the requested metric definitions verbatim, and ask "Is each fact the correct value for its requested target?" instead of "consistent with cited evidence". Keep `taskType: response`. |
| Negative controls (labelled controlled faults) | 1 wrong attribution row (common stock instead of parent), 1 comparative-year column, 1 nine-month value labelled as a quarter, 1 scale error (billions), each on a copy of a supported Verizon 3Q25 version. |
| Positive controls | 2 untouched, fully supported versions (Verizon 3Q25 and AT&T 2Q25). |
| Arms | The same 6 inputs under the current packet (v1) and the revised packet (v2). |
| Maximum budget | 12 evaluations × 440 credits = **5,280 credits** (text only, no attachments). Stop on any 401/402 or unknown submission outcome. |
| Pre-declared readout | Per control: flagged (score < 85 or decision reject, or a trace naming the fault) versus not flagged. Report all 12, including misses, with raw traces. |

Running this needs explicit approval of the credit budget.
