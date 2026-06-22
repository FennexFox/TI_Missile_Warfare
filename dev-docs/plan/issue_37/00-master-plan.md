# First single-ship live controlled apply

## Issue Target And Scope Summary

- Issue target: #37
- Title: First single-ship live controlled apply
- Source context: GitHub issue #37, `00-context.md`, #36 plan/results, `docs/diagnostics/snapshot-and-allocation.md`, `docs/diagnostics/runtime-validation-history.md`, and `docs/research/selected-command-scope.md`
- Scope: implement the first behavior-changing controlled command boundary for at most one eligible selected player missile ship and one resolved target, behind the existing controlled trigger and explicit `AllowCommandApply` safety toggle.

## Strategy

- Preserve the #34-#36 envelope: no continuous automation, retries, unselected ships, AI ships, broad fleet selection, projectile physics changes, cooldown mutation, ammo mutation, or heuristic tuning.
- Treat the reviewed vanilla command path as the only live operation for #37: `SelectSalvoTargetCommand.OnCommandExecute(TISpaceShipState, CombatTargetableState)`, which queues `SetCombatPrimaryTargetAction` and `SetWeaponModeAction(..., FireMode.Salvo)` through the game's player action runner.
- Keep Terra Invicta coupling inside `MissileFireControl.Mod` and use reflection/runtime objects already captured by `ExtractedCombatSnapshot`.
- Attempt at most one eligible candidate per explicit experiment. All other candidates remain dry-run diagnostics and must log as skipped.
- Emit additive command-result rows that parser/report tooling can distinguish as applied, skipped, or failed first-live-apply attempts.
- If runtime identity, selected scope, command authority, target object, command type, method lookup, or invocation result is ambiguous, skip/fail closed with an explicit reason.

## Phase Order

1. [Discovery and safety boundary](01-discovery.md)
2. [Single-command apply and parser reporting](02-implementation.md)
3. [Docs and validation](03-verification.md)

## Phase Dependencies

- Phase 1 has no phase dependency beyond resolved issue context.
- Phase 2 depends on completion and validation of phase 1.
- Phase 3 depends on completion and validation of phase 2.

## Source Of Truth Decisions

- `00-master-plan.md` is the phased implementation source of truth for #37.
- `00-context.md` is input context only.
- Runtime logging source of truth: `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`.
- Safety toggle source of truth: `src/MissileFireControl.Mod/ModSettings.cs` and `src/MissileFireControl.Mod/Main.cs`.
- Parser/report source of truth: `tools/parse_player_log.py`.
- Durable behavior docs belong in `docs/diagnostics/snapshot-and-allocation.md`, `docs/diagnostics/runtime-validation-history.md`, `docs/research/selected-command-scope.md`, and `docs/planning/mvp-roadmap.md`.

## Global Validation Expectations

- dotnet build TI_Missile_Fire_Control.sln
- python tools\check_layout.py
- python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
- python -m compileall tools
- python tools\parse_player_log.py tools\fixtures\first_live_apply.txt --require-launchlogs --require-snapshots

## Known Risks And Assumptions

- This is the first behavior-changing slice; runtime smoke is still required before claiming live success.
- Source review confirms the vanilla single-ship salvo target command path, but local static validation can only prove schema/parser behavior.
- `SelectSalvoTargetCommand.OnCommandExecute` has broader ship-level granularity than one module. #37 accepts that only for one selected ship and logs `shipAllSalvoCapableWeapons`.
- The controlled apply toggle remains default-off; enabling it plus pressing the trigger is required for any live attempt.
- If the first runtime attempt skips or fails for a safety reason, that can still satisfy the containment goal if the log proves at most one bounded attempt and no scope violation.
