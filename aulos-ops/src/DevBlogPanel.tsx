import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import {
  fetchDevBlogList,
  fetchDevBlogPost,
  fetchOpsTask,
  generateDevBlog,
  type DevBlogListFilters,
  type DevBlogPost,
  type DevBlogSummary,
} from './api'
import { requestAssetVersionCheck } from './assetVersion'
import { formatDateTime } from './time'
import { DevBlogMarkdown } from './devBlogMarkdown'

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
}

function utcToday(): string {
  return new Date().toISOString().slice(0, 10)
}

export function DevBlogPanel({ setError, setNotice }: Props) {
  const [rows, setRows] = useState<DevBlogSummary[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [evidenceDay, setEvidenceDay] = useState(utcToday())
  const [filterDay, setFilterDay] = useState('')
  const [filterFrom, setFilterFrom] = useState('')
  const [filterTo, setFilterTo] = useState('')
  const [keyword, setKeyword] = useState('')
  const [post, setPost] = useState<DevBlogPost | null>(null)
  const [showEvidence, setShowEvidence] = useState(false)
  const [listLoading, setListLoading] = useState(false)
  const [postLoadingId, setPostLoadingId] = useState<number | null>(null)
  const [generating, setGenerating] = useState(false)
  const [pendingTasks, setPendingTasks] = useState<number[]>([])
  const pendingRef = useRef(pendingTasks)

  useEffect(() => {
    pendingRef.current = pendingTasks
  }, [pendingTasks])

  const listFilters = useCallback((): DevBlogListFilters => {
    const f: DevBlogListFilters = { limit: 100 }
    if (filterDay.trim()) f.day = filterDay.trim()
    if (filterFrom.trim()) f.dayFrom = filterFrom.trim()
    if (filterTo.trim()) f.dayTo = filterTo.trim()
    if (keyword.trim()) f.q = keyword.trim()
    return f
  }, [filterDay, filterFrom, filterTo, keyword])

  const applyFilters = useCallback(
    async (overrides?: Partial<DevBlogListFilters>) => {
      const f: DevBlogListFilters = { limit: 100, ...listFilters(), ...overrides }
      const list = await fetchDevBlogList(f)
      setRows(list)
      if (overrides?.day) setFilterDay(overrides.day)
      return list
    },
    [listFilters],
  )

  const refreshList = useCallback(async () => {
    setListLoading(true)
    try {
      return await applyFilters()
    } finally {
      setListLoading(false)
    }
  }, [applyFilters])

  const loadPost = useCallback(async (postId: number) => {
    setPostLoadingId(postId)
    setSelectedId(postId)
    try {
      const data = await fetchDevBlogPost(postId)
      setPost(data)
      setEvidenceDay(data.day)
    } finally {
      setPostLoadingId(null)
    }
  }, [])

  useEffect(() => {
    requestAssetVersionCheck()
  }, [])

  useEffect(() => {
    void (async () => {
      setError(null)
      try {
        await refreshList()
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load blog list')
      }
    })()
  }, [refreshList, setError])

  useEffect(() => {
    if (pendingTasks.length === 0) return

    let cancelled = false
    const poll = async () => {
      requestAssetVersionCheck()
      const ids = [...pendingRef.current]
      if (ids.length === 0) return

      for (const taskId of ids) {
        try {
          const row = await fetchOpsTask(taskId)
          if (cancelled) return
          if (row.status !== 'completed' && row.status !== 'failed') continue

          setPendingTasks((prev) => prev.filter((id) => id !== taskId))

          if (row.status === 'failed') {
            setError(row.error_detail || `Task #${taskId} failed`)
            continue
          }

          const postId = row.result?.post_id
          setNotice(`Blog task #${taskId} completed.`)
          await refreshList()
          if (typeof postId === 'number') {
            await loadPost(postId)
          }
        } catch (err) {
          if (!cancelled) {
            setError(err instanceof Error ? err.message : `Task #${taskId} poll failed`)
          }
        }
      }
    }

    void poll()
    const timer = window.setInterval(() => void poll(), 2000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [pendingTasks, loadPost, refreshList, setError, setNotice])

  const onApplyFilters = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    try {
      const list = await refreshList()
      if (list.length === 0) {
        setPost(null)
        setSelectedId(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Filter failed')
    }
  }

  const onClearFilters = () => {
    setFilterDay('')
    setFilterFrom('')
    setFilterTo('')
    setKeyword('')
    setError(null)
    setListLoading(true)
    void fetchDevBlogList({ limit: 100 })
      .then((list) => setRows(list))
      .catch((err) => setError(err instanceof Error ? err.message : 'Clear failed'))
      .finally(() => setListLoading(false))
  }

  const onFilterByRowDay = (day: string) => {
    setFilterDay(day)
    setFilterFrom('')
    setFilterTo('')
    void applyFilters({ day, dayFrom: undefined, dayTo: undefined }).catch((err) =>
      setError(err instanceof Error ? err.message : 'Filter failed'),
    )
  }

  const enqueueGenerate = async (day: string, options?: { force?: boolean; postId?: number }) => {
    setGenerating(true)
    setError(null)
    setNotice(null)
    try {
      const accepted = await generateDevBlog(day, options)
      setEvidenceDay(day)

      if (accepted.status === 'completed') {
        if (typeof accepted.post_id === 'number') {
          await loadPost(accepted.post_id)
        }
        await refreshList()
        setNotice(`Blog task #${accepted.task_id} completed.`)
        return
      }

      setPendingTasks((prev) =>
        prev.includes(accepted.task_id) ? prev : [...prev, accepted.task_id],
      )
      setNotice(
        `Blog task #${accepted.task_id} queued — you can keep working; the post will open when ready.`,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generate failed')
    } finally {
      setGenerating(false)
    }
  }

  const onGenerate = () => {
    const day = evidenceDay.trim() || utcToday()
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) {
      setError('Evidence day must be YYYY-MM-DD (UTC)')
      return
    }
    void enqueueGenerate(day)
  }

  const onRegenerate = () => {
    if (!post) return
    const day = evidenceDay.trim() || post.day
    void enqueueGenerate(day, { force: true, postId: post.id })
  }

  return (
    <section className="settings dev-blog" aria-labelledby="dev-blog-title">
      <div className="section-head">
        <h2 id="dev-blog-title">Dev Blog</h2>
        <button
          type="button"
          className="refresh"
          disabled={listLoading}
          onClick={() =>
            void refreshList().catch((err) =>
              setError(err instanceof Error ? err.message : 'Refresh failed'),
            )
          }
        >
          Refresh
        </button>
      </div>
      <p className="settings-lead">
        Internal development trace — factual summaries from git + harness evidence. On-demand
        generation; not for external publish. See SPEC-017 writing contract.
      </p>

      {pendingTasks.length > 0 ? (
        <p className="dev-blog-pending meta" role="status">
          {pendingTasks.length} background task{pendingTasks.length === 1 ? '' : 's'} running
          {pendingTasks.map((id) => ` #${id}`).join(',')} — page stays interactive.
        </p>
      ) : null}

      <form className="dev-blog-toolbar dev-blog-filters" onSubmit={(e) => void onApplyFilters(e)}>
        <label>
          Evidence day (generate)
          <input
            type="date"
            value={evidenceDay}
            onChange={(e) => setEvidenceDay(e.target.value)}
            disabled={generating}
          />
        </label>
        <button type="button" disabled={generating} onClick={onGenerate}>
          {generating ? 'Submitting…' : 'Generate new'}
        </button>
        <button
          type="button"
          className="ghost"
          disabled={generating || !post}
          onClick={onRegenerate}
        >
          Regenerate selected
        </button>
      </form>

      <form className="dev-blog-toolbar dev-blog-filters" onSubmit={(e) => void onApplyFilters(e)}>
        <label>
          Exact day
          <input
            type="date"
            value={filterDay}
            onChange={(e) => setFilterDay(e.target.value)}
            disabled={listLoading}
          />
        </label>
        <label>
          From
          <input
            type="date"
            value={filterFrom}
            onChange={(e) => setFilterFrom(e.target.value)}
            disabled={listLoading}
          />
        </label>
        <label>
          To
          <input
            type="date"
            value={filterTo}
            onChange={(e) => setFilterTo(e.target.value)}
            disabled={listLoading}
          />
        </label>
        <label className="dev-blog-keyword">
          Keyword
          <input
            type="search"
            placeholder="标题或正文关键词"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            disabled={listLoading}
          />
        </label>
        <button type="submit" disabled={listLoading}>
          Search
        </button>
        <button type="button" className="ghost" disabled={listLoading} onClick={onClearFilters}>
          Clear
        </button>
      </form>

      <div className="dev-blog-layout">
        <aside className="dev-blog-days" aria-label="Saved posts">
          <h3 className="dev-blog-aside-title">Posts ({rows.length})</h3>
          {rows.length === 0 ? (
            <p className="meta">No posts match — generate one or clear filters.</p>
          ) : (
            <ul className="dev-blog-day-list">
              {rows.map((row) => (
                <li key={row.id}>
                  <button
                    type="button"
                    className={
                      row.id === selectedId ? 'dev-blog-day active' : 'dev-blog-day'
                    }
                    disabled={postLoadingId === row.id}
                    onClick={() =>
                      void loadPost(row.id).catch((err) =>
                        setError(err instanceof Error ? err.message : 'Load failed'),
                      )
                    }
                  >
                    <span className="dev-blog-day-date">
                      {row.day}
                      <span className="dev-blog-post-id">#{row.id}</span>
                    </span>
                    <span className="dev-blog-day-title">{row.title || 'Untitled'}</span>
                    <span className="dev-blog-day-meta">
                      {row.provider} · {formatDateTime(row.generated_at)}
                    </span>
                    <span
                      role="link"
                      className="dev-blog-filter-day"
                      onClick={(e) => {
                        e.stopPropagation()
                        onFilterByRowDay(row.day)
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.stopPropagation()
                          onFilterByRowDay(row.day)
                        }
                      }}
                      tabIndex={0}
                    >
                      Filter {row.day}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <article className="dev-blog-article" aria-live="polite">
          {!post ? (
            <p className="meta">
              Select a post from the list, or generate a new story from an evidence day.
            </p>
          ) : (
            <>
              <header className="dev-blog-article-head">
                <p className="meta">
                  #{post.id} · evidence {post.day} · {post.provider} ·{' '}
                  {formatDateTime(post.generated_at)}
                </p>
                <button
                  type="button"
                  className="ghost"
                  onClick={() => setShowEvidence((v) => !v)}
                >
                  {showEvidence ? 'Hide evidence' : 'Show evidence'}
                </button>
              </header>
              <DevBlogMarkdown source={post.body_md} />
              {showEvidence && post.evidence ? (
                <div className="dev-blog-evidence">
                  <h4>Evidence</h4>
                  <p className="meta">
                    {post.evidence.commit_count ?? 0} commits
                    {post.evidence.repo_root ? ` · ${post.evidence.repo_root}` : ''}
                  </p>
                  {post.evidence.commits && post.evidence.commits.length > 0 ? (
                    <ul className="dev-blog-list">
                      {post.evidence.commits.slice(0, 20).map((c) => (
                        <li key={c.sha}>
                          <code>{c.sha}</code> {c.subject}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  {post.evidence.harness_sources && post.evidence.harness_sources.length > 0 ? (
                    <>
                      <p className="meta">Harness sources</p>
                      <ul className="dev-blog-list">
                        {post.evidence.harness_sources.map((h) => (
                          <li key={`${h.project}:${h.path}`}>
                            {h.project}: {h.path}
                          </li>
                        ))}
                      </ul>
                    </>
                  ) : null}
                </div>
              ) : null}
            </>
          )}
        </article>
      </div>
    </section>
  )
}
