import type { ReactNode } from 'react'
import type { ListeningDiaryPost } from './api'
import { sourceKindLabel } from './sourceKind'

export { sourceKindLabel }

export type ListeningPostCardProps = {
  post: ListeningDiaryPost
  onOpen: () => void
  disabled?: boolean
  titleAs?: 'h2' | 'h3'
  className?: string
  /** Extra byline content (status pill, author avatar, etc.) */
  byline?: ReactNode
  /** Meta row under excerpt */
  meta?: ReactNode
  posinset?: number
  setsize?: number
}

/**
 * Shared cover+title card for 聆乐广场 feed and 我的聆乐 blog list.
 * All cards share one size in the grid (no featured lead).
 */
export function ListeningPostCard({
  post,
  onOpen,
  disabled,
  titleAs = 'h2',
  className = '',
  byline,
  meta,
  posinset,
  setsize,
}: ListeningPostCardProps) {
  const excerpt = (post.listening_note || '').trim()
  const TitleTag = titleAs
  return (
    <article
      className={`plaza-card ${className}`.trim()}
      aria-posinset={posinset}
      aria-setsize={setsize}
    >
      <button type="button" className="plaza-card-hit" onClick={onOpen} disabled={disabled}>
        <div className="plaza-card-cover-wrap">
          {post.cover_image_url ? (
            <img className="plaza-card-cover" src={post.cover_image_url} alt="" loading="lazy" />
          ) : (
            <div className="plaza-card-cover plaza-card-cover-empty" aria-hidden />
          )}
          <span className="plaza-card-kind">{sourceKindLabel(post.source_kind)}</span>
        </div>
        <div className="plaza-card-body">
          {byline ? <p className="plaza-card-byline">{byline}</p> : null}
          <TitleTag className="plaza-card-title">{post.title || '未命名唱片'}</TitleTag>
          {excerpt ? <p className="plaza-card-excerpt">{excerpt}</p> : null}
          {meta ? <p className="plaza-card-meta">{meta}</p> : null}
        </div>
      </button>
    </article>
  )
}
