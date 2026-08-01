import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  enqueueKnowledgeDiscoveryCrawl,
  exploreKnowledgeSources,
  fetchKnowledgeDiscoveryRuns,
  fetchKnowledgeExploreSeeds,
  knowledgeMediaContentUrl,
  prepareKnowledgeExploreSeeds,
  registerKnowledgeDiscoveryCandidates,
  type KnowledgeDiscoveryCandidate,
  type KnowledgeDiscoveryCrawlJob,
  type KnowledgeDiscoveryRun,
  type KnowledgeExploreSeed,
} from '../../api'
import { DiscoveryGraph } from '../components/DiscoveryGraph'
import { fallbackExploreSeeds } from '../constants'

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
}

function ComposerAvatar({ seed, size = 48 }: { seed: KnowledgeExploreSeed; size?: number }) {
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
        onError={(e) => {
          const el = e.currentTarget
          el.style.display = 'none'
          const fallback = el.nextElementSibling as HTMLElement | null
          if (fallback) fallback.hidden = false
        }}
      />
    )
  }
  return (
    <span className="kb-composer-avatar fallback" style={{ width: size, height: size }} aria-hidden>
      {initial}
    </span>
  )
}

export function ExploreModule({ busy, setBusy, setError, setNotice }: Props) {
  const [seeds, setSeeds] = useState<KnowledgeExploreSeed[]>([])
  const [featured, setFeatured] = useState<KnowledgeExploreSeed[]>([])
  const [letters, setLetters] = useState<string[]>([])
  const [letter, setLetter] = useState('All')
  const [query, setQuery] = useState('')
  const [selected, setSelectedComposer] = useState<KnowledgeExploreSeed | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [maxDepth, setMaxDepth] = useState(2)
  const [enqueueCrawl, setEnqueueCrawl] = useState(true)

  const [runs, setRuns] = useState<KnowledgeDiscoveryRun[]>([])
  const [active, setActive] = useState<KnowledgeDiscoveryRun | null>(null)
  const [candSelected, setCandSelected] = useState<Set<string>>(new Set())
  const [focusNodeId, setFocusNodeId] = useState<string | null>(null)

  const loadSeeds = useCallback(async () => {
    try {
      const data = await fetchKnowledgeExploreSeeds()
      setSeeds(data.seeds)
      setFeatured(data.featured)
      setLetters(data.letters)
      return data
    } catch (err) {
      const fb = fallbackExploreSeeds()
      setSeeds(fb.seeds)
      setFeatured(fb.featured)
      setLetters(fb.letters)
      setNotice('种子目录暂时用本地精选列表（服务稍后可刷新）')
      console.warn('explore seeds fallback', err)
      return fb
    }
  }, [setNotice])

  const loadRuns = useCallback(async () => {
    const rows = await fetchKnowledgeDiscoveryRuns()
    setRuns(rows)
    return rows
  }, [])

  useEffect(() => {
    void loadSeeds()
      .then((data) => {
        setSelectedComposer((prev) => prev ?? data.featured[0] ?? data.seeds[0] ?? null)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'failed to load composers')
      })
    void loadRuns()
      .then((rows) => {
        setActive((prev) => prev ?? rows[0] ?? null)
      })
      .catch(() => {
        /* optional */
      })
  }, [loadSeeds, loadRuns, setError])

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

  const onExplore = async () => {
    if (!selected) {
      setError('先从列表里选一位音乐家')
      return
    }
    if (!selected.wikidata_qid) {
      setError(`${selected.name_en} 还没有 Wikidata 种子，请先准备种子或换一位著名音乐家`)
      return
    }
    setBusy(true)
    setError(null)
    try {
      const run = await exploreKnowledgeSources({
        wikidata_qid: selected.wikidata_qid,
        composer_id: selected.id,
        wikipedia_title: selected.wikipedia_title || undefined,
        max_depth: maxDepth,
        max_breadth: 24,
        enqueue_crawl: enqueueCrawl,
      })
      setActive(run)
      setCandSelected(new Set(run.candidates.map((c) => c.id)))
      const jobs = (run.crawl_jobs || []) as KnowledgeDiscoveryCrawlJob[]
      const started = jobs.filter((j) => j.job_id).length
      setNotice(
        `已从 ${selected.short_name} 展开探索 #${run.id} · ${run.candidates.length} 个候选源` +
          (enqueueCrawl ? ` · ${started} 个爬虫任务` : ''),
      )
      await loadRuns()
      await loadSeeds()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'explore failed')
    } finally {
      setBusy(false)
    }
  }

  const onPrepareSeeds = async () => {
    setBusy(true)
    setError(null)
    try {
      const result = await prepareKnowledgeExploreSeeds({ limit: 8, featured_only: true })
      if (!result.ok) {
        setError(result.error || 'prepare seeds failed')
        return
      }
      const done = result.jobs.filter((j) => j.status === 'succeeded').length
      setNotice(
        `已为 ${result.composers ?? 8} 位著名音乐家准备种子（${result.enqueued} 任务` +
          (done ? `，${done} 已完成` : '') +
          '）— 列表会刷新肖像',
      )
      await loadSeeds()
      await loadRuns()
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'prepare seeds failed'
      setError(
        /not found/i.test(msg)
          ? '准备种子接口未部署（404）。请重启 aulos-knowledge / aulos-ops 后再试。'
          : msg,
      )
    } finally {
      setBusy(false)
    }
  }

  const onRegister = async () => {
    if (!active) return
    setBusy(true)
    setError(null)
    try {
      const ids = [...candSelected]
      const result = await registerKnowledgeDiscoveryCandidates(active.id, {
        candidate_ids: ids.length ? ids : undefined,
        min_score: 10,
      })
      setNotice(`已注册 ${result.created.length} 个候选源 — 请到 Source registry 审核`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'register failed')
    } finally {
      setBusy(false)
    }
  }

  const onEnqueueCrawl = async () => {
    if (!active) return
    setBusy(true)
    setError(null)
    try {
      const result = await enqueueKnowledgeDiscoveryCrawl(active.id)
      const started = result.crawl_jobs.filter((j) => j.job_id).length
      setActive({ ...active, crawl_jobs: result.crawl_jobs, seed_hints: result.seed_hints })
      setNotice(`已为种子 enqueue ${started} 个权威爬虫任务`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'enqueue crawl failed')
    } finally {
      setBusy(false)
    }
  }

  const candidates = active?.candidates ?? []
  const crawlJobs = (active?.crawl_jobs || []) as KnowledgeDiscoveryCrawlJob[]
  const graphNodes = (active?.graph?.nodes || []).map((n) => ({
    id: String(n.id || ''),
    kind: String(n.kind || ''),
    label: String(n.label || n.id || ''),
    url: String(n.url || ''),
    score: typeof n.score === 'number' ? n.score : undefined,
    depth: typeof n.depth === 'number' ? n.depth : undefined,
  }))
  const graphEdges = (active?.graph?.edges || []).map((e) => ({
    src: String(e.src || ''),
    dst: String(e.dst || ''),
    relation: String(e.relation || ''),
  }))

  return (
    <div className="kb-module kb-explore">
      <header className="kb-module-head">
        <div>
          <h3>探索权威信息源</h3>
          <p className="mute">
            从音乐家出发，而不是从技术 ID。选一位作曲家 → 一键展开深度+广度图搜索 → 发现并注册更多权威源。
          </p>
        </div>
        <button type="button" className="ghost" disabled={busy} onClick={() => void onPrepareSeeds()}>
          准备肖像种子
        </button>
      </header>

      <section className="kb-explore-featured" aria-label="著名音乐家">
        <div className="kb-explore-featured-head">
          <h4>著名音乐家</h4>
          <span className="mute">种子网络起点</span>
        </div>
        <div className="kb-featured-strip">
          {featured.map((s) => (
            <button
              key={s.id}
              type="button"
              className={selected?.id === s.id ? 'kb-featured-card active' : 'kb-featured-card'}
              disabled={busy}
              onClick={() => setSelectedComposer(s)}
            >
              <ComposerAvatar seed={s} size={56} />
              <span className="kb-featured-name">{s.short_name}</span>
              <span className="kb-badge famous">Famous</span>
            </button>
          ))}
        </div>
      </section>

      <section className="kb-explore-picker">
        <div className="kb-explore-picker-tools">
          <label className="kb-explore-search">
            <span className="sr-only">按名字搜索</span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="按名字搜索音乐家…"
              disabled={busy}
            />
          </label>
          <div className="kb-letter-rail" role="tablist" aria-label="A 到 Z">
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

        <div className="kb-explore-picker-body">
          <ul className="kb-composer-list" aria-label="音乐家列表">
            {filtered.length === 0 ? (
              <li className="mute kb-empty">没有匹配的音乐家。试试 All，或点「准备肖像种子」。</li>
            ) : (
              filtered.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    className={selected?.id === s.id ? 'kb-composer-row active' : 'kb-composer-row'}
                    onClick={() => setSelectedComposer(s)}
                    disabled={busy}
                  >
                    <ComposerAvatar seed={s} size={40} />
                    <span className="kb-composer-meta">
                      <strong>{s.name_en}</strong>
                      <span className="mute">
                        {s.name_zh ? `${s.name_zh} · ` : ''}
                        {s.era || s.lifespan || '—'}
                      </span>
                    </span>
                    <span className="kb-composer-tags">
                      {s.famous ? <span className="kb-badge famous">Famous</span> : null}
                      {s.featured ? <span className="kb-badge featured">Featured</span> : null}
                      {s.portrait ? <span className="kb-badge portrait">Portrait</span> : null}
                    </span>
                  </button>
                </li>
              ))
            )}
          </ul>

          <aside className="kb-explore-selected" aria-live="polite">
            {selected ? (
              <>
                <div className="kb-selected-hero">
                  <ComposerAvatar seed={selected} size={72} />
                  <div>
                    <h4>{selected.name_en}</h4>
                    <p className="mute">
                      {selected.name_zh || selected.era || 'Classical seed'}
                      {selected.lifespan ? ` · ${selected.lifespan}` : ''}
                    </p>
                    <div className="kb-composer-tags">
                      {selected.famous ? <span className="kb-badge famous">Famous</span> : null}
                      {selected.in_corpus ? <span className="kb-badge">In corpus</span> : null}
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  className="primary kb-explore-cta"
                  disabled={busy || !selected.wikidata_qid}
                  onClick={() => void onExplore()}
                >
                  从这位音乐家开始探索
                </button>
                <p className="mute kb-explore-hint">
                  系统会自动带上权威链接与爬虫参数，你无需填写 Wikidata ID。
                </p>
                <details
                  className="kb-explore-advanced"
                  open={showAdvanced}
                  onToggle={(e) => setShowAdvanced((e.target as HTMLDetailsElement).open)}
                >
                  <summary>高级选项</summary>
                  <label>
                    Max depth
                    <input
                      type="number"
                      min={1}
                      max={4}
                      value={maxDepth}
                      onChange={(e) => setMaxDepth(Number(e.target.value))}
                      disabled={busy}
                    />
                  </label>
                  <label className="kb-explore-check">
                    <input
                      type="checkbox"
                      checked={enqueueCrawl}
                      onChange={(e) => setEnqueueCrawl(e.target.checked)}
                      disabled={busy}
                    />
                    探索后自动爬取权威源
                  </label>
                  <p className="mute truncate">
                    QID {selected.wikidata_qid || '—'} · {selected.id}
                  </p>
                </details>
              </>
            ) : (
              <p className="mute">从左侧或上方著名音乐家中选一位，作为探索起点。</p>
            )}
          </aside>
        </div>
      </section>

      {active && (
        <section className="kb-explore-results">
          <div className="kb-explore-stats">
            <span>探索 #{active.id}</span>
            <span>{Number(active.stats?.node_count ?? 0)} 节点</span>
            <span>{candidates.length} 候选源</span>
            <span>{crawlJobs.filter((j) => j.job_id).length} 爬虫任务</span>
          </div>

          <div className="kb-explore-graph-panel">
            <header>
              <h4>发现图</h4>
              <button type="button" className="secondary" disabled={busy} onClick={() => void onEnqueueCrawl()}>
                再次 enqueue 爬虫
              </button>
            </header>
            <DiscoveryGraph
              nodes={graphNodes}
              edges={graphEdges}
              selectedId={focusNodeId}
              onSelect={(n) => setFocusNodeId(n.id)}
            />
          </div>

          {crawlJobs.length > 0 && (
            <ul className="kb-list compact kb-explore-jobs">
              {crawlJobs.map((j, i) => (
                <li key={`${j.source_id}-${j.job_id ?? i}`}>
                  <code>{j.source_id}</code> → {j.status}
                  {j.job_id != null ? ` #${j.job_id}` : ''}
                </li>
              ))}
            </ul>
          )}

          <div className="kb-explore-candidates">
            <header>
              <h4>候选权威源</h4>
              <button
                type="button"
                className="secondary"
                disabled={busy || !candidates.length}
                onClick={() => void onRegister()}
              >
                注册所选
              </button>
            </header>
            <table className="kb-table">
              <thead>
                <tr>
                  <th />
                  <th>名称</th>
                  <th>分数</th>
                  <th>层级</th>
                  <th>URL</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((c: KnowledgeDiscoveryCandidate) => (
                  <tr key={c.id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={candSelected.has(c.id)}
                        onChange={() => {
                          setCandSelected((prev) => {
                            const next = new Set(prev)
                            if (next.has(c.id)) next.delete(c.id)
                            else next.add(c.id)
                            return next
                          })
                        }}
                      />
                    </td>
                    <td>
                      {c.name} <code className="mute">{c.id}</code>
                    </td>
                    <td>{c.score}</td>
                    <td>{c.tier}</td>
                    <td className="truncate">
                      <a href={c.url} target="_blank" rel="noreferrer">
                        {c.url}
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {runs.length > 1 && (
        <section className="kb-explore-history">
          <h4>最近探索</h4>
          <ul className="kb-list compact">
            {runs.slice(0, 8).map((r) => (
              <li key={r.id}>
                <button type="button" className="linkish" onClick={() => setActive(r)}>
                  #{r.id} · {r.status} · {r.candidates?.length ?? 0} candidates
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
