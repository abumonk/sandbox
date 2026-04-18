# Telemetry Capture - Operator Guide

The telemetry subsystem captures token usage from Claude Code hook events, computes
USD cost via configurable per-model rates, writes metrics rows to each adventure's
`metrics.md`, and aggregates frontmatter totals. It runs entirely as a hook subprocess
and never crashes the agent pipeline.

---

## Layout

```
.agent/telemetry/
├── capture.py          # Hook entrypoint: reads JSON from stdin, writes metrics row
├── schema.py           # Dataclasses + validators: SubagentEvent, MetricsRow
├── cost_model.py       # (model, tokens_in, tokens_out) -> USD; reads rates from config.md
├── aggregator.py       # Recomputes adventure frontmatter totals from all metrics rows
├── task_actuals.py     # Propagates actuals into task manifest evaluation tables
├── errors.py           # Exception hierarchy: CaptureError and subclasses
├── log.py              # Append-only writer for capture-errors.log
├── capture-errors.log  # Error sink (created on first failure; never truncated)
└── tools/
    ├── backfill.py              # CLI: reconstructs historical telemetry rows
    └── reconstructors/
        ├── existing_rows.py     # Confidence=high: parses rows already in metrics.md
        ├── log_parser.py        # Confidence=medium: extracts data from adventure.log
        ├── task_logs.py         # Confidence=medium: extracts data from task ## Log sections
        └── git_windows.py       # Confidence=low: infers timing from git commit history
```

---

## How the Hook is Wired

The hook is declared in `.claude/settings.local.json` under the `hooks` key:

```json
"hooks": {
  "SubagentStop": [{ "command": "python .agent/telemetry/capture.py" }],
  "PostToolUse":  [{ "command": "python .agent/telemetry/capture.py" }]
}
```

On each matching event Claude Code serializes the event payload as JSON to the
subprocess's stdin. `capture.py` reads that JSON, validates it with `schema.py`,
looks up the cost via `cost_model.py`, appends a row to the adventure's `metrics.md`,
and calls `aggregator.py` to refresh frontmatter totals.

**Important:** the `permissions.allow` list in `settings.local.json` contains 128
entries that enable tool access. Do not remove or reorder those entries when editing
the hooks block; modifying the wrong section will silently break tool permissions.

For the full payload shape see `.agent/adventures/ADV-010/designs/design-hook-integration.md`.

---

## How to Run Backfill

Use backfill to reconstruct telemetry for adventures that ran before the hook was wired,
or to repair rows that were lost due to a filesystem failure.

**One-liner:**
```bash
python -m telemetry.tools.backfill --adventure ADV-NNN
```

Run from the `R:/Sandbox/.agent` directory (or set `PYTHONPATH` to include it).

**What it does:**

1. Collects candidate rows from all four reconstructors, each tagged with a confidence level.
2. Merges by `(task_id, role)` key, preferring higher-confidence sources.
3. Writes the result to `metrics.md.new` alongside the live file.
4. Prints a unified diff so you can review before committing.
5. Renames `metrics.md.new` -> `metrics.md` only after the diff is confirmed.

**Confidence levels:**

| Level  | Source                        | Notes                              |
|--------|-------------------------------|------------------------------------|
| high   | Existing rows in metrics.md   | Already validated; kept as-is      |
| medium | adventure.log / task ## Log   | Derived from structured log lines  |
| low    | Git commit timestamps         | Timing only; token counts estimated|

The rename step is atomic on most filesystems, making backfill safe to re-run.

---

## How to Read `capture-errors.log`

**Location:** `.agent/telemetry/capture-errors.log`

**Format:** one line per failure, tab-separated:
```
2026-04-18T12:34:56Z	UnknownModelError	Model 'claude-new-4' not in cost config
```

**Exit-0 guardrail:** `capture.py` catches all `CaptureError` subclasses (and bare
`Exception`) before returning, so the hook always exits 0. A failure here never
stalls or crashes the agent pipeline; it only writes a line to this log.

**Exception hierarchy:**

```
CaptureError
├── PayloadError        # stdin was empty, not JSON, or missing required fields
├── SchemaError         # dataclass validation failed after parsing
├── CostModelError
│   └── UnknownModelError  # model key not found in config.md token_cost_per_1k
├── WriteError          # could not append to metrics.md (permissions, disk full)
├── AggregationError    # aggregator failed to recompute totals
└── TaskActualsError    # could not propagate actuals to task manifest
```

**Common triage patterns:**

- `PayloadError` in bulk -> the hook fired on an event type whose payload shape
  changed; check the Claude Code changelog and update `schema.py`.
- `UnknownModelError` -> a new model ID appeared in events; add its rate (see next
  section).
- `WriteError` -> check disk space and file permissions on `metrics.md`.

---

## How to Add a New Cost Rate

Cost rates are stored in `.agent/config.md` frontmatter — no Python changes needed.

1. Open `.agent/config.md`.
2. Find the `token_cost_per_1k:` block under `adventure:`:
   ```yaml
   adventure:
     token_cost_per_1k:
       opus:   0.015
       sonnet: 0.003
       haiku:  0.001
   ```
3. Add a new line with a 4-space indent (to stay inside the `token_cost_per_1k` mapping):
   ```yaml
       new-model-id: 0.NNN
   ```
4. The key must match the `model` field that appears in hook event payloads exactly
   (case-sensitive). Check `capture-errors.log` for the precise string if unsure.

`cost_model.py` re-reads `config.md` on each invocation using a minimal YAML-subset
parser, so the new rate takes effect immediately for the next captured event.

---

## Quick Reference

**Run the test suite:**
```bash
python -m unittest discover -s .agent/adventures/ADV-010/tests -v
```

**Backfill an adventure:**
```bash
python -m telemetry.tools.backfill --adventure ADV-NNN
```

**Tail errors in real time:**
```bash
tail -f .agent/telemetry/capture-errors.log
```
