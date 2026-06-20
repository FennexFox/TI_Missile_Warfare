# Development docs

`dev-docs/` is for temporary implementation context that helps finish a current issue or PR. It is not the durable product documentation set.

## Plan document lifecycle

- Put per-issue and per-PR working plans under `dev-docs/plan/<issue-or-pr>/`.
- Treat those plan documents as disposable after the related PR is merged, closed, or abandoned.
- Delete completed plan folders instead of preserving them as long-term references.
- Do not block `docs/` reorganization because a `dev-docs/plan/**` file still points at an old durable-doc path.
- Promote only still-useful conclusions into `docs/` before deleting a plan folder.

Durable architecture, diagnostics, roadmap, and research notes belong under `docs/`.
