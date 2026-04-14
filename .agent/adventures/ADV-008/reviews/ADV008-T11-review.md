---
task_id: ADV008-T11
adventure_id: ADV-008
status: PASSED
timestamp: 2026-04-14T15:30:10Z
build_result: PASS
test_result: PASS
---

# Review: ADV008-T11

## Summary
| Field | Value |
|-------|-------|
| Task | ADV008-T11 |
| Title | Operation primitives |
| Status | PASSED |
| Timestamp | 2026-04-14T15:30:10Z |

## Build Result
- Command: `python -c "import shape_grammar.tools.ops; print('import ok')"`
- Result: PASS
- Output: `import ok`

## Test Result
- Command: `pytest shape_grammar/tests/test_evaluator.py -q`
- Result: PASS
- Pass/Fail: 13 passed, 0 failed
- Output: `.............  13 passed in 0.06s`

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | All 8 op classes implemented | Yes | ExtrudeOp, SplitOp, CompOp, ScopeOp, IOp, TOp, ROp, SOp all present and import cleanly. OP_REGISTRY confirms 8 keys: `comp`, `extrude`, `i`, `r`, `s`, `scope`, `split`, `t`. |
| 2 | Each `apply` is deterministic under fixed seed | Yes | Verified programmatically: same SeededRng seed produces identical results for SplitOp; all 13 tests including `test_deterministic_roundtrip` and `test_rng_determinism` pass. |
| 3 | Operations registered in a central `OP_REGISTRY` dict for evaluator dispatch | Yes | `OP_REGISTRY: dict[str, type[Op]]` defined at module level with all 8 entries; `make_op()` factory dispatches through it and raises `KeyError` for unknown kinds. |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-05 | Python evaluator round-trip produces deterministic terminals under fixed seed | autotest | `pytest shape_grammar/tests/test_evaluator.py -q` | PASS | 13 passed in 0.05s |
| TC-19 | RNG determinism: `SeededRng(42).fork("a")` reproduces identical sequence across runs | autotest | `pytest shape_grammar/tests/test_evaluator.py -k rng_determinism -q` | PASS | 1 passed, 12 deselected in 0.03s |

## Issues Found

No issues found.

## Recommendations

The implementation is clean, well-structured, and matches the design spec precisely. A few optional quality observations:

- **CompOp component scopes share the parent transform** (no per-face position offset is computed). This is explicitly called out in the docstring ("callers may further resolve face centres via geometry helpers"), which is an appropriate deferral for a reference interpreter. The design doc does not require sub-scope positioning at this layer.
- **`_AXIS_IDX` class-level dataclass field in `SplitOp`** is declared but re-derived as a local dict inside `apply`. The field is harmless (excluded from `repr` and `compare`) but is unused dead code. Low priority.
- **`IOp.apply` returns `(TERMINAL, asset_path, label)`** where the first element is the sentinel, not a `Scope`. The doc-comment and the module docstring both clearly document this contract, so the evaluator can safely distinguish terminal results. Pattern is clear and intentional.
- The singleton pattern for `_TerminalMarker` is correct and safe for `is`-identity checks.
