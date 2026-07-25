export type ServerVersion = {
  app?: string
  buildId?: string
  builtAt?: string
  status?: number
}

export const CLIENT_BUILD_ID =
  typeof __AULOS_BUILD_ID__ === 'string' ? __AULOS_BUILD_ID__ : 'dev'

const DISMISS_KEY = 'aulos-asset-dismissed-build'

export function isBuildOutdated(serverBuildId: string | undefined, clientBuildId = CLIENT_BUILD_ID): boolean {
  return Boolean(serverBuildId && clientBuildId && serverBuildId !== clientBuildId)
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
