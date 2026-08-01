import { useCallback, useEffect, useState } from 'react'
import {
  executeKnowledgeImproveCycle,
  executeKnowledgeSafeActions,
  fetchKnowledgeBenchmarkDiagnosis,
  fetchKnowledgeBenchmarkRuns,
  runKnowledgeBenchmarkAndWait,
  type KnowledgeBenchmarkDiagnosis,
  type KnowledgeBenchmarkRunSummary,
  type KnowledgeImprovementAction,
} from '../../api'
import { insightSeverityClass } from '../benchmarkUtils'

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
}

export function ImproveModule({ busy, setBusy, setError, setNotice }: Props) {
  const [runs, setRuns] = useState<KnowledgeBenchmarkRunSummary[]>([])
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null)
  const [diagnosis, setDiagnosis] = useState<KnowledgeBenchmarkDiagnosis | null>(null)

  const loadRuns = useCallback(async () => {
    const rows = await fetchKnowledgeBenchmarkRuns()
    setRuns(rows.filter((r) => r.status === 'succeeded'))
    if (rows.length && selectedRunId == null) {
      setSelectedRunId(rows[0].id)
    }
  }, [selectedRunId])

  const loadDiagnosis = useCallback(
    async (runId: number) => {
      setError(null)
      const d = await fetchKnowledgeBenchmarkDiagnosis(runId)
      setDiagnosis(d)
    },
    [setError],
  )

  useEffect(() => {
    void loadRuns().catch((err) => {
      setError(err instanceof Error ? err.message : 'failed to load runs')
    })
  }, [loadRuns, setError])

  useEffect(() => {
    if (selectedRunId == null) return
    void loadDiagnosis(selectedRunId).catch((err) => {
      setError(err instanceof Error ? err.message : 'diagnosis load failed')
    })
  }, [selectedRunId, loadDiagnosis, setError])

  const onRunBenchmark = async () => {
    setBusy(true)
    setError(null)
    try {
      const r = await runKnowledgeBenchmarkAndWait()
      setNotice(`Benchmark #${r.id} complete — loading diagnosis…`)
      await loadRuns()
      setSelectedRunId(r.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'benchmark failed')
    } finally {
      setBusy(false)
    }
  }

  const onExecuteSafe = async () => {
    if (!diagnosis?.diagnosis_id) return
    setBusy(true)
    setError(null)
    try {
      await executeKnowledgeSafeActions(diagnosis.diagnosis_id)
      setNotice('Safe L1 actions executed (crawl / catalog refresh)')
      if (selectedRunId) await loadDiagnosis(selectedRunId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'execute safe failed')
    } finally {
      setBusy(false)
    }
  }

  const onImproveCycle = async () => {
    setBusy(true)
    setError(null)
    try {
      const result = await executeKnowledgeImproveCycle(selectedRunId ?? undefined)
      const delta = result.score_delta
      setNotice(
        `Improve cycle done · before ${result.score_before} → after ${result.score_after ?? '…'}` +
          (delta != null ? ` (Δ ${delta >= 0 ? '+' : ''}${delta})` : ''),
      )
      await loadRuns()
      if (result.benchmark_run_id_after) {
        setSelectedRunId(result.benchmark_run_id_after)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'improve cycle failed')
    } finally {
      setBusy(false)
    }
  }

  const engineering = diagnosis?.engineering_tasks ?? []
  const actions = diagnosis?.actions ?? []
  const safePending = actions.filter((a) => a.auto_safe && a.status === 'proposed')

  return (
    <div className="kb-module kb-improve-module">
      <header className="kb-module-head">
        <div>
          <h3>Diagnose & improve</h3>
          <p className="mute">
            KB-DIAG-001 / KB-IMPROVE-001 — structured findings, auto crawl from authority sources, and
            engineering tasks for RAG upgrades.
          </p>
        </div>
        <div className="row kb-improve-actions">
          <button type="button" disabled={busy} onClick={() => void onRunBenchmark()}>
            Run benchmark
          </button>
          <button type="button" className="ghost" disabled={busy || !safePending.length} onClick={() => void onExecuteSafe()}>
            Execute safe actions ({safePending.length})
          </button>
          <button type="button" className="ghost" disabled={busy || !selectedRunId} onClick={() => void onImproveCycle()}>
            Full improve cycle
          </button>
        </div>
      </header>

      <div className="kb-improve-layout">
        <section className="kb-panel-card">
          <h4>Benchmark runs</h4>
          <div className="kb-table-wrap">
            <table className="kb-table">
              <thead>
                <tr>
                  <th>Run</th>
                  <th>Score</th>
                  <th>When</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr
                    key={r.id}
                    className={selectedRunId === r.id ? 'kb-row-selected' : undefined}
                    onClick={() => setSelectedRunId(r.id)}
                  >
                    <td>#{r.id}</td>
                    <td>{r.overall_score}</td>
                    <td className="mute">{r.created_at ? new Date(r.created_at).toLocaleString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="kb-panel-card kb-improve-main">
          {diagnosis ? (
            <>
              <p className="kb-improve-meta mute">
                Diagnosis #{diagnosis.diagnosis_id} · score {diagnosis.overall_score} ({diagnosis.grade})
                {diagnosis.score_delta != null ? ` · Δ ${diagnosis.score_delta}` : ''} ·{' '}
                {diagnosis.auto_safe_count} auto-safe / {diagnosis.action_count} actions
              </p>

              <h4>Findings</h4>
              <ul className="plain kb-improve-findings">
                {(diagnosis.items || []).map((item) => (
                  <li key={item.id} className={`kb-improve-item ${insightSeverityClass(item.severity)}`}>
                    <p className="kb-improve-item-head">
                      <code>{item.root_cause_code}</code> — {item.title}
                    </p>
                    <p className="mute">{item.detail}</p>
                  </li>
                ))}
              </ul>

              <h4>Actions</h4>
              <ul className="plain kb-improve-action-list">
                {actions.map((a: KnowledgeImprovementAction) => (
                  <li key={a.id} className="kb-improve-action-row">
                    <span className={a.auto_safe ? 'kb-gate-pill-ok' : 'kb-gate-pill-blocked'}>
                      {a.auto_safe ? 'L1 auto' : a.layer}
                    </span>
                    <code>{a.action_type}</code>
                    <span className={`kb-job-tag kb-job-tag-${a.status === 'succeeded' ? 'succeeded' : a.status === 'failed' ? 'failed' : 'running'}`}>
                      {a.status}
                    </span>
                    <span>{a.item_id}</span>
                  </li>
                ))}
              </ul>

              {engineering.length ? (
                <>
                  <h4>Engineering tasks (coding layer)</h4>
                  <ul className="plain kb-improve-eng">
                    {engineering.map((t) => (
                      <li key={t.item_id} className="kb-improve-eng-item">
                        <strong>{t.title}</strong>
                        <p className="mute">{t.detail}</p>
                        {t.payload?.files ? (
                          <p className="mute">
                            Files: {(t.payload.files as string[]).map((f) => (
                              <code key={f}>{f} </code>
                            ))}
                          </p>
                        ) : null}
                        {t.payload?.acceptance ? (
                          <p className="mute">Acceptance: {String(t.payload.acceptance)}</p>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </>
              ) : null}

              <h4>Diagnosis report</h4>
              <pre className="kb-bench-markdown">{diagnosis.markdown}</pre>
            </>
          ) : (
            <p className="mute">Select a benchmark run or run a new evaluation.</p>
          )}
        </section>
      </div>
    </div>
  )
}
