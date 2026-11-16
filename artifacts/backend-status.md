# Backend status — 2026-11-16 (technical-depth extension)

Read docs/PROOF-REPORT.md for figures, IDs and limits. Summary:

| Item | State |
|---|---|
| Corpus | 5 USD statements (Verizon FY25/FY24/3Q25 development; AT&T 3Q25/2Q25 holdout), 48 frozen targets, real Docling parses |
| Binding + certificates | Implemented (binding-v3); 618/618 stored certificates re-verify under their own policy |
| SERV | Real; v2 target-aware extraction; 50 experiment calls + dev smoke |
| Reppo | Real; 11 completed evaluations (1 dev smoke + 10 experiment), 4,840 credits; all scored 100/100 |
| Four-arm experiment | exp-2026-11-16-a frozen: A=B=C=D 56/96 strict, C→D 0/0. exp-2026-11-16-b post-hoc: A 62, C 74, D 74, C→D 0/0 |
| References | Provisional, builder-drafted, source-reviewed; no independent human review |
| Deployment | Local only |
