import { useEffect, useRef, useState } from 'react'
import {
  dismissBuild,
  fetchServerVersion,
  isBuildOutdated,
  isDismissed,
} from './assetVersion'

const POLL_MS = 60_000
const MIN_CHECK_GAP_MS = 12_000
const BACKOFF_BASE_MS = 60_000
const BACKOFF_MAX_MS = 10 * 60_000

/** Soft, dismissible tip when deployed assets diverge from the running tab. */
export function AssetUpdateToast() {
  const [remoteBuildId, setRemoteBuildId] = useState<string | null>(null)
  const lastCheckRef = useRef(0)
  const backoffUntilRef = useRef(0)
  const backoffMsRef = useRef(BACKOFF_BASE_MS)
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    let cancelled = false

    const schedule = (delay: number) => {
      if (timerRef.current != null) window.clearTimeout(timerRef.current)
      timerRef.current = window.setTimeout(() => void check(), delay)
    }

    const check = async () => {
      if (cancelled) return
      const now = Date.now()
      if (now < backoffUntilRef.current) {
        schedule(backoffUntilRef.current - now)
        return
      }
      if (now - lastCheckRef.current < MIN_CHECK_GAP_MS) {
        schedule(MIN_CHECK_GAP_MS - (now - lastCheckRef.current))
        return
      }
      lastCheckRef.current = now

      const remote = await fetchServerVersion()
      if (cancelled) return

      if (remote?.status === 429) {
        const wait = Math.min(backoffMsRef.current, BACKOFF_MAX_MS)
        backoffUntilRef.current = Date.now() + wait
        backoffMsRef.current = Math.min(wait * 2, BACKOFF_MAX_MS)
        schedule(wait)
        return
      }

      backoffMsRef.current = BACKOFF_BASE_MS
      if (!remote?.buildId) {
        schedule(POLL_MS)
        return
      }
      if (!isBuildOutdated(remote.buildId) || isDismissed(remote.buildId)) {
        setRemoteBuildId(null)
        schedule(POLL_MS)
        return
      }
      setRemoteBuildId(remote.buildId)
      schedule(POLL_MS)
    }

    void check()
    const onVisible = () => {
      if (document.visibilityState === 'visible') void check()
    }
    window.addEventListener('focus', onVisible)
    document.addEventListener('visibilitychange', onVisible)
    return () => {
      cancelled = true
      if (timerRef.current != null) window.clearTimeout(timerRef.current)
      window.removeEventListener('focus', onVisible)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [])

  if (!remoteBuildId) return null

  return (
    <div className="asset-update-toast" role="status" aria-live="polite">
      <span className="asset-update-toast__text">New version</span>
      <button
        type="button"
        className="asset-update-toast__action"
        onClick={() => window.location.reload()}
      >
        Reload
      </button>
      <button
        type="button"
        className="asset-update-toast__dismiss"
        aria-label="Dismiss"
        onClick={() => {
          dismissBuild(remoteBuildId)
          setRemoteBuildId(null)
        }}
      >
        ×
      </button>
    </div>
  )
}
