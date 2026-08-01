import type { OpsTabId } from '../sessionScene'
import { OPS_NAV_GROUPS } from './opsNav'
import { OpsNavIcon } from './navIcons'

type Props = {
  tab: OpsTabId
  onTabChange: (tab: OpsTabId) => void
  onNavigate?: () => void
  id?: string
  collapsed?: boolean
}

export function OpsSidebar({ tab, onTabChange, onNavigate, id = 'ops-sidebar', collapsed = false }: Props) {
  return (
    <nav
      id={id}
      className={collapsed ? 'ops-sidebar is-collapsed' : 'ops-sidebar'}
      aria-label="Ops navigation"
    >
      {OPS_NAV_GROUPS.map((group) => (
        <div key={group.id} className="ops-nav-group">
          <p className="ops-nav-group-label">{group.label}</p>
          <ul className="ops-nav-list">
            {group.items.map((item) => {
              const active = tab === item.id
              const tip = collapsed ? `${item.label} — ${item.hint}` : undefined
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    className={active ? 'ops-nav-item active' : 'ops-nav-item'}
                    aria-current={active ? 'page' : undefined}
                    title={tip}
                    onClick={() => {
                      onTabChange(item.id)
                      onNavigate?.()
                    }}
                  >
                    <OpsNavIcon tab={item.id} className="ops-nav-icon" />
                    <span className="ops-nav-text">
                      <span className="ops-nav-label">{item.label}</span>
                      <span className="ops-nav-hint">{item.hint}</span>
                    </span>
                  </button>
                </li>
              )
            })}
          </ul>
        </div>
      ))}
    </nav>
  )
}
