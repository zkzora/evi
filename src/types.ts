import { z } from 'zod'

export const metricNames = {
  revenue: 'Revenue',
  operating_profit: 'Operating profit',
  profit_attributable_to_owners: 'Profit attributable to owners',
} as const
export type Metric = keyof typeof metricNames
export const metricSchema = z.enum(['revenue', 'operating_profit', 'profit_attributable_to_owners'])
export const documentSchema = z.object({
  document_id: z.string(), issuer_name: z.string(), title: z.string(), source_url: z.string(),
  sha256: z.string(), page_count: z.number().int().positive(),
  source_page: z.number().int().positive().default(1),
  source_path: z.string().optional(), period_label: z.string().optional(),
  parse_status: z.string().default('not_started'), parse_id: z.string().nullable().optional(),
  availability: z.string().default('downloaded'),
}).passthrough()
export type Report = z.infer<typeof documentSchema>
export const checkSchema = z.object({
  check_id: z.string(), fact_id: z.string(), check_type: z.string(),
  status: z.enum(['pass', 'fail', 'unknown', 'not_applicable']), message: z.string(),
  evidence_ids: z.array(z.string()).default([]),
}).passthrough()
export type Check = z.infer<typeof checkSchema>
export const factSchema = z.object({
  fact_id: z.string(), document_id: z.string(), metric: metricSchema, metric_label: z.string(),
  scope: z.string(), reported_value: z.string().nullable(), currency: z.string().nullable(),
  unit_scale: z.string().nullable(), normalized_value: z.string().nullable(),
  period: z.object({ start_date: z.string().nullable(), end_date: z.string().nullable(),
    duration_months: z.number().nullable(), kind: z.string(), label: z.string() }),
  evidence: z.object({ value_ids: z.array(z.string()), metric_ids: z.array(z.string()),
    period_ids: z.array(z.string()), unit_ids: z.array(z.string()) }),
  origin: z.string(), notes: z.array(z.string()).default([]),
}).passthrough()
export type Fact = z.infer<typeof factSchema>
export const versionSchema = z.object({
  version_id: z.string(), run_id: z.string(), parent_version_id: z.string().nullable().optional(),
  origin: z.string(), facts: z.array(factSchema), checks: z.array(checkSchema).default([]),
}).passthrough()
export type FactVersion = z.infer<typeof versionSchema>
export const runSchema = z.object({
  run_id: z.string(), document_id: z.string(), status: z.string(),
  mode: z.string(), created_at: z.string(), version_ids: z.array(z.string()).default([]),
}).passthrough()
export type Run = z.infer<typeof runSchema>
export const evidenceSchema = z.object({
  evidence_id: z.string(), document_id: z.string(), document_sha256: z.string(), text: z.string(),
  page_number: z.number().int().positive(),
  bbox: z.object({ left: z.number(), top: z.number(), right: z.number(), bottom: z.number(),
    origin: z.enum(['TOPLEFT', 'BOTTOMLEFT']) }).nullable().optional(),
  page_width: z.number().optional(), page_height: z.number().optional(),
}).passthrough()
export type Evidence = z.infer<typeof evidenceSchema>
export const evaluationSchema = z.object({
  evaluation_id: z.string(), version_id: z.string(), mode: z.string(), status: z.string(),
  eval_id: z.string().nullable().optional(), created_at: z.string(),
  result: z.object({
    verdict: z.object({ score: z.number().nullable(), decision: z.string(), confidence: z.string() }).passthrough(),
    verdicts: z.array(z.object({ criterion: z.string(), score: z.number().nullable(), critique: z.string() })),
  }).nullable().optional(),
}).passthrough()
export type Evaluation = z.infer<typeof evaluationSchema>
const scoreSchema = z.object({ correct: z.number().int().nonnegative(), total: z.number().int().positive() })
export const benchmarkSchema = z.object({
  benchmark_id: z.string(), split: z.string(), created_at: z.string(),
  document_count: z.number().int().nonnegative(), baseline: scoreSchema, revised: scoreSchema,
  regressions: z.number().int().nonnegative(), label_provenance: z.string(),
}).passthrough().refine(b => b.baseline.correct <= b.baseline.total && b.revised.correct <= b.revised.total,
  'Correct counts cannot exceed the denominator')
export type Benchmark = z.infer<typeof benchmarkSchema>
export const jobSchema = z.object({
  job_id: z.string(), status: z.string(), message: z.string().optional(),
  error: z.object({ message: z.string() }).nullable().optional(),
}).passthrough()
export type Job = z.infer<typeof jobSchema>
