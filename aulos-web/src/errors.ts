/** Shared unknown→message helper (META-001 §3.5 — one err helper for the app). */
export function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback
}
