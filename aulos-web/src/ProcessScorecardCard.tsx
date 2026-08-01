import type { ProcessScorecard } from './api'

type Props = {
  scorecard?: ProcessScorecard | null
  className?: string
}

function bandClass(band?: string) {
  if (band === 'strong') return 'psc-band-strong'
  if (band === 'solid') return 'psc-band-solid'
  if (band === 'developing') return 'psc-band-developing'
  if (band === 'weak') return 'psc-band-weak'
  return 'psc-band-unknown'
}

function shortTrigger(trigger: string) {
  return trigger.replace(/^listening\./, '')
}

/**
 * Compact process scorecard for Studio Atelier + diary 导赏工坊 (SPEC-019).
 */
export function ProcessScorecardCard({ scorecard, className = '' }: Props) {
  if (!scorecard?.rollup) return null
  const { rollup, nodes = [], gates, product } = scorecard
  const hard = Boolean(rollup.hard_fail || gates?.review_failed)

  return (
    <aside className={`process-scorecard ${className}`.trim()} aria-label="导赏过程积分卡">
      <div className="psc-head">
        <div>
          <p className="psc-kicker">Process scorecard</p>
          <p className="psc-title">
            <span className={`psc-pct ${bandClass(rollup.band)}`}>{rollup.pct ?? '—'}%</span>
            <span className={`psc-band ${bandClass(rollup.band)}`}>{rollup.band || 'unknown'}</span>
          </p>
        </div>
        <div className="psc-gates" aria-label="Gates">
          {gates?.ambient_ok === false ? <span className="psc-chip fail">no ambient</span> : null}
          {gates?.review_failed ? <span className="psc-chip fail">本意偏离已拦截</span> : null}
          {hard ? <span className="psc-chip fail">hard fail</span> : null}
          {gates?.eval_pass ? <span className="psc-chip ok">eval pass</span> : <span className="psc-chip mute">eval soft</span>}
          {typeof rollup.hard_flaws_remaining === 'number' ? (
            <span className={`psc-chip ${rollup.hard_flaws_remaining > 0 ? 'fail' : 'ok'}`}>
              硬伤 {rollup.hard_flaws_remaining}
            </span>
          ) : null}
        </div>
      </div>

      {nodes.length ? (
        <ul className="psc-nodes">
          {nodes.map((node) => (
            <li key={node.trigger}>
              <span className="psc-node-id">{shortTrigger(node.trigger)}</span>
              <span className="psc-node-bar" aria-hidden>
                <span style={{ width: `${Math.min(100, Number(node.pct) || 0)}%` }} />
              </span>
              <span className={`psc-node-pct ${bandClass(node.band)}`}>{node.pct ?? 0}%</span>
            </li>
          ))}
        </ul>
      ) : null}

      {product?.scores ? (
        <p className="psc-product mute">
          Product · specificity {product.scores.specificity ?? '—'} · ear {product.scores.ear_cues ?? '—'} ·
          structure {product.scores.structure ?? '—'} · bilingual {product.scores.bilingual ?? '—'} · ambient{' '}
          {product.scores.ambient ?? '—'}
        </p>
      ) : null}
    </aside>
  )
}
