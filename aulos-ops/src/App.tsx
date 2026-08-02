import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import {
  AULOS_SERVICES,
  fetchGatewayHealth,
  fetchMailgun,
  fetchMailgunDeliveries,
  fetchMe,
  fetchOpsRoles,
  fetchOpsUsers,
  fetchOverview,
  login,
  logout,
  deleteOpsUser,
  fetchLlmConfig,
  fetchListeningReviewConfig,
  fetchAmbientFallbackConfig,
  fetchSkills,
  fetchEmbedConfig,
  fetchWebResearchConfig,
  fetchDiscogsConfig,
  fetchKnowledgeStats,
  resendUserVerification,
  testLlmProvider,
  testMailgun,
  updateLlmConfig,
  updateListeningReviewConfig,
  updateAmbientFallbackConfig,
  updateEmbedConfig,
  updateWebResearchConfig,
  updateDiscogsConfig,
  updateMailgun,
  updateOpsUser,
  type DeliveryRow,
  type DiscogsConfig,
  type EmbedConfig,
  type HealthResponse,
  type LlmConfig,
  type ListeningReviewConfig,
  type AmbientFallbackConfig,
  type MailgunConfig,
  type OpsOverview,
  type OpsRole,
  type OpsUser,
  type SkillRow,
  type User,
  type WebResearchConfig,
} from './api'
import { KnowledgePanel } from './KnowledgePanel'
import { SkillsPanel } from './SkillsPanel'
import { GuideQualityPanel } from './GuideQualityPanel'
import { DbHaPanel } from './DbHaPanel'
import { DevBlogPanel } from './DevBlogPanel'
import { TaskQueuePanel } from './TaskQueuePanel'
import { PasswordField } from './PasswordField'
import { formatDateTime, formatTime } from './time'
import {
  consumeOpsScene,
  registerSceneCapture,
  saveOpsScene,
  type OpsSessionScene,
  type OpsTabId,
} from './sessionScene'
import { requestAssetVersionCheck } from './assetVersion'
import { OpsDashboardShell } from './layout/OpsDashboardShell'
import './App.css'

const PENDING_SCENE: OpsSessionScene | null =
  typeof window === 'undefined' ? null : consumeOpsScene()

const FALLBACK_MODEL_OPTIONS: Record<string, { id: string; label: string }[]> = {
  deepseek: [
    { id: 'deepseek-chat', label: 'deepseek-chat (V3 — general)' },
    { id: 'deepseek-reasoner', label: 'deepseek-reasoner (R1 — thinking)' },
    { id: 'deepseek-v4-pro', label: 'deepseek-v4-pro' },
    { id: 'deepseek-v4-flash', label: 'deepseek-v4-flash' },
    { id: 'deepseek-coder', label: 'deepseek-coder' },
  ],
  grok: [
    { id: 'grok-3-mini', label: 'grok-3-mini (fast / cheap)' },
    { id: 'grok-3', label: 'grok-3' },
    { id: 'grok-3-fast', label: 'grok-3-fast' },
    { id: 'grok-4', label: 'grok-4' },
    { id: 'grok-4-0709', label: 'grok-4-0709' },
    { id: 'grok-2-1212', label: 'grok-2-1212' },
    { id: 'grok-2-vision-1212', label: 'grok-2-vision-1212' },
  ],
}

function ProviderModelSelect({
  id,
  value,
  options,
  onChange,
}: {
  id: string
  value: string
  options: { id: string; label: string }[]
  onChange: (next: string) => void
}) {
  const known = options.some((o) => o.id === value)
  const selectValue = known ? value : '__custom__'
  return (
    <div className="llm-model-picker">
      <select
        id={id}
        value={selectValue}
        onChange={(e) => {
          const next = e.target.value
          if (next === '__custom__') {
            onChange(known ? '' : value)
            return
          }
          onChange(next)
        }}
      >
        {options.map((o) => (
          <option key={o.id} value={o.id}>
            {o.label}
          </option>
        ))}
        <option value="__custom__">Custom model id…</option>
      </select>
      {selectValue === '__custom__' ? (
        <input
          aria-label="Custom model id"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="provider-model-id"
        />
      ) : null}
    </div>
  )
}

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [tab, setTab] = useState<OpsTabId>(() => PENDING_SCENE?.tab ?? 'overview')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [overview, setOverview] = useState<OpsOverview | null>(null)
  const [opsUsers, setOpsUsers] = useState<OpsUser[]>([])
  const [roles, setRoles] = useState<OpsRole[]>([])
  const [userQuery, setUserQuery] = useState(() => PENDING_SCENE?.userQuery ?? '')
  const [roleFilter, setRoleFilter] = useState(() => PENDING_SCENE?.roleFilter ?? '')
  const [activeFilter, setActiveFilter] = useState<'all' | 'true' | 'false'>(
    () => PENDING_SCENE?.activeFilter ?? 'all',
  )
  const [verifiedFilter, setVerifiedFilter] = useState<'all' | 'true' | 'false'>(
    () => PENDING_SCENE?.verifiedFilter ?? 'all',
  )
  const [mailgun, setMailgun] = useState<MailgunConfig | null>(null)
  const [llm, setLlm] = useState<LlmConfig | null>(null)
  const [listeningReview, setListeningReview] = useState<ListeningReviewConfig | null>(null)
  const [reviewLlmEnabled, setReviewLlmEnabled] = useState(true)
  const [ambientFallback, setAmbientFallback] = useState<AmbientFallbackConfig | null>(null)
  const [ambientFallbackMode, setAmbientFallbackMode] = useState<'embed' | 'stream'>('embed')
  const [llmActive, setLlmActive] = useState('fake')
  const [llmDraftProvider, setLlmDraftProvider] = useState('deepseek')
  const [llmReviewProvider, setLlmReviewProvider] = useState('grok')
  const [deepseekKey, setDeepseekKey] = useState('')
  const [deepseekModel, setDeepseekModel] = useState('deepseek-chat')
  const [deepseekBase, setDeepseekBase] = useState('https://api.deepseek.com')
  const [grokKey, setGrokKey] = useState('')
  const [grokModel, setGrokModel] = useState('grok-3-mini')
  const [grokBase, setGrokBase] = useState('https://api.x.ai/v1')
  const [embed, setEmbed] = useState<EmbedConfig | null>(null)
  const [embedProvider, setEmbedProvider] = useState('local')
  const [embedKey, setEmbedKey] = useState('')
  const [embedModel, setEmbedModel] = useState(
    'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
  )
  const [embedBase, setEmbedBase] = useState('https://api.openai.com/v1')
  const [webResearch, setWebResearch] = useState<WebResearchConfig | null>(null)
  const [webEnabled, setWebEnabled] = useState(true)
  const [webMinHits, setWebMinHits] = useState(3)
  const [webMinRich, setWebMinRich] = useState(5)
  const [webRefreshHours, setWebRefreshHours] = useState(168)
  const [webPersistGlobal, setWebPersistGlobal] = useState(true)
  const [webAgentReach, setWebAgentReach] = useState(true)
  const [webBraveKey, setWebBraveKey] = useState('')
  const [discogs, setDiscogs] = useState<DiscogsConfig | null>(null)
  const [discogsEnabled, setDiscogsEnabled] = useState(true)
  const [discogsToken, setDiscogsToken] = useState('')
  const [discogsClearToken, setDiscogsClearToken] = useState(false)
  const [kbStats, setKbStats] = useState<{
    documents: number
    chunks: number
    embed_ready: boolean
    plane_enabled?: boolean
    plane_url?: string
  } | null>(null)
  const [skills, setSkills] = useState<SkillRow[]>([])
  const [deliveries, setDeliveries] = useState<DeliveryRow[]>([])
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [domain, setDomain] = useState('')
  const [fromEmail, setFromEmail] = useState('')
  const [region, setRegion] = useState('us')
  const [enabled, setEnabled] = useState(false)
  const [testToEmail, setTestToEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [updatedAt, setUpdatedAt] = useState<string | null>(null)
  const sceneSnapshotRef = useRef({
    tab: 'overview' as OpsTabId,
    userQuery: '',
    roleFilter: '',
    activeFilter: 'all' as 'all' | 'true' | 'false',
    verifiedFilter: 'all' as 'all' | 'true' | 'false',
  })
  sceneSnapshotRef.current = { tab, userQuery, roleFilter, activeFilter, verifiedFilter }

  useEffect(() => {
    requestAssetVersionCheck()
  }, [tab])

  useEffect(() => {
    return registerSceneCapture(() => {
      const snap = sceneSnapshotRef.current
      saveOpsScene({
        v: 1,
        tab: snap.tab,
        userQuery: snap.userQuery,
        roleFilter: snap.roleFilter,
        activeFilter: snap.activeFilter,
        verifiedFilter: snap.verifiedFilter,
        scrollY: window.scrollY,
      })
    })
  }, [])

  useEffect(() => {
    if (!PENDING_SCENE || !user) return
    if (typeof PENDING_SCENE.scrollY === 'number') {
      window.requestAnimationFrame(() => window.scrollTo(0, PENDING_SCENE.scrollY ?? 0))
    }
    setNotice('Restored your place after update')
  }, [user])

  const refreshHealth = useCallback(async () => {
    try {
      const data = await fetchGatewayHealth()
      setHealth(data)
      setUpdatedAt(formatTime(new Date()))
    } catch (err) {
      setHealth(null)
      setError(err instanceof Error ? err.message : 'Health request failed')
    }
  }, [])

  const refreshDeliveries = useCallback(async () => {
    const rows = await fetchMailgunDeliveries()
    setDeliveries(rows)
  }, [])

  const refreshOverview = useCallback(async () => {
    setOverview(await fetchOverview())
  }, [])

  const refreshUsers = useCallback(
    async (overrides?: {
      q?: string
      role?: string
      active?: 'all' | 'true' | 'false'
      verified?: 'all' | 'true' | 'false'
    }) => {
      const q = overrides?.q ?? userQuery
      const role = overrides?.role ?? roleFilter
      const active = overrides?.active ?? activeFilter
      const verified = overrides?.verified ?? verifiedFilter
      const rows = await fetchOpsUsers({
        q: q.trim() || undefined,
        role: role || undefined,
        active: active === 'all' ? undefined : active === 'true',
        verified: verified === 'all' ? undefined : verified === 'true',
      })
      setOpsUsers(rows)
      setRoles(await fetchOpsRoles())
    },
    [userQuery, roleFilter, activeFilter, verifiedFilter],
  )

  const loadOps = useCallback(async () => {
    const me = await fetchMe()
    if (!me.roles.includes('superadmin')) {
      void logout()
      setUser(null)
      throw new Error('Ops portal requires the superadmin role')
    }
    setUser(me)
    const cfg = await fetchMailgun()
    setMailgun(cfg)
    setDomain(cfg.domain)
    setFromEmail(cfg.from_email)
    setEnabled(cfg.enabled)
    setRegion(cfg.region || 'us')
    setTestToEmail((prev) => prev || me.email)
    setApiKey('')
    const llmCfg = await fetchLlmConfig()
    setLlm(llmCfg)
    setLlmActive(llmCfg.active_provider)
    setLlmDraftProvider(llmCfg.draft_provider || 'deepseek')
    setLlmReviewProvider(llmCfg.review_provider || 'grok')
    setDeepseekModel(llmCfg.deepseek.model)
    setDeepseekBase(llmCfg.deepseek.base_url)
    setGrokModel(llmCfg.grok.model)
    setGrokBase(llmCfg.grok.base_url)
    setDeepseekKey('')
    setGrokKey('')
    try {
      const rev = await fetchListeningReviewConfig()
      setListeningReview(rev)
      setReviewLlmEnabled(rev.enabled)
    } catch {
      setListeningReview(null)
      setReviewLlmEnabled(true)
    }
    try {
      const amb = await fetchAmbientFallbackConfig()
      setAmbientFallback(amb)
      setAmbientFallbackMode(amb.mode === 'stream' ? 'stream' : 'embed')
    } catch {
      setAmbientFallback(null)
      setAmbientFallbackMode('embed')
    }
    try {
      const emb = await fetchEmbedConfig()
      setEmbed(emb)
      setEmbedProvider(emb.provider || 'local')
      setEmbedModel(emb.model)
      setEmbedBase(emb.base_url)
      setEmbedKey('')
      setKbStats(await fetchKnowledgeStats())
      const wr = await fetchWebResearchConfig()
      setWebResearch(wr)
      setWebEnabled(wr.enabled)
      setWebMinHits(wr.min_rag_hits)
      setWebMinRich(wr.min_dossier_richness)
      setWebRefreshHours(wr.refresh_after_hours ?? 168)
      setWebPersistGlobal(wr.persist_global)
      setWebAgentReach(wr.agent_reach_enabled ?? true)
      setWebBraveKey('')
    } catch {
      setEmbed(null)
      setKbStats(null)
      setWebResearch(null)
    }
    try {
      const dg = await fetchDiscogsConfig()
      setDiscogs(dg)
      setDiscogsEnabled(dg.enabled)
      setDiscogsToken('')
      setDiscogsClearToken(false)
    } catch {
      setDiscogs(null)
    }
    try {
      setSkills(await fetchSkills())
    } catch {
      setSkills([])
    }
    await Promise.all([
      refreshDeliveries(),
      refreshOverview(),
      fetchOpsUsers().then(setOpsUsers),
      fetchOpsRoles().then(setRoles),
    ])
  }, [refreshDeliveries, refreshOverview])

  useEffect(() => {
    void refreshHealth()
    const id = window.setInterval(() => void refreshHealth(), 15000)
    return () => window.clearInterval(id)
  }, [refreshHealth])

  useEffect(() => {
    setBusy(true)
    loadOps()
      .catch((err) => {
        const msg = err instanceof Error ? err.message : 'Session restore failed'
        if (!/not authenticated|401/i.test(msg)) setError(msg)
      })
      .finally(() => setBusy(false))
  }, [loadOps])

  async function onLogin(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const data = await login(email.trim(), password)
      if (!data.user.roles.includes('superadmin')) {
        void logout()
        throw new Error('Ops portal requires the superadmin role')
      }
      setUser(data.user)
      await loadOps()
      setPassword('')
      setNotice('Signed in as superadmin.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  async function onSaveLlm(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const cfg = await updateLlmConfig({
        active_provider: llmActive,
        draft_provider: llmDraftProvider,
        review_provider: llmReviewProvider,
        deepseek_api_key: deepseekKey.trim() || undefined,
        deepseek_model: deepseekModel.trim(),
        deepseek_base_url: deepseekBase.trim(),
        grok_api_key: grokKey.trim() || undefined,
        grok_model: grokModel.trim(),
        grok_base_url: grokBase.trim(),
      })
      setLlm(cfg)
      setDeepseekKey('')
      setGrokKey('')
      const rev = await updateListeningReviewConfig({ enabled: reviewLlmEnabled })
      setListeningReview(rev)
      const amb = await updateAmbientFallbackConfig({ mode: ambientFallbackMode })
      setAmbientFallback(amb)
      setNotice(
        `LLM saved. Active=${cfg.active_provider}; draft=${cfg.draft_provider}/${cfg.ready_for_draft ? 'ready' : 'not ready'}; review=${cfg.review_provider}/${cfg.ready_for_review ? 'ready' : 'not ready'}. Review LLM=${rev.enabled ? 'on' : 'off'}. Ambient=${amb.mode}.`,
      )
      await refreshOverview()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'LLM save failed')
    } finally {
      setBusy(false)
    }
  }

  async function onSaveEmbed(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const cfg = await updateEmbedConfig({
        provider: embedProvider,
        api_key: embedKey.trim() || undefined,
        model: embedModel.trim(),
        base_url: embedBase.trim(),
      })
      setEmbed(cfg)
      setEmbedProvider(cfg.provider || 'local')
      setEmbedKey('')
      setKbStats(await fetchKnowledgeStats())
      setNotice(
        cfg.ready
          ? `Embeddings saved — provider=${cfg.provider} (${cfg.model}).`
          : 'Embeddings saved — not ready (install fastembed or complete remote key).',
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Embeddings save failed')
    } finally {
      setBusy(false)
    }
  }

  async function onSaveWebResearch(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const cfg = await updateWebResearchConfig({
        enabled: webEnabled,
        min_rag_hits: webMinHits,
        min_dossier_richness: webMinRich,
        refresh_after_hours: webRefreshHours,
        persist_global: webPersistGlobal,
        agent_reach_enabled: webAgentReach,
        brave_api_key: webBraveKey.trim() || undefined,
      })
      setWebResearch(cfg)
      setWebEnabled(cfg.enabled)
      setWebMinHits(cfg.min_rag_hits)
      setWebMinRich(cfg.min_dossier_richness)
      setWebRefreshHours(cfg.refresh_after_hours)
      setWebPersistGlobal(cfg.persist_global)
      setWebAgentReach(cfg.agent_reach_enabled ?? true)
      setWebBraveKey('')
      setNotice(
        cfg.enabled
          ? `Web research on — cold-fill when thin; refresh after ${cfg.refresh_after_hours}h (0=always). Agent Reach Jina=${cfg.agent_reach_enabled}.`
          : 'Web research disabled.',
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Web research save failed')
    } finally {
      setBusy(false)
    }
  }

  async function onSaveDiscogs(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const cfg = await updateDiscogsConfig({
        enabled: discogsEnabled,
        user_token: discogsClearToken ? undefined : discogsToken.trim() || undefined,
        clear_user_token: discogsClearToken,
      })
      setDiscogs(cfg)
      setDiscogsEnabled(cfg.enabled)
      setDiscogsToken('')
      setDiscogsClearToken(false)
      setNotice(
        cfg.enabled
          ? `Discogs ${cfg.authenticated ? `authenticated (${cfg.auth_source})` : 'enabled — unauthenticated low tier'}; studio /discogs uses this token.`
          : 'Discogs connector disabled.',
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Discogs save failed')
    } finally {
      setBusy(false)
    }
  }

  async function onTestLlm(provider?: string) {
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      await updateLlmConfig({
        active_provider: llmActive,
        draft_provider: llmDraftProvider,
        review_provider: llmReviewProvider,
        deepseek_api_key: deepseekKey.trim() || undefined,
        deepseek_model: deepseekModel.trim(),
        deepseek_base_url: deepseekBase.trim(),
        grok_api_key: grokKey.trim() || undefined,
        grok_model: grokModel.trim(),
        grok_base_url: grokBase.trim(),
      })
      const result = await testLlmProvider(provider)
      setNotice(result.detail)
      const cfg = await fetchLlmConfig()
      setLlm(cfg)
      setDeepseekKey('')
      setGrokKey('')
      await refreshOverview()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'LLM test failed')
    } finally {
      setBusy(false)
    }
  }

  async function onSaveMailgun(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const cfg = await updateMailgun({
        api_key: apiKey.trim() || undefined,
        domain: domain.trim(),
        from_email: fromEmail.trim(),
        enabled,
        region,
      })
      setMailgun(cfg)
      setApiKey('')
      setNotice(
        cfg.provider_mode === 'mailgun'
          ? 'Mailgun settings saved. Live sending is active.'
          : 'Mailgun settings saved. Provider is still fake — enable Mailgun and ensure AULOS_MAIL_PROVIDER=auto.',
      )
      await Promise.all([refreshDeliveries(), refreshOverview()])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setBusy(false)
    }
  }

  async function onTestMailgun(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      await updateMailgun({
        api_key: apiKey.trim() || undefined,
        domain: domain.trim(),
        from_email: fromEmail.trim(),
        enabled,
        region,
      })
      const result = await testMailgun(testToEmail.trim())
      setNotice(result.detail)
      const cfg = await fetchMailgun()
      setMailgun(cfg)
      setApiKey('')
      await Promise.all([refreshDeliveries(), refreshOverview()])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Mailgun test failed')
      try {
        await refreshDeliveries()
      } catch {
        /* ignore */
      }
    } finally {
      setBusy(false)
    }
  }

  async function onUserAction(
    target: OpsUser,
    action:
      | 'verify'
      | 'unverify'
      | 'activate'
      | 'deactivate'
      | 'grant_admin'
      | 'revoke_admin'
      | 'resend'
      | 'delete',
  ) {
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      if (action === 'delete') {
        const typed = window.prompt(
          `Permanently delete ${target.email}?\nType the email address to confirm.`,
          '',
        )
        if (typed === null) {
          setNotice('Delete cancelled.')
          return
        }
        if (typed.trim().toLowerCase() !== target.email.toLowerCase()) {
          throw new Error('Delete aborted — email confirmation did not match')
        }
        const result = await deleteOpsUser(target.id, target.email)
        setNotice(result.detail)
        await Promise.all([refreshUsers(), refreshOverview(), refreshDeliveries()])
        return
      }
      if (action === 'resend') {
        const result = await resendUserVerification(target.id)
        setNotice(result.detail)
        await Promise.all([refreshUsers(), refreshDeliveries(), refreshOverview()])
        return
      }
      let payload: Parameters<typeof updateOpsUser>[1] = {}
      if (action === 'verify') payload = { email_verified: true }
      if (action === 'unverify') payload = { email_verified: false }
      if (action === 'activate') payload = { is_active: true }
      if (action === 'deactivate') payload = { is_active: false }
      if (action === 'grant_admin') {
        const rolesSet = new Set(target.roles)
        rolesSet.add('user')
        rolesSet.add('superadmin')
        payload = { roles: [...rolesSet] }
      }
      if (action === 'revoke_admin') {
        payload = { roles: target.roles.filter((r) => r !== 'superadmin') }
        if (!payload.roles?.length) payload.roles = ['user']
      }
      const updated = await updateOpsUser(target.id, payload)
      setNotice(`Updated ${updated.email}`)
      await Promise.all([refreshUsers(), refreshOverview()])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'User update failed')
    } finally {
      setBusy(false)
    }
  }

  function onLogout() {
    void logout()
    setUser(null)
    setMailgun(null)
    setLlm(null)
    setDeliveries([])
    setOpsUsers([])
    setOverview(null)
    setNotice('Signed out.')
  }

  const gatewayOk = health?.status === 'ok'

  return (
    <div className="shell ops-app">
      <div className="grid-bg" aria-hidden="true" />

      {!user ? (
        <main className="ops-auth-stage">
          {notice ? <p className="notice" role="status">{notice}</p> : null}
          {error ? <p className="error" role="alert">{error}</p> : null}
          <section className="auth-panel" aria-labelledby="ops-login-title">
            <form className="auth-form" onSubmit={onLogin}>
              <h1 id="ops-login-title">Superadmin sign in</h1>
              <p className="tagline">Admin portal — superadmin sign-in required</p>
              <label htmlFor="ops-email">Email</label>
              <input
                id="ops-email"
                type="email"
                required
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <label htmlFor="ops-password">Password</label>
              <PasswordField
                id="ops-password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button type="submit" disabled={busy}>
                {busy ? 'Signing in…' : 'Sign in'}
              </button>
            </form>
          </section>
        </main>
      ) : (
        <OpsDashboardShell
          tab={tab}
          onTabChange={setTab}
          user={user}
          gatewayOk={gatewayOk}
          health={health}
          updatedAt={updatedAt}
          busy={busy}
          notice={notice}
          error={error}
          onRefreshHealth={() => void refreshHealth()}
          onLogout={onLogout}
        >
            {tab === 'overview' ? (
              <>
                <section className="health" aria-live="polite">
                  <h2>Gateway</h2>
                  <div className={`status-line ${gatewayOk ? 'ok' : 'down'}`}>
                    <span className="dot" />
                    <span>
                      {gatewayOk
                        ? `${health?.service} ${health?.version} — healthy`
                        : 'Gateway unreachable'}
                    </span>
                  </div>
                  {updatedAt ? <p className="meta">Last check {updatedAt}</p> : null}
                </section>

                <section className="overview" aria-labelledby="overview-title">
                  <div className="section-head">
                    <h2 id="overview-title">Business overview</h2>
                    <button
                      type="button"
                      className="refresh"
                      disabled={busy}
                      onClick={() => void refreshOverview()}
                    >
                      Refresh
                    </button>
                  </div>
                  {overview ? (
                    <>
                      <div className="stat-grid">
                        <div className="stat">
                          <p className="stat-value">{overview.users_total}</p>
                          <p className="stat-label">Users</p>
                        </div>
                        <div className="stat">
                          <p className="stat-value">{overview.users_active}</p>
                          <p className="stat-label">Active</p>
                        </div>
                        <div className="stat">
                          <p className="stat-value">{overview.users_verified}</p>
                          <p className="stat-label">Verified</p>
                        </div>
                        <div className="stat">
                          <p className="stat-value">{overview.users_unverified}</p>
                          <p className="stat-label">Unverified</p>
                        </div>
                        <div className="stat">
                          <p className="stat-value">{overview.email_deliveries_total}</p>
                          <p className="stat-label">Email sends</p>
                        </div>
                        <div className="stat">
                          <p className="stat-value">{overview.email_deliveries_failed}</p>
                          <p className="stat-label">Failed sends</p>
                        </div>
                      </div>
                      <p className="settings-lead">
                        Mail provider: <strong>{overview.mail_provider_mode}</strong>
                        {' · '}
                        live ready={overview.mail_ready_for_live_send ? 'yes' : 'no'}
                        {' · '}
                        LLM: <strong>{overview.llm_active_provider}</strong>
                        {' · '}
                        llm live={overview.llm_ready_for_live ? 'yes' : 'no'}
                        {' · '}
                        Discogs:{' '}
                        <strong>
                          {discogs == null
                            ? '—'
                            : !discogs.enabled
                              ? 'off'
                              : discogs.authenticated
                                ? discogs.auth_source
                                : 'no token'}
                        </strong>
                        {' · '}
                        roles:{' '}
                        {Object.entries(overview.roles)
                          .map(([name, count]) => `${name}=${count}`)
                          .join(', ') || 'none'}
                      </p>
                      <p className="settings-lead">
                        <button
                          type="button"
                          className="linkish"
                          onClick={() => setTab('discogs')}
                        >
                          Open Discogs token settings →
                        </button>
                      </p>
                    </>
                  ) : (
                    <p className="settings-lead">Loading overview…</p>
                  )}
                </section>
              </>
            ) : null}

            {tab === 'users' ? (
              <section className="users" aria-labelledby="users-title">
                <div className="section-head">
                  <h2 id="users-title">Users</h2>
                  <button
                    type="button"
                    className="refresh"
                    disabled={busy}
                    onClick={() => void refreshUsers()}
                  >
                    Refresh users
                  </button>
                </div>
                <form
                  className="filters"
                  onSubmit={(e) => {
                    e.preventDefault()
                    void refreshUsers()
                  }}
                >
                  <label htmlFor="user-q">Search</label>
                  <input
                    id="user-q"
                    value={userQuery}
                    onChange={(e) => setUserQuery(e.target.value)}
                    placeholder="email or name"
                  />
                  <label htmlFor="user-role">Role</label>
                  <select
                    id="user-role"
                    value={roleFilter}
                    onChange={(e) => setRoleFilter(e.target.value)}
                  >
                    <option value="">All roles</option>
                    {roles.map((r) => (
                      <option key={r.id} value={r.name}>
                        {r.name} ({r.user_count})
                      </option>
                    ))}
                  </select>
                  <label htmlFor="user-active">Active</label>
                  <select
                    id="user-active"
                    value={activeFilter}
                    onChange={(e) => setActiveFilter(e.target.value as 'all' | 'true' | 'false')}
                  >
                    <option value="all">All</option>
                    <option value="true">Active</option>
                    <option value="false">Inactive</option>
                  </select>
                  <label htmlFor="user-verified">Verified</label>
                  <select
                    id="user-verified"
                    value={verifiedFilter}
                    onChange={(e) => setVerifiedFilter(e.target.value as 'all' | 'true' | 'false')}
                  >
                    <option value="all">All</option>
                    <option value="true">Verified</option>
                    <option value="false">Unverified</option>
                  </select>
                  <button type="submit" className="refresh" disabled={busy}>
                    Apply
                  </button>
                </form>

                {opsUsers.length === 0 ? (
                  <p className="settings-lead">No users match the current filters.</p>
                ) : (
                  <ul className="user-list">
                    {opsUsers.map((row) => (
                      <li key={row.id} className={`user-row ${row.is_active ? '' : 'inactive'}`}>
                        <div className="user-main">
                          <p className="svc-name">
                            {row.display_name || row.email}
                            <span className="user-id">#{row.id}</span>
                          </p>
                          <p className="svc-role">{row.email}</p>
                          <p className="meta">
                            {row.is_active ? 'active' : 'inactive'}
                            {' · '}
                            {row.email_verified ? 'verified' : 'unverified'}
                            {' · '}
                            {row.roles.join(', ') || 'no roles'}
                            {' · '}
                            joined {formatDateTime(row.created_at)}
                          </p>
                        </div>
                        <div className="user-actions">
                          {row.email_verified ? (
                            <button
                              type="button"
                              className="refresh"
                              disabled={busy}
                              onClick={() => void onUserAction(row, 'unverify')}
                            >
                              Mark unverified
                            </button>
                          ) : (
                            <>
                              <button
                                type="button"
                                className="refresh"
                                disabled={busy}
                                onClick={() => void onUserAction(row, 'verify')}
                              >
                                Mark verified
                              </button>
                              <button
                                type="button"
                                className="refresh"
                                disabled={busy}
                                onClick={() => void onUserAction(row, 'resend')}
                              >
                                Resend verify
                              </button>
                            </>
                          )}
                          {row.is_active ? (
                            <button
                              type="button"
                              className="refresh"
                              disabled={busy || row.id === user.id}
                              onClick={() => void onUserAction(row, 'deactivate')}
                            >
                              Deactivate
                            </button>
                          ) : (
                            <button
                              type="button"
                              className="refresh"
                              disabled={busy}
                              onClick={() => void onUserAction(row, 'activate')}
                            >
                              Activate
                            </button>
                          )}
                          {row.roles.includes('superadmin') ? (
                            <button
                              type="button"
                              className="refresh"
                              disabled={busy || row.id === user.id}
                              onClick={() => void onUserAction(row, 'revoke_admin')}
                            >
                              Revoke admin
                            </button>
                          ) : (
                            <button
                              type="button"
                              className="refresh"
                              disabled={busy}
                              onClick={() => void onUserAction(row, 'grant_admin')}
                            >
                              Grant admin
                            </button>
                          )}
                          <button
                            type="button"
                            className="refresh danger"
                            disabled={busy || row.id === user.id}
                            onClick={() => void onUserAction(row, 'delete')}
                          >
                            Delete
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            ) : null}

            {tab === 'llm' ? (
              <section className="settings llm" aria-labelledby="llm-title">
                <h2 id="llm-title">LLM providers</h2>
                <p className="settings-lead">
                  Active: <strong>{llm?.active_provider ?? '…'}</strong>
                  {' · '}
                  draft=<strong>{llm?.draft_provider ?? 'deepseek'}</strong>
                  {llm?.ready_for_draft ? ' ✓' : ' ✗'}
                  {' · '}
                  review=<strong>{llm?.review_provider ?? 'grok'}</strong>
                  {llm?.ready_for_review ? ' ✓' : ' ✗'}
                  {' · '}
                  DeepSeek {llm?.deepseek.api_key_set ? 'key set' : 'key missing'}
                  {' · '}
                  Grok {llm?.grok.api_key_set ? 'key set' : 'key missing'}
                </p>
                <form className="auth-form" onSubmit={onSaveLlm}>
                  <label htmlFor="llm-active">Active provider (chat)</label>
                  <select
                    id="llm-active"
                    value={llmActive}
                    onChange={(e) => setLlmActive(e.target.value)}
                  >
                    <option value="fake">fake (echo / offline)</option>
                    <option value="deepseek">DeepSeek</option>
                    <option value="grok">Grok (xAI)</option>
                  </select>

                  <label htmlFor="llm-draft">Draft / author provider (初稿)</label>
                  <select
                    id="llm-draft"
                    value={llmDraftProvider}
                    onChange={(e) => setLlmDraftProvider(e.target.value)}
                  >
                    <option value="deepseek">DeepSeek</option>
                    <option value="grok">Grok (xAI)</option>
                  </select>
                  <label htmlFor="llm-review">Review provider (多 Agent 审稿)</label>
                  <select
                    id="llm-review"
                    value={llmReviewProvider}
                    onChange={(e) => setLlmReviewProvider(e.target.value)}
                  >
                    <option value="grok">Grok (xAI)</option>
                    <option value="deepseek">DeepSeek</option>
                  </select>
                  <p className="settings-lead">
                    Multi-agent default: draft=DeepSeek, review=Grok. Review must not share the
                    author model (anti rubber-stamp). Revise repairs still use the draft provider.
                  </p>

                  <h3>DeepSeek</h3>
                  <label htmlFor="ds-model">Model</label>
                  <ProviderModelSelect
                    id="ds-model"
                    value={deepseekModel}
                    options={llm?.model_options?.deepseek ?? FALLBACK_MODEL_OPTIONS.deepseek}
                    onChange={setDeepseekModel}
                  />
                  <label htmlFor="ds-base">Base URL</label>
                  <input
                    id="ds-base"
                    value={deepseekBase}
                    onChange={(e) => setDeepseekBase(e.target.value)}
                    placeholder="https://api.deepseek.com"
                  />
                  <label htmlFor="ds-key">API key</label>
                  <PasswordField
                    id="ds-key"
                    autoComplete="off"
                    secretLabel="API key"
                    value={deepseekKey}
                    onChange={(e) => setDeepseekKey(e.target.value)}
                    placeholder={
                      llm?.deepseek.api_key_set ? '•••••••• (leave blank to keep)' : 'sk-...'
                    }
                  />

                  <h3>Grok (xAI)</h3>
                  <label htmlFor="gx-model">Model</label>
                  <ProviderModelSelect
                    id="gx-model"
                    value={grokModel}
                    options={llm?.model_options?.grok ?? FALLBACK_MODEL_OPTIONS.grok}
                    onChange={setGrokModel}
                  />
                  <label htmlFor="gx-base">Base URL</label>
                  <input
                    id="gx-base"
                    value={grokBase}
                    onChange={(e) => setGrokBase(e.target.value)}
                    placeholder="https://api.x.ai/v1"
                  />
                  <label htmlFor="gx-key">API key</label>
                  <PasswordField
                    id="gx-key"
                    autoComplete="off"
                    secretLabel="API key"
                    value={grokKey}
                    onChange={(e) => setGrokKey(e.target.value)}
                    placeholder={llm?.grok.api_key_set ? '•••••••• (leave blank to keep)' : 'xai-...'}
                  />

                  <h3>Adversarial review (SPEC-018)</h3>
                  <p className="settings-lead">
                    Deterministic IntentLock review always runs. This switch gates the optional LLM
                    Critic after synthesize/compose ({listeningReview?.key ?? 'listening.review_llm'}).
                  </p>
                  <label htmlFor="review-llm" className="checkbox-row">
                    <input
                      id="review-llm"
                      type="checkbox"
                      checked={reviewLlmEnabled}
                      onChange={(e) => setReviewLlmEnabled(e.target.checked)}
                    />{' '}
                    Enable LLM Intent Critic (listening.review_llm)
                  </label>

                  <h3>Ambient fallback (SPEC-006)</h3>
                  <p className="settings-lead">
                    When no work-matched open recording exists, choose platform fallback
                    ({ambientFallback?.key ?? 'listening.ambient_fallback_mode'}). Default is
                    official Embed (compliance-first). Stream uses optional server-side yt-dlp.
                  </p>
                  <label htmlFor="ambient-fallback-embed" className="checkbox-row">
                    <input
                      id="ambient-fallback-embed"
                      type="radio"
                      name="ambient-fallback"
                      checked={ambientFallbackMode === 'embed'}
                      onChange={() => setAmbientFallbackMode('embed')}
                    />{' '}
                    Official Embed (YouTube / Bilibili)
                  </label>
                  <label htmlFor="ambient-fallback-stream" className="checkbox-row">
                    <input
                      id="ambient-fallback-stream"
                      type="radio"
                      name="ambient-fallback"
                      checked={ambientFallbackMode === 'stream'}
                      onChange={() => setAmbientFallbackMode('stream')}
                    />{' '}
                    Server stream extract (ops opt-in; ToS / fragility risk)
                  </label>

                  <button type="submit" disabled={busy}>
                    {busy ? 'Saving…' : 'Save LLM settings'}
                  </button>
                </form>
                <div className="llm-test-actions">
                  <button
                    type="button"
                    className="refresh"
                    disabled={busy}
                    onClick={() => void onTestLlm(llmActive)}
                  >
                    Test active provider
                  </button>
                  <button
                    type="button"
                    className="refresh"
                    disabled={busy}
                    onClick={() => void onTestLlm('deepseek')}
                  >
                    Test DeepSeek
                  </button>
                  <button
                    type="button"
                    className="refresh"
                    disabled={busy}
                    onClick={() => void onTestLlm('grok')}
                  >
                    Test Grok
                  </button>
                </div>

                <h2 id="embed-title" style={{ marginTop: '2rem' }}>
                  Embeddings (RAG)
                </h2>
                <p className="settings-lead">
                  provider=<strong>{embed?.provider ?? '…'}</strong>
                  {' · '}
                  ready={embed?.ready ? 'yes' : 'no'}
                  {' · '}
                  FastEmbed {embed?.fastembed_available ? 'installed' : 'missing'}
                  {embed?.provider === 'openai_compatible'
                    ? ` · ${embed?.api_key_set ? 'key set' : 'key missing'}`
                    : ''}
                  {kbStats
                    ? ` · KB docs=${kbStats.documents} chunks=${kbStats.chunks}`
                    : ''}
                </p>
                <form className="auth-form" onSubmit={onSaveEmbed}>
                  <label htmlFor="emb-provider">Provider</label>
                  <select
                    id="emb-provider"
                    value={embedProvider}
                    onChange={(e) => {
                      const next = e.target.value
                      setEmbedProvider(next)
                      if (next === 'local') {
                        setEmbedModel(
                          embed?.local_default_model ||
                            'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                        )
                      } else if (embedModel.includes('sentence-transformers/') || embedModel.includes('BAAI/')) {
                        setEmbedModel('text-embedding-3-small')
                      }
                    }}
                  >
                    <option value="local">local (FastEmbed)</option>
                    <option value="openai_compatible">openai_compatible (remote)</option>
                  </select>
                  <label htmlFor="emb-model">Model</label>
                  <input
                    id="emb-model"
                    value={embedModel}
                    onChange={(e) => setEmbedModel(e.target.value)}
                    placeholder={
                      embedProvider === 'local'
                        ? 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
                        : 'text-embedding-3-small'
                    }
                  />
                  {embedProvider === 'openai_compatible' ? (
                    <>
                      <label htmlFor="emb-base">Base URL (OpenAI-compatible)</label>
                      <input
                        id="emb-base"
                        value={embedBase}
                        onChange={(e) => setEmbedBase(e.target.value)}
                        placeholder="https://api.openai.com/v1"
                      />
                      <label htmlFor="emb-key">API key</label>
                      <PasswordField
                        id="emb-key"
                        autoComplete="off"
                        secretLabel="API key"
                        value={embedKey}
                        onChange={(e) => setEmbedKey(e.target.value)}
                        placeholder={embed?.api_key_set ? '•••••••• (leave blank to keep)' : 'sk-...'}
                      />
                    </>
                  ) : (
                    <p className="settings-lead">
                      Local ONNX via{' '}
                      <a href="https://github.com/qdrant/fastembed" target="_blank" rel="noreferrer">
                        qdrant/fastembed
                      </a>
                      . No API key. First run downloads the model.
                    </p>
                  )}
                  <button type="submit" disabled={busy}>
                    {busy ? 'Saving…' : 'Save embeddings'}
                  </button>
                </form>
                <form className="auth-form" onSubmit={(e) => void onSaveWebResearch(e)}>
                  <h3>Web research → KB</h3>
                  <p className="settings-lead">
                    Cold-fill when local KB chambers are thin; refresh when past TTL even if rich
                    (merge, do not freeze). Wikipedia / DuckDuckGo (+ optional Brave) → optional
                    Agent Reach Jina deepen → LLM verify → KB upsert. No composer-specific branches.
                    Social cookies / Agent Reach CLI install remain denied.
                  </p>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={webEnabled}
                      onChange={(e) => setWebEnabled(e.target.checked)}
                    />
                    Enabled
                  </label>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={webPersistGlobal}
                      onChange={(e) => setWebPersistGlobal(e.target.checked)}
                    />
                    Persist to global KB (shared growth)
                  </label>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={webAgentReach}
                      onChange={(e) => setWebAgentReach(e.target.checked)}
                    />
                    Agent Reach enabler (Jina deepen of trusted URLs)
                  </label>
                  <label htmlFor="web-min-hits">Cold-fill: min RAG hits</label>
                  <input
                    id="web-min-hits"
                    type="number"
                    min={0}
                    value={webMinHits}
                    onChange={(e) => setWebMinHits(Number(e.target.value) || 0)}
                  />
                  <label htmlFor="web-min-rich">Cold-fill: min dossier richness</label>
                  <input
                    id="web-min-rich"
                    type="number"
                    min={0}
                    value={webMinRich}
                    onChange={(e) => setWebMinRich(Number(e.target.value) || 0)}
                  />
                  <label htmlFor="web-refresh-h">Refresh after hours (0 = always re-check)</label>
                  <input
                    id="web-refresh-h"
                    type="number"
                    min={0}
                    value={webRefreshHours}
                    onChange={(e) => setWebRefreshHours(Number(e.target.value) || 0)}
                  />
                  <label htmlFor="web-brave">Brave API key (optional)</label>
                  <PasswordField
                    id="web-brave"
                    autoComplete="off"
                    secretLabel="API key"
                    value={webBraveKey}
                    onChange={(e) => setWebBraveKey(e.target.value)}
                    placeholder={
                      webResearch?.brave_api_key_set ? '•••••••• (leave blank to keep)' : 'optional'
                    }
                  />
                  <button type="submit" disabled={busy}>
                    {busy ? 'Saving…' : 'Save web research'}
                  </button>
                </form>
                <p className="settings-lead">
                  Discogs personal token for <code>/discogs</code> lives under the{' '}
                  <button
                    type="button"
                    className="linkish"
                    onClick={() => setTab('discogs')}
                  >
                    Discogs
                  </button>{' '}
                  tab.
                </p>
              </section>
            ) : null}

            {tab === 'discogs' ? (
              <section className="settings" aria-labelledby="discogs-title">
                <div className="section-head">
                  <h2 id="discogs-title">Discogs token</h2>
                  <button
                    type="button"
                    className="refresh"
                    disabled={busy}
                    onClick={() => {
                      void (async () => {
                        try {
                          const dg = await fetchDiscogsConfig()
                          setDiscogs(dg)
                          setDiscogsEnabled(dg.enabled)
                          setDiscogsToken('')
                          setDiscogsClearToken(false)
                          setNotice(
                            dg.authenticated
                              ? `Discogs auth: ${dg.auth_source}`
                              : 'Discogs: no token (low-tier API)',
                          )
                        } catch (err) {
                          setError(err instanceof Error ? err.message : 'Discogs refresh failed')
                        }
                      })()
                    }}
                  >
                    Refresh
                  </button>
                </div>
                <form className="auth-form discogs-form" onSubmit={(e) => void onSaveDiscogs(e)}>
                  <p className="settings-lead">
                    Paste your Discogs <strong>personal user token</strong> here. Studio slash
                    command <code>/discogs #release-id</code> or catalog number{" "}
                    <code>/discogs #423-287-1</code> uses it for higher rate limits.
                    Create a token at{' '}
                    <a
                      href="https://www.discogs.com/settings/developers"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      discogs.com/settings/developers
                    </a>
                    . OPS token overrides env <code>AULOS_DISCOGS_TOKEN</code>.
                  </p>
                  <div className="discogs-status" role="status">
                    <span
                      className={`dot ${discogs?.authenticated ? 'ok-dot' : 'down-dot'}`}
                      aria-hidden="true"
                    />
                    <span>
                      {discogs == null
                        ? 'Could not load Discogs config — is API /v1/ops/discogs deployed?'
                        : discogs.enabled
                          ? discogs.authenticated
                            ? `Connected via ${discogs.auth_source}${
                                discogs.user_token_set ? ' (token saved in OPS)' : ''
                              }`
                            : 'Enabled — unauthenticated low tier (add a token below)'
                          : 'Connector disabled'}
                    </span>
                  </div>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={discogsEnabled}
                      onChange={(e) => setDiscogsEnabled(e.target.checked)}
                    />
                    Enable Discogs connector
                  </label>
                  <label htmlFor="discogs-token">Personal user token</label>
                  <PasswordField
                    id="discogs-token"
                    autoComplete="off"
                    secretLabel="token"
                    value={discogsToken}
                    disabled={discogsClearToken || !discogsEnabled}
                    onChange={(e) => setDiscogsToken(e.target.value)}
                    placeholder={
                      discogs?.user_token_set
                        ? '•••••••• (leave blank to keep current token)'
                        : 'Paste Discogs personal access token'
                    }
                  />
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={discogsClearToken}
                      disabled={!discogs?.user_token_set}
                      onChange={(e) => setDiscogsClearToken(e.target.checked)}
                    />
                    Clear stored OPS token
                  </label>
                  <button type="submit" disabled={busy}>
                    {busy ? 'Saving…' : 'Save Discogs token'}
                  </button>
                </form>
              </section>
            ) : null}

            {tab === 'knowledge' ? (
              <KnowledgePanel
                busy={busy}
                setBusy={setBusy}
                setError={setError}
                setNotice={setNotice}
                planeEnabled={kbStats?.plane_enabled}
                planeUrl={kbStats?.plane_url}
              />
            ) : null}

            {tab === 'tasks' ? (
              <TaskQueuePanel busy={busy} setBusy={setBusy} setError={setError} />
            ) : null}

            {tab === 'blog' ? (
              <DevBlogPanel
                busy={busy}
                setBusy={setBusy}
                setError={setError}
                setNotice={setNotice}
              />
            ) : null}

            {tab === 'skills' ? (
              <SkillsPanel
                busy={busy}
                setBusy={setBusy}
                setError={setError}
                setNotice={setNotice}
                skills={skills}
                setSkills={setSkills}
              />
            ) : null}

            {tab === 'guides' ? (
              <GuideQualityPanel
                busy={busy}
                setBusy={setBusy}
                setError={setError}
                setNotice={setNotice}
              />
            ) : null}

            {tab === 'mail' ? (
              <>
                <section className="settings" aria-labelledby="mailgun-title">
                  <h2 id="mailgun-title">Mailgun</h2>
                  <p className="settings-lead">
                    Effective provider: <strong>{mailgun?.provider_mode ?? '…'}</strong>
                    {' · '}
                    env=<code>{mailgun?.env_mail_provider ?? '…'}</code>
                    {' · '}
                    live ready={mailgun?.ready_for_live_send ? 'yes' : 'no'}
                    {mailgun?.api_key_set ? ' · API key set' : ' · API key missing'}
                  </p>
                  <form className="auth-form" onSubmit={onSaveMailgun}>
                    <label htmlFor="mg-domain">Mailgun sending domain</label>
                    <input
                      id="mg-domain"
                      value={domain}
                      onChange={(e) => setDomain(e.target.value)}
                      placeholder="mg.example.com"
                    />
                    <label htmlFor="mg-from">From email</label>
                    <input
                      id="mg-from"
                      type="email"
                      value={fromEmail}
                      onChange={(e) => setFromEmail(e.target.value)}
                      placeholder="noreply@example.com"
                    />
                    <label htmlFor="mg-region">API region</label>
                    <select
                      id="mg-region"
                      value={region}
                      onChange={(e) => setRegion(e.target.value)}
                    >
                      <option value="us">US (api.mailgun.net)</option>
                      <option value="eu">EU (api.eu.mailgun.net)</option>
                    </select>
                    <label htmlFor="mg-key">API key</label>
                    <PasswordField
                      id="mg-key"
                      autoComplete="off"
                      secretLabel="API key"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder={mailgun?.api_key_set ? '•••••••• (leave blank to keep)' : 'key-...'}
                    />
                    <label className="check" htmlFor="mg-enabled">
                      <input
                        id="mg-enabled"
                        type="checkbox"
                        checked={enabled}
                        onChange={(e) => setEnabled(e.target.checked)}
                      />
                      Enable Mailgun sending
                    </label>
                    <button type="submit" disabled={busy}>
                      {busy ? 'Saving…' : 'Save Mailgun settings'}
                    </button>
                  </form>
                  <form className="auth-form test-form" onSubmit={onTestMailgun}>
                    <h3>Test configuration</h3>
                    <label htmlFor="mg-test-to">Send test email to</label>
                    <input
                      id="mg-test-to"
                      type="email"
                      required
                      value={testToEmail}
                      onChange={(e) => setTestToEmail(e.target.value)}
                      placeholder="you@example.com"
                    />
                    <button type="submit" disabled={busy || !testToEmail.trim()}>
                      {busy ? 'Testing…' : 'Test Mailgun'}
                    </button>
                  </form>
                </section>

                <section className="deliveries" aria-labelledby="deliveries-title">
                  <div className="section-head">
                    <h2 id="deliveries-title">Email delivery log</h2>
                    <button
                      type="button"
                      className="refresh"
                      onClick={() => void refreshDeliveries()}
                      disabled={busy}
                    >
                      Refresh log
                    </button>
                  </div>
                  {deliveries.length === 0 ? (
                    <p className="settings-lead">No delivery attempts recorded yet.</p>
                  ) : (
                    <ul className="delivery-list">
                      {deliveries.map((row) => (
                        <li key={row.id} className={`delivery-row status-${row.status}`}>
                          <div>
                            <p className="svc-name">
                              {row.kind} · {row.status} · {row.provider}
                            </p>
                            <p className="svc-role">
                              to {row.to_email} · {formatDateTime(row.created_at)}
                            </p>
                            <p className="delivery-detail">{row.detail}</p>
                            {row.provider_message_id ? (
                              <p className="meta">msg id: {row.provider_message_id}</p>
                            ) : null}
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              </>
            ) : null}

            {tab === 'fleet' ? (
              <section className="fleet">
                <h2>Fleet</h2>
                <ul className="service-list">
                  {AULOS_SERVICES.map((svc, index) => (
                    <li
                      key={svc.id}
                      className="service-row"
                      style={{ animationDelay: `${0.05 * index}s` }}
                    >
                      <div>
                        <p className="svc-name">{svc.name}</p>
                        <p className="svc-role">{svc.role}</p>
                      </div>
                      <code className="svc-path">{svc.path}</code>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            {tab === 'dbha' ? (
              <DbHaPanel busy={busy} setBusy={setBusy} setError={setError} setNotice={setNotice} />
            ) : null}
        </OpsDashboardShell>
      )}
    </div>
  )
}

export default App
