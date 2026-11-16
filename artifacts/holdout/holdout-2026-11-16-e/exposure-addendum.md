# Exposure addendum — holdout-2026-11-16-e (2026-11-16)

- Supersedes `holdout-2026-11-16-a` to `-d`; their frozen code changed before any candidate source was acquired or opened (latest: per-request spending-allowance reservations in providers.py, unknown-outcome handling for SERV read timeouts, allowance-aware capabilities). All are retained unchanged as records and are not used.
- Behaviour change relevant to a future run: every SERV request and Reppo submission now needs an owner-configured allowance (`EVI_ALLOWANCE_*`) in addition to the experiment approval file and `EVI_ALLOW_PAID_RUNS=1`; a SERV read timeout ends the job as `outcome_unknown` instead of retrying.
- Evi's public Real data explorer displays SEC XBRL observations for **T-Mobile US** and **Comcast** (two holdout candidates), including 2026 interim revenue. The frozen extraction/revision/evaluation pipeline never reads those observations. Reference labellers must label from the registered PDFs, not from SEC data, and must state whether they viewed the explorer for these issuers.
- No candidate holdout PDF has been downloaded, opened or registered.
