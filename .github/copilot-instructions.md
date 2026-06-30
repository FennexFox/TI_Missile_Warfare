# Repository instructions for GitHub Copilot

This repository is a conservative Terra Invicta missile fire-control mod project in a diagnostics and archived-log fitting phase.

## Project intent

The project should evolve as a conservative, diagnostics-first mod. Prefer small, reviewable changes that keep the game behavior unchanged until the relevant combat methods are identified and logged.

The current feature direction is:

1. Observe and log missile launch decisions.
2. Build a pure, testable fire-control core outside the game integration layer.
3. Turn archived logs into decision-context datasets for offline candidate replay.
4. Rank candidate policies with surrogate objectives and hard guardrails before live validation.
5. Add recommendation-only salvo allocation.
6. Add manual or bounded auto-allocation only when local docs and evidence support that behavior-changing phase.
7. Add launch-discipline filters only after diagnostics and scoring inputs are reliable.
8. Treat missile guidance, burn-model, and projectile-physics rewrites as experimental and out of scope for early milestones.

## Architecture conventions

Keep game integration thin.

- `MissileFireControl.Core` should contain pure C# logic and should avoid direct references to Terra Invicta, Unity, UMM, or Harmony.
- `MissileFireControl.Mod` should contain UMM/Harmony entrypoints, settings, diagnostics, and game-facing patch glue.
- Patch classes should be small adapters. Do not bury allocation logic inside Harmony patches.
- Prefer immutable or snapshot-style data models for combat state passed into the core logic.
- Keep diagnostics and behavior-changing patches separate.

## Reverse-engineering rules

When adding or changing a Harmony patch:

- Document the inspected game class and method.
- Record whether the patch is prefix, postfix, transpiler, or finalizer.
- Explain why that patch point is stable enough to use.
- Add logging first before changing behavior.
- Prefer safe no-op behavior when required game state cannot be found.
- Do not claim a patch is correct without either local testing or clear diagnostic output.

## Commit message rules

Use clear, imperative commit subjects.

Preferred subject style:

```text
<Verb> <area> <change>
```

Examples:

```text
Initialize mod scaffold
Add salvo allocation core models
Add combat launch diagnostics
Fix PD support weighting edge case
Document reverse-engineering workflow
Refactor launch-window evaluator
```

Guidelines:

- Use imperative mood: `Add`, `Fix`, `Update`, `Refactor`, `Document`, `Test`, `Build`, `Chore`.
- Keep the subject concise, ideally 72 characters or less.
- Do not end the subject with a period.
- Use a commit body when the change has non-obvious intent, tradeoffs, or validation notes.
- Mention validation commands actually run.
- Do not claim in-game validation unless it was performed.
- Separate scaffold/docs-only commits from behavior-changing commits.
- Separate reverse-engineering diagnostics from launch-behavior changes.

## Pull request rules

Before creating or updating a PR, inspect repository-local PR instructions and
templates. At minimum, read `.github/pull_request_template.md` and this
instruction file, then shape the title and body from those requirements before
opening the PR. Do not open a generic PR first and retrofit the template later.

Every PR should explain:

- What changed.
- What is intentionally out of scope.
- Whether the PR changes live combat behavior.
- Which validation commands were run.
- Which Terra Invicta classes or methods were inspected or patched, if any.
- Known risks and rollback path.

For early PRs, prefer one of these labels in the summary:

- `scaffold-only`
- `docs-only`
- `diagnostics-only`
- `core-only`
- `behavior-changing`

Use the template sections directly when creating the PR body:

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

Set checkbox states honestly from the work actually done. If runtime smoke,
mod-load validation, or in-game validation was not performed, leave that
checkbox unchecked and call out the remaining validation gap in the body.

When a user requests a PR to a specific branch, use that branch as the PR base.
Default new PRs to draft unless the user explicitly asks for ready-for-review.
After creating or updating the PR, read back the PR title, base, head, draft
state, and URL to confirm the final metadata.

## Validation expectations

For scaffold or docs-only changes:

```bash
python tools/check_layout.py
```

For core logic changes, add or run the relevant local tests once a test project exists.

For mod integration changes:

- Confirm the project builds with local Terra Invicta and UMM references.
- Confirm the mod loads.
- Confirm diagnostics are visible.
- Confirm the game still behaves normally when the feature is disabled.

## Local-only files

Do not commit local machine paths, copied game assemblies, UMM binaries, build outputs, or private reverse-engineering dumps.

Expected local-only files include:

- `Directory.Build.props`
- `bin/`
- `obj/`
- local logs
- local packaged mod zips
- copied Terra Invicta assemblies
- copied Unity Mod Manager assemblies
