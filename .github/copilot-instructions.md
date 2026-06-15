# Repository instructions for GitHub Copilot

This repository is an early scaffold for a Terra Invicta missile fire-control mod.

## Project intent

The project should evolve as a conservative, diagnostics-first mod. Prefer small, reviewable changes that keep the game behavior unchanged until the relevant combat methods are identified and logged.

The initial feature direction is:

1. Observe and log missile launch decisions.
2. Build a pure, testable fire-control core outside the game integration layer.
3. Add recommendation-only salvo allocation.
4. Add manual auto-allocation.
5. Add launch-discipline filters only after diagnostics are reliable.
6. Treat missile guidance, burn-model, and projectile-physics rewrites as experimental and out of scope for early milestones.

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
