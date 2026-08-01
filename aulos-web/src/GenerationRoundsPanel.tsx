import { useState } from 'react'
import type { ProcessScorecard } from './api'
import { ProcessScorecardCard } from './ProcessScorecardCard'
import { GuideReader } from './GuideReader'

export type RevisionHistoryEntry = {
  id?: string
  at?: string
  source?: string
  summary?: string
  targets?: string[]
  scope?: string
  score_before?: { pct?: number; hard_flaws?: number }
  score_after?: { pct?: number; hard_flaws?: number }
  diff_summary?: string[]
  intent_ids?: string[]
}

export type GenerationRounds = {
  schema?: string
  draft_v1?: {
    guide_html?: string
    summary?: string
    process_scorecard?: ProcessScorecard | null
    hard_flaws?: Array<{ severity?: string; code?: string; note?: string }>
  }
  review_report?: {
    schema?: string
    perspective?: string
    verdict?: string
    summary?: string
    findings?: Array<{
      severity?: string
      code?: string
      note?: string
      evidence?: string
      kind?: string
    }>
    required_corrections?: string[]
    sources_used?: Array<{ title?: string; url?: string }>
    layer?: string
    targets?: string[]
  }
  draft_v2?: {
    guide_html?: string
    summary?: string
    process_scorecard?: ProcessScorecard | null
    repair_log?: string[]
    hard_flaws?: Array<{ severity?: string; code?: string; note?: string }>
    hard_flaws_remaining?: Array<{ severity?: string; code?: string; note?: string }>
    patched_targets?: string[]
    scope?: string
  }
  comparison?: {
    v1_pct?: number
    v2_pct?: number
    delta_pct?: number
    v1_hard_flaws?: number
    v2_hard_flaws?: number
    delta_hard_flaws?: number
    winner?: string
    notes?: string[]
  }
  revision_history?: RevisionHistoryEntry[]
}

type Props = {
  rounds?: GenerationRounds | null
  workTitle?: string
}

type Pane = 'v1' | 'review' | 'v2'

function sourceLabel(source?: string) {
  if (source === 'human') return '人工审校'
  if (source === 'expert') return '专家 Review'
  if (source === 'mixed') return '专家+人工'
  return source || '—'
}

/**
 * SPEC-022Δ — draft v1 / review / v2 + revision history side log.
 */
export function GenerationRoundsPanel({ rounds, workTitle = 'Listening guide' }: Props) {
  const hasContent = Boolean(
    rounds?.draft_v1?.guide_html || rounds?.review_report || rounds?.draft_v2?.guide_html,
  )
  const [pane, setPane] = useState<Pane>('v2')
  const [historyOpen, setHistoryOpen] = useState(true)
  if (!hasContent || !rounds) {
    return null
  }
  const comparison = rounds.comparison
  const report = rounds.review_report
  const history = [...(rounds.revision_history || [])].reverse()
  const active: Pane =
    pane === 'v2' && !rounds.draft_v2?.guide_html
      ? rounds.review_report
        ? 'review'
        : 'v1'
      : pane

  return (
    <section className="generation-rounds" aria-label="双稿与审校刷新">
      <div className="section-head">
        <div>
          <h2>双稿与审校刷新</h2>
          <p className="section-sub">
            初稿 → 审校意见 → 定点修订（chamber 级）
            {comparison
              ? ` · 评分 ${comparison.v1_pct ?? '—'}% → ${comparison.v2_pct ?? '—'}% (Δ ${comparison.delta_pct ?? 0}) · 硬伤 ${comparison.v1_hard_flaws ?? '—'} → ${comparison.v2_hard_flaws ?? '—'}`
              : ''}
          </p>
        </div>
      </div>

      <div className="gen-round-layout">
        <div className="gen-round-main">
          <div className="gen-round-tabs" role="tablist" aria-label="Draft rounds">
            <button
              type="button"
              role="tab"
              className={active === 'v1' ? 'active' : ''}
              aria-selected={active === 'v1'}
              onClick={() => setPane('v1')}
            >
              初稿 v1
            </button>
            <button
              type="button"
              role="tab"
              className={active === 'review' ? 'active' : ''}
              aria-selected={active === 'review'}
              onClick={() => setPane('review')}
            >
              审校意见
            </button>
            <button
              type="button"
              role="tab"
              className={active === 'v2' ? 'active' : ''}
              aria-selected={active === 'v2'}
              onClick={() => setPane('v2')}
            >
              修订稿 v2
            </button>
          </div>

          {active === 'v1' ? (
            <div className="gen-round-pane">
              {rounds.draft_v1?.process_scorecard ? (
                <ProcessScorecardCard scorecard={rounds.draft_v1.process_scorecard} />
              ) : null}
              {rounds.draft_v1?.guide_html ? (
                <GuideReader html={rounds.draft_v1.guide_html} title={`${workTitle} · 初稿 v1`} />
              ) : (
                <p className="diary-empty">初稿尚未就绪。</p>
              )}
            </div>
          ) : null}

          {active === 'review' ? (
            <div className="gen-round-pane gen-review-report">
              <p className="gen-review-perspective">
                {report?.perspective === 'human_review_notes'
                  ? '人工审校意见'
                  : '专家视角：音乐导赏 · 音乐分析'}
                {report?.perspective ? <span className="muted"> · {report.perspective}</span> : null}
              </p>
              <p className="gen-review-verdict">
                <strong>{report?.verdict || '—'}</strong>
                {report?.layer ? <span className="muted"> · {report.layer}</span> : null}
              </p>
              <p>{report?.summary || '暂无报告摘要。'}</p>
              {report?.targets?.length ? (
                <p className="gen-targets">
                  定位 chambers：{report.targets.map((t) => (
                    <span key={t} className="gen-chip">
                      {t}
                    </span>
                  ))}
                </p>
              ) : null}
              {report?.required_corrections?.length ? (
                <div>
                  <h3>修复指令</h3>
                  <ul>
                    {report.required_corrections.map((c) => (
                      <li key={c}>{c}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {report?.findings?.length ? (
                <div>
                  <h3>Findings</h3>
                  <ul>
                    {report.findings.map((f, i) => (
                      <li key={`${f.code}-${i}`}>
                        <strong>{f.severity}</strong> · {f.code}: {f.note}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : null}

          {active === 'v2' ? (
            <div className="gen-round-pane">
              {rounds.draft_v2?.process_scorecard ? (
                <ProcessScorecardCard scorecard={rounds.draft_v2.process_scorecard} />
              ) : null}
              {rounds.draft_v2?.repair_log?.length ? (
                <p className="gen-repair-log">修缮动作：{rounds.draft_v2.repair_log.join(' · ')}</p>
              ) : null}
              {rounds.draft_v2?.patched_targets?.length ? (
                <p className="gen-targets">
                  定点：{rounds.draft_v2.patched_targets.map((t) => (
                    <span key={t} className="gen-chip">
                      {t}
                    </span>
                  ))}
                  {rounds.draft_v2.scope ? (
                    <span className="muted"> · scope={rounds.draft_v2.scope}</span>
                  ) : null}
                </p>
              ) : null}
              {rounds.draft_v2?.guide_html ? (
                <GuideReader html={rounds.draft_v2.guide_html} title={`${workTitle} · 修订稿 v2`} />
              ) : (
                <p className="diary-empty">修订稿尚未就绪。</p>
              )}
            </div>
          ) : null}
        </div>

        <aside className="gen-history" aria-label="审校迭代历史">
          <button
            type="button"
            className="gen-history-toggle"
            aria-expanded={historyOpen}
            onClick={() => setHistoryOpen((v) => !v)}
          >
            迭代历史 ({history.length})
          </button>
          {historyOpen ? (
            history.length ? (
              <ol className="gen-history-list">
                {history.map((h) => {
                  const before = h.score_before?.pct
                  const after = h.score_after?.pct
                  const delta =
                    before != null && after != null ? Math.round((after - before) * 10) / 10 : null
                  return (
                    <li key={h.id || `${h.at}-${h.summary}`} className="gen-history-item">
                      <div className="gen-history-meta">
                        <span>{sourceLabel(h.source)}</span>
                        <span className="muted">{h.scope || '—'}</span>
                      </div>
                      <p className="gen-history-summary">{h.summary || '—'}</p>
                      {h.targets?.length ? (
                        <p className="gen-targets">
                          {h.targets.map((t) => (
                            <span key={t} className="gen-chip">
                              {t}
                            </span>
                          ))}
                        </p>
                      ) : null}
                      <p className="gen-history-score">
                        {before ?? '—'}% → {after ?? '—'}%
                        {delta != null ? ` (Δ ${delta > 0 ? '+' : ''}${delta})` : ''}
                        {h.score_before?.hard_flaws != null || h.score_after?.hard_flaws != null
                          ? ` · 硬伤 ${h.score_before?.hard_flaws ?? '—'} → ${h.score_after?.hard_flaws ?? '—'}`
                          : ''}
                      </p>
                      {h.diff_summary?.length ? (
                        <ul className="gen-history-diff">
                          {h.diff_summary.slice(0, 6).map((d) => (
                            <li key={d}>{d}</li>
                          ))}
                        </ul>
                      ) : null}
                      {h.at ? <p className="muted gen-history-at">{h.at}</p> : null}
                    </li>
                  )
                })}
              </ol>
            ) : (
              <p className="diary-empty">尚无迭代记录。</p>
            )
          ) : null}
        </aside>
      </div>
    </section>
  )
}
