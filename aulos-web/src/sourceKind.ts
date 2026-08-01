/** Shared Discogs/source medium labels (META-001 §3.5). */
export function sourceKindLabel(kind: string | undefined | null): string {
  if (kind === 'vinyl') return '黑胶'
  if (kind === 'cd') return 'CD'
  if (!kind || kind === 'release') return '唱片'
  return kind
}
