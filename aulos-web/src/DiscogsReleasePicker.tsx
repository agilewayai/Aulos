import type { DiscogsSearchHit } from './api'
import { discogsHitMeta, useDiscogsSearch } from './useDiscogsSearch'

export type DiscogsReleasePickerProps = {
  query: string
  onQueryChange: (q: string) => void
  onPick: (hit: DiscogsSearchHit) => void
  disabled?: boolean
  /** studio: compact attach dropdown; diary: card list with CTA */
  variant?: 'studio' | 'diary'
  inputId?: string
  autoFocus?: boolean
  placeholder?: string
  /** Override default EN status strings (diary uses zh). */
  labels?: {
    tooShort?: string
    searching?: string
    empty?: string
    pickCta?: string
    searchLabel?: string
    errorFallback?: string
  }
}

/**
 * Shared Discogs release search UI — Studio attach menu + 我的聆乐 compose (META-001 §3.5).
 */
export function DiscogsReleasePicker({
  query,
  onQueryChange,
  onPick,
  disabled,
  variant = 'studio',
  inputId = 'discogs-search',
  autoFocus,
  placeholder = 'Artist, work, label, catalogue no.',
  labels = {},
}: DiscogsReleasePickerProps) {
  const { hits, loading, error, minChars } = useDiscogsSearch(
    query,
    true,
    labels.errorFallback ?? 'Discogs search failed',
  )
  const tooShort = labels.tooShort ?? 'Type at least two characters.'
  const searching = labels.searching ?? 'Searching Discogs…'
  const empty = labels.empty ?? 'No matches. Try a catalogue number or English composer name.'
  const pickCta = labels.pickCta ?? 'Use release'
  const searchLabel = labels.searchLabel ?? 'Search Discogs releases'
  const q = query.trim()

  if (variant === 'diary') {
    return (
      <div className="diary-compose" role="search">
        <p className="diary-compose-lead">
          在下方搜索并点选一张黑胶或 CD。选中后会拉取封面、演职员与曲目，成为这篇日记的主体。
        </p>
        <label htmlFor={inputId}>{searchLabel}</label>
        <input
          id={inputId}
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          autoComplete="off"
        />
        {q.length > 0 && q.length < minChars ? <p className="diary-status">{tooShort}</p> : null}
        {loading ? (
          <p className="diary-status" role="status">
            {searching}
          </p>
        ) : null}
        {error ? <p className="diary-status is-error">{error}</p> : null}
        <ul className="diary-hits">
          {hits.map((hit) => (
            <li key={hit.id}>
              <div className="diary-hit-card">
                {hit.thumb ? <img src={hit.thumb} alt="" /> : <span className="diary-thumb-fallback" aria-hidden />}
                <div className="diary-hit-body">
                  <strong>{hit.title}</strong>
                  <small>{discogsHitMeta(hit, [hit.country])}</small>
                </div>
                <button
                  type="button"
                  className="btn btn-primary diary-hit-cta"
                  disabled={disabled}
                  onClick={() => onPick(hit)}
                >
                  {pickCta}
                </button>
              </div>
            </li>
          ))}
        </ul>
        {q.length >= minChars && !loading && !hits.length ? <p className="diary-status">{empty}</p> : null}
      </div>
    )
  }

  return (
    <div className="discogs-picker">
      <label className="sr-only" htmlFor={inputId}>
        {searchLabel}
      </label>
      <input
        id={inputId}
        autoFocus={autoFocus}
        value={query}
        placeholder={placeholder}
        onChange={(e) => onQueryChange(e.target.value)}
      />
      {q.length > 0 && q.length < minChars ? <p className="discogs-status">{tooShort}</p> : null}
      {loading ? <p className="discogs-status">{searching}</p> : null}
      {error ? <p className="discogs-status is-error">{error}</p> : null}
      <div className="discogs-results">
        <ul>
          {hits.map((hit) => (
            <li key={hit.id}>
              <button type="button" disabled={disabled} onClick={() => onPick(hit)}>
                {hit.thumb ? <img src={hit.thumb} alt="" /> : <span className="discogs-thumb-fallback" aria-hidden="true" />}
                <span className="discogs-hit-body">
                  <span className="discogs-hit-title">{hit.title}</span>
                  <span className="discogs-hit-meta">{discogsHitMeta(hit)}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
