import { useMemo, useState, type FormEvent } from 'react'
import {
  createKnowledgeSource,
  patchKnowledgeSource,
  rejectKnowledgeSource,
  suspendKnowledgeSource,
  verifyKnowledgeSource,
  type KnowledgeSource,
} from '../../api'
import { SourceGateBadge } from '../components/SourceGateBadge'
import { REGISTERED_CONNECTORS } from '../constants'
import { sourceCanCrawl, verificationClass } from '../utils'

type Props = {
  busy: boolean
  sources: KnowledgeSource[]
  onRefresh: () => Promise<void>
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
}

export function SourceRegistryModule({
  busy,
  sources,
  onRefresh,
  setBusy,
  setError,
  setNotice,
}: Props) {
  const [filter, setFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [regId, setRegId] = useState('')
  const [regName, setRegName] = useState('')
  const [regConnector, setRegConnector] = useState('')
  const [regBaseUrls, setRegBaseUrls] = useState('')
  const [regNotes, setRegNotes] = useState('')
  const [showRegister, setShowRegister] = useState(false)

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase()
    return sources.filter((s) => {
      if (statusFilter && (s.verification_status || 'candidate') !== statusFilter) return false
      if (!q) return true
      return (
        s.id.toLowerCase().includes(q) ||
        s.name.toLowerCase().includes(q) ||
        (s.connector || '').toLowerCase().includes(q)
      )
    })
  }, [sources, filter, statusFilter])

  const selected = filtered.find((s) => s.id === selectedId) || filtered[0] || null

  const act = async (fn: () => Promise<unknown>, okMsg: string) => {
    setBusy(true)
    setError(null)
    try {
      await fn()
      setNotice(okMsg)
      await onRefresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'action failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="kb-module">
      <header className="kb-module-head">
        <div>
          <h3>Authority source registry</h3>
          <p className="mute">
            REQ-008 gate: crawl only when <strong>verified</strong> + <strong>enabled</strong> +{' '}
            <strong>connector registered</strong>. Manifest:{' '}
            <code>data/registry/sources.yaml</code>
          </p>
        </div>
        <button type="button" className="ghost" disabled={busy} onClick={() => setShowRegister((v) => !v)}>
          {showRegister ? 'Hide register' : 'Register candidate'}
        </button>
      </header>

      <div className="kb-registry-toolbar row">
        <label>
          Search
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="id, name, connector…"
            disabled={busy}
          />
        </label>
        <label>
          Status
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} disabled={busy}>
            <option value="">all</option>
            <option value="verified">verified</option>
            <option value="candidate">candidate</option>
            <option value="review">review</option>
            <option value="rejected">rejected</option>
            <option value="suspended">suspended</option>
          </select>
        </label>
        <p className="mute kb-registry-count">
          {filtered.length} source(s) · {sources.filter(sourceCanCrawl).length} crawl-ready
        </p>
      </div>

      <div className="kb-registry-layout">
        <div className="kb-table-wrap">
          <table className="kb-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Tier</th>
                <th>Status</th>
                <th>Gate</th>
                <th>License</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s) => (
                <tr
                  key={s.id}
                  className={selected?.id === s.id ? 'kb-row-selected' : ''}
                  onClick={() => setSelectedId(s.id)}
                >
                  <td>
                    <code>{s.id}</code>
                    <div className="mute">{s.name}</div>
                  </td>
                  <td>{s.tier}</td>
                  <td>
                    <span className={`badge ${verificationClass(s.verification_status)}`}>
                      {s.verification_status || 'candidate'}
                    </span>
                  </td>
                  <td>
                    <SourceGateBadge source={s} compact />
                  </td>
                  <td>{s.license_class}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {selected ? (
          <aside className="kb-registry-detail" aria-label="Source detail">
            <h4>{selected.name}</h4>
            <p>
              <code>{selected.id}</code> · {selected.origin_class || 'encyclopedia'}
            </p>
            <SourceGateBadge source={selected} />
            <dl className="kb-dl">
              <dt>Connector</dt>
              <dd>
                {selected.connector || '(none)'}
                {selected.connector_registered === false ? (
                  <span className="warn"> — not registered</span>
                ) : null}
                {selected.connector_semver ? ` @ ${selected.connector_semver}` : ''}
              </dd>
              <dt>Rate limit</dt>
              <dd>{selected.rate_limit_qps} qps</dd>
              <dt>Registry rev</dt>
              <dd>{selected.registry_revision || '—'}</dd>
              <dt>Verified by</dt>
              <dd>{selected.verified_by || '—'}</dd>
              <dt>Base URLs</dt>
              <dd>
                <ul className="plain kb-url-list">
                  {(selected.base_urls || []).map((u) => (
                    <li key={u}>
                      <code>{u}</code>
                    </li>
                  ))}
                </ul>
              </dd>
              <dt>Notes</dt>
              <dd>{selected.notes || '—'}</dd>
              <dt>ToS</dt>
              <dd>{selected.tos_notes || '—'}</dd>
              <dt>Attribution</dt>
              <dd>{selected.attribution_template || '—'}</dd>
            </dl>
            <div className="row kb-registry-actions">
              <button
                type="button"
                className="ghost"
                disabled={busy}
                onClick={() =>
                  void act(
                    () => patchKnowledgeSource(selected.id, { enabled: !selected.enabled }),
                    `${selected.id} ${selected.enabled ? 'disabled' : 'enabled'}`,
                  )
                }
              >
                {selected.enabled ? 'Disable' : 'Enable'}
              </button>
              <button
                type="button"
                disabled={busy || selected.verification_status === 'verified'}
                onClick={() => void act(() => verifyKnowledgeSource(selected.id), `Verified ${selected.id}`)}
              >
                Verify
              </button>
              <button
                type="button"
                className="ghost"
                disabled={busy}
                onClick={() => void act(() => rejectKnowledgeSource(selected.id), `Rejected ${selected.id}`)}
              >
                Reject
              </button>
              <button
                type="button"
                className="ghost"
                disabled={busy || selected.verification_status === 'suspended'}
                onClick={() => void act(() => suspendKnowledgeSource(selected.id), `Suspended ${selected.id}`)}
              >
                Suspend
              </button>
            </div>
          </aside>
        ) : null}
      </div>

      {showRegister ? (
        <section className="kb-panel-card kb-register-panel">
          <h4>Register candidate source</h4>
          <form
            className="knowledge-register"
            onSubmit={(e: FormEvent) => {
              e.preventDefault()
              const id = regId.trim()
              if (!id) {
                setError('Source id required')
                return
              }
              void act(async () => {
                await createKnowledgeSource({
                  id,
                  name: regName.trim() || id,
                  connector: regConnector.trim(),
                  base_urls: regBaseUrls
                    .split(/[\n,]+/)
                    .map((u) => u.trim())
                    .filter(Boolean),
                  notes: regNotes.trim(),
                  origin_class: 'encyclopedia',
                })
                setRegId('')
                setRegName('')
                setRegConnector('')
                setRegBaseUrls('')
                setRegNotes('')
              }, `Registered candidate ${id}`)
            }}
          >
            <label>
              Id
              <input value={regId} onChange={(e) => setRegId(e.target.value)} disabled={busy} required />
            </label>
            <label>
              Name
              <input value={regName} onChange={(e) => setRegName(e.target.value)} disabled={busy} />
            </label>
            <label>
              Connector
              <input
                value={regConnector}
                onChange={(e) => setRegConnector(e.target.value)}
                list="kb-connector-list"
                placeholder="wikidata"
                disabled={busy}
              />
              <datalist id="kb-connector-list">
                {REGISTERED_CONNECTORS.map((c) => (
                  <option key={c} value={c} />
                ))}
              </datalist>
            </label>
            <label>
              Base URLs
              <textarea
                value={regBaseUrls}
                onChange={(e) => setRegBaseUrls(e.target.value)}
                placeholder="https://example.org/"
                disabled={busy}
                rows={2}
              />
            </label>
            <label>
              Notes
              <input value={regNotes} onChange={(e) => setRegNotes(e.target.value)} disabled={busy} />
            </label>
            <button type="submit" disabled={busy}>
              Register candidate
            </button>
          </form>
        </section>
      ) : null}
    </div>
  )
}
