# Event Payload Schema — SubagentEvent

Version: 1.0.0  
Status: finalized  
Single source of truth for T004 (`schema.py`) and T005 (`capture.py`).

---

## SubagentEvent (internal canonical form)

A frozen dataclass in `.agent/telemetry/schema.py`. Represents the
canonical internal shape of a subagent-completion event **after**
`normalize_payload()` has rewritten wire-field aliases.

### Fields

| # | Field          | Python type       | Required | Constraint                                                             |
|---|----------------|-------------------|----------|------------------------------------------------------------------------|
| 1 | `event_type`   | `str`             | yes      | `"SubagentStop"` or `"PostToolUse"`                                    |
| 2 | `timestamp`    | `str`             | yes      | ISO-8601 UTC, regex `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`        |
| 3 | `adventure_id` | `str`             | yes      | regex `^ADV-\d{3}$`                                                    |
| 4 | `agent`        | `str`             | yes      | non-empty string; lowercase hyphenated by convention                   |
| 5 | `task`         | `Optional[str]`   | no       | `None` or regex `^ADV\d{3}-T\d{3}$`                                   |
| 6 | `model`        | `str`             | yes      | in `cost_model.known_models()` (e.g. `"opus"`, `"sonnet"`, `"haiku"`) |
| 7 | `tokens_in`    | `int`             | yes      | `>= 0`                                                                 |
| 8 | `tokens_out`   | `int`             | yes      | `>= 0`                                                                 |
| 9 | `duration_ms`  | `int`             | yes      | `> 0` (sub-ms runs are rounded up to 1 ms by the hook runtime)         |
|10 | `turns`        | `int`             | yes      | `>= 0`                                                                 |
|11 | `result`       | `str`             | yes      | one of `{"complete","ready","done","passed","failed","error"}`          |
|12 | `session_id`   | `Optional[str]`   | no       | any non-empty string, or `None`; used in Run ID computation             |

**Notes:**
- `task` is `None` for adventure-level agents (e.g. `adventure-planner`) that
  are not tied to a specific task.
- `session_id` may be absent in older hook payloads. When absent, `Run ID`
  is computable from the other 5 deterministic fields.
- `model` is the *normalized* model family string, not the full API model ID.
  `normalize_payload()` applies the mapping `"claude-opus-*" → "opus"`, etc.

---

## Wire payload (pre-normalize)

A dict parsed from stdin JSON. Field names differ from the internal dataclass;
`normalize_payload()` in `capture.py` performs all aliasing before validation.

### Wire-to-internal alias table

| Wire field             | Internal field   | Transform                                                |
|------------------------|------------------|----------------------------------------------------------|
| `event`                | `event_type`     | direct copy                                              |
| `task_id`              | `task`           | direct copy; absent → `None`                             |
| `usage.input_tokens`   | `tokens_in`      | unwrap nested dict                                       |
| `usage.output_tokens`  | `tokens_out`     | unwrap nested dict                                       |
| `cwd`                  | (not stored)     | used only during `adventure_id` resolution (see below)   |

All other wire fields (`timestamp`, `session_id`, `agent`, `model`,
`duration_ms`, `turns`, `result`) are copied directly under the same name.

### Example wire payload

```json
{
  "event": "SubagentStop",
  "timestamp": "2026-04-15T01:23:45Z",
  "session_id": "sess-abc123",
  "cwd": "/r/Sandbox",
  "agent": "adventure-planner",
  "task_id": "ADV010-T003",
  "model": "claude-opus-4-6",
  "usage": {"input_tokens": 48000, "output_tokens": 14000},
  "duration_ms": 720000,
  "turns": 12,
  "result": "complete"
}
```

---

## `adventure_id` resolution order

Resolution is attempted in order; the **first hit** wins:

1. `payload["adventure_id"]` — explicit field in the wire payload.
2. `payload["task_id"]` prefix — extract `ADV\d{3}` from the task ID string
   and reformat as `ADV-NNN`.
3. Environment variable `ADVENTURE_ID` if set by the parent pipeline process.
4. Parse `cwd` for a path segment matching `.agent/adventures/ADV-NNN/` and
   extract `ADV-NNN`.
5. **Fail** — log to `capture-errors.log` and exit 0 (never non-zero).

---

## Validation error catalog

`schema.validate_event(payload: dict) -> SubagentEvent` raises `CaptureError`
on any of the following conditions. Each case must have a dedicated test in
T016:

| # | Condition                                                              | Error message (prefix)             |
|---|------------------------------------------------------------------------|------------------------------------|
| 1 | Any required field is missing from the normalized dict                 | `"missing required field: {name}"` |
| 2 | `tokens_in` or `tokens_out` is not a non-negative integer              | `"invalid tokens: {field}"`        |
| 3 | `duration_ms` is not a positive integer                                | `"invalid duration_ms"`            |
| 4 | `model` is not in `cost_model.known_models()`                          | `"unknown model: {value}"`         |
| 5 | `adventure_id` does not match `^ADV-\d{3}$`                           | `"invalid adventure_id: {value}"`  |
| 6 | `task` is present but does not match `^ADV\d{3}-T\d{3}$`              | `"invalid task id: {value}"`       |

All six cases cause the event to be dropped; the error is written to
`.agent/telemetry/capture-errors.log` and `capture.py` exits 0.

---

## Relations

- `SubagentEvent` → `MetricsRow` via `build_row(event)` (see `row_schema.md`).
- `SubagentEvent.adventure_id` → a `metrics.md` path via `metrics_path(adventure_id)`.
- `SubagentEvent.task` (non-None, terminal result) → triggers
  `task_actuals.update()` (see `processes.md`).
