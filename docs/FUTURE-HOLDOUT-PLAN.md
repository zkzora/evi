# Future holdout plan (prepared 2026-11-16; nothing downloaded, processed or labelled)

**Why:** the AT&T "holdout" in exp-2026-11-16-a was read by the builder while designing rules and transcribing references, and exp-2026-11-16-b is post-hoc development work. Neither is evidence of generalization to unseen layouts. Both disclosures stay in place.

## Freeze before acquisition

1. Freeze code and policies first: binding-v3, revision-v3, extraction period-unit-v2, analysis-v2, replay-v2, coverage-v1. Record the git or file hashes in the new manifest before any new source is opened.
2. Choose **issuers and templates not used to tune these rules**: no Verizon or AT&T documents. Candidates (USD, telecom/connectivity, publish PDF statements): T-Mobile US, Comcast, Charter Communications, Lumen Technologies. Choose 3–4 statements mixing annual and interim; pick by a predeclared rule (e.g. the latest 10-Q/10-K statement PDF on each issuer's IR host), not by looking at layouts.
3. A person other than the builder registers the sources (URL, SHA-256, statement page) and sets the target columns by the targets-v1 rules, **without viewing model outputs**.

## Reference labelling

- The labeller works from rendered pages using `docs/REFERENCE-REVIEW-PACKET.md` conventions; a second reviewer adjudicates. Labels go into `data/references/references-holdout-v1.json`. Only its hash enters the manifest before inference.
- Any agent-drafted labels are stored separately and marked provisional.

## Execution (needs explicit budget approval)

- Arms A–D exactly as in exp-a (one SERV extraction per trial; C and D branch from the same A; one revision call each).
- **Reppo packet:** decide before running whether to use `reppo-packet-v1` (as audited) or a revised `reppo-packet-v2` (full table plus target definitions). Changing it after seeing results is not allowed.
- Maximum budget (illustrative, to be confirmed): 4 statements × 2 trials → 8 Reppo evaluations (3,520 credits) and about 24 SERV calls.
- Scoring with analysis-v2 metrics; replay-v2 must report VERIFIED before any result is reported.

## Reporting

Report reference match, complete interval coverage, certificate outcome, composite, detector TP/FP/FN, and paired transitions per document, including null and negative results. No pooled population claims.
