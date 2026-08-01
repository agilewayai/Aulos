import { useCallback, useEffect, useState } from 'react'
import {
  fetchKnowledgeBenchmarkRun,
  fetchKnowledgeBenchmarkRuns,
  fetchKnowledgeBenchmarkSuite,
  runKnowledgeBenchmarkAndWait,
  type KnowledgeBenchmarkReport,
  type KnowledgeBenchmarkRunSummary,
  type KnowledgeBenchmarkSuite,
} from '../../api'
import { gradeClass, scoreBarClass } from '../benchmarkUtils'

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
}

const DIMENSION_LABELS: Record<string, string> = {
  corpus: 'Corpus coverage',
  registry: 'Registry health',
  provenance: 'Provenance integrity',
  retrieval: 'Retrieval accuracy',
  pipeline: 'Pipeline health',
}

export function BenchmarkModule({ busy, setBusy, setError, setNotice }: Props) {
  const [suite, setSuite] = useState<KnowledgeBenchmarkSuite | null>(null)
  const [runs, setRuns] = useState<KnowledgeBenchmarkRunSummary[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [report, setReport] = useState<KnowledgeBenchmarkReport | null>(null)

  const [pendingRunId, setPendingRunId] = useState<number | null>(null)

  const load = useCallback(async () => {
    setError(null)
    const [suiteRes, runsRes] = await Promise.all([
      fetchKnowledgeBenchmarkSuite(),
      fetchKnowledgeBenchmarkRuns(),
    ])
    setSuite(suiteRes)
    setRuns(runsRes)
    if (runsRes.length && selectedId == null) {
      setSelectedId(runsRes[0].id)
    }
  }, [selectedId, setError])

  useEffect(() => {
    void load().catch((err) => {
      setError(err instanceof Error ? err.message : 'benchmark load failed')
    })
  }, [load, setError])

  useEffect(() => {
    if (selectedId == null) {
      setReport(null)
      return
    }
    void fetchKnowledgeBenchmarkRun(selectedId)
      .then(setReport)
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'failed to load report')
      })
  }, [selectedId, setError])

  const onRun = async () => {
    setBusy(true)
    setError(null)
    setPendingRunId(null)
    try {
      const r = await runKnowledgeBenchmarkAndWait()
      setNotice(`Benchmark run #${r.id}: ${r.overall_score} (${r.grade})`)
      setSelectedId(r.id)
      setReport(r)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'benchmark run failed')
    } finally {
      setPendingRunId(null)
      setBusy(false)
    }
  }

  const running = busy || pendingRunId != null

  const prevRun = runs.length > 1 ? runs.find((r) => r.id !== selectedId) : null
  const delta =
    report && prevRun ? Math.round((report.overall_score - prevRun.overall_score) * 10) / 10 : null

  return (
    <div className="kb-module">
      <header className="kb-module-head">
        <div>
          <h3>Benchmark</h3>
          <p className="mute">
            KB-BENCH-001 — score corpus, registry, provenance, retrieval suite, and pipeline after RAG
            or ingest changes.
          </p>
        </div>
        <button type="button" disabled={running} onClick={() => void onRun()}>
          {running ? 'Running evaluation…' : 'Run evaluation'}
        </button>
      </header>

      {running ? (
        <p className="kb-alert" role="status">
          Benchmark queued — scoring corpus, registry, provenance, retrieval suite, and pipeline…
        </p>
      ) : null}

      {suite ? (
        <p className="mute kb-bench-suite-meta">
          Suite <code>{suite.revision || '—'}</code> · {suite.required_case_count} required /{' '}
          {suite.case_count} total cases
        </p>
      ) : null}

      {report ? (
        <section className="kb-bench-hero">
          <article className="kb-bench-score-card">
            <p className="kb-metric-label">Overall score</p>
            <p className="kb-bench-overall">
              {report.overall_score}
              <span className={`kb-bench-grade ${gradeClass(report.grade)}`}>{report.grade}</span>
            </p>
            <p className="mute">
              Run #{report.id} · {report.duration_ms} ms
              {delta != null ? (
                <>
                  {' '}
                  · Δ vs prior {delta >= 0 ? '+' : ''}
                  {delta}
                </>
              ) : null}
            </p>
          </article>

          <div className="kb-bench-dimensions">
            {Object.entries(DIMENSION_LABELS).map(([key, label]) => {
              const dim = report.dimensions[key]
              const score = dim?.score ?? 0
              const weight = Math.round((report.weights?.[key] ?? 0) * 100)
              return (
                <article key={key} className="kb-bench-dim">
                  <div className="kb-bench-dim-head">
                    <span>{label}</span>
                    <strong>{score}</strong>
                  </div>
                  <div className="kb-bench-bar-track" aria-hidden>
                    <div
                      className={`kb-bench-bar-fill ${scoreBarClass(score)}`}
                      style={{ width: `${Math.min(100, score)}%` }}
                    />
                  </div>
                  <p className="mute">weight {weight}%</p>
                </article>
              )
            })}
          </div>
        </section>
      ) : (
        <div className="knowledge-empty">
          <p>No benchmark runs yet. Run evaluation after catalog import or source crawl.</p>
        </div>
      )}

      <div className="kb-bench-layout">
        <section className="kb-panel-card">
          <h4>Run history</h4>
          <div className="kb-table-wrap">
            <table className="kb-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Score</th>
                  <th>Grade</th>
                  <th>When</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr
                    key={r.id}
                    className={selectedId === r.id ? 'kb-row-selected' : undefined}
                    onClick={() => setSelectedId(r.id)}
                  >
                    <td>#{r.id}</td>
                    <td>{r.overall_score}</td>
                    <td>
                      <span className={`kb-bench-grade-pill ${gradeClass(r.grade)}`}>{r.grade}</span>
                    </td>
                    <td className="mute">{r.created_at ? new Date(r.created_at).toLocaleString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {report ? (
          <section className="kb-panel-card kb-bench-report">
            <h4>Retrieval cases</h4>
            <ul className="plain kb-bench-cases">
              {(report.dimensions.retrieval?.cases || []).map((c) => (
                <li key={c.id} className={c.passed ? 'kb-bench-case-pass' : 'kb-bench-case-fail'}>
                  <div className="kb-bench-case-head">
                    <span className={c.passed ? 'kb-gate-pill-ok' : 'kb-gate-pill-blocked'}>
                      {c.passed ? 'PASS' : 'FAIL'}
                    </span>
                    <strong>{c.label}</strong>
                    <code>{c.id}</code>
                  </div>
                  <p className="mute">
                    hits={c.hits} top={c.top_score?.toFixed(3)}
                    {c.optional ? ' · optional' : ''}
                  </p>
                  {(c.notes || []).map((n) => (
                    <p key={n} className="kb-bench-note">
                      {n}
                    </p>
                  ))}
                </li>
              ))}
            </ul>

            <h4>Report</h4>
            <pre className="kb-bench-markdown">{report.markdown}</pre>
          </section>
        ) : null}
      </div>
    </div>
  )
}
