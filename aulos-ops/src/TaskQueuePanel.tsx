import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  fetchOpsTask,
  fetchOpsTaskDashboard,
  fetchOpsTasks,
  type OpsTaskDashboard,
  type OpsTaskRow,
} from './api'
import { formatDateTime } from './time'

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
}

export function TaskQueuePanel({ busy, setBusy, setError }: Props) {
  const [dashboard, setDashboard] = useState<OpsTaskDashboard | null>(null)
  const [rows, setRows] = useState<OpsTaskRow[]>([])
  const [statusFilter, setStatusFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [selected, setSelected] = useState<OpsTaskRow | null>(null)

  const refresh = useCallback(async () => {
    const [dash, list] = await Promise.all([
      fetchOpsTaskDashboard(),
      fetchOpsTasks({
        status: statusFilter || undefined,
        task_type: typeFilter || undefined,
        source: sourceFilter || undefined,
        limit: 80,
      }),
    ])
    setDashboard(dash)
    setRows(list)
  }, [statusFilter, typeFilter, sourceFilter])

  useEffect(() => {
    void (async () => {
      setBusy(true)
      setError(null)
      try {
        await refresh()
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load tasks')
      } finally {
        setBusy(false)
      }
    })()
  }, [refresh, setBusy, setError])

  const onFilter = (e: FormEvent) => {
    e.preventDefault()
    void refresh().catch((err) => setError(err instanceof Error ? err.message : 'Filter failed'))
  }

  return (
    <section className="settings task-queue" aria-labelledby="task-queue-title">
      <div className="section-head">
        <h2 id="task-queue-title">Task queue</h2>
        <button type="button" className="refresh" disabled={busy} onClick={() => void refresh()}>
          Refresh
        </button>
      </div>
      <p className="settings-lead">
        Background jobs by source and type — mail, listening guides, Ops tasks (e.g. dev blog
        generate). Non-blocking; poll status here.
      </p>

      {dashboard ? (
        <div className="task-queue-cards">
          {dashboard.queues.map((q) => (
            <article key={`${q.source}:${q.task_type}`} className="task-queue-card">
              <h3>{q.label}</h3>
              <p className="meta">{q.task_type}</p>
              <p>
                Depth: {q.depth ?? '—'} · Worker: {q.worker_started ? 'on' : 'off'}
                {typeof q.active_jobs === 'number' ? ` · Active: ${q.active_jobs}` : ''}
              </p>
            </article>
          ))}
        </div>
      ) : null}

      <form className="dev-blog-toolbar dev-blog-filters" onSubmit={onFilter}>
        <label>
          Status
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} disabled={busy}>
            <option value="">All</option>
            <option value="queued">queued</option>
            <option value="running">running</option>
            <option value="completed">completed</option>
            <option value="failed">failed</option>
          </select>
        </label>
        <label>
          Task type
          <input
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            placeholder="dev_blog.generate"
            disabled={busy}
          />
        </label>
        <label>
          Source
          <input
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            placeholder="ops.dev_blog"
            disabled={busy}
          />
        </label>
        <button type="submit" disabled={busy}>
          Filter
        </button>
      </form>

      <div className="task-queue-layout">
        <ul className="task-queue-list">
          {rows.length === 0 ? (
            <li className="meta">No tasks match.</li>
          ) : (
            rows.map((row) => (
              <li key={row.id}>
                <button
                  type="button"
                  className={selected?.id === row.id ? 'task-row active' : 'task-row'}
                  onClick={() =>
                    void fetchOpsTask(row.id)
                      .then(setSelected)
                      .catch((err) => setError(err instanceof Error ? err.message : 'Load failed'))
                  }
                >
                  <span className="task-row-head">
                    #{row.id} · {row.status} · {row.task_type}
                  </span>
                  <span className="meta">
                    {row.source} · {formatDateTime(row.created_at)}
                  </span>
                </button>
              </li>
            ))
          )}
        </ul>
        <aside className="task-queue-detail">
          {!selected ? (
            <p className="meta">Select a task for payload / result.</p>
          ) : (
            <>
              <h3>
                Task #{selected.id} — {selected.status}
              </h3>
              <p className="meta">
                {selected.task_type} · {selected.source}
              </p>
              {selected.error_detail ? <p className="error-inline">{selected.error_detail}</p> : null}
              <h4>Payload</h4>
              <pre className="task-json">{JSON.stringify(selected.payload, null, 2)}</pre>
              <h4>Result</h4>
              <pre className="task-json">{JSON.stringify(selected.result, null, 2)}</pre>
            </>
          )}
        </aside>
      </div>
    </section>
  )
}
