import { useEffect, useState } from 'react'
import { CheckCheck, ExternalLink, Info, ShieldCheck, TriangleAlert } from 'lucide-react'
import { api } from './api'

type Obligation = { id: string; status: string; reason: string; evidence: string[] }
type Edge = { rel: string; src: string; rule: string; note: string }
type Cert = {
  claim_outcome: string; content_sha256: string; policy_version: string
  resolution: { outcome: string; reason: string; candidates: unknown[] }
  claim_cell_reading: { tuple: Record<string, string | number | null>; obligations: Obligation[]; edges: Edge[]; row_label: string | null } | null
  field_verdicts: { field: string; status: string; reason: string }[]
  source: { sha256: string }; parse: { parse_id: string }
  coverage?: { complete_required_context: boolean; unique_supported_reading: boolean; exact_interval: string; label: string; unknown_fields: string[] }
}
type Decision = { target_key: string; decision: string; why: string; field_transitions?: Record<string, string> }

const OB_LABEL: Record<string, string> = {
  S1: 'Source & parse identity', S2: 'Value cell text', M1: 'Metric row', M2: 'Consolidation / attribution scope',
  P1: 'Year column', P2: 'Interval heading', P3: 'Exact dates', U1: 'Currency', U2: 'Scale applies to this cell',
  N1: 'Number convention', N2: 'Normalization', C1: 'No conflicting context',
}
const icon = (s: string) => s === 'pass' ? <CheckCheck size={14}/> : s === 'fail' ? <TriangleAlert size={14}/> : <Info size={14}/>

export default function CertificatePanel({ versionId, factId, targetKey }: { versionId: string; factId: string; targetKey?: string }) {
  const [certId, setCertId] = useState('')
  const [cert, setCert] = useState<Cert | null>(null)
  const [decision, setDecision] = useState<Decision | null>(null)
  const [verify, setVerify] = useState<{ verified: boolean; problems: string[] } | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    setCert(null); setCertId(''); setVerify(null); setDecision(null); setError('')
    api.certificates(versionId).then(async list => {
      // Newest checker policy first; older certificates remain verifiable under their own recorded policy.
      const mine = list.items.filter(c => c.fact_id === factId)
        .sort((a, b) => a.policy_version.localeCompare(b.policy_version, undefined, { numeric: true })).at(-1)
      if (!mine) { if (active) setError('No support certificate was issued for this fact.'); return }
      const body = await api.certificate(mine.certificate_id)
      if (active) { setCertId(mine.certificate_id); setCert(body as Cert) }
    }).catch(() => { if (active) setError('Certificate unavailable.') })
    api.receipt(versionId).then(r => {
      const d = (r.decisions as Decision[] | undefined)?.find(x => x.target_key === targetKey)
      if (active && d) setDecision(d)
    }).catch(() => undefined)
    return () => { active = false }
  }, [versionId, factId, targetKey])
  if (error) return <div className="cert-panel"><p className="cert-muted">{error}</p></div>
  if (!cert) return null
  const reading = cert.claim_cell_reading
  const t = reading?.tuple || {}
  const paths = (reading?.edges || []).filter(e => !['in_table', 'on_page'].includes(e.rel))
  const runVerify = async () => { setBusy(true); try { setVerify(await api.verifyCertificate(certId)) } catch { setVerify({ verified: false, problems: ['Verification request failed.'] }) } finally { setBusy(false) } }
  return <div className="cert-panel">
    <div className="cert-head"><ShieldCheck size={16}/><h4>Source-support certificate</h4>
      <span className={`cert-badge ${cert.coverage && cert.coverage.unique_supported_reading && !cert.coverage.complete_required_context ? 'partial' : cert.claim_outcome}`}>{cert.coverage && cert.coverage.unique_supported_reading && !cert.coverage.complete_required_context ? 'Supported · partial context' : cert.claim_outcome.replaceAll('_', ' ')}</span></div>
    {cert.coverage && <p className="cert-coverage" data-complete={String(cert.coverage.complete_required_context)}>{cert.coverage.label}{cert.coverage.unknown_fields.length ? ` (unknown: ${cert.coverage.unknown_fields.join(', ').replaceAll('_', ' ')})` : ''}</p>}
    <p className="cert-muted">Resolver: {cert.resolution.outcome} ({cert.resolution.reason.replaceAll('_', ' ')}) · {cert.resolution.candidates.length} candidate cell(s) · policy {cert.policy_version}</p>
    {t.amount != null && <p className="cert-ops"><code>{String(t.amount_text)}</code> × <code>{String(t.unit_scale)}</code> = <strong>{String(t.normalized_value)}</strong> {String(t.currency || '')}
      {t.duration_months ? <> · {String(t.duration_months)} months, FY{String(t.fiscal_year)}{t.end_date ? `, ${t.start_date} → ${t.end_date}` : ', end date not printed'}</> : null}</p>}
    <div className="cert-grid">{(reading?.obligations || []).map(o => <div key={o.id} className={`cert-ob ${o.status}`} title={o.reason}>{icon(o.status)}<b>{o.id}</b><span>{OB_LABEL[o.id]}</span><em>{o.reason.replaceAll('_', ' ')}</em></div>)}</div>
    {cert.field_verdicts.some(v => v.status !== 'pass') && <div className="cert-fields"><h5>Claim fields failed or unknown</h5>{cert.field_verdicts.filter(v => v.status !== 'pass').map(v => <p key={v.field}>{icon(v.status)} {v.field.replaceAll('_', ' ')} — {v.reason.replaceAll('_', ' ')}</p>)}</div>}
    <details className="cert-paths"><summary>Applicability paths ({paths.length})</summary>{paths.map((e, i) => <p key={i}><code>{e.rel}</code> {e.note} <small>{e.rule}</small></p>)}</details>
    {decision && <div className="cert-fields"><h5>Revision decision for this target</h5><p>{decision.decision}: {decision.why.replaceAll('_', ' ')}</p>
      {decision.field_transitions && Object.entries(decision.field_transitions).map(([k, v]) => <p key={k}><code>{k}</code> {v}</p>)}</div>}
    <div className="cert-actions"><button className="button small" disabled={busy} onClick={runVerify}>{busy ? 'Verifying…' : 'Re-verify from source'}</button>
      <a className="cert-link" href={api.certificateUrl(certId)} target="_blank" rel="noreferrer">Certificate JSON <ExternalLink size={12}/></a>
      <code className="cert-hash">{cert.content_sha256.slice(0, 16)}</code></div>
    {verify && <p className={`cert-verify ${verify.verified ? 'ok' : 'bad'}`}>{verify.verified ? 'Verified: recomputed from the registered PDF bytes and Docling artifact.' : `Not verified: ${verify.problems.join('; ')}`}</p>}
    <p className="cert-muted">Certifies the documented applicability rules over this source, not the issuer's accounting.</p>
  </div>
}
