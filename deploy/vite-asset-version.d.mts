import type { Plugin } from 'vite'

export function createBuildId(): string
export function assetVersionPlugin(appName?: string): Plugin
