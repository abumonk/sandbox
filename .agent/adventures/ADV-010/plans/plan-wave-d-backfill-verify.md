# Plan — Wave D: Backfill and Live Verification

## Designs Covered

- designs/design-backfill-strategy.md

Reconstruct historical telemetry for ADV-001..ADV-007 (and fill
gaps in ADV-008, ADV-009). Also: run the live canary on ADV-009 to
prove the whole stack end-to-end with a real subagent.

## Tasks

### Backfill tool — reconstructors

- **ID**: ADV010-T011
- **Description**: Implement the 4 reconstructor submodules under
  `.agent/telemetry/tools/reconstructors/`:
  - `existing_rows.py` (parse current metrics.md, strip tildes,
    confidence=medium)
  - `log_parser.py` (parse adventure.log, extract spawn/complete
    pairs)
  - `git_windows.py` (shell out to `git log --pretty=...
    --name-only`, derive per-task commit windows)
  - `task_logs.py` (read task-file `## Log` sections)
  Each returns `List[Candidate]`; a Candidate has the same shape
  as MetricsRow plus a `source` field.
- **Files**:
  - `.agent/telemetry/tools/__init__.py` (new)
  - `.agent/telemetry/tools/reconstructors/__init__.py` (new)
  - `.agent/telemetry/tools/reconstructors/existing_rows.py` (new)
  - `.agent/telemetry/tools/reconstructors/log_parser.py` (new)
  - `.agent/telemetry/tools/reconstructors/git_windows.py` (new)
  - `.agent/telemetry/tools/reconstructors/task_logs.py` (new)
- **Acceptance Criteria**:
  - `existing_rows.parse(ADV-008/metrics.md)` returns 34 candidates
    with tildes stripped and integer tokens.
  - `log_parser.parse(ADV-008/adventure.log)` returns ≥ 19 spawn
    events (one per task).
  - `git_windows.for_adventure("ADV-008")` returns per-task
    windows (using `git log` bounded by created..updated).
  - Each reconstructor has at least one fixture-based unit test.
- **Target Conditions**: TC-BF-2 (existing), TC-BF-5 (unreconstructable flagging at merge)
- **Depends On**: ADV010-T005
- **Evaluation**:
  - Access requirements: Read (.agent/, .git via shell), Write
    (.agent/telemetry/tools/), Bash (git log)
  - Skill set: log parsing, git CLI, regex
  - Estimated duration: 30min
  - Estimated tokens: 70000

### Backfill merge + CLI + reversibility

- **ID**: ADV010-T012
- **Description**: Implement
  `.agent/telemetry/tools/backfill.py` — the top-level CLI. Merge
  candidates per task, pick highest-confidence field-by-field,
  emit MetricsRow set. Write to `metrics.md.new`; emit unified
  diff; if `--apply`, rename with backup. Covers
  `--adventure ADV-NNN`, `--all`, `--sources ...`, `--apply`,
  `--dry-run`.
- **Files**:
  - `.agent/telemetry/tools/backfill.py` (new)
- **Acceptance Criteria**:
  - `python -m telemetry.tools.backfill --adventure ADV-008
    --dry-run` emits a diff without modifying
    `ADV-008/metrics.md`.
  - `--apply` renames original to `metrics.md.backup.<ts>`.
  - Running twice without `--apply` produces identical diffs
    (idempotency).
  - Row's Run ID is stable across runs.
  - Unreconstructable task → row with `result: unrecoverable`.
- **Target Conditions**: TC-BF-3, TC-BF-4, TC-BF-5, TC-BF-6
- **Depends On**: ADV010-T011
- **Evaluation**:
  - Access requirements: Read, Write (backfill touches all
    `.agent/adventures/*/metrics.md` only via `.new` companion
    files unless `--apply`)
  - Skill set: Python CLI, diff generation, file renaming
  - Estimated duration: 25min
  - Estimated tokens: 50000

### Run backfill on ADV-001..ADV-009

- **ID**: ADV010-T013
- **Description**: Execute `python -m telemetry.tools.backfill
  --all --apply`. Review each diff before applying (operator-
  interactive is fine). Commit the backup files alongside the new
  metrics.md files. After completion, assert each
  `metrics.md` has `agent_runs > 0` in frontmatter and that the
  autotest `test_every_completed_adventure_has_runs` passes.
- **Files**:
  - `.agent/adventures/ADV-001/metrics.md` (rewrite)
  - `.agent/adventures/ADV-002/metrics.md` (rewrite)
  - `.agent/adventures/ADV-003/metrics.md` (rewrite)
  - `.agent/adventures/ADV-004/metrics.md` (rewrite)
  - `.agent/adventures/ADV-005/metrics.md` (rewrite)
  - `.agent/adventures/ADV-006/metrics.md` (rewrite)
  - `.agent/adventures/ADV-007/metrics.md` (rewrite)
  - `.agent/adventures/ADV-008/metrics.md` (rewrite — adds Run ID,
    Confidence columns; preserves numeric content)
  - `.agent/adventures/ADV-009/metrics.md` (rewrite)
  - `.agent/adventures/ADV-00*/metrics.md.backup.<ts>` (new)
- **Acceptance Criteria**:
  - Every completed adventure's metrics.md has frontmatter
    `agent_runs > 0` and `total_tokens_in > 0`.
  - Every backup file is present and matches the pre-run content.
  - No `~` characters appear in any rewritten metrics.md.
  - `test_every_completed_adventure_has_runs` passes.
- **Target Conditions**: TC-BF-1, TC-BF-2
- **Depends On**: ADV010-T012, ADV010-T016 (tests must exist)
- **Evaluation**:
  - Access requirements: Read, Write (all `.agent/adventures/*/metrics.md`),
    Bash (python, git)
  - Skill set: operator care, reviewing diffs
  - Estimated duration: 20min
  - Estimated tokens: 30000

### Live canary on ADV-009

- **ID**: ADV010-T014
- **Description**: With hook installed and capture.py wired,
  trigger one real subagent run bound to ADV-009 (a small research
  sub-task: e.g. "summarize ADV-009's current state in one
  paragraph"). Verify that `ADV-009/metrics.md` gains exactly one
  new row with `Confidence: high`, non-zero tokens, the model set
  correctly, and that frontmatter totals update to match.
- **Files**:
  - `.agent/adventures/ADV-009/metrics.md` (gains one row via live
    hook; not hand-edited)
  - `.agent/adventures/ADV-010/tests/fixtures/canary/` — record the
    pre/post metrics snapshot for the autotest to compare.
- **Acceptance Criteria**:
  - New row present with `Confidence: high`.
  - `total_tokens_in` after = `total_tokens_in` before +
    row.tokens_in.
  - `agent_runs` incremented by exactly 1.
  - `test_adv009_canary_row_populated` passes.
- **Target Conditions**: TC-LC-1
- **Depends On**: ADV010-T008, ADV010-T013, ADV010-T016
- **Evaluation**:
  - Access requirements: Read, Write (tests/fixtures/canary/),
    ability to invoke a subagent (Task tool)
  - Skill set: Claude Code sub-agent invocation
  - Estimated duration: 15min
  - Estimated tokens: 20000
