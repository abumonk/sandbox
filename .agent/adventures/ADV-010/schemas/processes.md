# Process Workflows

Version: 1.0.0  
Status: finalized  
Documents the three data flows that write and maintain `metrics.md` rows.
Cross-reference: `design-capture-contract.md`, `design-hook-integration.md`,
`design-backfill-strategy.md`, `design-aggregation-rules.md`.

---

## 1. Live capture (hook path)

**Trigger**: Claude Code fires `SubagentStop` at subagent completion, or
`PostToolUse` when `tool == "Task"` and the nested usage block is populated.

**Steps:**

1. Claude Code hook runtime invokes
   `python .agent/telemetry/capture.py` with the event JSON on **stdin**
   and a 5 000 ms timeout.
2. `capture.main()` reads `sys.stdin` and calls `json.loads()`.
3. `normalize_payload(raw_dict)` rewrites wire-field aliases (see
   `event_payload.md §Wire-to-internal alias table`).
4. `schema.validate_event(normalized)` → `SubagentEvent` (raises
   `CaptureError` on any validation failure; see
   `event_payload.md §Validation error catalog`).
5. `build_row(event)` → `MetricsRow`:
   - Computes `Run ID` via SHA-1 formula.
   - Sets `Duration (s) = max(1, round(event.duration_ms / 1000))`.
   - Calls `cost_model.cost_for(event.model, event.tokens_in,
     event.tokens_out)` → `Cost (USD)`.
   - Sets `Confidence = "high"`.
6. `append_row(metrics_path(event.adventure_id), row)`:
   - Parses existing rows; checks for `Run ID` collision → **no-op if
     duplicate** (idempotency).
   - Appends formatted pipe-table row to `## Agent Runs` section.
7. `aggregator.recompute_frontmatter(metrics_path)`:
   - Re-sums all rows → updates `total_tokens_in`, `total_tokens_out`,
     `total_duration`, `total_cost`, `agent_runs`.
8. **Conditional task-actuals propagation**: if `event.task` is not `None`
   and `event.result` is in `{"complete","done","passed"}`:
   - `task_actuals.update(manifest_path(event.adventure_id), event.task)`.
9. Exit `0`.

**Error path (any step 2–8 raises):**

- Log one line to `.agent/telemetry/capture-errors.log`:
  `{timestamp} | {ExceptionClass} | {raw_stdin[:500]}`
- Exit `0` (never non-zero — see `design-error-isolation.md`).

**Idempotency guarantee**: Running the same event payload through the hook
twice produces exactly one row in `metrics.md`. The Run ID collision check
in step 6 is the sole guard; no file locks or transaction logs are used.

**Ordering constraint**: All steps must complete within the hook's 5 000 ms
timeout. Budget allocation: stdin parse < 5 ms, validate < 5 ms, cost lookup
< 1 ms (memoised), file append < 20 ms, aggregator < 50 ms, task_actuals
(conditional) < 50 ms. Total well under 200 ms on typical hardware.

---

## 2. Backfill (reconstruction path)

**Trigger**: Operator invokes `python -m telemetry.tools.backfill` with
`--all` (all adventures) or `--adventure ADV-NNN` (single adventure).

**Steps:**

1. For each target adventure directory:
   a. **Evidence collection**: run 4 reconstructors in sequence, each
      producing `List[MetricsRow]` with `confidence != "high"`:
      - `log_reconstructor`: parse `adventure.log`, extract spawn/complete
        pairs, derive duration from timestamp diff (discarding non-monotonic
        pairs; see `design-backfill-strategy.md §Timestamp reliability`).
      - `task_file_reconstructor`: read task `.md` frontmatter for
        `estimated_tokens`, `estimated_duration`; yield a row with
        `confidence = "estimated"` when no log or git evidence is available.
      - `git_reconstructor`: extract author-date from git commit messages
        whose subject references the task ID; use commit timestamp as
        authoritative start/end when log timestamps are non-monotonic.
      - `metrics_reconstructor`: read the existing `metrics.md` rows to
        preserve any manually-entered data, carrying their existing
        `confidence` values.
   b. **Merge**: deduplicate candidates by `Run ID`; when two candidates
      share a Run ID, prefer the one with higher confidence
      (`high > medium > low > estimated`).
   c. Emit `List[MetricsRow]` ordered by `Timestamp` ascending.
2. Write the merged list to `metrics.md.new` (full file, header and separator
   included).
3. Emit a unified diff to stdout.
4. If `--apply` flag is set:
   a. Rename `metrics.md` to `metrics.md.bak`.
   b. Rename `metrics.md.new` to `metrics.md`.
   c. Run `aggregator.recompute_frontmatter(metrics_path)` on the new file.
5. Exit `0`.

**Error path:**

- Any reconstructor exception: log warning, skip that reconstructor's output
  for this adventure, continue with remaining reconstructors.
- File write failure: log error, leave `metrics.md.new` in place for manual
  inspection, continue to next adventure.
- The original `metrics.md` is **never modified** unless `--apply` is passed
  and a `metrics.md.new` was successfully written.

**Reversal**: `metrics.md.bak` can be restored manually at any time. The tool
does not delete `.bak` files automatically.

---

## 3. Task-actuals propagation

**Trigger**: `capture.main()` detected a row with a non-`None` `task` field
and a terminal `result` (`"complete"`, `"done"`, or `"passed"`). Also callable
directly: `python -m telemetry.task_actuals --adventure ADV-NNN --task ADV010-T003`.

**Steps:**

1. `task_actuals.update(manifest_path, task_id)`:
   a. Read the manifest `.md` file.
   b. Locate the `## Evaluations` pipe-table header line.
   c. Find the table row where column 1 (`Task`) equals `task_id`.
      - If not found: log warning `"task_id not in Evaluations table"`
        and return (no-op, no error raised).
   d. Read `metrics.md` for the same adventure; collect all rows where
      the `Task` column equals `task_id`.
   e. Compute actuals from the collected rows:
      - `actual_duration_s = sum(row.duration_s for row in rows)`
      - `actual_tokens = sum(row.tokens_in + row.tokens_out for row in rows)`
      - `actual_cost = sum(row.cost_usd for row in rows)` (pre-pinned values)
   f. Format actuals for the table:
      - `Actual Duration`: `"Nmin"` if `actual_duration_s >= 60`, else `"Ns"`.
      - `Actual Tokens`: integer.
      - `Actual Cost`: `"$N.NNNN"` (4dp, leading `$`).
      - `Variance`: computed from `Est. Tokens` column (the canonical
        estimate field): `round((actual_tokens - est_tokens) / est_tokens * 100)`;
        formatted as `"+N%"` / `"-N%"` / `"±0%"`; `"—"` if `est_tokens == 0`.
   g. Rewrite the single matched table row in the file buffer, preserving all
      other bytes exactly (no re-serialization of unrelated rows).
   h. Write to a temp file, then atomic rename over the manifest path.
2. Return (no exception on success).

**Error paths:**

- Multiple rows in the Evaluations table with the same `task_id`: log warning
  `"duplicate task rows: picking first"`, process the first match only.
- Metrics parse error while collecting rows: raise `TaskActualsError` (caller
  logs to `capture-errors.log`).
- Manifest file not writable: raise `TaskActualsError`.
- `Est. Tokens` cell is `"—"` or non-numeric: set `Variance = "—"`.
