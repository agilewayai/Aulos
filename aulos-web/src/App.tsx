import { useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent, MouseEvent as ReactMouseEvent } from 'react'
import {
  deleteListeningGuide,
  favoriteListeningGuide,
  fetchMe,
  fetchListeningGuide,
  forgotPassword,
  fetchGuideTrace,
  listListeningGuides,
  login,
  logout,
  patchListeningGuideTags,
  publishListeningGuide,
  register,
  resetPassword,
  retryListeningJob,
  searchDiscogsReleases,
  shareGuideUrl,
  streamGuideEvents,
  streamListeningGuide,
  streamRecomposeGuide,
  unfavoriteListeningGuide,
  unpublishListeningGuide,
  updatePublishListeningGuide,
  verifyEmail,
  type ChainTrace,
  type DiscogsSearchHit,
  type ListeningGuide,
  type User,
  type WorkflowStep,
} from './api'
import { formatDateTime } from './time'
import { PasswordField } from './PasswordField'
import { GUIDE_IFRAME_SANDBOX, prepareGuideHtml } from './guideHtml'
import {
  consumeWebScene,
  registerSceneCapture,
  saveWebScene,
  type WebSessionScene,
} from './sessionScene'
import './App.css'

type Mode = 'login' | 'register' | 'verify' | 'forgot' | 'reset' | 'studio'
type StudioTab = 'guide' | 'atelier' | 'library'
type AttachMenu = 'menu' | 'discogs' | null
type LibraryFilter = 'all' | 'favorites' | 'published' | 'progress'

const PENDING_SCENE: WebSessionScene | null =
  typeof window === 'undefined' ? null : consumeWebScene()

const EXAMPLE =
  "I'm beginning to listen to Bach's Goldberg Variations — I want to learn this masterwork while I listen."
const DISCOGS_EXAMPLE = '/discogs #423-287-1'

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback
}

function App() {
  const initialToken = useMemo(
    () => (typeof window === 'undefined' ? null : new URLSearchParams(window.location.search).get('token')),
    [],
  )
  const initialResetToken = useMemo(
    () =>
      typeof window === 'undefined'
        ? null
        : new URLSearchParams(window.location.search).get('reset_token'),
    [],
  )
  const [mode, setMode] = useState<Mode>(() => {
    if (initialResetToken) return 'reset'
    if (initialToken) return 'verify'
    const pendingMode = PENDING_SCENE?.mode
    if (pendingMode && pendingMode !== 'studio') return pendingMode
    return 'login'
  })
  const [user, setUser] = useState<User | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [email, setEmail] = useState(() => PENDING_SCENE?.email ?? '')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [displayName, setDisplayName] = useState(() => PENDING_SCENE?.displayName ?? '')
  const [verifyToken, setVerifyToken] = useState(initialToken ?? '')
  const [resetToken, setResetToken] = useState(initialResetToken ?? '')

  const [draft, setDraft] = useState(() => PENDING_SCENE?.draft ?? EXAMPLE)
  const [guide, setGuide] = useState<ListeningGuide | null>(null)
  const [visibleSteps, setVisibleSteps] = useState<WorkflowStep[]>([])
  const [history, setHistory] = useState<ListeningGuide[]>([])
  const [showGuide, setShowGuide] = useState(() => PENDING_SCENE?.showGuide ?? false)
  const [attachMenu, setAttachMenu] = useState<AttachMenu>(null)
  const [discogsQuery, setDiscogsQuery] = useState('')
  const [discogsResults, setDiscogsResults] = useState<DiscogsSearchHit[]>([])
  const [discogsError, setDiscogsError] = useState<string | null>(null)
  const [discogsLoading, setDiscogsLoading] = useState(false)
  const [chainTrace, setChainTrace] = useState<ChainTrace | null>(null)
  const [traceOpen, setTraceOpen] = useState(false)
  const [studioTab, setStudioTab] = useState<StudioTab>(() => PENDING_SCENE?.studioTab ?? 'guide')
  const [actionsOpen, setActionsOpen] = useState(false)
  const [libraryQuery, setLibraryQuery] = useState(() => PENDING_SCENE?.libraryQuery ?? '')
  const [libraryFilter, setLibraryFilter] = useState<LibraryFilter>(() => PENDING_SCENE?.libraryFilter ?? 'all')
  const [tagFilter, setTagFilter] = useState(() => PENDING_SCENE?.tagFilter ?? '')
  const [tagDraft, setTagDraft] = useState('')
  const [taggingId, setTaggingId] = useState<number | null>(null)
  const [composeOpen, setComposeOpen] = useState(() => PENDING_SCENE?.composeOpen ?? true)
  const [chainProgress, setChainProgress] = useState<{ done: number; total: number } | null>(null)
  const [retryableGuideId, setRetryableGuideId] = useState<number | null>(null)
  const trailRef = useRef<HTMLDivElement>(null)
  const attachRef = useRef<HTMLDivElement>(null)
  const actionsRef = useRef<HTMLDivElement>(null)
  const watchingRef = useRef<number | null>(null)
  const sceneRef = useRef<WebSessionScene | null>(PENDING_SCENE)
  const sceneAppliedRef = useRef(false)
  const sceneSnapshotRef = useRef({
    mode: mode as Mode,
    email: '',
    displayName: '',
    studioTab: 'guide' as StudioTab,
    composeOpen: true,
    draft: EXAMPLE,
    guideId: null as number | null,
    showGuide: false,
    libraryQuery: '',
    libraryFilter: 'all' as LibraryFilter,
    tagFilter: '',
  })

  sceneSnapshotRef.current = {
    mode,
    email,
    displayName,
    studioTab,
    composeOpen,
    draft,
    guideId: guide?.id ?? null,
    showGuide,
    libraryQuery,
    libraryFilter,
    tagFilter,
  }

  useEffect(() => {
    return registerSceneCapture(() => {
      const snap = sceneSnapshotRef.current
      saveWebScene({
        v: 1,
        mode: snap.mode,
        email: snap.mode === 'studio' ? undefined : snap.email,
        displayName: snap.mode === 'register' ? snap.displayName : undefined,
        studioTab: snap.studioTab,
        composeOpen: snap.composeOpen,
        draft: snap.draft,
        guideId: snap.guideId,
        showGuide: snap.showGuide,
        libraryQuery: snap.libraryQuery,
        libraryFilter: snap.libraryFilter,
        tagFilter: snap.tagFilter,
        scrollY: window.scrollY,
      })
    })
  }, [])

  useEffect(() => {
    trailRef.current?.scrollTo({ top: trailRef.current.scrollHeight, behavior: 'smooth' })
  }, [visibleSteps, busy])

  useEffect(() => {
    if (!notice) return
    const timer = window.setTimeout(() => setNotice(null), 5600)
    return () => window.clearTimeout(timer)
  }, [notice])

  useEffect(() => {
    if (!error) return
    const timer = window.setTimeout(() => setError(null), 7200)
    return () => window.clearTimeout(timer)
  }, [error])

  useEffect(() => {
    if (!attachMenu) return
    const close = (event: MouseEvent) => {
      if (!attachRef.current?.contains(event.target as Node)) setAttachMenu(null)
    }
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setAttachMenu(null)
    }
    document.addEventListener('mousedown', close)
    document.addEventListener('keydown', escape)
    return () => {
      document.removeEventListener('mousedown', close)
      document.removeEventListener('keydown', escape)
    }
  }, [attachMenu])

  useEffect(() => {
    if (!actionsOpen) return
    const close = (event: MouseEvent) => {
      if (!actionsRef.current?.contains(event.target as Node)) setActionsOpen(false)
    }
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setActionsOpen(false)
    }
    document.addEventListener('mousedown', close)
    document.addEventListener('keydown', escape)
    return () => {
      document.removeEventListener('mousedown', close)
      document.removeEventListener('keydown', escape)
    }
  }, [actionsOpen])

  useEffect(() => {
    if (attachMenu !== 'discogs' || discogsQuery.trim().length < 2) {
      setDiscogsResults([])
      setDiscogsLoading(false)
      return
    }
    let current = true
    const timer = window.setTimeout(() => {
      setDiscogsLoading(true)
      setDiscogsError(null)
      searchDiscogsReleases(discogsQuery.trim())
        .then((result) => current && setDiscogsResults(result.results))
        .catch((err) => current && setDiscogsError(errorMessage(err, 'Discogs search failed')))
        .finally(() => current && setDiscogsLoading(false))
    }, 280)
    return () => {
      current = false
      window.clearTimeout(timer)
    }
  }, [attachMenu, discogsQuery])

  useEffect(() => {
    if (!guide?.id) {
      setChainTrace(null)
      setTraceOpen(false)
      return
    }
    let current = true
    fetchGuideTrace(guide.id)
      .then((result) => current && setChainTrace(result.chain_trace))
      .catch(() => current && setChainTrace(null))
    return () => {
      current = false
    }
  }, [guide?.id])

  useEffect(() => {
    if (initialToken || initialResetToken) return
    setBusy(true)
    fetchMe()
      .then(async (me) => {
        setUser(me)
        setMode('studio')
        try {
          setHistory(await listListeningGuides({ limit: 50 }))
        } catch {
          /* History is non-critical after successful sign-in. */
        }
      })
      .catch(() => { void logout() })
      .finally(() => setBusy(false))
  }, [initialResetToken, initialToken])

  async function onRegister(event: FormEvent) {
    event.preventDefault()
    setBusy(true); setError(null); setNotice(null)
    try {
      await register(email.trim(), password, displayName.trim())
      setNotice('Account created. Check your email for a verification link, then sign in.')
      setMode('login'); setPassword('')
    } catch (err) {
      setError(errorMessage(err, 'Registration failed'))
    } finally { setBusy(false) }
  }

  async function onLogin(event: FormEvent) {
    event.preventDefault()
    setBusy(true); setError(null); setNotice(null)
    try {
      const data = await login(email.trim(), password)
      setUser(data.user); setMode('studio'); setPassword('')
      setHistory(await listListeningGuides({ limit: 50 }))
    } catch (err) {
      setError(errorMessage(err, 'Login failed'))
    } finally { setBusy(false) }
  }

  async function onVerify(event: FormEvent) {
    event.preventDefault()
    setBusy(true); setError(null); setNotice(null)
    try {
      await verifyEmail(verifyToken.trim())
      setNotice('Email verified. You can sign in now.'); setMode('login')
      const url = new URL(window.location.href)
      url.searchParams.delete('token')
      window.history.replaceState({}, '', url.pathname + url.search)
    } catch (err) {
      setError(errorMessage(err, 'Verification failed'))
    } finally { setBusy(false) }
  }

  async function onForgot(event: FormEvent) {
    event.preventDefault()
    setBusy(true); setError(null); setNotice(null)
    try {
      const result = await forgotPassword(email.trim())
      setNotice(result.detail); setMode('login')
    } catch (err) {
      setError(errorMessage(err, 'Could not send reset email'))
    } finally { setBusy(false) }
  }

  async function onReset(event: FormEvent) {
    event.preventDefault()
    if (password !== passwordConfirm) {
      setError('Passwords do not match')
      return
    }
    setBusy(true); setError(null); setNotice(null)
    try {
      const result = await resetPassword(resetToken.trim(), password)
      setNotice(result.detail); setPassword(''); setPasswordConfirm(''); setMode('login')
      const url = new URL(window.location.href)
      url.searchParams.delete('reset_token')
      window.history.replaceState({}, '', url.pathname + url.search)
    } catch (err) {
      setError(errorMessage(err, 'Password reset failed'))
    } finally { setBusy(false) }
  }

  function receiveStep(step: WorkflowStep) {
    setVisibleSteps((previous) => {
      const next = [...previous.filter((item) => item.id !== step.id), step]
      next.sort((a, b) => (a.index ?? 0) - (b.index ?? 0))
      const done = next.filter((s) =>
        ['done', 'completed', 'ok', 'skip', 'skipped', 'failed'].includes(s.status),
      ).length
      const total = step.total || next[0]?.total || next.length
      setChainProgress({ done, total })
      return next
    })
  }

  function receiveProgress(progress: { done: number; total: number; steps: WorkflowStep[] }) {
    const steps = [...progress.steps].sort((a, b) => (a.index ?? 0) - (b.index ?? 0))
    setVisibleSteps(steps)
    setChainProgress({ done: progress.done, total: progress.total || steps.length })
  }

  function mergeGuide(updated: ListeningGuide) {
    setGuide(updated)
    setHistory((previous) => [updated, ...previous.filter((item) => item.id !== updated.id)])
  }

  async function refreshLibrary() {
    const params: Parameters<typeof listListeningGuides>[0] = { limit: 50 }
    const q = libraryQuery.trim()
    if (q) params!.q = q
    if (libraryFilter === 'favorites') params!.favorited = true
    if (libraryFilter === 'published') params!.published = true
    if (libraryFilter === 'progress') params!.status = 'running'
    if (tagFilter.trim()) params!.tag = tagFilter.trim()
    // progress filter also wants queued — fetch both client-side if needed
    let rows = await listListeningGuides(params)
    if (libraryFilter === 'progress') {
      const queued = await listListeningGuides({ ...params, status: 'queued' })
      const seen = new Set(rows.map((r) => r.id))
      rows = [...queued.filter((r) => !seen.has(r.id)), ...rows]
    }
    setHistory(rows)
    return rows
  }

  async function watchJob(guideId: number, opts?: { noticeReady?: boolean }) {
    if (watchingRef.current === guideId) return
    watchingRef.current = guideId
    setBusy(true)
    setError(null)
    setRetryableGuideId(null)
    setStudioTab('atelier')
    setShowGuide(false)
    try {
      // Hydrate current plan immediately (reconnect / resume)
      try {
        const snap = await fetchListeningGuide(guideId)
        if (snap.steps?.length) {
          receiveProgress({
            done: snap.steps.filter((s) =>
              ['done', 'completed', 'ok', 'skip', 'skipped', 'failed'].includes(s.status),
            ).length,
            total: snap.steps[0]?.total || snap.steps.length,
            steps: snap.steps,
          })
        }
      } catch {
        /* best-effort */
      }
      await streamGuideEvents(guideId, {
        onStep: receiveStep,
        onProgress: receiveProgress,
        onDone: (result) => {
          mergeGuide(result)
          setVisibleSteps(result.steps || [])
          setChainProgress(null)
          setShowGuide(true)
          setStudioTab('guide')
          setComposeOpen(false)
          if (opts?.noticeReady !== false) {
            setNotice(`Listening guide ready — ${result.work_title}`)
          }
        },
        onError: (detail, meta) => {
          setError(detail)
          if (meta?.retryable) setRetryableGuideId(meta.guideId ?? guideId)
        },
      })
      await refreshLibrary()
    } catch (err) {
      setError(errorMessage(err, 'Could not follow guide job'))
      setRetryableGuideId(guideId)
    } finally {
      if (watchingRef.current === guideId) watchingRef.current = null
      setBusy(false)
    }
  }

  async function runCompose(message: string, workHint?: string) {
    if (!message.trim() || busy) return
    setBusy(true); setError(null); setNotice(null); setShowGuide(false)
    setVisibleSteps([]); setGuide(null); setChainTrace(null); setChainProgress(null)
    setRetryableGuideId(null); setStudioTab('atelier')
    try {
      await streamListeningGuide(message.trim(), {
        onStep: receiveStep,
        onProgress: receiveProgress,
        onDone: (result) => {
          setGuide(result); setVisibleSteps(result.steps); setShowGuide(true)
          setChainProgress(null)
          setNotice(`Listening guide ready — ${result.work_title}`); setStudioTab('guide')
          setComposeOpen(false)
        },
        onError: (detail, meta) => {
          setError(detail)
          if (meta?.retryable && meta.guideId) setRetryableGuideId(meta.guideId)
        },
      }, workHint)
      await refreshLibrary()
    } catch (err) {
      setError(errorMessage(err, 'Guide workflow failed'))
    } finally { setBusy(false) }
  }

  async function onRetryChain() {
    const id = retryableGuideId || guide?.id
    if (!id || busy) return
    setBusy(true)
    setError(null)
    setNotice('Retrying atelier chain…')
    setRetryableGuideId(null)
    setStudioTab('atelier')
    try {
      const row = await retryListeningJob(id)
      mergeGuide(row)
      setVisibleSteps(row.steps || [])
      watchingRef.current = null
      await watchJob(row.id)
    } catch (err) {
      setError(errorMessage(err, 'Retry failed'))
      setRetryableGuideId(id)
      setBusy(false)
    }
  }

  async function onCompose(event: FormEvent) {
    event.preventDefault()
    await runCompose(draft)
  }

  function onPickDiscogs(hit: DiscogsSearchHit) {
    const command = `/discogs #${hit.id}`
    setDraft(command); setAttachMenu(null); setDiscogsQuery('')
    void runCompose(command, hit.title)
  }

  function onLogout() {
    void logout(); setUser(null); setMode('login'); setGuide(null); setVisibleSteps([])
    setHistory([]); setNotice('Signed out.'); setStudioTab('guide')
    watchingRef.current = null
  }

  function openHistoryItem(item: ListeningGuide) {
    if (item.status === 'queued' || item.status === 'running') {
      setGuide(item)
      setVisibleSteps(item.steps || [])
      setNotice(`Resuming job — ${item.work_title}`)
      void watchJob(item.id)
      return
    }
    if (item.status === 'failed') {
      setGuide(item)
      setVisibleSteps(item.steps || [])
      setShowGuide(false)
      setStudioTab('library')
      setError(item.error_detail || 'This guide job failed')
      return
    }
    setGuide(item); setVisibleSteps(item.steps || []); setShowGuide(true); setStudioTab('guide')
    setComposeOpen(false)
    setNotice(`Opened guide — ${item.work_title}`)
  }

  async function onToggleFavorite(item: ListeningGuide, event: ReactMouseEvent) {
    event.stopPropagation()
    try {
      const updated = item.favorited
        ? await unfavoriteListeningGuide(item.id)
        : await favoriteListeningGuide(item.id)
      mergeGuide(updated)
      if (guide?.id === item.id) setGuide(updated)
      await refreshLibrary()
    } catch (err) {
      setError(errorMessage(err, 'Could not update favorite'))
    }
  }

  async function onDeleteGuide(item: ListeningGuide, event: ReactMouseEvent) {
    event.stopPropagation()
    if (!window.confirm(`Delete “${item.work_title}”? This cannot be undone.`)) return
    try {
      await deleteListeningGuide(item.id)
      setHistory((previous) => previous.filter((row) => row.id !== item.id))
      if (guide?.id === item.id) {
        setGuide(null); setVisibleSteps([]); setShowGuide(false); setChainTrace(null)
      }
      setNotice('Guide deleted')
    } catch (err) {
      setError(errorMessage(err, 'Delete failed'))
    }
  }

  async function onSaveTags(item: ListeningGuide) {
    try {
      const tags = tagDraft.split(/[,，]/).map((t) => t.trim()).filter(Boolean)
      const updated = await patchListeningGuideTags(item.id, tags)
      mergeGuide(updated)
      setTaggingId(null)
      setTagDraft('')
      await refreshLibrary()
      setNotice('Tags saved')
    } catch (err) {
      setError(errorMessage(err, 'Could not save tags'))
    }
  }

  async function onRetryFailed(item: ListeningGuide) {
    const message = (item.message || '').trim()
    if (!message) {
      setError('No original message to retry')
      return
    }
    setDraft(message)
    await runCompose(message, item.work_title)
  }

  useEffect(() => {
    if (mode !== 'studio' || !user) return
    const timer = window.setTimeout(() => {
      void refreshLibrary().catch(() => undefined)
    }, 180)
    return () => window.clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional filter-driven refresh
  }, [libraryQuery, libraryFilter, tagFilter, mode, user?.id])

  useEffect(() => {
    if (PENDING_SCENE) return
    if (mode !== 'studio' || !user || watchingRef.current != null) return
    let cancelled = false
    ;(async () => {
      try {
        const rows = await listListeningGuides({ limit: 50 })
        if (cancelled) return
        const active = rows.find((row) => row.status === 'queued' || row.status === 'running')
        if (!active || watchingRef.current != null) return
        setGuide(active)
        setVisibleSteps(active.steps || [])
        setNotice(`Resuming atelier job — ${active.work_title}`)
        await watchJob(active.id)
      } catch {
        /* resume is best-effort */
      }
    })()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, user?.id])

  useEffect(() => {
    if (!PENDING_SCENE || PENDING_SCENE.mode === 'studio') return
    if (typeof PENDING_SCENE.scrollY === 'number') {
      window.requestAnimationFrame(() => window.scrollTo(0, PENDING_SCENE.scrollY ?? 0))
    }
    setNotice('Restored your place after update')
  }, [])

  useEffect(() => {
    if (mode !== 'studio' || !user || sceneAppliedRef.current) return
    const scene = sceneRef.current
    if (!scene) {
      sceneAppliedRef.current = true
      return
    }
    sceneAppliedRef.current = true
    let cancelled = false
    ;(async () => {
      try {
        const rows = await listListeningGuides({ limit: 50 })
        if (cancelled) return
        setHistory(rows)
        if (scene.guideId != null) {
          const item = rows.find((row) => row.id === scene.guideId)
          if (item) {
            if (item.status === 'queued' || item.status === 'running') {
              setGuide(item)
              setVisibleSteps(item.steps || [])
              void watchJob(item.id, { noticeReady: true })
            } else if (item.status === 'failed') {
              setGuide(item)
              setVisibleSteps(item.steps || [])
              setShowGuide(false)
              if (scene.studioTab) setStudioTab(scene.studioTab)
            } else {
              setGuide(item)
              setVisibleSteps(item.steps || [])
              setShowGuide(scene.showGuide ?? true)
              if (scene.studioTab) setStudioTab(scene.studioTab)
              setComposeOpen(scene.composeOpen ?? false)
            }
          }
        }
        if (typeof scene.scrollY === 'number') {
          window.requestAnimationFrame(() => window.scrollTo(0, scene.scrollY ?? 0))
        }
        setNotice('Restored your place after update')
      } catch {
        setNotice('Restored your place after update')
      } finally {
        sceneRef.current = null
      }
    })()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, user?.id])

  async function onPublish() {
    if (!guide || busy) return
    setBusy(true); setError(null)
    try {
      const updated = await publishListeningGuide(guide.id)
      mergeGuide(updated)
      const url = updated.share_path ? shareGuideUrl(updated.share_path) : ''
      if (url && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url)
        setNotice(`Published — link copied: ${url}`)
      } else setNotice(url ? `Published — share: ${url}` : 'Published')
    } catch (err) { setError(errorMessage(err, 'Publish failed')) } finally { setBusy(false) }
  }

  async function onUnpublish() {
    if (!guide || busy) return
    setBusy(true); setError(null)
    try {
      mergeGuide(await unpublishListeningGuide(guide.id))
      setNotice('Unpublished — the public link no longer works.')
    } catch (err) { setError(errorMessage(err, 'Unpublish failed')) } finally { setBusy(false) }
  }

  async function onCopyShareLink() {
    if (!guide?.share_path) return
    const url = shareGuideUrl(guide.share_path)
    try { await navigator.clipboard.writeText(url); setNotice(`Link copied: ${url}`) }
    catch { setNotice(`Share link: ${url}`) }
  }

  async function onRecompose() {
    if (!guide || busy) return
    setBusy(true); setError(null); setNotice('Re-composing…'); setShowGuide(false); setStudioTab('atelier')
    setRetryableGuideId(null); setChainProgress(null)
    try {
      await streamRecomposeGuide(guide.id, {
        onStep: receiveStep,
        onProgress: receiveProgress,
        onDone: (result) => {
          mergeGuide(result); setVisibleSteps(result.steps); setShowGuide(true); setStudioTab('guide'); setComposeOpen(false)
          setChainProgress(null)
          setNotice(result.published ? `Re-composed — public link updated: ${result.share_path}` : `Re-composed — ${result.work_title}`)
        },
        onError: (detail, meta) => {
          setError(detail)
          if (meta?.retryable) setRetryableGuideId(meta.guideId ?? guide.id)
        },
      }, { message: draft.trim() || undefined, workHint: guide.work_title })
      await refreshLibrary()
    } catch (err) {
      setError(errorMessage(err, 'Recompose failed'))
      setRetryableGuideId(guide.id)
    } finally { setBusy(false) }
  }

  async function onUpdatePublish() {
    if (!guide || busy) return
    setBusy(true); setError(null)
    try {
      const updated = await updatePublishListeningGuide(guide.id)
      mergeGuide(updated)
      setNotice(updated.share_path ? `Published / updated — ${shareGuideUrl(updated.share_path)}` : 'Published')
    } catch (err) { setError(errorMessage(err, 'Update publish failed')) } finally { setBusy(false) }
  }

  const isStudio = mode === 'studio' && Boolean(user)
  const isActiveAuthTab = (tab: Mode) => mode === tab
  return (
    <div className={`shell ${isStudio ? 'shell-studio' : 'shell-auth'}`}>
      <a className="skip-link" href="#main">Skip to main content</a>
      <div className="atmosphere" aria-hidden="true" />
      <header className="topbar">
        <div className="topbar-brand">
          <p className="brand">Aulos</p>
          <p className="tagline">{user ? 'A listening practice, composed for you' : 'Deep listening companion'}</p>
        </div>
        {user && <div className="topbar-user"><span className="user-chip">{user.display_name || user.email}</span><button type="button" className="btn btn-ghost btn-sm" onClick={onLogout}>Sign out</button></div>}
      </header>
      <div className="toast-stack" aria-live="polite">
        {notice && <p className="toast toast-ok" role="status"><span>{notice}</span><button className="toast-dismiss" type="button" onClick={() => setNotice(null)} aria-label="Dismiss notification">×</button></p>}
        {error && <p className="toast toast-err" role="alert"><span>{error}</span><button className="toast-dismiss" type="button" onClick={() => setError(null)} aria-label="Dismiss error">×</button></p>}
      </div>
      <main id="main" className="stage">
        {!isStudio ? <section className="auth-gate" aria-label="Account access">
          <aside className="auth-brand">
            <p className="auth-kicker">Aulos listening portal</p><h1 className="auth-display">Hear the work beneath the performance.</h1>
            <p className="auth-lede">A composed route into the music: context, landmarks, and a practice for listening again.</p>
            <ul className="auth-points"><li>Research-led listening guides</li><li>Visible studio process</li><li>Your private guide library</li></ul>
          </aside>
          <section className="auth-panel">
            <div className="auth-tabs" role="tablist" aria-label="Account">
              {(['login', 'register', 'verify'] as const).map((tab) => <button key={tab} type="button" role="tab" aria-selected={isActiveAuthTab(tab)} className={isActiveAuthTab(tab) ? 'active' : ''} onClick={() => { setMode(tab); setError(null) }}>{tab === 'login' ? 'Sign in' : tab === 'register' ? 'Register' : 'Verify'}</button>)}
            </div>
            {mode === 'register' && <form className="auth-form" onSubmit={onRegister}><h2>Create account</h2><label htmlFor="reg-name">Display name</label><input id="reg-name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} autoComplete="name" /><label htmlFor="reg-email">Email</label><input id="reg-email" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" /><label htmlFor="reg-password">Password</label><PasswordField id="reg-password" required minLength={10} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" /><button className="btn btn-primary" type="submit" disabled={busy}>{busy ? 'Creating…' : 'Register'}</button></form>}
            {mode === 'login' && <form className="auth-form" onSubmit={onLogin}><h2>Sign in</h2><label htmlFor="login-email">Email</label><input id="login-email" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" /><label htmlFor="login-password">Password</label><PasswordField id="login-password" required value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" /><button className="btn btn-primary" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button><p className="auth-aside"><button type="button" className="linkish" onClick={() => { setMode('forgot'); setError(null); setNotice(null) }}>Forgot password?</button></p></form>}
            {mode === 'forgot' && <form className="auth-form" onSubmit={onForgot}><h2>Forgot password</h2><p className="auth-hint">Enter your email and we will send a reset link if an account exists.</p><label htmlFor="forgot-email">Email</label><input id="forgot-email" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" /><button className="btn btn-primary" type="submit" disabled={busy}>{busy ? 'Sending…' : 'Send reset link'}</button><p className="auth-aside"><button className="linkish" type="button" onClick={() => setMode('login')}>Back to sign in</button></p></form>}
            {mode === 'reset' && <form className="auth-form" onSubmit={onReset}><h2>Set new password</h2><label htmlFor="reset-token">Reset token</label><input id="reset-token" required value={resetToken} onChange={(event) => setResetToken(event.target.value)} autoComplete="off" /><label htmlFor="reset-password">New password</label><PasswordField id="reset-password" required minLength={10} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" /><label htmlFor="reset-password-confirm">Confirm password</label><PasswordField id="reset-password-confirm" required minLength={10} value={passwordConfirm} onChange={(event) => setPasswordConfirm(event.target.value)} autoComplete="new-password" /><button className="btn btn-primary" type="submit" disabled={busy}>{busy ? 'Updating…' : 'Update password'}</button></form>}
            {mode === 'verify' && <form className="auth-form" onSubmit={onVerify}><h2>Verify email</h2><label htmlFor="verify-token">Verification token</label><input id="verify-token" required value={verifyToken} onChange={(event) => setVerifyToken(event.target.value)} autoComplete="off" /><p className="hint">Paste the token from your email, or open the verification link directly.</p><button className="btn btn-primary" type="submit" disabled={busy}>{busy ? 'Verifying…' : 'Verify email'}</button></form>}
          </section>
        </section> : <div className="studio">
          <nav className="studio-tabs" role="tablist" aria-label="Studio views">
            <button type="button" role="tab" id="tab-guide" aria-selected={studioTab === 'guide'} aria-controls="pane-guide" className={studioTab === 'guide' ? 'active' : ''} onClick={() => setStudioTab('guide')}>Guide</button>
            <button type="button" role="tab" id="tab-atelier" aria-selected={studioTab === 'atelier'} aria-controls="pane-atelier" className={studioTab === 'atelier' ? 'active' : ''} onClick={() => setStudioTab('atelier')}>Atelier {busy && <span className="tab-pulse" aria-label="Working" />}</button>
            <button type="button" role="tab" id="tab-library" aria-selected={studioTab === 'library'} aria-controls="pane-library" className={studioTab === 'library' ? 'active' : ''} onClick={() => setStudioTab('library')}>Library <span className="tab-count">{history.length}</span></button>
          </nav>
          <section className={`compose-dock ${composeOpen ? 'is-open' : 'is-collapsed'}`} aria-labelledby="studio-title">
            <div className="compose-bar">
              <div className="compose-bar-copy">
                <p className="eyebrow">Listening studio</p>
                <h1 id="studio-title">{composeOpen ? 'Tell Aulos what you are learning' : 'Compose'}</h1>
              </div>
              <button
                type="button"
                className="btn btn-ghost btn-sm compose-toggle"
                aria-expanded={composeOpen}
                onClick={() => setComposeOpen((open) => !open)}
              >
                {composeOpen ? 'Hide' : 'New guide'}
              </button>
            </div>
            {composeOpen ? (
              <>
                <p className="hero-copy">Name a masterwork or choose a release. Aulos researches the work, then makes a guide for your next listening.</p>
                <form
                  className="composer studio-composer"
                  onSubmit={(event) => {
                    void onCompose(event)
                    setComposeOpen(false)
                  }}
                >
                  <div className="composer-row">
                    <div className="attach-wrap" ref={attachRef}>
                      <button className="attach-btn" type="button" disabled={busy} aria-label="Attach a source" aria-expanded={attachMenu !== null} onClick={() => setAttachMenu((menu) => menu ? null : 'menu')}>+</button>
                      {attachMenu === 'menu' && <div className="attach-menu"><button type="button" onClick={() => setAttachMenu('discogs')}>Search Discogs</button></div>}
                      {attachMenu === 'discogs' && <div className="discogs-picker"><label className="sr-only" htmlFor="discogs-search">Search Discogs releases</label><input id="discogs-search" autoFocus value={discogsQuery} placeholder="Artist, work, label, catalogue no." onChange={(event) => setDiscogsQuery(event.target.value)} />{discogsQuery.length > 0 && discogsQuery.length < 2 && <p className="discogs-status">Type at least two characters.</p>}{discogsLoading && <p className="discogs-status">Searching Discogs…</p>}{discogsError && <p className="discogs-status is-error">{discogsError}</p>}<div className="discogs-results"><ul>{discogsResults.map((hit) => <li key={hit.id}><button type="button" onClick={() => onPickDiscogs(hit)}>{hit.thumb ? <img src={hit.thumb} alt="" /> : <span className="discogs-thumb-fallback" aria-hidden="true" />}<span className="discogs-hit-body"><span className="discogs-hit-title">{hit.title}</span><span className="discogs-hit-meta">{[hit.catno, hit.label, hit.year].filter(Boolean).join(' · ')}</span></span></button></li>)}</ul></div></div>}
                    </div>
                    <div><label className="sr-only" htmlFor="prompt">Listening intent</label><textarea id="prompt" rows={2} value={draft} placeholder="I'm listening to… or /discogs #423-287-1" onChange={(event) => setDraft(event.target.value)} /></div>
                  </div>
                  <div className="composer-actions"><div className="composer-chips"><button className="chip" type="button" disabled={busy} onClick={() => setDraft(EXAMPLE)}>Goldberg</button><button className="chip" type="button" disabled={busy} onClick={() => setDraft(DISCOGS_EXAMPLE)}>Discogs</button></div><button className="btn btn-primary" type="submit" disabled={busy || !draft.trim()}>{busy ? 'Researching…' : 'Compose guide'}</button></div>
                </form>
              </>
            ) : null}
          </section>
          <div className="studio-stage" data-tab={studioTab}>
            <section id="pane-atelier" role="tabpanel" aria-labelledby="tab-atelier" hidden={studioTab !== 'atelier'} className="workflow panel-card studio-pane">
              <div className="section-head">
                <div>
                  <h2 id="workflow-title">Atelier</h2>
                  <p className="section-sub">Countable research chain — every stage visible</p>
                </div>
                {guide && <span className="meta-pill">{guide.source} · {guide.status}{guide.published ? ' · published' : ''}</span>}
              </div>
              {(chainProgress || visibleSteps.length > 0) && (
                <div className="chain-progress" aria-live="polite">
                  <div className="chain-progress-meta">
                    <span>
                      Progress{' '}
                      <strong>
                        {chainProgress?.done ??
                          visibleSteps.filter((s) =>
                            ['done', 'completed', 'ok', 'skip', 'skipped', 'failed'].includes(s.status),
                          ).length}
                        {' / '}
                        {chainProgress?.total || visibleSteps[0]?.total || visibleSteps.length || '—'}
                      </strong>
                    </span>
                    {busy && <span className="chain-progress-live">Running</span>}
                  </div>
                  <div
                    className="chain-progress-bar"
                    role="progressbar"
                    aria-valuemin={0}
                    aria-valuemax={chainProgress?.total || visibleSteps.length || 1}
                    aria-valuenow={
                      chainProgress?.done ??
                      visibleSteps.filter((s) =>
                        ['done', 'completed', 'ok', 'skip', 'skipped', 'failed'].includes(s.status),
                      ).length
                    }
                  >
                    <span
                      style={{
                        width: `${Math.min(
                          100,
                          Math.round(
                            (100 *
                              (chainProgress?.done ??
                                visibleSteps.filter((s) =>
                                  ['done', 'completed', 'ok', 'skip', 'skipped', 'failed'].includes(s.status),
                                ).length)) /
                              Math.max(
                                1,
                                chainProgress?.total || visibleSteps[0]?.total || visibleSteps.length || 1,
                              ),
                          ),
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              )}
              {retryableGuideId != null && (
                <div className="chain-recover">
                  <p>Chain interrupted or failed. Progress is saved — retry to continue robustly.</p>
                  <button type="button" className="btn btn-primary btn-sm" disabled={busy} onClick={() => void onRetryChain()}>
                    Retry chain
                  </button>
                </div>
              )}
              <div className="trail" ref={trailRef}>
                {visibleSteps.length === 0 && !busy && (
                  <p className="empty">Your process appears here: Discogs → identity → knowledge → web → LLM → agent skills → persist.</p>
                )}
                {busy && visibleSteps.length === 0 && (
                  <p className="thinking"><span className="thinking-dot" />Aulos is opening the research atelier…</p>
                )}
                <ol className="step-list">
                  {visibleSteps.map((step, index) => (
                    <li key={step.id} className={`step status-${step.status}`} style={{ animationDelay: `${index * 0.04}s` }}>
                      <div className="step-index">{step.index ?? index + 1}</div>
                      <div>
                        <p className="step-title">
                          {step.title}
                          <span className="step-status-label">{step.status}</span>
                        </p>
                        {step.skill_id && (
                          <p className="step-skill">
                            {step.skill_id}
                            {step.skill_version ? `@${step.skill_version}` : ''}
                          </p>
                        )}
                        <p className="step-thinking">{step.thinking}</p>
                        {step.detail && <p className="step-detail">{step.detail}</p>}
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
              {chainTrace && <div className="chain-trace"><button type="button" className="chain-trace-toggle" aria-expanded={traceOpen} onClick={() => setTraceOpen((open) => !open)}>Diagnostic log · {chainTrace.deviations?.length ? `${chainTrace.deviations.length} deviation${chainTrace.deviations.length === 1 ? '' : 's'}` : 'clean'}</button>{traceOpen && <div className="chain-trace-body">{chainTrace.deviations?.length ? <ul className="trace-deviations">{chainTrace.deviations.map((deviation, index) => <li key={`${deviation.code}-${index}`}>{deviation.code}: {deviation.summary}</li>)}</ul> : <p className="trace-clean">No deviations recorded.</p>}{chainTrace.milestones?.length ? <ul className="trace-milestones">{chainTrace.milestones.map((milestone) => <li key={milestone.id} className={`trace-${milestone.status}`}><span className="trace-id">{milestone.id}</span><span className="trace-status">{milestone.status}</span><span>{milestone.summary}</span></li>)}</ul> : null}{chainTrace.identity_arc?.length ? <div className="trace-arc"><p className="trace-arc-label">Identity arc</p><ol>{chainTrace.identity_arc.map((arc, index) => <li key={`${arc.stage}-${index}`}><code>{arc.stage}</code> · {[arc.composer, arc.work_title].filter(Boolean).join(' — ')}</li>)}</ol></div> : null}</div>}</div>}
            </section>
            <section id="pane-guide" role="tabpanel" aria-labelledby="tab-guide" hidden={studioTab !== 'guide'} className="guide-pane panel-card studio-pane">
              <div className="section-head"><div><h2 id="guide-title">Listening guide</h2>{guide?.created_at && <p className="section-sub">{guide.work_title} · {formatDateTime(guide.created_at)}</p>}</div>{guide && showGuide && <div className="guide-actions" ref={actionsRef}><button type="button" className="btn btn-ghost btn-sm" disabled={busy} onClick={() => { setActionsOpen(false); void onRecompose() }}>Re-compose</button><button type="button" className="btn btn-ghost btn-sm actions-more-btn" aria-expanded={actionsOpen} aria-haspopup="menu" onClick={() => setActionsOpen((open) => !open)}>More</button><div className={`guide-actions-more ${actionsOpen ? 'is-open' : ''}`} role="menu">{!guide.published ? <button type="button" role="menuitem" className="btn btn-ghost btn-sm" disabled={busy} onClick={() => { setActionsOpen(false); void onPublish() }}>Publish & copy link</button> : <><button type="button" role="menuitem" className="btn btn-ghost btn-sm" onClick={() => { setActionsOpen(false); void onCopyShareLink() }}>Copy share link</button><a className="btn btn-ghost btn-sm" role="menuitem" href={guide.share_path || '#'} target="_blank" rel="noopener noreferrer" onClick={() => setActionsOpen(false)}>Open share page</a><button type="button" role="menuitem" className="btn btn-ghost btn-sm" disabled={busy} onClick={() => { setActionsOpen(false); void onUnpublish() }}>Unpublish</button></>}<button type="button" role="menuitem" className="btn btn-ghost btn-sm" disabled={busy} onClick={() => { setActionsOpen(false); void onUpdatePublish() }}>Update publish</button><button type="button" role="menuitem" className="btn btn-ghost btn-sm" onClick={() => { setActionsOpen(false); const url = URL.createObjectURL(new Blob([prepareGuideHtml(guide.guide_html)], { type: 'text/html' })); window.open(url, '_blank', 'noopener,noreferrer') }}>Open full page</button></div></div>}</div>
              {guide?.published && guide.share_path && <p className="share-url">Public link: <code>{shareGuideUrl(guide.share_path)}</code></p>}
              {guide && showGuide ? <iframe className="guide-frame" title={guide.work_title} sandbox={GUIDE_IFRAME_SANDBOX} srcDoc={prepareGuideHtml(guide.guide_html)} /> : <div className="guide-placeholder"><p className="placeholder-title">A guide awaits.</p><p>Tell Aulos what you are listening for, and the page will appear here.</p></div>}
            </section>
            <section id="pane-library" role="tabpanel" aria-labelledby="tab-library" hidden={studioTab !== 'library'} className="library panel-card studio-pane">
<div className="section-head">
                <div>
                  <h2 id="library-title">Library</h2>
                  <p className="section-sub">Search, filter, favorite, and manage guides</p>
                </div>
              </div>
              <div className="library-toolbar">
                <label className="sr-only" htmlFor="library-search">Search library</label>
                <input
                  id="library-search"
                  className="library-search"
                  value={libraryQuery}
                  placeholder="Search title, composer…"
                  onChange={(event) => setLibraryQuery(event.target.value)}
                />
                <div className="library-filters" role="group" aria-label="Library filters">
                  {([
                    ['all', 'All'],
                    ['favorites', 'Favorites'],
                    ['published', 'Published'],
                    ['progress', 'In progress'],
                  ] as const).map(([id, label]) => (
                    <button
                      key={id}
                      type="button"
                      className={libraryFilter === id ? 'active' : ''}
                      onClick={() => setLibraryFilter(id)}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <label className="sr-only" htmlFor="library-tag">Filter by tag</label>
                <input
                  id="library-tag"
                  className="library-tag-filter"
                  value={tagFilter}
                  placeholder="Tag filter"
                  onChange={(event) => setTagFilter(event.target.value)}
                />
              </div>
              {history.length ? (
                <ul className="library-list">
                  {history.map((item) => (
                    <li key={item.id} className={`lib-row status-${item.status}`}>
                      <button
                        type="button"
                        className={`lib-open ${guide?.id === item.id ? 'active' : ''}`}
                        onClick={() => openHistoryItem(item)}
                      >
                        <span className="lib-title-row">
                          <span className="lib-title">{item.work_title}</span>
                          <span className={`lib-status status-${item.status}`}>{item.status}</span>
                        </span>
                        <span className="lib-meta">
                          {item.composer}
                          {item.published ? ' · shared' : ''}
                          {item.created_at ? ` · ${formatDateTime(item.created_at)}` : ''}
                        </span>
                        {item.tags?.length ? (
                          <span className="lib-tags">{item.tags.map((tag) => <span key={tag}>{tag}</span>)}</span>
                        ) : null}
                        {item.status === 'failed' && item.error_detail ? (
                          <span className="lib-error">{item.error_detail}</span>
                        ) : null}
                      </button>
                      <div className="lib-actions">
                        <button
                          type="button"
                          className={`lib-icon ${item.favorited ? 'is-on' : ''}`}
                          aria-label={item.favorited ? 'Remove favorite' : 'Add favorite'}
                          onClick={(event) => void onToggleFavorite(item, event)}
                        >
                          ★
                        </button>
                        <button
                          type="button"
                          className="lib-icon"
                          aria-label="Edit tags"
                          onClick={(event) => {
                            event.stopPropagation()
                            setTaggingId(item.id)
                            setTagDraft((item.tags || []).join(', '))
                          }}
                        >
                          #
                        </button>
                        {item.status === 'failed' ? (
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            onClick={(event) => {
                              event.stopPropagation()
                              void onRetryFailed(item)
                            }}
                          >
                            Retry
                          </button>
                        ) : null}
                        <button
                          type="button"
                          className="lib-icon lib-danger"
                          aria-label="Delete guide"
                          onClick={(event) => void onDeleteGuide(item, event)}
                        >
                          ×
                        </button>
                      </div>
                      {taggingId === item.id ? (
                        <div className="lib-tag-editor">
                          <label className="sr-only" htmlFor={`tags-${item.id}`}>Tags</label>
                          <input
                            id={`tags-${item.id}`}
                            value={tagDraft}
                            placeholder="salon, teach"
                            onChange={(event) => setTagDraft(event.target.value)}
                          />
                          <button type="button" className="btn btn-primary btn-sm" onClick={() => void onSaveTags(item)}>
                            Save
                          </button>
                          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setTaggingId(null)}>
                            Cancel
                          </button>
                        </div>
                      ) : null}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="empty">Guides you compose will be kept here.</p>
              )}

            </section>
          </div>
        </div>}
      </main>
    </div>
  )
}

export default App
