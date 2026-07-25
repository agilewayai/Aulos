import { useCallback, useEffect, useState } from 'react'
import { AULOS_SERVICES, fetchGatewayHealth, type HealthResponse } from './api'
import './App.css'

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [updatedAt, setUpdatedAt] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchGatewayHealth()
      setHealth(data)
      setUpdatedAt(new Date().toLocaleTimeString())
    } catch (err) {
      setHealth(null)
      setError(err instanceof Error ? err.message : 'Health request failed')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
    const id = window.setInterval(() => void refresh(), 15000)
    return () => window.clearInterval(id)
  }, [refresh])

  const gatewayOk = health?.status === 'ok'

  return (
    <div className="shell">
      <div className="grid-bg" aria-hidden="true" />
      <header className="top">
        <div>
          <p className="brand">Aulos Ops</p>
          <p className="tagline">Admin and operations portal for the Aulos fleet</p>
        </div>
        <button type="button" className="refresh" onClick={() => void refresh()} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </header>

      <main className="stage">
        <section className="health" aria-live="polite">
          <h2>Gateway</h2>
          <div className={`status-line ${gatewayOk ? 'ok' : 'down'}`}>
            <span className="dot" />
            <span>
              {gatewayOk
                ? `${health?.service} ${health?.version} — healthy`
                : error ?? 'Gateway unreachable'}
            </span>
          </div>
          {updatedAt ? <p className="meta">Last check {updatedAt}</p> : null}
          {health?.backends ? (
            <ul className="backends">
              {Object.entries(health.backends).map(([name, state]) => (
                <li key={name}>
                  <code>{name}</code>
                  <span>{state}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </section>

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
      </main>
    </div>
  )
}

export default App
