import { z } from 'zod'
import { benchmarkSchema, documentSchema, evaluationSchema, evidenceSchema, jobSchema, runSchema, versionSchema } from './types'

const base = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '')
export class ApiError extends Error {
  constructor(message: string, public status = 0) { super(message); this.name = 'ApiError' }
}
export async function request<T>(path: string, schema: z.ZodType<T>, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${base}${path}`, { ...init, credentials: 'same-origin',
      headers: { Accept: 'application/json', ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...init?.headers },
      signal: init?.signal ?? AbortSignal.timeout(15000) })
  } catch { throw new ApiError('The processing service is unavailable. Your source documents are still accessible.') }
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new ApiError('The processing service is not connected yet.', response.status)
  }
  const body: unknown = await response.json()
  if (!response.ok) {
    const failure = z.object({ error: z.object({ message: z.string() }) }).safeParse(body)
    throw new ApiError(failure.success ? failure.data.error.message : `Request could not complete (${response.status}).`, response.status)
  }
  const result = schema.safeParse(body)
  if (!result.success) throw new ApiError('The service returned an unsupported response. No results have been substituted.', response.status)
  return result.data
}
const items = <T>(schema: z.ZodType<T>) => z.object({ items: z.array(schema) })
const post = (body: unknown) => ({ method: 'POST', body: JSON.stringify(body) })
export const api = {
  health: () => request('/health', z.object({ status: z.enum(['ok', 'ready']), live_execution_enabled: z.boolean().default(false), processing_enabled: z.boolean().default(false) }).passthrough()),
  documents: () => request('/documents', items(documentSchema)),
  runs: (id: string) => request(`/runs?document_id=${encodeURIComponent(id)}`, items(runSchema)),
  version: (id: string) => request(`/versions/${encodeURIComponent(id)}`, versionSchema),
  evidence: (id: string) => request(`/evidence/${encodeURIComponent(id)}`, evidenceSchema),
  parse: (id: string) => request(`/documents/${encodeURIComponent(id)}/parse`, jobSchema, post({})),
  extract: (id: string, parseId: string) => request('/runs', jobSchema, post({ document_id: id, parse_id: parseId,
    policy_version: 'period-unit-v1', metrics: ['revenue', 'operating_profit', 'profit_attributable_to_owners'], mode: 'live' })),
  job: (id: string) => request(`/jobs/${encodeURIComponent(id)}`, jobSchema),
  evaluations: () => request('/evaluations', items(evaluationSchema)),
  evaluate: (id: string) => request(`/versions/${encodeURIComponent(id)}/evaluations`, jobSchema, post({ mode: 'reppo_live' })),
  refreshEvaluation: (id: string) => request(`/evaluations/${encodeURIComponent(id)}/refresh`, jobSchema, post({})),
  revise: (versionId: string, evaluationId: string) => request(`/versions/${encodeURIComponent(versionId)}/revisions`, jobSchema,
    post({ evaluation_id: evaluationId })),
  benchmarks: () => request('/benchmarks', items(benchmarkSchema)),
  certificates: (versionId: string) => request(`/versions/${encodeURIComponent(versionId)}/certificates`, items(z.object({
    certificate_id: z.string(), fact_id: z.string().nullable(), target_key: z.string(), policy_version: z.string(),
    claim_outcome: z.string(), resolution_outcome: z.string(), content_sha256: z.string() }).passthrough())),
  certificate: (id: string) => request(`/certificates/${encodeURIComponent(id)}`, z.record(z.string(), z.unknown())),
  verifyCertificate: (id: string) => request(`/certificates/${encodeURIComponent(id)}/verification`,
    z.object({ verified: z.boolean(), problems: z.array(z.string()) }).passthrough()),
  receipt: (versionId: string) => request(`/versions/${encodeURIComponent(versionId)}/receipt`, z.record(z.string(), z.unknown())),
  reviseWithoutFeedback: (versionId: string) => request(`/versions/${encodeURIComponent(versionId)}/revisions`, jobSchema, post({ arm: 'C' })),
  certificateUrl: (id: string) => `${base}/certificates/${encodeURIComponent(id)}`,
  source: (id: string) => `${base}/documents/${encodeURIComponent(id)}/source`,
}
