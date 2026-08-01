/** Pure helpers for 我的聆乐 blog calendar + tag cloud (SPEC-009). */

import { sourceKindLabel } from './sourceKind'

export type DiaryTagKind = 'composer' | 'performer' | 'ensemble' | 'genre' | 'style' | 'format'

export type DiaryTag = {
  id: string
  label: string
  kind: DiaryTagKind
  count: number
}

export type DiaryDateLike = {
  id: number
  listened_on?: string | null
  created_at?: string | null
  source_kind?: string
  snapshot?: {
    composers?: string[]
    performers?: string[]
    ensembles?: string[]
    genres?: string[]
    styles?: string[]
    source_kind?: string
  } | null
}

const KIND_LABEL: Record<DiaryTagKind, string> = {
  composer: '作曲家',
  performer: '演奏家',
  ensemble: '乐团',
  genre: '类型',
  style: '风格',
  format: '介质',
}

export function tagKindLabel(kind: DiaryTagKind): string {
  return KIND_LABEL[kind]
}

/** YYYY-MM-DD for calendar / filter. Prefer listened_on; else local date of created_at. */
export function postListeningDate(post: DiaryDateLike): string | null {
  const on = (post.listened_on || '').trim()
  if (/^\d{4}-\d{2}-\d{2}$/.test(on)) return on
  const created = (post.created_at || '').trim()
  if (!created) return null
  const d = new Date(created)
  if (Number.isNaN(d.getTime())) return null
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function countsByDate(posts: DiaryDateLike[]): Map<string, number> {
  const map = new Map<string, number>()
  for (const p of posts) {
    const key = postListeningDate(p)
    if (!key) continue
    map.set(key, (map.get(key) || 0) + 1)
  }
  return map
}

function pushNames(
  bucket: Map<string, DiaryTag>,
  names: string[] | undefined,
  kind: DiaryTagKind,
) {
  for (const raw of names || []) {
    const label = String(raw || '').trim()
    if (!label) continue
    const id = `${kind}:${label.toLowerCase()}`
    const prev = bucket.get(id)
    if (prev) prev.count += 1
    else bucket.set(id, { id, label, kind, count: 1 })
  }
}

export function buildDiaryTagCloud(posts: DiaryDateLike[]): DiaryTag[] {
  const bucket = new Map<string, DiaryTag>()
  for (const p of posts) {
    const snap = p.snapshot
    pushNames(bucket, snap?.composers, 'composer')
    pushNames(bucket, snap?.performers, 'performer')
    pushNames(bucket, snap?.ensembles, 'ensemble')
    pushNames(bucket, snap?.genres, 'genre')
    pushNames(bucket, snap?.styles, 'style')
    const format = (p.source_kind || snap?.source_kind || '').trim()
    if (format) {
      pushNames(bucket, [sourceKindLabel(format)], 'format')
    }
  }
  return [...bucket.values()].sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, 'zh'))
}

export function tagWeightScale(tags: DiaryTag[]): { min: number; max: number } {
  if (!tags.length) return { min: 1, max: 1 }
  let min = Infinity
  let max = -Infinity
  for (const t of tags) {
    min = Math.min(min, t.count)
    max = Math.max(max, t.count)
  }
  if (!Number.isFinite(min)) min = 1
  if (!Number.isFinite(max)) max = 1
  return { min, max }
}

/** Map count → font-size rem between 0.78 and 1.55 */
export function tagFontRem(count: number, min: number, max: number): number {
  if (max <= min) return 1
  const t = (count - min) / (max - min)
  return 0.78 + t * 0.77
}

export function postHasTag(post: DiaryDateLike, tag: DiaryTag): boolean {
  const snap = post.snapshot
  if (tag.kind === 'composer') return (snap?.composers || []).some((n) => n.trim() === tag.label)
  if (tag.kind === 'performer') return (snap?.performers || []).some((n) => n.trim() === tag.label)
  if (tag.kind === 'ensemble') return (snap?.ensembles || []).some((n) => n.trim() === tag.label)
  if (tag.kind === 'genre') return (snap?.genres || []).some((n) => n.trim() === tag.label)
  if (tag.kind === 'style') return (snap?.styles || []).some((n) => n.trim() === tag.label)
  if (tag.kind === 'format') {
    const format = (post.source_kind || snap?.source_kind || '').trim()
    return sourceKindLabel(format) === tag.label
  }
  return false
}

export function filterDiaryPosts(
  posts: DiaryDateLike[],
  opts: { date?: string | null; tag?: DiaryTag | null },
): DiaryDateLike[] {
  return posts.filter((p) => {
    if (opts.date && postListeningDate(p) !== opts.date) return false
    if (opts.tag && !postHasTag(p, opts.tag)) return false
    return true
  })
}

/** Build calendar cells for a month (Sunday-first). */
export type CalendarCell = {
  date: string | null
  day: number | null
  inMonth: boolean
  count: number
}

export function buildMonthGrid(year: number, monthIndex: number, counts: Map<string, number>): CalendarCell[] {
  const first = new Date(year, monthIndex, 1)
  const startPad = first.getDay() // 0=Sun
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate()
  const cells: CalendarCell[] = []
  for (let i = 0; i < startPad; i++) {
    cells.push({ date: null, day: null, inMonth: false, count: 0 })
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const date = `${year}-${String(monthIndex + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    cells.push({ date, day: d, inMonth: true, count: counts.get(date) || 0 })
  }
  while (cells.length % 7 !== 0) {
    cells.push({ date: null, day: null, inMonth: false, count: 0 })
  }
  return cells
}

export function shiftMonth(year: number, monthIndex: number, delta: number): { year: number; monthIndex: number } {
  const d = new Date(year, monthIndex + delta, 1)
  return { year: d.getFullYear(), monthIndex: d.getMonth() }
}

export function todayIsoLocal(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
