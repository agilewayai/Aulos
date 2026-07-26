import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  fetchDevBlog,
  fetchDevBlogList,
  generateDevBlog,
  type DevBlogPost,
  type DevBlogSummary,
} from './api'
import { formatDateTime } from './time'

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
}

function utcToday(): string {
  return new Date().toISOString().slice(0, 10)
}

/** Lightweight markdown → React for blog reading (no extra deps). */
function BlogMarkdown({ source }: { source: string }) {
  const blocks = source.replace(/\r\n/g, '\n').split(/\n\n+/)
  return (
    <div className="dev-blog-prose">
      {blocks.map((block, i) => {
        const lines = block.split('\n')
        const first = lines[0]?.trim() ?? ''
        if (first.startsWith('# ')) {
          return (
            <h3 key={i} className="dev-blog-h1">
              {first.slice(2)}
            </h3>
          )
        }
        if (first.startsWith('## ')) {
          return (
            <h4 key={i} className="dev-blog-h2">
              {first.slice(3)}
            </h4>
          )
        }
        if (lines.every((l) => l.trim().startsWith('- ') || l.trim() === '')) {
          return (
            <ul key={i} className="dev-blog-list">
              {lines
                .filter((l) => l.trim().startsWith('- '))
                .map((l, j) => (
                  <li key={j}>{l.trim().slice(2)}</li>
                ))}
            </ul>
          )
        }
        return (
          <p key={i} className="dev-blog-p">
            {lines.join(' ')}
          </p>
        )
      })}
    </div>
  )
}

export function DevBlogPanel({ busy, setBusy, setError, setNotice }: Props) {
  const [rows, setRows] = useState<DevBlogSummary[]>([])
  const [selectedDay, setSelectedDay] = useState<string>(utcToday())
  const [dayInput, setDayInput] = useState(utcToday())
  const [post, setPost] = useState<DevBlogPost | null>(null)
  const [showEvidence, setShowEvidence] = useState(false)

  const refreshList = useCallback(async () => {
    const list = await fetchDevBlogList()
    setRows(list)
  }, [])

  const loadDay = useCallback(
    async (day: string) => {
      setSelectedDay(day)
      setDayInput(day)
      try {
        const data = await fetchDevBlog(day)
        setPost(data)
      } catch {
        setPost(null)
      }
    },
    [],
  )

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

  const onGenerate = async (force: boolean) => {
    const day = dayInput.trim() || utcToday()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const data = await generateDevBlog(day, force)
      setPost(data)
      setSelectedDay(data.day)
      setDayInput(data.day)
      await refreshList()
      setNotice(
        data.provider === 'fake'
          ? `Draft for ${data.day} ready (fake LLM — configure a live provider under LLM for richer prose).`
          : `Blog for ${data.day} generated via ${data.provider}.`,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generate failed')
    } finally {
      setBusy(false)
    }
  }

  const onPickDay = async (event: FormEvent) => {
    event.preventDefault()
    const day = dayInput.trim()
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) {
      setError('Day must be YYYY-MM-DD (UTC)')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await loadDay(day)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Load failed')
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
        One monorepo story per UTC day — product features, who it helps, and how the system
        changed. Written for humans from git + harness evidence.
      </p>

      <form className="dev-blog-toolbar" onSubmit={(e) => void onPickDay(e)}>
        <label>
          Day (UTC)
          <input
            type="date"
            value={dayInput}
            onChange={(e) => setDayInput(e.target.value)}
            disabled={busy}
          />
        </label>
        <button type="submit" disabled={busy}>
          Open
        </button>
        <button type="button" disabled={busy} onClick={() => void onGenerate(false)}>
          {busy ? 'Working…' : 'Generate'}
        </button>
        <button
          type="button"
          className="ghost"
          disabled={busy || !post}
          onClick={() => void onGenerate(true)}
        >
          Regenerate
        </button>
      </form>

      <div className="dev-blog-layout">
        <aside className="dev-blog-days" aria-label="Cached blog days">
          <h3 className="dev-blog-aside-title">Saved days</h3>
          {rows.length === 0 ? (
            <p className="meta">No posts yet — pick a day and generate.</p>
          ) : (
            <ul className="dev-blog-day-list">
              {rows.map((row) => (
                <li key={row.day}>
                  <button
                    type="button"
                    className={
                      row.day === selectedDay ? 'dev-blog-day active' : 'dev-blog-day'
                    }
                    disabled={busy}
                    onClick={() =>
                      void (async () => {
                        setBusy(true)
                        setError(null)
                        try {
                          await loadDay(row.day)
                        } catch (err) {
                          setError(err instanceof Error ? err.message : 'Load failed')
                        } finally {
                          setBusy(false)
                        }
                      })()
                    }
                  >
                    <span className="dev-blog-day-date">{row.day}</span>
                    <span className="dev-blog-day-title">{row.title || 'Untitled'}</span>
                    <span className="dev-blog-day-meta">
                      {row.provider} · {formatDateTime(row.generated_at)}
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
              No cached post for {selectedDay}. Generate one from today&apos;s git + harness
              evidence.
            </p>
          ) : (
            <>
              <header className="dev-blog-article-head">
                <p className="meta">
                  {post.day} · {post.provider} · {formatDateTime(post.generated_at)}
                </p>
                <button
                  type="button"
                  className="ghost"
                  onClick={() => setShowEvidence((v) => !v)}
                >
                  {showEvidence ? 'Hide evidence' : 'Show evidence'}
                </button>
              </header>
              <BlogMarkdown source={post.body_md} />
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
