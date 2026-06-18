# Graphify Snapshot

This directory intentionally tracks a small Graphify snapshot for human and
agent reviewers. The report, graph JSON, labels, cost metadata, and HTML view
are committed so review can inspect the current architecture map without
rebuilding the graph locally.

Ignored files under `graphify-out/` are limited to cache, manifest, interpreter,
temporary extraction, and chunk files that are machine-local or regenerated
during a Graphify run.

`GRAPH_REPORT.md` may call out isolated or low-cohesion nodes. Those findings
are review guidance for the current early scaffold, not a requirement to remove
the snapshot from version control. Isolated nodes are expected while diagnostic
and allocation components are still being wired together.
