import { useMemo, useState } from 'react'
import type { KnowledgeMedia } from '../../api'

type Props = {
  media: KnowledgeMedia[]
}

export function MediaModule({ media }: Props) {
  const [kindFilter, setKindFilter] = useState('')
  const [diskOnly, setDiskOnly] = useState(false)

  const filtered = useMemo(() => {
    return media.filter((m) => {
      if (kindFilter && m.kind !== kindFilter) return false
      if (diskOnly && !m.exists_on_disk) return false
      return true
    })
  }, [media, kindFilter, diskOnly])

  const missing = media.filter((m) => !m.exists_on_disk).length

  return (
    <div className="kb-module">
      <header className="kb-module-head">
        <div>
          <h3>Media assets</h3>
          <p className="mute">Images, PD audio, and metadata blobs on durable disk — observability for media ingest.</p>
        </div>
      </header>

      <div className="row kb-media-toolbar">
        <label>
          Kind
          <select value={kindFilter} onChange={(e) => setKindFilter(e.target.value)}>
            <option value="">all</option>
            <option value="image">image</option>
            <option value="audio">audio</option>
            <option value="meta">meta</option>
          </select>
        </label>
        <label className="kb-check-label">
          <input type="checkbox" checked={diskOnly} onChange={(e) => setDiskOnly(e.target.checked)} />
          On disk only
        </label>
        <p className="mute">
          {filtered.length} shown · {missing} missing on disk
        </p>
      </div>

      <div className="kb-table-wrap">
        <table className="kb-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Kind</th>
              <th>Title</th>
              <th>Size</th>
              <th>License</th>
              <th>Disk</th>
              <th>Path</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((m) => (
              <tr key={m.id}>
                <td>#{m.id}</td>
                <td>{m.kind}</td>
                <td>{m.title.slice(0, 48)}</td>
                <td>{(m.byte_size / 1024).toFixed(1)} KiB</td>
                <td>{m.license_class}</td>
                <td>
                  <span
                    className={`doc-status doc-status-${m.exists_on_disk ? 'published' : 'quarantine'}`}
                  >
                    {m.exists_on_disk ? 'ok' : 'missing'}
                  </span>
                </td>
                <td className="kb-mono">{m.storage_path}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
