import { useEffect, useRef, useState } from 'react'
import {
  alreadyReloadedFor,
  ASSET_VERSION_CHECK_EVENT,
  clearReloadAttempt,
  dismissBuild,
  fetchServerVersion,
  hardReload,
  isBuildOutdated,
  isDismissed,
  markReloadedFor,
} from './assetVersion'
import { captureRegisteredScenes } from './sessionScene'

const POLL_MS = 30_000
const MIN_CHECK_GAP_MS = 5_000
const BACKOFF_BASE_MS = 60_000
const BACKOFF_MAX_MS = 10 * 60_000
const AUTO_RELOAD_MS = 1_200

type Phase = 'idle' | 'updating' | 'prompt'

/** Detects deployed asset drift; auto-refreshes once, then offers a manual update. */
export function AssetUpdateToast() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [remoteBuildId, setRemoteBuildId] = useState<string | null>(null)
  const lastCheckRef = useRef(0)
  const backoffUntilRef = useRef(0)
  const backoffMsRef = useRef(BACKOFF_BASE_MS)
  const timerRef = useRef<number | null>(null)
  const reloadTimerRef = useRef<number | null>(null)
  const reloadingRef = useRef(false)

  useEffect(() => {
    let cancelled = false
    try {
      const url = new URL(window.location.href)
      if (url.searchParams.has('_aulos_v')) {
        url.searchParams.delete('_aulos_v')
        window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`)
      }
    } catch {
      /* ignore */
    }

    const schedule = (delay: number) => {
      if (timerRef.current != null) window.clearTimeout(timerRef.current)
      timerRef.current = window.setTimeout(() => void check(false), delay)
    }

    const beginAutoReload = (buildId: string) => {
      if (reloadingRef.current || cancelled) return
      reloadingRef.current = true
      markReloadedFor(buildId)
      captureRegisteredScenes()
      setRemoteBuildId(buildId)
      setPhase('updating')
      if (reloadTimerRef.current != null) window.clearTimeout(reloadTimerRef.current)
      reloadTimerRef.current = window.setTimeout(() => {
        hardReload()
      }, AUTO_RELOAD_MS)
    }

    const check = async (urgent = false) => {
      if (cancelled || reloadingRef.current) return
      const now = Date.now()
      if (now < backoffUntilRef.current) {
        schedule(backoffUntilRef.current - now)
        return
      }
      if (!urgent && now - lastCheckRef.current < MIN_CHECK_GAP_MS) {
        schedule(MIN_CHECK_GAP_MS - (now - lastCheckRef.current))
        return
      }
      lastCheckRef.current = now

      const remote = await fetchServerVersion()
      if (cancelled || reloadingRef.current) return

      if (remote?.status === 429) {
        const wait = Math.min(backoffMsRef.current, BACKOFF_MAX_MS)
        backoffUntilRef.current = Date.now() + wait
        backoffMsRef.current = Math.min(wait * 2, BACKOFF_MAX_MS)
        schedule(wait)
        return
      }

      backoffMsRef.current = BACKOFF_BASE_MS
      const buildId = remote?.buildId
      if (!buildId) {
        schedule(POLL_MS)
        return
      }

      if (!isBuildOutdated(buildId)) {
        clearReloadAttempt(buildId)
        setPhase('idle')
        setRemoteBuildId(null)
        schedule(POLL_MS)
        return
      }

      if (isDismissed(buildId)) {
        setPhase('idle')
        setRemoteBuildId(null)
        schedule(POLL_MS)
        return
      }

      if (alreadyReloadedFor(buildId)) {
        setRemoteBuildId(buildId)
        setPhase('prompt')
        schedule(POLL_MS)
        return
      }

      beginAutoReload(buildId)
    }

    void check(true)
    const onVisible = () => {
      if (document.visibilityState === 'visible') void check(true)
    }
    const onAssetCheck = () => void check(true)
    window.addEventListener('focus', onVisible)
    document.addEventListener('visibilitychange', onVisible)
    window.addEventListener(ASSET_VERSION_CHECK_EVENT, onAssetCheck)
    return () => {
      cancelled = true
      if (timerRef.current != null) window.clearTimeout(timerRef.current)
      if (reloadTimerRef.current != null) window.clearTimeout(reloadTimerRef.current)
      window.removeEventListener('focus', onVisible)
      document.removeEventListener('visibilitychange', onVisible)
      window.removeEventListener(ASSET_VERSION_CHECK_EVENT, onAssetCheck)
    }
  }, [])

  if (phase === 'idle' || !remoteBuildId) return null

  if (phase === 'updating') {
    return (
      <div className="asset-update-toast" role="status" aria-live="polite">
        <span className="asset-update-toast__pulse" aria-hidden="true" />
        <span className="asset-update-toast__text">New version found — refreshing…</span>
        <button
          type="button"
          className="asset-update-toast__dismiss"
          aria-label="Dismiss"
          onClick={() => {
            if (reloadTimerRef.current != null) window.clearTimeout(reloadTimerRef.current)
            reloadingRef.current = false
            dismissBuild(remoteBuildId)
            setPhase('idle')
            setRemoteBuildId(null)
          }}
        >
          ×
        </button>
      </div>
    )
  }

  return (
    <div className="asset-update-toast" role="status" aria-live="polite">
      <span className="asset-update-toast__text">New version available</span>
      <button
        type="button"
        className="asset-update-toast__action"
        onClick={() => {
          captureRegisteredScenes()
          markReloadedFor(remoteBuildId)
          hardReload()
        }}
      >
        Update
      </button>
      <button
        type="button"
        className="asset-update-toast__dismiss"
        aria-label="Dismiss"
        onClick={() => {
          dismissBuild(remoteBuildId)
          setPhase('idle')
          setRemoteBuildId(null)
        }}
      >
        ×
      </button>
    </div>
  )
}
