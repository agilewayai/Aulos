export const DIMENSION_ORDER = [
  'corpus',
  'registry',
  'provenance',
  'retrieval',
  'pipeline',
] as const

export function gradeClass(grade: string | null | undefined): string {
  if (!grade) return 'kb-bench-grade-bad'
  if (grade === 'A' || grade === 'B') return 'kb-bench-grade-ok'
  if (grade === 'C') return 'kb-bench-grade-warn'
  return 'kb-bench-grade-bad'
}

export function scoreBarClass(score: number): string {
  if (score >= 80) return 'kb-bench-bar-ok'
  if (score >= 60) return 'kb-bench-bar-warn'
  return 'kb-bench-bar-bad'
}

export function healthStatusClass(status: string): string {
  if (status === 'healthy') return 'kb-dash-health-ok'
  if (status === 'watch') return 'kb-dash-health-warn'
  if (status === 'critical') return 'kb-dash-health-bad'
  return 'kb-dash-health-none'
}

export function healthStatusLabel(status: string): string {
  if (status === 'healthy') return 'Healthy'
  if (status === 'watch') return 'Needs attention'
  if (status === 'critical') return 'Below target'
  return 'No baseline'
}

export function insightSeverityClass(severity: string): string {
  if (severity === 'ok') return 'kb-insight-ok'
  if (severity === 'warn') return 'kb-insight-warn'
  if (severity === 'critical') return 'kb-insight-critical'
  return 'kb-insight-info'
}

export function formatDelta(delta: number | null | undefined): string {
  if (delta == null) return '—'
  const sign = delta >= 0 ? '+' : ''
  return `${sign}${delta}`
}

export function formatWhen(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}
