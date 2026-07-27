---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-27T09:44:37+00:00"
effective_status: "active"
effective_since: "2026-07-27T09:44:37+00:00"
content_fingerprint: "sha256:adb78fad26e24211a7cb0cc7dacd8cb622ee16e63888e7fe12716fa960810f9c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
/**
 * Behavior: before intentional asset reload, persist UI scene; after reload, restore once.
 *
 * ## Capture
 * - AssetUpdateToast polls `/version.json`; on mismatch calls `captureRegisteredScenes()` then reloads.
 * - App registers a capture callback with tab, compose draft, open guide id, library filters, scrollY.
 * - Never persist passwords.
 *
 * ## Restore
 * - `consumeWebScene()` / `consumeOpsScene()` once at boot (sessionStorage).
 * - Re-apply studio tab / filters / draft / guide; re-attach in-progress job watch when needed.
 * - Soft notice: “Restored your place after update”.
 *
 * ## Non-goals
 * - Full DOM / iframe scroll inside guide HTML.
 * - Cross-device sync.
 */
