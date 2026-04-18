# Run Backfill on ADV-001..ADV-009 - Design

## Approach

This is an **operator task**, not an implementation task. The backfill CLI
(built by T011 + T012) is already available. The operator runs it per-adventure,
reviews each diff, applies when safe, and verifies post-conditions. The role
file (telemetry-historian) prescribes a strict dry-run-then-apply workflow
with diff review at each step.

## Target Files

- `.agent/adventures/ADV-001/metrics.md` - Backfill rewrite (add Run ID, Timestamp, Confidence columns; strip tildes; recompute frontmatter)
- `.agent/adventures/ADV-002/metrics.md` - Same
- `.agent/adventures/ADV-003/metrics.md` - Same
- `.agent/adventures/ADV-004/metrics.md` - Same
- `.agent/adventures/ADV-005/metrics.md` - Same
- `.agent/adventures/ADV-006/metrics.md` - Same
- `.agent/adventures/ADV-007/metrics.md` - Same
- `.agent/adventures/ADV-008/metrics.md` - Same (preserves existing numeric values, strips tildes, adds new columns)
- `.agent/adventures/ADV-009/metrics.md` - Same
- `.agent/adventures/ADV-00*/metrics.md.backup.<ts>` - Backup files created by `--apply` (new, one per adventure)

## Implementation Steps

### Phase 1: Pre-flight checks

1. **Verify dependencies are complete.** Confirm T012 (backfill CLI) and T016 (tests) are implemented. The backfill CLI must be runnable via `python -m telemetry.tools.backfill --help`.

2. **Snapshot current state.** For each ADV-001..ADV-009, note the current `agent_runs` and `total_tokens_in` from frontmatter. This provides a before/after comparison independent of the tool's own backups.

### Phase 2: Dry-run pass (all nine adventures)

3. **Dry-run each adventure individually.** For each `NNN` in `001, 002, 003, 004, 005, 006, 007, 008, 009`:
   ```
   python -m telemetry.tools.backfill --adventure ADV-NNN --dry-run
   ```
   Redirect or capture the diff output. Review each diff for:
   - Every row has a `Confidence` value of `medium`, `low`, or `estimated` (never `high`).
   - Token estimates are plausible given the task's duration and model (opus ~6K/min in, sonnet ~4K/min in per the design-backfill-strategy priors).
   - No `~` tilde characters remain in any numeric cell.
   - ADV-008 specifically: existing numeric values are preserved (only tilde-stripping and column additions).
   - Unreconstructable tasks (no log/git/row evidence) produce rows with `result: unrecoverable`.
   - Frontmatter `agent_runs` > 0 and `total_tokens_in` > 0 in the proposed output.

4. **Flag any suspicious diffs.** If any adventure's diff shows "too-good" token counts where estimates should appear, or `Confidence: high` on a backfilled row, STOP and log a blocker note. Do not proceed to apply for that adventure.

### Phase 3: Apply pass (per-adventure, sequential)

5. **Apply each adventure one at a time.** For each `NNN` in `001..009` (in order):
   ```
   python -m telemetry.tools.backfill --adventure ADV-NNN --apply
   ```
   After each apply:

6. **Verify backup exists.** Confirm `metrics.md.backup.<ts>` was created in the adventure directory. Verify its content matches the pre-apply `metrics.md` (the tool renames the original).

7. **Verify rewritten metrics.md.** Read the new `metrics.md` and confirm:
   - Frontmatter `agent_runs > 0` and `total_tokens_in > 0`.
   - No `~` characters anywhere in the file.
   - All rows have the 12-column schema (Run ID through Confidence).
   - The `## Agent Runs` header and pipe-table structure are intact.

8. **Log the operation.** After each successful apply, note in the task log: which adventure, how many rows, how many `unrecoverable`.

### Phase 4: Verification

9. **Run the autotest suite.** Execute:
   ```
   python -m unittest .agent/adventures/ADV-010/tests/test_backfill.py
   ```
   Specifically confirm these tests pass:
   - `test_every_completed_adventure_has_runs` - validates `agent_runs > 0` for all completed adventures.
   - `test_backfill_rows_never_high_confidence` - validates no backfilled row has `Confidence: high`.

10. **Grep for residual tildes.** Run:
    ```
    grep '~' .agent/adventures/ADV-00*/metrics.md
    ```
    Must produce zero matches.

11. **Verify backup completeness.** For each ADV-001..ADV-009, confirm exactly one `metrics.md.backup.<ts>` file exists and that `diff` against the original content (captured in step 2 or from the backup itself) shows no unexpected changes.

### Phase 5: Rollback protocol (if needed)

12. **If any test fails**, roll back the offending adventure:
    ```
    mv .agent/adventures/ADV-NNN/metrics.md.backup.<ts> .agent/adventures/ADV-NNN/metrics.md
    ```
    Log the failure and file a blocker note on T013 citing the specific adventure and failure reason.

## Testing Strategy

- **Primary gate**: `test_every_completed_adventure_has_runs` must pass.
- **Secondary gate**: `test_backfill_rows_never_high_confidence` must pass.
- **Manual verification**: `grep '~'` across all rewritten metrics files returns empty.
- **Backup integrity**: Each backup file exists and byte-matches the pre-apply content.

## Risks

1. **Dependency not ready.** T012 (backfill CLI) or T016 (tests) may not be implemented yet. Both are listed as dependencies. If either is incomplete, this task is blocked.
2. **Sparse evidence for early adventures.** ADV-001..ADV-003 may have minimal log/git evidence, resulting in many `unrecoverable` rows. This is acceptable per the design (the row is emitted with `result: unrecoverable, confidence: estimated`), but the operator should verify the count is reasonable.
3. **ADV-008 regression.** ADV-008 has 34 existing rows with real data. The backfill must preserve all numeric values (TC-BF-2). If the diff shows any numeric drift, do not apply.
4. **Git history availability.** The `git_windows` reconstructor shells out to `git log`. If git history is shallow or pruned, this source may return empty results for some adventures. This reduces confidence but does not block the operation.
