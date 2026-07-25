---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "checkpoint"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:052920a1996ad2796db8f93036db9a6415769a4880770c6280cb6b89f4814361"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# CKPT-005 — Ambient media + identity hygiene gates

status: complete
date: 2026-07-25
related: REQ-005, SPEC-006, SPEC-005, REQ-004

## Delivered

- Adaptive ambient agent + Open Goldberg 32-track playlist; cello family ambient (Bach Suite I)
- Media cache/proxy with `inline` disposition; client cache-first failover; floating player
- Synthesize: refuse empty-title KB dossiers; family list ownership; foreign-chamber scrub
- Compose/eval 0.3: ambient required to pass; bilingual + floating CSS in `guide_render`
- Studio iframe sandbox + base href so preview playback works
- Live recomposed guides #15 (Goldberg) and #17 (Beethoven cello) to current bar

## Verify

```bash
cd aulos-api && .venv/bin/python -m pytest ../aulos-skills/tests/test_runtime.py \
  ../aulos-skills/tests/test_ambient_agent.py \
  ../aulos-skills/tests/test_ambient_playlist.py \
  tests/test_media.py -q
curl -sI 'http://127.0.0.1:5090/v1/media/audio?src=...&mode=cache' | grep -i content-disposition
# expect: inline
```

## Measurable before → after

| Gate | Before | After |
| --- | --- | --- |
| Beethoven #17 ambient | absent | present + BWV 1007 |
| Beethoven #17 bilingual | absent | `data-lang=zh/en` |
| Beethoven #17 Goldberg leak | Aria bass / Gould Goldberg | scrubbed |
| Eval without ambient | could pass | hard-fail |
| Media disposition | attachment | inline |
