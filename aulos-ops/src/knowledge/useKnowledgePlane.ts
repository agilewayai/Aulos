import { useCallback, useMemo, useState } from 'react'
import {
  enqueueKnowledgeJob,
  fetchKnowledgeArtifact,
  fetchKnowledgeChunkProvenance,
  fetchKnowledgeComposers,
  fetchKnowledgeDocument,
  fetchKnowledgeDocuments,
  fetchKnowledgeJobs,
  fetchKnowledgeMedia,
  fetchKnowledgePlaneHealth,
  fetchKnowledgePlaneStats,
  fetchKnowledgeProvenance,
  fetchKnowledgeSources,
  type KnowledgeChunk,
  type KnowledgeComposer,
  type KnowledgeDoc,
  type KnowledgeJob,
  type KnowledgeMedia,
  type KnowledgePlaneStats,
  type KnowledgeSource,
} from '../api'
import { FAMOUS_SEED } from './constants'
import type { CrawlSeed, DocStatusFilter } from './types'

type UseKnowledgePlaneOpts = {
  docStatus: DocStatusFilter
  docType: string
  docSource: string
  docQuery: string
}

export function useKnowledgePlane({
  docStatus,
  docType,
  docSource,
  docQuery,
}: UseKnowledgePlaneOpts) {
  const [planeReachable, setPlaneReachable] = useState<boolean | null>(null)
  const [planeHealth, setPlaneHealth] = useState('')
  const [planeStats, setPlaneStats] = useState<KnowledgePlaneStats | null>(null)
  const [sources, setSources] = useState<KnowledgeSource[]>([])
  const [jobs, setJobs] = useState<KnowledgeJob[]>([])
  const [docs, setDocs] = useState<KnowledgeDoc[]>([])
  const [composers, setComposers] = useState<KnowledgeComposer[]>([])
  const [media, setMedia] = useState<KnowledgeMedia[]>([])

  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDoc | null>(null)
  const [provenance, setProvenance] = useState<Record<string, unknown> | null>(null)
  const [chunkProvenance, setChunkProvenance] = useState<Record<string, unknown> | null>(null)
  const [selectedChunkId, setSelectedChunkId] = useState<number | null>(null)
  const [artifactPreview, setArtifactPreview] = useState('')
  const [showRawProvenance, setShowRawProvenance] = useState(false)

  const load = useCallback(async () => {
    try {
      const h = await fetchKnowledgePlaneHealth()
      setPlaneReachable(true)
      setPlaneHealth(`${h.service} ${h.version} — ${h.status}`)
      const [stats, src, jobRows, comps, mediaRows] = await Promise.all([
        fetchKnowledgePlaneStats(),
        fetchKnowledgeSources(),
        fetchKnowledgeJobs(),
        fetchKnowledgeComposers(),
        fetchKnowledgeMedia({ limit: 80 }),
      ])
      setPlaneStats(stats)
      setSources(src)
      setJobs(jobRows)
      setComposers(comps)
      setMedia(mediaRows)
      const docRows = await fetchKnowledgeDocuments({
        status: docStatus === 'all' ? '' : docStatus,
        entity_type: docType,
        source_id: docSource,
        q: docQuery,
        limit: 120,
      })
      setDocs(docRows)
    } catch (err) {
      setPlaneReachable(false)
      setPlaneHealth(err instanceof Error ? err.message : 'knowledge plane unreachable')
      setPlaneStats(null)
      setSources([])
      setJobs([])
      setDocs([])
      setComposers([])
      setMedia([])
      setSelectedDoc(null)
      setProvenance(null)
      throw err
    }
  }, [docStatus, docType, docSource, docQuery])

  const crawlOptions = useMemo((): CrawlSeed[] => {
    if (composers.length) {
      return composers
        .map((c) => ({
          id: c.id,
          label: c.name_en || c.name_zh || c.id,
          qid: c.external_ids?.wikidata || c.external_ids?.qid || '',
          mb: c.name_en || '',
        }))
        .filter((c) => c.id)
    }
    return FAMOUS_SEED
  }, [composers])

  const openDoc = useCallback(async (id: number) => {
    setSelectedId(id)
    setSelectedChunkId(null)
    setChunkProvenance(null)
    const [doc, prov] = await Promise.all([fetchKnowledgeDocument(id), fetchKnowledgeProvenance(id)])
    setSelectedDoc(doc)
    setProvenance(prov)
    setArtifactPreview('')
    if (doc.artifact_id) {
      const art = await fetchKnowledgeArtifact(doc.artifact_id)
      setArtifactPreview(art.preview || '')
    }
  }, [])

  const openChunk = useCallback(async (chunkId: number) => {
    setSelectedChunkId(chunkId)
    const prov = await fetchKnowledgeChunkProvenance(chunkId)
    setChunkProvenance(prov)
  }, [])

  const runJob = useCallback(
    async (sourceId: string, params: Record<string, unknown>) => {
      const job = await enqueueKnowledgeJob(sourceId, params)
      await load()
      return job
    },
    [load],
  )

  return {
    planeReachable,
    planeHealth,
    planeStats,
    sources,
    jobs,
    docs,
    composers,
    media,
    crawlOptions,
    selectedId,
    selectedDoc,
    provenance,
    chunkProvenance,
    selectedChunkId,
    artifactPreview,
    showRawProvenance,
    setShowRawProvenance,
    load,
    openDoc,
    openChunk,
    runJob,
    setSelectedDoc,
    setProvenance,
    setChunkProvenance,
    setSelectedChunkId,
  }
}

export type { KnowledgeChunk, KnowledgeDoc, KnowledgeJob, KnowledgeMedia, KnowledgeSource }
