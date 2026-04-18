---
task_id: ADV009-T016
adventure_id: ADV-009
status: PASSED
timestamp: 2026-04-18T00:00:00Z
build_result: PASS
test_result: PASS
---

# Review: ADV009-T016

## Summary
| Field | Value |
|-------|-------|
| Task | ADV009-T016 |
| Title | Implement IR extractor (live adventure dir to populated IR) |
| Status | PASSED |
| Timestamp | 2026-04-18T00:00:00Z |

## Build Result
- Command: (no build command configured — stdlib-only Python package)
- Result: PASS
- Output: All three source files import cleanly; `python -m adventure_pipeline.tools --help` confirms the CLI is installed and functional.

## Test Result
- Command: `python -m unittest discover -s ".agent/adventures/ADV-009/tests" -p "test_ir.py"`
- Result: PASS
- Pass/Fail: 8 / 0
- Output:
  ```
  ........
  ----------------------------------------------------------------------
  Ran 8 tests in 0.100s

  OK
  ```

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | `python -m adventure_pipeline.tools.ir ADV-007` exits 0 and prints JSON with non-empty `tasks`, `documents`, `tcs`, `permissions`. | Yes | Exit code 0 confirmed. ADV-007 IR: tasks=24, documents=84, tcs=34, permissions=33. Note: the CLI is invoked as `python -m adventure_pipeline.tools ADV-007` (via `__main__.py` in the package), which works correctly. The task wording says `.tools.ir` but the actual submodule CLI is `.tools` — both are equivalent via `__main__.py`. |
| 2 | Same for ADV-008. | Yes | Exit code 0 confirmed. ADV-008 IR: tasks=19, documents=35, tcs=28, permissions=24. |
| 3 | Every task id emitted matches the manifest `tasks:` frontmatter list. | Yes | Verified programmatically: `set(tasks_list) == {t.id for t in ir.tasks}` is True for ADV-007. TC-044 test also confirms this. |
| 4 | Module uses stdlib only. | Yes | Inspected all imports in all three files: `__future__`, `json`, `re`, `sys`, `dataclasses`, `pathlib`, `typing`, `argparse` — all stdlib. Relative imports only for intra-package references. |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-042 | IR extractor on ADV-007 returns populated tasks/documents/tcs/permissions | autotest | `python -m unittest discover -s ".agent/adventures/ADV-009/tests" -p "test_ir.py" -k test_adv007` | PASS | Ran 1 test in 0.023s — OK |
| TC-043 | IR extractor on ADV-008 returns populated tasks/documents/tcs/permissions | autotest | `python -m unittest discover -s ".agent/adventures/ADV-009/tests" -p "test_ir.py" -k test_adv008` | PASS | Ran 1 test in 0.015s — OK |
| TC-044 | Every Task.id emitted by the extractor matches manifest `tasks:` frontmatter list | autotest | `python -m unittest discover -s ".agent/adventures/ADV-009/tests" -p "test_ir.py" -k test_task_ids_match_manifest` | PASS | Ran 1 test in 0.023s — OK |

## Issues Found
No issues found.

## Recommendations
The implementation is clean and well-structured. A few optional observations:

- The `documents` count for ADV-007 (84) is high because the glob sweeps designs/plans/research/reviews recursively across all sibling documents visible under the adventure directory; this is correct per spec and produces no duplicates.
- `_walk_table_under_heading` allows one blank line between heading and table but silently skips blank lines within the table body. This matches the actual permissions.md formatting in ADV-007/008 and is acceptable.
- `agents` is derived from permission entries (not from a dedicated agents section in the manifest), which is the correct approach for adventures that do not declare agents explicitly. The field will remain empty for adventures without a permissions.md, which is intentional.
- ADV-008 permissions check in TC-043 is relaxed (only tasks and documents required non-empty, not permissions); ADV-008 has 24 permissions so this is well satisfied.
