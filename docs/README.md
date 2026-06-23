# Missile Warfare docs

This directory is the durable documentation entry point for the Terra Invicta missile-warfare mod.

## Current state

The project is still diagnostics-first. Start with the concise
[agent current-state summary](agent/CURRENT_STATE.md), then follow the evidence
links before changing behavior.

## Start here

- [Agent docs index](agent/INDEX.md): recommended durable reading order for
  coding agents.
- [Current state](agent/CURRENT_STATE.md): concise project posture, confirmed
  facts, blockers, and `Needs verification:` gaps.
- [Architecture](guide/architecture.md): high-level mod/Core boundary and design principle.
- [MVP roadmap](planning/mvp-roadmap.md): current issue-sized roadmap, completed diagnostics, blockers, and next work.
- [Reverse-engineering plan](research/reverse-engineering-plan.md): diagnostic-first plan for finding runtime combat entry points.
- [Confirmed combat launch hooks](diagnostics/hooks.md): runtime hooks confirmed by deployed diagnostics and parser output.
- [Battle snapshot and allocation diagnostics](diagnostics/snapshot-and-allocation.md): current snapshot fields, shadow allocation logs, parser behavior, and validation commands.
- [Runtime validation history](diagnostics/runtime-validation-history.md): historical smoke-test results and issue-by-issue runtime findings.
- [Readiness semantics](research/readiness-semantics.md): confirmed ammo/gate budget semantics and remaining command-safety constraints.
- [Selected command scope](research/selected-command-scope.md): verified selected-player command scope and vanilla salvo command granularity.
- [Assumption audit](maintenance/assumption-audit.md): assumptions that were fixed or explicitly marked provisional.
- [ADR index](adr/README.md): accepted durable decisions and their consequences.

## Directory map

- `agent/`: concise agent orientation, current state, and workflow.
- `adr/`: accepted decisions and their consequences.
- `guide/`: stable orientation documents.
- `diagnostics/`: confirmed runtime observations, log formats, and parser validation notes.
- `research/`: unsettled reverse-engineering questions and semantic investigations.
- `planning/`: durable roadmap documents that remain useful after one PR.
- `investigations/`: durable investigation records promoted from temporary issue work.
- `maintenance/`: documentation hygiene and assumption-audit notes.
- `archive/`: superseded durable notes retained only for historical context.

## Relationship with `dev-docs/`

`dev-docs/plan/**` is not durable documentation. It may contain per-issue or per-PR working plans, temporary context, and handoff notes. Once the related PR is merged or abandoned, those plan documents may be deleted instead of migrated. Do not treat references from `dev-docs/plan/**` as blockers for reorganizing durable `docs/` files.

## Documentation rules

- Separate confirmed runtime evidence from hypotheses.
- Use `ammoGateBudgetShots` for the validated module-keyed ammo plus vanilla gate budget; do not introduce `readyShots` terminology.
- Keep controlled command/application work gated behind dry-run evidence and command-application safety, using the verified selected-player command scope.
- Keep temporary implementation plans in `dev-docs/plan/**`, not in durable `docs/` pages.
