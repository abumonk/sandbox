---
task_id: ADV009-T014
adventure_id: ADV-009
status: PASSED
timestamp: 2026-04-18T00:00:05Z
build_result: N/A
test_result: N/A
---

# Review: ADV009-T014

## Summary
| Field | Value |
|-------|-------|
| Task | ADV009-T014 |
| Title | Update README for v2 |
| Status | PASSED |
| Timestamp | 2026-04-18T00:00:05Z |

## Build Result
- Command: *(empty — no build_command configured in config.md)*
- Result: N/A
- Output: No build step applicable for a documentation-only task.

## Test Result
- Command: *(empty — no test_command configured in config.md)*
- Result: N/A
- Output: No automated test suite applies to this documentation-only task. TC-038 is proof_method: manual (see Target Conditions section).

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | README mentions exactly the four v2 tabs (Overview, Tasks, Documents, Decisions) and does not list the nine v1 tabs in the "What it does" section. | Yes | Four-row table present at lines 32–35. No v1 tabs appear as table rows. `grep -E "(Overview|Tasks|Documents|Decisions)"` returns 7 hits; v1 tab names absent from the "What it does" section. |
| 2 | The endpoints table lists `GET /api/adventures/{id}/documents`. | Yes | Row present at line 52: `| GET | `/api/adventures/{id}/documents` | — | Unified list of designs/plans/research/reviews with lightweight metadata |` |
| 3 | The endpoints table (or a new note) mentions that `GET /api/adventures/{id}` response now includes a `summary` block (tc counts, tasks_by_status, next_action). | Yes | Lines 60–63 contain the paragraph: "`GET /api/adventures/{id}` also returns a derived `summary` block with `tc_total`, `tc_passed`, `tc_failed`, `tc_pending`, `tasks_by_status`, and a `next_action` hint (`kind`, `label`, `state_hint`). These values are computed on every request; nothing new is persisted to disk." All required fields are named. |
| 4 | Run command still "`python .agent/adventure-console/server.py`". | Yes | Line 10 contains the exact run command inside the `## Run` section code block. |
| 5 | Sections "Run", "How the backend works" (header), "Safety", and "Files" remain present and substantively unchanged (wording may be refreshed but structure preserved). | Yes | All four section headers confirmed at lines 6, 42, 79, 87 respectively. Safety bullets and Files tree unchanged verbatim. |
| 6 | No stale references to v1-only tab names ("Designs", "Plans", "Permissions", "Reviews", "Knowledge", "Research", "Log") as top-level tabs. | Yes | `grep -E "^\| (Designs|Plans|Permissions|Reviews|Knowledge|Research|Log)\b"` returned no results. The word "reviews" appears only as a document category inside the Documents tab description and the Files tree, which is permitted. |
| 7 | Knowledge-extraction section is updated to note that knowledge curation now lives inside the **Decisions** tab (not a standalone Knowledge tab). | Yes | Line 67: "The **Decisions** tab parses the `## 6. Knowledge Extraction Suggestions`..." — correctly references Decisions tab. The `reviews/knowledge-selection.json` payload and extractor-agent disclaimer are preserved verbatim. |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-038 | README updated to reflect the four v2 tabs and new /documents endpoint | manual | `diff README.md; grep for v2 tab names` | PASS | Four tabs present in "What it does" table (lines 32–35). `/api/adventures/{id}/documents` listed in endpoints table (line 52). `summary` block paragraph present (lines 60–63). No v1 tab names as tab rows. Run command unchanged. Sections Run/Safety/Files intact. Manual verification criteria all satisfied. |

## Issues Found

No issues found.

## Recommendations

The implementation is clean and exactly on-scope. A few minor observations (not defects):

1. The sidebar description at line 24 reads "those are one click away in the Overview tab" which is slightly different from the design doc's phrasing "those live one click away in Overview". Both are acceptable; the intent is equivalent.
2. The "Main pane — tabs per adventure:" label (line 28) retains that phrasing — the design doc did not specify changing this label, so it is correct as-is.
3. The `summary` block paragraph (lines 60–63) is placed after the endpoints table and reads as prose, which matches the design spec well. All six required fields are documented (`tc_total`, `tc_passed`, `tc_failed`, `tc_pending`, `tasks_by_status`, `next_action`).
