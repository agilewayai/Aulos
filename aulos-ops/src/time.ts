/** Display timestamps in the OS / browser timezone. Wire format remains UTC ISO. */

export function formatDateTime(value: string | Date | null | undefined): string {
  const date = parseInstant(value)
  if (!date) return ''
  return date.toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

export function formatTime(value: string | Date | null | undefined): string {
  const date = parseInstant(value)
  if (!date) return ''
  return date.toLocaleTimeString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
  })
}

function parseInstant(value: string | Date | null | undefined): Date | null {
  if (value == null || value === '') return null
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return date
}
