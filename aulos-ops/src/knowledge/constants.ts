import type { CrawlSeed } from './types'

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
