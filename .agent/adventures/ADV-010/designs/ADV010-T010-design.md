# Wire Task Actuals into capture.py - Design

## Approach

Add a post-aggregation step in `capture.py`'s `main()` that conditionally
invokes `task_actuals.update()` when the event carries a non-empty `task`
field and a terminal `result`. The call is wrapped in the existing
`except Exception` guardrail so a `TaskActualsError` logs to
`capture-errors.log` and exits 0 without propagating.

This is a small wiring task: the heavy logic lives in `task_actuals.py`
(T009). T010 only adds the import, the conditional call, and the
`manifest_path()` helper (if not already present from T007).

## Target Files

- `.agent/telemetry/capture.py` - Add import of `task_actuals`, define
  `manifest_path()` helper, add conditional call after
  `recompute_frontmatter` inside `main()`.

## Implementation Steps

1. **Add import** at the top of `capture.py`:
   ```python
   from . import task_actuals
   ```
   (or `import telemetry.task_actuals as task_actuals` depending on the
   import style established in T007).

2. **Define `manifest_path()` helper** (if not already present from T007):
   ```python
   def manifest_path(adventure_id: str) -> Path:
       """Return the adventure manifest path for the given adventure ID."""
       return Path(f".agent/adventures/{adventure_id}/manifest.md")
   ```
   This mirrors the existing `metrics_path()` pattern from T007. The
   manifest is the adventure's main planning document that contains the
   `## Evaluations` pipe-table.

3. **Define terminal result set** as a module-level constant:
   ```python
   TERMINAL_RESULTS = frozenset({"done", "complete", "passed", "ready", "failed", "error"})
   ```
   These are the result values from `design-capture-contract.md` that
   indicate the task run has finished (vs. intermediate states).

4. **Add conditional call** in `main()`, immediately after the
   `recompute_frontmatter(metrics_path(event.adventure_id))` line and
   still inside the existing `try` block:
   ```python
   if event.task and event.result in TERMINAL_RESULTS:
       task_actuals.update(manifest_path(event.adventure_id), event.task)
   ```
   The guard checks:
   - `event.task` is truthy (non-None, non-empty) -- adventure-level
     agents like `adventure-planner` have `task=None`.
   - `event.result` is terminal -- non-terminal results should not
     trigger actuals recomputation.

5. **Error isolation is already handled**: The entire body of `main()` is
   wrapped in `except Exception` per `design-error-isolation.md`. If
   `task_actuals.update()` raises `TaskActualsError` (or any other
   `Exception` subclass), it will be caught by the existing guardrail,
   logged to `capture-errors.log`, and `main()` will return 0.

   No additional try/except is needed around the `task_actuals.update()`
   call specifically -- the outer guardrail covers it. This matches the
   pseudocode in `design-error-isolation.md` exactly.

6. **Partial-failure semantics**: If the row was appended and frontmatter
   recomputed but `task_actuals.update()` fails:
   - The metrics row is safely written (ground truth preserved).
   - The manifest's Evaluations table has stale actuals.
   - The next successful capture for the same task will heal the
     manifest (task_actuals recomputes from all matching metrics rows).
   - This matches `design-error-isolation.md` "partial-failure semantics"
     and is verified by TC-EI-5.

## Testing Strategy

Per the acceptance criteria:

1. **End-to-end test**: Create a synthetic `SubagentEvent` JSON with
   `task: "ADV010-T005"` and a terminal `result`. Pipe it to
   `capture.py` via subprocess. Verify the manifest's `## Evaluations`
   table for T005 now has populated `Actual Duration`, `Actual Tokens`,
   `Actual Cost`, and `Variance` columns. This exercises the full path
   from stdin through to manifest update.

2. **Error isolation test**: Mock or stub `task_actuals.update()` to
   raise `TaskActualsError`. Verify `main()` returns 0 and an entry
   appears in `capture-errors.log`. This can be tested by providing a
   manifest path that doesn't exist or contains a malformed Evaluations
   table.

Both tests align with the subprocess testing convention from the role
file: `subprocess.run([sys.executable, "-m", "telemetry.capture"],
input=payload, capture_output=True, check=False, timeout=5)`.

## Risks

- **Manifest path assumption**: The `manifest_path()` helper assumes the
  manifest is at `.agent/adventures/{ADV-ID}/manifest.md`. If the actual
  filename differs (e.g., `adventure.md`), the helper needs adjustment.
  The implementer should verify the actual filename used in ADV-010.

- **Import ordering**: If T009 (`task_actuals.py`) is not yet
  implemented when T010 runs, the import will fail at module load time.
  This is acceptable since T009 is a declared dependency. The outer
  `except Exception` in `main()` would NOT catch an `ImportError` at
  module level -- but the dependency chain ensures T009 lands first.
