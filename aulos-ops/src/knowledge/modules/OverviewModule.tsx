import type { KnowledgeJob, KnowledgePlaneStats, KnowledgeSource } from '../../api'
import type { KnowledgeModuleId } from '../types'
import { sourceCanCrawl, countJobsByStatus, formatPct } from '../utils'

type Props = {
  planeHealth: string
  planeReachable: boolean | null
  planeStats: KnowledgePlaneStats | null
  sources: KnowledgeSource[]
  jobs: KnowledgeJob[]
  planeEnabled?: boolean
  planeUrl?: string
  onNavigate: (module: KnowledgeModuleId) => void
}

export function OverviewModule({
  planeHealth,
  planeReachable,
  planeStats,
  sources,
  jobs,
  planeEnabled,
  planeUrl,
  onNavigate,
}: Props) {
  const crawlReady = sources.filter(sourceCanCrawl).length
  const jobCounts = countJobsByStatus(jobs)
  const failedRecent = jobs.filter((j) => j.status === 'failed').slice(0, 5)
  const recentJobs = jobs.slice(0, 8)

  const publishPct = planeStats
    ? formatPct(planeStats.documents_published, planeStats.documents)
    : '—'

  return (
    <div className="kb-module">
      <header className="kb-module-head">
        <div>
          <h3>Observability</h3>
          <p className="mute">
            Plane health, corpus metrics, registry gates, and recent ingest activity.
          </p>
        </div>
        <p className="plane-status-row kb-module-status">
          <span
            className={
              planeReachable === true
                ? 'plane-badge plane-badge-ok'
                : planeReachable === false
                  ? 'plane-badge plane-badge-down'
                  : 'plane-badge plane-badge-unknown'
            }
          >
            {planeReachable === true ? 'up' : planeReachable === false ? 'down' : '…'}
          </span>{' '}
          {planeHealth}
          {planeEnabled != null ? (
            <>
              {' '}
              · RAG={String(planeEnabled)} · <code>{planeUrl}</code>
            </>
          ) : null}
        </p>
      </header>

      {planeStats ? (
        <div className="kb-bento">
          <article className="kb-metric-card kb-metric-highlight">
            <p className="kb-metric-label">Documents</p>
            <p className="kb-metric-value">{planeStats.documents}</p>
            <p className="mute">
              {planeStats.documents_published} published · {planeStats.documents_quarantine} quarantine (
              {publishPct} live)
            </p>
          </article>
          <article className="kb-metric-card">
            <p className="kb-metric-label">Chunks</p>
            <p className="kb-metric-value">{planeStats.chunks ?? '—'}</p>
            <p className="mute">RAG retrieval units</p>
          </article>
          <article className="kb-metric-card">
            <p className="kb-metric-label">Sources</p>
            <p className="kb-metric-value">
              {crawlReady}/{sources.length}
            </p>
            <p className="mute">
              crawl-ready · {planeStats.sources_verified ?? '—'} verified ·{' '}
              {planeStats.sources_enabled ?? '—'} enabled
            </p>
          </article>
          <article className="kb-metric-card">
            <p className="kb-metric-label">Entities</p>
            <p className="kb-metric-value">{planeStats.composers ?? 0}</p>
            <p className="mute">{planeStats.works} works catalogued</p>
          </article>
          <article className="kb-metric-card">
            <p className="kb-metric-label">Jobs</p>
            <p className="kb-metric-value">{planeStats.jobs}</p>
            <p className="mute">
              {jobCounts.succeeded ?? 0} ok · {jobCounts.failed ?? 0} failed · {jobCounts.running ?? 0}{' '}
              running
            </p>
          </article>
          <article className="kb-metric-card">
            <p className="kb-metric-label">Artifacts</p>
            <p className="kb-metric-value">{planeStats.artifacts}</p>
            <p className="mute">raw fetch blobs for audit replay</p>
          </article>
          <article className="kb-metric-card">
            <p className="kb-metric-label">Media</p>
            <p className="kb-metric-value">{planeStats.media_assets ?? 0}</p>
            <p className="mute">
              {planeStats.media_images ?? 0} img · {planeStats.media_audio ?? 0} audio ·{' '}
              {planeStats.media_meta ?? 0} meta
            </p>
          </article>
        </div>
      ) : null}

      <div className="kb-overview-panels">
        <section className="kb-panel-card">
          <div className="kb-panel-card-head">
            <h4>Registry gates</h4>
            <button type="button" className="ghost" onClick={() => onNavigate('registry')}>
              Open registry
            </button>
          </div>
          <ul className="kb-registry-mini plain">
            {sources.map((s) => (
              <li key={s.id}>
                <code>{s.id}</code>
                <span className={`badge ${s.verification_status === 'verified' ? 'badge-verified' : 'badge-candidate'}`}>
                  {s.verification_status || 'candidate'}
                </span>
                <span className={sourceCanCrawl(s) ? 'kb-dot kb-dot-ok' : 'kb-dot kb-dot-off'} />
                {sourceCanCrawl(s) ? 'ready' : 'blocked'}
              </li>
            ))}
          </ul>
        </section>

        <section className="kb-panel-card">
          <div className="kb-panel-card-head">
            <h4>Recent jobs</h4>
            <button type="button" className="ghost" onClick={() => onNavigate('jobs')}>
              All jobs
            </button>
          </div>
          {failedRecent.length ? (
            <p className="kb-alert" role="status">
              {failedRecent.length} recent failure(s) — inspect Jobs module.
            </p>
          ) : null}
          <ul className="plain kb-job-mini">
            {recentJobs.map((j) => (
              <li key={j.id}>
                <span className={`kb-job-tag kb-job-tag-${j.status}`}>{j.status}</span> #{j.id}{' '}
                <code>{j.source_id}</code>
                {j.error ? <span className="warn"> — {j.error.slice(0, 80)}</span> : null}
              </li>
            ))}
          </ul>
        </section>

        <section className="kb-panel-card kb-quick-actions">
          <h4>Quick actions</h4>
          <div className="row">
            <button type="button" onClick={() => onNavigate('documents')}>
              Browse documents
            </button>
            <button type="button" className="ghost" onClick={() => onNavigate('simulate')}>
              RAG simulate
            </button>
            <button type="button" className="ghost" onClick={() => onNavigate('registry')}>
              Verify sources
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}
