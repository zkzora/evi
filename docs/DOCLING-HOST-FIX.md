# Docling upload host diagnosis — 2026-11-16

## Read-only findings

The Railway CLI was queried for the existing `reasonable-benevolence` project, service `evi`, production environment. No settings, deployments, uploads, model configurations or provider budgets were changed. No SERV or Reppo calls were made.

Command:

```text
railway metrics --project 8c021a5b-1565-407f-8609-755c61c8ee28 --service evi --environment production --memory --volume --since 6h --json
```

Window: 2026-11-16 04:40:36–10:40:37 UTC. The returned summaries were:

| Resource | Limit (CLI MB) | Maximum observed (CLI MB) | Current (CLI MB) |
| --- | --- | --- | --- |
| Container memory | 1023.99737856 | 1023.988989952 | 91.72942848 |
| `/data` volume | 500.0 | 346.810220544 | 346.40756736 |

Memory reached essentially the entire 1 GB allowance. Combined with recorded worker/container restarts during fresh Docling parsing, this strongly supports memory exhaustion as the current blocker. No explicit kernel OOM record was obtained, so do not claim a kernel-level diagnosis from the summary alone.

The earlier model-cache disk problem is distinct: deployment notes now record model weights baked into the image rather than downloaded into the small `/data` volume. Moving application records to another database does not increase this container's RAM.

## Recommended bounded change

1. Open the existing Evi Railway service, **Settings → Deploy → Replica Limits**.
2. Verify the current plan can provide the desired resource ceiling. Set a **4 GB memory ceiling** as an initial sizing estimate for API plus one Docling worker; an increased paid plan or resource allowance requires the owner's decision.
3. Keep **one replica** and **one active processing job**. This SQLite/local-volume deployment must not be scaled horizontally to address memory exhaustion.
4. Apply the change and verify the effective memory limit in metrics. Keep the accurate Docling configuration, existing baked-in models, source identities and provider limits.
5. Under the existing explicit allowance, run at most one fresh uploaded-page smoke test. Confirm fresh Docling completion, one new SERV extraction if permitted, the same job after reload, source-page highlights, certificates, and no container restart. Inspect peak memory and remaining disk after the run. If the request outcome is unknown, reconcile it instead of repeating the paid submission.

Four GB is an initial engineering estimate, not a measured guarantee. Observe an actual successful parse before declaring the upload path complete. If usage remains high after a parse, investigate model lifetime/allocator retention before enabling more parallel work.

Resource changes have not been applied by this diagnosis. Railway bills actual resource usage according to the plan; a 4 GB limit is not a fixed monthly-price quote.

## Official references

- [Resource and replica limits configuration](https://docs.railway.com/pricing/cost-control).
- [Service metrics](https://docs.railway.com/observability/metrics).
- [Vertical scaling](https://docs.railway.com/deployments/scaling).
- [Current pricing](https://railway.com/pricing).
