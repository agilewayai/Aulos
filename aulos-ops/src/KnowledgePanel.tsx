import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import {
  enqueueKnowledgeJob,
  fetchKnowledgeArtifact,
  fetchKnowledgeComposers,
  fetchKnowledgeDocument,
  fetchKnowledgeDocuments,
  fetchKnowledgeJobs,
  fetchKnowledgePlaneHealth,
  fetchKnowledgePlaneStats,
  fetchKnowledgeProvenance,
  fetchKnowledgeSources,
  fetchKnowledgeMedia,
  knowledgeRetrieveLab,
  patchKnowledgeSource,
  publishKnowledgeDocument,
  quarantineKnowledgeDocument,
  type KnowledgeComposer,
  type KnowledgeDoc,
  type KnowledgeJob,
  type KnowledgeMedia,
  type KnowledgePlaneStats,
  type KnowledgeSource,
} from './api'

type PanelId = 'browse' | 'sources' | 'jobs' | 'lab'

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
  planeEnabled?: boolean
  planeUrl?: string
}

const FAMOUS_SEED = [
  { id: 'johann-sebastian-bach', qid: 'Q1339', label: 'J.S. Bach', mb: 'Johann Sebastian Bach' },
  { id: 'wolfgang-amadeus-mozart', qid: 'Q254', label: 'Mozart', mb: 'Wolfgang Amadeus Mozart' },
  { id: 'ludwig-van-beethoven', qid: 'Q255', label: 'Beethoven', mb: 'Ludwig van Beethoven' },
  { id: 'frederic-chopin', qid: 'Q1268', label: 'Chopin', mb: 'Frédéric Chopin' },
  { id: 'franz-schubert', qid: 'Q7312', label: 'Schubert', mb: 'Franz Schubert' },
  { id: 'johannes-brahms', qid: 'Q7294', label: 'Brahms', mb: 'Johannes Brahms' },
  { id: 'pyotr-ilyich-tchaikovsky', qid: 'Q7315', label: 'Tchaikovsky', mb: 'Pyotr Ilyich Tchaikovsky' },
  { id: 'gustav-mahler', qid: 'Q7304', label: 'Mahler', mb: 'Gustav Mahler' },
  { id: 'claude-debussy', qid: 'Q4700', label: 'Debussy', mb: 'Claude Debussy' },
  { id: 'igor-stravinsky', qid: 'Q7314', label: 'Stravinsky', mb: 'Igor Stravinsky' },
]

export function KnowledgePanel({
  busy,
  setBusy,
  setError,
  setNotice,
  planeEnabled,
  planeUrl,
}: Props) {
  const [panel, setPanel] = useState<PanelId>('browse')
  const [planeHealth, setPlaneHealth] = useState('')
  const [planeReachable, setPlaneReachable] = useState<boolean | null>(null)
  const [planeStats, setPlaneStats] = useState<KnowledgePlaneStats | null>(null)
  const [sources, setSources] = useState<KnowledgeSource[]>([])
  const [jobs, setJobs] = useState<KnowledgeJob[]>([])
  const [docs, setDocs] = useState<KnowledgeDoc[]>([])
  const [composers, setComposers] = useState<KnowledgeComposer[]>([])
  const [media, setMedia] = useState<KnowledgeMedia[]>([])
  const [docStatus, setDocStatus] = useState<'all' | 'published' | 'quarantine'>('all')
  const [docType, setDocType] = useState('')
  const [docSource, setDocSource] = useState('')
  const [docQuery, setDocQuery] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDoc | null>(null)
  const [provenance, setProvenance] = useState<Record<string, unknown> | null>(null)
  const [artifactPreview, setArtifactPreview] = useState('')
  const [crawlComposer, setCrawlComposer] = useState('')
  const crawlOptions = useMemo(() => {
    if (composers.length) {
      return composers
        .map((c) => ({
          id: c.id,
          label: c.name_en || c.name_zh || c.id,
          qid: c.external_ids?.wikidata || c.external_ids?.qid || '',
          mb: c.name_en || '',
        }))
        .filter((c) => c.id)
    }
    // Fallback seed only when plane has no composer rows yet — not a runtime branch.
    return FAMOUS_SEED
  }, [composers])
  useEffect(() => {
    if (!crawlComposer && crawlOptions[0]?.id) setCrawlComposer(crawlOptions[0].id)
  }, [crawlComposer, crawlOptions])
  const [labQuery, setLabQuery] = useState('Bach cello suites')
  const [labWorkId, setLabWorkId] = useState('bach.cello-suites.bwv-1007-1012')
  const [labComposerId, setLabComposerId] = useState('')
  const [labHits, setLabHits] = useState<
    Array<{ title: string; score: number; text: string; aulos_work_id?: string }>
  >([])

  const load = useCallback(async () => {
    try {
      const h = await fetchKnowledgePlaneHealth()
      setPlaneReachable(true)
      setPlaneHealth(`${h.service} ${h.version} — ${h.status}`)
      const [stats, src, jobRows, comps, mediaRows] = await Promise.all([
        fetchKnowledgePlaneStats(),
        fetchKnowledgeSources(),
        fetchKnowledgeJobs(),
        fetchKnowledgeComposers(),
        fetchKnowledgeMedia({ limit: 40 }),
      ])
      setPlaneStats(stats)
      setSources(src)
      setJobs(jobRows)
      setComposers(comps)
      setMedia(mediaRows)
      const docRows = await fetchKnowledgeDocuments({
        status: docStatus === 'all' ? '' : docStatus,
        entity_type: docType,
        source_id: docSource,
        q: docQuery,
        limit: 80,
      })
      setDocs(docRows)
    } catch (err) {
      setPlaneReachable(false)
      setPlaneHealth(err instanceof Error ? err.message : 'knowledge plane unreachable')
      setPlaneStats(null)
      setSources([])
      setJobs([])
      setDocs([])
      setComposers([])
      setMedia([])
      setSelectedDoc(null)
      setProvenance(null)
    }
  }, [docStatus, docType, docSource, docQuery])

  useEffect(() => {
    void load()
  }, [load])

  const openDoc = useCallback(
    async (id: number) => {
      setBusy(true)
      setError(null)
      try {
        setSelectedId(id)
        const [doc, prov] = await Promise.all([
          fetchKnowledgeDocument(id),
          fetchKnowledgeProvenance(id),
        ])
        setSelectedDoc(doc)
        setProvenance(prov)
        setArtifactPreview('')
        const artId = doc.artifact_id
        if (artId) {
          const art = await fetchKnowledgeArtifact(artId)
          setArtifactPreview(art.preview || '')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'failed to open document')
      } finally {
        setBusy(false)
      }
    },
    [setBusy, setError],
  )

  const runJob = useCallback(
    async (sourceId: string, params: Record<string, unknown>, label: string) => {
      setBusy(true)
      setError(null)
      try {
        const job = await enqueueKnowledgeJob(sourceId, params)
        setNotice(`${label}: job #${job.id} → ${job.status}${job.error ? ` (${job.error})` : ''}`)
        await load()
      } catch (err) {
        setError(err instanceof Error ? err.message : 'job failed')
      } finally {
        setBusy(false)
      }
    },
    [load, setBusy, setError, setNotice],
  )

  const selectedSeed = useMemo(
    () => crawlOptions.find((c) => c.id === crawlComposer) || crawlOptions[0] || FAMOUS_SEED[0],
    [crawlComposer, crawlOptions],
  )

  return (
    <section className="settings knowledge-panel" aria-labelledby="knowledge-title">
      <div className="section-head">
        <h2 id="knowledge-title">Knowledge audit</h2>
        <button
          type="button"
          className="ghost"
          disabled={busy}
          onClick={() => {
            void load()
          }}
        >
          Refresh
        </button>
      </div>
      <p className="lede">
        View, audit provenance, and proofread (quarantine / republish) documents on the professional music
        knowledge plane — separate from business SQLite.
      </p>

      <p className="plane-status-row">
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
        <strong>Plane:</strong> {planeHealth || 'not loaded — click Refresh'}
        {planeEnabled != null ? (
          <>
            {' '}
            · RAG flag={String(planeEnabled)} · {planeUrl}
          </>
        ) : null}
      </p>

      {planeReachable === false ? (
        <div className="knowledge-empty" role="status">
          <p>
            Knowledge plane unreachable. Start <code>aulos-knowledge</code> against Postgres and confirm API
            proxy <code>AULOS_KNOWLEDGE_BASE_URL</code>.
          </p>
          <button type="button" className="ghost" disabled={busy} onClick={() => void load()}>
            Retry connection
          </button>
        </div>
      ) : null}

      {planeStats ? (
        <div className="stat-grid knowledge-stats">
          <div className="stat">
            <p className="stat-value">{planeStats.composers ?? '—'}</p>
            <p className="stat-label">Composers</p>
          </div>
          <div className="stat">
            <p className="stat-value">{planeStats.works}</p>
            <p className="stat-label">Works</p>
          </div>
          <div className="stat">
            <p className="stat-value">{planeStats.documents_published}</p>
            <p className="stat-label">Published</p>
          </div>
          <div className="stat">
            <p className="stat-value">{planeStats.documents_quarantine}</p>
            <p className="stat-label">Quarantine</p>
          </div>
          <div className="stat">
            <p className="stat-value">{planeStats.jobs}</p>
            <p className="stat-label">Jobs</p>
          </div>
          <div className="stat">
            <p className="stat-value">{planeStats.artifacts}</p>
            <p className="stat-label">Artifacts</p>
          </div>
          <div className="stat">
            <p className="stat-value">{planeStats.media_images ?? 0}</p>
            <p className="stat-label">Images</p>
          </div>
          <div className="stat">
            <p className="stat-value">{planeStats.media_meta ?? 0}</p>
            <p className="stat-label">Music meta</p>
          </div>
          <div className="stat">
            <p className="stat-value">{planeStats.media_audio ?? 0}</p>
            <p className="stat-label">PD audio</p>
          </div>
        </div>
      ) : null}

      <nav className="knowledge-subtabs" aria-label="Knowledge panels">
        {(
          [
            ['browse', 'Browse & proofread'],
            ['sources', 'Sources'],
            ['jobs', 'Jobs & crawl'],
            ['lab', 'Retrieve lab'],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={panel === id ? 'tab active' : 'tab'}
            onClick={() => {
              setPanel(id)
              if (planeReachable !== false) void load()
            }}
          >
            {label}
          </button>
        ))}
      </nav>

      {panel === 'browse' && planeReachable !== false ? (
        <div className="knowledge-browse">
          <div className="knowledge-filters row">
            <label>
              Status
              <select
                value={docStatus}
                onChange={(e) => setDocStatus(e.target.value as typeof docStatus)}
              >
                <option value="all">all</option>
                <option value="published">published</option>
                <option value="quarantine">quarantine</option>
              </select>
            </label>
            <label>
              Type
              <select value={docType} onChange={(e) => setDocType(e.target.value)}>
                <option value="">any</option>
                <option value="composer">composer</option>
                <option value="work">work</option>
              </select>
            </label>
            <label>
              Source
              <select value={docSource} onChange={(e) => setDocSource(e.target.value)}>
                <option value="">any</option>
                {sources.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.id}
                  </option>
                ))}
              </select>
            </label>
            <label className="grow">
              Search
              <input
                value={docQuery}
                onChange={(e) => setDocQuery(e.target.value)}
                placeholder="title, body, work_id…"
              />
            </label>
            <button type="button" disabled={busy} onClick={() => void load()}>
              Apply
            </button>
          </div>

          <div className="knowledge-split">
            <div className="knowledge-list-col">
              <h3>Documents ({docs.length})</h3>
              <ul className="plain knowledge-doc-list">
                {docs.map((d) => (
                  <li key={d.id} className={selectedId === d.id ? 'selected' : ''}>
                    <button type="button" className="doc-pick" onClick={() => void openDoc(d.id)}>
                      <span className={`doc-status doc-status-${d.status}`}>{d.status}</span>
                      <strong>#{d.id}</strong> {d.title}
                      <span className="mute">
                        {d.source_id} · {d.entity_type || '—'} · {d.aulos_work_id || d.entity_id || ''}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
              {composers.length ? (
                <>
                  <h3>Composers ({composers.length})</h3>
                  <ul className="plain">
                    {composers.map((c) => (
                      <li key={c.id}>
                        <code>{c.id}</code> — {c.name_en}
                        {c.name_zh ? ` / ${c.name_zh}` : ''}
                        {c.lifespan ? ` · ${c.lifespan}` : ''}
                      </li>
                    ))}
                  </ul>
                </>
              ) : null}
              {media.length ? (
                <>
                  <h3>Media on durable disk ({media.length})</h3>
                  <ul className="plain">
                    {media.map((m) => (
                      <li key={m.id}>
                        <span className={`doc-status doc-status-${m.exists_on_disk ? 'published' : 'quarantine'}`}>
                          {m.kind}
                        </span>{' '}
                        #{m.id} {m.title.slice(0, 60)} · {(m.byte_size / 1024).toFixed(1)} KiB · {m.license_class}
                        <div className="mute">
                          {m.storage_path} {m.exists_on_disk ? '✓ disk' : '✗ missing'}
                        </div>
                      </li>
                    ))}
                  </ul>
                </>
              ) : null}
            </div>

            <div className="knowledge-detail-col" aria-live="polite">
              {selectedDoc ? (
                <>
                  <div className="section-head">
                    <h3>Proofread · #{selectedDoc.id}</h3>
                    <div className="row">
                      {selectedDoc.status === 'published' ? (
                        <button
                          type="button"
                          className="ghost"
                          disabled={busy}
                          onClick={() => {
                            void (async () => {
                              setBusy(true)
                              try {
                                await quarantineKnowledgeDocument(selectedDoc.id)
                                setNotice(`Document #${selectedDoc.id} quarantined`)
                                await load()
                                await openDoc(selectedDoc.id)
                              } catch (err) {
                                setError(err instanceof Error ? err.message : 'quarantine failed')
                              } finally {
                                setBusy(false)
                              }
                            })()
                          }}
                        >
                          Quarantine
                        </button>
                      ) : (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => {
                            void (async () => {
                              setBusy(true)
                              try {
                                await publishKnowledgeDocument(selectedDoc.id)
                                setNotice(`Document #${selectedDoc.id} published`)
                                await load()
                                await openDoc(selectedDoc.id)
                              } catch (err) {
                                setError(err instanceof Error ? err.message : 'publish failed')
                              } finally {
                                setBusy(false)
                              }
                            })()
                          }}
                        >
                          Publish
                        </button>
                      )}
                    </div>
                  </div>
                  <p>
                    <span className={`doc-status doc-status-${selectedDoc.status}`}>
                      {selectedDoc.status}
                    </span>{' '}
                    · {selectedDoc.source_id} · {selectedDoc.license_class} · extractor{' '}
                    {selectedDoc.extractor_version}
                  </p>
                  <p className="mute">
                    entity={selectedDoc.entity_type}/{selectedDoc.entity_id} · work_id=
                    {selectedDoc.aulos_work_id || '—'} · job={selectedDoc.job_id ?? '—'} · artifact=
                    {selectedDoc.artifact_id ?? '—'}
                  </p>
                  <h4>Body</h4>
                  <pre className="code-block knowledge-body">{selectedDoc.body || ''}</pre>
                  <h4>Provenance</h4>
                  <pre className="code-block">
                    {provenance ? JSON.stringify(provenance, null, 2) : '—'}
                  </pre>
                  {artifactPreview ? (
                    <>
                      <h4>Artifact preview</h4>
                      <pre className="code-block knowledge-body">{artifactPreview}</pre>
                    </>
                  ) : null}
                </>
              ) : (
                <p className="muted">Select a document to audit provenance and proofread content.</p>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {panel === 'sources' && planeReachable !== false ? (
        <>
          <h3>Authority sources</h3>
          <ul className="plain">
            {sources.map((s) => (
              <li key={s.id}>
                <code>{s.id}</code> · {s.name} · tier={s.tier} · {s.connector} · {s.license_class} · qps=
                {s.rate_limit_qps} · {s.enabled ? 'on' : 'off'}{' '}
                <button
                  type="button"
                  className="ghost"
                  disabled={busy}
                  onClick={() => {
                    void (async () => {
                      setBusy(true)
                      try {
                        await patchKnowledgeSource(s.id, { enabled: !s.enabled })
                        await load()
                      } catch (err) {
                        setError(err instanceof Error ? err.message : 'patch failed')
                      } finally {
                        setBusy(false)
                      }
                    })()
                  }}
                >
                  {s.enabled ? 'Disable' : 'Enable'}
                </button>
                {s.notes ? <div className="mute">{s.notes}</div> : null}
              </li>
            ))}
          </ul>
        </>
      ) : null}

      {panel === 'jobs' && planeReachable !== false ? (
        <>
          <h3>Enqueue</h3>
          <div className="row">
            <button
              type="button"
              disabled={busy}
              onClick={() => void runJob('catalog-local', {}, 'Catalog import')}
            >
              Run catalog import
            </button>
          </div>
          <div className="row knowledge-crawl">
            <label>
              Famous composer
              <select value={crawlComposer} onChange={(e) => setCrawlComposer(e.target.value)}>
                {crawlOptions.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.label}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                void runJob(
                  'wikidata',
                  { qids: [selectedSeed.qid], composer_id: selectedSeed.id },
                  `Wikidata ${selectedSeed.label}`,
                )
              }
            >
              Crawl Wikidata
            </button>
            <button
              type="button"
              className="ghost"
              disabled={busy}
              onClick={() =>
                void runJob(
                  'musicbrainz',
                  {
                    mode: 'artist',
                    query: `artist:"${selectedSeed.mb}" AND type:person`,
                    composer_id: selectedSeed.id,
                  },
                  `MusicBrainz artist ${selectedSeed.label}`,
                )
              }
            >
              Crawl MusicBrainz artist
            </button>
          </div>
          <h3>Recent jobs</h3>
          <ul className="plain">
            {jobs.slice(0, 24).map((j) => (
              <li key={j.id}>
                #{j.id} {j.source_id} — <strong>{j.status}</strong>
                {j.error ? ` — ${j.error}` : ''}
                {j.finished_at ? ` · ${j.finished_at}` : ''}
              </li>
            ))}
          </ul>
        </>
      ) : null}

      {panel === 'lab' && planeReachable !== false ? (
        <>
          <h3>Retrieve lab</h3>
          <p className="mute">Debug identity bleed: set work_id / composer_id filters before retrieve.</p>
          <form
            className="stack"
            onSubmit={(e: FormEvent) => {
              e.preventDefault()
              void (async () => {
                setBusy(true)
                setError(null)
                try {
                  const r = await knowledgeRetrieveLab(labQuery, labWorkId, labComposerId)
                  setLabHits(r.hits || [])
                } catch (err) {
                  setError(err instanceof Error ? err.message : 'retrieve failed')
                } finally {
                  setBusy(false)
                }
              })()
            }}
          >
            <label>
              Query
              <input value={labQuery} onChange={(e) => setLabQuery(e.target.value)} />
            </label>
            <label>
              work_id filter
              <input value={labWorkId} onChange={(e) => setLabWorkId(e.target.value)} />
            </label>
            <label>
              composer_id filter
              <input value={labComposerId} onChange={(e) => setLabComposerId(e.target.value)} />
            </label>
            <button type="submit" disabled={busy}>
              Retrieve
            </button>
          </form>
          <ul className="plain">
            {labHits.map((h, i) => (
              <li key={`${h.title}-${i}`}>
                {h.score} · {h.title} · {h.aulos_work_id || ''}
                <div className="mute">{h.text.slice(0, 220)}</div>
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </section>
  )
}
