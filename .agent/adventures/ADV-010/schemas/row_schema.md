# Row Schema

Version: 1.0.0  
Status: finalized  
Single source of truth for T004 (`schema.py`), T005 (`capture.py`),
T008 (`aggregator.py`), and T016 (test suite).

---

## MetricsRow

Represents one row in the `## Agent Runs` pipe-table of a
`metrics.md`. Frozen dataclass in `.agent/telemetry/schema.py`.

### Column specification

Columns are **fixed-order**. The test `test_row_header_columns_exact`
enforces the exact column sequence below.

| Col | Header          | Python type | Constraint                           | Derivation / notes                                                              |
|-----|-----------------|-------------|--------------------------------------|---------------------------------------------------------------------------------|
| 1   | `Run ID`        | `str`       | 12 hex characters `[0-9a-f]{12}`     | `sha1(f"{adventure_id}\|{agent}\|{task or '-'}\|{model}\|{timestamp}\|{session_id or ''}")[:12]` |
| 2   | `Timestamp`     | `str`       | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`  | copied from `SubagentEvent.timestamp`                                           |
| 3   | `Agent`         | `str`       | non-empty                            | copied from `SubagentEvent.agent`                                               |
| 4   | `Task`          | `str`       | task ID or literal `-`               | `SubagentEvent.task` or `"-"` when `None`                                       |
| 5   | `Model`         | `str`       | normalized family name               | copied from `SubagentEvent.model`                                               |
| 6   | `Tokens In`     | `int`       | `>= 0`                               | copied from `SubagentEvent.tokens_in`                                           |
| 7   | `Tokens Out`    | `int`       | `>= 0`                               | copied from `SubagentEvent.tokens_out`                                          |
| 8   | `Duration (s)`  | `int`       | `>= 1`                               | `max(1, round(SubagentEvent.duration_ms / 1000))`                               |
| 9   | `Turns`         | `int`       | `>= 0`                               | copied from `SubagentEvent.turns`                                               |
| 10  | `Cost (USD)`    | `float`     | `>= 0.0`, 4 decimal places           | `cost_model.cost_for(model, tokens_in, tokens_out)` — pinned at write time      |
| 11  | `Result`        | `str`       | enum (see event_payload.md)          | copied from `SubagentEvent.result`                                              |
| 12  | `Confidence`    | `str`       | `high\|medium\|low\|estimated`       | `"high"` for live hook rows; see backfill docs for other values                 |

### Example row

```
| a1b2c3d4e5f6 | 2026-04-15T01:23:45Z | adventure-planner | - | opus | 48000 | 14000 | 720 | 12 | 0.9300 | complete | high |
```

### Precision rules

- **Tokens**: integer, never rounded, never truncated.
- **Duration**: `max(1, round(duration_ms / 1000))`. Sub-second runs round to
  1 so `total_duration` is never artificially low.
- **Cost**: computed at write time via `cost_model.cost_for()` and pinned to
  the row. Aggregators read the stored value; they do not re-run the cost model.
  Formatted to exactly 4 decimal places (e.g. `0.9300`, not `0.93`).
- **Run ID**: SHA-1 of the pipe-delimited key string, hex-encoded, first 12
  characters retained. Lowercase hex only.

### Idempotency

Before appending, `append_row()` parses the existing `## Agent Runs` table and
checks whether any row's `Run ID` column equals the new row's `Run ID`. If a
match is found, the append is a no-op (return without writing).

### `~` tilde values

The live hook **never** writes a `~`-prefixed value. Legacy rows with `~N`
token counts are handled by the backfill tool, which strips the `~` and sets
`Confidence = estimated`. The schema validator rejects `~`-prefixed integers
on read (raises `SchemaError`).

---

## MetricsFrontmatter

YAML frontmatter block at the top of `metrics.md`, between `---` fences.
Derived exclusively from the `## Agent Runs` table; never hand-authored after
first file initialisation.

### Fields

| Field               | Python type | Constraint       | Derivation                                           |
|---------------------|-------------|------------------|------------------------------------------------------|
| `adventure_id`      | `str`       | `^ADV-\d{3}$`   | set at file creation; not recomputed                 |
| `total_tokens_in`   | `int`       | `>= 0`          | sum of all `Tokens In` column values                 |
| `total_tokens_out`  | `int`       | `>= 0`          | sum of all `Tokens Out` column values                |
| `total_duration`    | `int`       | `>= 0`          | sum of all `Duration (s)` column values (seconds)    |
| `total_cost`        | `float`     | `>= 0.0`, 4dp   | sum of all `Cost (USD)` column values                |
| `agent_runs`        | `int`       | `>= 0`          | count of data rows (header and separator not counted) |

**Schema bump note**: `total_duration` is now integer seconds. Historical
`metrics.md` files store mixed strings (`"16min"`, `"95s"`). The backfill tool
converts these on its first pass; the aggregator then writes the integer.

---

## ManifestEvaluationRow

Row in a manifest's `## Evaluations` pipe-table. The planner writes the
estimate columns; the capture pipeline fills the actual columns when a task
reaches a terminal result.

### Column specification

| Col | Header              | Type           | Constraint                                         |
|-----|---------------------|----------------|----------------------------------------------------|
| 1   | `Task`              | `str`          | task ID, e.g. `ADV010-T003`                        |
| 2   | `Access Requirements`| `str`         | free-form list                                     |
| 3   | `Skill Set`         | `str`          | free-form list                                     |
| 4   | `Est. Duration`     | `str`          | human string, e.g. `"15min"`                       |
| 5   | `Est. Tokens`       | `int`          | `>= 0`                                             |
| 6   | `Est. Cost`         | `str`          | leading `$` preserved, e.g. `"$0.0675"`            |
| 7   | `Actual Duration`   | `str`          | `"16min"` or `"—"` (em-dash) if unset              |
| 8   | `Actual Tokens`     | `int \| str`   | integer or `"—"` if unset                          |
| 9   | `Actual Cost`       | `str`          | `"$1.2345"` or `"—"` if unset                      |
| 10  | `Variance`          | `str`          | signed `"+12%"` / `"-8%"` / `"±0%"` or `"—"`      |

**Variance formula**: `(actual − estimate) / estimate`, expressed as a signed
integer percentage rounded to the nearest whole number. When `estimate` is 0,
variance is `"—"`.

**Actual Duration formatting**: reported as `"Nmin"` when `>= 60 s`, `"Ns"`
otherwise. Derived from `sum(Duration (s))` of matching metrics rows.

---

## Row parsing algorithm

Used by `aggregator.py`, `task_actuals.py`, and the schema test suite:

1. Read file bytes.
2. Split on first `\n---\n` after optional leading `---\n` to separate
   frontmatter from body.
3. Parse frontmatter with the hand-rolled YAML subset reader (see
   `design-cost-model.md` §YAML constraint).
4. In the body, locate the first pipe-table following a `## Agent Runs` heading.
5. Skip the header row and the separator row (`|---|---|...`).
6. For each data row: split on `|`, strip each cell, coerce types via the
   column-index map above.

Error paths:

- `## Agent Runs` heading not found → `SchemaError("missing Agent Runs section")`
- Wrong column count → `SchemaError(line=N, msg="expected 12 columns, got M")`
- Non-numeric value in a numeric column (e.g. `~48000`) → `SchemaError(line=N, column="Tokens In")`
- `Run ID` not matching `[0-9a-f]{12}` → `SchemaError(line=N, column="Run ID")`
