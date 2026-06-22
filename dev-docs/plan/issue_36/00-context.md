# Issue #36 context

This is local context for Codex planning, not a phased implementation plan.

## Role in #6

Issue #36 introduces the final hard-stop safety gate before any live command application. The slice may route eligible dry-run command plans up to a named apply boundary, but every command must still be blocked when command application is not explicitly allowed.

This remains a no-live-command slice.

## Context carried from earlier slices

#34 should supply the controlled experiment envelope and parser grouping. #35 should supply command-plan resolvability and selected-scope safety summaries. #36 should then make the command-application boundary explicit and auditable.

## Planning information for Codex

The plan should preserve a two-step safety model: controlled experiment mode and an explicit command-application allow toggle. Both concepts should be disabled by default or command-blocking by default. The hard-stop boundary should be easy to search and easy to rollback.

Logs should distinguish safety-gate blocks from evidence-missing skips and command failures. A candidate blocked by safety toggle is different from a candidate that could not resolve launcher/weapon/target identity.

## Parser/report emphasis

The report should have a separate safety-gate-blocked count. The expected #36 validation state is: controlled dry-run can run, eligible command plans can reach the named boundary, all candidates are blocked by the hard-stop gate, and applied command count remains zero.

## Boundary

Do not call vanilla command/action APIs in this issue. Do not broaden selected scope. Do not tune heuristic parameters. Manual control should remain unaffected because nothing is applied.
