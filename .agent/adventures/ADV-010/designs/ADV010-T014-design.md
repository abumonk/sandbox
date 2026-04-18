# Live Canary on ADV-009 - Design

## Approach

This task is the end-to-end validation of the entire telemetry capture stack. It triggers one real subagent run bound to ADV-009, then verifies that the hook-to-row pipeline produced a correct, high-confidence metrics row and that the aggregator updated frontmatter totals accordingly.

The canary is deliberately minimal: a single research sub-task ("summarize ADV-009's current state in one paragraph") that exercises the full chain: Claude Code hook fires SubagentStop, capture.py receives the event on stdin, normalizes the payload, computes cost, appends a row to ADV-009/metrics.md, recomputes frontmatter, and optionally propagates task actuals.

## Prerequisites (from dependencies)

- **ADV010-T008** (done): Hook registered in `.claude/settings.local.json` -- SubagentStop and PostToolUse both point at `python .agent/telemetry/capture.py`.
- **ADV010-T013** (done): Backfill has run on ADV-009, so `metrics.md` has backfilled rows with `Confidence: medium/low/estimated` and frontmatter totals reflect those rows.
- **ADV010-T016** (done): `test_live_canary.py` exists with `test_adv009_canary_row_populated` that `skipUnless` fixture files are present.

## Target Files

- `.agent/adventures/ADV-009/metrics.md` -- gains exactly one new row via the live hook (never hand-edited by the implementer)
- `.agent/adventures/ADV-010/tests/fixtures/canary/pre_metrics.md` -- snapshot of ADV-009/metrics.md before the canary run
- `.agent/adventures/ADV-010/tests/fixtures/canary/post_metrics.md` -- snapshot of ADV-009/metrics.md after the canary run

## Implementation Steps

### Step 1: Snapshot pre-canary state

1. Read `.agent/adventures/ADV-009/metrics.md` in its current state (post-backfill from T013).
2. Record the frontmatter values: `total_tokens_in`, `total_tokens_out`, `total_duration`, `total_cost`, `agent_runs`.
3. Count the existing rows in the `## Agent Runs` table.
4. Create the fixtures directory: `.agent/adventures/ADV-010/tests/fixtures/canary/`.
5. Write the full file content to `tests/fixtures/canary/pre_metrics.md`.

### Step 2: Trigger the canary subagent run

1. Use the Task tool (Claude Code subagent invocation) to spawn a small research sub-task bound to ADV-009.
2. The sub-task prompt should be something like: "Read `.agent/adventures/ADV-009/adventure.log` and the ADV-009 manifest. Summarize the current state of ADV-009 in one paragraph. Output only the summary paragraph."
3. This must be a real subagent invocation (not a simulated one) so the SubagentStop hook fires naturally.
4. The hook will deliver the event payload to `capture.py` on stdin, which will:
   - Parse and validate the event
   - Resolve `adventure_id` to `ADV-009` (from the task_id prefix or cwd)
   - Compute a Run ID via SHA-1
   - Compute cost via cost_model
   - Append a row to `ADV-009/metrics.md`
   - Recompute frontmatter totals via aggregator

### Step 3: Verify the new row

1. Re-read `.agent/adventures/ADV-009/metrics.md`.
2. Confirm exactly one new row was appended (row count = previous + 1).
3. Parse the new row and verify:
   - **Confidence** column = `high` (hook-written rows always use `high`)
   - **Tokens In** > 0 (non-zero)
   - **Tokens Out** > 0 (non-zero)
   - **Model** is set correctly (should be `opus` or `sonnet`, matching the model used)
   - **Run ID** is a 12-character hex string
   - **Cost (USD)** > 0 and matches `cost_model.cost_for(model, tokens_in, tokens_out)` to 4dp
   - **Duration (s)** > 0
   - **Result** is a valid terminal status

### Step 4: Verify frontmatter aggregation

1. Parse the updated frontmatter.
2. Assert: `total_tokens_in` (after) = `total_tokens_in` (before) + new_row.tokens_in
3. Assert: `total_tokens_out` (after) = `total_tokens_out` (before) + new_row.tokens_out
4. Assert: `agent_runs` (after) = `agent_runs` (before) + 1
5. Assert: `total_cost` (after) = `total_cost` (before) + new_row.cost_usd (to 4dp)

### Step 5: Record post-canary fixture

1. Write the updated `ADV-009/metrics.md` content to `tests/fixtures/canary/post_metrics.md`.
2. This fixture pair (pre/post) enables `test_live_canary.py::test_adv009_canary_row_populated` to run as a pure assertion against recorded snapshots.

### Step 6: Verify the autotest passes

1. Run: `python -m unittest .agent.adventures.ADV-010.tests.test_live_canary -v`
2. Confirm `test_adv009_canary_row_populated` passes (it should now find the fixture files and run its assertions).

## Testing Strategy

The canary IS the test. Verification is both live (steps 3-4 assertions during the task) and recorded (step 5-6 fixture-based autotest). The `test_live_canary.py` test uses `@unittest.skipUnless(os.path.exists(CANARY_PRE), "canary fixtures not yet recorded")` so it is safe in CI before this task runs, but becomes a real assertion after.

Key assertions in `test_adv009_canary_row_populated`:
- Post file has exactly one more row than pre file
- The new row's Confidence is `high`
- Frontmatter `agent_runs` incremented by exactly 1
- Frontmatter `total_tokens_in` increased by exactly the new row's tokens_in value

## Risks

1. **Hook not firing**: If T008's hook registration is incorrect or the hook runtime does not trigger for Task-tool-invoked subagents, no row will appear. Mitigation: verify `.claude/settings.local.json` has the correct hook entries before triggering.
2. **Adventure ID resolution**: The subagent's cwd or task_id must resolve to `ADV-009`. If the resolution logic (from T007) falls back to ADV-010 instead, the row lands in the wrong file. Mitigation: explicitly scope the sub-task to an ADV-009 task ID.
3. **Backfill not yet applied**: If T013 has not run, the pre-canary metrics.md may still have `~` tilde-prefixed estimates rather than clean numeric rows, which could confuse aggregation. The dependency chain prevents this.
4. **Double-fire**: Both SubagentStop and PostToolUse hooks may fire for the same subagent. The idempotency guard (Run ID collision check from T007) should prevent a duplicate row. Verify only one new row appears.
