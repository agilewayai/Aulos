/** Studio guide iframe prep + sandbox contract (SPEC-015 / AUDIT-009 F2). */

/** Opaque-origin sandbox: scripts may run, but cannot read portal cookies/DOM. */
export const GUIDE_IFRAME_SANDBOX =
  'allow-scripts allow-popups allow-popups-to-escape-sandbox' as const

export function prepareGuideHtml(html: string): string {
  if (!html) return html
  const origin = typeof window === 'undefined' ? 'https://aulos.purezen.ai' : window.location.origin
  const inject = `<base href="${origin}/"><style id="aulos-ambient-float">.wrap{padding-bottom:7.5rem!important}.ambient{position:fixed!important;z-index:60!important;right:.75rem!important;bottom:.75rem!important;left:auto!important;width:min(22.5rem,calc(100vw - 1.5rem))!important;margin:0!important;max-height:min(72vh,30rem)!important;display:flex!important;flex-direction:column!important;background:rgba(16,22,27,.92)!important;backdrop-filter:blur(12px);box-shadow:0 12px 36px rgba(0,0,0,.45)}.ambient .ambient-details{overflow:auto;flex:1 1 auto;min-height:0}@media(max-width:719px){.ambient{right:.5rem!important;left:.5rem!important;bottom:.5rem!important;width:auto!important}}</style>`
  if (html.includes('id="aulos-ambient-float"') || html.includes("id='aulos-ambient-float'")) {
    return /<head[^>]*>/i.test(html) && !/<base\s/i.test(html)
      ? html.replace(/<head([^>]*)>/i, `<head$1><base href="${origin}/">`)
      : html
  }
  return /<head[^>]*>/i.test(html)
    ? html.replace(/<head([^>]*)>/i, `<head$1>${inject}`)
    : inject + html
}

export function guideSandboxOmitsSameOrigin(sandbox: string = GUIDE_IFRAME_SANDBOX): boolean {
  return !/\ballow-same-origin\b/.test(sandbox) && /\ballow-scripts\b/.test(sandbox)
}
