# Agent workflow

Use this workflow when updating durable docs.

## Before editing

1. Read [Current state](CURRENT_STATE.md) and [Architecture](../guide/architecture.md).
2. Read the narrow durable docs for the area you are touching.
3. Read `dev-docs/plan/**` only when it is directly relevant to the current
   issue, PR, or user prompt.
4. Check whether an accepted decision already exists under `docs/adr/`.

## Where to put information

- Put stable architecture and project boundaries in `docs/guide/`.
- Put current issue sequencing and durable roadmap status in `docs/planning/`.
- Put confirmed runtime observations, schemas, parser behavior, and validation
  evidence in `docs/diagnostics/`.
- Put unsettled or still-useful reverse-engineering conclusions in
  `docs/research/`.
- Put durable investigation records in `docs/investigations/` only when the
  conclusion must outlive a disposable issue plan.
- Put accepted durable decisions in `docs/adr/`.
- Put superseded durable docs in `docs/archive/` only when deletion would lose
  useful context.

## How to write durable docs

- Prefer current conclusions, evidence links, and explicit remaining gaps over
  long chronological notes.
- Mark uncertain claims as `Needs verification:` and name the missing evidence.
- Keep issue-local progress logs in `dev-docs/plan/**`, not durable docs.
- Do not make completion claims for issues unless the repo has evidence.
- Preserve diagnostics-first boundaries: docs may describe future behavior, but
  must not imply that live combat behavior changed unless it did.
- When documenting tuning work, distinguish offline candidate fitting from live
  controlled validation. Offline fitting can rank candidates, but it is not proof
  of live combat improvement.

## ADR practice

Create an ADR when a decision is expected to guide future work across multiple
issues or PRs.

Use this shape:

```md
# ADR NNNN: Title

Date: YYYY-MM-DD
Status: Accepted | Proposed | Superseded

## Context

## Decision

## Consequences
```

When a decision changes, add a new ADR and mark the older one as superseded
instead of rewriting history.
