#!/usr/bin/env python3
"""Tiny Python mirror of the initial heuristic for quick sanity checks.

This is not used by the mod. It documents the intended allocation behavior in a way
that can run before the C# project is wired to Terra Invicta.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Target:
    name: str
    pd_score: float
    value: float
    required_leakers: int
    launch_score: float


def allocate(ready: int, targets: list[Target], safety_margin: int = 2) -> list[tuple[str, int, str]]:
    candidates = []
    for target in targets:
        saturation = int(target.pd_score + 0.999) + 1
        kill = int(target.pd_score + 0.999) + target.required_leakers + safety_margin
        if target.launch_score < 0.35:
            continue
        candidates.append((target.value * target.launch_score / kill, target, saturation, kill))

    plan: list[tuple[str, int, str]] = []
    for _score, target, saturation, kill in sorted(candidates, reverse=True, key=lambda item: item[0]):
        if ready >= kill:
            plan.append((target.name, kill, "kill package"))
            ready -= kill
        elif ready >= saturation:
            plan.append((target.name, ready, "partial saturation"))
            ready = 0
        if ready <= 0:
            break
    return plan


if __name__ == "__main__":
    sample_targets = [
        Target("PD Destroyer", pd_score=8.5, value=95, required_leakers=3, launch_score=0.72),
        Target("Damaged Corvette", pd_score=2.0, value=40, required_leakers=1, launch_score=0.90),
        Target("Receding Battleship", pd_score=12.0, value=140, required_leakers=5, launch_score=0.22),
    ]
    for target, shots, reason in allocate(ready=18, targets=sample_targets):
        print(f"{shots:2d} -> {target:20s} {reason}")
