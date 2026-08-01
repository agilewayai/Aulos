import { useCallback, useEffect, useState } from 'react'
import {
  fetchKnowledgeBenchmarkDashboard,
  runKnowledgeBenchmarkAndWait,
  type KnowledgeBenchmarkDashboard,
} from '../../api'
import { BenchmarkDashboardReport } from '../components/BenchmarkDashboardReport'
import type { KnowledgeModuleId } from '../types'

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
  onNavigate: (module: KnowledgeModuleId) => void
}

export function ReportModule({ busy, setBusy, setError, setNotice, onNavigate }: Props) {
  const [dashboard, setDashboard] = useState<KnowledgeBenchmarkDashboard | null>(null)

  const load = useCallback(async () => {
    setError(null)
    const data = await fetchKnowledgeBenchmarkDashboard()
    setDashboard(data)
  }, [setError])

  useEffect(() => {
    void load().catch((err) => {
      setError(err instanceof Error ? err.message : 'dashboard load failed')
    })
  }, [load, setError])

  const onRun = async () => {
    setBusy(true)
    setError(null)
    try {
      const r = await runKnowledgeBenchmarkAndWait()
      setNotice(`Benchmark run #${r.id}: ${r.overall_score} (${r.grade})`)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'benchmark run failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="kb-module kb-report-module">
      <header className="kb-module-head">
        <div>
          <h3>Performance report</h3>
          <p className="mute">
            Dashboard view of knowledge plane capability — benchmark scores, trends, and actionable
            insights after RAG or ingest changes.
          </p>
        </div>
        <button type="button" className="ghost" disabled={busy} onClick={() => void load()}>
          Refresh report
        </button>
      </header>

      <BenchmarkDashboardReport
        dashboard={dashboard}
        variant="full"
        busy={busy}
        onRunBenchmark={() => void onRun()}
        onNavigate={onNavigate}
      />
    </div>
  )
}
