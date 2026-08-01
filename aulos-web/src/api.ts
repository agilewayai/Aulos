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
  index?: number | null
  total?: number | null
  /** When false, step is visible but excluded from done/total (e.g. review milestones). */
  countable?: boolean | null
}

export type GuideProgress = {
  guide_id?: number
  status: string
  done: number
  total: number
  completed?: number
  skipped?: number
  failed?: number
  steps: WorkflowStep[]
  error_detail?: string
}

export type ProcessScorecard = {
  schema?: string
  nodes?: Array<{
    trigger: string
    pct?: number
    band?: string
    hard_fail?: boolean
    scores?: Record<string, number>
  }>
  product?: {
    scores?: Record<string, number>
    pct?: number
    band?: string
    hard_fail?: boolean
  }
  rollup?: {
    earned?: number
    max_possible?: number
    pct?: number
    band?: string
    hard_fail?: boolean
    hard_flaws_high?: number
    hard_flaws_medium?: number
    hard_flaws_remaining?: number
    flaw_budget_earned?: number
    flaw_budget_max?: number
  }
  gates?: {
    eval_pass?: boolean
    review_failed?: boolean
    decontam_failed?: boolean
    ambient_ok?: boolean
  }
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
  process_scorecard?: ProcessScorecard | null
  generation_rounds?: {
    schema?: string
    draft_v1?: {
      guide_html?: string
      summary?: string
      process_scorecard?: ProcessScorecard | null
    }
    review_report?: Record<string, unknown>
    draft_v2?: {
      guide_html?: string
      summary?: string
      process_scorecard?: ProcessScorecard | null
      patched_targets?: string[]
      scope?: string
    }
    comparison?: {
      v1_pct?: number
      v2_pct?: number
      delta_pct?: number
      v1_hard_flaws?: number
      v2_hard_flaws?: number
      winner?: string
      notes?: string[]
    }
    revision_history?: Array<{
      id?: string
      at?: string
      source?: string
      summary?: string
      targets?: string[]
      scope?: string
      score_before?: { pct?: number; hard_flaws?: number }
      score_after?: { pct?: number; hard_flaws?: number }
      diff_summary?: string[]
    }>
  } | null
  external_review_report?: Record<string, unknown> | null
  created_at?: string | null
  updated_at?: string | null
  published?: boolean
  share_slug?: string | null
  share_path?: string | null
  published_at?: string | null
  message?: string
  error_detail?: string
  favorited?: boolean
  favorited_at?: string | null
  tags?: string[]
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

/** Session is HttpOnly cookie-based (SPEC-014); no JS-readable token. */
export function getStoredToken(): string | null {
  return null
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
  void auth
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    headers,
    credentials: 'include',
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
  return request<TokenResponse>('/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
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
  onProgress?: (progress: GuideProgress) => void
  onDone?: (guide: ListeningGuide) => void
  onError?: (detail: string, meta?: { retryable?: boolean; guideId?: number }) => void
}

export async function enqueueListeningJob(message: string, workHint?: string) {
  return request<ListeningGuide>(
    '/v1/listening-guides/jobs',
    {
      method: 'POST',
      body: JSON.stringify({ message, work_hint: workHint || undefined }),
    },
    true,
  )
}

export async function enqueueRecomposeJob(
  guideId: number,
  opts?: { message?: string; workHint?: string },
) {
  return request<ListeningGuide>(
    `/v1/listening-guides/${guideId}/recompose/jobs`,
    {
      method: 'POST',
      body: JSON.stringify({
        message: opts?.message || undefined,
        work_hint: opts?.workHint || undefined,
      }),
    },
    true,
  )
}

export async function fetchListeningGuide(guideId: number) {
  return request<ListeningGuide>(`/v1/listening-guides/${guideId}`, {}, true)
}

function progressFromGuideSteps(snap: {
  id: number
  status: string
  steps?: WorkflowStep[]
  error_detail?: string
}): GuideProgress | null {
  const steps = snap.steps || []
  if (!steps.length) return null
  const countable = steps.filter((s) => s.countable !== false)
  return {
    guide_id: snap.id,
    status: snap.status,
    done: countable.filter((s) =>
      ['done', 'completed', 'ok', 'skip', 'skipped', 'failed'].includes(s.status),
    ).length,
    completed: countable.filter((s) => ['done', 'completed', 'ok'].includes(s.status)).length,
    skipped: countable.filter((s) => ['skip', 'skipped'].includes(s.status)).length,
    failed: countable.filter((s) => s.status === 'failed').length,
    total: steps[0]?.total || countable.length || steps.length,
    steps,
    error_detail: snap.error_detail,
  }
}

export async function retryListeningJob(guideId: number) {
  return request<ListeningGuide>(`/v1/listening-guides/${guideId}/retry`, { method: 'POST' }, true)
}

/** Watch a durable job with SSE reconnect + terminal poll fallback. */
export async function streamGuideEvents(guideId: number, handlers: GuideStreamHandlers) {
  const maxAttempts = 8
  let attempt = 0
  let terminal = false
  const wrapped: GuideStreamHandlers = {
    onStep: handlers.onStep,
    onProgress: handlers.onProgress,
    onDone: (guide) => {
      terminal = true
      handlers.onDone?.(guide)
    },
    onError: (detail, meta) => {
      terminal = true
      handlers.onError?.(detail, meta)
    },
  }

  while (!terminal && attempt < maxAttempts) {
    attempt += 1
    try {
      const response = await fetch(`${apiBase}/v1/listening-guides/${guideId}/events`, {
        method: 'GET',
        credentials: 'include',
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
      await _consumeGuideSSE(response.body, wrapped)
      if (terminal) return
      // Stream ended without terminal event — poll once then reconnect.
      const snap = await fetchListeningGuide(guideId)
      const progress = progressFromGuideSteps(snap)
      if (progress) wrapped.onProgress?.(progress)
      if (snap.status === 'completed') {
        wrapped.onDone?.(snap)
        return
      }
      if (snap.status === 'failed') {
        wrapped.onError?.(snap.error_detail || 'Guide job failed', {
          retryable: true,
          guideId,
        })
        return
      }
    } catch (err) {
      if (terminal) throw err
      const delay = Math.min(12_000, 800 * 2 ** (attempt - 1))
      await new Promise((r) => window.setTimeout(r, delay))
      try {
        const snap = await fetchListeningGuide(guideId)
        if (snap.status === 'completed') {
          wrapped.onDone?.(snap)
          return
        }
        if (snap.status === 'failed') {
          wrapped.onError?.(snap.error_detail || 'Guide job failed', {
            retryable: true,
            guideId,
          })
          return
        }
        const progress = progressFromGuideSteps(snap)
        if (progress) wrapped.onProgress?.(progress)
      } catch {
        /* keep reconnecting */
      }
    }
  }
  if (!terminal) {
    handlers.onError?.('Lost connection to guide job after several retries', {
      retryable: true,
      guideId,
    })
  }
}

export async function streamListeningGuide(
  message: string,
  handlers: GuideStreamHandlers,
  workHint?: string,
) {
  const job = await enqueueListeningJob(message, workHint)
  handlers.onStep?.({
    id: 'queued',
    title: 'Queued',
    status: 'running',
    thinking: 'Guide job entered the atelier queue.',
    detail: `Guide #${job.id}`,
  })
  await streamGuideEvents(job.id, handlers)
}

export async function streamRecomposeGuide(
  guideId: number,
  handlers: GuideStreamHandlers,
  opts?: { message?: string; workHint?: string },
) {
  const job = await enqueueRecomposeJob(guideId, opts)
  handlers.onStep?.({
    id: 'queued',
    title: 'Queued',
    status: 'running',
    thinking: 'Recompose job entered the atelier queue.',
    detail: `Guide #${job.id}`,
  })
  await streamGuideEvents(job.id, handlers)
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
      if (event === 'progress' && data && typeof data === 'object') {
        handlers.onProgress?.(data as GuideProgress)
      } else if (event === 'step' && data && typeof data === 'object') {
        handlers.onStep?.(data as WorkflowStep)
      } else if (event === 'done' && data && typeof data === 'object') {
        handlers.onDone?.(data as ListeningGuide)
      } else if (event === 'error') {
        const detail =
          data && typeof data === 'object' && 'detail' in data
            ? String((data as { detail: unknown }).detail)
            : 'Stream failed'
        const retryable =
          data && typeof data === 'object' && 'retryable' in data
            ? Boolean((data as { retryable: unknown }).retryable)
            : false
        const guideId =
          data && typeof data === 'object' && 'guide_id' in data
            ? Number((data as { guide_id: unknown }).guide_id)
            : undefined
        handlers.onError?.(detail, { retryable, guideId })
      }
    }
  }
}

export type GuideListParams = {
  q?: string
  status?: string
  published?: boolean
  favorited?: boolean
  tag?: string
  limit?: number
  offset?: number
}

export function listListeningGuides(params?: GuideListParams) {
  const search = new URLSearchParams()
  if (params?.q) search.set('q', params.q)
  if (params?.status) search.set('status', params.status)
  if (params?.published != null) search.set('published', String(params.published))
  if (params?.favorited != null) search.set('favorited', params.favorited ? '1' : '0')
  if (params?.tag) search.set('tag', params.tag)
  if (params?.limit != null) search.set('limit', String(params.limit))
  if (params?.offset != null) search.set('offset', String(params.offset))
  const qs = search.toString()
  return request<ListeningGuide[]>(`/v1/listening-guides${qs ? `?${qs}` : ''}`, {}, true)
}

export function deleteListeningGuide(guideId: number) {
  return request<void>(`/v1/listening-guides/${guideId}`, { method: 'DELETE' }, true)
}

export function favoriteListeningGuide(guideId: number) {
  return request<ListeningGuide>(`/v1/listening-guides/${guideId}/favorite`, { method: 'POST' }, true)
}

export function unfavoriteListeningGuide(guideId: number) {
  return request<ListeningGuide>(`/v1/listening-guides/${guideId}/favorite`, { method: 'DELETE' }, true)
}

export function patchListeningGuideTags(guideId: number, tags: string[]) {
  return request<ListeningGuide>(
    `/v1/listening-guides/${guideId}/tags`,
    { method: 'PATCH', body: JSON.stringify({ tags }) },
    true,
  )
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

export type DiscogsSearchHit = {
  id: number
  title: string
  catno: string
  year: string
  label: string
  country: string
  thumb: string
  genres: string[]
  resource_url?: string
  uri?: string
}

export function searchDiscogsReleases(q: string, limit = 10) {
  const params = new URLSearchParams({ q, limit: String(limit) })
  return request<{ query: string; results: DiscogsSearchHit[] }>(
    `/v1/discogs/search?${params}`,
    {},
    true,
  )
}

export type ChainTraceMilestone = {
  id: string
  status: string
  at?: string
  summary: string
  facts?: Record<string, unknown>
  signals?: string[]
}

export type ChainTrace = {
  schema: string
  trace_id: string
  started_at?: string
  finished_at?: string
  input?: { message?: string; work_hint?: string }
  identity_arc?: Array<{
    stage: string
    composer?: string
    work_title?: string
    work_id?: string | null
  }>
  milestones?: ChainTraceMilestone[]
  deviations?: Array<{
    code: string
    at_milestone?: string
    summary: string
    facts?: Record<string, unknown>
  }>
}

export function fetchGuideTrace(guideId: number) {
  return request<{
    guide_id: number
    work_title: string
    composer: string
    created_at?: string | null
    chain_trace: ChainTrace | null
  }>(`/v1/listening-guides/${guideId}/trace`, {}, true)
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

export type DiaryAuthor = {
  id: number
  display_name: string
}

export type DiarySnapshot = {
  provider?: string
  external_id?: string
  source_kind?: string
  title?: string
  cover_image_url?: string
  composers?: string[]
  performers?: string[]
  ensembles?: string[]
  year?: string
  label?: string
  catno?: string
  uri?: string
  genres?: string[]
  styles?: string[]
  tracklist?: Array<{ position?: string; title: string; duration?: string; type?: string }>
}

export type DiaryGuideLink = {
  id: number
  diary_post_id: number
  guide_id?: number | null
  aspect?: string
  status: string
  review_notes?: string
  revised_at?: string | null
  notified_at?: string | null
  published_at?: string | null
  created_at?: string | null
  diary_title?: string
  diary_cover_image_url?: string
  needs_attention?: boolean
  actions?: {
    can_publish?: boolean
    can_revise?: boolean
    can_unpublish?: boolean
    can_dismiss?: boolean
    can_delete?: boolean
  }
  guide?: {
    id: number
    work_title?: string
    composer?: string
    status?: string
    summary?: string
    published?: boolean
    share_slug?: string | null
    share_path?: string | null
    error_detail?: string
    updated_at?: string | null
    steps?: WorkflowStep[]
    guide_html?: string
    process_scorecard?: ProcessScorecard | null
    generation_rounds?: import('./GenerationRoundsPanel').GenerationRounds | null
    external_review_report?: Record<string, unknown> | null
    eval_pass?: boolean | null
    eval_score?: number | null
  } | null
}

export type ListeningDiaryPost = {
  id: number
  user_id: number
  status: string
  source_provider: string
  source_external_id: string
  source_kind: string
  title: string
  cover_image_url: string
  listening_note: string
  listened_on?: string | null
  share_slug?: string | null
  share_path?: string | null
  published?: boolean
  published_at?: string | null
  like_count: number
  comment_count: number
  created_at?: string | null
  updated_at?: string | null
  snapshot?: DiarySnapshot | null
  author?: DiaryAuthor
  guides?: DiaryGuideLink[]
}

export function createListeningDiary(body: {
  provider: string
  external_id: string
  listening_note?: string
  listened_on?: string
  source_kind?: string
}) {
  return request<ListeningDiaryPost>('/v1/listening-diary', { method: 'POST', body: JSON.stringify(body) }, true)
}

export function listListeningDiary(status?: string) {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  params.set('limit', '100')
  const q = params.toString()
  return request<ListeningDiaryPost[]>(`/v1/listening-diary?${q}`, {}, true)
}

export function fetchListeningDiary(postId: number) {
  return request<ListeningDiaryPost>(`/v1/listening-diary/${postId}`, {}, true)
}

export function patchListeningDiary(
  postId: number,
  body: { listening_note?: string; listened_on?: string },
) {
  return request<ListeningDiaryPost>(
    `/v1/listening-diary/${postId}`,
    { method: 'PATCH', body: JSON.stringify(body) },
    true,
  )
}

export function publishListeningDiary(postId: number) {
  return request<ListeningDiaryPost>(`/v1/listening-diary/${postId}/publish`, { method: 'POST' }, true)
}

export function unpublishListeningDiary(postId: number) {
  return request<ListeningDiaryPost>(`/v1/listening-diary/${postId}/unpublish`, { method: 'POST' }, true)
}

export function deleteListeningDiary(postId: number) {
  return request<void>(`/v1/listening-diary/${postId}`, { method: 'DELETE' }, true)
}

export function enqueueDiaryGuide(postId: number, aspect = '作品导赏') {
  return request<DiaryGuideLink>(
    `/v1/listening-diary/${postId}/guides`,
    { method: 'POST', body: JSON.stringify({ aspect }) },
    true,
  )
}

export function listDiaryGuides(postId: number) {
  return request<{ items: DiaryGuideLink[] }>(`/v1/listening-diary/${postId}/guides`, {}, true)
}

export function listDiaryGuideTasks(limit = 50) {
  return request<{
    items: DiaryGuideLink[]
    ready_for_review_count: number
    queued_count: number
  }>(`/v1/listening-diary/guide-tasks?limit=${limit}`, {}, true)
}

export function publishDiaryGuideLink(linkId: number) {
  return request<DiaryGuideLink>(`/v1/listening-diary/guides/${linkId}/publish`, { method: 'POST' }, true)
}

export function unpublishDiaryGuideLink(linkId: number) {
  return request<DiaryGuideLink>(
    `/v1/listening-diary/guides/${linkId}/unpublish`,
    { method: 'POST' },
    true,
  )
}

export function reviseDiaryGuideLink(linkId: number, notes: string) {
  return request<DiaryGuideLink>(
    `/v1/listening-diary/guides/${linkId}/revise`,
    { method: 'POST', body: JSON.stringify({ notes }) },
    true,
  )
}

export function deleteDiaryGuideLink(linkId: number) {
  return request<void>(`/v1/listening-diary/guides/${linkId}`, { method: 'DELETE' }, true)
}

export function dismissDiaryGuideLink(linkId: number) {
  return request<DiaryGuideLink>(`/v1/listening-diary/guides/${linkId}/dismiss`, { method: 'POST' }, true)
}

export function ackDiaryGuideLink(linkId: number) {
  return request<DiaryGuideLink>(`/v1/listening-diary/guides/${linkId}/ack`, { method: 'POST' }, true)
}

export function fetchPlazaFeed(limit = 30) {
  return request<{ items: ListeningDiaryPost[]; limit: number; offset: number }>(
    `/v1/plaza/feed?limit=${limit}`,
  )
}

export function fetchPlazaHome(limit = 30) {
  return request<{ items: ListeningDiaryPost[]; limit: number; offset: number }>(
    `/v1/plaza/home?limit=${limit}`,
    {},
    true,
  )
}

export function fetchPlazaPost(slug: string) {
  return request<ListeningDiaryPost>(`/v1/plaza/posts/${encodeURIComponent(slug)}`)
}

export function likePlazaPost(postId: number) {
  return request<ListeningDiaryPost>(`/v1/plaza/posts/${postId}/likes`, { method: 'POST' }, true)
}

export function unlikePlazaPost(postId: number) {
  return request<ListeningDiaryPost>(`/v1/plaza/posts/${postId}/likes`, { method: 'DELETE' }, true)
}

export function listPlazaComments(postId: number) {
  return request<{
    items: Array<{
      id: number
      post_id: number
      body: string
      created_at?: string | null
      author: DiaryAuthor
    }>
  }>(`/v1/plaza/posts/${postId}/comments`)
}

export function addPlazaComment(postId: number, body: string) {
  return request<{
    id: number
    post_id: number
    body: string
    created_at?: string | null
    author: DiaryAuthor
  }>(`/v1/plaza/posts/${postId}/comments`, { method: 'POST', body: JSON.stringify({ body }) }, true)
}

export function followUser(userId: number) {
  return request<{ follower_id: number; followee_id: number }>(
    `/v1/social/follows/${userId}`,
    { method: 'POST' },
    true,
  )
}

export function unfollowUser(userId: number) {
  return request<void>(`/v1/social/follows/${userId}`, { method: 'DELETE' }, true)
}

export type PersonEntityCard = {
  name: string
  kind: string
  person_id: string
  display_name: string
  display_name_en?: string
  display_name_zh?: string
  lifespan?: string
  era?: string
  summary?: string
  summary_en?: string
  summary_zh?: string
  summary_en_origin?: string
  summary_zh_origin?: string
  portrait_url?: string
  external_ids?: Record<string, string | string[]>
  snippets?: Array<{ title?: string; text?: string; source_id?: string; score?: number }>
  sources?: Array<{ source_id?: string; role?: string; url?: string; fields?: string[]; lang?: string }>
  source?: string
  provenance?: Array<{ source_id?: string; url?: string }>
  locale_default?: string
  matched?: boolean
}

export function resolvePersonEntity(name: string, kind = 'person', enrich = true, locale = 'zh') {
  const params = new URLSearchParams({
    name,
    kind,
    enrich: enrich ? 'true' : 'false',
    locale,
  })
  return request<PersonEntityCard>(`/v1/entities/person?${params.toString()}`)
}

export async function logout() {
  try {
    await request('/v1/auth/logout', { method: 'POST' })
  } catch {
    /* best-effort */
  }
}
