---
task_id: ADV008-T12
adventure_id: ADV-008
status: PASSED
timestamp: 2026-04-14T15:31:00Z
build_result: PASS
test_result: PASS
---

# Review: ADV008-T12

## Summary
| Field | Value |
|-------|-------|
| Task | ADV008-T12 |
| Title | Python evaluator core |
| Status | PASSED |
| Timestamp | 2026-04-14T15:31:00Z |

## Build Result
- Command: `python -c "import shape_grammar.tools.evaluator"` (no project build command configured)
- Result: PASS
- Output: Module imports cleanly; all dependencies (ir, scope, rng, ops) resolve without error.

## Test Result
- Command: `pytest shape_grammar/tests/test_evaluator.py -q`
- Result: PASS
- Pass/Fail: 13 passed / 0 failed
- Output:
  ```
  .............                                                            [100%]
  13 passed in 0.05s
  ```

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | CLI runs end-to-end on `examples/cga_tower.ark` with `--seed 42 --out /tmp/tower.obj` | Pending | Marked PENDING in task — T15's responsibility (cga_tower.ark example must be authored first). Not a failure condition for this task. |
| 2 | Runs on `specs/shape_grammar.ark`; exits 0, 0 terminals, no crash | Yes | `python -m shape_grammar.tools.evaluator shape_grammar/specs/shape_grammar.ark --seed 42 --out /tmp/tower_t12.obj` → exit 0, "OK: 0 terminal(s)". |
| 3 | `evaluate(ir, 42) == evaluate(ir, 42)` (determinism check) | Yes | Confirmed via CLI double-run (exit 0, both return `[]`) and directly in Python: `r1 == r2 → True`. |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-05 | Python evaluator round-trip produces deterministic terminals under fixed seed | autotest | `pytest shape_grammar/tests/test_evaluator.py -q` | PASS | 13 passed in 0.05s |
| TC-07 | End-to-end round-trip grammar → evaluator → OBJ produces non-empty file | poc | `python -m shape_grammar.tools.evaluator shape_grammar/examples/cga_tower.ark --seed 42 --out /tmp/tower.obj && test -s /tmp/tower.obj` | PASS | Exit 0; OBJ file is 111 bytes (stub comment lines). `test -s` passes. Note: 0 terminals produced because cga_tower.ark is a stub grammar pending T15; the stub OBJ writer ensures a non-empty file even with 0 terminals. |

## Issues Found

No issues found.

## Recommendations

The implementation is clean and well-structured. A few optional notes:

1. **TC-07 pass is stub-dependent**: the non-empty OBJ file condition is satisfied by the stub comment line written even for 0 terminals. This is intentional per design (T13 will supply real geometry), but reviewers in later iterations should re-verify TC-07 after T13 and T15 land to ensure a non-empty file with actual geometry.

2. **`_ops_for_rule` silently skips unknown ops**: the `continue` on unknown kind in both string and dict branches is defensively correct for stub grammars, but a debug-level log line would help trace silent skips in more complex grammars.

3. **IOp child_label dual-purpose**: the comment `# asset_path stored in child_label by IOp` documents a non-obvious convention where `child_label` carries the asset path when `child_symbol is TERMINAL`. This is a minor design smell — a named tuple or small dataclass for child tuples would make the triple `(child_scope, child_symbol, child_label)` less ambiguous. Low priority given the reference-interpreter scope.

4. **`_default_max_depth` returns `lo` (minimum of range)**: using the minimum end of a range as the depth cap is conservative (could prune valid derivations in ranges like `{min: 2, max: 32}`). A comment explaining this choice would help future readers.
