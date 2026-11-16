import type { Capabilities } from './api'

// Status text derived ONLY from server-reported capabilities; connectivity alone never implies processing.
export function capabilityLabel(connection: string, caps?: Capabilities) {
  if (connection === 'checking') return { text: 'Checking availability', tone: 'checking' }
  if (connection !== 'connected') return { text: 'Service offline · source PDFs only', tone: 'offline' }
  if (!caps) return { text: 'Stored results', tone: 'connected' }
  const x = caps.extraction.state
  if (x === 'available') return { text: 'Live processing available', tone: 'live' }
  if (x === 'busy') return { text: 'Processing busy · stored results available', tone: 'busy' }
  const code = (caps.extraction as { code?: string | null }).code
  if (code === 'allowance_exhausted') return { text: 'Processing allowance used · stored results available', tone: 'archive' }
  if (code === 'allowance_expired') return { text: 'Processing allowance ended · stored results available', tone: 'archive' }
  if (code === 'no_allowance' || code === 'allowance_not_started') return { text: 'No processing allowance · stored results available', tone: 'archive' }
  if (x === 'budget_exhausted') return { text: 'Processing allowance used today', tone: 'busy' }
  return { text: caps.mode === 'archive' ? 'Archive · stored results' : 'Processing unavailable · stored results', tone: 'archive' }
}
