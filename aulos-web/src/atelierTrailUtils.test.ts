import assert from 'node:assert/strict'
import {
  atelierCompletedCount,
  atelierDoneCount,
  atelierProgressPercent,
  atelierSkippedCount,
  atelierTotalCount,
  chainProgressFromSteps,
  stepStatusLabel,
} from './atelierTrailUtils.ts'
import type { WorkflowStep } from './api.ts'

const steps: WorkflowStep[] = [
  { id: 'a', title: 'A', status: 'done', thinking: '', detail: '', total: 4 },
  { id: 'b', title: 'B', status: 'skip', thinking: '', detail: 'no discogs' },
  { id: 'c', title: 'C', status: 'running', thinking: '', detail: '' },
  { id: 'd', title: 'D', status: 'pending', thinking: '', detail: '' },
  {
    id: 'review-x',
    title: 'Review',
    status: 'done',
    thinking: '',
    detail: '',
    countable: false,
  },
]

assert.equal(atelierCompletedCount(steps), 1)
assert.equal(atelierSkippedCount(steps), 1)
assert.equal(atelierDoneCount(steps), 2)
assert.equal(atelierTotalCount(steps, null), 4)
assert.equal(atelierTotalCount([], null), null)
assert.equal(atelierProgressPercent(steps, { done: 2, total: 4 }), 50)
assert.equal(atelierProgressPercent(steps, null), 50)

const progress = chainProgressFromSteps(steps, 4)
assert.equal(progress.completed, 1)
assert.equal(progress.skipped, 1)
assert.equal(progress.done, 2)
assert.equal(progress.total, 4)

assert.equal(stepStatusLabel('skip'), '跳过')
assert.equal(stepStatusLabel('done'), '完成')
assert.equal(stepStatusLabel('running'), '进行中')

console.log('atelierTrailUtils ok')
