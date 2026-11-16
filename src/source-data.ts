import { z } from 'zod'
import manifestJSON from './data-manifest.json'

export const sourceManifest = manifestJSON
export type SourceCompany = typeof sourceManifest.companies[number]
export type SourceCase = typeof sourceManifest.cases[number]
const conceptSchema = z.object({ namespace: z.string(), tag: z.string(), label: z.string(), description: z.string(), metric: z.string().nullable() })
const rowSchema = z.tuple([z.number().int().nonnegative(), z.string(), z.string().nullable(), z.string(), z.string(), z.string(), z.string(), z.string(), z.number().nullable(), z.string().nullable(), z.string().nullable(), z.number().int().nonnegative()])
export const sourcePayloadSchema = z.object({ company: z.string(), cik: z.string(), concepts: z.array(conceptSchema), rows: z.array(rowSchema) })
export type SourcePayload = z.infer<typeof sourcePayloadSchema>
export type SourceRow = z.infer<typeof rowSchema>
export function periodDays(start: string | null, end: string): number | null {
  if (!start) return null
  const days = Math.round((Date.parse(`${end}T00:00:00Z`) - Date.parse(`${start}T00:00:00Z`)) / 86400000) + 1
  return Number.isFinite(days) && days > 0 ? days : null
}
export function periodMonths(start: string | null, end: string): number | null {
  const days = periodDays(start, end)
  if (days === null) return null
  return [[3, 60, 120], [6, 150, 210], [9, 240, 310], [12, 330, 400]].find(([, low, high]) => days >= low && days <= high)?.[0] ?? null
}
export function periodLabel(start: string | null, end: string): string {
  if (!start) return 'Point in time'
  const months = periodMonths(start, end)
  return months ? `${months} months` : `${periodDays(start, end) ?? 'Unknown'} days`
}
export function exactAmount(value: string, scale = 0): string {
  // Shift the decimal as text: do not convert financial values to floating-point numbers.
  const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(value)
  if (!match) return value
  const [, sign, whole, fraction = ''] = match
  const digits = whole.padStart(scale + 1, '0')
  const integer = scale ? digits.slice(0, -scale) : digits
  const decimal = `${scale ? digits.slice(-scale) : ''}${fraction}`.replace(/0+$/, '')
  return `${sign}${integer.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}${decimal ? `.${decimal}` : ''}`
}
export function contextCheck(start: string | null, end: string, sourceUnit: string, expectedMonths: string, expectedUnit: string) {
  const days = periodDays(start, end)
  const months = periodMonths(start, end)
  const period = expectedMonths === 'instant' ? !start ? 'pass' : 'fail' : !start || days === null || months === null ? 'unknown' : months === Number(expectedMonths) ? 'pass' : 'fail'
  return { period, unit: sourceUnit === expectedUnit ? 'pass' : 'fail', days, months } as const
}
export function filingURL(cik: string, accession: string) {
  return `https://www.sec.gov/Archives/edgar/data/${cik}/${accession.replaceAll('-', '')}/${accession}-index.html`
}
export function sourceLabel(concept: { label: string; metric: string | null }) {
  const labels: Record<string, string> = { revenue: 'Revenue', operating_profit: 'Operating profit', profit_attributable_to_owners: 'Profit attributable to owners' }
  return concept.metric ? labels[concept.metric] || concept.label : concept.label
}
export const number = (n: number) => n.toLocaleString('en-US')
