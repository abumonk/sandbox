# Design — Aggregation Rules

## Overview

Defines how frontmatter totals are kept in sync with row data in
every `metrics.md`. Also defines the task-actuals propagation into
the manifest `## Evaluations` table.

## Target files

- `.agent/telemetry/aggregator.py` — frontmatter recomputation
  (new).
- `.agent/telemetry/task_actuals.py` — manifest update (new).

## Append-only rows, recompute totals

Rows are append-only. The writer never rewrites an existing row.
Frontmatter totals are **derived** — recomputed from scratch on
every write.

```python
def recompute_frontmatter(metrics_path: Path) -> None:
    rows = parse_rows(metrics_path)
    totals = {
        "total_tokens_in": sum(r.tokens_in for r in rows),
        "total_tokens_out": sum(r.tokens_out for r in rows),
        "total_duration": sum(r.duration_s for r in rows),   # seconds
        "total_cost": round(sum(r.cost_usd for r in rows), 4),
        "agent_runs": len(rows),
    }
    rewrite_frontmatter(metrics_path, totals)
```

The rewrite is atomic: write to `metrics.md.tmp`, fsync, rename. On
Windows, `os.replace()` gives atomic rename semantics.

### Duration format

Frontmatter `total_duration` stores **integer seconds** (not the
mixed `16min` / `95s` strings in today's files). This requires a
schema bump — existing files with `total_duration: 16min` are
migrated by the backfill tool (which always runs through the
aggregator).

Readers that want human-friendly rendering call
`format_duration(seconds)` → `"16min"` / `"2h 15min"` etc. That
function lives in `aggregator.py` and is covered by a unit test.

## Idempotency of aggregation

`recompute_frontmatter` is a pure function of row contents. Running
it twice produces byte-identical output. Every aggregation test
includes a double-invocation check.

## Task actuals propagation

After a row is appended whose `Task` is non-empty AND the row's
`result` is a terminal status (`done`, `complete`, `passed`,
`ready`, `failed`, `error`), the writer updates the manifest's
`## Evaluations` table for that task:

```python
def update_task_actuals(manifest_path: Path, task_id: str,
                        metrics_rows: List[Row]) -> None:
    """Find the row in Evaluations table whose Task column equals
    task_id. Compute Actual Duration / Actual Tokens / Actual Cost
    / Variance from metrics_rows restricted to this task. Rewrite
    that single table row, leaving all others untouched."""
```

### Actuals computation

For a task T with metrics rows `R_T`:

- `Actual Duration` = `format_duration(sum(r.duration_s for r in R_T))`.
- `Actual Tokens`   = `sum(r.tokens_in + r.tokens_out for r in R_T)`.
- `Actual Cost`     = `sum(r.cost_usd for r in R_T)`, rendered as
                      `$X.XXXX`.
- `Variance`        = signed percentage vs estimate:

  ```
  if Est. Cost is "—": Variance = "—"
  else:
      pct = (Actual Tokens − Est. Tokens) / Est. Tokens * 100
      Variance = f"{pct:+.0f}%"    # "+12%" / "-8%" / "+0%"
  ```

  Variance is computed against **tokens**, not cost or duration,
  because tokens is the most stable planner-estimated signal (cost
  is a derivative of tokens + model; duration is noisier).

### Manifest row update

The `## Evaluations` table is a markdown pipe-table. We rewrite
exactly the matched row in place. Unmatched rows are preserved
byte-for-byte (including whitespace). The update function:

1. Reads the manifest.
2. Locates the `## Evaluations` header, then the first pipe-table
   below it.
3. Parses header row → column index map.
4. Finds the data row where `Task` == `task_id`.
5. Rewrites columns `Actual Duration`, `Actual Tokens`,
   `Actual Cost`, `Variance`.
6. Writes manifest.md.tmp → rename.

If no row matches, the update is a no-op and a line is logged to
`capture-errors.log` (not fatal — non-task agent runs exist, e.g.
`adventure-planner` itself).

## Multi-row tasks

A task can have multiple rows (implementer + reviewer, or retries).
Aggregation simply sums. `Variance` tells the reviewer whether
retries blew the estimate.

## Target Conditions

- TC-AG-1: Given a metrics.md with N rows, frontmatter
  `total_tokens_in` equals the row sum to the integer.
- TC-AG-2: Same for `total_tokens_out`, `total_duration`,
  `total_cost`, `agent_runs`.
- TC-AG-3: `recompute_frontmatter` is idempotent (byte-identical
  output on second run).
- TC-AG-4: `update_task_actuals` on a fixture manifest + metrics
  pair produces hand-computed Actual/Variance values exactly.
- TC-AG-5: `update_task_actuals` leaves all non-matching rows
  byte-identical (diff has exactly one changed row).
- TC-AG-6: `format_duration(16 * 60)` == `"16min"`; `format_duration(95)`
  == `"95s"`; table-driven over ≥ 6 cases.

## Dependencies

- `schemas/row_schema.md` — parser target.
- `design-capture-contract.md` — writer invokes aggregator after
  every append.
