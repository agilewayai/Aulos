import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  fetchDevBlogList,
  fetchDevBlogPost,
  generateDevBlog,
  waitForOpsTask,
  type DevBlogListFilters,
  type DevBlogPost,
  type DevBlogSummary,
} from './api'
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

export function DevBlogPanel({ busy, setBusy, setError, setNotice }: Props) {
  const [rows, setRows] = useState<DevBlogSummary[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [evidenceDay, setEvidenceDay] = useState(utcToday())
  const [filterDay, setFilterDay] = useState('')
  const [filterFrom, setFilterFrom] = useState('')
  const [filterTo, setFilterTo] = useState('')
  const [keyword, setKeyword] = useState('')
  const [post, setPost] = useState<DevBlogPost | null>(null)
  const [showEvidence, setShowEvidence] = useState(false)

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

  const refreshList = useCallback(async () => applyFilters(), [applyFilters])

  const loadPost = useCallback(async (postId: number) => {
    setSelectedId(postId)
    const data = await fetchDevBlogPost(postId)
    setPost(data)
    setEvidenceDay(data.day)
  }, [])

  useEffect(() => {
    void (async () => {
      setBusy(true)
      setError(null)
      try {
        await refreshList()
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load blog list')
      } finally {
        setBusy(false)
      }
    })()
  }, [refreshList, setBusy, setError])

  const onApplyFilters = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const list = await refreshList()
      if (list.length === 0) {
        setPost(null)
        setSelectedId(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Filter failed')
    } finally {
      setBusy(false)
    }
  }

  const onClearFilters = () => {
    setFilterDay('')
    setFilterFrom('')
    setFilterTo('')
    setKeyword('')
    setBusy(true)
    setError(null)
    void fetchDevBlogList({ limit: 100 })
      .then((list) => setRows(list))
      .catch((err) => setError(err instanceof Error ? err.message : 'Clear failed'))
      .finally(() => setBusy(false))
  }

  const onFilterByRowDay = (day: string) => {
    setFilterDay(day)
    setFilterFrom('')
    setFilterTo('')
    void applyFilters({ day, dayFrom: undefined, dayTo: undefined }).catch((err) =>
      setError(err instanceof Error ? err.message : 'Filter failed'),
    )
  }

  const resolvePostFromTask = async (taskId: number, immediatePostId?: number | null) => {
    if (immediatePostId) {
      await loadPost(immediatePostId)
      return
    }
    const done = await waitForOpsTask(taskId)
    if (done.status === 'failed') {
      throw new Error(done.error_detail || `Task ${taskId} failed`)
    }
    const postId = done.result?.post_id
    if (typeof postId === 'number') {
      await loadPost(postId)
    }
  }

  const onGenerate = async () => {
    const day = evidenceDay.trim() || utcToday()
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) {
      setError('Evidence day must be YYYY-MM-DD (UTC)')
      return
    }
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const accepted = await generateDevBlog(day)
      await resolvePostFromTask(accepted.task_id, accepted.post_id)
      setEvidenceDay(day)
      await refreshList()
      setNotice(
        accepted.status === 'completed'
          ? `Blog task #${accepted.task_id} completed.`
          : `Blog task #${accepted.task_id} queued — refresh or open Tasks tab.`,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generate failed')
    } finally {
      setBusy(false)
    }
  }

  const onRegenerate = async () => {
    if (!post) return
    const day = evidenceDay.trim() || post.day
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const accepted = await generateDevBlog(day, { force: true, postId: post.id })
      await resolvePostFromTask(accepted.task_id, accepted.post_id)
      await refreshList()
      setNotice(`Regenerated via task #${accepted.task_id}.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Regenerate failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="settings dev-blog" aria-labelledby="dev-blog-title">
      <div className="section-head">
        <h2 id="dev-blog-title">Dev Blog</h2>
        <button
          type="button"
          className="refresh"
          disabled={busy}
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

      <form className="dev-blog-toolbar dev-blog-filters" onSubmit={(e) => void onApplyFilters(e)}>
        <label>
          Evidence day (generate)
          <input
            type="date"
            value={evidenceDay}
            onChange={(e) => setEvidenceDay(e.target.value)}
            disabled={busy}
          />
        </label>
        <button type="button" disabled={busy} onClick={() => void onGenerate()}>
          {busy ? 'Working…' : 'Generate new'}
        </button>
        <button
          type="button"
          className="ghost"
          disabled={busy || !post}
          onClick={() => void onRegenerate()}
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
            disabled={busy}
          />
        </label>
        <label>
          From
          <input
            type="date"
            value={filterFrom}
            onChange={(e) => setFilterFrom(e.target.value)}
            disabled={busy}
          />
        </label>
        <label>
          To
          <input
            type="date"
            value={filterTo}
            onChange={(e) => setFilterTo(e.target.value)}
            disabled={busy}
          />
        </label>
        <label className="dev-blog-keyword">
          Keyword
          <input
            type="search"
            placeholder="标题或正文关键词"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            disabled={busy}
          />
        </label>
        <button type="submit" disabled={busy}>
          Search
        </button>
        <button type="button" className="ghost" disabled={busy} onClick={onClearFilters}>
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
                    disabled={busy}
                    onClick={() =>
                      void (async () => {
                        setBusy(true)
                        setError(null)
                        try {
                          await loadPost(row.id)
                        } catch (err) {
                          setError(err instanceof Error ? err.message : 'Load failed')
                        } finally {
                          setBusy(false)
                        }
                      })()
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
