import { useState } from 'react'
import {
  publishKnowledgeDocument,
  quarantineKnowledgeDocument,
  type KnowledgeChunk,
  type KnowledgeDoc,
  type KnowledgeSource,
} from '../../api'
import { ProvenanceCard } from '../components/ProvenanceCard'
import type { DocStatusFilter } from '../types'

type Props = {
  busy: boolean
  docs: KnowledgeDoc[]
  sources: KnowledgeSource[]
  selectedId: number | null
  selectedDoc: KnowledgeDoc | null
  provenance: Record<string, unknown> | null
  chunkProvenance: Record<string, unknown> | null
  selectedChunkId: number | null
  artifactPreview: string
  showRawProvenance: boolean
  setShowRawProvenance: (v: boolean) => void
  docStatus: DocStatusFilter
  setDocStatus: (v: DocStatusFilter) => void
  docType: string
  setDocType: (v: string) => void
  docSource: string
  setDocSource: (v: string) => void
  docQuery: string
  setDocQuery: (v: string) => void
  onApplyFilters: () => void
  onOpenDoc: (id: number) => Promise<void>
  onOpenChunk: (id: number) => Promise<void>
  onRefresh: () => Promise<void>
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
}

export function DocumentsModule({
  busy,
  docs,
  sources,
  selectedId,
  selectedDoc,
  provenance,
  chunkProvenance,
  selectedChunkId,
  artifactPreview,
  showRawProvenance,
  setShowRawProvenance,
  docStatus,
  setDocStatus,
  docType,
  setDocType,
  docSource,
  setDocSource,
  docQuery,
  setDocQuery,
  onApplyFilters,
  onOpenDoc,
  onOpenChunk,
  onRefresh,
  setBusy,
  setError,
  setNotice,
}: Props) {
  const [provTab, setProvTab] = useState<'doc' | 'chunk'>('doc')

  return (
    <div className="kb-module">
      <header className="kb-module-head">
        <div>
          <h3>Documents & verification</h3>
          <p className="mute">Query corpus, proofread (publish / quarantine), audit document and chunk provenance.</p>
        </div>
      </header>

      <div className="knowledge-filters row kb-doc-filters">
        <label>
          Status
          <select
            value={docStatus}
            onChange={(e) => setDocStatus(e.target.value as DocStatusFilter)}
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
            <option value="history">history</option>
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
            placeholder="title, body, work_id, entity_id…"
          />
        </label>
        <button type="button" disabled={busy} onClick={() => void onApplyFilters()}>
          Query
        </button>
      </div>

      <div className="knowledge-split kb-doc-split">
        <div className="knowledge-list-col">
          <h4>Results ({docs.length})</h4>
          <ul className="plain knowledge-doc-list">
            {docs.map((d) => (
              <li key={d.id} className={selectedId === d.id ? 'selected' : ''}>
                <button type="button" className="doc-pick" onClick={() => void onOpenDoc(d.id)}>
                  <span className={`doc-status doc-status-${d.status}`}>{d.status}</span>
                  <strong>#{d.id}</strong> {d.title}
                  <span className="mute">
                    {d.source_id} · {d.entity_type || '—'} · {d.aulos_work_id || d.entity_id || ''}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="knowledge-detail-col" aria-live="polite">
          {selectedDoc ? (
            <>
              <div className="section-head">
                <h4>#{selectedDoc.id} — {selectedDoc.title}</h4>
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
                            await onRefresh()
                            await onOpenDoc(selectedDoc.id)
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
                            await onRefresh()
                            await onOpenDoc(selectedDoc.id)
                          } catch (err) {
                            setError(err instanceof Error ? err.message : 'publish failed')
                          } finally {
                            setBusy(false)
                          }
                        })()
                      }}
                    >
                      Publish (verify)
                    </button>
                  )}
                  <label className="kb-raw-toggle">
                    <input
                      type="checkbox"
                      checked={showRawProvenance}
                      onChange={(e) => setShowRawProvenance(e.target.checked)}
                    />
                    Raw JSON
                  </label>
                </div>
              </div>
              <p className="mute">
                {selectedDoc.source_id} · {selectedDoc.license_class} · extractor {selectedDoc.extractor_version}
              </p>
              <h5>Body</h5>
              <pre className="code-block knowledge-body">{selectedDoc.body || ''}</pre>

              <h5>Chunks</h5>
              {selectedDoc.chunks?.length ? (
                <ul className="plain knowledge-chunks">
                  {selectedDoc.chunks.map((c: KnowledgeChunk) => (
                    <li key={c.id}>
                      <button
                        type="button"
                        className="doc-pick"
                        disabled={busy}
                        onClick={() => {
                          setProvTab('chunk')
                          void onOpenChunk(c.id)
                        }}
                      >
                        #{c.id} · {c.section || '(section)'} · {c.text_len ?? 0} chars
                        {selectedChunkId === c.id ? ' ←' : ''}
                      </button>
                      <div className="mute">{c.text_preview || ''}</div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mute">No chunks.</p>
              )}

              <nav className="kb-prov-tabs" aria-label="Provenance view">
                <button
                  type="button"
                  className={provTab === 'doc' ? 'tab active' : 'tab'}
                  onClick={() => setProvTab('doc')}
                >
                  Document provenance
                </button>
                <button
                  type="button"
                  className={provTab === 'chunk' ? 'tab active' : 'tab'}
                  disabled={!chunkProvenance}
                  onClick={() => setProvTab('chunk')}
                >
                  Chunk provenance
                </button>
              </nav>
              <ProvenanceCard
                title={provTab === 'chunk' ? `Chunk #${selectedChunkId}` : `Document #${selectedDoc.id}`}
                provenance={provTab === 'chunk' ? chunkProvenance : provenance}
                artifactPreview={provTab === 'doc' ? artifactPreview : ''}
                showRaw={showRawProvenance}
              />
            </>
          ) : (
            <p className="muted">Select a document to verify content and inspect provenance.</p>
          )}
        </div>
      </div>
    </div>
  )
}
