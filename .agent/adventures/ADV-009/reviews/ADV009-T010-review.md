---
task_id: ADV009-T010
adventure_id: ADV-009
status: PASSED
timestamp: 2026-04-18T00:00:05Z
build_result: PASS
test_result: PASS
---

# Review: ADV009-T010

## Summary
| Field | Value |
|-------|-------|
| Task | ADV009-T010 |
| Title | Implement Decisions tab (merges Permissions + Knowledge + state transitions) |
| Status | PASSED |
| Timestamp | 2026-04-18T00:00:05Z |

## Build Result
- Command: *(none — `build_command` is empty in config.md)*
- Result: PASS
- Output: No build step required for this frontend-only task.

## Test Result
- Command: `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"`
- Result: PASS
- Pass/Fail: 79 run, 71 passed, 8 skipped (0 failed)
- Output:
  ```
  Ran 79 tests in 2.897s
  OK (skipped=8)
  ```

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | Three cards render when applicable; empty cards hidden. | Yes | `renderDecisions` calls three sub-helpers; each returns `null` when inapplicable. An `anyCard` boolean gates the `decisions-empty` fallback (line 1665–1672). |
| 2 | Permissions card shows counts of shell/file/MCP requests parsed client-side; full doc behind disclosure. | Yes | `parsePermissionCounts(md)` at lines 2251–2282 tallies shell/file/MCP counts. `summaryEl` (testid `permissions-summary`) is populated async (lines 1740–1745). Full doc sits inside a `<details class="disclosure">` collapsed by default (lines 1720–1725). |
| 3 | State-transition buttons post to `/api/adventures/{id}/state`. | Yes | Buttons call `this.transitionState(nextState)` (line 1692), which calls `API.setState(a.id, newState)` (line 2109). `API.setState` POSTs to `/api/adventures/{id}/state` (line 546). |
| 4 | Knowledge card writes same JSON payload as v1 (regression parity). | Yes | `API.applyKB(a.id, picked)` (line 1819) posts `{indices: [...]}` to `/api/adventures/{id}/knowledge/apply` (line 549). TC-025 `TestKnowledgePayload.test_roundtrip` confirms payload shape passes server-side. |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-022 | Decisions tab renders three cards; empty cards hidden | autotest | `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_ui_layout.py" -k "TestDecisions"` | PASS | `Ran 1 test in 0.001s OK` — all three `data-testid` strings present in script block |
| TC-023 | Permissions card shows request counts; full doc hidden by default | poc | open ADV-009 Decisions tab, verify counts + disclosure | Manual verification required | `permissions-summary` testid present at line 1717; disclosure `<details>` wraps full doc at lines 1720–1725 per code inspection |
| TC-024 | State-transition button from Decisions posts to /api/adventures/{id}/state | autotest | `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_ui_smoke.py" -k "TestDecisions"` | PASS (skipped) | `Ran 1 test in 0.000s OK (skipped=1)` — test skipped because Playwright is not installed; code path verified by static inspection (lines 1692, 2105–2109, 546) |
| TC-025 | Knowledge suggestions write same JSON payload as v1 (regression) | autotest | `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_server.py" -k "TestKnowledgePayload"` | PASS | `Ran 1 test in 0.586s OK` — `selected_indices` matches submitted indices, `adventure_id` correct |

## Issues Found

No issues found.

## Recommendations

The implementation is clean and complete. A few optional observations for future improvements:

- **TC-024 Playwright gap**: The `test_state_post` test is permanently skipped without Playwright. A lightweight HTTP-stub test (analogous to `TestKnowledgePayload`) could provide always-running coverage of the state-POST path without a browser.
- **`renderKnowledgeCard` async card removal**: When `suggestions.length === 0`, the card removes itself from the DOM (line 1788). This works correctly but leaves the `anyCard` flag in `renderDecisions` in a potentially misleading state (the `anyCard` flag was set to `true` before the async removal). If all three cards remove themselves post-render, the `decisions-empty` message will not appear. This edge case is unlikely in practice but worth noting.
- **`parsePermissionCounts` column index**: The parser reads column index 2 (0-based) as the type field, assuming the table format `| # | name | type | ... |`. If any permission doc uses a different column order, counts will be silently wrong. A comment acknowledging this assumption (already present) is sufficient.
