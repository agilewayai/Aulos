import type { KnowledgeBenchmarkDashboard } from '../../api'
import type { KnowledgeModuleId as NavId } from '../types'
import {
  formatDelta,
  formatWhen,
  gradeClass,
  healthStatusClass,
  healthStatusLabel,
  insightSeverityClass,
  scoreBarClass,
} from '../benchmarkUtils'

type Props = {
  dashboard: KnowledgeBenchmarkDashboard | null
  variant?: 'full' | 'compact'
  busy?: boolean
  onRunBenchmark?: () => void
  onNavigate?: (module: NavId) => void
}

function insightAction(
  action: string | null | undefined,
  onNavigate?: (module: NavId) => void,
): { label: string; module: NavId } | null {
  if (!action || !onNavigate) return null
  const map: Record<string, { label: string; module: NavId }> = {
    run_benchmark: { label: 'Run benchmark', module: 'benchmark' },
    simulate_rag: { label: 'RAG simulate', module: 'simulate' },
    review_documents: { label: 'Review documents', module: 'documents' },
    verify_sources: { label: 'Verify sources', module: 'registry' },
    audit_provenance: { label: 'Audit documents', module: 'documents' },
    inspect_jobs: { label: 'Inspect jobs', module: 'jobs' },
  }
  return map[action] ?? null
}

export function BenchmarkDashboardReport({
  dashboard,
  variant = 'full',
  busy,
  onRunBenchmark,
  onNavigate,
}: Props) {
  if (!dashboard) {
    return (
      <div className="kb-dash-report kb-dash-empty">
        <p className="mute">Loading performance dashboard…</p>
      </div>
    )
  }

  const latest = dashboard.latest_run
  const trendMax = Math.max(...dashboard.trend.map((t) => t.score), 100)

  if (variant === 'compact') {
    return (
      <section className="kb-dash-report kb-dash-compact" aria-label="Knowledge performance summary">
        <div className="kb-dash-compact-head">
          <span className={`kb-dash-health-pill ${healthStatusClass(dashboard.health_status)}`}>
            {healthStatusLabel(dashboard.health_status)}
          </span>
          {latest ? (
            <p className="kb-dash-compact-score">
              <strong>{latest.overall_score}</strong>
              <span className={`kb-bench-grade ${gradeClass(latest.grade)}`}>{latest.grade}</span>
              {dashboard.score_delta != null ? (
                <span className="kb-dash-delta">Δ {formatDelta(dashboard.score_delta)}</span>
              ) : null}
            </p>
          ) : (
            <p className="mute">No benchmark runs yet</p>
          )}
        </div>
        <p className="mute kb-dash-headline">{dashboard.headline}</p>
        <div className="kb-dash-compact-actions">
          {onNavigate ? (
            <button type="button" className="ghost" onClick={() => onNavigate('report')}>
              Open report
            </button>
          ) : null}
          {onRunBenchmark ? (
            <button type="button" disabled={busy} onClick={onRunBenchmark}>
              Run evaluation
            </button>
          ) : null}
        </div>
      </section>
    )
  }

  return (
    <section className="kb-dash-report" aria-label="Knowledge performance dashboard report">
      <header className={`kb-dash-banner ${healthStatusClass(dashboard.health_status)}`}>
        <div>
          <p className="kb-dash-banner-kicker">KB-BENCH-001 · Performance dashboard</p>
          <h4 className="kb-dash-banner-title">{dashboard.headline}</h4>
          <p className="kb-dash-banner-meta mute">
            Generated {formatWhen(dashboard.generated_at)}
            {dashboard.run_count ? ` · ${dashboard.run_count} run(s) on record` : ''}
            {dashboard.suite_revision ? ` · suite ${dashboard.suite_revision}` : ''}
          </p>
        </div>
        <div className="kb-dash-banner-actions">
          {onRunBenchmark ? (
            <button type="button" disabled={busy} onClick={onRunBenchmark}>
              Run evaluation
            </button>
          ) : null}
        </div>
      </header>

      <div className="kb-dash-hero">
        <article className="kb-dash-score-panel">
          {latest ? (
            <>
              <p className="kb-metric-label">Overall capability score</p>
              <p className="kb-bench-overall kb-dash-overall">
                {latest.overall_score}
                <span className={`kb-bench-grade ${gradeClass(latest.grade)}`}>{latest.grade}</span>
              </p>
              <p className="mute">
                Run #{latest.id} · {latest.duration_ms} ms · {formatWhen(latest.created_at)}
              </p>
              {dashboard.score_delta != null ? (
                <p className={`kb-dash-delta-line ${dashboard.score_delta >= 0 ? 'kb-dash-up' : 'kb-dash-down'}`}>
                  Δ vs previous run: {formatDelta(dashboard.score_delta)}
                </p>
              ) : null}
            </>
          ) : (
            <>
              <p className="kb-metric-label">Overall capability score</p>
              <p className="kb-dash-no-data">—</p>
              <p className="mute">Run benchmark to establish baseline metrics.</p>
            </>
          )}
        </article>

        <article className="kb-dash-trend-panel">
          <p className="kb-metric-label">Score trend</p>
          {dashboard.trend.length ? (
            <div className="kb-dash-trend-chart" role="img" aria-label="Benchmark score trend">
              {dashboard.trend.map((pt) => (
                <div key={pt.id} className="kb-dash-trend-col" title={`#${pt.id}: ${pt.score}`}>
                  <div
                    className={`kb-dash-trend-bar ${scoreBarClass(pt.score)}`}
                    style={{ height: `${Math.max(8, (pt.score / trendMax) * 100)}%` }}
                  />
                  <span className="kb-dash-trend-label">{pt.score}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="mute">Trend appears after multiple benchmark runs.</p>
          )}
        </article>
      </div>

      <div className="kb-dash-dimension-grid">
        {dashboard.dimensions.map((dim) => (
          <article key={dim.id} className="kb-dash-dim-card">
            <div className="kb-bench-dim-head">
              <span>{dim.label}</span>
              <strong>{dim.score}</strong>
            </div>
            <div className="kb-bench-bar-track" aria-hidden>
              <div
                className={`kb-bench-bar-fill ${scoreBarClass(dim.score)}`}
                style={{ width: `${Math.min(100, dim.score)}%` }}
              />
            </div>
            <p className="mute">weight {dim.weight_pct}%</p>
            <ul className="plain kb-dash-dim-details">
              {Object.entries(dim.details || {})
                .slice(0, 4)
                .map(([k, v]) => (
                  <li key={k}>
                    <code>{k}</code> {String(v)}
                  </li>
                ))}
            </ul>
          </article>
        ))}
      </div>

      <div className="kb-dash-lower">
        <section className="kb-panel-card kb-dash-insights">
          <h4>Insights & recommendations</h4>
          <ul className="plain kb-dash-insight-list">
            {dashboard.insights.map((ins) => {
              const act = insightAction(ins.action, onNavigate)
              return (
                <li key={`${ins.severity}-${ins.title}`} className={`kb-dash-insight ${insightSeverityClass(ins.severity)}`}>
                  <p className="kb-dash-insight-title">{ins.title}</p>
                  <p className="mute">{ins.detail}</p>
                  {act ? (
                    <button type="button" className="ghost" onClick={() => onNavigate?.(act.module)}>
                      {act.label}
                    </button>
                  ) : null}
                </li>
              )
            })}
          </ul>
        </section>

        <section className="kb-panel-card kb-dash-retrieval">
          <h4>Retrieval suite</h4>
          {dashboard.retrieval_summary.total ? (
            <>
              <p className="kb-dash-retrieval-score">
                <strong>
                  {dashboard.retrieval_summary.passed}/{dashboard.retrieval_summary.total}
                </strong>{' '}
                required cases passed
              </p>
              {dashboard.retrieval_summary.failed_cases.length ? (
                <ul className="plain kb-bench-cases">
                  {dashboard.retrieval_summary.failed_cases.map((c) => (
                    <li key={c.id} className="kb-bench-case-fail">
                      <code>{c.id}</code> — {c.label}
                      {(c.notes || []).map((n) => (
                        <p key={n} className="kb-bench-note">
                          {n}
                        </p>
                      ))}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="kb-dash-all-pass">All required retrieval cases passing.</p>
              )}
            </>
          ) : (
            <p className="mute">No retrieval results — run benchmark first.</p>
          )}
        </section>
      </div>

      <section className="kb-panel-card kb-dash-summary-md">
        <h4>Executive summary</h4>
        <pre className="kb-bench-markdown kb-dash-markdown">{dashboard.markdown_summary}</pre>
      </section>
    </section>
  )
}
