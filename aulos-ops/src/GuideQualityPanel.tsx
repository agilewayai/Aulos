import { useCallback, useEffect, useState } from 'react'
import {
  fetchGuideScorecards,
  fetchOpsGuideTrace,
  promoteCandidateToProduction,
  stagePromoteCandidate,
  type GuideScorecardSummary,
} from './api'
import { formatDateTime } from './time'

type Trace = Awaited<ReturnType<typeof fetchOpsGuideTrace>>

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
}

export function GuideQualityPanel({ busy, setBusy, setError, setNotice }: Props) {
  const [items, setItems] = useState<GuideScorecardSummary[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [trace, setTrace] = useState<Trace | null>(null)

  const load = useCallback(async () => {
    setBusy(true)
    setError(null)
    try {
      const data = await fetchGuideScorecards(50)
      setItems(data.items)
      setNotice(`Loaded ${data.total} guide scorecard summaries`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scorecards')
    } finally {
      setBusy(false)
    }
  }, [setBusy, setError, setNotice])

  useEffect(() => {
    void load()
  }, [load])

  async function openRow(id: number) {
    setSelectedId(id)
    setBusy(true)
    setError(null)
    try {
      const t = await fetchOpsGuideTrace(id)
      setTrace(t)
    } catch (err) {
      setTrace(null)
      setError(err instanceof Error ? err.message : 'Trace fetch failed')
    } finally {
      setBusy(false)
    }
  }

  async function stageCraft(id: number) {
    setBusy(true)
    setError(null)
    try {
      const out = await stagePromoteCandidate(id, false)
      setNotice(`Staged craft ${out.suggested_work_id} → ${out.staged_path}`)
      const t = await fetchOpsGuideTrace(id)
      setTrace(t)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Promote stage failed')
    } finally {
      setBusy(false)
    }
  }

  async function promoteProduction(id: number) {
    setBusy(true)
    setError(null)
    try {
      const out = await promoteCandidateToProduction(id, false)
      setNotice(
        `Promoted ${out.report.work_id} → Catalog + craft (system pipeline, not a case patch)`,
      )
      const t = await fetchOpsGuideTrace(id)
      setTrace(t)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Promote to production failed')
    } finally {
      setBusy(false)
    }
  }

  const promote = trace?.promote_candidate

  return (
    <section className="settings guide-quality" aria-labelledby="guide-quality-title">
      <div className="section-head">
        <div>
          <h2 id="guide-quality-title">Guide quality</h2>
          <p className="settings-lead">
            Process scorecards + dimensional unknown-case promote (SPEC-019/030/031).
            Engine is facet→dimension→stage→production — not per-work patches.
          </p>
        </div>
        <button type="button" className="refresh" disabled={busy} onClick={() => void load()}>
          Refresh
        </button>
      </div>

      <div className="gq-table-wrap">
        <table className="gq-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Work</th>
              <th>Composer</th>
              <th>Pct</th>
              <th>Band</th>
              <th>Asset</th>
              <th>Promote</th>
              <th>Eval</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={9} className="mute">
                  No guides yet.
                </td>
              </tr>
            ) : (
              items.map((row) => (
                <tr
                  key={row.guide_id}
                  className={selectedId === row.guide_id ? 'active' : ''}
                  onClick={() => void openRow(row.guide_id)}
                >
                  <td>#{row.guide_id}</td>
                  <td>{row.work_title || '—'}</td>
                  <td>{row.composer || '—'}</td>
                  <td>{row.has_scorecard ? `${row.pct ?? '—'}%` : '—'}</td>
                  <td>
                    <span className={`gq-band band-${row.band || 'unknown'}`}>{row.band || 'unknown'}</span>
                  </td>
                  <td>
                    {row.asset_depth != null
                      ? `${row.asset_depth}${row.product_band ? ` · ${row.product_band}` : ''}`
                      : '—'}
                  </td>
                  <td>
                    {row.has_promote_candidate ? row.promote_status || 'candidate' : '—'}
                  </td>
                  <td>{row.eval_pass == null ? '—' : row.eval_pass ? 'pass' : 'fail'}</td>
                  <td>{row.created_at ? formatDateTime(row.created_at) : '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {selectedId && promote ? (
        <div className="gq-detail gq-promote">
          <h3>
            Promote candidate · {promote.suggested_work_id || '—'} ·{' '}
            {promote.status || (promote.dry_run ? 'dry-run' : 'candidate')}
          </h3>
          <p className="mute">
            family {promote.family_id || '—'}
            {trace?.synthesize_source ? ` · ${trace.synthesize_source}` : ''}
            {trace?.facet_classification?.archetype_id
              ? ` · archetype ${trace.facet_classification.archetype_id}`
              : ''}
          </p>
          {promote.craft_draft?.listening_thesis ? (
            <p>{promote.craft_draft.listening_thesis}</p>
          ) : null}
          {promote.craft_draft?.zh?.listening_thesis ? (
            <p className="mute">{promote.craft_draft.zh.listening_thesis}</p>
          ) : null}
          {promote.staged_path && promote.status !== 'production' ? (
            <div className="gq-promote-actions">
              <p className="mute">Staged: {promote.staged_path}</p>
              <button
                type="button"
                disabled={busy}
                onClick={() => void promoteProduction(selectedId)}
              >
                Promote to production (Catalog + craft)
              </button>
            </div>
          ) : null}
          {promote.status === 'production' ? (
            <p className="mute">
              Production: {promote.suggested_work_id}
              {typeof promote.production_craft_path === 'string'
                ? ` · ${promote.production_craft_path}`
                : ''}
            </p>
          ) : null}
          {!promote.staged_path && promote.status !== 'production' ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => void stageCraft(selectedId)}
            >
              Stage craft (staging only)
            </button>
          ) : null}
        </div>
      ) : null}

      {trace?.process_scorecard ? (
        <div className="gq-detail">
          <h3>
            #{trace.guide_id} · {trace.work_title} · rollup{' '}
            {trace.process_scorecard.rollup?.pct ?? '—'}% (
            {trace.process_scorecard.rollup?.band || '—'})
          </h3>
          <ul className="gq-nodes">
            {(trace.process_scorecard.nodes || []).map((n) => (
              <li key={n.trigger}>
                <strong>{n.trigger.replace(/^listening\./, '')}</strong> {n.pct}% · {n.band}
                {n.scores ? (
                  <span className="mute">
                    {' '}
                    (
                    {Object.entries(n.scores)
                      .map(([k, v]) => `${k}:${v}`)
                      .join(' · ')}
                    )
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
          {trace.process_scorecard.product?.scores ? (
            <p className="mute">
              Product dims:{' '}
              {Object.entries(trace.process_scorecard.product.scores)
                .map(([k, v]) => `${k}=${v}`)
                .join(' · ')}
            </p>
          ) : null}
          {trace.product_scorecard?.dimensions ? (
            <p className="mute">
              ProductScorecard:{' '}
              {Object.entries(trace.product_scorecard.dimensions)
                .map(([k, v]) => `${k}=${v}`)
                .join(' · ')}
              {trace.product_scorecard.band ? ` · ${trace.product_scorecard.band}` : ''}
            </p>
          ) : null}
        </div>
      ) : selectedId && !promote ? (
        <p className="mute">No process_scorecard on guide #{selectedId} yet.</p>
      ) : null}
    </section>
  )
}
