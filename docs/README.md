# Missile Warfare docs

This directory is the durable documentation entry point for the Terra Invicta missile-warfare mod.

## Start here

- [Architecture](guide/architecture.md): high-level mod/Core boundary and design principle.
- [MVP roadmap](planning/mvp-roadmap.md): current issue-sized roadmap and acceptance criteria.
- [Reverse-engineering plan](research/reverse-engineering-plan.md): diagnostic-first plan for finding runtime combat entry points.
- [Confirmed combat launch hooks](diagnostics/hooks.md): runtime hooks confirmed by deployed diagnostics and parser output.
- [Battle snapshot and allocation diagnostics](diagnostics/snapshot-and-allocation.md): snapshot fields, shadow allocation logs, parser reports, and runtime validation notes.
- [Readiness semantics](research/readiness-semantics.md): current evidence and open hypotheses for ammo/gate/shot-budget semantics.
- [Assumption audit](maintenance/assumption-audit.md): provisional assumptions that were fixed or still need follow-up.

## Directory map

- `guide/`: stable orientation documents.
- `diagnostics/`: confirmed runtime observations, log formats, and parser validation notes.
- `research/`: unsettled reverse-engineering questions and semantic investigations.
- `planning/`: durable roadmap documents that remain useful after one PR.
- `maintenance/`: documentation hygiene and assumption-audit notes.
- `archive/`: historical setup notes.

## Relationship with `dev-docs/`

`dev-docs/plan/**` is not durable documentation. It may contain per-issue or per-PR working plans, temporary context, and handoff notes. Once the related PR is merged or abandoned, those plan documents may be deleted instead of migrated. Do not treat references from `dev-docs/plan/**` as blockers for reorganizing durable `docs/` files.

## Documentation rules

- Separate confirmed runtime evidence from hypotheses.
- Do not call ammo or gate evidence `readyShots` until `research/readiness-semantics.md` says the semantics are validated.
- Keep controlled command/application work gated behind verified player-selection or command-path evidence.
- Keep temporary implementation plans in `dev-docs/plan/**`, not in durable `docs/` pages.
