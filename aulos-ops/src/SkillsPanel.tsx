import { useState } from 'react'
import type { FormEvent } from 'react'
import {
  fetchOpsGuideTrace,
  fetchSkills,
  probeSkills,
  toggleSkill,
  type SkillProbe,
  type SkillRow,
} from './api'

type GuideTrace = Awaited<ReturnType<typeof fetchOpsGuideTrace>>

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
  skills: SkillRow[]
  setSkills: (rows: SkillRow[] | ((prev: SkillRow[]) => SkillRow[])) => void
}

export function SkillsPanel({
  busy,
  setBusy,
  setError,
  setNotice,
  skills,
  setSkills,
}: Props) {
  const [skillProbeMsg, setSkillProbeMsg] = useState(
    "I'm listening to Bach Goldberg Variations",
  )
  const [skillProbe, setSkillProbe] = useState<SkillProbe | null>(null)
  const [traceGuideId, setTraceGuideId] = useState('')
  const [guideTrace, setGuideTrace] = useState<GuideTrace | null>(null)

  async function onProbeSkills(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const result = await probeSkills(skillProbeMsg.trim())
      setSkillProbe(result)
      setNotice(
        `Skill probe: ${result.work_title} · score ${result.eval_score} · pass=${result.eval_pass}`,
      )
      setSkills(await fetchSkills())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Skill probe failed')
    } finally {
      setBusy(false)
    }
  }

  async function onFetchGuideTrace(event: FormEvent) {
    event.preventDefault()
    const id = Number(traceGuideId.trim())
    if (!Number.isFinite(id) || id <= 0) {
      setError('Enter a valid listening guide id')
      return
    }
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const result = await fetchOpsGuideTrace(id)
      setGuideTrace(result)
      const n = result.chain_trace?.deviations?.length || 0
      setNotice(
        n > 0
          ? `Guide #${id} trace: ${n} deviation(s)`
          : `Guide #${id} trace loaded (no deviations)`,
      )
    } catch (err) {
      setGuideTrace(null)
      setError(err instanceof Error ? err.message : 'Trace fetch failed')
    } finally {
      setBusy(false)
    }
  }

  async function onToggleSkill(row: SkillRow) {
    setBusy(true)
    setError(null)
    try {
      const updated = await toggleSkill(row.id, !row.enabled)
      setSkills((prev) => prev.map((s) => (s.id === updated.id ? updated : s)))
      setNotice(`${updated.id} ${updated.enabled ? 'enabled' : 'disabled'}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Skill toggle failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="settings skills" aria-labelledby="skills-title">
      <div className="section-head">
        <h2 id="skills-title">Aulos skills</h2>
        <button
          type="button"
          className="refresh"
          disabled={busy}
          onClick={() => void fetchSkills().then(setSkills)}
        >
          Refresh
        </button>
      </div>
      <p className="settings-lead">
        Domain-runtime packs power listening 导赏. Toggle availability and probe the full chain.
      </p>
      <ul className="user-list">
        {skills.map((row) => (
          <li key={row.id} className={`user-row ${row.enabled ? '' : 'inactive'}`}>
            <div className="user-main">
              <p className="svc-name">
                {row.name}
                <span className="user-id">
                  {row.id}@{row.version}
                </span>
              </p>
              <p className="svc-role">
                {row.layer}
                {row.runtime ? ` · runtime=${row.runtime}` : ''}
              </p>
              <p className="meta">{row.summary}</p>
              {row.triggers.length ? (
                <p className="meta">triggers: {row.triggers.join(', ')}</p>
              ) : null}
            </div>
            <div className="user-actions">
              <button
                type="button"
                className="refresh"
                disabled={busy}
                onClick={() => void onToggleSkill(row)}
              >
                {row.enabled ? 'Disable' : 'Enable'}
              </button>
            </div>
          </li>
        ))}
      </ul>
      <form className="auth-form test-form" onSubmit={(e) => void onProbeSkills(e)}>
        <h3>Probe listening chain</h3>
        <label htmlFor="skill-probe">Message</label>
        <input
          id="skill-probe"
          value={skillProbeMsg}
          onChange={(e) => setSkillProbeMsg(e.target.value)}
        />
        <button type="submit" disabled={busy || !skillProbeMsg.trim()}>
          {busy ? 'Probing…' : 'Run skill probe'}
        </button>
      </form>
      {skillProbe ? (
        <div className="delivery-row" style={{ marginTop: '0.85rem' }}>
          <p className="svc-name">
            {skillProbe.work_title} · score {skillProbe.eval_score} · pass=
            {String(skillProbe.eval_pass)}
          </p>
          <p className="svc-role">{skillProbe.summary}</p>
          <p className="meta">skills: {Object.keys(skillProbe.skill_versions).join(', ')}</p>
          <p className="delivery-detail">
            {skillProbe.steps.map((s) => `${String(s.id)}:${String(s.skill_id || '')}`).join(' → ')}
          </p>
        </div>
      ) : null}
      <form className="auth-form test-form" onSubmit={(e) => void onFetchGuideTrace(e)}>
        <h3>Listening chain trace (复盘)</h3>
        <label htmlFor="guide-trace-id">Guide id</label>
        <input
          id="guide-trace-id"
          value={traceGuideId}
          onChange={(e) => setTraceGuideId(e.target.value)}
          placeholder="e.g. 42"
        />
        <button type="submit" disabled={busy || !traceGuideId.trim()}>
          {busy ? 'Loading…' : 'Load diagnostic log'}
        </button>
      </form>
      {guideTrace?.chain_trace ? (
        <div className="delivery-row" style={{ marginTop: '0.85rem' }}>
          <p className="svc-name">
            #{guideTrace.guide_id} · {guideTrace.work_title} · {guideTrace.composer}
          </p>
          <p className="meta">
            deviations: {guideTrace.chain_trace.deviations?.length || 0} · milestones:{' '}
            {guideTrace.chain_trace.milestones?.length || 0}
          </p>
          {(guideTrace.chain_trace.deviations || []).map((d, i) => (
            <p key={`${d.code}-${i}`} className="delivery-detail">
              ⚠ {d.code}
              {d.at_milestone ? ` @ ${d.at_milestone}` : ''}: {d.summary}
            </p>
          ))}
          <p className="delivery-detail">
            {(guideTrace.chain_trace.milestones || []).map((m) => `${m.id}:${m.status}`).join(' → ')}
          </p>
        </div>
      ) : null}
    </section>
  )
}
