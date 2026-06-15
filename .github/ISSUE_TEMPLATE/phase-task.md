---
name: Phase task
description: Track one independently reviewable implementation phase
title: "Phase: "
labels: ["phase", "modding"]
body:
  - type: textarea
    id: goal
    attributes:
      label: Goal
      description: What should this phase achieve?
    validations:
      required: true
  - type: textarea
    id: scope
    attributes:
      label: Scope
      description: Files, systems, and behavior included in this phase.
    validations:
      required: true
  - type: textarea
    id: non_goals
    attributes:
      label: Non-goals
      description: What must not be changed in this phase?
  - type: textarea
    id: acceptance
    attributes:
      label: Acceptance criteria
      value: |
        - [ ]
        - [ ]
        - [ ]
    validations:
      required: true
  - type: textarea
    id: validation
    attributes:
      label: Validation commands / manual smoke tests
      value: |
        ```bash
        python tools/check_layout.py
        ```
  - type: textarea
    id: risks
    attributes:
      label: Risks and rollback
