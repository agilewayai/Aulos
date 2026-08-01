---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "request-brief"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T09:50:00Z"
effective_status: "active"
effective_since: "2026-08-01T09:50:00Z"
content_fingerprint: "sha256:86afd7d9d5399da24e729e5c51704e5ebe5187ca3719e27ae2002be1ae3f9af7"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-005 — 我的聆乐日记 · 博客式日历与 Tag 云

## Outcome

「我的聆乐」改为博客式浏览：主栏日记流 + 侧栏月历与 Tag 云。点击日历某日可查看该日聆乐；Tag 按作曲家、演奏家、乐团、曲目类型（genres/styles）与介质分布，点击可筛选。

## Non-goals

- 服务端分页搜索 / 全库聚合 API（本切片用 list 快照客户端聚合）
- 公开个人博客页（仍为登录后私有日记）
