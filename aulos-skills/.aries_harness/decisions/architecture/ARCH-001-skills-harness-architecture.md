---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "system-design"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T11:22:04Z"
content_fingerprint: "sha256:cf22009464b81d2d849a3645deb07f71128dafc46433dbfb8e6507b22a2bc825"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Architecture Design Pack

## Document Control

- Architecture ID: ARCH-001
- Title: aulos-skills harness pack architecture
- Status: active
- Related request: REQ-001
- Related spec: SPEC-001
- Child refs: ADR-001, STORY-001

## Design Drivers

- Primary business outcome: governed `aulos-skills` (main harness skills)
- Quality attributes: modularity, offline testability, clear sibling contracts

## Target shape

- `CLI → registry.discover_skills(skills/*) → skill.yaml + SKILL.md packs`

## Package layout

```text
aulos-skills/
├── .aries_harness/
│   ├── scripts/          # facility CLI (aries-harness.sh, ah.sh, …)
│   ├── templates/        # init skeletons (*.tmpl)
│   └── …                 # MISSION/STATE/history/runs/…
├── skills/<id>/{skill.yaml,SKILL.md}
├── src/aulos_skills/{cli,config,registry}.py
├── tests/
└── pyproject.toml
```

Facility scripts/templates stay under `.aries_harness/` — never at project-root `scripts/` or `templates/`.

## Open decisions

- Auth model deferred
- Production deploy deferred
