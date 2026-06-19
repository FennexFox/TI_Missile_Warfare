# Issue #11 Phase 04 smoke report

## Fresh runtime validation

- Log parsed: active `Player.log`
- Parser command: `python tools/parse_player_log.py --require-launchlogs --require-snapshots`
- Parser verdict: `OK`
- Launch window: `2026-06-19T08:26:32.1817341Z` through `2026-06-19T08:30:57.9316235Z`
- Diagnostics bootstrap: `patched=3`, `skipped=0`
- LaunchLog entries: 21,474
- Sequence range: `1-21474`
- Sequence gaps: none
- Duplicate sequences: none
- MissileWarfare issues: none

## Pre-fire evidence

- Successful `MissileWeapon.TryFire` rows: 670
- All seven `preFire*` fields present: 670/670
- `preFireAmmoEvidenceSource=shipAmmoByWeaponData`: 670/670
- Numeric `preFireRemaining` and `postFireRemaining` pairs: 670/670
- `preFireRemaining - postFireRemaining = 1`: 670/670

The observed relationship is consistent with the Harmony prefix reading
`TISpaceShipState.ammo[weaponData]` before `TISpaceShipState.FireWeapon`
decrements ammo, and the postfix reading the same ammo state after the
decrement.

## Ready-shot conclusion

The Harmony prefix is observation-only. It returns normally and does not skip,
suppress, or alter the original `MissileWeapon.TryFire` method.

`preFireRemaining` is ammo-state evidence. It is not automatically a true
ready, loaded, or chambered `readyShots` count.

`SnapshotLog readyShots` remains `unknown`: 670/670 snapshots in the smoke log
reported `readyShots=unknown`. True ready/loaded/chambered recovery is still
unavailable from the confirmed observation point and would require another
documented source before mapping anything into `SnapshotLog readyShots`.

Parser/report additions for this phase are intentionally scoped to Issue #11
ammo/readiness evidence. Allocation decision summaries and tuning reports remain
out of scope and belong to Issue #13.
