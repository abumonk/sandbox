---
task_id: ADV009-T020
adventure_id: ADV-009
status: PASSED
timestamp: 2026-04-18T00:04:00Z
build_result: N/A
test_result: PASS
---

# Review: ADV009-T020

## Summary
| Field | Value |
|-------|-------|
| Task | ADV009-T020 |
| Title | Add graph edit affordances (drag, click, right-click menu) |
| Status | PASSED |
| Timestamp | 2026-04-18T00:04:00Z |

## Build Result
- Command: N/A (no build command configured in `.agent/config.md`)
- Result: N/A
- Output: No compilation step required — vanilla JS in a single HTML file.

## Test Result
- Command: `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_pipeline_tab.py"`
- Result: PASS
- Pass/Fail: 13/0
- Output:
  ```
  Ran 13 tests in 0.027s
  OK
  ```

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | Drag gesture fires exactly one POST per completed gesture | Yes | `muHandler` self-removes from the DOM event listener on its first call via `removeEventListener`, and all POST calls are wrapped in `guardOnce` which blocks re-entry for 500 ms. TC-055 tests both the guard constant (EDIT_GUARD_MS=500) and the `guardOnce` call inside `_wireDragToDepend`. |
| 2 | On 4xx, the optimistic edge is removed and a `.toast` shows the server's error message | Yes | The catch block inside `guardOnce` calls `cy.remove('#' + optId)` and then `toast(msg, 'error')`. TC-056 verifies `cy.remove(` appears after `catch` in `_wireDragToDepend`. |
| 3 | Context menu items route only to existing endpoints + the new depends_on POST; no other new routes introduced here | Yes | Static inspection of the `PipelineEdit` block confirms zero raw `fetch(` or `post(` calls. All mutations use `API.setState`, `API.approveDes`, `API.approvePerm`, `API.applyKB`, and `API.addDepends`. The one raw URL string (`window.open('/api/file?path=...')`) uses the pre-existing `/api/file` route for the "Open document" navigation (not a mutation). |
| 4 | State-transition click posts to `/api/adventures/{id}/state` with the same payload as the v1 Decisions tab | Yes | `_wireStateEdgeClick` calls `API.setState(adv.id, name)` which posts `{new_state}` — the same helper and payload used by the Decisions tab at line 2109. |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-055 | Drag-to-connect emits exactly one POST per gesture | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_pipeline_tab.TestDragOneShot` | PASS | `test_drag_handler_calls_guard ... ok`, `test_single_post_guard ... ok` |
| TC-056 | 4xx response rolls visual edge back | autotest | `python -m unittest .agent.adventures.ADV-009.tests.test_pipeline_tab.TestRollback` | PASS | `test_optimistic_removal_on_4xx ... ok` |
| TC-057 | Context menu items route only to existing endpoints + depends_on | poc | Inspect `PipelineEdit` block: grep for raw `fetch(`/`post(` — zero found; all mutations via `API.*`; `window.open` for doc link uses existing `/api/file` route | PASS | No raw API strings found inside PipelineEdit for mutations; `API.*` calls: setState, approveDes, approvePerm, applyKB, addDepends |

## Issues Found

No issues found.

## Recommendations

The implementation is clean and matches the design contract exactly. A few optional notes for future consideration:

1. The `window.open('/api/file?path=...')` in `showMenu` bypasses the `API.file` helper (which wraps the same URL). This is intentional for opening in a new tab but is a minor inconsistency with the "all routes through API.*" comment. Not a defect — navigation vs mutation is a valid distinction.
2. The `{ once: false }` option on the `mouseup` event listener (line 2421) is redundant since the handler removes itself on first invocation. Harmless but slightly misleading.
3. `applyGraphDiff` correctly skips optimistic edges via `!el.data('optimistic')` guard (line 2048), fulfilling the risk mitigation described in the T020 design for poll-tick racing.
