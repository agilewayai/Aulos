import { useEffect, useId, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import {
  ackDiaryGuideLink,
  addPlazaComment,
  createListeningDiary,
  deleteDiaryGuideLink,
  deleteListeningDiary,
  dismissDiaryGuideLink,
  enqueueDiaryGuide,
  fetchListeningDiary,
  fetchPlazaFeed,
  fetchPlazaHome,
  fetchPlazaPost,
  followUser,
  likePlazaPost,
  listDiaryGuideTasks,
  listListeningDiary,
  listPlazaComments,
  patchListeningDiary,
  publishDiaryGuideLink,
  publishListeningDiary,
  resolvePersonEntity,
  reviseDiaryGuideLink,
  retryListeningJob,
  streamGuideEvents,
  unlikePlazaPost,
  unpublishDiaryGuideLink,
  unpublishListeningDiary,
  type DiaryGuideLink,
  type DiscogsSearchHit,
  type ListeningDiaryPost,
  type PersonEntityCard,
  type User,
  type WorkflowStep,
} from './api'
import { formatDateTime } from './time'
import { errorMessage } from './errors'
import { AtelierTrail } from './AtelierTrail'
import { ProcessScorecardCard } from './ProcessScorecardCard'
import { GenerationRoundsPanel } from './GenerationRoundsPanel'
import { GuideReader } from './GuideReader'
import { DiscogsReleasePicker } from './DiscogsReleasePicker'
import { ListeningPostCard, sourceKindLabel } from './ListeningPostCard'
import { chainProgressFromSteps, sortWorkflowSteps, upsertWorkflowStep, type ChainProgress } from './atelierTrailUtils'
import {
  buildDiaryTagCloud,
  buildMonthGrid,
  countsByDate,
  filterDiaryPosts,
  postListeningDate,
  shiftMonth,
  tagFontRem,
  tagKindLabel,
  tagWeightScale,
  todayIsoLocal,
  type DiaryTag,
} from './diaryBlogUtils'

type PersonKind = 'composer' | 'performer' | 'ensemble' | 'person'

function PersonNameLinks({
  names,
  kind,
  onOpen,
}: {
  names: string[]
  kind: PersonKind
  onOpen: (name: string, kind: PersonKind) => void
}) {
  if (!names.length) return null
  return (
    <span className="person-name-list">
      {names.map((name, i) => (
        <span key={`${kind}-${name}-${i}`}>
          {i > 0 ? '、' : null}
          <button type="button" className="person-name-link" onClick={() => onOpen(name, kind)}>
            {name}
          </button>
        </span>
      ))}
    </span>
  )
}

function PersonEntityPanel({
  open,
  loading,
  error,
  card,
  onClose,
}: {
  open: boolean
  loading: boolean
  error: string
  card: PersonEntityCard | null
  onClose: () => void
}) {
  const [locale, setLocale] = useState<'zh' | 'en'>('zh')
  if (!open) return null

  const sourceLabel =
    card?.source === 'aggregated' || card?.source === 'enriched'
      ? '多源权威聚合并写入知识库'
      : card?.source === 'knowledge'
        ? '来自知识库'
        : '暂未找到可靠资料'

  const displayName =
    locale === 'en'
      ? card?.display_name_en || card?.display_name || card?.name || 'Person'
      : card?.display_name_zh || card?.display_name || card?.name || '人物卡片'
  const summary =
    locale === 'en'
      ? card?.summary_en || card?.summary || ''
      : card?.summary_zh || card?.summary || ''
  const origin =
    locale === 'en' ? card?.summary_en_origin || '' : card?.summary_zh_origin || ''
  const originLabel =
    origin === 'translated'
      ? locale === 'en'
        ? 'translated'
        : '译自另一语种'
      : origin === 'wikipedia'
        ? 'Wikipedia'
        : origin === 'discogs'
          ? 'Discogs'
          : origin === 'wikidata'
            ? 'Wikidata'
            : origin === 'local'
              ? locale === 'en'
                ? 'knowledge base'
                : '知识库'
              : ''

  return (
    <div className="person-card-backdrop" role="presentation" onClick={onClose}>
      <aside
        className="person-card-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="person-card-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="person-card-head">
          <div>
            <p className="person-card-kicker">{sourceLabel}</p>
            <h2 id="person-card-title">{displayName}</h2>
            {(card?.lifespan || card?.era) && (
              <p className="person-card-meta">
                {[card.lifespan, card.era].filter(Boolean).join(' · ')}
              </p>
            )}
            {(card?.display_name_en || card?.display_name_zh) && (
              <p className="person-card-meta">
                {[card.display_name_en, card.display_name_zh].filter(Boolean).join(' · ')}
              </p>
            )}
          </div>
          <div className="person-card-head-actions">
            <div className="person-locale-toggle" role="group" aria-label="语言">
              <button
                type="button"
                className={locale === 'zh' ? 'is-on' : ''}
                onClick={() => setLocale('zh')}
              >
                中文
              </button>
              <button
                type="button"
                className={locale === 'en' ? 'is-on' : ''}
                onClick={() => setLocale('en')}
              >
                EN
              </button>
            </div>
            <button type="button" className="btn btn-ghost btn-sm" onClick={onClose}>
              关闭
            </button>
          </div>
        </header>
        {loading ? (
          <div className="person-card-loading">
            <div className="pulse line w90" />
            <div className="pulse line w75" />
            <div className="pulse line w85" />
            <p>正在聚合 Discogs / Wikidata / Wikipedia…</p>
          </div>
        ) : error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : (
          <div className="person-card-body">
            {card?.portrait_url ? (
              <img className="person-card-portrait" src={card.portrait_url} alt="" loading="lazy" />
            ) : null}
            {summary ? (
              <>
                {originLabel ? <p className="person-card-origin">简介来源：{originLabel}</p> : null}
                <p className="person-card-summary">{summary}</p>
              </>
            ) : (
              <p className="diary-empty">{locale === 'en' ? 'No biography yet' : '暂无简介'}</p>
            )}
            {card?.sources && card.sources.length > 0 ? (
              <div className="person-card-sources">
                <h3>权威来源</h3>
                <ul>
                  {card.sources.map((s, i) => (
                    <li key={`${s.source_id}-${i}`}>
                      {s.url ? (
                        <a href={s.url} target="_blank" rel="noreferrer">
                          {s.source_id}
                          {s.lang ? ` (${s.lang})` : ''}
                        </a>
                      ) : (
                        <span>
                          {s.source_id}
                          {s.lang ? ` (${s.lang})` : ''}
                        </span>
                      )}
                      {s.role ? <small> · {s.role}</small> : null}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {card?.snippets && card.snippets.length > 0 ? (
              <div className="person-card-snippets">
                <h3>知识库摘录</h3>
                <ul>
                  {card.snippets.slice(0, 3).map((s, i) => (
                    <li key={`${s.title}-${i}`}>
                      {s.title ? <strong>{s.title}</strong> : null}
                      <span>{s.text}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {card?.provenance && card.provenance.length > 0 && !(card.sources && card.sources.length) ? (
              <p className="person-card-provenance">
                来源：{' '}
                {card.provenance.map((p, i) => (
                  <span key={`${p.source_id}-${i}`}>
                    {i > 0 ? ' · ' : null}
                    {p.url ? (
                      <a href={p.url} target="_blank" rel="noreferrer">
                        {p.source_id || '来源'}
                      </a>
                    ) : (
                      p.source_id || '来源'
                    )}
                  </span>
                ))}
              </p>
            ) : null}
            {card?.external_ids?.wikidata ? (
              <p className="person-card-provenance">
                Wikidata:{' '}
                <a
                  href={`https://www.wikidata.org/wiki/${card.external_ids.wikidata}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  {String(card.external_ids.wikidata)}
                </a>
              </p>
            ) : null}
          </div>
        )}
      </aside>
    </div>
  )
}

function usePersonCard() {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [card, setCard] = useState<PersonEntityCard | null>(null)

  async function openPerson(name: string, kind: PersonKind) {
    setOpen(true)
    setLoading(true)
    setError('')
    setCard(null)
    try {
      const data = await resolvePersonEntity(name, kind, true, 'zh')
      setCard(data)
    } catch (e) {
      setError(errorMessage(e, '无法加载人物信息'))
    } finally {
      setLoading(false)
    }
  }

  return {
    openPerson,
    panelProps: {
      open,
      loading,
      error,
      card,
      onClose: () => setOpen(false),
    },
  }
}

function DiarySkeleton() {
  return (
    <div className="diary-skeleton" aria-hidden="true">
      <div className="diary-skeleton-cover pulse" />
      <div className="diary-skeleton-lines">
        <div className="pulse line w60" />
        <div className="pulse line w90" />
        <div className="pulse line w75" />
        <div className="pulse line w85" />
      </div>
    </div>
  )
}

/** Discogs 快照 = 聆乐日记主体 */
function DiaryBody({
  post,
  onOpenPerson,
}: {
  post: ListeningDiaryPost
  onOpenPerson?: (name: string, kind: PersonKind) => void
}) {
  const snap = post.snapshot
  const composers = snap?.composers || []
  const performers = snap?.performers || []
  const ensembles = snap?.ensembles || []
  const tracks = snap?.tracklist || []
  const kindLabel = sourceKindLabel(post.source_kind)
  const open = onOpenPerson || (() => undefined)

  return (
    <div className="diary-body">
      <div className="diary-body-hero">
        {post.cover_image_url ? (
          <img className="diary-cover" src={post.cover_image_url} alt={`${post.title || '唱片'} 封面`} loading="lazy" />
        ) : (
          <div className="diary-cover diary-cover-empty" aria-hidden />
        )}
        <div className="diary-body-lead">
          <p className="diary-kind">{kindLabel}</p>
          <h2>{post.title || '未命名唱片'}</h2>
          <dl className="diary-facts">
            {composers.length ? (
              <div>
                <dt>作曲</dt>
                <dd>
                  <PersonNameLinks names={composers} kind="composer" onOpen={open} />
                </dd>
              </div>
            ) : null}
            {performers.length ? (
              <div>
                <dt>演奏</dt>
                <dd>
                  <PersonNameLinks names={performers} kind="performer" onOpen={open} />
                </dd>
              </div>
            ) : null}
            {ensembles.length ? (
              <div>
                <dt>乐团</dt>
                <dd>
                  <PersonNameLinks names={ensembles} kind="ensemble" onOpen={open} />
                </dd>
              </div>
            ) : null}
            {snap?.year ? (
              <div>
                <dt>年份</dt>
                <dd>{snap.year}</dd>
              </div>
            ) : null}
            {snap?.label ? (
              <div>
                <dt>厂牌</dt>
                <dd>{snap.label}</dd>
              </div>
            ) : null}
            {snap?.catno ? (
              <div>
                <dt>编号</dt>
                <dd>{snap.catno}</dd>
              </div>
            ) : null}
            {post.listened_on ? (
              <div>
                <dt>聆乐日</dt>
                <dd>{post.listened_on}</dd>
              </div>
            ) : null}
          </dl>
          {snap?.uri ? (
            <p className="diary-source-link">
              <a href={snap.uri} target="_blank" rel="noreferrer">
                在 Discogs 打开原页
              </a>
            </p>
          ) : null}
        </div>
      </div>

      {tracks.length > 0 ? (
        <section className="diary-section" aria-labelledby="diary-tracklist-title">
          <h3 id="diary-tracklist-title">曲目列表</h3>
          <ol className="diary-tracklist">
            {tracks.map((t, i) => (
              <li key={`${t.position}-${t.title}-${i}`}>
                <span className="diary-track-pos">{t.position || String(i + 1)}</span>
                <span className="diary-track-title">{t.title}</span>
                {t.duration ? <span className="diary-track-dur">{t.duration}</span> : null}
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      {post.listening_note ? (
        <section className="diary-section" aria-labelledby="diary-note-title">
          <h3 id="diary-note-title">今日听感</h3>
          <p className="diary-note">{post.listening_note}</p>
        </section>
      ) : null}
    </div>
  )
}

export function MyListeningDiary({
  user,
  onNotice,
  onError,
}: {
  user: User
  onNotice: (msg: string) => void
  onError: (msg: string) => void
}) {
  const searchId = useId()
  const detailRef = useRef<HTMLElement | null>(null)
  const [posts, setPosts] = useState<ListeningDiaryPost[]>([])
  const [selected, setSelected] = useState<ListeningDiaryPost | null>(null)
  const [busy, setBusy] = useState(false)
  const [phase, setPhase] = useState<'idle' | 'search' | 'pulling' | 'draft'>('idle')
  const [query, setQuery] = useState('')
  const [pendingTitle, setPendingTitle] = useState('')
  const [note, setNote] = useState('')
  const [guideTasks, setGuideTasks] = useState<DiaryGuideLink[]>([])
  const [readyCount, setReadyCount] = useState(0)
  const [queuedCount, setQueuedCount] = useState(0)
  const [reviewLink, setReviewLink] = useState<DiaryGuideLink | null>(null)
  const [reviewNotes, setReviewNotes] = useState('')
  const [filterDate, setFilterDate] = useState<string | null>(null)
  const [filterTag, setFilterTag] = useState<DiaryTag | null>(null)
  const [calCursor, setCalCursor] = useState(() => {
    const t = new Date()
    return { year: t.getFullYear(), monthIndex: t.getMonth() }
  })
  const [asideOpen, setAsideOpen] = useState(true)
  const [guideSteps, setGuideSteps] = useState<WorkflowStep[]>([])
  const [guideProgress, setGuideProgress] = useState<ChainProgress | null>(null)
  const [watchingGuideId, setWatchingGuideId] = useState<number | null>(null)
  const [guideWatchBusy, setGuideWatchBusy] = useState(false)
  const { openPerson, panelProps } = usePersonCard()

  const dateCounts = countsByDate(posts)
  const tagCloud = buildDiaryTagCloud(posts)
  const tagScale = tagWeightScale(tagCloud)
  const monthCells = buildMonthGrid(calCursor.year, calCursor.monthIndex, dateCounts)
  const filteredPosts = filterDiaryPosts(posts, { date: filterDate, tag: filterTag }) as ListeningDiaryPost[]
  const monthTitle = `${calCursor.year}年${calCursor.monthIndex + 1}月`
  const hasFilters = Boolean(filterDate || filterTag)

  async function refreshTasks() {
    const res = await listDiaryGuideTasks()
    setGuideTasks(res.items)
    setReadyCount(res.ready_for_review_count)
    setQueuedCount(res.queued_count)
  }

  async function refresh() {
    const rows = await listListeningDiary()
    setPosts(rows)
    await refreshTasks()
  }

  useEffect(() => {
    void refresh().catch((e) => onError(errorMessage(e, '无法加载聆乐日记')))
  }, [user.id])

  useEffect(() => {
    const handle = window.setInterval(() => {
      void refreshTasks().catch(() => undefined)
    }, 8000)
    return () => window.clearInterval(handle)
  }, [user.id])

  useEffect(() => {
    if ((phase === 'draft' || phase === 'pulling') && detailRef.current) {
      detailRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [phase, selected?.id])

  function startCompose() {
    setPhase('search')
    setSelected(null)
    setQuery('')
    setNote('')
    setPendingTitle('')
    onError('')
  }

  function cancelCompose() {
    setPhase(selected ? 'draft' : 'idle')
    setQuery('')
    setPendingTitle('')
  }

  async function onPick(hit: DiscogsSearchHit) {
    setBusy(true)
    setPhase('pulling')
    setPendingTitle(hit.title)
    onError('')
    try {
      const created = await createListeningDiary({
        provider: 'discogs',
        external_id: String(hit.id),
        listening_note: note.trim() || undefined,
      })
      const full = await fetchListeningDiary(created.id)
      setSelected(full)
      setNote(full.listening_note || '')
      setPhase('draft')
      setQuery('')
      await refresh()
      onNotice('唱片信息已写入聆乐日记主体')
    } catch (e) {
      setPhase('search')
      onError(errorMessage(e, '拉取唱片失败：请确认已登录，且 Discogs 可用'))
    } finally {
      setBusy(false)
      setPendingTitle('')
    }
  }

  async function openPost(id: number) {
    setBusy(true)
    onError('')
    try {
      const full = await fetchListeningDiary(id)
      setSelected(full)
      setNote(full.listening_note || '')
      setPhase('draft')
      setQuery('')
      const ready = (full.guides || []).find((g) => g.status === 'ready_for_review')
      if (ready) openReviewLink(ready)
      else {
        setReviewLink(null)
        setReviewNotes('')
      }
      const activeGuide =
        (full.guides || []).find((g) => g.status === 'queued' || g.status === 'failed') ||
        (full.guides || [])[0]
      const steps = activeGuide?.guide?.steps || []
      setGuideSteps(steps)
      setGuideProgress(null)
      setWatchingGuideId(activeGuide?.guide_id || null)
      if (activeGuide?.guide_id && (activeGuide.status === 'queued' || activeGuide.guide?.status === 'queued' || activeGuide.guide?.status === 'running')) {
        void watchDiaryGuide(activeGuide.guide_id)
      }
    } catch (e) {
      onError(errorMessage(e, '无法打开聆乐日记'))
    } finally {
      setBusy(false)
    }
  }

  async function watchDiaryGuide(guideId: number) {
    setWatchingGuideId(guideId)
    setGuideWatchBusy(true)
    setGuideSteps([])
    setGuideProgress(null)
    try {
      await streamGuideEvents(guideId, {
        onStep: (step) => {
          setGuideSteps((prev) => {
            const next = upsertWorkflowStep(prev, step)
            setGuideProgress(chainProgressFromSteps(next, step.total))
            return next
          })
        },
        onProgress: (p) => {
          if (p.steps?.length) {
            const steps = sortWorkflowSteps(p.steps)
            setGuideSteps(steps)
            const derived = chainProgressFromSteps(steps, p.total)
            setGuideProgress({
              done: p.done ?? derived.done,
              total: p.total || derived.total,
              completed: p.completed ?? derived.completed,
              skipped: p.skipped ?? derived.skipped,
              failed: p.failed ?? derived.failed,
            })
          } else if (typeof p.done === 'number' && typeof p.total === 'number') {
            setGuideProgress({
              done: p.done,
              total: p.total,
              completed: p.completed,
              skipped: p.skipped,
              failed: p.failed,
            })
          }
        },
        onDone: async () => {
          setGuideWatchBusy(false)
          onNotice('聆乐导赏已生成，请审阅后发布')
          await refreshTasks()
          if (selected) {
            const full = await fetchListeningDiary(selected.id)
            setSelected(full)
            const ready = (full.guides || []).find((g) => g.status === 'ready_for_review')
            if (ready) openReviewLink(ready)
            const g = (full.guides || []).find((x) => x.guide_id === guideId)?.guide
            if (g?.steps?.length) setGuideSteps(g.steps)
          }
        },
        onError: async (detail) => {
          setGuideWatchBusy(false)
          onError(detail || '导赏生成失败')
          await refreshTasks()
          if (selected) {
            const full = await fetchListeningDiary(selected.id)
            setSelected(full)
            const g = (full.guides || []).find((x) => x.guide_id === guideId)?.guide
            if (g?.steps?.length) setGuideSteps(g.steps)
          }
        },
      })
    } catch (e) {
      setGuideWatchBusy(false)
      onError(errorMessage(e, '无法跟踪导赏生成进度'))
    }
  }

  async function onGenerateGuide() {
    if (!selected) return
    setBusy(true)
    onError('')
    try {
      const link = await enqueueDiaryGuide(selected.id, '作品导赏')
      onNotice('聆乐导赏已推入生成队列 — 下方可看工坊进度')
      await refreshTasks()
      const full = await fetchListeningDiary(selected.id)
      setSelected(full)
      if (link.guide?.steps?.length) setGuideSteps(link.guide.steps)
      if (link.guide_id) {
        void watchDiaryGuide(link.guide_id)
      }
      if (link.status === 'ready_for_review') openReviewLink(link)
    } catch (e) {
      onError(errorMessage(e, '无法排队生成聆乐导赏'))
    } finally {
      setBusy(false)
    }
  }

  async function onRetryDiaryGuide(guideId: number) {
    setBusy(true)
    onError('')
    try {
      const row = await retryListeningJob(guideId)
      onNotice('已重新排队生成聆乐导赏')
      if (row.steps?.length) setGuideSteps(row.steps)
      void watchDiaryGuide(guideId)
      await refreshTasks()
    } catch (e) {
      onError(errorMessage(e, '无法重试导赏生成'))
    } finally {
      setBusy(false)
    }
  }

  async function onPublishGuideLink(linkId: number) {
    setBusy(true)
    try {
      const link = await publishDiaryGuideLink(linkId)
      onNotice('导赏已发布，将显示在聆乐博客中')
      setReviewLink(link)
      setReviewNotes(link.review_notes || '')
      await refresh()
      if (selected) {
        const full = await fetchListeningDiary(selected.id)
        setSelected(full)
      }
    } catch (e) {
      onError(errorMessage(e, '发布导赏失败'))
    } finally {
      setBusy(false)
    }
  }

  async function onUnpublishGuideLink(linkId: number) {
    setBusy(true)
    try {
      const link = await unpublishDiaryGuideLink(linkId)
      setReviewLink(link)
      setReviewNotes(link.review_notes || reviewNotes)
      onNotice('已撤回导赏发布 — 可继续审阅或按意见重生')
      await refresh()
      if (selected) {
        const full = await fetchListeningDiary(selected.id)
        setSelected(full)
      }
    } catch (e) {
      onError(errorMessage(e, '撤回发布失败'))
    } finally {
      setBusy(false)
    }
  }

  async function onReviseGuideLink(linkId: number) {
    const notes = reviewNotes.trim()
    if (!notes) {
      onError('请先填写审阅意见，再重新生成')
      return
    }
    setBusy(true)
    onError('')
    try {
      const link = await reviseDiaryGuideLink(linkId, notes)
      setReviewLink(link)
      setReviewNotes(link.review_notes || notes)
      onNotice('已按意见重新排队生成导赏')
      await refreshTasks()
      if (selected) {
        const full = await fetchListeningDiary(selected.id)
        setSelected(full)
      }
      if (link.guide_id) {
        void watchDiaryGuide(link.guide_id)
      }
    } catch (e) {
      onError(errorMessage(e, '按意见重新生成失败'))
    } finally {
      setBusy(false)
    }
  }

  async function onDismissGuideLink(linkId: number) {
    setBusy(true)
    try {
      await dismissDiaryGuideLink(linkId)
      setReviewLink(null)
      setReviewNotes('')
      await refreshTasks()
      if (selected) {
        const full = await fetchListeningDiary(selected.id)
        setSelected(full)
      }
      onNotice('已废除这条导赏（不再出现在待审阅）')
    } catch (e) {
      onError(errorMessage(e, '废除失败'))
    } finally {
      setBusy(false)
    }
  }

  async function onDeleteGuideLink(linkId: number) {
    if (!window.confirm('确定删除这条日记导赏关联？未发布的独占导赏正文也会一并删除。')) {
      return
    }
    setBusy(true)
    try {
      const link = reviewLink
      if (link?.status === 'published') {
        await unpublishDiaryGuideLink(linkId)
      }
      await deleteDiaryGuideLink(linkId)
      setReviewLink(null)
      setReviewNotes('')
      setGuideSteps([])
      await refreshTasks()
      if (selected) {
        const full = await fetchListeningDiary(selected.id)
        setSelected(full)
      }
      onNotice('导赏关联已删除')
    } catch (e) {
      onError(errorMessage(e, '删除导赏失败'))
    } finally {
      setBusy(false)
    }
  }

  async function onAckGuideLink(linkId: number) {
    try {
      await ackDiaryGuideLink(linkId)
      await refreshTasks()
    } catch {
      /* best-effort */
    }
  }

  function openReviewLink(link: DiaryGuideLink) {
    setReviewLink(link)
    setReviewNotes(link.review_notes || '')
  }

  async function onSaveNote() {
    if (!selected) return
    setBusy(true)
    try {
      const updated = await patchListeningDiary(selected.id, { listening_note: note.trim() })
      setSelected(updated)
      await refresh()
      onNotice('听感已保存')
    } catch (e) {
      onError(errorMessage(e, '保存听感失败'))
    } finally {
      setBusy(false)
    }
  }

  async function onPublish() {
    if (!selected) return
    setBusy(true)
    try {
      if (note.trim() !== (selected.listening_note || '')) {
        await patchListeningDiary(selected.id, { listening_note: note.trim() })
      }
      const updated = await publishListeningDiary(selected.id)
      setSelected(updated)
      await refresh()
      onNotice('已发布到聆乐广场')
    } catch (e) {
      onError(errorMessage(e, '发布失败'))
    } finally {
      setBusy(false)
    }
  }

  async function onUnpublish() {
    if (!selected) return
    setBusy(true)
    try {
      const updated = await unpublishListeningDiary(selected.id)
      setSelected(updated)
      await refresh()
      onNotice('已撤回公开')
    } catch (e) {
      onError(errorMessage(e, '撤回失败'))
    } finally {
      setBusy(false)
    }
  }

  async function onDelete() {
    if (!selected) return
    if (!window.confirm('确定删除这篇聆乐日记？此操作不可撤销。')) return
    setBusy(true)
    try {
      await deleteListeningDiary(selected.id)
      setSelected(null)
      setNote('')
      setPhase('idle')
      await refresh()
      onNotice('已删除')
    } catch (e) {
      onError(errorMessage(e, '删除失败'))
    } finally {
      setBusy(false)
    }
  }

  const step = phase === 'search' ? 1 : phase === 'pulling' || phase === 'draft' ? 2 : 0
  const browsing = phase === 'idle' && !selected

  function clearFilters() {
    setFilterDate(null)
    setFilterTag(null)
  }

  function toggleDate(date: string) {
    setFilterDate((prev) => (prev === date ? null : date))
  }

  function toggleTag(tag: DiaryTag) {
    setFilterTag((prev) => (prev?.id === tag.id ? null : tag))
  }

  const aside = (
    <aside className={`diary-blog-aside ${asideOpen ? 'is-open' : ''}`} aria-label="日历与标签">
      <section className="diary-cal" aria-labelledby="diary-cal-title">
        <div className="diary-cal-head">
          <h2 id="diary-cal-title">聆乐日历</h2>
          <div className="diary-cal-nav">
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              aria-label="上个月"
              onClick={() => setCalCursor((c) => shiftMonth(c.year, c.monthIndex, -1))}
            >
              ‹
            </button>
            <button
              type="button"
              className="btn btn-ghost btn-sm diary-cal-month"
              onClick={() => {
                const t = new Date()
                setCalCursor({ year: t.getFullYear(), monthIndex: t.getMonth() })
                setFilterDate(todayIsoLocal())
              }}
            >
              {monthTitle}
            </button>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              aria-label="下个月"
              onClick={() => setCalCursor((c) => shiftMonth(c.year, c.monthIndex, 1))}
            >
              ›
            </button>
          </div>
        </div>
        <div className="diary-cal-weekdays" aria-hidden>
          {['日', '一', '二', '三', '四', '五', '六'].map((w) => (
            <span key={w}>{w}</span>
          ))}
        </div>
        <div className="diary-cal-grid" role="grid" aria-label={monthTitle}>
          {monthCells.map((cell, i) =>
            cell.date ? (
              <button
                key={cell.date}
                type="button"
                role="gridcell"
                className={`diary-cal-day ${cell.count ? 'has-posts' : ''} ${filterDate === cell.date ? 'is-selected' : ''} ${cell.date === todayIsoLocal() ? 'is-today' : ''}`}
                aria-pressed={filterDate === cell.date}
                aria-label={`${cell.date}${cell.count ? `，${cell.count} 篇` : ''}`}
                onClick={() => toggleDate(cell.date!)}
              >
                <span>{cell.day}</span>
                {cell.count > 0 ? <i className="diary-cal-dot" aria-hidden /> : null}
              </button>
            ) : (
              <span key={`pad-${i}`} className="diary-cal-day is-pad" aria-hidden />
            ),
          )}
        </div>
        {filterDate ? (
          <p className="diary-cal-hint">
            已选 {filterDate}
            <button type="button" className="linkish" onClick={() => setFilterDate(null)}>
              清除日期
            </button>
          </p>
        ) : (
          <p className="diary-cal-hint">点击有标记的日期，查看当天聆乐。</p>
        )}
      </section>

      <section className="diary-tags" aria-labelledby="diary-tags-title">
        <div className="diary-tags-head">
          <h2 id="diary-tags-title">Tag 云</h2>
          {filterTag ? (
            <button type="button" className="linkish" onClick={() => setFilterTag(null)}>
              清除标签
            </button>
          ) : null}
        </div>
        {tagCloud.length ? (
          <div className="diary-tag-cloud">
            {tagCloud.map((tag) => (
              <button
                key={tag.id}
                type="button"
                className={`diary-tag ${filterTag?.id === tag.id ? 'is-active' : ''} kind-${tag.kind}`}
                style={{ fontSize: `${tagFontRem(tag.count, tagScale.min, tagScale.max)}rem` }}
                aria-pressed={filterTag?.id === tag.id}
                title={`${tagKindLabel(tag.kind)} · ${tag.count}`}
                onClick={() => toggleTag(tag)}
              >
                {tag.label}
                <span className="diary-tag-count">{tag.count}</span>
              </button>
            ))}
          </div>
        ) : (
          <p className="diary-cal-hint">写下几篇日记后，这里会按作曲家、演奏家与类型聚合成云。</p>
        )}
        <ul className="diary-tag-legend" aria-label="标签类别">
          {(['composer', 'performer', 'ensemble', 'genre', 'style', 'format'] as const).map((k) => (
            <li key={k} className={`kind-${k}`}>
              {tagKindLabel(k)}
            </li>
          ))}
        </ul>
      </section>
    </aside>
  )

  return (
    <section className={`diary-shell diary-blog ${browsing ? 'is-browsing' : 'is-focused'}`} aria-label="我的聆乐日记">
      <header className="diary-head plaza-masthead">
        <div className="plaza-masthead-copy">
          <p className="eyebrow">聆乐</p>
          <h1>我的聆乐日记</h1>
          <p className="section-sub">像写博客一样记录每一次聆听：选碟、写听感、按日历与标签回看。</p>
        </div>
        <div className="diary-head-actions">
          {browsing ? (
            <button type="button" className="btn btn-ghost diary-aside-toggle" onClick={() => setAsideOpen((v) => !v)}>
              {asideOpen ? '收起侧栏' : '日历 · Tag'}
            </button>
          ) : null}
          {phase === 'search' || phase === 'pulling' ? (
            <button type="button" className="btn btn-ghost" disabled={busy && phase === 'pulling'} onClick={cancelCompose}>
              取消选碟
            </button>
          ) : (
            <button type="button" className="btn btn-primary" disabled={busy} onClick={startCompose}>
              新建聆乐
            </button>
          )}
        </div>
      </header>

      {(readyCount > 0 || queuedCount > 0) && (
        <div className="diary-guide-banner" role="status">
          {readyCount > 0 ? (
            <p>
              有 <strong>{readyCount}</strong> 篇聆乐导赏已生成，待你审阅后发布到博客。
            </p>
          ) : (
            <p>
              导赏队列中有 <strong>{queuedCount}</strong> 个任务正在生成…
            </p>
          )}
          <ul className="diary-guide-task-list">
            {guideTasks
              .filter((t) => t.status === 'ready_for_review' || t.status === 'queued')
              .slice(0, 6)
              .map((t) => (
                <li key={t.id}>
                  <button
                    type="button"
                    className="person-name-link"
                    onClick={() => {
                      void openPost(t.diary_post_id)
                      if (t.status === 'ready_for_review') {
                        openReviewLink(t)
                        void onAckGuideLink(t.id)
                      }
                    }}
                  >
                    {t.diary_title || `日记 #${t.diary_post_id}`}
                  </button>
                  <span className="diary-guide-status">
                    {t.status === 'ready_for_review' ? '待审阅' : '生成中'}
                    {t.aspect ? ` · ${t.aspect}` : ''}
                  </span>
                </li>
              ))}
          </ul>
        </div>
      )}

      {(phase === 'search' || phase === 'pulling' || phase === 'draft') && (
        <ol className="diary-steps" aria-label="聆乐步骤">
          <li className={step >= 1 ? 'is-on' : ''}>
            <span className="diary-step-num">1</span>
            <span>选碟</span>
          </li>
          <li className={step >= 2 ? 'is-on' : ''}>
            <span className="diary-step-num">2</span>
            <span>日记主体</span>
          </li>
          <li className={selected?.status === 'published' ? 'is-on' : ''}>
            <span className="diary-step-num">3</span>
            <span>发布</span>
          </li>
        </ol>
      )}

      {phase === 'search' && (
        <DiscogsReleasePicker
          variant="diary"
          query={query}
          onQueryChange={setQuery}
          onPick={(hit) => void onPick(hit)}
          disabled={busy}
          inputId={searchId}
          autoFocus
          placeholder="艺术家、作品、厂牌、唱片编号…"
          labels={{
            searchLabel: '搜索 Discogs',
            tooShort: '至少输入两个字符',
            searching: '正在搜索…',
            empty: '没有匹配结果。试试厂牌编号或作曲家英文名。',
            pickCta: '选用并拉取',
            errorFallback: 'Discogs 搜索失败',
          }}
        />
      )}

      <div className={`diary-blog-layout ${browsing ? '' : 'is-reading'}`}>
        <div className="diary-blog-main">
          {browsing ? (
            <>
              <div className="diary-blog-toolbar">
                <h2 className="diary-list-title">
                  {hasFilters
                    ? `筛选结果 · ${filteredPosts.length}`
                    : `全部日记 · ${posts.length}`}
                </h2>
                {hasFilters ? (
                  <button type="button" className="btn btn-ghost btn-sm" onClick={clearFilters}>
                    清除筛选
                    {filterDate ? ` · ${filterDate}` : ''}
                    {filterTag ? ` · ${filterTag.label}` : ''}
                  </button>
                ) : null}
              </div>
              {filteredPosts.length ? (
                <div className="diary-blog-feed" role="feed">
                  {filteredPosts.map((p, index) => {
                    const day = postListeningDate(p)
                    return (
                      <ListeningPostCard
                        key={p.id}
                        post={p}
                        titleAs="h3"
                        className="diary-blog-card"
                        posinset={index + 1}
                        disabled={busy}
                        onOpen={() => void openPost(p.id)}
                        byline={
                          <>
                            <span className={`diary-status-pill ${p.status === 'published' ? 'is-pub' : 'is-draft'}`}>
                              {p.status === 'published' ? '已发布' : '草稿'}
                            </span>
                            {day ? <time dateTime={day}>{day}</time> : null}
                          </>
                        }
                        meta={
                          <>
                            {(p.snapshot?.composers || []).slice(0, 2).map((c) => (
                              <span key={c}>{c}</span>
                            ))}
                            {(p.snapshot?.genres || []).slice(0, 1).map((g) => (
                              <span key={g}>{g}</span>
                            ))}
                          </>
                        }
                      />
                    )
                  })}
                </div>
              ) : (
                <div className="plaza-empty">
                  <p className="diary-empty-lead">{posts.length ? '没有匹配的日记' : '还没有聆乐日记'}</p>
                  <p>
                    {posts.length
                      ? '试试清除日期或标签筛选，或换一个月看看。'
                      : '点「新建聆乐」，从 Discogs 选一张唱片开始。'}
                  </p>
                </div>
              )}
            </>
          ) : null}

          {phase === 'pulling' && (
            <article className="diary-detail plaza-reader is-loading" ref={detailRef} aria-busy="true" aria-live="polite">
              <button type="button" className="diary-back plaza-reader-back" onClick={cancelCompose}>
                ← 返回日记
              </button>
              <p className="diary-detail-kicker">正在从 Discogs 拉取「{pendingTitle || '唱片'}」…</p>
              <DiarySkeleton />
              <p className="diary-status is-pulling">写入聆乐日记主体中，请稍候</p>
            </article>
          )}

          {phase !== 'pulling' && selected && (
            <article className="diary-detail plaza-reader" ref={detailRef}>
              <button
                type="button"
                className="diary-back plaza-reader-back"
                onClick={() => {
                  setSelected(null)
                  setReviewLink(null)
                  setPhase('idle')
                }}
              >
                ← 返回日记
              </button>
              <p className="diary-detail-kicker">
                {selected.status === 'published' ? '已发布' : '草稿'}
                {postListeningDate(selected) ? ` · 聆乐日 ${postListeningDate(selected)}` : ''}
                {' · '}
                主体来自 Discogs
              </p>
              <DiaryBody post={selected} onOpenPerson={openPerson} />

              <section className="diary-section" aria-labelledby="diary-edit-note">
                <h3 id="diary-edit-note">今日听感（可选）</h3>
                <textarea
                  rows={3}
                  maxLength={500}
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="写一两句今天听这张碟的感受…"
                  disabled={busy}
                />
                <button type="button" className="btn btn-ghost btn-sm" disabled={busy} onClick={() => void onSaveNote()}>
                  保存听感
                </button>
              </section>

              <section className="diary-section diary-atelier" aria-labelledby="diary-guide-block">
                <h3 id="diary-guide-block">聆乐导赏工坊</h3>
                <p className="section-sub">基于本篇唱片信息排队生成导赏；过程与「导赏」工作室同源，可逐步看见研究链。</p>
                <div className="diary-actions">
                  <button type="button" className="btn btn-primary" disabled={busy || guideWatchBusy} onClick={() => void onGenerateGuide()}>
                    {guideWatchBusy ? '工坊生成中…' : busy ? '处理中…' : '生成聆乐导赏'}
                  </button>
                </div>

                {(guideWatchBusy || guideSteps.length > 0) && (
                  <div className="diary-atelier-panel">
                    <AtelierTrail
                      steps={guideSteps}
                      progress={guideProgress}
                      busy={guideWatchBusy}
                      progressLabel="进度"
                      liveLabel="生成中"
                      openingLabel="工坊正在打开研究链…"
                      emptyLabel={null}
                      showEmpty={false}
                      listClassName="diary-atelier-steps"
                    />
                    {(() => {
                      const card =
                        reviewLink?.guide?.process_scorecard ||
                        (selected.guides || []).find((g) => g.guide?.process_scorecard)?.guide
                          ?.process_scorecard
                      return card ? <ProcessScorecardCard scorecard={card} /> : null
                    })()}
                    <GenerationRoundsPanel
                      rounds={reviewLink?.guide?.generation_rounds || null}
                      workTitle={reviewLink?.guide?.work_title || '聆乐导赏'}
                    />
                  </div>
                )}

                {(selected.guides || []).length > 0 ? (
                  <ul className="diary-guide-task-list">
                    {(selected.guides || []).map((g) => (
                      <li key={g.id}>
                        <span>
                          {g.aspect || '导赏'} ·{' '}
                          {g.status === 'published'
                            ? '已发布'
                            : g.status === 'ready_for_review'
                              ? '待审阅'
                              : g.status === 'queued'
                                ? '队列中'
                                : g.status === 'failed'
                                  ? '失败'
                                  : g.status}
                          {g.guide?.error_detail ? ` — ${g.guide.error_detail}` : ''}
                        </span>
                        <div className="diary-guide-row-actions">
                          {(g.status === 'ready_for_review' ||
                            g.status === 'published' ||
                            g.status === 'failed' ||
                            g.status === 'dismissed') && (
                            <button
                              type="button"
                              className="btn btn-ghost btn-sm"
                              onClick={() => openReviewLink(g)}
                            >
                              {g.status === 'ready_for_review'
                                ? '打开审阅'
                                : g.status === 'published'
                                  ? '管理导赏'
                                  : g.status === 'failed'
                                    ? '打开处理'
                                    : '查看'}
                            </button>
                          )}
                          {g.status === 'failed' && g.guide_id ? (
                            <button
                              type="button"
                              className="btn btn-primary btn-sm"
                              disabled={busy || guideWatchBusy}
                              onClick={() => {
                                if (g.guide?.steps?.length) setGuideSteps(g.guide.steps)
                                void onRetryDiaryGuide(g.guide_id!)
                              }}
                            >
                              重试生成
                            </button>
                          ) : null}
                          {g.status === 'queued' && g.guide_id ? (
                            <button
                              type="button"
                              className="btn btn-ghost btn-sm"
                              disabled={guideWatchBusy && watchingGuideId === g.guide_id}
                              onClick={() => {
                                if (g.guide?.steps?.length) setGuideSteps(g.guide.steps)
                                void watchDiaryGuide(g.guide_id!)
                              }}
                            >
                              查看进度
                            </button>
                          ) : null}
                          {g.status === 'published' && g.guide?.share_path ? (
                            <a href={g.guide.share_path} target="_blank" rel="noreferrer">
                              查看导赏
                            </a>
                          ) : null}
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : null}
                {reviewLink && reviewLink.diary_post_id === selected.id ? (
                  <div className="diary-guide-review guide-pane">
                    <div className="section-head">
                      <div>
                        <h4 id="diary-guide-review-title">
                          {reviewLink.guide?.work_title || '聆乐导赏'}
                        </h4>
                        <p className="section-sub">
                          状态：
                          {reviewLink.status === 'ready_for_review'
                            ? '待审阅'
                            : reviewLink.status === 'published'
                              ? '已发布'
                              : reviewLink.status === 'queued'
                                ? '生成中'
                                : reviewLink.status === 'failed'
                                  ? '失败'
                                  : reviewLink.status === 'dismissed'
                                    ? '已废除'
                                    : reviewLink.status}
                          {reviewLink.aspect ? ` · ${reviewLink.aspect}` : ''}
                        </p>
                        {reviewLink.guide?.summary ? (
                          <p className="section-sub">{reviewLink.guide.summary}</p>
                        ) : null}
                      </div>
                    </div>
                    <div className="diary-guide-review-workspace">
                      <div className="diary-guide-review-main">
                        {reviewLink.guide?.guide_html ? (
                          <GuideReader
                            html={reviewLink.guide.guide_html}
                            title={reviewLink.guide.work_title || '聆乐导赏'}
                          />
                        ) : reviewLink.status === 'queued' ? (
                          <p className="diary-empty">导赏正在生成，完成后可在此审阅。</p>
                        ) : (
                          <p className="diary-empty">正文尚未就绪，请稍候刷新。</p>
                        )}
                      </div>
                      <aside className="diary-guide-review-rail" aria-label="审阅操作">
                        {(reviewLink.actions?.can_revise ||
                          reviewLink.status === 'ready_for_review' ||
                          reviewLink.status === 'published' ||
                          reviewLink.status === 'failed') && (
                          <label className="diary-review-notes">
                            <span>审阅意见</span>
                            <textarea
                              rows={5}
                              value={reviewNotes}
                              placeholder="希望加强什么、纠正什么？提交后将带意见重新生成。"
                              onChange={(e) => setReviewNotes(e.target.value)}
                              disabled={busy || reviewLink.status === 'queued'}
                            />
                          </label>
                        )}

                        <div className="diary-actions diary-guide-lifecycle">
                          {reviewLink.actions?.can_publish ? (
                            <button
                              type="button"
                              className="btn btn-primary"
                              disabled={busy}
                              onClick={() => void onPublishGuideLink(reviewLink.id)}
                            >
                              审阅通过并发布
                            </button>
                          ) : null}
                          {reviewLink.actions?.can_unpublish ? (
                            <button
                              type="button"
                              className="btn btn-ghost"
                              disabled={busy}
                              onClick={() => void onUnpublishGuideLink(reviewLink.id)}
                            >
                              撤回发布
                            </button>
                          ) : null}
                          {reviewLink.actions?.can_revise ? (
                            <button
                              type="button"
                              className="btn btn-primary"
                              disabled={busy || !reviewNotes.trim()}
                              onClick={() => void onReviseGuideLink(reviewLink.id)}
                            >
                              按意见重新生成
                            </button>
                          ) : null}
                          {reviewLink.actions?.can_dismiss ? (
                            <button
                              type="button"
                              className="btn btn-ghost"
                              disabled={busy}
                              title="不再出现在待审阅，可稍后删除"
                              onClick={() => void onDismissGuideLink(reviewLink.id)}
                            >
                              废除
                            </button>
                          ) : null}
                          {(reviewLink.actions?.can_delete || reviewLink.status === 'published') && (
                            <button
                              type="button"
                              className="btn btn-ghost"
                              disabled={busy}
                              onClick={() => void onDeleteGuideLink(reviewLink.id)}
                            >
                              删除
                            </button>
                          )}
                          <button
                            type="button"
                            className="btn btn-ghost"
                            disabled={busy}
                            onClick={() => {
                              setReviewLink(null)
                              setReviewNotes('')
                            }}
                          >
                            收起
                          </button>
                        </div>
                      </aside>
                    </div>
                  </div>
                ) : null}
              </section>

              <div className="diary-actions diary-actions-sticky">
                {selected.status !== 'published' ? (
                  <button type="button" className="btn btn-primary" disabled={busy} onClick={() => void onPublish()}>
                    {busy ? '处理中…' : '发布到聆乐广场'}
                  </button>
                ) : (
                  <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => void onUnpublish()}>
                    撤回发布
                  </button>
                )}
                <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => void onDelete()}>
                  删除
                </button>
                <button type="button" className="btn btn-ghost" disabled={busy} onClick={startCompose}>
                  再写一篇
                </button>
              </div>
            </article>
          )}
        </div>

        {browsing || phase === 'search' ? aside : null}
      </div>
      <PersonEntityPanel {...panelProps} />
    </section>
  )
}

export function ListeningPlaza({
  user,
  onNotice,
  onError,
}: {
  user: User
  onNotice: (msg: string) => void
  onError: (msg: string) => void
}) {
  const plazaDetailRef = useRef<HTMLElement | null>(null)
  const [tab, setTab] = useState<'plaza' | 'following'>('plaza')
  const [items, setItems] = useState<ListeningDiaryPost[]>([])
  const [active, setActive] = useState<ListeningDiaryPost | null>(null)
  const [loading, setLoading] = useState(true)
  const [comments, setComments] = useState<Array<{ id: number; body: string; author: { display_name: string } }>>([])
  const [commentBody, setCommentBody] = useState('')
  const [busy, setBusy] = useState(false)
  const { openPerson, panelProps } = usePersonCard()

  async function loadFeed() {
    setLoading(true)
    try {
      const res = tab === 'following' ? await fetchPlazaHome() : await fetchPlazaFeed()
      setItems(res.items)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setActive(null)
    setComments([])
    setCommentBody('')
    void loadFeed().catch((e) => onError(errorMessage(e, '无法加载聆乐广场')))
  }, [tab, user.id])

  useEffect(() => {
    if (active && plazaDetailRef.current) {
      plazaDetailRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }, [active?.id])

  async function openItem(post: ListeningDiaryPost) {
    setBusy(true)
    onError('')
    try {
      let full = post
      if (post.share_slug) {
        full = await fetchPlazaPost(post.share_slug)
      }
      setActive(full)
      const res = await listPlazaComments(post.id)
      setComments(res.items)
    } catch (e) {
      setActive(post)
      setComments([])
      onError(errorMessage(e, '无法打开这条聆乐'))
    } finally {
      setBusy(false)
    }
  }

  async function onLike() {
    if (!active) return
    setBusy(true)
    try {
      const updated = await likePlazaPost(active.id)
      setActive({ ...active, ...updated, snapshot: active.snapshot })
      setItems((prev) => prev.map((p) => (p.id === updated.id ? { ...p, like_count: updated.like_count } : p)))
    } catch (e) {
      onError(errorMessage(e, '点赞失败'))
    } finally {
      setBusy(false)
    }
  }

  async function onUnlike() {
    if (!active) return
    setBusy(true)
    try {
      const updated = await unlikePlazaPost(active.id)
      setActive({ ...active, ...updated, snapshot: active.snapshot })
      setItems((prev) => prev.map((p) => (p.id === updated.id ? { ...p, like_count: updated.like_count } : p)))
    } catch (e) {
      onError(errorMessage(e, '取消点赞失败'))
    } finally {
      setBusy(false)
    }
  }

  async function onFollow() {
    if (!active?.author?.id || active.author.id === user.id) return
    setBusy(true)
    try {
      await followUser(active.author.id)
      onNotice(`已关注 ${active.author.display_name}`)
    } catch (e) {
      onError(errorMessage(e, '关注失败'))
    } finally {
      setBusy(false)
    }
  }

  async function onComment(event: FormEvent) {
    event.preventDefault()
    if (!active || !commentBody.trim()) return
    setBusy(true)
    try {
      await addPlazaComment(active.id, commentBody.trim())
      setCommentBody('')
      const res = await listPlazaComments(active.id)
      setComments(res.items)
      setActive({ ...active, comment_count: res.items.length })
      setItems((prev) => prev.map((p) => (p.id === active.id ? { ...p, comment_count: res.items.length } : p)))
    } catch (e) {
      onError(errorMessage(e, '评论失败'))
    } finally {
      setBusy(false)
    }
  }

  const publishedGuides = (active?.guides || []).filter((g) => g.status === 'published')

  return (
    <section className={`diary-shell plaza-shell ${active ? 'is-reading' : 'is-browsing'}`} aria-label="聆乐广场">
      {!active ? (
        <>
          <header className="plaza-masthead">
            <div className="plaza-masthead-copy">
              <p className="eyebrow">聆乐广场</p>
              <h1>爱乐者的公共聆听场</h1>
              <p className="section-sub">浏览他人的唱片日记，留下你的听感回应。</p>
            </div>
            <div className="plaza-tabs" role="tablist" aria-label="广场视图">
              <button
                type="button"
                role="tab"
                aria-selected={tab === 'plaza'}
                className={tab === 'plaza' ? 'active' : ''}
                onClick={() => setTab('plaza')}
              >
                发现
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={tab === 'following'}
                className={tab === 'following' ? 'active' : ''}
                onClick={() => setTab('following')}
              >
                关注
              </button>
            </div>
          </header>

          {loading ? (
            <div className="plaza-feed" aria-busy="true" aria-label="加载中">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="plaza-card plaza-card-skeleton pulse" aria-hidden>
                  <div className="plaza-card-cover" />
                  <div className="plaza-card-body">
                    <span className="line w40" />
                    <span className="line w85" />
                    <span className="line w60" />
                  </div>
                </div>
              ))}
            </div>
          ) : items.length ? (
            <div className="plaza-feed" role="feed" aria-label={tab === 'following' ? '关注动态' : '发现动态'}>
              {items.map((p, index) => {
                const guideCount = (p.guides || []).filter((g) => g.status === 'published').length
                return (
                  <ListeningPostCard
                    key={p.id}
                    post={p}
                    posinset={index + 1}
                    setsize={items.length}
                    disabled={busy}
                    onOpen={() => void openItem(p)}
                    byline={
                      <>
                        <span className="plaza-avatar" aria-hidden>
                          {(p.author?.display_name || '聆').slice(0, 1)}
                        </span>
                        <span className="plaza-card-author">{p.author?.display_name || '聆乐者'}</span>
                        {p.published_at ? (
                          <time dateTime={p.published_at}>{formatDateTime(p.published_at)}</time>
                        ) : null}
                      </>
                    }
                    meta={
                      <>
                        <span>赞 {p.like_count}</span>
                        <span>评 {p.comment_count}</span>
                        {guideCount > 0 ? <span className="plaza-card-badge">导赏 {guideCount}</span> : null}
                      </>
                    }
                  />
                )
              })}
            </div>
          ) : (
            <div className="plaza-empty">
              <p className="diary-empty-lead">{tab === 'following' ? '关注流还是空的' : '广场静悄悄'}</p>
              <p>
                {tab === 'following'
                  ? '关注几位爱乐者后，他们的新日记会出现在这里。'
                  : '去「我的聆乐」发布第一篇，成为广场的开场。'}
              </p>
            </div>
          )}
        </>
      ) : (
        <article className="plaza-reader" ref={plazaDetailRef}>
          <header className="plaza-reader-bar">
            <button type="button" className="diary-back plaza-reader-back" onClick={() => setActive(null)}>
              ← 返回广场
            </button>
            <div className="plaza-reader-byline">
              <span className="plaza-avatar plaza-avatar-lg" aria-hidden>
                {(active.author?.display_name || '聆').slice(0, 1)}
              </span>
              <div>
                <p className="plaza-reader-author">{active.author?.display_name || '聆乐者'}</p>
                <p className="plaza-reader-when">
                  {active.published_at ? formatDateTime(active.published_at) : '聆乐日记'}
                  {active.listened_on ? ` · 聆乐日 ${active.listened_on}` : ''}
                </p>
              </div>
              {active.author && active.author.id !== user.id ? (
                <button type="button" className="btn btn-ghost btn-sm plaza-follow" disabled={busy} onClick={() => void onFollow()}>
                  关注
                </button>
              ) : null}
            </div>
          </header>

          <DiaryBody post={active} onOpenPerson={openPerson} />

          {publishedGuides.length > 0 ? (
            <section className="plaza-guides" aria-labelledby="plaza-guides">
              <h3 id="plaza-guides">聆乐导赏</h3>
              <ul className="plaza-guide-list">
                {publishedGuides.map((g) => (
                  <li key={g.id}>
                    <div>
                      <strong>{g.guide?.work_title || g.aspect || '导赏'}</strong>
                      {g.guide?.summary ? <p>{g.guide.summary}</p> : null}
                    </div>
                    {g.guide?.share_path ? (
                      <a className="btn btn-ghost btn-sm" href={g.guide.share_path} target="_blank" rel="noreferrer">
                        阅读导赏
                      </a>
                    ) : null}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <div className="plaza-engage diary-actions-sticky" role="group" aria-label="互动">
            <button type="button" className="btn btn-primary" disabled={busy} onClick={() => void onLike()}>
              赞 · {active.like_count}
            </button>
            <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => void onUnlike()}>
              取消赞
            </button>
            <span className="plaza-engage-meta">评论 {active.comment_count}</span>
          </div>

          <section className="plaza-thread" aria-labelledby="plaza-thread-title">
            <h3 id="plaza-thread-title">听感回应</h3>
            <form className="plaza-comment-form" onSubmit={onComment}>
              <label htmlFor="plaza-comment" className="sr-only">
                写一条评论
              </label>
              <div className="plaza-comment-row">
                <input
                  id="plaza-comment"
                  value={commentBody}
                  onChange={(e) => setCommentBody(e.target.value)}
                  placeholder="写一句听感回应…"
                  maxLength={1000}
                  enterKeyHint="send"
                  autoComplete="off"
                  disabled={busy}
                />
                <button type="submit" className="btn btn-primary" disabled={busy || !commentBody.trim()}>
                  发送
                </button>
              </div>
            </form>
            <ul className="plaza-comments">
              {comments.map((c) => (
                <li key={c.id}>
                  <span className="plaza-avatar plaza-avatar-sm" aria-hidden>
                    {(c.author.display_name || '听').slice(0, 1)}
                  </span>
                  <div>
                    <strong>{c.author.display_name}</strong>
                    <p>{c.body}</p>
                  </div>
                </li>
              ))}
              {!comments.length && <li className="plaza-comments-empty">还没有评论。写下你的第一句回应吧。</li>}
            </ul>
          </section>
        </article>
      )}
      <PersonEntityPanel {...panelProps} />
    </section>
  )
}
