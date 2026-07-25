# Aulos Ops Observability

Use when operating or reviewing Aulos services from an admin/ops perspective.

## Signals to collect

- Gateway health (`aulos-api /health`)
- Sub-project harness `history-status`
- Recent verification reports under `.aries_harness/runs/`
- Open risks from each project's `RISKS.md` / `STATE.md`

## Cadence

- For runs > 30 minutes, sync status at least every 30 minutes
- Promote durable facts into MEMORY cards; keep hot STATE concise
