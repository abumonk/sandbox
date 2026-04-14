# Plan: Audit and Backend Foundation (Wave A)

## Designs Covered
- design-simplification-audit: UI audit table
- design-backend-endpoints: server.py extensions
- design-test-strategy: test strategy doc (gating)

## Tasks

### Design test strategy for ADV-009 console v2
- **ID**: ADV009-T001
- **Description**: Author `.agent/adventures/ADV-009/tests/test-strategy.md`
  mapping every TC with `proof_method: autotest` to a named test function
  in a named test file (see design-test-strategy.md). Declare the three
  stdlib-unittest files (`test_server.py`, `test_ui_smoke.py`,
  `test_ui_layout.py`) and the full run command. Include the
  `data-testid` contract list as an appendix.
- **Files**: `.agent/adventures/ADV-009/tests/test-strategy.md`
- **Acceptance Criteria**:
  - Every `autotest` TC appears at least once in the strategy's mapping
    table.
  - Test framework choice (stdlib `unittest`), three test files, and run
    command are explicit.
  - The `data-testid` appendix lists every hook id used by the designs.
- **Target Conditions**: TC-034, TC-035
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: test planning, markdown authoring
  - Estimated duration: 12 min
  - Estimated tokens: 18000

### Simplification audit of the current console
- **ID**: ADV009-T002
- **Description**: Produce `.agent/adventures/ADV-009/research/audit.md`
  cataloging every UI element in the current console with a
  `keep / hide-behind-toggle / remove` verdict and a v2 target surface.
  Drive the verdicts from the user's requirements in the manifest concept
  (5-second glance, no raw paths / frontmatter / log dumps by default).
- **Files**: `.agent/adventures/ADV-009/research/audit.md`
- **Acceptance Criteria**:
  - ≥ 30 distinct elements enumerated.
  - Every row has a `verdict` in the allowed set.
  - Every current-tab dispatch branch (overview/designs/plans/tasks/
    permissions/reviews/knowledge/research/log) has ≥ 1 row.
  - Summary line at top: "X kept · Y hidden · Z removed".
- **Target Conditions**: TC-001, TC-002, TC-003
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: UX analysis, markdown
  - Estimated duration: 20 min
  - Estimated tokens: 30000

### Add AdventureSummary to server.py
- **ID**: ADV009-T003
- **Description**: Extend `get_adventure()` to include a `summary` object
  with TC counts, task-status counts, and `next_action` (see
  design-backend-endpoints). Add `compute_next_action()` helper.
  Stdlib-only. No new fields persisted.
- **Files**: `.agent/adventure-console/server.py`
- **Acceptance Criteria**:
  - `GET /api/adventures/{id}` responses include a `summary` block with
    all declared fields.
  - `compute_next_action` handles every state enum value.
  - No new third-party imports added.
- **Target Conditions**: TC-026, TC-029, TC-030
- **Depends On**: [ADV009-T001]
- **Evaluation**:
  - Access requirements: Read, Edit, Bash (python -m unittest)
  - Skill set: Python 3 stdlib HTTP, JSON, frontmatter parsing
  - Estimated duration: 18 min
  - Estimated tokens: 45000

### Add GET /api/adventures/{id}/documents endpoint
- **ID**: ADV009-T004
- **Description**: Implement a new handler that returns a unified list of
  designs/plans/research/reviews with per-type metadata
  (`one_liner`, `task_count`, `waves`, `status`, `task_id`). Route it in
  `do_GET`. Stdlib-only.
- **Files**: `.agent/adventure-console/server.py`
- **Acceptance Criteria**:
  - `GET /api/adventures/{id}/documents` returns JSON array of
    `DocumentEntry`.
  - A plan file with `## Wave 1` and `## Wave 2` headings reports
    `waves: 2`.
  - Designs include a `one_liner` parsed from the first sentence of
    `## Overview` (≤120 chars).
  - No new third-party imports.
- **Target Conditions**: TC-027, TC-028, TC-030
- **Depends On**: [ADV009-T001]
- **Evaluation**:
  - Access requirements: Read, Edit, Bash (python -m unittest)
  - Skill set: Python 3 stdlib HTTP, regex
  - Estimated duration: 20 min
  - Estimated tokens: 50000
