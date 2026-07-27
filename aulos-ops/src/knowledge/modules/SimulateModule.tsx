import { useState, type FormEvent } from 'react'
import { knowledgeRetrieveLab } from '../../api'
import { RETRIEVE_PRESETS } from '../constants'

type Hit = { title: string; score: number; text: string; aulos_work_id?: string }

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
}

export function SimulateModule({ busy, setBusy, setError }: Props) {
  const [labQuery, setLabQuery] = useState('Bach cello suites')
  const [labWorkId, setLabWorkId] = useState('bach.cello-suites.bwv-1007-1012')
  const [labComposerId, setLabComposerId] = useState('johann-sebastian-bach')
  const [hits, setHits] = useState<Hit[]>([])
  const [lastMs, setLastMs] = useState<number | null>(null)

  const runRetrieve = async (query: string, workId: string, composerId: string) => {
    setBusy(true)
    setError(null)
    const t0 = performance.now()
    try {
      const r = await knowledgeRetrieveLab(query, workId, composerId)
      setHits(r.hits || [])
      setLastMs(Math.round(performance.now() - t0))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'retrieve failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="kb-module">
      <header className="kb-module-head">
        <div>
          <h3>RAG simulate</h3>
          <p className="mute">
            Run retrieve against the published corpus — test identity filters and spot bleed before
            shipping to listeners.
          </p>
        </div>
      </header>

      <section className="kb-panel-card">
        <h4>Presets</h4>
        <div className="kb-preset-row">
          {RETRIEVE_PRESETS.map((p) => (
            <button
              key={p.label}
              type="button"
              className="ghost"
              disabled={busy}
              onClick={() => {
                setLabQuery(p.query)
                setLabWorkId(p.workId)
                setLabComposerId(p.composerId)
                void runRetrieve(p.query, p.workId, p.composerId)
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
      </section>

      <form
        className="stack kb-sim-form"
        onSubmit={(e: FormEvent) => {
          e.preventDefault()
          void runRetrieve(labQuery, labWorkId, labComposerId)
        }}
      >
        <label>
          Query
          <input value={labQuery} onChange={(e) => setLabQuery(e.target.value)} disabled={busy} />
        </label>
        <label>
          work_id filter
          <input value={labWorkId} onChange={(e) => setLabWorkId(e.target.value)} disabled={busy} />
        </label>
        <label>
          composer_id filter
          <input
            value={labComposerId}
            onChange={(e) => setLabComposerId(e.target.value)}
            disabled={busy}
          />
        </label>
        <button type="submit" disabled={busy}>
          Simulate retrieve
        </button>
      </form>

      {lastMs != null ? (
        <p className="mute">
          {hits.length} hit(s) · {lastMs} ms · only <strong>published</strong> chunks returned
        </p>
      ) : null}

      <ul className="plain kb-sim-hits">
        {hits.map((h, i) => (
          <li key={`${h.title}-${i}`} className="kb-sim-hit">
            <div className="kb-sim-hit-head">
              <span className="kb-score">{h.score.toFixed(3)}</span>
              <strong>{h.title}</strong>
              {h.aulos_work_id ? (
                <code className="kb-work-id">{h.aulos_work_id}</code>
              ) : (
                <span className="warn">no work_id</span>
              )}
            </div>
            <p className="mute">{h.text.slice(0, 320)}{h.text.length > 320 ? '…' : ''}</p>
          </li>
        ))}
      </ul>
    </div>
  )
}
