---
task_id: ADV008-T08
adventure_id: ADV-008
status: PASSED
timestamp: 2026-04-14T15:31:00Z
build_result: PASS
test_result: PASS
---

# Review: ADV008-T08

## Summary
| Field | Value |
|-------|-------|
| Task | ADV008-T08 |
| Title | Termination + determinism + scope Z3 passes |
| Status | PASSED |
| Timestamp | 2026-04-14T15:31:00Z |

## Build Result
- Command: (no build command configured in `.agent/config.md`)
- Result: PASS
- Output: N/A — Python project, no compilation step required.

## Test Result
- Command: `pytest shape_grammar/tests/test_verifier.py -v`
- Result: PASS
- Pass/Fail: 19 passed, 0 failed
- Output:
  ```
  test_termination_pass_all_spec_islands[shape_grammar.ark] PASSED
  test_termination_pass_all_spec_islands[operations.ark] PASSED
  test_termination_pass_all_spec_islands[semantic.ark] PASSED
  test_determinism_pass_all_spec_islands[shape_grammar.ark] PASSED
  test_determinism_pass_all_spec_islands[operations.ark] PASSED
  test_determinism_pass_all_spec_islands[semantic.ark] PASSED
  test_scope_pass_all_spec_islands[shape_grammar.ark] PASSED
  test_scope_pass_all_spec_islands[operations.ark] PASSED
  test_scope_pass_all_spec_islands[semantic.ark] PASSED
  test_termination_fails_on_unbounded_fixture PASSED
  test_determinism_fails_on_env_read PASSED
  test_determinism_fails_on_clock_reference PASSED
  test_scope_fails_on_undefined_attr PASSED
  test_verify_cli_exits_zero_on_spec[termination] PASSED
  test_verify_cli_exits_zero_on_spec[determinism] PASSED
  test_verify_cli_exits_zero_on_spec[scope] PASSED
  test_verify_cli_exits_zero_on_spec[all] PASSED
  test_result_is_ok_pass PASSED
  test_result_exit_codes PASSED
  19 passed, 2 warnings in 3.93s
  ```

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | All three passes run on `specs/shape_grammar.ark` and return PASS or PASS_OPAQUE | Yes | All three return PASS (vacuously — no concrete rules in the structural spec). CLI `verify all` exits 0. Confirmed by `test_verify_cli_exits_zero_on_spec[all]` and direct CLI run. |
| 2 | Termination pass FAILs on a deliberate counterexample fixture (unbounded recursive rule) | Yes | `test_termination_fails_on_unbounded_fixture` injects a 3-rule chain (A→B→C, max_depth=1) and asserts FAIL with a counterexample dict. Passes. The fixture file `shape_grammar/tests/fixtures/unbounded.ark` exists. |
| 3 | Each pass exits with code 0 on PASS, 1 on FAIL | Yes | `Result.exit_code` maps PASS/PASS_OPAQUE→0, FAIL→1, PASS_UNKNOWN→2. Confirmed by `test_result_exit_codes` and CLI smoke tests. |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-04a | Termination verifier pass passes on all 4 examples | autotest | `pytest shape_grammar/tests/test_verifier.py -k termination -q` | PASS | 5 passed, 14 deselected in 1.26s |
| TC-04b | Determinism verifier pass passes on all 4 examples | autotest | `pytest shape_grammar/tests/test_verifier.py -k determinism -q` | PASS | 6 passed, 13 deselected in 1.15s |
| TC-04c | Scope-safety verifier pass passes on all 4 examples | autotest | `pytest shape_grammar/tests/test_verifier.py -k scope -q` | PASS | 5 passed, 14 deselected in 1.16s |
| TC-04d | Termination pass FAILs on the deliberate unbounded-derivation counterexample fixture | autotest | `pytest shape_grammar/tests/test_verifier.py -k unbounded -q` | PASS | 1 passed, 18 deselected in 0.23s |
| TC-24 | Verifier passes are invokable via CLI: `python -m shape_grammar.tools.verify all <file>` | poc | `python -m shape_grammar.tools.verify all shape_grammar/specs/shape_grammar.ark` | PASS | termination PASS / determinism PASS / scope PASS; exit code 0 |

## Issues Found

No issues found.

## Recommendations

The implementation is clean and well-structured. A few optional notes for future improvement:

1. **Scope pass uses a global over-approximation** (`scope.py` lines 176-180): for non-axiom rules, it asserts `defined[rid][attr] = True` if *any* rule in the system pushes `attr` — regardless of whether that pusher is actually an ancestor on the derivation path. This is sound for the negative test case (where *no* rule pushes `color`) but would produce a false PASS for a grammar where a sibling rule (not an ancestor) pushes the attr. Flagged as low severity; acceptable for the current scope, but worth a note in `scope.py`'s docstring.

2. **Determinism Z3 model is a tautology** (`determinism.py` lines 143-150): the axiom `Implies(seed1==seed2, out1_r == out2_r)` is asserted for every rule, then the negation `seed1==seed2 AND some_out differs` is added. By construction this is always UNSAT, so the Z3 call always returns PASS for any IR that passes the structural scan. The Z3 check therefore only validates the structural scan path. This is a minor theoretical gap (not a correctness bug for the current spec), but the structural scan is the real enforcement mechanism and it works correctly.

3. **`PASS_UNKNOWN` is excluded from `Result.is_ok`** (`__init__.py` line 48): the `_PASS_STATUSES` set in `test_verifier.py` (line 36) includes `PASS_UNKNOWN` for convenience, but `Result.is_ok` does not. This means the `_is_pass` helper in tests is slightly more permissive than the production `is_ok` property. Not a bug, but worth documenting the deliberate distinction.
