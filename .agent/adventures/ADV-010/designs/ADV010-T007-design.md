# Capture Entrypoint with Error Isolation - Design

## Approach
Implement two new Python modules: `.agent/telemetry/capture.py` (the hook entrypoint) and `.agent/telemetry/log.py` (error-log helpers). `capture.py` wires together T004 (cost_model), T005 (schema), and T006 (aggregator) behind a `main()` guardrail that catches all `Exception` subclasses, logs failures to `capture-errors.log` as JSONL, and always exits 0. `KeyboardInterrupt` and `SystemExit` propagate normally.

## Target Files
- `.agent/telemetry/capture.py` - New. Hook entrypoint with `main()`, `normalize_payload()`, `resolve_adventure_id()`, `read_stdin()`, `append_row()`, `metrics_path()`, `manifest_path()`.
- `.agent/telemetry/log.py` - New. Error-logging helpers: `log_capture_error(exc, raw_payload)` writing JSONL lines to `capture-errors.log`.

## Implementation Steps

### Step 1: Create `.agent/telemetry/log.py`

Implement the error-log helper module:

```python
def log_capture_error(exc: Exception, raw_payload: str | None = None) -> None:
```

- Write one JSON line per call to `.agent/telemetry/capture-errors.log` (append mode, create on first failure).
- JSONL format: `{"ts": "<ISO-8601-UTC>", "exc": "<class name>", "msg": "<str(exc)>", "payload_excerpt": "<first 500 chars of raw_payload or null>"}`.
- Use `datetime.datetime.now(datetime.timezone.utc)` for timestamp.
- The function itself must never raise; wrap its body in a bare `try/except` that silently drops write failures (a logging failure must not mask the original error).
- Use only stdlib: `json`, `datetime`, `os`, `pathlib`.

### Step 2: Create `.agent/telemetry/capture.py` - Core Functions

#### `read_stdin() -> str`
- Read all of `sys.stdin` (`.read()`). Return raw string.
- On empty stdin, raise `PayloadError("empty stdin")`.

#### `normalize_payload(raw: dict) -> dict`
- Alias wire fields to internal names per `design-hook-integration.md`:
  - `event` -> `event_type`
  - `task_id` -> `task`
  - `usage.input_tokens` -> `tokens_in` (unwrap nested dict)
  - `usage.output_tokens` -> `tokens_out` (unwrap nested dict)
- Pass through fields already using internal names (idempotent normalization).
- `adventure_id` resolution via `resolve_adventure_id(payload)`.
- `model` normalization via `cost_model.normalize_model(payload["model"])`.

#### `resolve_adventure_id(payload: dict) -> str`
Resolution order (first hit wins):
1. `payload.get("adventure_id")` if present and matches `^ADV-\d{3}$`.
2. `payload.get("task_id")` or `payload.get("task")` — extract `ADV\d{3}` prefix, format as `ADV-NNN`.
3. `os.environ.get("ADVENTURE_ID")` if set and valid.
4. Parse `payload.get("cwd", "")` for `.agent/adventures/ADV-NNN/` path segment.
5. Raise `PayloadError("cannot resolve adventure_id")`.

#### `append_row(adventure_id: str, row: MetricsRow) -> pathlib.Path`
- Compute `metrics_path(adventure_id)` -> `.agent/adventures/{adventure_id}/metrics.md`.
- Read existing file; parse rows via `aggregator.parse_rows()`.
- Check idempotency: if any existing row has matching `Run ID`, return early (no-op).
- Append the serialized row line to the file (after the last row or after the table header if empty).
- Return the metrics path for subsequent aggregation.

#### `metrics_path(adventure_id: str) -> pathlib.Path`
- Return `Path(".agent/adventures") / adventure_id / "metrics.md"`.
- Resolve relative to the script's expected working directory.

#### `manifest_path(adventure_id: str) -> pathlib.Path`
- Return `Path(".agent/adventures") / adventure_id / "manifest.md"` (or equivalent adventure manifest location).

### Step 3: Create `.agent/telemetry/capture.py` - `main()` Guardrail

```python
def main(argv: list[str] | None = None) -> int:
    raw_payload: str | None = None
    try:
        raw_payload = read_stdin()
        payload = json.loads(raw_payload)
        payload = normalize_payload(payload)
        event = schema.validate_event(payload)
        row = schema.build_row(event)
        mp = append_row(event.adventure_id, row)
        aggregator.recompute_frontmatter(mp)
        if event.task:
            update_task_actuals(manifest_path(event.adventure_id), event.task)
    except Exception as exc:  # noqa: BLE001 -- intentional catch-all
        log_capture_error(exc, raw_payload=raw_payload)
    return 0  # always 0
```

Key design decisions:
- `raw_payload` is declared before the try block so it is available in the except clause even if `read_stdin()` itself fails.
- `KeyboardInterrupt` is NOT caught (`Exception` does not cover it).
- `SystemExit` is NOT caught (`Exception` does not cover it in Python 3).
- The `--event` CLI flag (from hook integration) can be parsed via `argv` to distinguish `SubagentStop` vs `PostToolUse` triggers but is not needed for core row-writing logic (idempotency handles double-fire).

### Step 4: Wire the `if __name__ == "__main__"` block

```python
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

This ensures `capture.py` is invocable as `python .agent/telemetry/capture.py` from the hook command.

### Step 5: `update_task_actuals` stub or import

- If `task_actuals.py` exists (from T006 or a later task), import and call `task_actuals.update()`.
- If not yet implemented, wrap the call in a try/except that catches `ImportError` and logs gracefully. The task_actuals propagation is a secondary concern for this task; the primary contract is row-append + aggregation.

## Testing Strategy

All tests are subprocess-based per the role file and acceptance criteria:

1. **Valid JSON -> row written, exit 0**: Create a temp directory with a fixture `metrics.md`. Pipe valid event JSON via `subprocess.run([sys.executable, "-m", "telemetry.capture"], input=..., capture_output=True, check=False, timeout=5)`. Assert `returncode == 0`. Parse the metrics.md and verify exactly one new row with correct columns.

2. **Malformed JSON -> exit 0 + error log**: Pipe `"not json"` to stdin. Assert `returncode == 0`. Assert `capture-errors.log` exists and contains one JSONL line with `"exc": "PayloadError"` (or `JSONDecodeError`).

3. **Idempotency**: Pipe the same valid event twice. Assert only one row exists in metrics.md after both runs.

4. **KeyboardInterrupt propagates**: This is harder to test via subprocess. One approach: a small wrapper script that sends SIGINT to the capture process and asserts non-zero exit. Alternatively, test via direct import of `main()` in a unittest that patches stdin and raises `KeyboardInterrupt` inside the try block, asserting it is not caught.

5. **Error log format**: After triggering a failure, parse the JSONL line and assert keys `ts`, `exc`, `msg` are present and `ts` is valid ISO-8601.

## Risks

1. **T004-T006 not yet implemented**: `capture.py` imports from `cost_model`, `schema`, and `aggregator`. If those modules do not exist yet at implementation time, the implementer must either (a) wait for dependencies or (b) create minimal stubs. The task's `depends_on: [ADV010-T006]` should prevent premature scheduling.

2. **Windows path handling**: `metrics_path()` and `manifest_path()` must work on Windows (the target platform). Use `pathlib.Path` throughout, never hardcode `/` separators.

3. **Concurrent writes**: If two hooks fire simultaneously (unlikely but possible with `SubagentStop` + `PostToolUse`), the append could race. The 5s timeout and idempotency check mitigate but do not fully prevent this. Accepted risk per design-error-isolation.md's partial-failure semantics.

4. **task_actuals module availability**: May not exist at T007 implementation time. The design calls for a graceful import guard.
