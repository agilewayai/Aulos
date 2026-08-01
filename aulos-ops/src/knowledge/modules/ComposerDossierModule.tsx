import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  buildComposerDossierAndWait,
  fetchComposerDossier,
  fetchKnowledgeExploreSeeds,
  knowledgeMediaContentUrl,
  type ComposerDossier,
  type ComposerDossierWorkNode,
  type KnowledgeExploreSeed,
} from '../../api'
import { fallbackExploreSeeds } from '../constants'
import type { KnowledgeModuleId } from '../types'

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
  onNavigate: (module: KnowledgeModuleId) => void
}

function ComposerAvatar({ seed, size = 56 }: { seed: KnowledgeExploreSeed; size?: number }) {
  const src = seed.portrait?.content_path
    ? knowledgeMediaContentUrl(seed.portrait.content_path)
    : seed.portrait?.source_url || ''
  const initial = (seed.short_name || seed.name_en || '?').slice(0, 1).toUpperCase()
  if (src) {
    return (
      <img
        className="kb-composer-avatar"
        src={src}
        alt=""
        width={size}
        height={size}
        loading="lazy"
      />
    )
  }
  return (
    <span className="kb-composer-avatar fallback" style={{ width: size, height: size }} aria-hidden>
      {initial}
    </span>
  )
}

function WorkTreeNode({ node, depth = 0 }: { node: ComposerDossierWorkNode; depth?: number }) {
  const [open, setOpen] = useState(depth < 1)
  const hasKids = (node.children || []).length > 0
  const catalogs = (node.catalog_numbers || []).filter(Boolean).join(', ')
  const genre =
    node.genre ||
    (typeof node.facets?.genre === 'string' ? (node.facets.genre as string) : '') ||
    ''
  return (
    <li className={`kb-dossier-work depth-${Math.min(depth, 3)}`}>
      <div className="kb-dossier-work-row">
        {hasKids ? (
          <button type="button" className="ghost kb-dossier-toggle" onClick={() => setOpen((v) => !v)}>
            {open ? '▾' : '▸'}
          </button>
        ) : (
          <span className="kb-dossier-toggle spacer" aria-hidden>
            ·
          </span>
        )}
        <div className="kb-dossier-work-meta">
          <strong>{node.title_en}</strong>
          <span className="kb-composer-tags">
            <span className="kb-badge">{node.work_kind}</span>
            {node.year_start ? <span className="kb-badge">{node.year_start}</span> : null}
            {catalogs ? <span className="kb-badge">{catalogs}</span> : null}
            {genre ? <span className="kb-badge">{genre}</span> : null}
          </span>
        </div>
      </div>
      {hasKids && open ? (
        <ul className="kb-dossier-work-children">
          {node.children.map((c) => (
            <WorkTreeNode key={c.id} node={c} depth={depth + 1} />
          ))}
        </ul>
      ) : null}
    </li>
  )
}

function FlatWorkRow({ node }: { node: ComposerDossierWorkNode }) {
  const catalogs = (node.catalog_numbers || []).filter(Boolean).join(', ')
  const genre =
    node.genre ||
    (typeof node.facets?.genre === 'string' ? (node.facets.genre as string) : '') ||
    ''
  return (
    <li className="kb-dossier-work depth-0">
      <div className="kb-dossier-work-row">
        <span className="kb-dossier-toggle spacer" aria-hidden>
          ·
        </span>
        <div className="kb-dossier-work-meta">
          <strong>{node.title_en}</strong>
          <span className="kb-composer-tags">
            {node.year_start ? <span className="kb-badge">{node.year_start}</span> : null}
            {catalogs ? <span className="kb-badge">{catalogs}</span> : null}
            {genre ? <span className="kb-badge">{genre}</span> : null}
          </span>
        </div>
      </div>
    </li>
  )
}

export function ComposerDossierModule({ busy, setBusy, setError, setNotice, onNavigate }: Props) {
  const [seeds, setSeeds] = useState<KnowledgeExploreSeed[]>([])
  const [featured, setFeatured] = useState<KnowledgeExploreSeed[]>([])
  const [letters, setLetters] = useState<string[]>([])
  const [letter, setLetter] = useState('All')
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<KnowledgeExploreSeed | null>(null)
  const [dossier, setDossier] = useState<ComposerDossier | null>(null)
  const [worksView, setWorksView] = useState<'genre' | 'year' | 'tree'>('genre')

  const loadSeeds = useCallback(async () => {
    try {
      const data = await fetchKnowledgeExploreSeeds()
      setSeeds(data.seeds)
      setFeatured(data.featured)
      setLetters(data.letters)
      return data
    } catch {
      const fb = fallbackExploreSeeds()
      setSeeds(fb.seeds)
      setFeatured(fb.featured)
      setLetters(fb.letters)
      return fb
    }
  }, [])

  const loadDossier = useCallback(
    async (composerId: string) => {
      try {
        const data = await fetchComposerDossier(composerId)
        setDossier(data)
        return data
      } catch (err) {
        setDossier(null)
        throw err
      }
    },
    [],
  )

  useEffect(() => {
    void loadSeeds()
      .then((data) => {
        setSelected((prev) => prev ?? data.featured[0] ?? data.seeds[0] ?? null)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'failed to load composers'))
  }, [loadSeeds, setError])

  useEffect(() => {
    if (!selected) return
    void loadDossier(selected.id).catch(() => {
      setDossier(null)
    })
  }, [selected, loadDossier])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return seeds.filter((s) => {
      if (letter !== 'All' && s.letter !== letter) return false
      if (!q) return true
      return (
        s.name_en.toLowerCase().includes(q) ||
        s.short_name.toLowerCase().includes(q) ||
        (s.name_zh || '').includes(query.trim()) ||
        s.id.toLowerCase().includes(q)
      )
    })
  }, [seeds, letter, query])

  const onBuild = async () => {
    if (!selected) {
      setError('先从列表里选一位音乐家')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const result = await buildComposerDossierAndWait(selected.id, {
        qid: selected.wikidata_qid || undefined,
      })
      if (result.status === 'failed') {
        setError(`构建失败: ${result.error || 'job failed'}`)
      } else {
        setNotice(`履历构建完成 · job #${result.job_id} → ${result.status}`)
      }
      await loadDossier(selected.id)
      await loadSeeds()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'build dossier failed')
    } finally {
      setBusy(false)
    }
  }

  const portraitSrc =
    dossier?.portrait?.content_path
      ? knowledgeMediaContentUrl(dossier.portrait.content_path)
      : selected?.portrait?.content_path
        ? knowledgeMediaContentUrl(selected.portrait.content_path)
        : ''

  const c = dossier?.composer
  const displayName = c?.name_en || selected?.name_en || '—'
  const displayZh = c?.name_zh || selected?.name_zh || ''
  const lifespan = c?.lifespan || selected?.lifespan || ''
  const era = c?.era || selected?.era || ''

  return (
    <section className="kb-module kb-dossier" aria-labelledby="kb-dossier-title">
      <header className="kb-module-head">
        <div>
          <h3 id="kb-dossier-title">Composer dossier</h3>
          <p className="lede">人生年表与作品树 — 从音乐家出发，不需要先填 QID</p>
        </div>
      </header>

      {featured.length ? (
        <div className="kb-explore-featured">
          <div className="kb-explore-featured-head">
            <h4>Famous</h4>
            <span className="meta">{featured.length} 位精选</span>
          </div>
          <div className="kb-featured-strip" role="list">
            {featured.map((s) => (
              <button
                key={s.id}
                type="button"
                role="listitem"
                className={selected?.id === s.id ? 'kb-featured-card active' : 'kb-featured-card'}
                onClick={() => setSelected(s)}
              >
                <ComposerAvatar seed={s} size={44} />
                <span className="kb-featured-name">{s.short_name}</span>
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div className="kb-explore-picker-body kb-dossier-layout">
        <aside className="kb-dossier-picker">
          <div className="kb-explore-picker-tools">
            <div className="kb-explore-search">
              <input
                type="search"
                placeholder="搜索音乐家…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label="Search composers"
              />
            </div>
            <div className="kb-letter-rail" role="toolbar" aria-label="A–Z">
              <button
                type="button"
                className={letter === 'All' ? 'active' : ''}
                onClick={() => setLetter('All')}
              >
                All
              </button>
              {letters.map((L) => (
                <button
                  key={L}
                  type="button"
                  className={letter === L ? 'active' : ''}
                  onClick={() => setLetter(L)}
                >
                  {L}
                </button>
              ))}
            </div>
          </div>
          <ul className="kb-composer-list">
            {filtered.map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  className={selected?.id === s.id ? 'kb-composer-row active' : 'kb-composer-row'}
                  onClick={() => setSelected(s)}
                >
                  <ComposerAvatar seed={s} size={36} />
                  <span className="kb-composer-meta">
                    <strong>{s.name_en}</strong>
                    <span className="kb-composer-tags">
                      {s.famous ? <span className="kb-badge famous">Famous</span> : null}
                      {s.era ? <span className="kb-badge">{s.era}</span> : null}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <div className="kb-dossier-canvas">
          <header className="kb-dossier-hero">
            {portraitSrc ? (
              <img className="kb-dossier-portrait" src={portraitSrc} alt="" width={96} height={96} />
            ) : selected ? (
              <ComposerAvatar seed={selected} size={96} />
            ) : null}
            <div className="kb-dossier-hero-text">
              <h4>
                {displayName}
                {displayZh ? <span className="kb-dossier-zh"> {displayZh}</span> : null}
              </h4>
              <p className="kb-dossier-sub">
                {[lifespan, era].filter(Boolean).join(' · ') || '尚未构建履历'}
                {c?.famous || selected?.famous ? (
                  <>
                    {' '}
                    <span className="kb-badge famous">Famous</span>
                  </>
                ) : null}
              </p>
              {c?.summary_en ? <p className="kb-dossier-summary">{c.summary_en}</p> : null}
              <div className="kb-explore-cta">
                <button type="button" disabled={busy || !selected} onClick={() => void onBuild()}>
                  构建履历与作品
                </button>
                <button
                  type="button"
                  className="ghost"
                  disabled={!selected}
                  onClick={() => onNavigate('documents')}
                >
                  相关文档
                </button>
                <button
                  type="button"
                  className="ghost"
                  disabled={!selected}
                  onClick={() => onNavigate('jobs')}
                >
                  任务队列
                </button>
              </div>
              <p className="kb-explore-hint meta">
                {dossier
                  ? `${dossier.events_count} 件人生事件 · ${dossier.works_count} 部作品`
                  : '点击构建后从 Wikidata 拉取年表与作品树'}
              </p>
            </div>
          </header>

          <div className="kb-dossier-panels">
            <section className="kb-dossier-panel" aria-labelledby="kb-timeline-h">
              <h5 id="kb-timeline-h">人生年表</h5>
              {(dossier?.timeline || []).length === 0 ? (
                <p className="meta">暂无事件 — 先构建履历</p>
              ) : (
                <ol className="kb-dossier-timeline">
                  {dossier!.timeline.map((ev) => (
                    <li
                      key={ev.id}
                      className={
                        ev.significance === 'major' ? 'kb-dossier-event major' : 'kb-dossier-event'
                      }
                    >
                      <time>{ev.date_start || '—'}</time>
                      <div>
                        <strong>{ev.title_en}</strong>
                        <span className="kb-composer-tags">
                          <span className="kb-badge">{ev.event_type}</span>
                          {ev.place_label ? <span className="kb-badge">{ev.place_label}</span> : null}
                        </span>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </section>

            <section className="kb-dossier-panel" aria-labelledby="kb-works-h">
              <div className="kb-dossier-works-head">
                <h5 id="kb-works-h">作品目录</h5>
                <div className="kb-letter-rail" role="tablist" aria-label="作品视图">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={worksView === 'genre'}
                    className={worksView === 'genre' ? 'active' : ''}
                    onClick={() => setWorksView('genre')}
                  >
                    题材
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={worksView === 'year'}
                    className={worksView === 'year' ? 'active' : ''}
                    onClick={() => setWorksView('year')}
                  >
                    时间线
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={worksView === 'tree'}
                    className={worksView === 'tree' ? 'active' : ''}
                    onClick={() => setWorksView('tree')}
                  >
                    树
                  </button>
                </div>
              </div>
              {(dossier?.works_count || 0) === 0 ? (
                <p className="meta">暂无作品 — 构建后按题材 / 时间线浏览</p>
              ) : (
                <>
                  <p className="meta kb-explore-hint">
                    已收录 {dossier!.works_count} 部
                    {dossier!.works_cap ? `（软上限 ${dossier!.works_cap}，未必等于全集）` : ''}
                  </p>
                  {worksView === 'genre' ? (
                    <ul className="kb-dossier-work-tree">
                      {(dossier!.works_by_genre || []).map((g) => (
                        <li key={g.genre || 'g'} className="kb-dossier-work depth-0">
                          <div className="kb-dossier-work-row">
                            <span className="kb-dossier-toggle spacer" aria-hidden>
                              ·
                            </span>
                            <div className="kb-dossier-work-meta">
                              <strong>{g.genre || 'Unclassified'}</strong>
                              <span className="kb-composer-tags">
                                <span className="kb-badge">{g.count}</span>
                              </span>
                            </div>
                          </div>
                          <ul className="kb-dossier-work-children">
                            {(g.works || []).map((w) => (
                              <FlatWorkRow key={w.id} node={w} />
                            ))}
                          </ul>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  {worksView === 'year' ? (
                    <ul className="kb-dossier-work-tree">
                      {(dossier!.works_by_year || []).map((y) => (
                        <li key={y.year || 'y'} className="kb-dossier-work depth-0">
                          <div className="kb-dossier-work-row">
                            <span className="kb-dossier-toggle spacer" aria-hidden>
                              ·
                            </span>
                            <div className="kb-dossier-work-meta">
                              <strong>{y.year === 'undated' ? '年代未知' : y.year}</strong>
                              <span className="kb-composer-tags">
                                <span className="kb-badge">{y.count}</span>
                              </span>
                            </div>
                          </div>
                          <ul className="kb-dossier-work-children">
                            {(y.works || []).map((w) => (
                              <FlatWorkRow key={w.id} node={w} />
                            ))}
                          </ul>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  {worksView === 'tree' ? (
                    <ul className="kb-dossier-work-tree">
                      {dossier!.works_tree.map((n) => (
                        <WorkTreeNode key={n.id} node={n} />
                      ))}
                    </ul>
                  ) : null}
                </>
              )}
            </section>
          </div>
        </div>
      </div>
    </section>
  )
}
