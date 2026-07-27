import { useMemo, useState } from 'react'
import type { CrawlSeed } from '../types'
import type { KnowledgeJob, KnowledgeSource } from '../../api'
import { jobStatusClass } from '../utils'

type Props = {
  busy: boolean
  jobs: KnowledgeJob[]
  sources: KnowledgeSource[]
  crawlOptions: CrawlSeed[]
  onRunJob: (sourceId: string, params: Record<string, unknown>, label: string) => Promise<void>
}

export function JobsModule({ busy, jobs, sources, crawlOptions, onRunJob }: Props) {
  const [statusFilter, setStatusFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [crawlComposer, setCrawlComposer] = useState(crawlOptions[0]?.id || '')

  const selectedSeed = useMemo(
    () => crawlOptions.find((c) => c.id === crawlComposer) || crawlOptions[0],
    [crawlComposer, crawlOptions],
  )

  const filtered = useMemo(() => {
    return jobs.filter((j) => {
      if (statusFilter && j.status !== statusFilter) return false
      if (sourceFilter && j.source_id !== sourceFilter) return false
      return true
    })
  }, [jobs, statusFilter, sourceFilter])

  const crawlReadySources = sources.filter((s) => s.enabled && s.verification_status === 'verified')

  return (
    <div className="kb-module">
      <header className="kb-module-head">
        <div>
          <h3>Jobs & crawl</h3>
          <p className="mute">Enqueue connector runs and observe ingest status / errors.</p>
        </div>
      </header>

      <section className="kb-panel-card">
        <h4>Quick enqueue</h4>
        <div className="row">
          <button
            type="button"
            disabled={busy}
            onClick={() => void onRunJob('catalog-local', {}, 'Catalog import')}
          >
            Catalog import
          </button>
        </div>
        <div className="row knowledge-crawl kb-crawl-grid">
          <label>
            Composer seed
            <select value={crawlComposer} onChange={(e) => setCrawlComposer(e.target.value)}>
              {crawlOptions.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </label>
          {selectedSeed ? (
            <>
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  void onRunJob(
                    'wikidata',
                    { qids: [selectedSeed.qid], composer_id: selectedSeed.id },
                    `Wikidata ${selectedSeed.label}`,
                  )
                }
              >
                Wikidata
              </button>
              <button
                type="button"
                className="ghost"
                disabled={busy}
                onClick={() =>
                  void onRunJob(
                    'musicbrainz',
                    {
                      mode: 'artist',
                      query: `artist:"${selectedSeed.mb}" AND type:person`,
                      composer_id: selectedSeed.id,
                    },
                    `MusicBrainz ${selectedSeed.label}`,
                  )
                }
              >
                MusicBrainz
              </button>
              <button
                type="button"
                className="ghost"
                disabled={busy}
                onClick={() =>
                  void onRunJob(
                    'wikipedia',
                    {
                      title: selectedSeed.mb || selectedSeed.label,
                      langs: ['en', 'zh'],
                      composer_id: selectedSeed.id,
                    },
                    `Wikipedia ${selectedSeed.label}`,
                  )
                }
              >
                Wikipedia
              </button>
              <button
                type="button"
                className="ghost"
                disabled={busy}
                onClick={() =>
                  void onRunJob(
                    'imslp',
                    {
                      title: `Category:${selectedSeed.mb || selectedSeed.label}`,
                      composer_id: selectedSeed.id,
                    },
                    `IMSLP ${selectedSeed.label}`,
                  )
                }
              >
                IMSLP
              </button>
              <button
                type="button"
                className="ghost"
                disabled={busy}
                onClick={() =>
                  void onRunJob(
                    'rism',
                    {
                      q: selectedSeed.mb || selectedSeed.label,
                      mode: 'people',
                      limit: 5,
                      composer_id: selectedSeed.id,
                    },
                    `RISM ${selectedSeed.label}`,
                  )
                }
              >
                RISM
              </button>
            </>
          ) : null}
        </div>
        <p className="mute">
          Crawl-ready sources: {crawlReadySources.map((s) => s.id).join(', ') || 'none'}
        </p>
      </section>

      <section className="kb-panel-card">
        <div className="kb-panel-card-head">
          <h4>Job log</h4>
          <div className="row kb-job-filters">
            <label>
              Status
              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} disabled={busy}>
                <option value="">all</option>
                <option value="succeeded">succeeded</option>
                <option value="failed">failed</option>
                <option value="running">running</option>
                <option value="queued">queued</option>
              </select>
            </label>
            <label>
              Source
              <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)} disabled={busy}>
                <option value="">all</option>
                {sources.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.id}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
        <div className="kb-table-wrap">
          <table className="kb-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Source</th>
                <th>Status</th>
                <th>Error</th>
                <th>Finished</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 60).map((j) => (
                <tr key={j.id}>
                  <td>#{j.id}</td>
                  <td>
                    <code>{j.source_id}</code>
                  </td>
                  <td>
                    <span className={`kb-job-tag ${jobStatusClass(j.status)}`}>{j.status}</span>
                  </td>
                  <td className="kb-mono">{j.error ? j.error.slice(0, 120) : '—'}</td>
                  <td>{j.finished_at || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
