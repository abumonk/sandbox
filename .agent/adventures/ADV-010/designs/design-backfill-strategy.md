# Design — Backfill Strategy

## Overview

Reconstruct historical telemetry for ADV-001..ADV-007 (and fill
gaps in ADV-008, ADV-009) from every available trail. Emits rows to
each adventure's `metrics.md` with an explicit `Confidence` column so
live-captured data is never confused with reconstructed data.
Reversible: writes to `metrics.md.new`, diffs, prompts, then renames.

## Target files

- `.agent/telemetry/tools/backfill.py` — the reconstruction tool
  (new).
- `.agent/telemetry/tools/reconstructors/` — submodules, one per
  data source (new):
  - `log_parser.py` — parses `adventure.log`.
  - `git_windows.py` — derives duration bounds from git commits.
  - `task_logs.py` — reads task-file `## Log` sections.
  - `existing_rows.py` — preserves already-populated rows (ADV-008).
- `.agent/adventures/ADV-010/tests/test_backfill.py` — autotests.
- Each historical `metrics.md` — rewritten in-place (only by this
  tool; see reversibility rules below).

## Sources used per adventure

For each `.agent/adventures/ADV-NNN/` the tool collects:

1. **Existing rows in `metrics.md`.** These are treated as ground
   truth and only their `Confidence` column is added. Their
   timestamps are reconstructed from adjacent log entries (best-
   effort) and their `Run ID` is newly generated.
2. **`adventure.log` entries** with `spawn: {task}` and the following
   `complete` / status-update entries. Duration = delta.
3. **Git history** over the adventure's `created..updated` window:
   `git log --pretty=format:"%H|%ai|%s" --name-only` filtered by
   paths that start with `.agent/adventures/ADV-NNN/`. Produces a
   per-task lower-bound duration (first commit touching a task
   file to last commit).
4. **Task files' `## Log` sections** (e.g.
   `.agent/adventures/ADV-NNN/tasks/ADVNNN-T001.md`). Provides
   status transitions and implementer identity.

## Reconstruction algorithm

For each task T in adventure A:

```
candidates = []
if row exists in metrics.md for T:
    candidates.append(Row(source="existing", confidence=high-if-no-tilde-else-medium))
if log has spawn+complete markers for T:
    candidates.append(Row(source="log", confidence=medium,
                          tokens_in=estimate_from_model_and_duration(...)))
if git touches T's files:
    candidates.append(Row(source="git", confidence=low,
                          duration=commit_last - commit_first,
                          tokens_in=0, tokens_out=0))
if task file has log section:
    candidates.append(Row(source="task_log", confidence=medium,
                          duration=status_transition_delta, ...))

# Merge: pick the candidate with highest confidence for each field.
# For token estimation:
# - if "existing" candidate has tokens: use them, strip tilde.
# - else: estimate_tokens(duration_s, model) via rough prior
#   (opus: ~6K/min in + ~1.5K/min out; sonnet: ~4K/min in + ~800/min out)
#   and set confidence=estimated.
```

The token-estimation prior is derived from ADV-008's populated rows
(the only live-ish sample we have). It is intentionally conservative
and the `confidence` column makes its uncertainty visible.

### Unreconstructable periods

If no source contains information for a known task (e.g. a task
file exists with `status: done` but zero log, git, or row evidence),
the tool emits one row with:

```
| <newid> | <adv.updated> | unknown | <task> | unknown | 0 | 0 | 0 | 0 | 0.0000 | unrecoverable | estimated |
```

This keeps `agent_runs > 0` (satisfies the autotest) while making
the gap visible to human readers.

## Confidence grading

| Grade       | Criteria                                              |
|-------------|-------------------------------------------------------|
| `high`      | Live hook capture. Not emitted by backfill.           |
| `medium`    | ≥ 2 independent sources (e.g. existing row + log).    |
| `low`       | Single source with concrete numbers (e.g. git only).  |
| `estimated` | Token prior used; duration may also be prior-derived. |

## Reversibility contract

Backfill never writes to `metrics.md` directly. Workflow:

1. Read `metrics.md` → in-memory model.
2. Apply reconstruction → in-memory model'.
3. Write `metrics.md.new`.
4. Emit a unified diff to stdout for review.
5. If invoked with `--apply`: rename `metrics.md` →
   `metrics.md.backup.<ts>`, rename `metrics.md.new` →
   `metrics.md`. Exit 0 with the backup path logged.
6. If invoked without `--apply` (default): exit 0, leaving
   `metrics.md.new` beside the original for human comparison.

Rollback at any time: `mv metrics.md.backup.<ts> metrics.md`.

## CLI

```
python -m telemetry.tools.backfill {--adventure ADV-NNN | --all}
                                   [--apply]
                                   [--dry-run]
                                   [--sources existing,log,git,task_log]
```

`--sources` lets us re-run with a subset after inspecting the diff.

## Target Conditions

- TC-BF-1: After backfill on every completed adventure
  (ADV-001..ADV-009), each `metrics.md` has `agent_runs > 0` in
  frontmatter.
- TC-BF-2: Backfill on ADV-008 preserves every existing row's
  numeric fields (strips only the `~` tildes) — a regression test
  over the file's 34-row corpus.
- TC-BF-3: Backfill run twice on the same input produces a
  byte-identical second-run output (idempotency via Run ID
  stability).
- TC-BF-4: Every backfill-emitted row has a non-default
  `Confidence` column (`medium`/`low`/`estimated`) — never `high`.
- TC-BF-5: An unreconstructable task produces a row with
  `result: unrecoverable` and is counted in a reported summary.
- TC-BF-6: Without `--apply`, the original `metrics.md` is
  unmodified (reversibility guard).

## Dependencies

- `schemas/row_schema.md` — output shape.
- `design-cost-model.md` — for computing cost on reconstructed rows.
- `design-aggregation-rules.md` — backfill triggers an aggregation
  pass after writing rows.
