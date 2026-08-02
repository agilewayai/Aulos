import { useEffect, useMemo, useState, type FormEvent } from 'react'
import {
  fetchAmbientFallbackConfig,
  fetchListeningReviewConfig,
  fetchLlmConfig,
  testLlmProvider,
  updateAmbientFallbackConfig,
  updateListeningReviewConfig,
  updateLlmConfig,
  type AmbientFallbackConfig,
  type ListeningReviewConfig,
  type LlmConfig,
  type LlmModelOption,
} from './api'
import { PasswordField } from './PasswordField'

const FALLBACK_MODEL_OPTIONS: Record<string, LlmModelOption[]> = {
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
  aicodemirror: [
    { id: 'gpt-5.5', label: 'gpt-5.5 (Codex relay)' },
    { id: 'gpt-5.4', label: 'gpt-5.4' },
    { id: 'gpt-5.3-codex', label: 'gpt-5.3-codex' },
    { id: 'gpt-5.2', label: 'gpt-5.2' },
    { id: 'gpt-5.1', label: 'gpt-5.1' },
    { id: 'gpt-5-codex', label: 'gpt-5-codex' },
    { id: 'o3', label: 'o3' },
    { id: 'o4-mini', label: 'o4-mini' },
  ],
}

const LIVE_PROVIDER_OPTIONS = [
  { id: 'deepseek', label: 'DeepSeek' },
  { id: 'grok', label: 'Grok (xAI)' },
  { id: 'aicodemirror', label: 'AI Code Mirror (Codex)' },
] as const

const CHAT_PROVIDER_OPTIONS = [
  { id: 'fake', label: 'fake (offline echo)' },
  ...LIVE_PROVIDER_OPTIONS,
] as const

type ProviderId = 'deepseek' | 'grok' | 'aicodemirror'

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
  onAfterChange?: () => void | Promise<void>
  /** Initial payloads from parent load; panel re-syncs when these change. */
  initialLlm: LlmConfig | null
  initialReview: ListeningReviewConfig | null
  initialAmbient: AmbientFallbackConfig | null
}

function StatusPill({
  ok,
  okLabel,
  badLabel,
}: {
  ok: boolean
  okLabel: string
  badLabel: string
}) {
  return (
    <span className={`llm-pill ${ok ? 'is-ok' : 'is-warn'}`} title={ok ? okLabel : badLabel}>
      <span className="llm-pill-dot" aria-hidden />
      <span>{ok ? okLabel : badLabel}</span>
    </span>
  )
}

function ProviderModelSelect({
  id,
  value,
  options,
  onChange,
}: {
  id: string
  value: string
  options: LlmModelOption[]
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
          if (next === '__custom__') return
          onChange(next)
        }}
        aria-label="Model"
      >
        {options.map((o) => (
          <option key={o.id} value={o.id}>
            {o.label}
          </option>
        ))}
        <option value="__custom__">Custom model id…</option>
      </select>
      {!known ? (
        <input
          aria-label="Custom model id"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="custom-model-id"
        />
      ) : null}
    </div>
  )
}

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      className={`llm-chevron-icon ${open ? 'is-open' : ''}`}
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      aria-hidden
    >
      <path d="m9 18 6-6-6-6" />
    </svg>
  )
}

function providerLabel(id: string): string {
  if (id === 'fake') return 'fake'
  const hit = LIVE_PROVIDER_OPTIONS.find((p) => p.id === id)
  return hit?.label ?? id
}

export function LlmSettingsPanel({
  busy,
  setBusy,
  setError,
  setNotice,
  onAfterChange,
  initialLlm,
  initialReview,
  initialAmbient,
}: Props) {
  const [llm, setLlm] = useState<LlmConfig | null>(initialLlm)
  const [listeningReview, setListeningReview] = useState(initialReview)
  const [ambientFallback, setAmbientFallback] = useState(initialAmbient)

  const [llmActive, setLlmActive] = useState('fake')
  const [llmDraftProvider, setLlmDraftProvider] = useState('deepseek')
  const [llmReviewProvider, setLlmReviewProvider] = useState('grok')

  const [deepseekKey, setDeepseekKey] = useState('')
  const [deepseekModel, setDeepseekModel] = useState('deepseek-chat')
  const [deepseekBase, setDeepseekBase] = useState('https://api.deepseek.com')
  const [grokKey, setGrokKey] = useState('')
  const [grokModel, setGrokModel] = useState('grok-3-mini')
  const [grokBase, setGrokBase] = useState('https://api.x.ai/v1')
  const [acmKey, setAcmKey] = useState('')
  const [acmModel, setAcmModel] = useState('gpt-5.5')
  const [acmBase, setAcmBase] = useState(
    'https://api.aicodemirror.ai/api/codex/backend-api/codex',
  )
  const [acmReasoning, setAcmReasoning] = useState('xhigh')

  const [reviewLlmEnabled, setReviewLlmEnabled] = useState(false)
  const [ambientFallbackMode, setAmbientFallbackMode] = useState('embed')

  const [expanded, setExpanded] = useState<Record<ProviderId, boolean>>({
    deepseek: true,
    grok: false,
    aicodemirror: false,
  })
  const [testingProvider, setTestingProvider] = useState<string | null>(null)

  useEffect(() => {
    setLlm(initialLlm)
    if (!initialLlm) return
    setLlmActive(initialLlm.active_provider)
    setLlmDraftProvider(initialLlm.draft_provider || 'deepseek')
    setLlmReviewProvider(initialLlm.review_provider || 'grok')
    setDeepseekModel(initialLlm.deepseek.model)
    setDeepseekBase(initialLlm.deepseek.base_url)
    setGrokModel(initialLlm.grok.model)
    setGrokBase(initialLlm.grok.base_url)
    if (initialLlm.aicodemirror) {
      setAcmModel(initialLlm.aicodemirror.model || 'gpt-5.5')
      setAcmBase(
        initialLlm.aicodemirror.base_url ||
          'https://api.aicodemirror.ai/api/codex/backend-api/codex',
      )
      setAcmReasoning(initialLlm.aicodemirror.reasoning_effort || 'xhigh')
    }
    const roles = new Set(
      [
        initialLlm.active_provider,
        initialLlm.draft_provider,
        initialLlm.review_provider,
      ].filter(Boolean),
    )
    setExpanded({
      deepseek: roles.has('deepseek') || !roles.size,
      grok: roles.has('grok'),
      aicodemirror: roles.has('aicodemirror'),
    })
  }, [initialLlm])

  useEffect(() => {
    setListeningReview(initialReview)
    setReviewLlmEnabled(Boolean(initialReview?.enabled))
  }, [initialReview])

  useEffect(() => {
    setAmbientFallback(initialAmbient)
    setAmbientFallbackMode(initialAmbient?.mode || 'embed')
  }, [initialAmbient])

  const sameDraftReview = llmDraftProvider === llmReviewProvider

  const providerReady = useMemo(() => {
    return {
      deepseek: Boolean(llm?.deepseek.ready),
      grok: Boolean(llm?.grok.ready),
      aicodemirror: Boolean(llm?.aicodemirror?.ready),
      deepseekKey: Boolean(llm?.deepseek.api_key_set),
      grokKey: Boolean(llm?.grok.api_key_set),
      acmKey: Boolean(llm?.aicodemirror?.api_key_set),
    }
  }, [llm])

  function toggleProvider(id: ProviderId) {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  function expandUsed() {
    setExpanded({
      deepseek:
        llmActive === 'deepseek' ||
        llmDraftProvider === 'deepseek' ||
        llmReviewProvider === 'deepseek',
      grok:
        llmActive === 'grok' ||
        llmDraftProvider === 'grok' ||
        llmReviewProvider === 'grok',
      aicodemirror:
        llmActive === 'aicodemirror' ||
        llmDraftProvider === 'aicodemirror' ||
        llmReviewProvider === 'aicodemirror',
    })
  }

  async function persistDraft() {
    return updateLlmConfig({
      active_provider: llmActive,
      draft_provider: llmDraftProvider,
      review_provider: llmReviewProvider,
      deepseek_api_key: deepseekKey.trim() || undefined,
      deepseek_model: deepseekModel.trim(),
      deepseek_base_url: deepseekBase.trim(),
      grok_api_key: grokKey.trim() || undefined,
      grok_model: grokModel.trim(),
      grok_base_url: grokBase.trim(),
      aicodemirror_api_key: acmKey.trim() || undefined,
      aicodemirror_model: acmModel.trim(),
      aicodemirror_base_url: acmBase.trim(),
      aicodemirror_reasoning_effort: acmReasoning.trim() || undefined,
    })
  }

  async function onSave(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const cfg = await persistDraft()
      setLlm(cfg)
      setDeepseekKey('')
      setGrokKey('')
      setAcmKey('')
      const rev = await updateListeningReviewConfig({ enabled: reviewLlmEnabled })
      setListeningReview(rev)
      const amb = await updateAmbientFallbackConfig({ mode: ambientFallbackMode })
      setAmbientFallback(amb)
      setNotice(
        `LLM saved · chat=${cfg.active_provider} · draft=${cfg.draft_provider}/${cfg.ready_for_draft ? 'ready' : 'not ready'} · review=${cfg.review_provider}/${cfg.ready_for_review ? 'ready' : 'not ready'} · critic=${rev.enabled ? 'on' : 'off'} · ambient=${amb.mode}`,
      )
      await onAfterChange?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'LLM save failed')
    } finally {
      setBusy(false)
    }
  }

  async function onTest(provider?: string) {
    setBusy(true)
    setTestingProvider(provider || llmActive)
    setError(null)
    setNotice(null)
    try {
      const cfg = await persistDraft()
      setLlm(cfg)
      const result = await testLlmProvider(provider)
      setNotice(result.detail)
      const fresh = await fetchLlmConfig()
      setLlm(fresh)
      setDeepseekKey('')
      setGrokKey('')
      setAcmKey('')
      await onAfterChange?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'LLM test failed')
    } finally {
      setTestingProvider(null)
      setBusy(false)
    }
  }

  async function reloadFromServer() {
    setBusy(true)
    setError(null)
    try {
      const [cfg, rev, amb] = await Promise.all([
        fetchLlmConfig(),
        fetchListeningReviewConfig(),
        fetchAmbientFallbackConfig(),
      ])
      setLlm(cfg)
      setListeningReview(rev)
      setAmbientFallback(amb)
      setNotice('LLM settings reloaded from server.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reload failed')
    } finally {
      setBusy(false)
    }
  }

  const roleReady = (provider: string) => {
    if (provider === 'fake') return true
    if (provider === 'deepseek') return providerReady.deepseek
    if (provider === 'grok') return providerReady.grok
    if (provider === 'aicodemirror') return providerReady.aicodemirror
    return false
  }

  return (
    <section className="settings llm llm-console" aria-labelledby="llm-title">
      <header className="llm-console-head">
        <div>
          <h2 id="llm-title">LLM providers</h2>
          <p className="settings-lead llm-console-lead">
            Configure chat, multi-agent draft/review, and listening critic settings. Keys stay on
            the server — leave blank to keep an existing secret.
          </p>
        </div>
        <div className="llm-console-head-actions">
          <button
            type="button"
            className="refresh"
            disabled={busy}
            onClick={() => void reloadFromServer()}
          >
            Reload
          </button>
          <button type="button" className="refresh" disabled={busy} onClick={expandUsed}>
            Expand in-use
          </button>
        </div>
      </header>

      <div className="llm-status-grid" role="status" aria-live="polite">
        <article className="llm-status-card">
          <p className="llm-status-kicker">Chat</p>
          <p className="llm-status-value">{providerLabel(llm?.active_provider || llmActive)}</p>
          <StatusPill
            ok={Boolean(llm?.ready_for_live) || llmActive === 'fake'}
            okLabel={llmActive === 'fake' ? 'offline' : 'live ready'}
            badLabel="not ready"
          />
        </article>
        <article className="llm-status-card">
          <p className="llm-status-kicker">Draft / 初稿</p>
          <p className="llm-status-value">
            {providerLabel(llm?.draft_provider || llmDraftProvider)}
          </p>
          <StatusPill
            ok={Boolean(llm?.ready_for_draft)}
            okLabel="ready"
            badLabel="needs key"
          />
        </article>
        <article className="llm-status-card">
          <p className="llm-status-kicker">Review / 审稿</p>
          <p className="llm-status-value">
            {providerLabel(llm?.review_provider || llmReviewProvider)}
          </p>
          <StatusPill
            ok={Boolean(llm?.ready_for_review)}
            okLabel="ready"
            badLabel="needs key"
          />
        </article>
        <article className="llm-status-card llm-status-card-keys">
          <p className="llm-status-kicker">Keys</p>
          <ul className="llm-key-list">
            <li>
              <span>DeepSeek</span>
              <StatusPill
                ok={providerReady.deepseekKey}
                okLabel="set"
                badLabel="missing"
              />
            </li>
            <li>
              <span>Grok</span>
              <StatusPill ok={providerReady.grokKey} okLabel="set" badLabel="missing" />
            </li>
            <li>
              <span>AI Code Mirror</span>
              <StatusPill ok={providerReady.acmKey} okLabel="set" badLabel="missing" />
            </li>
          </ul>
        </article>
      </div>

      <form className="llm-form" onSubmit={onSave}>
        <section className="llm-block" aria-labelledby="llm-roles-title">
          <div className="llm-block-head">
            <h3 id="llm-roles-title">Role routing</h3>
            <p>
              Chat uses Active. Listening atelier uses Draft for authoring and Review for the
              adversarial critic — keep them on different providers when possible.
            </p>
          </div>

          {sameDraftReview ? (
            <p className="llm-inline-warn" role="status">
              Draft and Review currently share <strong>{providerLabel(llmDraftProvider)}</strong>.
              That weakens multi-agent review (rubber-stamp risk).
            </p>
          ) : null}

          <div className="llm-role-grid">
            <label className="llm-role-card" htmlFor="llm-active">
              <span className="llm-role-title">
                Active (chat)
                <StatusPill
                  ok={roleReady(llmActive)}
                  okLabel={llmActive === 'fake' ? 'offline' : 'ready'}
                  badLabel="not ready"
                />
              </span>
              <select
                id="llm-active"
                value={llmActive}
                onChange={(e) => setLlmActive(e.target.value)}
              >
                {CHAT_PROVIDER_OPTIONS.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.label}
                  </option>
                ))}
              </select>
              <span className="llm-role-hint">Operator chat & general live calls</span>
            </label>

            <label className="llm-role-card" htmlFor="llm-draft">
              <span className="llm-role-title">
                Draft / author
                <StatusPill
                  ok={roleReady(llmDraftProvider)}
                  okLabel="ready"
                  badLabel="not ready"
                />
              </span>
              <select
                id="llm-draft"
                value={llmDraftProvider}
                onChange={(e) => setLlmDraftProvider(e.target.value)}
              >
                {LIVE_PROVIDER_OPTIONS.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.label}
                  </option>
                ))}
              </select>
              <span className="llm-role-hint">Guide enrich · revise repairs</span>
            </label>

            <label className="llm-role-card" htmlFor="llm-review">
              <span className="llm-role-title">
                Review / critic
                <StatusPill
                  ok={roleReady(llmReviewProvider)}
                  okLabel="ready"
                  badLabel="not ready"
                />
              </span>
              <select
                id="llm-review"
                value={llmReviewProvider}
                onChange={(e) => setLlmReviewProvider(e.target.value)}
              >
                {LIVE_PROVIDER_OPTIONS.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.label}
                  </option>
                ))}
              </select>
              <span className="llm-role-hint">
                Intent Critic · external review — may use AI Code Mirror Codex
                (Responses)
              </span>
            </label>
          </div>
        </section>

        <section className="llm-block" aria-labelledby="llm-providers-title">
          <div className="llm-block-head">
            <h3 id="llm-providers-title">Provider credentials</h3>
            <p>Expand a provider to edit model, base URL, and API key. Test before promoting to a role.</p>
          </div>

          <div className="llm-provider-stack">
            {/* DeepSeek */}
            <article
              className={`llm-provider-card ${expanded.deepseek ? 'is-open' : ''}`}
              data-provider="deepseek"
            >
              <div className="llm-provider-toolbar">
                <button
                  type="button"
                  className="llm-provider-toggle"
                  aria-expanded={expanded.deepseek}
                  onClick={() => toggleProvider('deepseek')}
                >
                  <span className="llm-provider-name">DeepSeek</span>
                  <span className="llm-chip">chat</span>
                  <StatusPill
                    ok={providerReady.deepseek}
                    okLabel="ready"
                    badLabel="needs key"
                  />
                  <Chevron open={expanded.deepseek} />
                </button>
                <button
                  type="button"
                  className="refresh llm-provider-test"
                  disabled={busy}
                  onClick={() => void onTest('deepseek')}
                >
                  {testingProvider === 'deepseek' ? 'Testing…' : 'Test'}
                </button>
              </div>
              {expanded.deepseek ? (
                <div className="llm-provider-body">
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
                    autoComplete="off"
                  />
                  <label htmlFor="ds-key">API key</label>
                  <PasswordField
                    id="ds-key"
                    autoComplete="off"
                    secretLabel="DeepSeek API key"
                    value={deepseekKey}
                    onChange={(e) => setDeepseekKey(e.target.value)}
                    placeholder={
                      llm?.deepseek.api_key_set
                        ? '•••••••• (leave blank to keep)'
                        : 'sk-...'
                    }
                  />
                </div>
              ) : null}
            </article>

            {/* Grok */}
            <article
              className={`llm-provider-card ${expanded.grok ? 'is-open' : ''}`}
              data-provider="grok"
            >
              <div className="llm-provider-toolbar">
                <button
                  type="button"
                  className="llm-provider-toggle"
                  aria-expanded={expanded.grok}
                  onClick={() => toggleProvider('grok')}
                >
                  <span className="llm-provider-name">Grok (xAI)</span>
                  <span className="llm-chip">chat</span>
                  <StatusPill ok={providerReady.grok} okLabel="ready" badLabel="needs key" />
                  <Chevron open={expanded.grok} />
                </button>
                <button
                  type="button"
                  className="refresh llm-provider-test"
                  disabled={busy}
                  onClick={() => void onTest('grok')}
                >
                  {testingProvider === 'grok' ? 'Testing…' : 'Test'}
                </button>
              </div>
              {expanded.grok ? (
                <div className="llm-provider-body">
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
                    autoComplete="off"
                  />
                  <label htmlFor="gx-key">API key</label>
                  <PasswordField
                    id="gx-key"
                    autoComplete="off"
                    secretLabel="Grok API key"
                    value={grokKey}
                    onChange={(e) => setGrokKey(e.target.value)}
                    placeholder={
                      llm?.grok.api_key_set ? '•••••••• (leave blank to keep)' : 'xai-...'
                    }
                  />
                </div>
              ) : null}
            </article>

            {/* AI Code Mirror */}
            <article
              className={`llm-provider-card ${expanded.aicodemirror ? 'is-open' : ''}`}
              data-provider="aicodemirror"
            >
              <div className="llm-provider-toolbar">
                <button
                  type="button"
                  className="llm-provider-toggle"
                  aria-expanded={expanded.aicodemirror}
                  onClick={() => toggleProvider('aicodemirror')}
                >
                  <span className="llm-provider-name">AI Code Mirror</span>
                  <span className="llm-chip llm-chip-accent">responses · Codex</span>
                  <StatusPill
                    ok={providerReady.aicodemirror}
                    okLabel="ready"
                    badLabel="needs key"
                  />
                  <Chevron open={expanded.aicodemirror} />
                </button>
                <button
                  type="button"
                  className="refresh llm-provider-test"
                  disabled={busy}
                  onClick={() => void onTest('aicodemirror')}
                >
                  {testingProvider === 'aicodemirror' ? 'Testing…' : 'Test'}
                </button>
              </div>
              {expanded.aicodemirror ? (
                <div className="llm-provider-body">
                  <p className="llm-provider-note">
                    Codex Responses mid-relay (<code>wire_api=responses</code>). Uses{' '}
                    <code>/responses</code>, not Chat Completions.
                  </p>
                  <label htmlFor="acm-model">Model</label>
                  <ProviderModelSelect
                    id="acm-model"
                    value={acmModel}
                    options={
                      llm?.model_options?.aicodemirror ?? FALLBACK_MODEL_OPTIONS.aicodemirror
                    }
                    onChange={setAcmModel}
                  />
                  <label htmlFor="acm-base">Base URL</label>
                  <input
                    id="acm-base"
                    value={acmBase}
                    onChange={(e) => setAcmBase(e.target.value)}
                    placeholder="https://api.aicodemirror.ai/api/codex/backend-api/codex"
                    autoComplete="off"
                    spellCheck={false}
                  />
                  <label htmlFor="acm-reason">Reasoning effort</label>
                  <select
                    id="acm-reason"
                    value={acmReasoning}
                    onChange={(e) => setAcmReasoning(e.target.value)}
                  >
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                    <option value="xhigh">xhigh</option>
                  </select>
                  <label htmlFor="acm-key">API key</label>
                  <PasswordField
                    id="acm-key"
                    autoComplete="off"
                    secretLabel="AI Code Mirror API key"
                    value={acmKey}
                    onChange={(e) => setAcmKey(e.target.value)}
                    placeholder={
                      llm?.aicodemirror?.api_key_set
                        ? '•••••••• (leave blank to keep)'
                        : 'sk-...'
                    }
                  />
                </div>
              ) : null}
            </article>
          </div>
        </section>

        <section className="llm-block" aria-labelledby="llm-listening-title">
          <div className="llm-block-head">
            <h3 id="llm-listening-title">Listening options</h3>
            <p>Saved together with LLM settings. These gate atelier behavior after compose.</p>
          </div>

          <div className="llm-option-grid">
            <fieldset className="llm-option-card">
              <legend>Adversarial review (SPEC-018)</legend>
              <p className="llm-option-copy">
                Deterministic IntentLock always runs. This switch enables the optional LLM Critic
                after synthesize/compose (
                {listeningReview?.key ?? 'listening.review_llm'}).
              </p>
              <label htmlFor="review-llm" className="checkbox-row llm-switch-row">
                <input
                  id="review-llm"
                  type="checkbox"
                  checked={reviewLlmEnabled}
                  onChange={(e) => setReviewLlmEnabled(e.target.checked)}
                />
                <span>
                  Enable LLM Intent Critic
                  <small>Uses the Review provider above</small>
                </span>
              </label>
            </fieldset>

            <fieldset className="llm-option-card">
              <legend>Ambient fallback (SPEC-006)</legend>
              <p className="llm-option-copy">
                When no work-matched recording exists (
                {ambientFallback?.key ?? 'listening.ambient_fallback_mode'}). Default is official
                Embed.
              </p>
              <div className="llm-radio-stack" role="radiogroup" aria-label="Ambient fallback mode">
                <label htmlFor="ambient-fallback-embed" className="checkbox-row llm-switch-row">
                  <input
                    id="ambient-fallback-embed"
                    type="radio"
                    name="ambient-fallback"
                    checked={ambientFallbackMode === 'embed'}
                    onChange={() => setAmbientFallbackMode('embed')}
                  />
                  <span>
                    Official Embed
                    <small>YouTube / Bilibili — compliance-first</small>
                  </span>
                </label>
                <label htmlFor="ambient-fallback-stream" className="checkbox-row llm-switch-row">
                  <input
                    id="ambient-fallback-stream"
                    type="radio"
                    name="ambient-fallback"
                    checked={ambientFallbackMode === 'stream'}
                    onChange={() => setAmbientFallbackMode('stream')}
                  />
                  <span>
                    Server stream extract
                    <small>Ops opt-in · ToS / fragility risk</small>
                  </span>
                </label>
              </div>
            </fieldset>
          </div>
        </section>

        <div className="llm-action-bar">
          <div className="llm-action-bar-main">
            <button type="submit" className="llm-save-btn" disabled={busy}>
              {busy && !testingProvider ? 'Saving…' : 'Save LLM settings'}
            </button>
            <button
              type="button"
              className="refresh"
              disabled={busy}
              onClick={() => void onTest(llmActive)}
            >
              {testingProvider === llmActive ? 'Testing…' : 'Test active'}
            </button>
          </div>
          <p className="llm-action-hint">
            Save writes roles, credentials, critic switch, and ambient mode in one pass.
          </p>
        </div>
      </form>
    </section>
  )
}
