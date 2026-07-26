export type User = {
  id: number
  email: string
  display_name: string
  email_verified: boolean
  roles: string[]
}

export type TokenResponse = {
  access_token: string
  token_type: string
  user: User
}

export type ChatResponse = {
  reply: string
  thread_id: string
  source: string
}

export type WorkflowStep = {
  id: string
  title: string
  status: string
  thinking: string
  detail: string
  skill_id?: string | null
  skill_version?: string | null
  started_at?: string | null
  finished_at?: string | null
}

export type ListeningGuide = {
  id: number
  work_title: string
  composer: string
  status: string
  source: string
  summary: string
  guide_html: string
  steps: WorkflowStep[]
  skill_versions?: Record<string, string>
  eval_pass?: boolean | null
  eval_score?: number | null
  created_at?: string | null
  published?: boolean
  share_slug?: string | null
  share_path?: string | null
  published_at?: string | null
}

export type PublicGuideMeta = {
  work_title: string
  composer: string
  summary: string
  share_slug: string
  share_path: string
  published_at?: string | null
}

const apiBase = import.meta.env.VITE_AULOS_API_BASE ?? ''
const TOKEN_KEY = 'aulos_access_token'

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function storeToken(token: string | null) {
  if (!token) localStorage.removeItem(TOKEN_KEY)
  else localStorage.setItem(TOKEN_KEY, token)
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  auth = false,
): Promise<T> {
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json')
  }
  if (auth) {
    const token = getStoredToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }
  const response = await fetch(`${apiBase}${path}`, { ...init, headers })
  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function register(email: string, password: string, displayName: string) {
  return request<User>('/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      email,
      password,
      display_name: displayName,
    }),
  })
}

export async function login(email: string, password: string) {
  const data = await request<TokenResponse>('/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  storeToken(data.access_token)
  return data
}

export function verifyEmail(token: string) {
  return request<User>('/v1/auth/verify-email', {
    method: 'POST',
    body: JSON.stringify({ token }),
  })
}

export function forgotPassword(email: string) {
  return request<{ ok: boolean; detail: string }>('/v1/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
}

export function resetPassword(token: string, password: string) {
  return request<{ ok: boolean; detail: string }>('/v1/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, password }),
  })
}

export function fetchMe() {
  return request<User>('/v1/auth/me', {}, true)
}

export function sendChat(message: string, threadId: string) {
  return request<ChatResponse>(
    '/v1/chat',
    {
      method: 'POST',
      body: JSON.stringify({ message, thread_id: threadId }),
    },
    true,
  )
}

export function createListeningGuide(message: string, workHint?: string) {
  return request<ListeningGuide>(
    '/v1/listening-guides',
    {
      method: 'POST',
      body: JSON.stringify({
        message,
        work_hint: workHint || undefined,
      }),
    },
    true,
  )
}

export type GuideStreamHandlers = {
  onStep?: (step: WorkflowStep) => void
  onDone?: (guide: ListeningGuide) => void
  onError?: (detail: string) => void
}

export async function streamListeningGuide(
  message: string,
  handlers: GuideStreamHandlers,
  workHint?: string,
) {
  const headers = new Headers({ 'Content-Type': 'application/json' })
  const token = getStoredToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${apiBase}/v1/listening-guides/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message,
      work_hint: workHint || undefined,
    }),
  })
  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  if (!response.body) {
    throw new Error('Streaming body unavailable')
  }
  await _consumeGuideSSE(response.body, handlers)
}

export async function streamRecomposeGuide(
  guideId: number,
  handlers: GuideStreamHandlers,
  opts?: { message?: string; workHint?: string },
) {
  const headers = new Headers({ 'Content-Type': 'application/json' })
  const token = getStoredToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${apiBase}/v1/listening-guides/${guideId}/recompose/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message: opts?.message || undefined,
      work_hint: opts?.workHint || undefined,
    }),
  })
  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  if (!response.body) {
    throw new Error('Streaming body unavailable')
  }
  await _consumeGuideSSE(response.body, handlers)
}

async function _consumeGuideSSE(body: ReadableStream<Uint8Array>, handlers: GuideStreamHandlers) {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() || ''
    for (const chunk of chunks) {
      const lines = chunk.split('\n')
      let event = 'message'
      const dataLines: string[] = []
      for (const line of lines) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
      }
      if (!dataLines.length) continue
      const raw = dataLines.join('\n')
      let data: unknown = raw
      try {
        data = JSON.parse(raw)
      } catch {
        /* keep raw */
      }
      if (event === 'step' && data && typeof data === 'object') {
        handlers.onStep?.(data as WorkflowStep)
      } else if (event === 'done' && data && typeof data === 'object') {
        handlers.onDone?.(data as ListeningGuide)
      } else if (event === 'error') {
        const detail =
          data && typeof data === 'object' && 'detail' in data
            ? String((data as { detail: unknown }).detail)
            : 'Stream failed'
        handlers.onError?.(detail)
      }
    }
  }
}

export function listListeningGuides() {
  return request<ListeningGuide[]>('/v1/listening-guides', {}, true)
}

export function publishListeningGuide(guideId: number) {
  return request<ListeningGuide>(`/v1/listening-guides/${guideId}/publish`, { method: 'POST' }, true)
}

export function updatePublishListeningGuide(guideId: number) {
  return request<ListeningGuide>(`/v1/listening-guides/${guideId}/update-publish`, { method: 'POST' }, true)
}

export function unpublishListeningGuide(guideId: number) {
  return request<ListeningGuide>(`/v1/listening-guides/${guideId}/unpublish`, { method: 'POST' }, true)
}

export function searchKnowledge(q: string, workHint?: string) {
  const params = new URLSearchParams({ q })
  if (workHint) params.set('work_hint', workHint)
  return request<{
    rag_mode: string
    hits: Array<{ score: number; section: string; text: string; title: string }>
    matched_title?: string
    stats?: { documents: number; chunks: number }
  }>(`/v1/knowledge/search?${params}`, {}, true)
}

export function fetchPublicGuideMeta(slug: string) {
  return request<PublicGuideMeta>(`/v1/public/guides/${encodeURIComponent(slug)}/meta`)
}

export function publicGuidePageUrl(slug: string) {
  return `${apiBase}/v1/public/guides/${encodeURIComponent(slug)}`
}

export function shareGuideUrl(sharePath: string) {
  if (typeof window === 'undefined') return sharePath
  return `${window.location.origin}${sharePath}`
}

export function logout() {
  storeToken(null)
}
