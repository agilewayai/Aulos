import type { ReactNode } from 'react'

export type DevBlogBlock =
  | { kind: 'h1'; text: string }
  | { kind: 'h2'; text: string }
  | { kind: 'p'; text: string }
  | { kind: 'ul'; items: string[] }

/** Split markdown into render blocks (exported for selftests). */
export function parseDevBlogBlocks(source: string): DevBlogBlock[] {
  const normalized = source.replace(/\r\n/g, '\n').trim()
  if (!normalized) return []

  const out: DevBlogBlock[] = []
  for (const chunk of normalized.split(/\n\n+/)) {
    const lines = chunk.split('\n')
    const first = lines[0]?.trim() ?? ''
    const rest = lines.slice(1)

    if (first.startsWith('# ')) {
      out.push({ kind: 'h1', text: first.slice(2).trim() })
      out.push(...bodyLinesToBlocks(rest))
      continue
    }
    if (first.startsWith('## ')) {
      out.push({ kind: 'h2', text: first.slice(3).trim() })
      out.push(...bodyLinesToBlocks(rest))
      continue
    }
    out.push(...bodyLinesToBlocks(lines))
  }
  return out
}

function bodyLinesToBlocks(lines: string[]): DevBlogBlock[] {
  const blocks: DevBlogBlock[] = []
  let listItems: string[] = []

  const flushList = () => {
    if (listItems.length > 0) {
      blocks.push({ kind: 'ul', items: [...listItems] })
      listItems = []
    }
  }

  for (const raw of lines) {
    const line = raw.trimEnd()
    const trimmed = line.trim()
    if (!trimmed) {
      flushList()
      continue
    }
    if (trimmed.startsWith('- ')) {
      listItems.push(trimmed.slice(2))
      continue
    }
    flushList()
    blocks.push({ kind: 'p', text: trimmed })
  }
  flushList()
  return blocks
}

const INLINE_RE = /(\*\*[^*]+\*\*|`[^`]+`)/g

export function renderDevBlogInline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = []
  let last = 0
  let match: RegExpExecArray | null
  let idx = 0
  INLINE_RE.lastIndex = 0
  while ((match = INLINE_RE.exec(text)) !== null) {
    if (match.index > last) {
      nodes.push(text.slice(last, match.index))
    }
    const token = match[0]
    if (token.startsWith('**') && token.endsWith('**')) {
      nodes.push(
        <strong key={`${keyPrefix}-b${idx}`}>{token.slice(2, -2)}</strong>,
      )
    } else if (token.startsWith('`') && token.endsWith('`')) {
      nodes.push(<code key={`${keyPrefix}-c${idx}`}>{token.slice(1, -1)}</code>)
    } else {
      nodes.push(token)
    }
    last = match.index + token.length
    idx += 1
  }
  if (last < text.length) {
    nodes.push(text.slice(last))
  }
  return nodes.length > 0 ? nodes : [text]
}

export function DevBlogMarkdown({ source }: { source: string }) {
  const blocks = parseDevBlogBlocks(source)
  return (
    <div className="dev-blog-prose">
      {blocks.map((block, i) => {
        const key = `b${i}`
        switch (block.kind) {
          case 'h1':
            return (
              <h3 key={key} className="dev-blog-h1">
                {renderDevBlogInline(block.text, key)}
              </h3>
            )
          case 'h2':
            return (
              <h4 key={key} className="dev-blog-h2">
                {renderDevBlogInline(block.text, key)}
              </h4>
            )
          case 'p':
            return (
              <p key={key} className="dev-blog-p">
                {renderDevBlogInline(block.text, key)}
              </p>
            )
          case 'ul':
            return (
              <ul key={key} className="dev-blog-list">
                {block.items.map((item, j) => (
                  <li key={`${key}-${j}`}>{renderDevBlogInline(item, `${key}-${j}`)}</li>
                ))}
              </ul>
            )
          default:
            return null
        }
      })}
    </div>
  )
}
