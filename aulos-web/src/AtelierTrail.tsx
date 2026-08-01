import type { Ref } from 'react'
import type { WorkflowStep } from './api'
import type { ChainProgress } from './atelierTrailUtils'
import {
  atelierCompletedCount,
  atelierDoneCount,
  atelierProgressPercent,
  atelierSkippedCount,
  atelierTotalCount,
  stepStatusLabel,
} from './atelierTrailUtils'

export type AtelierTrailProps = {
  steps: WorkflowStep[]
  progress?: ChainProgress | null
  busy?: boolean
  /** Shown when busy and no steps yet */
  openingLabel?: string
  /** Shown when idle and no steps */
  emptyLabel?: string | null
  progressLabel?: string
  liveLabel?: string
  className?: string
  listClassName?: string
  trailRef?: Ref<HTMLDivElement>
  showEmpty?: boolean
}

/**
 * Shared research-chain trail for Studio Atelier and 我的聆乐导赏工坊.
 * One component — do not fork markup (META-001 §3.5 DRY).
 */
export function AtelierTrail({
  steps,
  progress = null,
  busy = false,
  openingLabel = 'Aulos is opening the research atelier…',
  emptyLabel = 'Your process appears here: Discogs → identity → knowledge → web → LLM → agent skills → persist.',
  progressLabel = '进度',
  liveLabel = '进行中',
  className = '',
  listClassName = '',
  trailRef,
  showEmpty = true,
}: AtelierTrailProps) {
  const finished = progress?.done ?? atelierDoneCount(steps)
  const completed = progress?.completed ?? atelierCompletedCount(steps)
  const skipped = progress?.skipped ?? atelierSkippedCount(steps)
  const total = atelierTotalCount(steps, progress)
  const pct = atelierProgressPercent(steps, progress)
  const showBar = Boolean(progress) || steps.length > 0

  return (
    <div className={`atelier-trail ${className}`.trim()}>
      {showBar ? (
        <div className="chain-progress" aria-live="polite">
          <div className="chain-progress-meta">
            <span className="chain-progress-counts">
              <span>
                {progressLabel}{' '}
                <strong>
                  {finished} / {total ?? '—'}
                </strong>
              </span>
              <span className="chain-progress-breakdown" aria-label="步骤分项">
                <span className="chain-stat chain-stat-done">完成 {completed}</span>
                <span className="chain-stat chain-stat-skip">跳过 {skipped}</span>
                {total != null ? <span className="chain-stat">共 {total}</span> : null}
              </span>
            </span>
            {busy ? <span className="chain-progress-live">{liveLabel}</span> : null}
          </div>
          <div
            className="chain-progress-bar"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={total ?? 1}
            aria-valuenow={finished}
            aria-label={`${progressLabel} ${finished}/${total ?? '—'}，跳过 ${skipped}`}
          >
            <span style={{ width: `${pct}%` }} />
          </div>
        </div>
      ) : null}

      <div className="trail" ref={trailRef}>
        {showEmpty && steps.length === 0 && !busy && emptyLabel ? <p className="empty">{emptyLabel}</p> : null}
        {busy && steps.length === 0 ? (
          <p className="thinking">
            <span className="thinking-dot" />
            {openingLabel}
          </p>
        ) : null}
        {steps.length > 0 ? (
          <ol className={`step-list ${listClassName}`.trim()}>
            {steps.map((step, index) => (
              <li
                key={step.id || `${step.title}-${index}`}
                className={`step status-${step.status}${step.countable === false ? ' step-uncounted' : ''}`}
                style={{ animationDelay: `${index * 0.04}s` }}
              >
                <div className="step-index">{step.index ?? index + 1}</div>
                <div>
                  <p className="step-title">
                    {step.title}
                    <span className={`step-status-label status-tag-${step.status}`}>
                      {stepStatusLabel(step.status)}
                    </span>
                  </p>
                  {step.skill_id ? (
                    <p className="step-skill">
                      {step.skill_id}
                      {step.skill_version ? `@${step.skill_version}` : ''}
                    </p>
                  ) : null}
                  {step.skill_id === 'listening.review' && step.status === 'failed' ? (
                    <p className="step-detail review-blocked">本意偏离已拦截</p>
                  ) : null}
                  {step.thinking ? <p className="step-thinking">{step.thinking}</p> : null}
                  {step.detail ? <p className="step-detail">{step.detail}</p> : null}
                </div>
              </li>
            ))}
          </ol>
        ) : null}
      </div>
    </div>
  )
}
