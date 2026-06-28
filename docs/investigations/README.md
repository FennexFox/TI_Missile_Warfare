# Durable investigations

Use this directory for investigation records that must outlive a temporary
issue or PR plan.

## Index

- [Issue #39 controlled correlation investigation](issue-39-controlled-correlation.md)

## Lifecycle

- Start most issue-specific investigation notes under `dev-docs/plan/**`.
- Promote only durable conclusions into `docs/investigations/` when they remain
  useful after the issue closes.
- Keep each investigation focused on evidence, conclusion, and remaining
  `Needs verification:` gaps.
- Link to confirmed diagnostics, research, or ADRs instead of copying long log
  excerpts.
- When an investigation becomes accepted architecture or policy, summarize it in
  the relevant durable doc and create or update an ADR if future work depends on
  the decision.

Do not use this directory as a permanent copy of disposable implementation
plans.
