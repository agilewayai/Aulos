import { useEffect, useState } from 'react'
import { searchDiscogsReleases, type DiscogsSearchHit } from './api'
import { errorMessage } from './errors'

const DEBOUNCE_MS = 280
const MIN_CHARS = 2

/** Debounced Discogs release search (Studio attach + 我的聆乐 compose). */
export function useDiscogsSearch(query: string, enabled: boolean, errorFallback = 'Discogs search failed') {
  const [hits, setHits] = useState<DiscogsSearchHit[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const q = query.trim()
    if (!enabled || q.length < MIN_CHARS) {
      if (q.length < MIN_CHARS) setHits([])
      setLoading(false)
      setError(null)
      return
    }
    let current = true
    const timer = window.setTimeout(() => {
      setLoading(true)
      setError(null)
      searchDiscogsReleases(q)
        .then((result) => {
          if (current) setHits(result.results)
        })
        .catch((err) => {
          if (current) {
            setHits([])
            setError(errorMessage(err, errorFallback))
          }
        })
        .finally(() => {
          if (current) setLoading(false)
        })
    }, DEBOUNCE_MS)
    return () => {
      current = false
      window.clearTimeout(timer)
    }
  }, [query, enabled, errorFallback])

  return { hits, loading, error, minChars: MIN_CHARS }
}

export function discogsHitMeta(hit: DiscogsSearchHit, extra?: Array<string | undefined | null>): string {
  return [hit.catno, hit.label, hit.year, ...(extra || [])].filter(Boolean).join(' · ')
}
