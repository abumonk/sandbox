# Design — Capture Contract

## Overview

Defines the exact contract between a subagent-completion event and a
row in `.agent/adventures/{ADV-ID}/metrics.md`. The contract is
deliberately narrow so that: (a) the Python writer has a pure-data
input to test against, (b) the hook can be rewritten in a different
runtime without changing the writer, (c) schema drift is caught by a
schema test rather than review eyeballs.

## Target files

- `.agent/telemetry/schema.py` — dataclasses + validators (new).
- `.agent/telemetry/capture.py` — hook entrypoint (new).
- `.agent/adventures/ADV-010/schemas/event_payload.md` — wire format
  specification (new).
- `.agent/adventures/ADV-010/schemas/row_schema.md` — row schema
  specification (new).

## Event payload (input to capture.py)

The hook forwards a JSON object on stdin. Required fields:

```python
@dataclass(frozen=True)
class SubagentEvent:
    event_type: str             # "SubagentStop" | "PostToolUse"
    timestamp: str              # ISO-8601 UTC "YYYY-MM-DDTHH:MM:SSZ"
    adventure_id: str           # "ADV-010" — from cwd or env
    agent: str                  # e.g. "adventure-planner"
    task: Optional[str]         # e.g. "ADV010-T003" or None for non-task runs
    model: str                  # e.g. "claude-opus-4-6" (normalized to "opus"/"sonnet"/"haiku" for cost)
    tokens_in: int              # usage.input_tokens
    tokens_out: int             # usage.output_tokens
    duration_ms: int            # wall-clock milliseconds
    turns: int                  # number of assistant turns
    result: str                 # "complete"|"ready"|"done"|"passed"|"failed"|"error"
    session_id: Optional[str]   # Claude session ID (for idempotency)
```

All fields are required except `task` (None for adventure-level
agents like `adventure-planner`) and `session_id` (absent in older
hook payloads; if missing, `run_id` is still computable from the
other fields).

### Payload validation

`schema.validate_event(payload: dict) -> SubagentEvent` raises
`CaptureError` with a specific message on any of:

- missing required field
- `tokens_in`/`tokens_out` not non-negative int
- `duration_ms` not positive int
- `model` not in known set (cost_model.known_models())
- `adventure_id` does not match `^ADV-\d{3}$`
- `task` (when present) does not match `^ADV\d{3}-T\d{3}$`

## Row shape (output to metrics.md)

One pipe-separated line per event. Column order is fixed:

```
| Run ID | Timestamp | Agent | Task | Model | Tokens In | Tokens Out | Duration (s) | Turns | Cost (USD) | Result | Confidence |
```

Example:

```
| a1b2c3d4e5f6 | 2026-04-15T01:23:45Z | adventure-planner | - | opus | 48000 | 14000 | 720 | 12 | 0.93 | complete | high |
```

Rules:

- `Run ID` = `sha1(f"{adventure_id}|{agent}|{task}|{model}|{timestamp}|{session_id or ''}")[0:12]`.
- `Task` column is `-` (literal ASCII minus) when event has no task.
- `Duration (s)` = `round(duration_ms / 1000)` as integer.
- `Cost (USD)` = `cost_model.cost_for(model, tokens_in, tokens_out)`,
  formatted to 4 decimal places (`0.0037`). No `$` symbol.
- `Confidence` is literal `high` for hook-written rows. Backfill
  rows use `medium`/`low`/`estimated`.

## When is a row written?

- On every `SubagentStop` event (the primary path).
- On `PostToolUse` **only if** `tool == "Task"` AND the nested usage
  block is populated AND there is no already-written row with the
  same `Run ID` (idempotency).

`PostToolUse` is a belt-and-braces fallback for cases where
`SubagentStop` doesn't fire (tool errors, cancelled runs).
Idempotency protects against double-counting when both fire.

## Precision guarantees

- Tokens are integer. Never rounded, never truncated.
- Duration rounds to the nearest second. Sub-second agent runs
  (possible for cached tool lookups) round to 1, not 0, so
  `total_duration` never looks artificially low.
- Cost is computed at write time and pinned to the row. An
  aggregator that reads a row never re-runs the cost model.

## Failure handling

If any of: stdin parse, payload validation, cost computation, file
write — fails, `capture.py`:

1. Writes a line to `.agent/telemetry/capture-errors.log` with the
   timestamp, the exception class, and the first 500 chars of the
   raw stdin payload.
2. Exits `0` (never non-zero). Capture failure must never abort the
   pipeline — see `design-error-isolation.md`.

## Target Conditions

- TC-CC-1: `schema.validate_event` rejects every documented invalid
  payload variant (10 rejection cases) with the right error class.
- TC-CC-2: Given a valid event fixture, `capture.py` writes exactly
  one row to the correct `metrics.md` with every column correctly
  populated in the order declared above.
- TC-CC-3: Running the same event twice writes the row once
  (idempotency — Run ID collision).
- TC-CC-4: Row `Cost (USD)` exactly equals
  `cost_model.cost_for(event.model, event.tokens_in,
  event.tokens_out)` to 4dp.

## Dependencies

- `design-cost-model.md` — supplies `cost_for`.
- `design-hook-integration.md` — supplies the payload on stdin.
