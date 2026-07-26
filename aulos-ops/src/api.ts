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

export type HealthResponse = {
  status: string
  service: string
  version: string
  backends?: Record<string, string>
}

export type MailgunConfig = {
  domain: string
  from_email: string
  enabled: boolean
  api_key_set: boolean
  region: string
  provider_mode: string
  env_mail_provider: string
  ready_for_live_send: boolean
}

export type MailgunTestResult = {
  ok: boolean
  provider_mode: string
  detail: string
  domain?: string
  from_email?: string
  region?: string
  delivery_id?: number | null
}

export type DeliveryRow = {
  id: number
  kind: string
  to_email: string
  subject: string
  provider: string
  status: string
  detail: string
  provider_message_id: string
  created_at: string
}

export type OpsUser = {
  id: number
  email: string
  display_name: string
  email_verified: boolean
  is_active: boolean
  roles: string[]
  created_at: string
  updated_at: string
}

export type OpsRole = {
  id: number
  name: string
  description: string
  user_count: number
}

export type OpsOverview = {
  users_total: number
  users_active: number
  users_verified: number
  users_unverified: number
  users_inactive: number
  roles: Record<string, number>
  email_deliveries_total: number
  email_deliveries_failed: number
  mail_provider_mode: string
  mail_ready_for_live_send: boolean
  llm_active_provider: string
  llm_ready_for_live: boolean
}

export type LlmProviderPublic = {
  api_key_set: boolean
  model: string
  base_url: string
  ready: boolean
}

export type LlmConfig = {
  active_provider: string
  ready_for_live: boolean
  deepseek: LlmProviderPublic
  grok: LlmProviderPublic
  supported_providers: string[]
}

export type EmbedConfig = {
  provider: string
  api_key_set: boolean
  model: string
  base_url: string
  ready: boolean
  supported_providers?: string[]
  local_default_model?: string
  fastembed_available?: boolean
}

export type LlmTestResult = {
  ok: boolean
  provider: string
  detail: string
  model?: string
}

export type SkillRow = {
  id: string
  name: string
  layer: string
  runtime: string
  version: string
  summary: string
  triggers: string[]
  observability_title: string
  enabled: boolean
}

export type SkillProbe = {
  work_title: string
  composer: string
  summary: string
  steps: Array<Record<string, unknown>>
  skill_versions: Record<string, string>
  eval_pass: boolean
  eval_score: number
  source: string
  guide_html_chars?: number
}

export type ServiceCard = {
  id: string
  name: string
  role: string
  path: string
}

export const AULOS_SERVICES: ServiceCard[] = [
  { id: 'aulos-web', name: 'Web', role: 'Operator GUI', path: 'aulos-web/' },
  { id: 'aulos-api', name: 'API', role: 'HTTP gateway', path: 'aulos-api/' },
  { id: 'aulos-agent', name: 'Agent', role: 'LangGraph runtime', path: 'aulos-agent/' },
  { id: 'aulos-mcp', name: 'MCP', role: 'Agent integrations', path: 'aulos-mcp/' },
  { id: 'aulos-skills', name: 'Skills', role: 'Main harness skills', path: 'aulos-skills/' },
  { id: 'aulos-ops', name: 'Ops', role: 'Admin portal', path: 'aulos-ops/' },
]

const apiBase = import.meta.env.VITE_AULOS_API_BASE ?? ''
const TOKEN_KEY = 'aulos_ops_access_token'

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function storeToken(token: string | null) {
  if (!token) localStorage.removeItem(TOKEN_KEY)
  else localStorage.setItem(TOKEN_KEY, token)
}

async function request<T>(path: string, init: RequestInit = {}, auth = false): Promise<T> {
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
  return response.json() as Promise<T>
}

export async function login(email: string, password: string) {
  const data = await request<TokenResponse>('/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  storeToken(data.access_token)
  return data
}

export function fetchMe() {
  return request<User>('/v1/auth/me', {}, true)
}

export function fetchGatewayHealth() {
  return request<HealthResponse>('/health')
}

export function fetchMailgun() {
  return request<MailgunConfig>('/v1/ops/mailgun', {}, true)
}

export function updateMailgun(payload: {
  api_key?: string
  domain: string
  from_email: string
  enabled: boolean
  region: string
}) {
  return request<MailgunConfig>(
    '/v1/ops/mailgun',
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    },
    true,
  )
}

export function testMailgun(toEmail: string) {
  return request<MailgunTestResult>(
    '/v1/ops/mailgun/test',
    {
      method: 'POST',
      body: JSON.stringify({ to_email: toEmail }),
    },
    true,
  )
}

export function fetchMailgunDeliveries() {
  return request<DeliveryRow[]>('/v1/ops/mailgun/deliveries', {}, true)
}

export function fetchOverview() {
  return request<OpsOverview>('/v1/ops/overview', {}, true)
}

export function fetchOpsUsers(params?: {
  q?: string
  role?: string
  active?: boolean
  verified?: boolean
}) {
  const qs = new URLSearchParams()
  if (params?.q) qs.set('q', params.q)
  if (params?.role) qs.set('role', params.role)
  if (params?.active !== undefined) qs.set('active', String(params.active))
  if (params?.verified !== undefined) qs.set('verified', String(params.verified))
  const suffix = qs.toString() ? `?${qs.toString()}` : ''
  return request<OpsUser[]>(`/v1/ops/users${suffix}`, {}, true)
}

export function fetchOpsRoles() {
  return request<OpsRole[]>('/v1/ops/roles', {}, true)
}

export function updateOpsUser(
  userId: number,
  payload: {
    display_name?: string
    email_verified?: boolean
    is_active?: boolean
    roles?: string[]
  },
) {
  return request<OpsUser>(
    `/v1/ops/users/${userId}`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    },
    true,
  )
}

export function resendUserVerification(userId: number) {
  return request<{ ok: boolean; detail: string; delivery_id?: number | null }>(
    `/v1/ops/users/${userId}/resend-verification`,
    { method: 'POST' },
    true,
  )
}

export function deleteOpsUser(userId: number, confirmEmail: string) {
  return request<{
    ok: boolean
    deleted_user_id: number
    deleted_email: string
    detail: string
  }>(
    `/v1/ops/users/${userId}`,
    {
      method: 'DELETE',
      body: JSON.stringify({ confirm_email: confirmEmail }),
    },
    true,
  )
}

export function fetchLlmConfig() {
  return request<LlmConfig>('/v1/ops/llm', {}, true)
}

export function updateLlmConfig(payload: {
  active_provider: string
  deepseek_api_key?: string
  deepseek_model?: string
  deepseek_base_url?: string
  grok_api_key?: string
  grok_model?: string
  grok_base_url?: string
}) {
  return request<LlmConfig>(
    '/v1/ops/llm',
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    },
    true,
  )
}

export function testLlmProvider(provider?: string) {
  return request<LlmTestResult>(
    '/v1/ops/llm/test',
    {
      method: 'POST',
      body: JSON.stringify({ provider: provider || null }),
    },
    true,
  )
}

export function fetchEmbedConfig() {
  return request<EmbedConfig>('/v1/ops/embeddings', {}, true)
}

export type WebResearchConfig = {
  enabled: boolean
  min_rag_hits: number
  min_dossier_richness: number
  refresh_after_hours: number
  brave_api_key_set: boolean
  persist_global: boolean
  max_sources: number
  agent_reach_enabled: boolean
}

export function fetchWebResearchConfig() {
  return request<WebResearchConfig>('/v1/ops/web-research', {}, true)
}

export function updateWebResearchConfig(payload: {
  enabled?: boolean
  min_rag_hits?: number
  min_dossier_richness?: number
  refresh_after_hours?: number
  brave_api_key?: string
  persist_global?: boolean
  max_sources?: number
  agent_reach_enabled?: boolean
}) {
  return request<WebResearchConfig>(
    '/v1/ops/web-research',
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    },
    true,
  )
}

export type DiscogsConfig = {
  enabled: boolean
  user_token_set: boolean
  auth_source: string
  authenticated: boolean
}

export function fetchDiscogsConfig() {
  return request<DiscogsConfig>('/v1/ops/discogs', {}, true)
}

export function updateDiscogsConfig(payload: {
  enabled?: boolean
  user_token?: string
  clear_user_token?: boolean
}) {
  return request<DiscogsConfig>(
    '/v1/ops/discogs',
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    },
    true,
  )
}

export function updateEmbedConfig(payload: {
  provider?: string
  api_key?: string
  model?: string
  base_url?: string
}) {
  return request<EmbedConfig>(
    '/v1/ops/embeddings',
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    },
    true,
  )
}

export function fetchKnowledgeStats() {
  return request<{
    documents: number
    chunks: number
    embed_ready: boolean
    plane_enabled?: boolean
    plane_url?: string
  }>('/v1/ops/knowledge/stats', {}, true)
}

export type KnowledgeSource = {
  id: string
  name: string
  tier: string
  connector: string
  license_class: string
  rate_limit_qps: number
  enabled: boolean
  notes: string
}

export type KnowledgeJob = {
  id: number
  source_id: string
  status: string
  error: string
  created_at?: string | null
  finished_at?: string | null
}

export type KnowledgeDoc = {
  id: number
  title: string
  entity_type?: string
  entity_id?: string
  aulos_work_id: string
  status: string
  source_id: string
  artifact_id?: number | null
  job_id?: number | null
  extractor_version: string
  license_class: string
  body_preview?: string
  body?: string
}

export type KnowledgeComposer = {
  id: string
  name_en: string
  name_zh: string
  lifespan: string
  external_ids: Record<string, string>
}

export type KnowledgePlaneStats = {
  sources: number
  works: number
  composers?: number
  documents: number
  documents_published: number
  documents_quarantine: number
  jobs: number
  artifacts: number
  media_assets?: number
  media_images?: number
  media_audio?: number
  media_meta?: number
}

function plane(path: string, init: RequestInit = {}) {
  return request<unknown>(`/v1/ops/knowledge/plane${path}`, init, true)
}

export function fetchKnowledgePlaneHealth() {
  return plane('/health') as Promise<{ status: string; service: string; version: string }>
}

export function fetchKnowledgePlaneStats() {
  return plane('/v1/kb/stats') as Promise<KnowledgePlaneStats>
}

export function fetchKnowledgeSources() {
  return plane('/v1/admin/sources') as Promise<KnowledgeSource[]>
}

export function fetchKnowledgeJobs() {
  return plane('/v1/admin/jobs') as Promise<KnowledgeJob[]>
}

export function enqueueKnowledgeJob(sourceId: string, params: Record<string, unknown> = {}) {
  return plane('/v1/admin/jobs', {
    method: 'POST',
    body: JSON.stringify({ source_id: sourceId, params }),
  }) as Promise<KnowledgeJob>
}

export function fetchKnowledgeComposers() {
  return plane('/v1/admin/composers') as Promise<KnowledgeComposer[]>
}

export function fetchKnowledgeDocuments(opts: {
  status?: string
  entity_type?: string
  source_id?: string
  q?: string
  limit?: number
} = {}) {
  const sp = new URLSearchParams()
  if (opts.status) sp.set('status', opts.status)
  if (opts.entity_type) sp.set('entity_type', opts.entity_type)
  if (opts.source_id) sp.set('source_id', opts.source_id)
  if (opts.q) sp.set('q', opts.q)
  if (opts.limit) sp.set('limit', String(opts.limit))
  const q = sp.toString()
  return plane(`/v1/admin/documents${q ? `?${q}` : ''}`) as Promise<KnowledgeDoc[]>
}

export function fetchKnowledgeDocument(documentId: number) {
  return plane(`/v1/admin/documents/${documentId}`) as Promise<KnowledgeDoc>
}

export function fetchKnowledgeProvenance(documentId: number) {
  return plane(`/v1/admin/provenance/${documentId}`) as Promise<Record<string, unknown>>
}

export function fetchKnowledgeArtifact(artifactId: number) {
  return plane(`/v1/admin/artifacts/${artifactId}`) as Promise<{
    id: number
    content_hash: string
    storage_path: string
    source_url: string
    exists: boolean
    preview: string
  }>
}

export function knowledgeRetrieveLab(query: string, workId = '', composerId = '') {
  return plane('/v1/kb/retrieve', {
    method: 'POST',
    body: JSON.stringify({ query, work_id: workId, composer_id: composerId, k: 6 }),
  }) as Promise<{ hits: Array<{ title: string; score: number; text: string; aulos_work_id?: string }> }>
}

export function patchKnowledgeSource(sourceId: string, payload: { enabled?: boolean }) {
  return plane(`/v1/admin/sources/${encodeURIComponent(sourceId)}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  }) as Promise<{ ok: boolean; id: string; enabled: boolean }>
}

export function quarantineKnowledgeDocument(docId: number) {
  return plane(`/v1/admin/documents/${docId}/quarantine`, {
    method: 'POST',
    body: JSON.stringify({}),
  }) as Promise<{ ok: boolean; status: string }>
}

export function publishKnowledgeDocument(docId: number) {
  return plane(`/v1/admin/documents/${docId}/publish`, {
    method: 'POST',
    body: JSON.stringify({}),
  }) as Promise<{ ok: boolean; status: string }>
}

export type KnowledgeMedia = {
  id: number
  kind: string
  title: string
  entity_id: string
  storage_path: string
  byte_size: number
  license_class: string
  exists_on_disk: boolean
  content_type: string
  source_url: string
}

export function fetchKnowledgeMedia(opts: { kind?: string; entity_id?: string; limit?: number } = {}) {
  const sp = new URLSearchParams()
  if (opts.kind) sp.set('kind', opts.kind)
  if (opts.entity_id) sp.set('entity_id', opts.entity_id)
  if (opts.limit) sp.set('limit', String(opts.limit))
  const q = sp.toString()
  return plane(`/v1/admin/media${q ? `?${q}` : ''}`) as Promise<KnowledgeMedia[]>
}

export type DbHaStatus = {
  active_role: 'primary' | 'failover' | string
  primary: { url_scheme: string; dialect: string; ok: boolean }
  failover: {
    configured: boolean
    url_scheme: string | null
    dialect: string | null
    ok: boolean
  }
  sync: {
    status: string
    at?: string | null
    error?: string
    tables?: Record<string, number>
    duration_ms?: number
    trigger?: string
    row_total?: number
  }
  auto_failover: boolean
  sync_interval_sec: number
  redis_queue?: string
}

export function fetchDbHa() {
  return request<DbHaStatus>('/v1/ops/db/ha', {}, true)
}

export function enqueueDbSync(queue = true) {
  const q = queue ? '?queue=true' : '?queue=false'
  return request<Record<string, unknown>>(`/v1/ops/db/sync${q}`, { method: 'POST' }, true)
}

export function setDbActiveRole(role: 'primary' | 'failover', reason = 'ops') {
  return request<{ ok: boolean; active_role: string; status: DbHaStatus }>(
    '/v1/ops/db/role',
    { method: 'POST', body: JSON.stringify({ role, reason }) },
    true,
  )
}

export function fetchSkills() {
  return request<SkillRow[]>('/v1/ops/skills', {}, true)
}

export function toggleSkill(skillId: string, enabled: boolean) {
  return request<SkillRow>(
    `/v1/ops/skills/${encodeURIComponent(skillId)}`,
    {
      method: 'PATCH',
      body: JSON.stringify({ enabled }),
    },
    true,
  )
}

export function probeSkills(message: string) {
  return request<SkillProbe>(
    '/v1/ops/skills/probe',
    {
      method: 'POST',
      body: JSON.stringify({ message }),
    },
    true,
  )
}

export type DevBlogSummary = {
  day: string
  title: string
  provider: string
  generated_at: string
  evidence?: {
    day?: string
    repo_root?: string
    commit_count?: number
    commits?: Array<{ sha: string; date: string; author: string; subject: string }>
    harness_sources?: Array<{ project: string; path: string }>
    changed_harness_paths?: string[]
  }
}

export type DevBlogPost = DevBlogSummary & {
  body_md: string
}

export function fetchDevBlogList() {
  return request<DevBlogSummary[]>('/v1/ops/dev-blog', {}, true)
}

export function fetchDevBlog(day: string) {
  return request<DevBlogPost>(`/v1/ops/dev-blog/${encodeURIComponent(day)}`, {}, true)
}

export function generateDevBlog(day: string, force = false) {
  return request<DevBlogPost>(
    `/v1/ops/dev-blog/${encodeURIComponent(day)}/generate`,
    {
      method: 'POST',
      body: JSON.stringify({ force }),
    },
    true,
  )
}

export function logout() {
  storeToken(null)
}
