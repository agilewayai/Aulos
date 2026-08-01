import type { OpsTabId } from '../sessionScene'

export type OpsNavItem = {
  id: OpsTabId
  label: string
  hint: string
}

export type OpsNavGroup = {
  id: string
  label: string
  items: OpsNavItem[]
}

/** OPS information architecture — sidebar order and grouping. */
export const OPS_NAV_GROUPS: OpsNavGroup[] = [
  {
    id: 'home',
    label: 'Home',
    items: [{ id: 'overview', label: 'Overview', hint: 'Gateway health & metrics' }],
  },
  {
    id: 'people',
    label: 'People',
    items: [{ id: 'users', label: 'Users', hint: 'Accounts, roles, verification' }],
  },
  {
    id: 'ai',
    label: 'AI & knowledge',
    items: [
      { id: 'llm', label: 'LLM & embeddings', hint: 'Providers, embed, web research' },
      { id: 'skills', label: 'Skills', hint: 'Harness skills registry' },
      { id: 'guides', label: 'Guide quality', hint: 'Process scorecards' },
      { id: 'knowledge', label: 'Knowledge', hint: 'Registry, corpus, RAG lab' },
      { id: 'tasks', label: 'Task queue', hint: 'Async ops jobs' },
    ],
  },
  {
    id: 'content',
    label: 'Content & comms',
    items: [
      { id: 'blog', label: 'Dev blog', hint: 'Daily engineering narrative' },
      { id: 'mail', label: 'Mail', hint: 'Mailgun & deliveries' },
    ],
  },
  {
    id: 'integrations',
    label: 'Integrations',
    items: [{ id: 'discogs', label: 'Discogs', hint: 'Release guide token' }],
  },
  {
    id: 'platform',
    label: 'Platform',
    items: [
      { id: 'fleet', label: 'Fleet', hint: 'Service map & paths' },
      { id: 'dbha', label: 'Database HA', hint: 'Postgres failover' },
    ],
  },
]

export const OPS_NAV_FLAT: OpsNavItem[] = OPS_NAV_GROUPS.flatMap((g) => g.items)

export function opsNavLabel(tab: OpsTabId): string {
  return OPS_NAV_FLAT.find((i) => i.id === tab)?.label ?? tab
}
