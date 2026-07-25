/**
 * Vite plugin: inject build id into the client bundle and emit dist/version.json.
 * Clients poll /version.json (no-cache) and prompt a soft reload when it differs.
 */
import { execSync } from 'node:child_process'
import { writeFileSync } from 'node:fs'
import { join } from 'node:path'

export function createBuildId() {
  if (process.env.AULOS_BUILD_ID) return process.env.AULOS_BUILD_ID
  let rev = 'local'
  try {
    rev = execSync('git rev-parse --short HEAD', {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim()
  } catch {
    /* not a git checkout */
  }
  const stamp = new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0, 14)
  return `${stamp}-${rev}`
}

/**
 * @param {string} appName
 * @returns {import('vite').Plugin}
 */
export function assetVersionPlugin(appName = 'aulos') {
  const buildId = createBuildId()
  const builtAt = new Date().toISOString()
  const payload = JSON.stringify({ app: appName, buildId, builtAt }, null, 2) + '\n'

  return {
    name: 'aulos-asset-version',
    config() {
      return {
        define: {
          __AULOS_BUILD_ID__: JSON.stringify(buildId),
          __AULOS_BUILT_AT__: JSON.stringify(builtAt),
        },
      }
    },
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url?.split('?', 1)[0]
        if (url !== '/version.json') return next()
        res.setHeader('Content-Type', 'application/json; charset=utf-8')
        res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate')
        res.end(payload)
      })
    },
    writeBundle(outputOptions) {
      const dir = outputOptions.dir
      if (!dir) return
      writeFileSync(join(dir, 'version.json'), payload)
    },
  }
}
