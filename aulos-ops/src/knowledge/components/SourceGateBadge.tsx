import type { KnowledgeSource } from '../../api'
import { sourceCanCrawl } from '../utils'

type Props = {
  source: KnowledgeSource
  compact?: boolean
}

export function SourceGateBadge({ source, compact = false }: Props) {
  const verified = (source.verification_status || '') === 'verified'
  const enabled = Boolean(source.enabled)
  const connectorOk = source.connector_registered !== false && Boolean((source.connector || '').trim())
  const crawlOk = sourceCanCrawl(source)

  if (compact) {
    return (
      <span className={`kb-gate-pill ${crawlOk ? 'kb-gate-pill-ok' : 'kb-gate-pill-blocked'}`}>
        {crawlOk ? 'crawl ready' : 'blocked'}
      </span>
    )
  }

  return (
    <div className="kb-gate" aria-label="Crawl gate status">
      <span className={verified ? 'kb-gate-step kb-gate-on' : 'kb-gate-step kb-gate-off'} title="Verified">
        verified
      </span>
      <span className={enabled ? 'kb-gate-step kb-gate-on' : 'kb-gate-step kb-gate-off'} title="Enabled">
        enabled
      </span>
      <span
        className={connectorOk ? 'kb-gate-step kb-gate-on' : 'kb-gate-step kb-gate-off'}
        title="Connector registered"
      >
        connector
      </span>
      <span className={crawlOk ? 'kb-gate-result kb-gate-ok' : 'kb-gate-result kb-gate-blocked'}>
        {crawlOk ? 'crawl OK' : 'blocked'}
      </span>
    </div>
  )
}
