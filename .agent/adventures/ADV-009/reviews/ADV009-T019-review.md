---
task_id: ADV009-T019
adventure_id: ADV-009
status: PASSED
timestamp: 2026-04-18T00:00:05Z
build_result: PASS
test_result: PASS
---

# Review: ADV009-T019

## Summary
| Field | Value |
|-------|-------|
| Task | ADV009-T019 |
| Title | Implement Pipeline tab rendering (cytoscape + polling) |
| Status | PASSED |
| Timestamp | 2026-04-18T00:00:05Z |

## Build Result
- Command: _(no build command configured in config.md)_
- Result: PASS
- Output: N/A — single-file HTML/JS, no build step required

## Test Result
- Command: `python -m unittest discover -s tests -p "test_*.py"` (run from `.agent/adventures/ADV-009/`)
- Result: PASS
- Pass/Fail: 79 passed, 8 skipped, 0 failed
- Output:
  ```
  Ran 79 tests in 2.894s
  OK (skipped=8)
  ```

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | Pipeline appears as the 4th top-level tab (between Documents and Decisions) — total of 5 tabs | Yes | `TABS_V2` at line 747 defines five tabs in order: overview, tasks, documents, pipeline, decisions. Pipeline is index 3 (4th). |
| 2 | cytoscape loaded from a CDN URL (`https://cdn.jsdelivr.net/.../cytoscape...`); no local copy, no bundler artifact | Yes | Line 8: `https://cdn.jsdelivr.net/npm/cytoscape@3.28.1/dist/cytoscape.min.js`. No local vendor path present. |
| 3 | Graph renders adventure/phase/task/document/tc/decision nodes with status-colour mapping per design | Yes | `buildCyStyle()` at line 1943 maps all six node kinds to correct CSS-var-derived colours: task→accent/ok/err, tc→ok/err, decision→warn/ok, document→muted/text, adventure→accent/ok/err, phase→muted/ok. |
| 4 | Polling uses `setTimeout` at 5000 ms default, overridable via `?poll=N`; no WebSocket/EventSource anywhere in `index.html` | Yes | `pipelinePollMs()` at line 1844 reads `?poll` param, falls back to 5000. `pollGraph()` uses `setTimeout` at line 2026. `grep` confirms zero WebSocket/EventSource hits. |
| 5 | Tooltip text read exclusively from `explanations[id]` returned by `/api/adventures/{id}/graph`; no hardcoded tooltip strings inside `renderPipeline`/`showTooltip` | Yes | `showTooltip()` at line 2080: `const text = this.lastGraphExplanations[node.id()] \|\| ''`. No domain strings hardcoded in the function body. |
| 6 | Polling timer is cleared on tab switch, adventure switch, and detail refresh (no orphaned pollers) | Yes | `stopPolling()` called from: `switchTab()` (line 774), `open()` (line 662, covers adventure switch), and `mountCytoscape()` (line 1892). `reopen()` delegates to `open()` which calls `stopPolling()`. All exit paths covered. |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|--------------|---------|--------|--------|
| TC-047 | index.html loads cytoscape via a CDN `<script>` tag (no bundler, no local copy) | autotest | `python -m unittest tests.test_pipeline_tab.TestCdn` | PASS | `test_cytoscape_script_tag ... ok` |
| TC-048 | Pipeline tab appears as 4th top-level tab, between Documents and Decisions (5 tabs total) | autotest | `python -m unittest tests.test_pipeline_tab.TestTabOrder` | PASS | `test_five_tabs_pipeline_fourth ... ok` |
| TC-049 | Node status colours follow design mapping (task/tc/decision/document) | autotest | `python -m unittest tests.test_pipeline_tab.TestStatusColours` | PASS | 5 subtests all `ok` |
| TC-050 | Polling uses setTimeout; no WebSocket/EventSource in server.py or index.html | autotest | `python -m unittest tests.test_pipeline_tab.TestNoWebsocket` | PASS | `test_no_ws_or_eventsource ... ok` |
| TC-051 | Tooltip text comes from backend explanations map (no hardcoded tooltip strings in renderPipeline) | autotest | `python -m unittest tests.test_pipeline_tab.TestTooltipsFromBackend` | PASS | `test_explanations_set_from_backend ... ok`, `test_no_hardcoded_tooltip_strings ... ok` |

## Issues Found

No issues found.

## Recommendations

The implementation is clean and faithful to the design. A few quality observations:

- The design specified a `nodeStyleFor(kind, status)` helper but the implementation consolidates this into `buildCyStyle(colours)` which returns the full style array. This is a sound architectural choice — the selector-based approach is more idiomatic for cytoscape and avoids per-node function calls at runtime.
- `applyGraphDiff` correctly preserves layout on status-only updates by checking `nodeSetChanged` before re-running the layout. The optimistic-edge preservation (`!el.data('optimistic')`) is a forward-compatible hook for T020.
- The empty-state fallback in `pollGraph` (lines 2015-2022) handles the case where the `/graph` backend is absent without throwing, as required by the design's risk section.
- The `queueMicrotask` deferral in `renderPipeline` (line 1866) correctly ensures the canvas `div` is in the DOM before cytoscape mounts to it.
