import type { CrawlSeed } from './types'
import type { KnowledgeExploreSeed } from '../api'

export const FAMOUS_SEED: CrawlSeed[] = [
  { id: 'johann-sebastian-bach', qid: 'Q1339', label: 'J.S. Bach', mb: 'Johann Sebastian Bach' },
  { id: 'wolfgang-amadeus-mozart', qid: 'Q254', label: 'Mozart', mb: 'Wolfgang Amadeus Mozart' },
  { id: 'ludwig-van-beethoven', qid: 'Q255', label: 'Beethoven', mb: 'Ludwig van Beethoven' },
  { id: 'frederic-chopin', qid: 'Q1268', label: 'Chopin', mb: 'Frédéric Chopin' },
  { id: 'franz-schubert', qid: 'Q7312', label: 'Schubert', mb: 'Franz Schubert' },
  { id: 'johannes-brahms', qid: 'Q7294', label: 'Brahms', mb: 'Johannes Brahms' },
  { id: 'pyotr-ilyich-tchaikovsky', qid: 'Q7315', label: 'Tchaikovsky', mb: 'Pyotr Ilyich Tchaikovsky' },
  { id: 'gustav-mahler', qid: 'Q7304', label: 'Mahler', mb: 'Gustav Mahler' },
  { id: 'claude-debussy', qid: 'Q4700', label: 'Debussy', mb: 'Claude Debussy' },
  { id: 'igor-stravinsky', qid: 'Q7314', label: 'Stravinsky', mb: 'Igor Stravinsky' },
]

const FEATURED_IDS = new Set([
  'johann-sebastian-bach',
  'wolfgang-amadeus-mozart',
  'ludwig-van-beethoven',
  'frederic-chopin',
  'pyotr-ilyich-tchaikovsky',
  'claude-debussy',
  'franz-schubert',
  'johannes-brahms',
])

/** Client fallback when explore/seeds API is unreachable (META-001 §3.4). */
export function fallbackExploreSeeds(): {
  seeds: KnowledgeExploreSeed[]
  featured: KnowledgeExploreSeed[]
  letters: string[]
  stats: { total: number; famous: number; with_portrait: number; in_corpus: number }
} {
  const seeds: KnowledgeExploreSeed[] = FAMOUS_SEED.map((s) => {
    const short = s.label.replace(/^J\.S\.\s+/, '') || s.label
    const letter = short.slice(0, 1).toUpperCase()
    return {
      id: s.id,
      name_en: s.mb,
      name_zh: '',
      short_name: short,
      era: '',
      letter,
      sort_key: short.toLowerCase(),
      wikidata_qid: s.qid,
      wikipedia_title: s.mb,
      famous: true,
      featured: FEATURED_IDS.has(s.id),
      in_corpus: false,
      lifespan: '',
      external_ids: { wikidata: s.qid },
      portrait: null,
    }
  }).sort((a, b) => a.sort_key.localeCompare(b.sort_key))

  const featured = [...FEATURED_IDS]
    .map((id) => seeds.find((s) => s.id === id))
    .filter(Boolean) as KnowledgeExploreSeed[]
  const letters = [...new Set(seeds.map((s) => s.letter))].sort()
  return {
    seeds,
    featured,
    letters,
    stats: { total: seeds.length, famous: seeds.length, with_portrait: 0, in_corpus: 0 },
  }
}

export const REGISTERED_CONNECTORS = [
  'catalog_import',
  'wikidata',
  'musicbrainz',
  'wikipedia',
  'imslp',
  'rism',
] as const

export const RETRIEVE_PRESETS = [
  {
    label: 'Bach cello suites',
    query: 'Bach cello suites unaccompanied',
    workId: 'bach.cello-suites.bwv-1007-1012',
    composerId: 'johann-sebastian-bach',
  },
  {
    label: 'Goldberg variations',
    query: 'Goldberg variations aria',
    workId: 'bach.goldberg-variations.bwv-988',
    composerId: 'johann-sebastian-bach',
  },
  {
    label: 'Mozart requiem',
    query: 'Mozart Requiem Lacrimosa',
    workId: '',
    composerId: 'wolfgang-amadeus-mozart',
  },
] as const
