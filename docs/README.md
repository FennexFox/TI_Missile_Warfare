# Missile Warfare docs

This directory is the durable documentation entry point for the Terra Invicta missile-warfare mod.

## Current state

The project is still diagnostics-first. Current runtime evidence can observe missile launch hooks, launcher identity, launcher-selected target identity in some cases, and paired pre/post ammo plus gate/cooldown evidence from `MissileWeapon.TryFire`.

The main unresolved design question is shot-budget semantics: whether `TISpaceShipState.ammo[weaponData]` plus known gates is the game-equivalent fireable budget, whether a distinct runtime source exists, or whether controlled allocation should avoid a numeric fleet-level budget. See [Readiness semantics](research/readiness-semantics.md).

Controlled command/application work should remain disabled until both shot-budget semantics and selected-player command scope are verified.

## Start here

- [Architecture](guide/architecture.md): high-level mod/Core boundary and design principle.
- [MVP roadmap](planning/mvp-roadmap.md): current issue-sized roadmap, completed diagnostics, blockers, and next work.
- [Reverse-engineering plan](research/reverse-engineering-plan.md): diagnostic-first plan for finding runtime combat entry points.
- [Confirmed combat launch hooks](diagnostics/hooks.md): runtime hooks confirmed by deployed diagnostics and parser output.
- [Battle snapshot and allocation diagnostics](diagnostics/snapshot-and-allocation.md): current snapshot fields, shadow allocation logs, parser behavior, and validation commands.
- [Runtime validation history](diagnostics/runtime-validation-history.md): historical smoke-test results and issue-by-issue runtime findings.
- [Readiness semantics](research/readiness-semantics.md): current evidence and open hypotheses for ammo/gate/shot-budget semantics.
- [Assumption audit](maintenance/assumption-audit.md): assumptions that were fixed or explicitly marked provisional.

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
