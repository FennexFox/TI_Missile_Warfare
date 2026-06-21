# Phase 02: Parse and report PD capability quality

## Goal

- Make parser and fitting outputs consume the new PD capability fields while preserving legacy log behavior.

## Scope

- `tools/parse_player_log.py`
- `tools/fit_shadow_allocation.py`
- Synthetic fixtures under `tools/fixtures/`

## Non-goals

- No real combat log artifact commits.
- No change to controlled command readiness.

## Affected files

- `tools/parse_player_log.py`
- `tools/fit_shadow_allocation.py`
- `tools/fixtures/shadow_allocation_synthetic.txt`
- `tools/fixtures/shadow_allocation_missing_target_noop.txt`

## Implementation steps

- Added snapshot, allocation, and cycle-level counters for PD quality, capability source, missing reason, and limitations.
- Follow-up: added snapshot, allocation, and cycle-level counters for `pdCapabilityObservedFields`.
- Added human-readable parser summary output for the new counters.
- Extended fitting cycle context with PD quality/source fields.
- Updated `target_pd_status(...)` so missing new fields keep legacy `observedTargetWeaponTemplates` as `presenceOnly`.
- Classified `observedTemplateCapability` as `provisional` with template-only limitations.
- Kept future `geometryAwareCapability` as `provisional`; no #29 output may become `ready` by string alone.
- Updated fixtures to exercise template-capability and defaulted no-op paths.

## Acceptance criteria

- Old logs without new fields remain parseable.
- New logs can upgrade from `presenceOnly` to `provisional` only when capability quality fields are present.
- Fitting evidence output includes the static observed-field categories behind `observedTemplateCapability`.
- `geometryAwareCapability` remains `provisional` unless a future documented readiness gate proves more.
- Defaulted PD evidence remains defaulted fallback evidence.

## Validation commands

- `python -m compileall tools` - passed.
- `python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py` - passed.
- `python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_29_synthetic` - passed with expected synthetic-only `Not ready` verdict.
- `python tools\parse_player_log.py tools\fixtures\shadow_allocation_synthetic.txt --json` - passed and showed `observedTemplateCapability` counters.
- Follow-up validation: synthetic fixture PD status is `provisional` and evidence includes `capability_observed_fields` with `range` and `cooldown`.
- Follow-up validation: legacy four-log sweep remains `presenceOnly` because old logs do not contain `pdEvidenceQuality` / observed-field details.
- Follow-up validation: direct `target_pd_status(...)` check for `geometryAwareCapability` returns `provisional`, not `ready`.

## Manual smoke tests

- Reviewed generated `artifacts/shadow-fitting/issue_29_synthetic/summary.json`; observed target PD evidence classified as `provisional` with template-only/no-live/no-geometry limitations.

## Rollback risks

- Parser changes are additive but touch central summary dataclasses; compileall and fixture parsing cover syntax and schema regressions.

## Progress

- Completed.

## Decision log

- `geometryAwareCapability` is recognized by the fitter for future logs, but current C# does not emit it and the fitter keeps it provisional.
- `observedLiveCapability` is reserved for a future hook that proves target defensive weapon state.

## Outcomes / Retrospective

- Reports now distinguish legacy presence-only PD evidence from richer static template capability evidence without overclaiming.
