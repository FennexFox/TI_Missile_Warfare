# Phase 1: Schema documentation

## Goal

Define the durable experiment corpus and parameter ledger contract for #44.

## Scope

- Add `docs/diagnostics/experiment-corpus.md`.
- Define registry, metadata, parameters, verdict, and summary semantics.
- Explicitly separate fixture, shadow replay, controlled-live, and future fleet-wide evidence modes.
- Document that private raw logs remain local by default.

## Non-goals

- No allocator tuning.
- No live command behavior changes.
- No game automation or external database.

## Affected Files

- `docs/diagnostics/experiment-corpus.md`
- `dev-docs/plan/issue_44/01-schema-docs.md`

## Implementation Steps

- Document run mode meanings and evidence interpretation.
- Document registry JSONL required and optional fields.
- Document parameter snapshot, scenario metadata, manual verdict, and generated summary outputs.

## Acceptance Criteria

- The docs describe how future fitting loops append new runs without overwriting old evidence.
- The docs state that shadow replay is not causal combat proof.
- Parameter provenance and manual verdict capture are documented without requiring parser code changes.

## Validation Commands

- `python tools\check_layout.py`
- `python -m compileall tools`

## Manual Smoke Tests

- Read the new doc and confirm the registry and output paths are usable without committing private raw logs.

## Rollback Risks

- Docs-only rollback is safe and does not affect runtime behavior.

## Progress

- Completed durable corpus documentation.

## Decision Log

- Chose repo-relative paths in registry entries so ignored local artifacts and committed fixtures use the same schema.
- Chose JSONL for append-friendly registry history and separate JSON files for mutable reviewer verdicts.

## Outcomes / Retrospective

- The schema is lightweight enough for local fitting loops and explicit enough for later #43 fleet-wide evaluation to consume.
