import type { ReactNode } from 'react'
import type { OpsTabId } from '../sessionScene'

function Svg({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <svg
      className={className}
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {children}
    </svg>
  )
}

export function OpsNavIcon({ tab, className }: { tab: OpsTabId; className?: string }) {
  switch (tab) {
    case 'overview':
      return (
        <Svg className={className}>
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
        </Svg>
      )
    case 'users':
      return (
        <Svg className={className}>
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </Svg>
      )
    case 'llm':
      return (
        <Svg className={className}>
          <path d="M12 3v3" />
          <path d="M6 8l2 2" />
          <path d="M18 8l-2 2" />
          <rect x="4" y="11" width="16" height="10" rx="2" />
          <path d="M9 16h6" />
        </Svg>
      )
    case 'skills':
      return (
        <Svg className={className}>
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
        </Svg>
      )
    case 'knowledge':
      return (
        <Svg className={className}>
          <ellipse cx="12" cy="5" rx="9" ry="3" />
          <path d="M3 5v14a9 3 0 0 0 18 0V5" />
          <path d="M3 12a9 3 0 0 0 18 0" />
        </Svg>
      )
    case 'tasks':
      return (
        <Svg className={className}>
          <path d="M9 11l3 3L22 4" />
          <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
        </Svg>
      )
    case 'blog':
      return (
        <Svg className={className}>
          <path d="M12 20h9" />
          <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
        </Svg>
      )
    case 'mail':
      return (
        <Svg className={className}>
          <rect x="2" y="4" width="20" height="16" rx="2" />
          <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
        </Svg>
      )
    case 'discogs':
      return (
        <Svg className={className}>
          <circle cx="12" cy="12" r="10" />
          <circle cx="12" cy="12" r="3" />
        </Svg>
      )
    case 'fleet':
      return (
        <Svg className={className}>
          <rect x="2" y="7" width="20" height="14" rx="2" />
          <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
        </Svg>
      )
    case 'dbha':
      return (
        <Svg className={className}>
          <ellipse cx="12" cy="5" rx="9" ry="3" />
          <path d="M3 5v6c0 1.66 4 3 9 3s9-1.34 9-3V5" />
          <path d="M3 11v6c0 1.66 4 3 9 3s9-1.34 9-3v-6" />
        </Svg>
      )
    default:
      return (
        <Svg className={className}>
          <circle cx="12" cy="12" r="1" />
        </Svg>
      )
  }
}
