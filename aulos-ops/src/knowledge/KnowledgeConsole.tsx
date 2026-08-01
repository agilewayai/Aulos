import { useCallback, useEffect, useState } from 'react'
import { KNOWLEDGE_MODULES, type KnowledgeModuleId, type DocStatusFilter } from './types'
import { useKnowledgePlane } from './useKnowledgePlane'
import { OverviewModule } from './modules/OverviewModule'
import { ReportModule } from './modules/ReportModule'
import { SourceRegistryModule } from './modules/SourceRegistryModule'
import { DocumentsModule } from './modules/DocumentsModule'
import { JobsModule } from './modules/JobsModule'
import { SimulateModule } from './modules/SimulateModule'
import { BenchmarkModule } from './modules/BenchmarkModule'
import { ImproveModule } from './modules/ImproveModule'
import { ExploreModule } from './modules/ExploreModule'
import { ComposerDossierModule } from './modules/ComposerDossierModule'
import { MediaModule } from './modules/MediaModule'

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
  planeEnabled?: boolean
  planeUrl?: string
}

export function KnowledgeConsole({
  busy,
  setBusy,
  setError,
  setNotice,
  planeEnabled,
  planeUrl,
}: Props) {
  const [module, setModule] = useState<KnowledgeModuleId>('overview')
  const [docStatus, setDocStatus] = useState<DocStatusFilter>('all')
  const [docType, setDocType] = useState('')
  const [docSource, setDocSource] = useState('')
  const [docQuery, setDocQuery] = useState('')

  const {
    load,
    planeReachable,
    planeHealth,
    planeStats,
    sources,
    jobs,
    docs,
    media,
    crawlOptions,
    selectedId,
    selectedDoc,
    provenance,
    chunkProvenance,
    selectedChunkId,
    artifactPreview,
    showRawProvenance,
    setShowRawProvenance,
    openDoc: planeOpenDoc,
    openChunk: planeOpenChunk,
    runJob: planeRunJob,
  } = useKnowledgePlane({ docStatus, docType, docSource, docQuery })

  const refresh = useCallback(async () => {
    setError(null)
    try {
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'knowledge plane unreachable')
    }
  }, [load, setError])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const runJob = useCallback(
    async (sourceId: string, params: Record<string, unknown>, label: string) => {
      setBusy(true)
      setError(null)
      try {
        const job = await planeRunJob(sourceId, params)
        setNotice(`${label}: job #${job.id} → ${job.status}${job.error ? ` (${job.error})` : ''}`)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'job failed')
      } finally {
        setBusy(false)
      }
    },
    [planeRunJob, setBusy, setError, setNotice],
  )

  const openDoc = useCallback(
    async (id: number) => {
      setBusy(true)
      setError(null)
      try {
        await planeOpenDoc(id)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'failed to open document')
      } finally {
        setBusy(false)
      }
    },
    [planeOpenDoc, setBusy, setError],
  )

  const openChunk = useCallback(
    async (id: number) => {
      setBusy(true)
      setError(null)
      try {
        await planeOpenChunk(id)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'failed to open chunk')
      } finally {
        setBusy(false)
      }
    },
    [planeOpenChunk, setBusy, setError],
  )

  return (
    <section className="settings knowledge-panel kb-console" aria-labelledby="knowledge-title">
      <header className="kb-console-top ops-page-head">
        <div>
          <h2 id="knowledge-title">Knowledge</h2>
          <p className="lede">
            Registry-gated ingest · query · verify · simulate · observe
          </p>
        </div>
        <button type="button" className="ghost" disabled={busy} onClick={() => void refresh()}>
          Refresh
        </button>
      </header>

      {planeReachable === false ? (
        <div className="knowledge-empty" role="status">
          <p>
            Knowledge plane unreachable. Start <code>aulos-knowledge</code> and confirm API proxy{' '}
            <code>AULOS_KNOWLEDGE_BASE_URL</code>.
          </p>
          <button type="button" className="ghost" disabled={busy} onClick={() => void refresh()}>
            Retry
          </button>
        </div>
      ) : null}

      <div className="kb-console-body">
        <nav className="kb-console-nav" aria-label="Knowledge modules">
          {KNOWLEDGE_MODULES.map((m) => (
            <button
              key={m.id}
              type="button"
              className={module === m.id ? 'kb-nav-item active' : 'kb-nav-item'}
              onClick={() => {
                setModule(m.id)
                if (planeReachable !== false) void refresh()
              }}
            >
              <span className="kb-nav-label">{m.label}</span>
              <span className="kb-nav-hint">{m.hint}</span>
            </button>
          ))}
        </nav>

        <main className="kb-console-main">
          {module === 'overview' && planeReachable !== false ? (
            <OverviewModule
              planeHealth={planeHealth}
              planeReachable={planeReachable}
              planeStats={planeStats}
              sources={sources}
              jobs={jobs}
              planeEnabled={planeEnabled}
              planeUrl={planeUrl}
              busy={busy}
              setBusy={setBusy}
              setError={setError}
              setNotice={setNotice}
              onNavigate={setModule}
            />
          ) : null}

          {module === 'report' && planeReachable !== false ? (
            <ReportModule
              busy={busy}
              setBusy={setBusy}
              setError={setError}
              setNotice={setNotice}
              onNavigate={setModule}
            />
          ) : null}

          {module === 'registry' && planeReachable !== false ? (
            <SourceRegistryModule
              busy={busy}
              sources={sources}
              onRefresh={refresh}
              setBusy={setBusy}
              setError={setError}
              setNotice={setNotice}
            />
          ) : null}

          {module === 'explore' && planeReachable !== false ? (
            <ExploreModule
              busy={busy}
              setBusy={setBusy}
              setError={setError}
              setNotice={setNotice}
            />
          ) : null}

          {module === 'dossier' && planeReachable !== false ? (
            <ComposerDossierModule
              busy={busy}
              setBusy={setBusy}
              setError={setError}
              setNotice={setNotice}
              onNavigate={setModule}
            />
          ) : null}

          {module === 'documents' && planeReachable !== false ? (
            <DocumentsModule
              busy={busy}
              docs={docs}
              sources={sources}
              selectedId={selectedId}
              selectedDoc={selectedDoc}
              provenance={provenance}
              chunkProvenance={chunkProvenance}
              selectedChunkId={selectedChunkId}
              artifactPreview={artifactPreview}
              showRawProvenance={showRawProvenance}
              setShowRawProvenance={setShowRawProvenance}
              docStatus={docStatus}
              setDocStatus={setDocStatus}
              docType={docType}
              setDocType={setDocType}
              docSource={docSource}
              setDocSource={setDocSource}
              docQuery={docQuery}
              setDocQuery={setDocQuery}
              onApplyFilters={refresh}
              onOpenDoc={openDoc}
              onOpenChunk={openChunk}
              onRefresh={refresh}
              setBusy={setBusy}
              setError={setError}
              setNotice={setNotice}
            />
          ) : null}

          {module === 'jobs' && planeReachable !== false ? (
            <JobsModule
              busy={busy}
              jobs={jobs}
              sources={sources}
              crawlOptions={crawlOptions}
              onRunJob={runJob}
            />
          ) : null}

          {module === 'simulate' && planeReachable !== false ? (
            <SimulateModule busy={busy} setBusy={setBusy} setError={setError} />
          ) : null}

          {module === 'benchmark' && planeReachable !== false ? (
            <BenchmarkModule
              busy={busy}
              setBusy={setBusy}
              setError={setError}
              setNotice={setNotice}
            />
          ) : null}

          {module === 'improve' && planeReachable !== false ? (
            <ImproveModule
              busy={busy}
              setBusy={setBusy}
              setError={setError}
              setNotice={setNotice}
            />
          ) : null}

          {module === 'media' && planeReachable !== false ? (
            <MediaModule media={media} />
          ) : null}
        </main>
      </div>
    </section>
  )
}
