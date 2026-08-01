import { useCallback, useEffect, useState } from 'react'

const SIDEBAR_KEY = 'aulos-ops-layout-sidebar-collapsed'

function readSidebarCollapsed(): boolean {
  try {
    return localStorage.getItem(SIDEBAR_KEY) === '1'
  } catch {
    return false
  }
}

export function useOpsLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(readSidebarCollapsed)
  const [workspaceMaximized, setWorkspaceMaximized] = useState(false)

  useEffect(() => {
    try {
      localStorage.setItem(SIDEBAR_KEY, sidebarCollapsed ? '1' : '0')
    } catch {
      /* ignore */
    }
  }, [sidebarCollapsed])

  useEffect(() => {
    if (!workspaceMaximized) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setWorkspaceMaximized(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [workspaceMaximized])

  const toggleSidebarCollapsed = useCallback(() => {
    setSidebarCollapsed((v) => !v)
  }, [])

  const maximizeWorkspace = useCallback(() => {
    setWorkspaceMaximized(true)
  }, [])

  const restoreWorkspace = useCallback(() => {
    setWorkspaceMaximized(false)
  }, [])

  return {
    sidebarCollapsed,
    workspaceMaximized,
    toggleSidebarCollapsed,
    maximizeWorkspace,
    restoreWorkspace,
  }
}
