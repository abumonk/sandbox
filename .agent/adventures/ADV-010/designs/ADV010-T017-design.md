# Operator Documentation - Design

## Approach
Author a concise operator README at `.agent/telemetry/README.md` (max 200 lines) that serves as the single reference for anyone operating or extending the telemetry capture subsystem. The document covers five sections derived from the design docs plus the test-discovery and backfill one-liners required by acceptance criteria.

## Target Files
- `.agent/telemetry/README.md` - New file. The sole deliverable for this task.

## Implementation Steps

1. **Write the header and overview** (lines 1-15): Title "Telemetry Capture - Operator Guide", a one-paragraph summary of what the subsystem does (captures token usage, computes cost, writes metrics rows, aggregates frontmatter totals).

2. **Section: Layout** (approx 20-30 lines): Document the directory tree under `.agent/telemetry/` with one-line descriptions of each module:
   - `capture.py` - hook entrypoint, reads JSON from stdin, writes a row to metrics.md
   - `schema.py` - dataclasses + validators for SubagentEvent and MetricsRow
   - `cost_model.py` - maps (model, tokens_in, tokens_out) to USD cost; reads rates from `.agent/config.md` frontmatter
   - `aggregator.py` - recomputes frontmatter totals from rows
   - `task_actuals.py` - propagates actuals into manifest evaluations table
   - `errors.py` - exception hierarchy (CaptureError, PayloadError, SchemaError, etc.)
   - `tools/backfill.py` - reconstructs historical telemetry
   - `tools/reconstructors/` - log_parser.py, git_windows.py, task_logs.py, existing_rows.py
   - `capture-errors.log` - append-only error sink (created on first failure)

3. **Section: How the Hook is Wired** (approx 20-25 lines): Explain:
   - The hook is declared in `.claude/settings.local.json` under the `hooks` key
   - It fires on `SubagentStop` and `PostToolUse` events
   - Claude Code serializes the event as JSON to stdin
   - The hook command is `python .agent/telemetry/capture.py`
   - Reference `design-hook-integration.md` for the full payload shape
   - Note: the 128-entry `permissions.allow` list must not be modified when editing the settings file

4. **Section: How to Run Backfill** (approx 20-25 lines): Document:
   - The backfill one-liner: `python -m telemetry.tools.backfill --adventure ADV-NNN`
   - What it does: reconstructs rows from adventure.log, git history, task log sections, and existing metrics rows
   - Confidence levels: high (existing rows), medium (log/task-derived), low (git-only)
   - Safety: writes to `metrics.md.new` first, diffs, then renames (reversible)
   - Reference `design-backfill-strategy.md` for reconstruction algorithm details

5. **Section: How to Read `capture-errors.log`** (approx 20-25 lines): Document:
   - Location: `.agent/telemetry/capture-errors.log`
   - Format: each line is a timestamped error entry with exception class and message
   - The exit-0 guardrail: capture never crashes the agent pipeline; all failures are logged here instead
   - Exception hierarchy: PayloadError (bad stdin), SchemaError (validation), CostModelError/UnknownModelError (cost lookup), WriteError (filesystem), AggregationError, TaskActualsError
   - Triage: most errors are PayloadError (malformed event) or UnknownModelError (new model not in config)

6. **Section: How to Add a New Cost Rate** (approx 15-20 lines): Document:
   - Open `.agent/config.md`
   - Find the `token_cost_per_1k:` block under `adventure:`
   - Add a new line: `    new_model: 0.NNN` (2-space indent under the block)
   - The cost_model.py stdlib YAML-subset parser reads this at runtime; no code changes needed
   - If the model name in events doesn't match a key, an `UnknownModelError` is logged to capture-errors.log

7. **Include the discover one-liner** in a "Quick Reference" or within the relevant section:
   ```
   python -m unittest discover -s .agent/adventures/ADV-010/tests -v
   ```

8. **Review line count** - ensure total is under 200 lines. Trim prose if needed; prefer bullet lists and code blocks.

## Testing Strategy
- Manual verification: confirm the file exists at `.agent/telemetry/README.md`
- Verify it contains all 5 required sections (Layout, Hook Wiring, Backfill, Error Log, Cost Rates)
- Verify it contains the discover one-liner (`python -m unittest discover`)
- Verify it contains the backfill one-liner (`python -m telemetry.tools.backfill`)
- Verify line count <= 200

## Risks
- The telemetry directory may not yet exist if upstream tasks (T002-T012) haven't been implemented. The implementer should create the README regardless; the directory will be created by prior tasks in the dependency chain (T016 depends on all implementation tasks, and T017 depends on T016).
- Line count constraint (200 lines) requires disciplined, terse writing. Five sections plus code blocks can easily exceed this if not carefully managed.
