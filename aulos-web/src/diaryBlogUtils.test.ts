import assert from 'node:assert/strict'
import {
  buildDiaryTagCloud,
  buildMonthGrid,
  countsByDate,
  filterDiaryPosts,
  postListeningDate,
  shiftMonth,
  tagFontRem,
  type DiaryDateLike,
} from './diaryBlogUtils.ts'

const posts: DiaryDateLike[] = [
  {
    id: 1,
    listened_on: '2026-08-01',
    source_kind: 'vinyl',
    snapshot: {
      composers: ['Bach'],
      performers: ['Gould'],
      genres: ['Classical'],
      styles: ['Baroque'],
    },
  },
  {
    id: 2,
    listened_on: '2026-08-01',
    source_kind: 'cd',
    snapshot: {
      composers: ['Bach'],
      performers: ['Schiff'],
      genres: ['Classical'],
    },
  },
  {
    id: 3,
    created_at: '2026-07-15T12:00:00Z',
    source_kind: 'vinyl',
    snapshot: { composers: ['Mozart'], ensembles: ['VPO'] },
  },
]

assert.equal(postListeningDate(posts[0]), '2026-08-01')
assert.equal(countsByDate(posts).get('2026-08-01'), 2)

const tags = buildDiaryTagCloud(posts)
const bach = tags.find((t) => t.label === 'Bach' && t.kind === 'composer')
assert.ok(bach)
assert.equal(bach.count, 2)
assert.ok(tags.some((t) => t.kind === 'format' && t.label === '黑胶'))

const filtered = filterDiaryPosts(posts, { date: '2026-08-01', tag: bach })
assert.equal(filtered.length, 2)

const grid = buildMonthGrid(2026, 7, countsByDate(posts))
assert.ok(grid.some((c) => c.date === '2026-08-01' && c.count === 2))

const shifted = shiftMonth(2026, 0, -1)
assert.deepEqual(shifted, { year: 2025, monthIndex: 11 })

assert.ok(tagFontRem(2, 1, 2) > tagFontRem(1, 1, 2))

console.log('diaryBlogUtils ok')
