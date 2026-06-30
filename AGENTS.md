# AGENTS.md

Instructions for AI coding agents working in this repository.

## Repository Posture

This is a conservative, diagnostics-first Terra Invicta missile fire-control mod.
Keep changes small and reviewable. Do not introduce behavior-changing combat
logic unless the user explicitly asks for that phase and the local docs support
it.

The current project direction is measurement-first offline fitting over archived
logs. Treat offline candidate replay as a filter for live validation, not as
proof of live combat improvement.

## Local Instructions To Read

Before planning, coding, committing, or opening/updating a PR, read the relevant
repository-local instructions:

- `.github/copilot-instructions.md`
- `.github/pull_request_template.md` before creating or editing a PR
- `dev-docs/plan/issue_6/00-context.md` for Issue #6 slices
- issue-specific files under `dev-docs/plan/issue_<number>/`
- durable docs under `docs/diagnostics/`, `docs/research/`, and
  `docs/planning/` when the task touches those areas

If instructions conflict, follow the most specific local instruction that
applies to the current task, unless a higher-priority user/developer/system
instruction says otherwise.

## PR Requirements

Do not create a generic PR body. Use `.github/pull_request_template.md`
directly and fill every section honestly:

- Summary
- Change type
- Scope
- Non-goals
- Live combat behavior
- Implementation notes
- Validation
- Reverse-engineering notes
- Risk
- Rollback
- Screenshots / logs

PR titles should include the local change category when useful, especially for
early slices:

- `scaffold-only: ...`
- `docs-only: ...`
- `diagnostics-only: ...`
- `core-only: ...`
- `behavior-changing: ...`

When a user requests a PR to a specific branch, use that branch as the base.
Default new PRs to draft unless the user explicitly asks for ready-for-review.
After creating or updating a PR, read back the final title, base, head, draft
state, and URL.

## Location of Source

Decompiled source of Terra Invicta is in `../TI_RE_Workspace`. Refer to `../TI_RE_Workspace/graphify-out/.slices/missile-fire-control-master` to map decompiled classes/methods to the original assembly. Don't copy decompiled code into this repository.

## Commit Requirements

Use clear imperative commit subjects, ideally under 72 characters, such as:

- `Add combat launch diagnostics`
- `Fix try-fire target identity fallback`
- `Document apply-gate runtime validation`

Prefer phase-sized commits for issue implementation work unless the phase would
be artificially tiny or tightly coupled. Do not mix unrelated work in one
commit.

## Safety Boundaries

Keep game integration thin:

- `MissileFireControl.Core` stays independent of Terra Invicta, Unity, Harmony,
  and UMM.
- `MissileFireControl.Mod` owns UMM/Harmony entrypoints, settings, diagnostics,
  and game-facing glue.
- Diagnostics and behavior-changing patches must stay separate.
- When required game state is missing, log explicit missing/unknown reasons and
  fail closed.

For combat/modding PRs, document inspected or patched Terra Invicta classes and
methods. Do not claim runtime validation unless it was actually performed.

