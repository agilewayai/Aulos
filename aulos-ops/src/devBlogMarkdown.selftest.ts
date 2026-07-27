import { parseDevBlogBlocks } from './devBlogMarkdown'

function assert(cond: unknown, msg: string) {
  if (!cond) throw new Error(msg)
}

const sample = `# 标题示例

## 今天产品多了什么
第一段 **加粗** 和 \`代码\` 测试。
第二段正文不应丢失。

## 谁因此更好用了
- 列表项一
- 列表项二

## 系统怎么搭起来的
架构说明段落。`

const blocks = parseDevBlogBlocks(sample)
const h2Sections = blocks.filter((b) => b.kind === 'h2')
const paragraphs = blocks.filter((b) => b.kind === 'p')

assert(h2Sections.length === 3, 'expected 3 section headings')
assert(paragraphs.length >= 3, `expected paragraph bodies, got ${paragraphs.length}`)
assert(
  paragraphs.some((p) => p.kind === 'p' && p.text.includes('不应丢失')),
  'section body after ## must be preserved',
)
assert(
  blocks.some((b) => b.kind === 'ul' && b.items.length === 2),
  'bullet list must parse',
)

const jul26Like = `## 今天产品多了什么
今天产品新增了两个直接可用的能力：**用户自助重置密码**。`

const jul26Blocks = parseDevBlogBlocks(jul26Like)
assert(jul26Blocks.length === 2, 'heading + paragraph')
assert(jul26Blocks[1]?.kind === 'p', 'paragraph after h2')
assert(
  jul26Blocks[1]?.kind === 'p' && jul26Blocks[1].text.includes('自助重置密码'),
  'jul26-like section must retain body',
)

console.log('devBlogMarkdown.selftest: ok')
