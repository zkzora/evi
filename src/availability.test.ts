import { describe, expect, it } from 'vitest'
import { capabilityLabel } from './availability'
import { tourLinks } from './Tour'
import type { Capabilities } from './api'

const caps = (state: Capabilities['extraction']['state'], mode = 'live'): Capabilities => ({
  mode, stored_results: { available: true }, source_verification: { available: true, reason: '' },
  extraction: { state, reason: 'r' }, evaluation: { state: 'unavailable', reason: 'r' },
})

describe('capability-based availability', () => {
  it('never reports processing from connectivity alone', () => {
    expect(capabilityLabel('connected', caps('unavailable', 'archive')).text).toBe('Archive · stored results')
    expect(capabilityLabel('connected', caps('unavailable', 'archive')).text).not.toMatch(/connected|available/i)
    expect(capabilityLabel('connected', caps('available')).text).toBe('Live processing available')
    expect(capabilityLabel('connected', caps('busy')).text).toMatch(/busy/)
    expect(capabilityLabel('connected', caps('budget_exhausted')).text).toMatch(/allowance used/)
    expect(capabilityLabel('offline').text).toMatch(/offline/)
  })
  it('walkthrough deep links point at stored records and a real nine-month case', () => {
    expect(tourLinks.periodFullYear).toContain('expect_period=12')
    expect(tourLinks.periodNine).toContain('expect_period=9')
    expect(tourLinks.unitMismatch).toContain('expect_unit=USD+millions')
    expect(tourLinks.verizonFy2024).toContain('version=ver_b15ed7352811_5')
    for (const href of Object.values(tourLinks)) expect(href).not.toMatch(/parse|process\b/)
  })
})
