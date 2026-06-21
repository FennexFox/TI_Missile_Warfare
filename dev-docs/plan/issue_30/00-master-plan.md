# Run pre-Issue #6 readiness sweep across varied real combat logs

## Issue Target And Scope Summary

- Issue target: #30
- Title: Run pre-Issue #6 readiness sweep across varied real combat logs
- Scope: analyze the four available real Terra Invicta `Player*.log` combat logs with the existing parser and fitting wrapper, name any repeated severe or evidence-limited follow-up, and promote durable #6 readiness conclusions into docs.

## Strategy

Use the existing observation-only fitting wrapper without changing runtime code. Keep raw real logs and generated fitting artifacts under ignored `artifacts/` paths. Document only aggregate and per-log conclusions that are useful for #6 planning.

## Phase Order

1. [Issue context and selected log inventory](01-discovery.md)
2. [Four-log fitting analysis and follow-up triage](02-analysis.md)
3. [Durable readiness summary and issue closure](03-documentation.md)

## Phase Dependencies

- Phase 1 has no phase dependency beyond resolved issue context.
- Phase 2 depends on completion and validation of phase 1.
- Phase 3 depends on completion and validation of phase 2.

## Source Of Truth Decisions

- `docs/diagnostics/runtime-validation-history.md` is the durable source for the Issue #30 sweep result.
- `docs/planning/mvp-roadmap.md` is the durable source for next-work ordering before #6.
- `artifacts/combat-logs/issue_30_four_logs/` and `artifacts/shadow-fitting/issue_30_four_logs/` are ignored local evidence artifacts, not commit targets.
- Issue #32 is the named follow-up for the repeated evidence-limited `targetIdentity` no-op pattern.

## Global Validation Expectations

- `python tools\fit_shadow_allocation.py --input artifacts\combat-logs\issue_30_four_logs --output artifacts\shadow-fitting\issue_30_four_logs`
- `python tools\parse_player_log.py artifacts\combat-logs\issue_30_four_logs\Player.log --require-launchlogs --require-snapshots`
- Repeat the parser command for the three `Player-prev*.log` files when validating all selected logs directly.

## Known Risks And Assumptions

- The four raw logs are local real gameplay logs and should remain uncommitted.
- The fitting wrapper accepts `.txt` and `.log` recursively, so broad input directories can accidentally include non-combat files; the final Issue #30 input must stay scoped to `Player*.log`.
- Ambiguous rejection classifications are conservative fitting evidence and do not justify allocator tuning by themselves.
