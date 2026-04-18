# Plan — Wave C: Task Actuals Pipeline

## Designs Covered

- designs/design-aggregation-rules.md §Task actuals propagation
- designs/design-capture-contract.md §task-update

Wires the path from a captured row to the matching row in the
manifest's `## Evaluations` table, computing `Actual Duration /
Actual Tokens / Actual Cost / Variance`.

## Tasks

### Task actuals module

- **ID**: ADV010-T009
- **Description**: Implement
  `.agent/telemetry/task_actuals.py`:
  `update(manifest_path, task_id)`. Parses the `## Evaluations`
  table, finds the row for `task_id`, computes actuals from the
  adventure's `metrics.md`, rewrites that single row in place. All
  other bytes in the manifest preserved. Emits `Variance` against
  `Est. Tokens`.
- **Files**:
  - `.agent/telemetry/task_actuals.py` (new)
- **Acceptance Criteria**:
  - Given fixture manifest with one task row and a metrics.md with
    a matching row, actuals columns get populated.
  - Variance equals signed percentage vs Est. Tokens (hand-
    verified fixture).
  - `diff` between pre- and post-update manifest shows exactly one
    changed row.
  - No-op if manifest has no matching row (log line, no crash).
  - Multiple rows for same task → actuals are sum.
- **Target Conditions**: TC-AG-4, TC-AG-5
- **Depends On**: ADV010-T006
- **Evaluation**:
  - Access requirements: Read, Write (.agent/telemetry/)
  - Skill set: markdown pipe-table editing, byte-preservation diffs
  - Estimated duration: 30min
  - Estimated tokens: 50000

### Wire task actuals into capture.py

- **ID**: ADV010-T010
- **Description**: In `.agent/telemetry/capture.py`'s `main()`,
  after `recompute_frontmatter`, if `event.task` is non-empty and
  `event.result` is terminal, call
  `task_actuals.update(manifest_path(event.adventure_id),
  event.task)`. Error-isolate the call.
- **Files**:
  - `.agent/telemetry/capture.py` (edit)
- **Acceptance Criteria**:
  - End-to-end test: synthetic event with `task: ADV010-T005` →
    manifest's T005 row gains Actual Duration/Tokens/Cost/Variance.
  - `TaskActualsError` in the call does not raise into `main()`.
- **Target Conditions**: TC-AG-4 (end-to-end), TC-EI-5
- **Depends On**: ADV010-T007, ADV010-T009
- **Evaluation**:
  - Access requirements: Read, Edit (.agent/telemetry/capture.py)
  - Skill set: Python
  - Estimated duration: 10min
  - Estimated tokens: 15000
