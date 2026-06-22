# Phase 01: Discovery and safety boundary

## Goal

- Establish the exact #37 live-command boundary and prove the implementation should remain narrower than future group/fleet automation.

## Scope

- Read issue #37, #36 results, selected-scope research, diagnostics docs, and the reviewed decompiled command path.
- Identify source files and parser/report additions needed for the first live apply.

## Non-goals

- No code changes outside planning in this phase.
- No new reverse-engineering claims beyond inspected command-path source.

## Affected files

- `dev-docs/plan/issue_37/*`

## Implementation steps

- Confirm #36 runtime produced one eligible selected-ship candidate blocked by `blockedBySafetyToggle`.
- Confirm reviewed command path and command granularity.
- Record validation commands and runtime smoke expectations.

## Acceptance criteria

- Plan states the only reviewed operation for #37.
- Plan keeps the first attempt to at most one explicit selected player ship and one target.
- Plan names skip/fail as the safe outcome for ambiguity.

## Validation commands

- python tools\check_layout.py

## Manual smoke tests

- Not applicable for discovery.

## Rollback risks

- Plan-only changes are reversible by deleting `dev-docs/plan/issue_37/00-master-plan.md` and phase files.

## Progress

- Completed.

## Decision log

- Use `SelectSalvoTargetCommand.OnCommandExecute(TISpaceShipState, CombatTargetableState)` as the single reviewed command path.
- Do not use fleet command templates or direct weapon/ammo/cooldown mutations in #37.
- Use parser fixture coverage for result rows; require real runtime smoke separately before claiming live success.

## Outcomes / Retrospective

- #36 runtime evidence is sufficient to proceed to a first bounded live attempt: one eligible candidate, selected ship `El Alamein` id `276`, target `Centaur` id `277`, apply gate blocked by `blockedBySafetyToggle`, zero applied commands, zero scope violations.
- Decompiled-source review confirms `SelectSalvoTargetCommand.OnCommandExecute` queues primary target and salvo mode changes via `ship.faction.playerControl.StartAction(...)`.
