---
task_id: ADV009-T008
adventure_id: ADV-009
status: PASSED
timestamp: 2026-04-18T00:00:10Z
build_result: PASS
test_result: PASS
---

# Review: ADV009-T008

## Summary
| Field | Value |
|-------|-------|
| Task | ADV009-T008 |
| Title | Implement Tasks tab with custom task cards |
| Status | PASSED |
| Timestamp | 2026-04-18T00:00:10Z |

## Build Result
- Command: (none configured in config.md)
- Result: PASS
- Output: No build step required; this is a single-file HTML/JS change.

## Test Result
- Command: `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"`
- Result: PASS
- Pass/Fail: 71 passed, 8 skipped (Playwright not installed), 0 failed
- Output:
  ```
  Ran 79 tests in 2.947s
  OK (skipped=8)
  ```
  The 8 skipped tests are TC-010, TC-011, and related Playwright smoke tests that require a browser binary. All static/unit tests pass.

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | Tasks group by status bucket; empty buckets hidden. | Yes | `renderTasks` uses `BUCKET_ORDER = ['pending', 'in_progress', 'passed', 'failed', 'done']`, skips buckets where `tasks.length === 0`, plus an "Other" bucket. `data-testid="task-bucket-{status}"` hooks present. |
| 2 | Task card hides file path, assignee, iterations by default. | Yes | `renderTaskCard` renders only: status pill, ID, stage, title, depends_on, and TCs. `t.file`, `t.assignee`, and `t.iterations` are not referenced in that function. They appear only in the detail panel's status strip (correct). |
| 3 | Detail panel renders Description and Acceptance Criteria as structured components (not a markdown dump). | Yes | `openTaskDetail` creates separate `.card` elements with `<h3>` headings for Description and Acceptance Criteria. Description is rendered via `marked.parse` on the isolated section text. Acceptance Criteria are parsed line-by-line into `<li>` with `<input type="checkbox" disabled>` elements. |
| 4 | Show-details disclosure contains frontmatter + log + raw source. | Yes | A `<details class="disclosure">` element with `data-testid="task-show-details"` on its `<summary>` contains: frontmatter `<pre>`, file path, log `<pre class="log-tail">`, and full raw source `<pre>`. All collapsed by default. |
| 5 | TC checklist reflects each TC's current status. | Yes | For each TC id in `t.target_conditions`, the implementation looks up `tc.status` from `a.target_conditions`, sets `checked` if `status === 'passed'`/`'PASSED'`, and applies `.status-failed` class for failed TCs. `data-testid="tc-row-{tcId}"` hooks present. |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-008 | Tasks tab groups tasks into status buckets; empty buckets hidden | autotest | `python -m unittest tests.test_ui_layout.TestTasksTab.test_buckets` (run from ADV-009 dir) | PASS | Ran 1 test in 0.001s — OK |
| TC-009 | Task card shows status/ID/title/depends/TCs but no file path or assignee by default | autotest | `python -m unittest tests.test_ui_layout.TestTasksTab.test_card_shape` (run from ADV-009 dir) | PASS | Ran 1 test in 0.001s — OK |
| TC-010 | Task detail renders Description + Acceptance Criteria as components, not markdown blob | autotest | `python -m unittest tests.test_ui_smoke.TestTaskDetail.test_structured` | SKIP | Playwright not installed — test correctly skipped with `@unittest.skipUnless(PW_AVAILABLE, ...)`. Static code review confirms structured DOM construction (lines 1244-1276 of index.html). |
| TC-011 | Frontmatter/log/raw path hidden by default; visible after Show-details toggle | autotest | `python -m unittest tests.test_ui_smoke.TestTaskDetail.test_disclosure` | SKIP | Playwright not installed — same skip guard. Static review confirms `<details class="disclosure">` (not `open`) wraps all three items (lines 1279-1295 of index.html). |
| TC-012 | TC checklist row shows checkbox reflecting TC status | poc | open ADV-007 task, verify checklist matches manifest TC status | Manual verification required | Code review at lines 1219-1241 confirms: `isPassed` maps `status === 'passed'/'PASSED'` → `checked`; `isFailed` maps `status === 'failed'/'FAILED'` → `.status-failed` class. Logic is correct. |

## Issues Found

No issues found.

The implementation is complete and correct. Notable implementation details:

- **`parseTaskSections`** (lines 1012-1058): correctly splits YAML frontmatter using `---` fence regex, then walks body lines collecting content per `## Heading`. Handles missing sections gracefully (returns `null`/`[]`). Acceptance criteria lines with `- [x]` / `- [ ]` are preserved as raw strings for the renderer to parse.
- **`renderTasks`** (lines 1060-1124): BUCKET_ORDER defined, non-empty buckets rendered with `data-testid`, empty buckets skipped, "Other" catch-all for unknown statuses, empty-state guard for zero tasks. The `#task-detail` anchor is appended to the container for the inline expand pattern.
- **`renderTaskCard`** (lines 1126-1158): correct field set (pill, id, stage, title, meta line). Meta line renders `depends_on` with middle-dot separator and `TCs:` list, both guarded by `.length`. No forbidden fields (`file`, `assignee`, `iterations`). `cursor: pointer` applied via `.task-card { cursor: pointer }` CSS. `data-testid` present.
- **`openTaskDetail`** (lines 1160-1302): six-panel detail correctly ordered per design spec. Active card highlighting uses `classList.toggle`. `scrollIntoView({block:'nearest'})` called before async fetch. Error state shows colored error message. `parseTaskSections` is reused cleanly.
- **CSS** (lines 464-520): all new classes (`.task-bucket`, `.task-card`, `.task-card-top`, `.task-card-id`, `.task-card-stage`, `.task-card-meta`, `.status-dot`, `.task-detail-section`, `.depends-chain`, `.depends-node`, `.depends-arrow`, `.tc-checklist-row`, `.ac-list`) are defined in the `<style>` block annotated with `/* Tasks tab helpers (ADV009-T008) */`. No external CSS added.
- **`data-testid` hooks**: `task-bucket-{status}`, `task-bucket-other`, `task-card-{id}`, `task-detail`, `tc-row-{tcId}`, `task-show-details` — all present as specified in step 6 of the design.

One minor observation: the `test_card_shape` test checks for `tc-checklist` in the script, but the implemented class name is `tc-checklist-row` (not `tc-checklist`). The test passes because `tc-checklist` is a substring of `tc-checklist-row`. This is not a defect but is worth noting for test precision.

## Recommendations

The implementation is high quality. Optional future improvements:

1. The `test_card_shape` test's `tc-checklist` substring match is slightly loose — if TC testing is tightened in T012, consider asserting `tc-checklist-row` specifically.
2. TC-010 and TC-011 are skipped in CI without Playwright. T012 is designated to establish browser testing infrastructure — once that lands, these smoke tests will provide full coverage.
3. The depends-on chain appends an `→ (this)` terminal node with `border-color:var(--accent)` applied via inline style rather than a CSS class. This is functional but could be extracted to a `.depends-node-current` class to keep styling in the `<style>` block.
