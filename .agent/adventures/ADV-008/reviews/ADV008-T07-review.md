---
task_id: ADV008-T07
adventure_id: ADV-008
status: PASSED
timestamp: 2026-04-14T14:30:45Z
build_result: PASS
test_result: PASS
---

# Review: ADV008-T07

## Summary
| Field | Value |
|-------|-------|
| Task | ADV008-T07 |
| Title | IR extraction module |
| Status | PASSED |
| Timestamp | 2026-04-14T14:30:45Z |

## Build Result
- Command: (none configured in config.md)
- Result: PASS
- Output: No build step required for pure-Python module.

## Test Result
- Command: `pytest shape_grammar/tests/test_ir.py -q`
- Result: PASS
- Pass/Fail: 19 passed, 0 failed
- Output:
  ```
  ...................                                                      [100%]
  19 passed, 2 warnings in 3.20s
  ```
  (Warnings are Lark sre_parse deprecation notices from Python 3.12 — not from this task's code.)

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | `python -m shape_grammar.tools.ir shape_grammar/specs/shape_grammar.ark` prints a populated IR JSON | Yes | Exit code 0; JSON output contains island_name="ShapeGrammar", max_depth={min:1,max:100}, seed={min:0,max:2147483647}, 7 entities |
| 2 | All error paths from `schemas/processes.md` raise `IRError` with the documented message prefix | Yes | "no ShapeGrammar island found" via `require_island`; "rule {id} has no operations" via `validate_rules`; "max_depth must be positive Int" via `require_populated` — all confirmed with exact prefix matching |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-03 | IR extraction returns populated ShapeGrammarIR from every spec island | autotest | `pytest shape_grammar/tests/test_ir.py -q` | PASS | 19 passed in 3.20s |
| TC-25 | `ir.py` is invokable via CLI and emits JSON-shaped IR | poc | `python -m shape_grammar.tools.ir shape_grammar/specs/shape_grammar.ark` | PASS | Exit 0; JSON with island_name, max_depth, seed, entities printed to stdout |

## Issues Found

No issues found.

## Recommendations

The implementation is clean and well-structured. A few optional observations:

- The `require_populated` function doubles as a `require_island` guard (when entities are empty), which is slightly redundant with the explicit `require_island` helper. This is acceptable — the two functions serve distinct call sites (CLI vs. consumers), and the overlap is documented in the docstrings.
- `parse_ark` silently swallows all `IRError` from the library path and falls through to subprocess. This means a real parse error (e.g. malformed Ark syntax) could be reported with subprocess output rather than the cleaner library error message. Low risk for current usage but worth noting if parse error UX matters downstream.
- The `IRRule.operations` field stores `list[str]` (operation identifiers) rather than typed `IROperation` objects. This is explicitly noted as a placeholder for T15 example grammars. The design document acknowledges this; no action needed.
- 19 tests across 7 test functions (some parametrized) provide solid coverage of both happy-path extraction and all three documented error paths.
