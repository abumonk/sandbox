# Telemetry Gap Analysis — ADV-010

Purpose: enumerate every concrete reason telemetry is not being
captured live. Every finding is grounded in a file path, a line range,
and a current-vs-expected comparison. No prose hand-waving. This
document is the input for all ADV-010 design documents.

## Evidence base

Files inspected (as of 2026-04-15, line numbers verified 2026-04-18):

- `.agent/adventures/ADV-001/metrics.md` through `ADV-010/metrics.md`
- `.agent/config.md`
- `.claude/settings.local.json` (the only Claude-Code settings file
  present in-repo)
- `.agent/knowledge/patterns.md`, `decisions.md`, `issues.md`
- `.agent/adventures/ADV-008/manifest.md` (only adventure with
  populated `## Evaluations` estimate columns; `Actual*` columns empty)
- `.agent/adventures/ADV-008/adventure.log` (only log with a clean
  spawn→complete cadence)

## Finding summary (8 concrete defects)

| # | Defect                                                    | Severity | File(s)                                         |
|---|-----------------------------------------------------------|----------|-------------------------------------------------|
| F1 | No hook registered for `SubagentStop` / `PostToolUse`    | critical | `.claude/settings.local.json`                   |
| F2 | No capture writer exists under `.agent/telemetry/`       | critical | (directory does not exist)                      |
| F3 | No aggregator for frontmatter totals                     | critical | all `.agent/adventures/*/metrics.md`            |
| F4 | No task-actuals propagation to `## Evaluations`          | critical | all `.agent/adventures/*/manifest.md`           |
| F5 | Cost model rates exist but no code reads them            | high     | `.agent/config.md` L15-L21                       |
| F6 | Row schema drift: no `adventure_id` on rows, loose types | high     | all `.agent/adventures/*/metrics.md`            |
| F7 | Agent-run rows often written with `~` tilde estimates    | medium   | e.g. `ADV-001/metrics.md` rows 14-31            |
| F8 | `adventure.log` timestamps unreliable for reconstruction | medium   | see ADV-004 "Log Timestamp Placeholders" issue  |

## F1 — No hook registered for subagent events

**Current state** (`.claude/settings.local.json` L1-L128, verified 2026-04-18):

The file contains only a `permissions.allow` list. There is **no
`hooks` key, no `SubagentStop`, no `PostToolUse`, and no
`PreToolUse`**. The full top-level JSON schema in this file is:

```json
{ "permissions": { "allow": [ ...128 entries... ] } }
```

**Expected state.** Claude Code supports a `hooks` key at the settings
level (per Anthropic's Claude Code hook spec) with event-keyed arrays
of matcher/command pairs. ADV-010 requires at minimum:

```json
"hooks": {
  "SubagentStop": [{"matcher": "*", "hooks": [{"type": "command",
    "command": "python .agent/telemetry/capture.py"}]}],
  "PostToolUse":  [{"matcher": "Task", "hooks": [{"type": "command",
    "command": "python .agent/telemetry/capture.py"}]}]
}
```

**Consequence.** Without this key, no subagent finish event is ever
routed anywhere. Telemetry is simply lost at source. Every other
defect below is downstream of F1.

**Fix owner.** `design-hook-integration.md` (Wave B).

## F2 — No writer exists under `.agent/telemetry/`

**Current state.** `ls .agent/telemetry/` returns nothing (directory
does not exist). `Glob` for `.agent/telemetry/**/*` returns zero
matches.

**Expected state.** Per the approved concept §1, capture is *both*
hook-triggered *and* Python-written. The hook from F1 invokes a
Python script that must exist. The concept names the directory:
`.agent/telemetry/`.

**Consequence.** Even if a hook were registered today, the command
would exit non-zero and the event would be dropped. No code path
appends a row to `metrics.md` from runtime.

**Fix owner.** `design-capture-contract.md` + `plan-wave-b-capture.md`.

## F3 — No aggregator for frontmatter totals

**Current state.** Every `metrics.md` has YAML frontmatter fields
`total_tokens_in`, `total_tokens_out`, `total_duration`,
`total_cost`, `agent_runs`.

- `ADV-001/metrics.md` L2-L7: all five fields are `0` / `0.00`,
  despite **18 data rows** populated in the `## Agent Runs` table
  below (verified 2026-04-18; the file has grown from the 14 rows
  cited at planning time).
- `ADV-008/metrics.md` L2-L7:
  `total_tokens_in: 38000`, `total_tokens_out: 42000`,
  `total_duration: 16min`, `total_cost: 1.20`, `agent_runs: 1` —
  but the table below has **35 data rows**. Frontmatter reflects only the
  first row (the planner), not the sum.
- `ADV-009/metrics.md` L2-L7: zeros even though **46 data rows**
  exist below (verified 2026-04-18; the file has grown significantly
  from the two rows cited at planning time).

**Expected state.** After any row append, frontmatter `total_*`
fields must be recomputed as the exact sum of all row columns, and
`agent_runs` must equal the number of rows.

**Consequence.** Two out of ten adventures have any non-zero
frontmatter, and even those are wrong by a factor of ~8× (38K of
~500K). Any dashboard built on frontmatter is silently mis-reading
99% of the data. This is the exact failure cited in
`knowledge/issues.md` L8 ("Metrics Frontmatter Aggregation Gap").

**Fix owner.** `design-aggregation-rules.md` (Wave B).

## F4 — No task-actuals propagation

**Current state.** `ADV-008/manifest.md` L68-L90 shows an
`## Evaluations` table (header at L69, 19 task rows at L71-L89,
totals row at L90) where every row has populated estimate columns
(`Est. Duration`, `Est. Tokens`, `Est. Cost`) and the three actual
columns plus the `Variance` column are literally `-` (em-dash
placeholder). No other adventure even has estimates populated.

**Expected state.** When a task transitions to `done`, the row for
that task in the manifest `## Evaluations` table must be updated with:

- `Actual Duration` = sum of `Duration` column values in metrics.md
  rows whose `Task` field equals this task's ID.
- `Actual Tokens` = sum of `Tokens In + Tokens Out`.
- `Actual Cost` = sum of per-row cost computed via the cost model.
- `Variance` = `(Actual − Estimate) / Estimate` as a signed
  percentage, formatted as `+12%` / `-8%` / `±0%`.

**Consequence.** Task estimation has no feedback loop. The planner
cannot learn; `knowledge/patterns.md` cannot accumulate
estimate-accuracy lessons; reviewers cannot flag chronically
under-estimated task classes.

**Fix owner.** `design-capture-contract.md` §task-update +
`plan-wave-c-task-actuals.md`.

## F5 — Cost model rates exist but no code reads them

**Current state.** `.agent/config.md` L15-L21 (verified 2026-04-18;
lines shifted from original estimate of L17-L20):

```yaml
adventure:
  max_task_tokens: 100000
  max_task_duration: "30min"
  token_cost_per_1k:
    opus: 0.015
    sonnet: 0.003
    haiku: 0.001
```

These are the only rates in the repo. There is no Python module
that parses this file, and no test fixture that references these
numbers.

**Expected state.** A single `.agent/telemetry/cost_model.py` (stdlib
YAML is not stdlib — see §constraint) parses the frontmatter of
`.agent/config.md`, exposes
`cost_for(model: str, tokens_in: int, tokens_out: int) -> float`, and
raises a clear error on unknown `model` rather than silently
returning 0.0. All ADV-010 target conditions that assert costs must
route through this single function.

Note on YAML parsing: `.agent/config.md` has YAML frontmatter between
`---` fences. Python stdlib does not ship a YAML parser. Since the
grammar used here is trivial (flat + nested mapping of scalars), we
will parse it with a 20-line hand-rolled reader rather than pull in
PyYAML. This is called out explicitly in `design-cost-model.md`.

**Consequence.** Today, every `Est. Cost` value in ADV-008's
manifest was computed by hand in the planner's head (e.g. T01 45K
tokens × $0.015/1K = $0.675). There is no single source of truth;
drift between planner estimation and actual capture is inevitable.

**Fix owner.** `design-cost-model.md`.

## F6 — Row schema drift

**Current state.** The `## Agent Runs` table header across
adventures is:

```
| Agent | Task | Model | Tokens In | Tokens Out | Duration | Turns | Result |
```

Problems:

1. **No `adventure_id` column.** A writer attempting to locate the
   right `metrics.md` must be told externally which adventure the
   event belongs to. No column on a row records that fact. If rows
   are ever merged into a single jsonl for cross-adventure analysis,
   the adventure identity is lost.
2. **No timestamp column.** Rows cannot be ordered, de-duplicated by
   time window, or joined against `adventure.log` entries.
3. **No `run_id` / idempotency key.** Re-running a hook on the same
   event will append a duplicate row. There is no column by which a
   writer can say "skip, already recorded."
4. **Duration is a free-form string.** Rows mix `16min`, `95s`,
   `120s`, `~10min`, `25min`. Summation across rows is currently
   impossible without a parser. The `ADV-001/metrics.md` example
   alone has three formats.
5. **Tokens are sometimes tilde-prefixed** (see F7).
6. **No `cost` column on the row itself.** Per-row cost must be
   re-derived each time the aggregator runs.

**Expected state.** A strict row schema (enforced by a schema test
— see `schemas/row_schema.md`) with columns:

```
| Run ID | Timestamp | Agent | Task | Model | Tokens In | Tokens Out |
| Duration (s) | Turns | Cost (USD) | Result | Confidence |
```

- `Run ID` is a 12-hex SHA-1 prefix over `(agent, task, model,
  start_ts, adventure_id)` — the idempotency key.
- `Duration (s)` is integer seconds, not a string.
- `Cost (USD)` is computed at write time from the cost model and
  pinned to the row (so aggregation does not need to know the
  cost-model version).
- `Confidence` is `high` (live capture) / `medium` (reconstructed
  with 2+ sources) / `low` (single source) / `estimated` (pure
  guess). Default `high` for hook-written rows.

**Consequence.** Without a stable schema, no aggregator, validator,
or backfill script can work reliably.

**Fix owner.** `schemas/event_payload.md` + `schemas/row_schema.md`.

## F7 — Rows with `~` tilde estimates

**Current state.** `ADV-001/metrics.md` has **12 of 18 rows** where at
least one token column begins with `~` (verified 2026-04-18; the file
has grown from 14 to 18 data rows since planning, and 6 rows now use
bare integers):

- Row 14 (L14): `| adventure-planner | - | opus | ~85000 | ~28000 | ~30min | ~40 | complete |`
- Row 29 (L29): `| adventure-reviewer | ADV-001 | opus | ~120000 | ~8000 | ~10min | ~12 | complete |`
  (line number drifted from L28 → L29 due to the addition of rows)

ADV-008 mixes `~` and bare integers inconsistently (L46: `~18000 |
~4000 | 120s`). Any arithmetic aggregator must decide whether `~`
values count as 0, as the trailing integer, or as a confidence-down
rating.

**Expected state.** `~` is never written by the live hook. When the
backfill tool emits a reconstructed row, it writes the bare integer
and sets `Confidence = medium|low|estimated` instead.

**Consequence.** The aggregator's correctness depends on a
value-cleanup step that must be applied before summation. Every
aggregation test must cover both cleanly-typed and tilde-bearing
fixtures.

**Fix owner.** `design-backfill-strategy.md` (migrates historical
tildes to integer + confidence).

## F8 — `adventure.log` timestamps unreliable

**Current state.** `ADV-008/adventure.log` L27 vs L25 (verified
2026-04-18; line numbers confirmed):

```
[2026-04-14T12:30:00Z] shape-grammar-researcher | "spawn: ADV008-T01 implementing"
[2026-04-14T10:42:11Z] geometry-engineer | "spawn: ADV008-T02 implementing"
```

Timestamps are monotonically *decreasing* in file order — because
separate agent threads write concurrently with their own local
clocks and the file was not append-sorted. `knowledge/issues.md`
records this as a known failure mode (ADV-004 "Log Timestamp
Placeholders").

Worse for reconstruction: L27 says T02 started at `10:42:11Z` but
the adventure-creation entry (the chronologically earliest real
event) is at `11:00:00Z` (L5). The knowledge-extractor ran later but
its entries appear at L1-L4 in file order, ahead of the adventure-
creation entries — a second non-monotonic ordering phenomenon. Any
naive backfill that trusts file order will produce wrong durations.

**Expected state.** For live capture, timestamp is taken from the
hook event payload (`event.timestamp` ISO-8601) which is authoritative
— NOT from the log. For backfill, the reconstruction algorithm
pairs log entries with git commit timestamps and takes the **later**
of `spawn` and the predecessor task's `complete` as the start.

**Consequence.** The backfill algorithm must defensively discount
log timestamps; they are hints, not ground truth.

**Fix owner.** `design-backfill-strategy.md`.

## Derived requirements (feed into designs)

1. A Claude Code hook config in `.claude/settings.local.json` (or a
   separate `.claude/settings.json`) that wires `SubagentStop` and
   `PostToolUse` to one Python entrypoint — F1.
2. A `.agent/telemetry/` package with:
   - `capture.py` (hook entrypoint — parses stdin, writes a row)
   - `cost_model.py` (reads `.agent/config.md`, pure function)
   - `aggregator.py` (recomputes frontmatter)
   - `task_actuals.py` (updates manifest `## Evaluations`)
   - `schema.py` (dataclasses + validators)
   — F2, F3, F4, F5.
3. A row schema with idempotency key, timestamp, integer duration,
   pinned cost, confidence — F6, F7.
4. A backfill tool `tools/backfill.py` with its own autotest —
   addresses historical gaps; uses log + git + task-file fusion to
   emit reconstructed rows — F7, F8.
5. A tests harness under `.agent/adventures/ADV-010/tests/` that is
   the single source of CI-discoverable proof. Every TC's
   `proof_command` is a `python -m unittest` invocation pointing at
   a named test in this tree. Default = autotest.

## Constraints carried forward

- Python stdlib only for the writer and backfill, except hand-rolled
  YAML parser for the single config file.
- Do not modify `ark/` (ADV-008 precedent, patterns.md).
- Do not modify other adventures' `metrics.md` except via the
  backfill task, and keep backfill reversible (write to
  `metrics.md.new` first + diff + rename — see
  `design-backfill-strategy.md`).
- Hook config must merge with existing
  `.claude/settings.local.json` permissions; do not clobber the
  128-entry allow list.
