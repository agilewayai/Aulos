import { useEffect, useState, type ReactNode } from 'react'
import type { HealthResponse, User } from '../api'
import type { OpsTabId } from '../sessionScene'
import { opsNavLabel } from './opsNav'
import { OpsSidebar } from './OpsSidebar'
import { useOpsLayout } from './useOpsLayout'
import { IconChevronLeft, IconChevronRight, IconMaximize, IconRestore } from './layoutIcons'

type Props = {
  tab: OpsTabId
  onTabChange: (tab: OpsTabId) => void
  user: User
  gatewayOk: boolean
  health: HealthResponse | null
  updatedAt: string | null
  busy: boolean
  notice: string | null
  error: string | null
  onRefreshHealth: () => void
  onLogout: () => void
  children: ReactNode
}

export function OpsDashboardShell({
  tab,
  onTabChange,
  user,
  gatewayOk,
  health,
  updatedAt,
  busy,
  notice,
  error,
  onRefreshHealth,
  onLogout,
  children,
}: Props) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const {
    sidebarCollapsed,
    workspaceMaximized,
    toggleSidebarCollapsed,
    maximizeWorkspace,
    restoreWorkspace,
  } = useOpsLayout()

  useEffect(() => {
    setMobileNavOpen(false)
  }, [tab])

  useEffect(() => {
    if (!mobileNavOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMobileNavOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [mobileNavOpen])

  const shellClass = [
    'ops-dashboard',
    sidebarCollapsed && !workspaceMaximized ? 'ops-sidebar-collapsed' : '',
    workspaceMaximized ? 'ops-workspace-maximized' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={shellClass}>
      <header className="ops-topbar">
        <div className="ops-topbar-start">
          <button
            type="button"
            className="ops-menu-btn"
            aria-expanded={mobileNavOpen}
            aria-controls="ops-sidebar-drawer"
            onClick={() => setMobileNavOpen((v) => !v)}
          >
            <span className="sr-only">{mobileNavOpen ? 'Close menu' : 'Open menu'}</span>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
              {mobileNavOpen ? (
                <>
                  <path d="M18 6 6 18" />
                  <path d="m6 6 12 12" />
                </>
              ) : (
                <>
                  <path d="M4 6h16" />
                  <path d="M4 12h16" />
                  <path d="M4 18h16" />
                </>
              )}
            </svg>
          </button>
          <div className="ops-brand-block">
            <p className="ops-brand">Aulos Ops</p>
            <p className="ops-crumb" aria-current="page">
              {opsNavLabel(tab)}
              {workspaceMaximized ? ' · maximized' : ''}
            </p>
          </div>
        </div>
        <div className="ops-topbar-end">
          <div className="ops-layout-tools" aria-label="Layout controls">
            {workspaceMaximized ? (
              <button
                type="button"
                className="ghost ops-layout-btn"
                onClick={restoreWorkspace}
                title="Restore layout (Esc)"
              >
                <IconRestore />
                <span className="ops-layout-btn-label">Restore</span>
              </button>
            ) : (
              <>
                <button
                  type="button"
                  className="ghost ops-layout-btn"
                  onClick={maximizeWorkspace}
                  title="Maximize workspace"
                >
                  <IconMaximize />
                  <span className="ops-layout-btn-label">Maximize</span>
                </button>
                <button
                  type="button"
                  className="ghost ops-layout-btn ops-layout-btn-icon"
                  onClick={toggleSidebarCollapsed}
                  title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                  aria-expanded={!sidebarCollapsed}
                  aria-controls="ops-sidebar-desktop"
                >
                  {sidebarCollapsed ? <IconChevronRight /> : <IconChevronLeft />}
                  <span className="sr-only">{sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}</span>
                </button>
              </>
            )}
          </div>
          <span
            className={`ops-gateway-pill ${gatewayOk ? 'ops-gateway-ok' : 'ops-gateway-down'}`}
            title={gatewayOk ? 'Gateway healthy' : 'Gateway unreachable'}
          >
            <span className="ops-gateway-dot" aria-hidden />
            {gatewayOk ? health?.version ?? 'ok' : 'down'}
          </span>
          {updatedAt ? <span className="ops-updated meta">· {updatedAt}</span> : null}
          <span className="ops-user-email" title={user.email}>
            {user.email}
          </span>
          <button type="button" className="ghost ops-top-btn" disabled={busy} onClick={onRefreshHealth}>
            Refresh
          </button>
          <button type="button" className="ghost ops-top-btn" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </header>

      <div className="ops-body">
        {!workspaceMaximized ? (
          <aside id="ops-sidebar-desktop" className="ops-sidebar-desktop" aria-label="Ops sections">
            <div className="ops-sidebar-rail-head">
              <button
                type="button"
                className="ghost ops-layout-btn ops-sidebar-collapse-btn"
                onClick={toggleSidebarCollapsed}
                title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                aria-expanded={!sidebarCollapsed}
                aria-controls="ops-sidebar-desktop"
              >
                {sidebarCollapsed ? <IconChevronRight /> : <IconChevronLeft />}
                {!sidebarCollapsed ? <span className="ops-layout-btn-label">Collapse</span> : null}
              </button>
            </div>
            <OpsSidebar tab={tab} onTabChange={onTabChange} collapsed={sidebarCollapsed} />
          </aside>
        ) : null}

        {mobileNavOpen ? (
          <button
            type="button"
            className="ops-sidebar-backdrop"
            aria-label="Close navigation"
            onClick={() => setMobileNavOpen(false)}
          />
        ) : null}

        <aside
          id="ops-sidebar-drawer"
          className={mobileNavOpen ? 'ops-sidebar-drawer open' : 'ops-sidebar-drawer'}
          aria-hidden={!mobileNavOpen}
        >
          <OpsSidebar tab={tab} onTabChange={onTabChange} onNavigate={() => setMobileNavOpen(false)} />
        </aside>

        <main className="ops-workspace" id="ops-main">
          {workspaceMaximized ? (
            <div className="ops-maximized-bar">
              <span>Workspace maximized — more room for tables and audit panes.</span>
              <button type="button" className="ghost ops-layout-btn" onClick={restoreWorkspace}>
                <IconRestore />
                Restore
              </button>
            </div>
          ) : null}
          <a href="#ops-main-content" className="ops-skip">
            Skip to content
          </a>
          {notice ? (
            <p className="notice ops-banner" role="status">
              {notice}
            </p>
          ) : null}
          {error ? (
            <p className="error ops-banner" role="alert">
              {error}
            </p>
          ) : null}
          <div id="ops-main-content" className="ops-workspace-inner">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
