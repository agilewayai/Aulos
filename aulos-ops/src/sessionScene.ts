export const SCENE_STORAGE_KEY = 'aulos-ops-session-scene'
export const CAPTURE_EVENT = 'aulos:capture-scene'

export type OpsTabId =
  | 'overview'
  | 'users'
  | 'llm'
  | 'skills'
  | 'mail'
  | 'fleet'
  | 'dbha'
  | 'knowledge'
  | 'discogs'
  | 'blog'
  | 'tasks'

export type OpsSessionScene = {
  v: 1
  tab?: OpsTabId
  userQuery?: string
  roleFilter?: string
  activeFilter?: 'all' | 'true' | 'false'
  verifiedFilter?: 'all' | 'true' | 'false'
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
    /* ignore */
  }
}

export function saveOpsScene(scene: OpsSessionScene): void {
  try {
    sessionStorage.setItem(
      SCENE_STORAGE_KEY,
      JSON.stringify({ ...scene, v: 1, savedAt: new Date().toISOString() }),
    )
  } catch {
    /* ignore */
  }
}

export function peekOpsScene(): OpsSessionScene | null {
  try {
    const raw = sessionStorage.getItem(SCENE_STORAGE_KEY)
    if (!raw) return null
    const data = JSON.parse(raw) as OpsSessionScene
    if (data?.v !== 1) return null
    return data
  } catch {
    return null
  }
}

export function consumeOpsScene(): OpsSessionScene | null {
  const scene = peekOpsScene()
  try {
    sessionStorage.removeItem(SCENE_STORAGE_KEY)
  } catch {
    /* ignore */
  }
  return scene
}
