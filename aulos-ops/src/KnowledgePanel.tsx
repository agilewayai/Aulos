import { KnowledgeConsole } from './knowledge/KnowledgeConsole'

type Props = {
  busy: boolean
  setBusy: (v: boolean) => void
  setError: (v: string | null) => void
  setNotice: (v: string | null) => void
  planeEnabled?: boolean
  planeUrl?: string
}

/** OPS Knowledge management console (registry, documents, jobs, RAG simulate, observability). */
export function KnowledgePanel(props: Props) {
  return <KnowledgeConsole {...props} />
}
