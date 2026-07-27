/**
 * Minimal gate for sessionScene save/consume (no vitest in package).
 * Run: node --experimental-strip-types src/sessionScene.selftest.ts
 */
import {
  SCENE_STORAGE_KEY,
  consumeWebScene,
  peekWebScene,
  saveWebScene,
} from './sessionScene.ts'

function assert(cond: unknown, msg: string) {
  if (!cond) throw new Error(msg)
}

// sessionStorage polyfill for node
const store = new Map<string, string>()
;(globalThis as { sessionStorage?: Storage }).sessionStorage = {
  getItem: (k) => store.get(k) ?? null,
  setItem: (k, v) => {
    store.set(k, String(v))
  },
  removeItem: (k) => {
    store.delete(k)
  },
  clear: () => store.clear(),
  key: () => null,
  get length() {
    return store.size
  },
} as Storage

saveWebScene({
  v: 1,
  studioTab: 'library',
  guideId: 42,
  libraryFilter: 'favorites',
  draft: '/discogs #1',
  scrollY: 120,
})

const peeked = peekWebScene()
assert(peeked?.studioTab === 'library', 'peek studioTab')
assert(peeked?.guideId === 42, 'peek guideId')
assert(store.has(SCENE_STORAGE_KEY), 'key present')

const consumed = consumeWebScene()
assert(consumed?.libraryFilter === 'favorites', 'consume filter')
assert(peekWebScene() === null, 'cleared after consume')
assert(!store.has(SCENE_STORAGE_KEY), 'key removed')

console.log('sessionScene.selftest ok')
