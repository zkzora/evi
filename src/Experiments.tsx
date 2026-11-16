import { useEffect, useState } from 'react'
import { ArrowDownToLine, ExternalLink, FlaskConical, Info, Loader2, TriangleAlert } from 'lucide-react'
import { api } from './api'
import { download } from './export'

type Arm = Record<string, number>
type Exp = {
  experiment_id: string; created_at: string; kind: string; base_experiment: string | null; model: string
  policies: Record<string, string>; corpus: { document_id: string; issuer: string; title: string; split: string; physical_pages: number[]; source_url: string }[]
  targets: number; trials: number; target_observations_per_arm: number; exposure_notes: string[]
  reference: { version: string; provenance: string; human_review_status: Record<string, number>; independently_reviewed: boolean }
  arms: Record<string, string>; measurements_analysis_v2: Record<string, Arm>; paired_analysis_v2: Record<string, Record<string, number>>
  checker_detection_analysis_v2: Record<string, number>; historical_scoring_v1: { by_arm: Record<string, Arm>; note: string }
  arm_A_error_causes_analysis_v2: Record<string, number>; finding: string
  costs: { reppo_credits_charged: number; serv_calls: number; serv_total_tokens: number; serv_usd: string }
  evaluations: { evaluation_id: string; reppo_eval_id: string; trial: number; document_id: string; evaluated_version_id: string; packet: string; score: number | null; decision: string; credits_charged: number; workspace_link: string | null }[]
  artifacts: Record<string, string>
}
type Pub = { limitations: string[]; docs: Record<string, string>; experiments: Exp[] }

const n = (a: Arm, k: string) => a?.[k] ?? 0
const pair = (p: Record<string, number> | undefined) => p ? `+${p.improvement ?? 0} / −${p.regression ?? 0}` : '—'

export default function Experiments() {
  const [data, setData] = useState<Pub | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    api.experiments().then(d => setData(d as unknown as Pub)).catch(e => setError(e instanceof Error ? e.message : 'The published experiments could not be loaded.'))
  }, [])
  if (error) return <div className="error-banner" role="alert"><TriangleAlert size={18}/><p>{error} No result has been substituted.</p></div>
  if (!data) return <div className="loading-block" role="status"><Loader2 className="spin" size={22}/><span>Loading published experiments…</span></div>
  return <div className="experiments">
    <section className="panel exp-intro"><div className="panel-title"><div><h2><FlaskConical size={18}/> Published experiments <span className="count">{data.experiments.length}</span></h2>
      <p>Counts come from the frozen experiment artifacts. Arms share targets; B reuses A's prediction.</p></div>
      <button className="button small" onClick={() => download(JSON.stringify(data, null, 2), 'evi-experiments.v1.json', 'application/json')}><ArrowDownToLine size={14}/> Download JSON</button></div>
      <ul className="exp-limits">{data.limitations.map(l => <li key={l}><Info size={13}/>{l}</li>)}</ul></section>
    {data.experiments.map(e => {
      const a = e.measurements_analysis_v2, h = e.historical_scoring_v1.by_arm, rev = e.reference.human_review_status
      const reviewed = Object.entries(rev).filter(([k]) => k !== 'pending').reduce((s, [, v]) => s + v, 0)
      return <article className="panel exp-card" key={e.experiment_id}>
        <div className="exp-head"><div><span className="eyebrow">{e.kind.toUpperCase()}</span><h3>{e.experiment_id}</h3>
          <p>{new Date(e.created_at).toISOString().slice(0, 10)} · model {e.model} · binding {e.policies.binding} · revision {e.policies.revision}{e.base_experiment ? ` · branches from ${e.base_experiment}` : ''}</p></div>
          <span className={`badge ${e.kind.startsWith('post-hoc') ? 'partial' : 'neutral'}`}><span className="status-dot"/>{e.kind.startsWith('post-hoc') ? 'Development evidence' : 'Frozen protocol'}</span></div>
        <div className="exp-finding"><strong>Finding.</strong> {e.finding}</div>
        <p className="exp-meta">{e.corpus.length} reports ({[...new Set(e.corpus.map(c => c.issuer))].join(', ')}) · {e.targets} targets × {e.trials} trials = {e.target_observations_per_arm} observations per arm · references {e.reference.version}: {e.reference.provenance} · human review {reviewed}/{e.targets} ({e.reference.independently_reviewed ? 'independently reviewed' : 'not independently reviewed'})</p>
        <div className="exp-table-scroll"><table className="exp-table"><thead><tr><th>Arm</th><th>What it adds</th><th title="All frozen fields equal the reference (start date derived from the model's own end date)">Reference match</th><th title="Reference match AND a supported certificate">Composite</th><th>Certificate supported<br/><small>of which dates unknown</small></th><th>Complete interval<br/><small>of targets with printed dates</small></th><th>Historical strict<br/><small>scoring-v1</small></th></tr></thead>
          <tbody>{(['A', 'B', 'C', 'D'] as const).map(k => <tr key={k}><td><b>{k}</b></td><td>{e.arms[k]}</td><td>{n(a[k], 'reference_match')} / {n(a[k], 'executed')}</td><td>{n(a[k], 'composite')} / {n(a[k], 'executed')}</td><td>{n(a[k], 'certificate_supported')} <small>({n(a[k], 'certificate_supported_exact_dates_unknown')})</small></td><td>{n(a[k], 'complete_interval')} / {n(a[k], 'reference_interval_known')}</td><td>{n(h[k], 'strict_correct')} / {n(h[k], 'executed')}</td></tr>)}</tbody></table></div>
        <div className="exp-grid">
          <div><h4>Paired changes (improvements / regressions)</h4><p>Reference match: A→C {pair(e.paired_analysis_v2['reference_match:A->C'])}, A→D {pair(e.paired_analysis_v2['reference_match:A->D'])}, <b>C→D {pair(e.paired_analysis_v2['reference_match:C->D'])}</b></p>
            <p>Composite: A→C {pair(e.paired_analysis_v2['composite:A->C'])}, A→D {pair(e.paired_analysis_v2['composite:A->D'])}, <b>C→D {pair(e.paired_analysis_v2['composite:C->D'])}</b></p></div>
          <div><h4>Checker vs reference (arm B)</h4><p>Detected errors {e.checker_detection_analysis_v2.TP ?? 0} · false alarms {e.checker_detection_analysis_v2.FP ?? 0} · missed {e.checker_detection_analysis_v2.FN ?? 0} · correct passes {e.checker_detection_analysis_v2.TN ?? 0}</p></div>
          <div><h4>Arm A non-matching causes</h4>{Object.entries(e.arm_A_error_causes_analysis_v2).map(([c, v]) => <p key={c}>{v} × {c}</p>)}</div>
          <div><h4>Recorded cost</h4><p>Reppo {e.costs.reppo_credits_charged} credits · SERV {e.costs.serv_calls} calls, {e.costs.serv_total_tokens.toLocaleString('en-US')} tokens ({e.costs.serv_usd})</p></div>
        </div>
        <p className="exp-note">{e.historical_scoring_v1.note}. Unknown exact dates can be faithful to the source without being a complete interval.</p>
        {e.evaluations.length > 0 && <details className="exp-evals"><summary>{e.evaluations.length} real Reppo evaluations used by arm D</summary><ul>{e.evaluations.map(v => <li key={v.evaluation_id}>Trial {v.trial} · {v.document_id} · score {v.score ?? 'not returned'} ({v.decision}) · {v.credits_charged} credits · {v.packet} · evaluated <code>{v.evaluated_version_id}</code>{v.workspace_link && <> · <a href={v.workspace_link}>open evaluated version</a></>}</li>)}</ul><p>A Reppo score is an evaluator opinion, not extraction accuracy.</p></details>}
        {e.evaluations.length === 0 && e.base_experiment && <p className="exp-note">Arm D reused the 10 completed Reppo evaluations of {e.base_experiment} (same evaluated versions), so no new credits were charged.</p>}
        {e.exposure_notes.length > 0 && <details className="exp-evals"><summary>Exposure notes</summary><ul>{e.exposure_notes.map(x => <li key={x}>{x}</li>)}</ul></details>}
        <div className="exp-artifacts">{Object.entries(e.artifacts).map(([name, href]) => <a key={name} href={href} target="_blank" rel="noreferrer">{name} <ExternalLink size={11}/></a>)}</div>
      </article>
    })}
  </div>
}
