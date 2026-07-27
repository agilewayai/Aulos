import type { KnowledgeJob, KnowledgeSource } from '../api'

export function sourceCanCrawl(source: KnowledgeSource): boolean {
  return (
    (source.verification_status || '') === 'verified' &&
    Boolean(source.enabled) &&
    source.connector_registered !== false &&
    Boolean((source.connector || '').trim())
  )
}

export function verificationClass(status: string | undefined): string {
  const v = status || 'candidate'
  if (v === 'verified') return 'badge-verified'
  if (v === 'rejected' || v === 'suspended') return 'badge-rejected'
  return 'badge-candidate'
}

export function jobStatusClass(status: string): string {
  if (status === 'succeeded') return 'kb-job-succeeded'
  if (status === 'failed') return 'kb-job-failed'
  if (status === 'running') return 'kb-job-running'
  return 'kb-job-pending'
}

export function countJobsByStatus(jobs: KnowledgeJob[]): Record<string, number> {
  const out: Record<string, number> = {}
  for (const j of jobs) {
    out[j.status] = (out[j.status] || 0) + 1
  }
  return out
}

export function formatPct(part: number, total: number): string {
  if (!total) return '0%'
  return `${Math.round((part / total) * 100)}%`
}
