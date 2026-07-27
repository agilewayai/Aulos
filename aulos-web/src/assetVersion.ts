export type ServerVersion = {
  app?: string
  buildId?: string
  builtAt?: string
  status?: number
}

export const CLIENT_BUILD_ID =
  typeof __AULOS_BUILD_ID__ === 'string' ? __AULOS_BUILD_ID__ : 'dev'

const RELOAD_ATTEMPT_KEY = 'aulos-asset-reload-for'
const DISMISS_KEY = 'aulos-asset-dismissed-build'

export function isBuildOutdated(serverBuildId: string | undefined, clientBuildId = CLIENT_BUILD_ID): boolean {
  if (!serverBuildId || !clientBuildId) return false
  // Dev / missing inject must never force a reload loop.
  if (clientBuildId === 'dev') return false
  return serverBuildId !== clientBuildId
}

export function alreadyReloadedFor(serverBuildId: string): boolean {
  try {
    return sessionStorage.getItem(RELOAD_ATTEMPT_KEY) === serverBuildId
  } catch {
    return false
  }
}

export function markReloadedFor(serverBuildId: string): void {
  try {
    sessionStorage.setItem(RELOAD_ATTEMPT_KEY, serverBuildId)
  } catch {
    /* private mode */
  }
}

export function clearReloadAttempt(serverBuildId?: string): void {
  try {
    if (!serverBuildId || sessionStorage.getItem(RELOAD_ATTEMPT_KEY) === serverBuildId) {
      sessionStorage.removeItem(RELOAD_ATTEMPT_KEY)
    }
  } catch {
    /* ignore */
  }
}

export function isDismissed(serverBuildId: string): boolean {
  try {
    return sessionStorage.getItem(DISMISS_KEY) === serverBuildId
  } catch {
    return false
  }
}

export function dismissBuild(serverBuildId: string): void {
  try {
    sessionStorage.setItem(DISMISS_KEY, serverBuildId)
  } catch {
    /* private mode */
  }
}

/** Hard navigation so hashed assets are not stuck behind a soft reload cache. */
export function hardReload(): void {
  const url = new URL(window.location.href)
  url.searchParams.set('_aulos_v', String(Date.now()))
  window.location.replace(url.toString())
}

export async function fetchServerVersion(): Promise<ServerVersion | null> {
  try {
    const res = await fetch(`/version.json?_=${Date.now()}`, { cache: 'no-store' })
    if (res.status === 429) return { status: 429 }
    if (!res.ok) return null
    const data = (await res.json()) as ServerVersion
    return { ...data, status: res.status }
  } catch {
    return null
  }
}
