# Task Actuals Module - Design

## Approach
Implement `.agent/telemetry/task_actuals.py` as a stdlib-only Python module with one public function: `update(manifest_path, task_id)`. The module reads the adventure's `metrics.md` to collect all rows for the given task, computes actuals (duration, tokens, cost, variance), then locates the matching row in the manifest's `## Evaluations` pipe-table and rewrites that single row in place. All other bytes in the manifest are preserved. Atomic write via tmp+`os.replace()`. Errors raise `TaskActualsError` (caught by `capture.py`'s `main()` guardrail).

## Target Files
- `.agent/telemetry/task_actuals.py` - New module; public `update()` plus internal helpers for table parsing, row rewriting, and actuals computation

## Implementation Steps

1. **Imports and constants**
   - Import `os`, `pathlib.Path`, `re`, `logging` from stdlib.
   - Import `AggregationError` / `TaskActualsError` from `.errors` (T004).
   - Import `parse_rows` and `format_duration` from `.aggregator` (T006).
   - Define `logger = logging.getLogger(__name__)`.
   - Define `TERMINAL_RESULTS = {"done", "complete", "passed", "ready", "failed", "error"}` (reference only, not used for filtering here -- caller already checked terminality).

2. **`update(manifest_path: Path, task_id: str) -> None`** (public entry point)
   - Derive `metrics_path` from `manifest_path`: same directory, file named `metrics.md`. (The manifest lives at `.agent/adventures/{ADV-ID}/manifest.md` and the metrics at `.agent/adventures/{ADV-ID}/metrics.md`.)
   - Call `parse_rows(metrics_path)` to get all `MetricsRow` objects.
   - Filter to `R_T = [r for r in rows if r.task == task_id]`.
   - If `R_T` is empty, log a warning and return (no crash -- handles non-task agent runs).
   - Compute actuals via `_compute_actuals(R_T)`.
   - Call `_update_manifest_row(manifest_path, task_id, actuals)`.

3. **`_compute_actuals(rows: list[MetricsRow]) -> dict`**
   - `actual_duration_s = sum(r.duration_s for r in rows)` (integer seconds).
   - `actual_duration = format_duration(actual_duration_s)` (human string, e.g. `"16min"`).
   - `actual_tokens = sum(r.tokens_in + r.tokens_out for r in rows)` (integer).
   - `actual_cost = sum(r.cost_usd for r in rows)` (float, rendered as `$X.XXXX`).
   - Return `{"actual_duration": actual_duration, "actual_tokens": actual_tokens, "actual_cost": f"${actual_cost:.4f}"}`.

4. **`_compute_variance(actual_tokens: int, est_tokens_str: str) -> str`**
   - If `est_tokens_str` is `"--"` or empty or non-numeric, return `"--"`.
   - Parse `est_tokens = int(est_tokens_str)`.
   - If `est_tokens == 0`, return `"--"` (avoid division by zero).
   - `pct = (actual_tokens - est_tokens) / est_tokens * 100`.
   - Return `f"{pct:+.0f}%"` (e.g. `"+12%"`, `"-8%"`, `"+0%"`).

5. **`_update_manifest_row(manifest_path: Path, task_id: str, actuals: dict) -> None`**
   - Read manifest file as UTF-8 string.
   - Locate the `## Evaluations` header line (case-sensitive match).
   - From that point, find the pipe-table header row (first line starting with `|`).
   - Parse header cells to build `col_index` map: `{"Task": 0, "Est. Tokens": 4, "Actual Duration": 6, "Actual Tokens": 7, "Actual Cost": 8, "Variance": 9, ...}` (strip whitespace from each cell).
   - Identify the separator row (next line, matching `|---`). Skip it.
   - Iterate data rows. For each row starting with `|`:
     - Split on `|`, strip cells.
     - If `cells[col_index["Task"]].strip() == task_id`:
       - Extract `est_tokens_str = cells[col_index["Est. Tokens"]].strip()`.
       - Compute `variance = _compute_variance(actuals["actual_tokens"], est_tokens_str)`.
       - Rewrite the four actuals cells in place:
         - `cells[col_index["Actual Duration"]] = f" {actuals['actual_duration']} "`
         - `cells[col_index["Actual Tokens"]] = f" {actuals['actual_tokens']} "`
         - `cells[col_index["Actual Cost"]] = f" {actuals['actual_cost']} "`
         - `cells[col_index["Variance"]] = f" {variance} "`
       - Reassemble the row as `|` + `|`.join(cells) + `|`.
       - Replace the original line in the file content.
       - Break (first match wins; task IDs are unique in the table).
   - If no row matched, log a warning to `capture-errors.log` and return (no-op, no crash).
   - Atomic write: write to `manifest_path.with_suffix('.md.tmp')`, flush, fsync, `os.replace(tmp, manifest_path)`.

6. **Line-level byte preservation strategy**
   - The file is split into lines (`content.split('\n')`).
   - Only the single matched data row is replaced; all other lines are preserved verbatim (including trailing whitespace, blank lines, etc.).
   - Lines are rejoined with `'\n'.join(lines)` -- the original line ending style is preserved because we split/join consistently.
   - The `cells` list is reconstructed from the pipe-split of the original row, so leading/trailing spaces in non-modified cells are preserved exactly.

7. **Error handling**
   - All exceptions raised by this module are wrapped in `TaskActualsError`.
   - File-not-found on manifest: `TaskActualsError("Manifest not found: {path}")`.
   - File-not-found on metrics: `TaskActualsError("Metrics not found: {path}")`.
   - Missing `## Evaluations` header: `TaskActualsError("No ## Evaluations section")`.
   - Missing pipe-table or header: `TaskActualsError("No pipe-table under ## Evaluations")`.
   - Parse/write failures wrapped similarly.
   - The caller (`capture.py` main) catches `TaskActualsError` as part of the `CaptureError` hierarchy and logs to `capture-errors.log` with exit 0.

## Testing Strategy
- **TC-AG-4**: Create a fixture manifest with one task row (known Est. Tokens) and a fixture metrics.md with one or more matching rows. Run `update()`. Assert `Actual Duration`, `Actual Tokens`, `Actual Cost`, and `Variance` match hand-computed values exactly.
- **TC-AG-5**: Create a fixture manifest with 3+ task rows. Run `update()` for one task. Run `diff` (or byte comparison) between pre- and post-update manifest. Assert exactly one line differs.
- **No-op on missing row**: Call `update()` with a `task_id` not present in the manifest. Assert no crash, manifest unchanged.
- **Multi-row summation**: Fixture metrics.md with 3 rows for the same task_id (simulating implementer + reviewer + retry). Assert actuals are the sum across all rows.
- **Dash Est. Tokens**: If `Est. Tokens` is `"--"`, variance should be `"--"`.
- All tests use `tempfile.TemporaryDirectory`, `unittest.TestCase`, stdlib only.

## Risks
- **Dependency on T006 aggregator**: `parse_rows()` and `format_duration()` must be available. If T006 is incomplete, the implementer must stub or block. The `depends_on` chain should prevent this.
- **Pipe-table column drift**: If the manifest `## Evaluations` table gains or loses columns after this design, the column index map will be wrong. Mitigation: column indices are parsed dynamically from the header row, not hardcoded by position.
- **Cell padding preservation**: When rewriting a cell, surrounding spaces must match the table's visual alignment. The design uses ` value ` (single space padding) which matches the existing manifest style. If the original uses wider padding for alignment, the rewritten row may shift visually. This is acceptable per the design doc (byte-preservation applies to non-matching rows only).
- **Windows line endings**: If the manifest uses `\r\n`, the split/join on `\n` could corrupt. Mitigation: read in text mode (Python default), which normalizes `\r\n` to `\n` on Windows. Write in text mode to re-emit platform line endings. Alternatively, read/write in binary mode and split on `\r\n` or `\n` explicitly. The implementer should test on the actual platform.
