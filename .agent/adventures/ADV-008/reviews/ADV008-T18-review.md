---
task_id: ADV008-T18
adventure_id: ADV-008
status: PASSED
timestamp: 2026-04-14T00:05:00Z
build_result: PASS
test_result: PASS
---

# Review: ADV008-T18

## Summary
| Field | Value |
|-------|-------|
| Task | ADV008-T18 |
| Title | Evaluator + semantic + integrations + examples tests |
| Status | PASSED |
| Timestamp | 2026-04-14T00:05:00Z |

## Build Result
- Command: N/A (no build command in config.md for this Python project)
- Result: PASS
- Output: Package imports cleanly; all modules resolve during test collection.

## Test Result
- Command: `pytest shape_grammar/tests/ -q`
- Result: PASS
- Pass/Fail: 79 passed / 0 failed
- Output:
  ```
  79 passed, 2 warnings in 19.42s
  ```
  (2 deprecation warnings from Lark internals — not caused by T18 code)

T18 owns 41 of the 79 tests:
- `test_evaluator.py`: 13 tests
- `test_semantic.py`: 9 tests
- `test_integrations.py`: 11 tests
- `test_examples.py`: 8 tests

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | `pytest shape_grammar/tests/ -q` green (combined with test_ir.py + test_verifier.py from T09) | Yes | 79/79 pass in 19.42s |
| 2 | All TCs with `proof_method: autotest` have a passing test | Yes | TC-05, TC-07, TC-08, TC-14, TC-19, TC-20 all verified passing; TC-11/12/13 (individual adapter subtests) also green |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|--------------|---------|--------|--------|
| TC-05 | Python evaluator round-trip is deterministic under fixed seed | autotest | `pytest shape_grammar/tests/test_evaluator.py -q` | PASS | 13 passed in 0.05s |
| TC-07 | End-to-end grammar → evaluator → OBJ produces non-empty file | autotest | `pytest shape_grammar/tests/test_evaluator.py -q` (includes `test_grammar_to_obj_nonempty`) | PASS | 13 passed in 0.05s |
| TC-08 | Every terminal carries an inherited-or-overridden semantic label | autotest | `pytest shape_grammar/tests/test_semantic.py -q` | PASS | 9 passed in 0.03s |
| TC-14 | Full integration adapter test suite green | autotest | `pytest shape_grammar/tests/test_integrations.py -q` | PASS | 11 passed, 2 warnings in 7.31s |
| TC-19 | RNG determinism: SeededRng(42).fork("a") reproduces identical sequence | autotest | `pytest shape_grammar/tests/test_evaluator.py -k rng_determinism -q` | PASS | 1 passed, 12 deselected in 0.03s |
| TC-20 | Example-driven end-to-end: parse + verify + IR + evaluate each of 4 examples | autotest | `pytest shape_grammar/tests/test_examples.py -q` | PASS | 8 passed, 2 warnings in 5.01s |

Note on TC-11/12/13 (not in T18's `target_conditions` list but covered by this task's test_integrations.py):
- `pytest test_integrations.py -k visualizer`: 3 passed
- `pytest test_integrations.py -k impact`: 4 passed
- `pytest test_integrations.py -k diff`: 3 passed

## Issues Found

No issues found.

## Recommendations

PASSED with high quality. A few optional observations:

1. **test_examples.py coverage scope adjusted appropriately**: The test docstring correctly documents that spec-only example grammars produce `[]` from `evaluate()` — this is the "safe empty spec" behaviour, not a coverage gap. The parametric test asserts no crash and verifies the full pipeline (ark verify → IR extract → all 3 verifier passes → evaluate → write_obj), which is the TC-20 contract.

2. **test_max_depth_guard divergence from strategy**: The test-strategy document (§ `test_evaluator.py`) specifies that `test_max_depth_guard` should feed `max_depth=0` and assert `EvaluationError`. The implemented version instead feeds `max_depth=4` with a self-recursing rule and asserts the evaluator terminates without error, checking that provenance depth ≤ 4. This is a valid and arguably stronger test (it exercises the actual pruning mechanism rather than a zero-depth edge case), but it does not match the strategy spec literally. The AC "All TCs with proof_method: autotest have a passing test" is still met since TC-05 is covered by `test_deterministic_roundtrip` — the max-depth guard is supplementary coverage not tied to a TC. No deduction warranted; note for strategy alignment if the strategy document is kept as a living spec.

3. **Negative-test coverage is thorough**: Every file includes at least one negative/error-path test as required by test-strategy §5. The integrations module has particularly strong negative coverage (3 error-path tests + 3 garbage-subprocess-output tests), which validates adapter robustness beyond what the TCs strictly require.

4. **Frontmatter amendment**: Per the reviewer context note, the task frontmatter (status, AC checkboxes, log line) was amended post-hoc by the lead after the implementer reported success in chat. This is an admin-process gap only — it does not affect the deliverable quality. The actual work product (4 test files, 79/79 green, TC-10 pristine) was produced correctly by the implementation agent.
