import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { describe, expect, it } from 'vitest'
import { sourceManifest, sourcePayloadSchema } from './source-data'

describe('downloaded SEC corpus integrity', () => {
  it('validates every company shard and reconciles exact source counts and hashes', () => {
    let total = 0
    for (const company of sourceManifest.companies) {
      const normalized = readFileSync(`public${company.data_path}`)
      const original = readFileSync(`public${company.source_snapshot}`)
      const parsed = sourcePayloadSchema.parse(JSON.parse(normalized.toString()))
      expect(createHash('sha256').update(original).digest('hex')).toBe(company.source_sha256)
      expect(createHash('sha256').update(normalized).digest('hex')).toBe(company.data_sha256)
      expect(parsed.rows.length).toBe(company.observation_count)
      expect(parsed.rows.every(row => row[1] === 'USD')).toBe(true)
      expect(parsed.rows.every(row => Boolean(parsed.concepts[row[0]]))).toBe(true)
      total += parsed.rows.length
    }
    expect(total).toBe(sourceManifest.total_observations)
  })
  it('traces the featured comparisons back to the exact original SEC array entries', () => {
    for (const item of sourceManifest.cases) {
      for (const observation of [item.short, item.long]) {
        const company = sourceManifest.companies.find(c => c.id === observation.company)!
        const source = JSON.parse(readFileSync(`public${company.source_snapshot}`, 'utf8'))
        const original = source.facts[observation.taxonomy][observation.tag].units[observation.unit][observation.source_index]
        expect(String(original.val)).toBe(observation.value)
        expect(original.start).toBe(observation.start)
        expect(original.end).toBe(observation.end)
        expect(original.accn).toBe(observation.accession)
      }
    }
  })
})


describe('USD PDF scale case', () => {
  it('matches the featured annual revenue to the original SEC USD value', () => {
    const source = JSON.parse(readFileSync('public/datasets/verizon-source.json', 'utf8'))
    const row = source.facts['us-gaap'].Revenues.units.USD.find((item: { start: string; end: string; accn: string }) => item.start === '2025-01-01' && item.end === '2025-12-31' && item.accn === '0000732712-26-000007')
    expect(row.val).toBe(138191000000)
    expect(BigInt(138191) * BigInt(1000000)).toBe(BigInt(row.val))
  })
})
