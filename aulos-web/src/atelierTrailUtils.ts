import type { WorkflowStep } from './api'

const DONE = new Set(['done', 'completed', 'ok'])
const SKIP = new Set(['skip', 'skipped'])
const FAIL = new Set(['failed'])
const TERMINAL = new Set([...DONE, ...SKIP, ...FAIL])

export function isCountableStep(step: WorkflowStep): boolean {
  return step.countable !== false
}

export function atelierCompletedCount(steps: WorkflowStep[]): number {
  return steps.filter((s) => isCountableStep(s) && DONE.has(s.status)).length
}

export function atelierSkippedCount(steps: WorkflowStep[]): number {
  return steps.filter((s) => isCountableStep(s) && SKIP.has(s.status)).length
}

export function atelierFailedCount(steps: WorkflowStep[]): number {
  return steps.filter((s) => isCountableStep(s) && FAIL.has(s.status)).length
}

/** Finished countable steps (completed + skipped + failed). */
export function atelierDoneCount(steps: WorkflowStep[]): number {
  return steps.filter((s) => isCountableStep(s) && TERMINAL.has(s.status)).length
}

/** Raw total for display; null when unknown. */
export function atelierTotalCount(
  steps: WorkflowStep[],
  progress?: { done: number; total: number } | null,
): number | null {
  if (progress?.total && progress.total > 0) return progress.total
  const fromStep = steps.find((s) => isCountableStep(s) && (s.total || 0) > 0)?.total
  if (fromStep && fromStep > 0) return fromStep
  const n = steps.filter(isCountableStep).length
  return n > 0 ? n : null
}

export function atelierProgressPercent(
  steps: WorkflowStep[],
  progress?: { done: number; total: number } | null,
): number {
  const done = progress?.done ?? atelierDoneCount(steps)
  const total = atelierTotalCount(steps, progress) ?? 1
  return Math.min(100, Math.round((100 * done) / Math.max(1, total)))
}

export type ChainProgress = {
  done: number
  total: number
  completed?: number
  skipped?: number
  failed?: number
}

/** Upsert one SSE step by id and keep index order (Studio + diary). */
export function upsertWorkflowStep(prev: WorkflowStep[], step: WorkflowStep): WorkflowStep[] {
  const next = [...prev.filter((item) => item.id !== step.id), step]
  next.sort((a, b) => (a.index ?? 0) - (b.index ?? 0))
  return next
}

export function sortWorkflowSteps(steps: WorkflowStep[]): WorkflowStep[] {
  return [...steps].sort((a, b) => (a.index ?? 0) - (b.index ?? 0))
}

export function chainProgressFromSteps(
  steps: WorkflowStep[],
  fallbackTotal?: number | null,
): ChainProgress {
  const completed = atelierCompletedCount(steps)
  const skipped = atelierSkippedCount(steps)
  const failed = atelierFailedCount(steps)
  return {
    done: completed + skipped + failed,
    completed,
    skipped,
    failed,
    total: fallbackTotal || atelierTotalCount(steps, null) || steps.filter(isCountableStep).length,
  }
}

const STATUS_LABELS: Record<string, string> = {
  done: '完成',
  completed: '完成',
  ok: '完成',
  skip: '跳过',
  skipped: '跳过',
  failed: '失败',
  running: '进行中',
  pending: '等待',
}

export function stepStatusLabel(status: string): string {
  return STATUS_LABELS[status] || status
}
