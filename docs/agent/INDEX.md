# Agent docs index

This is the first durable reading path for coding agents working on
TI MissileWarfare.

## Reading order

1. [Current state](CURRENT_STATE.md)
2. [Architecture](../guide/architecture.md)
3. [MVP roadmap](../planning/mvp-roadmap.md)
4. [Confirmed combat launch hooks](../diagnostics/hooks.md)
5. [Battle snapshot and allocation diagnostics](../diagnostics/snapshot-and-allocation.md)
6. [Readiness semantics](../research/readiness-semantics.md)
7. [Selected command scope](../research/selected-command-scope.md)
8. [Agent workflow](WORKFLOW.md)
9. [ADR index](../adr/README.md)

Read issue-specific files under `dev-docs/plan/**` only when the current task
is for that issue or PR. Those files are working notes, not durable project
state.

## Durable docs by purpose

- `docs/agent/`: short orientation for future agents.
- `docs/guide/`: stable architecture and design boundaries.
- `docs/planning/`: durable roadmap and long-lived sequencing notes.
- `docs/diagnostics/`: confirmed runtime observations, schemas, and validation
  evidence.
- `docs/research/`: still-useful reverse-engineering conclusions and open
  semantic questions.
- `docs/investigations/`: durable investigation records promoted from temporary
  issue work.
- `docs/adr/`: accepted decisions and their consequences.
- `docs/maintenance/`: documentation hygiene and assumption audits.
- `docs/archive/`: superseded notes retained only for historical context.

## Ground rules

- Treat `CURRENT_STATE.md` and `planning/mvp-roadmap.md` as summaries, not proof.
  Follow their links before changing behavior.
- Do not copy decompiled Terra Invicta source into this repository.
- Mark uncertain claims as `Needs verification:` with the missing evidence.
- Keep live combat behavior unchanged unless the task explicitly asks for a
  behavior-changing phase and the relevant docs support it.
