import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { assetVersionPlugin } from '../deploy/vite-asset-version.mjs'

export default defineConfig({
  plugins: [react(), assetVersionPlugin('aulos-ops')],
  server: {
    port: 5174,
    proxy: {
      '/v1': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})
