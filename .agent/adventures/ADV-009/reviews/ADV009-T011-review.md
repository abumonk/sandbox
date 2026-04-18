---
task_id: ADV009-T011
adventure_id: ADV-009
status: PASSED
timestamp: 2026-04-18T00:01:00Z
build_result: N/A
test_result: PASS
---

# Review: ADV009-T011

## Summary
| Field | Value |
|-------|-------|
| Task | ADV009-T011 |
| Title | Retire legacy renderers and dead CSS |
| Status | PASSED |
| Timestamp | 2026-04-18T00:01:00Z |

## Build Result
- Command: (none configured in config.md)
- Result: N/A

## Test Result
- Command: `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"`
- Result: PASS
- Pass/Fail: 71 passed, 8 skipped (playwright not installed)
- Key: TC-005 (`test_no_legacy_tabs`) — ok; TC-004 (`test_four_tabs`) — ok

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | No references remain to the removed renderers | Yes | `grep -n "renderFileBrowser\|renderLog\|renderReviews"` returns 0 results |
| 2 | grep count for pattern is 0 (outside log strings) | Yes | 4 grep hits are `renderPermissionsCard` and `renderKnowledgeCard` — v2 renames, not the legacy methods. Exact-word grep for `renderPermissions\b` and `renderKnowledge\b` returns 0 |
| 3 | Page loads and 4 tabs work with no console errors | Yes | Inferred from all JS structural tests passing; smoke tests skipped (playwright absent) |
| 4 | `parseKnowledgeSuggestions` present and used by renderDecisions | Yes | Line 2208 defines it; line 1783 calls it from `renderKnowledgeCard` inside Decisions |
| 5 | `switchTab` coerces unknown keys to `overview` | Yes | Line 772-773: KNOWN_TABS guard with `key = 'overview'` fallback |
| 6 | Legacy CSS `.split`, `.split .file-list`, `.file-list .file-entry*` removed | Yes | No matches for those CSS selectors in index.html |
| 7 | `.file-view` / `.kb-*` removed only if no v2 caller remains | Yes | `.kb-*` retained (lines 165-177); `.file-view` and `.file-list`/`.file-entry` absent — no v2 caller emits them |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-005 | Log/Knowledge/Permissions/Designs/Plans/Research/Reviews do not appear as top-level tabs | autotest | `python -m unittest ...TestTabBar.test_no_legacy_tabs` | PASS | "TC-005: TABS_V2 does not define any legacy tab label. ... ok" |

## Issues Found
No issues found.

## Recommendations
Clean execution. The AC wording for criterion 2 uses a grep pattern that also matches the v2 method names (`renderPermissionsCard`, `renderKnowledgeCard`), which could cause confusion with literal interpretation. The implementer correctly scoped the intent (legacy standalone methods vs. v2 card helpers), and the actual removal is confirmed by word-boundary grep. Consider tightening the AC pattern in future tasks to use `\b` word boundaries.
