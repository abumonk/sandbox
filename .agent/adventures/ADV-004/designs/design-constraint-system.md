# Constraint System — Design

## Overview
Implement constraint checking for evolved variants in `tools/evolution/constraint_checker.py`. This ensures evolved content meets safety requirements: size limits, semantic preservation, test suite passing, and caching compatibility.

## Target Files
- `ark/tools/evolution/constraint_checker.py` — Constraint validation for evolved variants

## Approach

### Constraint Types

1. **size_limit**: Evolved variant must not exceed original size by more than threshold (default: +20%).
   - `check_size_limit(original: str, evolved: str, threshold: float) -> ConstraintResult`
   - Measures by character count (consistent, language-agnostic).

2. **semantic_preservation**: Evolved variant must preserve the semantic intent of the original.
   - `check_semantic_preservation(original: str, evolved: str, judge_fn) -> ConstraintResult`
   - Uses a callback judge_fn that compares original vs evolved and returns a preservation score (0.0-1.0).
   - Threshold: 0.8 default (configurable).

3. **test_suite**: If the target is code (Tier 4), the evolved variant must pass all existing tests.
   - `check_test_suite(evolved_file: str, test_command: str) -> ConstraintResult`
   - Runs the test command and checks exit code. Returns pass/fail + stdout.
   - Note: This constraint requires shell access; in non-shell contexts, returns a deferred result.

4. **caching_compat**: For prompts (Tier 3), the evolved variant must maintain prompt caching compatibility.
   - `check_caching_compat(original: str, evolved: str, prefix_length: int) -> ConstraintResult`
   - Checks that the first `prefix_length` characters are unchanged (prefix caching).

### Key Types

```python
@dataclass
class ConstraintResult:
    constraint_kind: str
    passed: bool
    enforcement: str     # "block" or "warn"
    message: str
    details: dict        # constraint-specific data (e.g., size_ratio, preservation_score)

def check_all_constraints(
    original: str,
    evolved: str,
    constraints: list[dict],  # from constraint AST items
    judge_fn=None,
    test_command=None,
) -> list[ConstraintResult]:
    """Run all applicable constraints and return results."""

def should_block(results: list[ConstraintResult]) -> bool:
    """Return True if any constraint with enforcement='block' failed."""
```

### Integration with Optimizer
The optimizer calls `check_all_constraints()` after each mutation. Variants that trigger a `block` constraint are discarded from the population. Variants that trigger `warn` constraints are kept but flagged.

### Design Decisions
- Constraint checker is pure functions + callbacks (no side effects except test_suite which shells out)
- Size limit uses character count, not tokens (simpler, deterministic, no tokenizer dependency)
- Semantic preservation uses callback injection — same pattern as fitness.py judge
- Constraints are loaded from the `constraint` AST items in the .ark spec

## Dependencies
- design-dsl-surface (constraint AST items)
- design-evolution-schema (EnforcementLevel enum)

## Target Conditions
- TC-018: Size limit constraint correctly blocks variants exceeding threshold
- TC-019: Size limit constraint passes variants within threshold
- TC-020: Semantic preservation uses judge callback and returns score-based result
- TC-021: Caching compatibility checks prefix preservation correctly
- TC-022: should_block returns True only when a block-enforcement constraint fails
