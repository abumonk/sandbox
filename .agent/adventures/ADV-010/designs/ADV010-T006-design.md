# Aggregator Module - Design

## Approach
Implement `.agent/telemetry/aggregator.py` as a stdlib-only Python module providing three public functions: `parse_rows()`, `recompute_frontmatter()`, and `format_duration()`. The module reads metrics.md files, parses the pipe-table rows and YAML-subset frontmatter, computes aggregate totals from row data, and rewrites the frontmatter atomically using `os.replace()`. It depends on `schema.py` (T005) for `MetricsRow` dataclass and row-parsing utilities, and on `errors.py` (T004) for `AggregationError`.

## Target Files
- `.agent/telemetry/aggregator.py` - New module; all three public functions plus internal helpers (`_parse_frontmatter`, `_serialize_frontmatter`, `_rewrite_frontmatter`)

## Implementation Steps

1. **Imports and constants**
   - Import `os`, `pathlib.Path`, `re` from stdlib.
   - Import `MetricsRow` from `.schema` (T005 dependency).
   - Import `AggregationError` from `.errors` (T004 dependency).

2. **`format_duration(seconds: int) -> str`**
   - Pure function, no I/O. Handles three tiers:
     - `seconds < 60`: return `f"{seconds}s"`
     - `60 <= seconds < 3600` and `seconds % 60 == 0`: return `f"{seconds // 60}min"`
     - `60 <= seconds < 3600` with remainder: return `f"{seconds // 60}min {seconds % 60}s"`
     - `seconds >= 3600`: compute hours and remaining minutes, return `f"{h}h {m}min"` (drop the `0min` suffix if minutes are zero, i.e. `f"{h}h"`).
   - Edge case: `seconds == 0` returns `"0s"`.

3. **`parse_rows(metrics_path: Path) -> list[MetricsRow]`**
   - Read file contents as UTF-8.
   - Split frontmatter from body using `---` fences.
   - Locate the `## Agent Runs` section in the body.
   - Find the first pipe-table below that header.
   - Skip header row and separator row (line matching `|---`).
   - For each data row: split on `|`, strip cells, coerce types per column index using the fixed column order from `row_schema.md` (Run ID, Timestamp, Agent, Task, Model, Tokens In, Tokens Out, Duration (s), Turns, Cost (USD), Result, Confidence).
   - Integers: `tokens_in`, `tokens_out`, `duration_s`, `turns`. Float: `cost_usd`. Strings: rest.
   - Handle rows with tilde-prefixed approximate values (e.g. `~45000`) by stripping the `~` and parsing as int -- these are legacy/hand-written rows.
   - On parse failure for a row, raise `AggregationError` with line number context.
   - Return list of `MetricsRow` instances.

4. **`recompute_frontmatter(metrics_path: Path) -> None`**
   - Call `parse_rows(metrics_path)` to get all rows.
   - Compute totals dict:
     - `total_tokens_in`: `sum(r.tokens_in for r in rows)`
     - `total_tokens_out`: `sum(r.tokens_out for r in rows)`
     - `total_duration`: `sum(r.duration_s for r in rows)` (integer seconds)
     - `total_cost`: `round(sum(r.cost_usd for r in rows), 4)`
     - `agent_runs`: `len(rows)`
   - Read the existing file, extract frontmatter block.
   - Preserve `adventure_id` from existing frontmatter.
   - Rebuild frontmatter YAML with updated totals in canonical key order: `adventure_id`, `total_tokens_in`, `total_tokens_out`, `total_duration`, `total_cost`, `agent_runs`.
   - Reconstruct full file: new frontmatter + original body (everything after closing `---`).
   - Atomic write: write to `metrics_path.with_suffix('.md.tmp')`, flush, fsync, then `os.replace(tmp, metrics_path)`.

5. **Internal helpers**
   - `_parse_frontmatter(text: str) -> dict`: Extract YAML-subset key-value pairs from `---` fenced block. Handles str, int, float values. Reuses the same hand-rolled approach as `cost_model.py` (T004) -- no PyYAML.
   - `_serialize_frontmatter(data: dict, key_order: list[str]) -> str`: Render dict back to `---\nkey: value\n...\n---\n` with controlled key order.

6. **Error handling**
   - All exceptions raised are `AggregationError` subtype of `CaptureError`.
   - File-not-found, permission errors, and parse failures are wrapped in `AggregationError` with descriptive messages.
   - The caller (`capture.py` in T007) catches these via the `main()` guardrail.

## Testing Strategy
- **TC-AG-1 / TC-AG-2**: Create a fixture `metrics.md` with N rows (varied token/duration/cost values). After `recompute_frontmatter()`, assert each `total_*` field equals the hand-computed row sum.
- **TC-AG-3**: Run `recompute_frontmatter()` twice on the same file. Read file bytes after each run and assert byte-identical.
- **TC-AG-6**: Table-driven test for `format_duration()` with at least 6 cases: `0` -> `"0s"`, `95` -> `"95s"`, `960` (16*60) -> `"16min"`, `125` -> `"2min 5s"`, `3600` -> `"1h"`, `8100` (2*3600+15*60) -> `"2h 15min"`.
- All tests use `tempfile.TemporaryDirectory` for file I/O. `unittest.TestCase` only (stdlib).

## Risks
- **Dependency on T005 schema**: `MetricsRow` dataclass and any row-parsing helpers must exist. If T005 is not yet implemented, the implementer will need to define a minimal local `MetricsRow` namedtuple as a shim (but this should not happen given the `depends_on` chain).
- **Legacy approximate values**: Existing metrics.md files contain `~45000`-style values. The parser must handle these gracefully (strip tilde prefix) rather than failing.
- **Windows atomic rename**: `os.replace()` is atomic on NTFS. The tmp file must be in the same directory as the target to avoid cross-device rename failures.
