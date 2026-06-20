# Architecture

## Principle

Keep game integration thin and heuristic logic testable.

```text
Terra Invicta combat objects
        ↓
Mod adapter / snapshot extractor
        ↓
MissileFireControl.Core pure model
        ↓
Allocation / launch-window recommendation
        ↓
Diagnostics or future command application
```

## Boundaries

### Core

`MissileFireControl.Core` must not reference Terra Invicta, Unity, Harmony, or UMM. It owns:

- `ShipSnapshot`
- `WeaponSnapshot`
- `MissileProfile`
- `PDScoreCalculator`
- `TargetValueCalculator`
- `SalvoPackageCalculator`
- `LaunchWindowEvaluator`
- `SalvoAllocator`

This lets us tune the model without repeatedly loading the game.

### Mod

`MissileFireControl.Mod` owns:

- UMM entry point.
- Harmony patches.
- Reflection or direct calls into Terra Invicta combat objects.
- Snapshot extraction.
- UI, debug logs, and future command application.

Patches should stay small. A patch should read the minimum data, call Core, and either log or apply a decision.

## Heuristic model

The initial model uses three scores:

```text
PDScore(target) = target own PD + nearby support PD weighted by distance
TargetValue(target) = threat + PD removal value + hull value + priority - disabled penalty
SalvoPackage(target) = estimated PD kills + required leakers + safety margin
```

Launch discipline adds:

```text
LaunchWindowScore = range term + approach/recede term - lateral velocity penalty
```

This is intentionally explainable rather than physically exact. Later, logged combat data can tune weights or replace parts with LUTs.

## Do not do in early versions

- Do not patch missile projectile physics.
- Do not rewrite guidance/burn behavior.
- Do not override AI for all factions before player-command helpers work.
- Do not assume weapon or class names until confirmed from `Assembly-CSharp.dll`.
