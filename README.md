# TI MissileWarfare

Experimental Terra Invicta MissileWarfare mod scaffold for missile salvo allocation, launch-discipline research, and diagnostics-first offline fitting.

This repository is still conservative and experimental. It has moved beyond the initial scaffold into a diagnostics and archived-log fitting phase, but behavior-changing launch logic should remain gated behind evidence and explicit review.

## Scope

Planned core features:

- **Auto Salvo Allocation**: assign ammo/gate-budgeted missile shots to enemy ships in package-sized salvos instead of scattering shots too thinly.
- **Launch Discipline**: avoid firing when range, relative velocity, or salvo size makes the launch likely to waste missiles.
- **Diagnostics First**: log battle snapshots and launch decisions so heuristics can be replayed, scored, and validated before live behavior changes.
- **Offline Fitting First**: use archived logs as a fixed dataset for candidate-policy replay before spending live combat validation time.

Explicit non-goals for the first version:

- Rewriting missile guidance, burn, or projectile physics.
- Rebalancing missile stats.
- Fully replacing Terra Invicta combat AI.

## Repository layout

```text
src/MissileFireControl.Core/   Pure C# heuristic model and allocation logic.
src/MissileFireControl.Mod/    Unity Mod Manager / Harmony entry points and future patches.
docs/                          Architecture, reverse-engineering plan, and MVP issue list.
tools/                         Deterministic repo checks and local helper scripts.
ModInfo.json                   UMM metadata copied beside the built DLL.
```

`Core` is deliberately game-independent. `Mod` should stay as a thin adapter over Terra Invicta / Unity / Harmony APIs.

## Suggested first commit

```bash
git init
git add .
git commit -m "Initial missile fire-control mod scaffold"
```

## Local setup notes

Code-mod work is expected to use:

- Visual Studio or MSBuild-compatible C# tooling.
- Unity Mod Manager.
- Harmony / 0Harmony from UMM or a local copy.
- Terra Invicta managed assemblies from `TerraInvicta_Data/Managed`.

Create a local `Directory.Build.props` from `Directory.Build.props.example` and point it at your installed Terra Invicta and Unity Mod Manager paths. Do **not** commit your local paths.

```powershell
copy Directory.Build.props.example Directory.Build.props
```

Then edit the properties:

```xml
<TerraInvictaManagedDir>C:\Program Files (x86)\Steam\steamapps\common\Terra Invicta\TerraInvicta_Data\Managed</TerraInvictaManagedDir>
<UnityModManagerDir>C:\Tools\UnityModManager</UnityModManagerDir>
```

## Validation

The scaffold includes a deterministic layout check that does not require Terra Invicta or UMM:

```bash
python tools/check_layout.py
```

Once local references are configured, build and deploy the UMM mod folder for in-game testing:

```powershell
.\build.ps1
```

If you do not want to create `Directory.Build.props`, pass local paths directly:

```powershell
.\build.ps1 -GameDir "C:\Program Files (x86)\Steam\steamapps\common\Terra Invicta" -UnityModManagerDir "C:\Tools\UnityModManager"
```

The script stages the mod in `dist/MissileWarfare` and deploys it to `Terra Invicta/Mods/Enabled/MissileWarfare`. Use `-NoDeploy` to only build and stage the folder, or `-Configuration Release` for a release build.

If the mod project is too brittle at first, build only `MissileFireControl.Core` and keep `MissileFireControl.Mod` as a patching shell until the real game methods are identified.

## Development strategy

1. **Log only**: identify battle, weapon, and launch-method entry points; record launch events without changing behavior.
2. **Offline fitting**: turn archived logs into allocation decision-context datasets and replay candidate policies outside the game.
3. **Candidate filtering**: rank pressure, allocation, and launch-discipline candidates with surrogate objectives and hard guardrails.
4. **Manual recommendation**: expose a debug panel or log output that recommends salvo packages.
5. **Controlled command helper**: add or expand player-triggered Auto Allocate behavior only after offline evidence and live safety gates support it.
6. **Launch discipline**: optionally suppress or delay poor launches after scoring inputs and validation are reliable.
7. **Experimental patches**: only after the fire-control layer is reliable, consider deeper launch-method replacement.
