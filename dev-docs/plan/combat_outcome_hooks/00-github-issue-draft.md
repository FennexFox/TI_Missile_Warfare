# GitHub issue draft — RE combat outcome hooks for missile attribution

## Title

RE combat outcome hooks for missile hit/intercept/kill attribution

## Body

### Background

Issue #39 established a selected-group controlled evidence path for missile allocation tuning:

- controlled command rows receive `commandResultId`;
- `MissileWeapon.TryFire` rows can be directly correlated through `directRuntimeContext`;
- launch rows expose `targetStateId` to bridge command target ids to runtime target objects;
- parser/report tooling records conservative post-direct-launch `DestroyShip` outcome hints;
- skipped controlled-command rows are kept causally separate from applied launch rows.

This is sufficient for bounded heuristic work such as same-target duplicate kill-package suppression or target-level aggregate controlled-command caps. It is not sufficient for exact projectile, hit, intercept, damage, or kill attribution.

### Problem

Current diagnostics can say:

```text
controlled command -> directly correlated missile launches/spend -> later same-target DestroyShip hint
```

They cannot safely say:

```text
this projectile hit / missed / was intercepted / caused damage / caused the kill
```

`DestroyShip` text is useful outcome-quality evidence, but it is not unique projectile or command attribution. For future fleet-wide fitting and outcome-aware evaluation, the mod needs a separate reverse-engineering track to find stable combat outcome hooks.

### Goal

Find and validate safe, diagnostics-only Terra Invicta combat hooks that can report missile outcome events and, where possible, connect them back to launch evidence or `commandResultId`.

Candidate outcome levels, in increasing precision:

1. projectile expired / removed;
2. projectile missed or lost target;
3. projectile intercepted by PD;
4. projectile hit target;
5. damage packet applied to target;
6. target disabled or destroyed;
7. destroy/disable cause attributable to projectile, launcher, or command context.

### Scope

This issue is research and diagnostics only.

Allowed work:

- inspect Terra Invicta managed code with dnSpy/ILSpy;
- identify stable candidate hooks around projectile lifecycle, hit handling, PD interception, damage application, and ship destruction;
- add diagnostics-only Harmony patches behind safe guards if a stable signature is found;
- log compact outcome rows with launcher/projectile/target ids when safe;
- extend parser/report tooling to summarize outcome rows separately from command-spend rows;
- document which outcome levels are confirmed, provisional, or unavailable.

Non-goals:

- do not change allocator heuristics;
- do not change live command behavior;
- do not broaden selected/fleet command scope;
- do not treat vanilla `DestroyShip` text as exact kill attribution;
- do not require this issue as a blocker for the immediate same-target cap follow-up;
- do not implement #44 corpus/ledger infrastructure here, except minimal compatibility notes.

### Relationship to other issues

- #39: provides direct command-spend evidence and conservative outcome hints for bounded selected-group tuning.
- #44: should provide repeated experiment corpus/ledger infrastructure; this outcome hook work becomes more valuable once results can be stored and compared across logs.
- #43: fleet-wide controlled allocation can proceed without exact hit/kill attribution, but outcome hooks would improve later fleet-wide quality evaluation.

Recommended ordering:

```text
#39 same-target cap validation -> #44 corpus/ledger -> this outcome-hook RE issue -> #43 outcome-aware evaluation improvements
```

This issue may run before #43 if exact outcome fidelity becomes necessary, but it should not block the immediate #39 same-target rule follow-up.

### Acceptance criteria

- Candidate hook inventory exists with class/method names and signature stability notes.
- At least one of the following is true:
  - stable diagnostics-only hook(s) are implemented and validated in a fresh combat log; or
  - documented source review explains why no safe stable hook was found yet.
- Any implemented hook logs compact rows with enough identity fields to compare against launch evidence:
  - projectile id or object identity when available;
  - launcher id/name when available;
  - target id/name and `targetStateId`-like bridge when available;
  - outcome type;
  - timestamp/sequence;
  - correlation limitations.
- Parser/report output distinguishes:
  - controlled command-spend evidence;
  - vanilla spillover launches;
  - conservative `DestroyShip` hints;
  - precise outcome-hook rows, if available.
- Docs clearly state which attribution claims are supported and which remain unsupported.

### Validation commands

Use the standard repo checks where feasible:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
python -m compileall tools
```

If hooks are implemented, validate with a fresh combat log and record the result in `docs/diagnostics/runtime-validation-history.md`.

### Notes

This issue should be kept separate from immediate heuristic changes. It is a deeper measurement layer for future outcome-aware fitting, not a prerequisite for the selected-group same-target cap work.
