import { GUIDE_IFRAME_SANDBOX, guideSandboxOmitsSameOrigin, prepareGuideHtml } from './guideHtml'

function assert(cond: unknown, msg: string) {
  if (!cond) throw new Error(msg)
}

assert(guideSandboxOmitsSameOrigin(), 'sandbox must omit allow-same-origin')
assert(guideSandboxOmitsSameOrigin(GUIDE_IFRAME_SANDBOX), 'GUIDE_IFRAME_SANDBOX contract')
assert(
  !guideSandboxOmitsSameOrigin('allow-scripts allow-same-origin'),
  'must fail when same-origin present',
)

const withHead = prepareGuideHtml('<html><head></head><body>x</body></html>')
assert(withHead.includes('aulos-ambient-float') || withHead.includes('<base '), 'inject into head')

console.log('guideHtml.selftest: ok')
