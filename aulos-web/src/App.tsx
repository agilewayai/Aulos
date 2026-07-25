import { useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import {
  fetchMe,
  getStoredToken,
  listListeningGuides,
  login,
  logout,
  publishListeningGuide,
  register,
  shareGuideUrl,
  streamListeningGuide,
  streamRecomposeGuide,
  unpublishListeningGuide,
  updatePublishListeningGuide,
  verifyEmail,
  type ListeningGuide,
  type User,
  type WorkflowStep,
} from './api'
import { formatDateTime } from './time'
import './App.css'

type Mode = 'login' | 'register' | 'verify' | 'studio'

const EXAMPLE =
  "I'm beginning to listen to Bach's Goldberg Variations — I want to learn this masterwork while I listen."

const DISCOGS_EXAMPLE = "/discogs #423-287-1"

/** Make guide HTML playable inside srcDoc / blob: absolute media base + floating player CSS. */
function prepareGuideHtml(html: string): string {
  if (!html) return html
  const origin = typeof window !== 'undefined' ? window.location.origin : 'https://aulos.purezen.ai'
  const inject = `<base href="${origin}/"><style id="aulos-ambient-float">.wrap{padding-bottom:7.5rem!important}.ambient{position:fixed!important;z-index:60!important;right:0.75rem!important;bottom:0.75rem!important;left:auto!important;width:min(22.5rem,calc(100vw - 1.5rem))!important;margin:0!important;max-height:min(72vh,30rem)!important;display:flex!important;flex-direction:column!important;background:rgba(16,22,27,0.92)!important;backdrop-filter:blur(12px);box-shadow:0 12px 36px rgba(0,0,0,0.45)}.ambient .ambient-details{overflow:auto;flex:1 1 auto;min-height:0}@media (max-width:719px){.ambient{right:0.5rem!important;left:0.5rem!important;bottom:0.5rem!important;width:auto!important}}</style>`
  if (html.includes('id="aulos-ambient-float"') || html.includes('id=\'aulos-ambient-float\'')) {
    if (/<head[^>]*>/i.test(html) && !/<base\s/i.test(html)) {
      return html.replace(/<head([^>]*)>/i, `<head$1><base href="${origin}/">`)
    }
    return html
  }
  if (/<head[^>]*>/i.test(html)) {
    return html.replace(/<head([^>]*)>/i, `<head$1>${inject}`)
  }
  return inject + html
}

function App() {
  const initialToken = useMemo(() => {
    if (typeof window === 'undefined') return null
    return new URLSearchParams(window.location.search).get('token')
  }, [])

  const [mode, setMode] = useState<Mode>(initialToken ? 'verify' : 'login')
  const [user, setUser] = useState<User | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [verifyToken, setVerifyToken] = useState(initialToken ?? '')

  const [draft, setDraft] = useState(EXAMPLE)
  const [guide, setGuide] = useState<ListeningGuide | null>(null)
  const [visibleSteps, setVisibleSteps] = useState<WorkflowStep[]>([])
  const [history, setHistory] = useState<ListeningGuide[]>([])
  const [showGuide, setShowGuide] = useState(false)
  const trailRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    trailRef.current?.scrollTo({ top: trailRef.current.scrollHeight, behavior: 'smooth' })
  }, [visibleSteps, busy])

  useEffect(() => {
    const token = getStoredToken()
    if (!token || initialToken) return
    setBusy(true)
    fetchMe()
      .then(async (me) => {
        setUser(me)
        setMode('studio')
        try {
          setHistory(await listListeningGuides())
        } catch {
          /* ignore */
        }
      })
      .catch(() => logout())
      .finally(() => setBusy(false))
  }, [initialToken])

  async function onRegister(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      await register(email.trim(), password, displayName.trim())
      setNotice('Account created. Check your email for a verification link, then sign in.')
      setMode('login')
      setPassword('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setBusy(false)
    }
  }

  async function onLogin(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const data = await login(email.trim(), password)
      setUser(data.user)
      setMode('studio')
      setPassword('')
      setHistory(await listListeningGuides())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  async function onVerify(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      await verifyEmail(verifyToken.trim())
      setNotice('Email verified. You can sign in now.')
      setMode('login')
      if (typeof window !== 'undefined') {
        const url = new URL(window.location.href)
        url.searchParams.delete('token')
        window.history.replaceState({}, '', url.pathname)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed')
    } finally {
      setBusy(false)
    }
  }

  async function onCompose(event: FormEvent) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || busy) return
    setBusy(true)
    setError(null)
    setNotice(null)
    setShowGuide(false)
    setVisibleSteps([])
    setGuide(null)
    try {
      await streamListeningGuide(text, {
        onStep: (step) => {
          setVisibleSteps((prev) => {
            const without = prev.filter((s) => s.id !== step.id)
            return [...without, step]
          })
        },
        onDone: (result) => {
          setGuide(result)
          setVisibleSteps(result.steps)
          setShowGuide(true)
          setNotice(`Listening guide ready — ${result.work_title}`)
        },
        onError: (detail) => {
          setError(detail)
        },
      })
      setHistory(await listListeningGuides())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Guide workflow failed')
    } finally {
      setBusy(false)
    }
  }

  function onLogout() {
    logout()
    setUser(null)
    setMode('login')
    setGuide(null)
    setVisibleSteps([])
    setHistory([])
    setNotice('Signed out.')
  }

  function openHistoryItem(item: ListeningGuide) {
    setGuide(item)
    setVisibleSteps(item.steps)
    setShowGuide(true)
    setNotice(`Opened guide — ${item.work_title}`)
  }

  function mergeGuide(updated: ListeningGuide) {
    setGuide(updated)
    setHistory((prev) => {
      const rest = prev.filter((g) => g.id !== updated.id)
      return [updated, ...rest]
    })
  }

  async function onPublish() {
    if (!guide || busy) return
    setBusy(true)
    setError(null)
    try {
      const updated = await publishListeningGuide(guide.id)
      mergeGuide(updated)
      const url = updated.share_path ? shareGuideUrl(updated.share_path) : ''
      if (url && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url)
        setNotice(`Published — link copied: ${url}`)
      } else {
        setNotice(url ? `Published — share: ${url}` : 'Published')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Publish failed')
    } finally {
      setBusy(false)
    }
  }

  async function onUnpublish() {
    if (!guide || busy) return
    setBusy(true)
    setError(null)
    try {
      const updated = await unpublishListeningGuide(guide.id)
      mergeGuide(updated)
      setNotice('Unpublished — the public link no longer works.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unpublish failed')
    } finally {
      setBusy(false)
    }
  }

  async function onCopyShareLink() {
    if (!guide?.share_path) return
    const url = shareGuideUrl(guide.share_path)
    try {
      await navigator.clipboard.writeText(url)
      setNotice(`Link copied: ${url}`)
    } catch {
      setNotice(`Share link: ${url}`)
    }
  }

  async function onRecompose() {
    if (!guide || busy) return
    setBusy(true)
    setError(null)
    setNotice('Re-composing…')
    setShowGuide(true)
    try {
      await streamRecomposeGuide(
        guide.id,
        {
          onStep: (step) => {
            setVisibleSteps((prev) => {
              const without = prev.filter((s) => s.id !== step.id)
              return [...without, step]
            })
          },
          onDone: (result) => {
            mergeGuide(result)
            setVisibleSteps(result.steps)
            setShowGuide(true)
            setNotice(
              result.published
                ? `Re-composed — public link updated: ${result.share_path}`
                : `Re-composed — ${result.work_title}`,
            )
          },
          onError: (detail) => {
            setError(detail)
          },
        },
        { message: draft.trim() || undefined, workHint: guide.work_title },
      )
      setHistory(await listListeningGuides())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Recompose failed')
    } finally {
      setBusy(false)
    }
  }

  async function onUpdatePublish() {
    if (!guide || busy) return
    setBusy(true)
    setError(null)
    try {
      const updated = await updatePublishListeningGuide(guide.id)
      mergeGuide(updated)
      const url = updated.share_path ? shareGuideUrl(updated.share_path) : ''
      setNotice(url ? `Published / updated — ${url}` : 'Published')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update publish failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="shell">
      <div className="atmosphere" aria-hidden="true" />
      <header className="top">
        <div>
          <p className="brand">Aulos</p>
          <p className="tagline">
            {user
              ? `Art agent · ${user.display_name || user.email}`
              : 'Deep listening companion — register, verify, then compose a guide'}
          </p>
        </div>
        {user ? (
          <button type="button" className="ghost" onClick={onLogout}>
            Sign out
          </button>
        ) : null}
      </header>

      <main className="stage">
        {notice ? <p className="notice" role="status">{notice}</p> : null}
        {error ? <p className="error" role="alert">{error}</p> : null}

        {mode !== 'studio' || !user ? (
          <section className="auth-panel" aria-labelledby="auth-title">
            <div className="auth-tabs" role="tablist" aria-label="Account">
              <button
                type="button"
                role="tab"
                aria-selected={mode === 'login'}
                className={mode === 'login' ? 'active' : ''}
                onClick={() => setMode('login')}
              >
                Sign in
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={mode === 'register'}
                className={mode === 'register' ? 'active' : ''}
                onClick={() => setMode('register')}
              >
                Register
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={mode === 'verify'}
                className={mode === 'verify' ? 'active' : ''}
                onClick={() => setMode('verify')}
              >
                Verify
              </button>
            </div>

            {mode === 'register' ? (
              <form className="auth-form" onSubmit={onRegister}>
                <h1 id="auth-title">Create account</h1>
                <label htmlFor="reg-name">Display name</label>
                <input
                  id="reg-name"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                />
                <label htmlFor="reg-email">Email</label>
                <input
                  id="reg-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <label htmlFor="reg-password">Password</label>
                <input
                  id="reg-password"
                  type="password"
                  required
                  minLength={10}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button type="submit" disabled={busy}>
                  {busy ? 'Creating…' : 'Register'}
                </button>
              </form>
            ) : null}

            {mode === 'login' ? (
              <form className="auth-form" onSubmit={onLogin}>
                <h1 id="auth-title">Sign in</h1>
                <label htmlFor="login-email">Email</label>
                <input
                  id="login-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <label htmlFor="login-password">Password</label>
                <input
                  id="login-password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button type="submit" disabled={busy}>
                  {busy ? 'Signing in…' : 'Sign in'}
                </button>
              </form>
            ) : null}

            {mode === 'verify' ? (
              <form className="auth-form" onSubmit={onVerify}>
                <h1 id="auth-title">Verify email</h1>
                <label htmlFor="verify-token">Verification token</label>
                <input
                  id="verify-token"
                  required
                  value={verifyToken}
                  onChange={(e) => setVerifyToken(e.target.value)}
                  aria-describedby="verify-help"
                />
                <p id="verify-help" className="hint">
                  Paste the token from your email, or open the verification link directly.
                </p>
                <button type="submit" disabled={busy}>
                  {busy ? 'Verifying…' : 'Verify email'}
                </button>
              </form>
            ) : null}
          </section>
        ) : (
          <div className="studio">
            <section className="studio-hero" aria-labelledby="studio-title">
              <p className="eyebrow">Listening studio</p>
              <h1 id="studio-title">Tell Aulos what you are learning</h1>
              <p className="hero-copy">
                Name a masterwork, or paste a Discogs release with{" "}
                <code>/discogs #release-id</code> or a catalog number like{" "}
                <code>/discogs #423-287-1</code>. Aulos recovers the work, composer, and
                performers, then composes a professional listening guide — with every thinking
                step visible.
              </p>
              <form className="composer studio-composer" onSubmit={onCompose}>
                <label className="sr-only" htmlFor="prompt">
                  Listening intent
                </label>
                <textarea
                  id="prompt"
                  rows={3}
                  value={draft}
                  placeholder="I'm listening to… or /discogs #423-287-1"
                  onChange={(e) => setDraft(e.target.value)}
                />
                <div className="composer-actions">
                  <button
                    type="button"
                    className="ghost"
                    disabled={busy}
                    onClick={() => setDraft(EXAMPLE)}
                  >
                    Use Goldberg example
                  </button>
                  <button
                    type="button"
                    className="ghost"
                    disabled={busy}
                    onClick={() => setDraft(DISCOGS_EXAMPLE)}
                  >
                    Use /discogs example
                  </button>
                  <button type="submit" disabled={busy || !draft.trim()}>
                    {busy ? 'Researching…' : 'Compose listening guide'}
                  </button>
                </div>
              </form>
            </section>

            <div className="studio-grid">
              <section className="workflow" aria-labelledby="workflow-title">
                <div className="section-head">
                  <h2 id="workflow-title">Chain of thought</h2>
                  {guide ? (
                    <span className="meta-pill">
                      {guide.source} · {guide.status}
                      {guide.published ? ' · published' : ''}
                      {guide.published_at
                        ? ` · ${formatDateTime(guide.published_at)}`
                        : guide.created_at
                          ? ` · ${formatDateTime(guide.created_at)}`
                          : ''}
                    </span>
                  ) : null}
                </div>
                <div className="trail" ref={trailRef}>
                  {visibleSteps.length === 0 && !busy ? (
                    <p className="empty">
                      Workflow steps appear here: intake → wide research → deep research → compose →
                      render.
                    </p>
                  ) : null}
                  {busy && visibleSteps.length === 0 ? (
                    <p className="thinking">Aulos is opening the research atelier…</p>
                  ) : null}
                  <ol className="step-list">
                    {visibleSteps.map((step, index) => (
                      <li
                        key={step.id}
                        className={`step status-${step.status}`}
                        style={{ animationDelay: `${0.04 * index}s` }}
                      >
                        <div className="step-index">{index + 1}</div>
                        <div className="step-body">
                          <p className="step-title">{step.title}</p>
                          {step.skill_id ? (
                            <p className="step-skill">
                              {step.skill_id}
                              {step.skill_version ? `@${step.skill_version}` : ''}
                            </p>
                          ) : null}
                          <p className="step-thinking">{step.thinking}</p>
                          {step.detail ? <p className="step-detail">{step.detail}</p> : null}
                        </div>
                      </li>
                    ))}
                  </ol>
                </div>
                {history.length > 0 ? (
                  <div className="history">
                    <h3>Recent guides</h3>
                    <ul>
                      {history.slice(0, 6).map((item) => (
                        <li key={item.id}>
                          <button type="button" onClick={() => openHistoryItem(item)}>
                            {item.work_title}
                            {item.published ? ' · shared' : ''}
                            {item.created_at ? ` · ${formatDateTime(item.created_at)}` : ''}
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </section>

              <section className="guide-pane" aria-labelledby="guide-title">
                <div className="section-head">
                  <h2 id="guide-title">Listening guide</h2>
                  {guide && showGuide ? (
                    <div className="guide-actions">
                      <button type="button" className="ghost" disabled={busy} onClick={onRecompose}>
                        Re-compose
                      </button>
                      <button type="button" className="ghost" disabled={busy} onClick={onUpdatePublish}>
                        Update publish
                      </button>
                      {!guide.published ? (
                        <button type="button" className="ghost" disabled={busy} onClick={onPublish}>
                          Publish & copy link
                        </button>
                      ) : (
                        <>
                          <button type="button" className="ghost" onClick={onCopyShareLink}>
                            Copy share link
                          </button>
                          <a
                            className="ghost linkish"
                            href={guide.share_path || '#'}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            Open share page
                          </a>
                          <button type="button" className="ghost" disabled={busy} onClick={onUnpublish}>
                            Unpublish
                          </button>
                        </>
                      )}
                      <button
                        type="button"
                        className="ghost"
                        onClick={() => {
                          const prepared = prepareGuideHtml(guide.guide_html)
                          const blob = new Blob([prepared], { type: 'text/html' })
                          const url = URL.createObjectURL(blob)
                          window.open(url, '_blank', 'noopener,noreferrer')
                        }}
                      >
                        Open full page
                      </button>
                    </div>
                  ) : null}
                </div>
                {guide?.published && guide.share_path ? (
                  <p className="share-url" role="status">
                    Public link (no login): <code>{shareGuideUrl(guide.share_path)}</code>
                  </p>
                ) : null}
                {guide && showGuide ? (
                  <iframe
                    className="guide-frame"
                    title={guide.work_title}
                    sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox"
                    srcDoc={prepareGuideHtml(guide.guide_html)}
                  />
                ) : (
                  <div className="guide-placeholder">
                    <p>
                      Your guide page will appear here — typography, listening map, and practice
                      path for the work you named.
                    </p>
                  </div>
                )}
              </section>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
