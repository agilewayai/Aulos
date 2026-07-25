import { useCallback, useEffect, useState } from 'react'
import {
  enqueueDbSync,
  fetchDbHa,
  setDbActiveRole,
  type DbHaStatus,
} from './api'

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
}

export function DbHaPanel({ busy, setBusy, setError, setNotice }: Props) {
  const [ha, setHa] = useState<DbHaStatus | null>(null)

  const load = useCallback(async () => {
    try {
      setHa(await fetchDbHa())
    } catch (err) {
      setHa(null)
      setError(err instanceof Error ? err.message : 'DB HA status failed')
    }
  }, [setError])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <section className="settings" aria-labelledby="dbha-title">
      <div className="section-head">
        <h2 id="dbha-title">Business DB HA</h2>
        <button type="button" className="ghost" disabled={busy} onClick={() => void load()}>
          Refresh
        </button>
      </div>
      <p className="lede">
        Primary Postgres for live traffic; SQLite failover mirror kept in sync via Redis queue + scheduled
        clone. Switch role if PG is down.
      </p>
      {ha ? (
        <>
          <p className="plane-status-row">
            <span
              className={
                ha.active_role === 'primary' ? 'plane-badge plane-badge-ok' : 'plane-badge plane-badge-down'
              }
            >
              {ha.active_role}
            </span>{' '}
            primary={ha.primary.dialect}/{ha.primary.ok ? 'up' : 'down'} · failover=
            {ha.failover.configured
              ? `${ha.failover.dialect}/${ha.failover.ok ? 'up' : 'down'}`
              : 'not configured'}{' '}
            · auto_failover={String(ha.auto_failover)} · interval={ha.sync_interval_sec}s
          </p>
          <p className="mute">
            Last sync: {ha.sync.status} · {ha.sync.at || 'never'} · trigger={ha.sync.trigger || '—'} · rows=
            {ha.sync.row_total ?? '—'} · {ha.sync.duration_ms ?? '—'}ms
            {ha.sync.error ? ` · err=${ha.sync.error}` : ''}
          </p>
          <div className="row">
            <button
              type="button"
              disabled={busy || !ha.failover.configured}
              onClick={() => {
                void (async () => {
                  setBusy(true)
                  setError(null)
                  try {
                    const r = await enqueueDbSync(true)
                    setNotice(
                      'queued' in r && r.queued
                        ? `Sync queued (depth=${r.depth})`
                        : `Sync done rows=${(r as { row_total?: number }).row_total ?? '?'}`,
                    )
                    await load()
                  } catch (err) {
                    setError(err instanceof Error ? err.message : 'sync failed')
                  } finally {
                    setBusy(false)
                  }
                })()
              }}
            >
              Enqueue sync (Redis)
            </button>
            <button
              type="button"
              className="ghost"
              disabled={busy || !ha.failover.configured}
              onClick={() => {
                void (async () => {
                  setBusy(true)
                  setError(null)
                  try {
                    const r = await enqueueDbSync(false)
                    setNotice(`Inline sync ${(r as { status?: string }).status} rows=${(r as { row_total?: number }).row_total}`)
                    await load()
                  } catch (err) {
                    setError(err instanceof Error ? err.message : 'sync failed')
                  } finally {
                    setBusy(false)
                  }
                })()
              }}
            >
              Sync now (inline)
            </button>
            <button
              type="button"
              className="ghost"
              disabled={busy || ha.active_role === 'primary'}
              onClick={() => {
                void (async () => {
                  setBusy(true)
                  try {
                    await setDbActiveRole('primary')
                    setNotice('Active role → primary (Postgres)')
                    await load()
                  } catch (err) {
                    setError(err instanceof Error ? err.message : 'role switch failed')
                  } finally {
                    setBusy(false)
                  }
                })()
              }}
            >
              Use primary
            </button>
            <button
              type="button"
              className="ghost"
              disabled={busy || !ha.failover.configured || ha.active_role === 'failover'}
              onClick={() => {
                void (async () => {
                  setBusy(true)
                  try {
                    await setDbActiveRole('failover')
                    setNotice('Active role → failover (SQLite)')
                    await load()
                  } catch (err) {
                    setError(err instanceof Error ? err.message : 'role switch failed')
                  } finally {
                    setBusy(false)
                  }
                })()
              }}
            >
              Fail over to SQLite
            </button>
          </div>
        </>
      ) : (
        <p className="muted">HA status not loaded (is API up with failover URL configured?).</p>
      )}
    </section>
  )
}
