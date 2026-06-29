# ADR 0001: Durable documentation structure

Date: 2026-06-23
Status: Accepted

## Context

The repository already separates durable docs under `docs/**` from disposable
working plans under `dev-docs/plan/**`. The durable docs were starting to carry
too much current state, historical status, and issue-specific context in the
same entry points.

Future coding agents need to quickly distinguish:

- current project state;
- stable architecture and safety boundaries;
- accepted decisions;
- confirmed diagnostics and research evidence;
- durable investigations;
- historical or superseded notes.

## Decision

Keep `docs/README.md` as the public durable docs entry point, but move
agent-oriented reading order and current-state orientation into `docs/agent/`.

Use these durable documentation areas:

- `docs/agent/` for concise agent reading order, current state, and workflow.
- `docs/adr/` for accepted decisions and their consequences.
- `docs/guide/` for stable architecture and boundaries.
- `docs/planning/` for durable roadmap and milestone sequencing.
- `docs/diagnostics/` for confirmed runtime evidence and validation notes.
- `docs/research/` for still-useful reverse-engineering conclusions and open
  semantic questions.
- `docs/investigations/` for investigation records promoted from temporary issue
  plans because they must remain durable.
- `docs/maintenance/` for documentation hygiene and assumption audits.
- `docs/archive/` for superseded durable notes retained only for historical
  context.

Temporary issue and PR plans remain in `dev-docs/plan/**` and may be deleted
after the related work closes. Durable docs should promote only still-useful
conclusions, not entire chronological working logs.

## Consequences

- Future agents have a short durable reading path before diving into detailed
  diagnostics or research.
- `docs/README.md` can stay concise instead of becoming the current-state dump.
- Accepted documentation structure is itself recorded as an ADR.
- Issue-specific investigations have a durable destination only when they need
  to outlive disposable plans.
- Historical notes can be retained without being mistaken for current guidance.
- Maintainers must keep `docs/agent/CURRENT_STATE.md` concise and update it when
  durable facts or blockers materially change.
