/** Capture / restore UI “现场” across intentional asset reloads. */

export const SCENE_STORAGE_KEY = 'aulos-web-session-scene'
export const CAPTURE_EVENT = 'aulos:capture-scene'

export type StudioTab = 'guide' | 'atelier' | 'library'
export type LibraryFilter = 'all' | 'favorites' | 'published' | 'progress'
export type AuthMode = 'login' | 'register' | 'verify' | 'forgot' | 'reset' | 'studio'

export type WebSessionScene = {
  v: 1
  mode?: AuthMode
  email?: string
  displayName?: string
  studioTab?: StudioTab
  composeOpen?: boolean
  draft?: string
  guideId?: number | null
  showGuide?: boolean
  libraryQuery?: string
  libraryFilter?: LibraryFilter
  tagFilter?: string
  scrollY?: number
  savedAt?: string
}

type CaptureFn = () => void

const captures = new Set<CaptureFn>()

export function registerSceneCapture(fn: CaptureFn): () => void {
  captures.add(fn)
  return () => {
    captures.delete(fn)
  }
}

/** Ask registered UIs to persist scene, then callers may reload. */
export function captureRegisteredScenes(): void {
  for (const fn of captures) {
    try {
      fn()
    } catch {
      /* best-effort */
    }
  }
  try {
    window.dispatchEvent(new Event(CAPTURE_EVENT))
  } catch {
    /* jsdom / private */
  }
}

export function saveWebScene(scene: WebSessionScene): void {
  try {
    const payload: WebSessionScene = {
      ...scene,
      v: 1,
      savedAt: new Date().toISOString(),
    }
    sessionStorage.setItem(SCENE_STORAGE_KEY, JSON.stringify(payload))
  } catch {
    /* quota / private mode */
  }
}

export function peekWebScene(): WebSessionScene | null {
  try {
    const raw = sessionStorage.getItem(SCENE_STORAGE_KEY)
    if (!raw) return null
    const data = JSON.parse(raw) as WebSessionScene
    if (data?.v !== 1) return null
    return data
  } catch {
    return null
  }
}

/** Read once and clear so a later normal refresh does not re-apply. */
export function consumeWebScene(): WebSessionScene | null {
  const scene = peekWebScene()
  try {
    sessionStorage.removeItem(SCENE_STORAGE_KEY)
  } catch {
    /* ignore */
  }
  return scene
}
