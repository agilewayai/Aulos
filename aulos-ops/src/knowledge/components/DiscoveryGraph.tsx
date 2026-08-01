import { useMemo, useState } from 'react'

type GraphNode = {
  id: string
  kind?: string
  label?: string
  url?: string
  score?: number
  depth?: number
}

type GraphEdge = {
  src: string
  dst: string
  relation?: string
}

type Props = {
  nodes: GraphNode[]
  edges: GraphEdge[]
  selectedId?: string | null
  onSelect?: (node: GraphNode) => void
}

const KIND_COLOR: Record<string, string> = {
  registry_source: '#2f6fed',
  entity: '#0f766e',
  url: '#b45309',
  candidate: '#7c3aed',
}

function layoutNodes(nodes: GraphNode[], width: number, height: number) {
  const byKind = new Map<string, GraphNode[]>()
  for (const n of nodes) {
    const k = n.kind || 'url'
    const list = byKind.get(k) || []
    list.push(n)
    byKind.set(k, list)
  }
  const columns = ['registry_source', 'entity', 'url', 'candidate'].filter((k) => byKind.has(k))
  const pos = new Map<string, { x: number; y: number }>()
  columns.forEach((kind, colIdx) => {
    const col = byKind.get(kind) || []
    const x = ((colIdx + 0.5) / Math.max(columns.length, 1)) * (width - 80) + 40
    col.forEach((n, rowIdx) => {
      const y = ((rowIdx + 0.5) / Math.max(col.length, 1)) * (height - 60) + 30
      pos.set(n.id, { x, y })
    })
  })
  // leftover kinds
  for (const n of nodes) {
    if (!pos.has(n.id)) {
      pos.set(n.id, { x: width / 2, y: height / 2 })
    }
  }
  return pos
}

export function DiscoveryGraph({ nodes, edges, selectedId, onSelect }: Props) {
  const [hoverId, setHoverId] = useState<string | null>(null)
  const width = 640
  const height = 280
  const visible = useMemo(() => nodes.slice(0, 28), [nodes])
  const visibleIds = useMemo(() => new Set(visible.map((n) => n.id)), [visible])
  const visibleEdges = useMemo(
    () => edges.filter((e) => visibleIds.has(e.src) && visibleIds.has(e.dst)).slice(0, 40),
    [edges, visibleIds],
  )
  const positions = useMemo(() => layoutNodes(visible, width, height), [visible])

  if (!visible.length) {
    return <p className="mute">No graph nodes yet — run explore first.</p>
  }

  const active = hoverId || selectedId

  return (
    <div className="kb-discovery-graph">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Source discovery graph">
        {visibleEdges.map((e, i) => {
          const a = positions.get(e.src)
          const b = positions.get(e.dst)
          if (!a || !b) return null
          const lit = active && (e.src === active || e.dst === active)
          return (
            <line
              key={`${e.src}-${e.dst}-${i}`}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              className={lit ? 'kb-graph-edge lit' : 'kb-graph-edge'}
            />
          )
        })}
        {visible.map((n) => {
          const p = positions.get(n.id)
          if (!p) return null
          const fill = KIND_COLOR[n.kind || ''] || '#64748b'
          const lit = active === n.id
          const r = lit ? 12 : 9
          return (
            <g
              key={n.id}
              className="kb-graph-node"
              transform={`translate(${p.x}, ${p.y})`}
              onMouseEnter={() => setHoverId(n.id)}
              onMouseLeave={() => setHoverId(null)}
              onClick={() => onSelect?.(n)}
              style={{ cursor: 'pointer' }}
            >
              <circle r={r} fill={fill} opacity={lit ? 1 : 0.85} />
              <title>
                {`${n.kind || 'node'}: ${n.label || n.id}${typeof n.score === 'number' ? ` (${n.score})` : ''}`}
              </title>
              <text y={r + 12} textAnchor="middle" className="kb-graph-label">
                {(n.label || n.id).slice(0, 18)}
              </text>
            </g>
          )
        })}
      </svg>
      <div className="kb-graph-legend">
        {Object.entries(KIND_COLOR).map(([kind, color]) => (
          <span key={kind}>
            <i style={{ background: color }} /> {kind.replace('_', ' ')}
          </span>
        ))}
      </div>
    </div>
  )
}
