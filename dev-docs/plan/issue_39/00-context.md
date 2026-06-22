# Issue #39 context

This is local context for Codex planning, not a phased implementation plan.

## Role in #6

Issue #39 closes the first learning loop. It uses controlled experiment reports to decide whether one small allocator heuristic/rule/parameter adjustment is justified by observed evidence.

This issue should not add new live command behavior. It is about evidence interpretation, bounded tuning, validation, and documentation.

## Planning information for Codex

Codex should treat controlled experiment evidence as the starting point, not synthetic fixtures alone. A valid outcome can be either a small justified heuristic adjustment or an explicit decision that no tuning is justified yet because evidence is insufficient.

Potential tuning families include target value weighting, PD risk scaling, launch-window score weighting, kill/saturation salvo sizing margin, or partial saturation threshold. The issue should not change multiple unrelated families in one PR.

## Validation/report emphasis

The before/after comparison matters more than the code diff size. The plan should preserve synthetic fixture validation, old-log and fresh-log fitting reports, controlled-experiment report regeneration, before/after classification summary, and known evidence gaps.

The report should make overfitting risk explicit. One anecdotal combat can justify a cautious hypothesis or no-op decision, but it should not be presented as broad controlled-live readiness.

## Boundary

Do not broaden automation scope. Do not add live command paths. Do not claim readiness beyond the controlled evidence actually reviewed.
