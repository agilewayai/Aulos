import type {
  KnowledgeComposer,
  KnowledgeDoc,
  KnowledgeJob,
  KnowledgeMedia,
  KnowledgePlaneStats,
  KnowledgeSource,
} from '../api'

export type KnowledgeModuleId =
  | 'overview'
  | 'report'
  | 'registry'
  | 'explore'
  | 'dossier'
  | 'documents'
  | 'jobs'
  | 'simulate'
  | 'benchmark'
  | 'improve'
  | 'media'

export type KnowledgeModuleMeta = {
  id: KnowledgeModuleId
  label: string
  hint: string
}

export const KNOWLEDGE_MODULES: KnowledgeModuleMeta[] = [
  { id: 'overview', label: 'Overview', hint: 'Health, metrics, gate summary' },
  { id: 'report', label: 'Performance report', hint: 'Benchmark dashboard & insights' },
  { id: 'registry', label: 'Source registry', hint: 'REQ-008 authority sources' },
  { id: 'explore', label: 'Explore sources', hint: 'Pick a composer · discover authorities' },
  { id: 'dossier', label: 'Composer dossier', hint: 'Life timeline · works tree' },
  { id: 'documents', label: 'Documents', hint: 'Query, proofread, provenance' },
  { id: 'jobs', label: 'Jobs & crawl', hint: 'Enqueue and observe ingest' },
  { id: 'simulate', label: 'RAG simulate', hint: 'Retrieve lab / identity bleed' },
  { id: 'benchmark', label: 'Benchmark', hint: 'KB-BENCH-001 score & report' },
  { id: 'improve', label: 'Diagnose & improve', hint: 'KB-DIAG auto crawl + L3 tasks' },
  { id: 'media', label: 'Media assets', hint: 'Images, audio, meta on disk' },
]

export type CrawlSeed = {
  id: string
  label: string
  qid: string
  mb: string
}

export type KnowledgePlaneState = {
  planeReachable: boolean | null
  planeHealth: string
  planeStats: KnowledgePlaneStats | null
  sources: KnowledgeSource[]
  jobs: KnowledgeJob[]
  docs: KnowledgeDoc[]
  composers: KnowledgeComposer[]
  media: KnowledgeMedia[]
}

export type DocStatusFilter = 'all' | 'published' | 'quarantine'
