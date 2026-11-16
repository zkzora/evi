import { useState } from 'react'
import { ArrowLeft, ArrowRight, ChevronDown, ChevronUp, RotateCcw, X } from 'lucide-react'
import type { Capabilities } from './api'
import { sourceManifest } from './source-data'

// Reproducible deep links into STORED records (original timestamps); none of them triggers processing.
const periodCase = sourceManifest.cases.find(c => c.id === 'verizon-period') ?? sourceManifest.cases[0]
const data = (params: Record<string, string>) => `/data?${new URLSearchParams({ company: periodCase.long.company, source_case: periodCase.id, ...params })}`
const ws = (document: string, run: string, version: string, fact: string) => `/workspace?${new URLSearchParams({ document, run, version, fact })}`
export const tourLinks = {
  periodFullYear: data({ expect_period: '12', expect_unit: 'USD', check: '1' }),
  periodNine: data({ expect_period: '9', expect_unit: 'USD', check: '1' }),
  unitMismatch: data({ expect_period: '9', expect_unit: 'USD millions', check: '1' }),
  process: '/workspace?document=verizon-3q2025',
  verizon3q: ws('verizon-3q2025', 'run_3f60316ec62f4d0bb449', 'ver_3f60316ec62f_5', 'run_3f60316ec62f4d0bb449:r5:verizon-3q2025:revenue:3M:2025'),
  verizonFy2024: ws('verizon-fy2024', 'run_b15ed73528114efe9b3e', 'ver_b15ed7352811_5', 'run_b15ed73528114efe9b3e:verizon-fy2024:revenue:12M:2024'),
  att2q: ws('att-2q2025', 'run_325e06e62b8c46e58b4d', 'ver_325e06e62b8c_5', 'run_325e06e62b8c46e58b4d:att-2q2025:revenue:3M:2025'),
  feedback: '/feedback',
  benchmark: '/benchmark',
}
const withTour = (href: string, step: number) => { const u = new URL(href, location.origin); u.searchParams.set('tour', String(step)); return u.pathname + u.search }
export const startTour = () => location.assign(withTour(tourLinks.periodFullYear, 1))

type Step = { title: string; body: (caps?: Capabilities) => string; links: [string, string][] }
const steps: Step[] = [
  { title: 'Catch a period mismatch',
    body: () => `${periodCase.long.company_name} revenue for ${periodCase.long.start} → ${periodCase.long.end} (SEC filing ${periodCase.long.accession}) is a nine-month figure. Checked as "Full year", the interval check fails; checked as "9 months", it passes. Choosing "USD millions" fails the unit check because the source value is in base USD. This is a rule check on published source metadata in your browser, not an AI extraction.`,
    links: [['Check as Full year', tourLinks.periodFullYear], ['Check as 9 months', tourLinks.periodNine], ['Try a unit mismatch', tourLinks.unitMismatch]] },
  { title: 'Run a real extraction',
    body: caps => caps?.extraction.state === 'available'
      ? 'Processing is available on this server. Choose a report and press "Process report": the job runs Docling (or reuses a cached parse, which is labelled), then one SERV extraction, then the source checks. Stages appear as they actually happen.'
      : `New processing is not available here: ${caps?.extraction.reason ?? 'the processing service is not connected.'} The workspace shows stored results from earlier real runs with their original timestamps. Nothing is re-run.`,
    links: [['Open the workspace', tourLinks.process]] },
  { title: 'Inspect the evidence',
    body: () => 'Open a fact: the Value, Metric, Period and Unit tabs highlight the cells on the original PDF page. "Re-verify from source" recomputes the certificate on the server from the registered PDF bytes and Docling output (no AI call). AT&T statements print no end date, so Evi shows "dates not printed" instead of guessing.',
    links: [['Verizon 3Q 2025 (complete context)', tourLinks.verizon3q], ['Verizon FY2024 (offset page coordinates)', tourLinks.verizonFy2024], ['AT&T 2Q 2025 (partial context)', tourLinks.att2q]] },
  { title: 'Evaluations and revisions',
    body: caps => `Every recorded Reppo evaluation is listed with the exact version it judged. Revisions may change nothing; that outcome is shown too. ${caps?.evaluation.state === 'available' ? 'New evaluations are enabled on this server within its allowance.' : 'New evaluations are not enabled here.'}`,
    links: [['Open evaluation history', tourLinks.feedback]] },
  { title: 'Measured evidence',
    body: () => 'The published experiments compare four arms on the same targets. The headline is a null result: real Reppo feedback (arm D) did not improve on the same revision without it (arm C). References are provisional until human review completes.',
    links: [['Open published experiments', tourLinks.benchmark]] },
]

export default function Tour({ step, caps, close, side = 'right' }: { step: number; caps?: Capabilities; close: () => void; side?: 'left' | 'right' }) {
  const [min, setMin] = useState(false)
  const s = steps[step - 1]
  if (!s) return null
  if (min) return <button className={`tour-pill ${side}`} onClick={() => setMin(false)}><ChevronUp size={14}/> Try Evi · step {step} / {steps.length}</button>
  return <aside className={`tour-card ${side}`} role="dialog" aria-label={`Try Evi, step ${step} of ${steps.length}`}>
    <div className="tour-head"><span>TRY EVI · STEP {step} / {steps.length}</span><span><button className="icon-button" aria-label="Minimize walkthrough" onClick={() => setMin(true)}><ChevronDown size={15}/></button><button className="icon-button" aria-label="Close walkthrough" onClick={close}><X size={15}/></button></span></div>
    <h3>{s.title}</h3>
    <p>{s.body(caps)}</p>
    <div className="tour-links">{s.links.map(([label, href]) => <a key={href} className="button small" href={withTour(href, step)}>{label}</a>)}</div>
    <div className="tour-nav">
      {step > 1 ? <a className="text-button" href={withTour(steps[step - 2].links[0][1], step - 1)}><ArrowLeft size={13}/> Back</a> : <span/>}
      <a className="text-button" href={withTour(tourLinks.periodFullYear, 1)} title="Restart the walkthrough (records are not changed)"><RotateCcw size={13}/> Restart</a>
      {step < steps.length ? <a className="button small primary" href={withTour(steps[step].links[0][1], step + 1)}>Next <ArrowRight size={13}/></a>
        : <button className="button small primary" onClick={close}>Done</button>}
    </div>
  </aside>
}
