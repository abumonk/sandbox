# Design — Error Isolation

## Overview

Any failure inside the capture mechanism must not affect the running
agent pipeline. Capture is a sidecar; its failures are logged, not
raised. This design enumerates the failure classes and the exact
guardrail for each.

## Target files

- `.agent/telemetry/errors.py` — exception hierarchy (new).
- `.agent/telemetry/capture.py` — the top-level `main()` wrapper
  that enforces exit-0.
- `.agent/telemetry/capture-errors.log` — append-only error sink
  (created on first failure).

## Exception hierarchy

```python
class CaptureError(Exception):
    """Base class — any failure inside the telemetry subsystem."""

class PayloadError(CaptureError):      # bad stdin / missing fields
class SchemaError(CaptureError):       # row schema violation
class CostModelError(CaptureError):    # cost_model can't resolve
class UnknownModelError(CostModelError):
class WriteError(CaptureError):        # filesystem / rename failure
class AggregationError(CaptureError):  # recompute failed
class TaskActualsError(CaptureError):  # manifest update failed
```

Unrelated exceptions (`KeyboardInterrupt`, `SystemExit`) propagate.
Everything else is caught and converted to an error-log line.

## The main() guardrail

```python
def main(argv: list[str]) -> int:
    try:
        payload = read_stdin()
        event = validate_event(payload)
        row = build_row(event)
        append_row(event.adventure_id, row)
        recompute_frontmatter(metrics_path(event.adventure_id))
        if event.task:
            update_task_actuals(manifest_path(event.adventure_id),
                                event.task)
    except Exception as exc:  # noqa: BLE001 — intentional catch-all
        log_capture_error(exc, raw_payload=payload if 'payload' in
                          locals() else None)
    return 0    # always 0
```

The bare `except Exception` is justified because:

- This process runs as a subprocess of the agent runtime. A non-zero
  exit here surfaces as a hook failure in the agent's log, which the
  concept explicitly forbids ("capture never blocks the pipeline").
- The hook has a 5s timeout budget; even infinite loops cap there.
- Every caught exception is written to `capture-errors.log` with
  traceback + raw payload excerpt, so failures are still visible to
  humans running `tail -f .agent/telemetry/capture-errors.log`.

## The error log format

One JSON line per failure:

```json
{"ts":"2026-04-15T01:23:45Z","exc":"SchemaError",
 "msg":"tokens_in must be non-negative int","payload_excerpt":"{...first 500 chars...}"}
```

Rationale for JSONL: machine-readable for a future CI check that
scans the error log; human-readable enough with `jq`.

## Partial-failure semantics

What if `append_row` succeeds but `recompute_frontmatter` fails?

- The row is in the file.
- Frontmatter is stale.
- Next successful capture will re-aggregate and heal the drift.

This is acceptable because:

- Rows are ground truth; frontmatter is derived.
- A separate sanity-check autotest runs in CI and will flag any
  drift (TC-AG-1 evaluated across all live adventures).
- Partial state is never worse than zero state (current situation).

## Target Conditions

- TC-EI-1: A `PayloadError` caught inside `main()` causes exit 0,
  not a raised exception (subprocess assertion).
- TC-EI-2: A `WriteError` caused by a read-only `metrics.md` causes
  exit 0 and one JSON line appended to `capture-errors.log`.
- TC-EI-3: A `KeyboardInterrupt` IS NOT caught (propagates as
  expected).
- TC-EI-4: `capture-errors.log` lines are valid JSON and contain
  the keys `ts`, `exc`, `msg`.
- TC-EI-5: After a simulated mid-capture failure (row written,
  aggregator crashed), the **next** successful capture heals the
  frontmatter drift.

## Dependencies

- `design-capture-contract.md` — defines `main()` call sequence.
- `design-hook-integration.md` — defines the 5s timeout.
