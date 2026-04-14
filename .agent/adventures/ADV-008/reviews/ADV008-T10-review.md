---
task_id: ADV008-T10
adventure_id: ADV-008
status: PASSED
timestamp: 2026-04-14T15:30:30Z
build_result: N/A
test_result: PASS
---

# Review: ADV008-T10

## Summary
| Field | Value |
|-------|-------|
| Task | ADV008-T10 |
| Title | Scope stack + seeded RNG |
| Status | PASSED |
| Timestamp | 2026-04-14T15:30:30Z |

## Build Result
- Command: N/A (no build command configured in `.agent/config.md`)
- Result: N/A
- Output: Pure Python modules — no compilation step required.

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
| 1 | `Scope.identity()` returns identity transform | Yes | Verified: translation=(0,0,0), rotation=(0,0,0), scale=(1,1,1), size=(0,0,0), attrs=() |
| 2 | `ScopeStack.push(scope).top() == scope` | Yes | Verified: push returns self (fluent), top() returns the same Scope object |
| 3 | `SeededRng(42).fork("a")` and `SeededRng(42).fork("a")` produce identical first 100 outputs | Yes | Verified manually: 100-element float sequences are identical across two independently constructed forks |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-05 | Python evaluator round-trip produces deterministic terminals under fixed seed | autotest | `pytest shape_grammar/tests/test_evaluator.py -q` | PASS | 13 passed in 0.05s |
| TC-19 | RNG determinism: `SeededRng(42).fork("a")` reproduces identical sequence across runs | autotest | `pytest shape_grammar/tests/test_evaluator.py -k rng_determinism -q` | PASS | 1 passed, 12 deselected in 0.03s |

## Issues Found

No issues found.

## Recommendations

The implementation is high quality. Two observations worth noting as positive decisions:

1. **SHA-256 over `hash()`**: The design document (`design-evaluator.md`) sketches `fork()` using Python's built-in `hash((seed, label))`, which is non-deterministic across processes due to `PYTHONHASHSEED`. The implementation correctly deviates by using `hashlib.sha256` — this is the right call and the module docstring explicitly documents the rationale. TC-19 cross-run determinism would have been impossible with the design's sketched approach.

2. **Frozen dataclass + sorted tuple attrs**: `Scope` uses `frozen=True` and stores `attrs` as a sorted tuple of pairs rather than a `dict`. This makes scopes immutable, hashable, and safe to use as dict keys or in sets — a stronger guarantee than the design requires, at negligible cost.

3. **`ScopeStack.get()` walks all frames**: The `get(name)` method on `ScopeStack` correctly walks top-to-bottom through all frames, implementing dynamic scope chain resolution. The `Scope.get()` method on a single scope is separate and only looks at that scope's own attrs — the naming is consistent with the design's layered model.

Optional (not required for pass): The `_MASK_32` applied to `parent_seed` in `_derive_subseed` means seeds larger than 32 bits are silently truncated. This is acceptable for the current use case but could be documented as a known limitation if large seeds become relevant.
