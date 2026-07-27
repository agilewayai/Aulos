type Props = {
  title: string
  provenance: Record<string, unknown> | null
  artifactPreview?: string
  showRaw?: boolean
}

function asRecord(v: unknown): Record<string, unknown> | null {
  return v && typeof v === 'object' && !Array.isArray(v) ? (v as Record<string, unknown>) : null
}

export function ProvenanceCard({ title, provenance, artifactPreview = '', showRaw = false }: Props) {
  if (!provenance) return <p className="muted">No provenance loaded.</p>

  const doc = asRecord(provenance.document)
  const chunk = asRecord(provenance.chunk)
  const source = asRecord(provenance.source)
  const artifact = asRecord(provenance.artifact)
  const job = asRecord(provenance.job)
  const chunks = Array.isArray(provenance.chunks) ? provenance.chunks : []

  return (
    <div className="kb-provenance">
      <h4>{title}</h4>
      <div className="kb-provenance-grid">
        {chunk ? (
          <article className="kb-prov-card">
            <h5>Chunk</h5>
            <dl>
              <dt>ID</dt>
              <dd>{String(chunk.id ?? '—')}</dd>
              <dt>Section</dt>
              <dd>{String(chunk.section ?? '—')}</dd>
              <dt>work_id</dt>
              <dd>
                <code>{String(chunk.aulos_work_id || '—')}</code>
              </dd>
            </dl>
            {chunk.text ? <pre className="kb-prov-snippet">{String(chunk.text).slice(0, 400)}</pre> : null}
          </article>
        ) : null}

        {doc ? (
          <article className="kb-prov-card">
            <h5>Document</h5>
            <dl>
              <dt>ID</dt>
              <dd>{String(doc.id ?? '—')}</dd>
              <dt>Status</dt>
              <dd>
                <span className={`doc-status doc-status-${doc.status || 'quarantine'}`}>
                  {String(doc.status ?? '—')}
                </span>
              </dd>
              <dt>Extractor</dt>
              <dd>{String(doc.extractor_version ?? '—')}</dd>
              <dt>License</dt>
              <dd>{String(doc.license_class ?? '—')}</dd>
              <dt>Entity</dt>
              <dd>
                {String(doc.entity_type ?? '—')}/{String(doc.entity_id ?? '—')}
              </dd>
            </dl>
          </article>
        ) : null}

        {source ? (
          <article className="kb-prov-card">
            <h5>Source</h5>
            <dl>
              <dt>ID</dt>
              <dd>
                <code>{String(source.id ?? '—')}</code>
              </dd>
              <dt>Tier</dt>
              <dd>{String(source.tier ?? '—')}</dd>
              <dt>Connector</dt>
              <dd>{String(source.connector ?? '—')}</dd>
              <dt>Verification</dt>
              <dd>{String(source.verification_status ?? '—')}</dd>
            </dl>
          </article>
        ) : null}

        {artifact ? (
          <article className="kb-prov-card">
            <h5>Artifact</h5>
            <dl>
              <dt>Hash</dt>
              <dd>
                <code className="kb-hash">{String(artifact.content_hash ?? '—')}</code>
              </dd>
              <dt>Path</dt>
              <dd className="kb-mono">{String(artifact.storage_path ?? '—')}</dd>
              <dt>URL</dt>
              <dd className="kb-mono">{String(artifact.source_url ?? '—')}</dd>
              <dt>Size</dt>
              <dd>{artifact.byte_size != null ? `${artifact.byte_size} B` : '—'}</dd>
            </dl>
          </article>
        ) : null}

        {job ? (
          <article className="kb-prov-card">
            <h5>Job</h5>
            <dl>
              <dt>ID</dt>
              <dd>#{String(job.id ?? '—')}</dd>
              <dt>Status</dt>
              <dd>{String(job.status ?? '—')}</dd>
              <dt>Error</dt>
              <dd>{String(job.error || '—')}</dd>
            </dl>
          </article>
        ) : null}
      </div>

      {!chunk && chunks.length ? (
        <p className="mute">{chunks.length} chunk(s) on document — open one from the list.</p>
      ) : null}

      {artifactPreview ? (
        <>
          <h5>Artifact preview</h5>
          <pre className="code-block knowledge-body">{artifactPreview}</pre>
        </>
      ) : null}

      {showRaw ? (
        <>
          <h5>Raw JSON</h5>
          <pre className="code-block">{JSON.stringify(provenance, null, 2)}</pre>
        </>
      ) : null}
    </div>
  )
}
