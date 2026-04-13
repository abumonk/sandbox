# Plan: Standard Library

## Designs Covered
- 03_stdlib_catalogue

## Tasks

### Port numeric expressions to stdlib
- **ID**: ADV001-T007
- **Description**: Create `R:/Sandbox/ark/dsl/stdlib/expression.ark` with the v1 numeric
  expressions from design 03 (absolute, add, subtract, multiply, divide, ceiling, floor,
  round, power, clamp, negate). Each entry declares `in`, `out`, and `chain` referencing
  target primitives.
- **Files**:
  - `R:/Sandbox/ark/dsl/stdlib/expression.ark` (NEW — numeric section)
- **Acceptance Criteria**:
  - `python ark.py parse dsl/stdlib/expression.ark` succeeds
  - At least 11 numeric expressions present
- **Target Conditions**: TC-009, TC-010
- **Depends On**: [ADV001-T006]
- **Evaluation**:
  - Access requirements: Write on expression.ark, Bash for ark.py parse
  - Skill set: Ark DSL authoring
  - Estimated duration: 15min
  - Estimated tokens: 20000

### Port text expressions to stdlib
- **ID**: ADV001-T008
- **Description**: Append v1 text expressions (text-to-lower, text-to-upper, text-trim,
  text-length, text-pad-right, text-pad-left, text-remove-chars, text-substring,
  text-replace) to `expression.ark`.
- **Files**:
  - `R:/Sandbox/ark/dsl/stdlib/expression.ark`
- **Acceptance Criteria**:
  - File parses cleanly
  - At least 9 text expressions present
- **Target Conditions**: TC-009, TC-011
- **Depends On**: [ADV001-T007]
- **Evaluation**:
  - Access requirements: Edit on expression.ark, Bash for ark.py parse
  - Skill set: Ark DSL authoring
  - Estimated duration: 10min
  - Estimated tokens: 15000

### Port null-handling expressions to stdlib
- **ID**: ADV001-T009
- **Description**: Append `null-to-zero`, `null-to-value`, `neutral` to `expression.ark`.
- **Files**:
  - `R:/Sandbox/ark/dsl/stdlib/expression.ark`
- **Acceptance Criteria**:
  - File parses cleanly; 3 new entries present
- **Target Conditions**: TC-009
- **Depends On**: [ADV001-T008]
- **Evaluation**:
  - Access requirements: Edit on expression.ark
  - Skill set: Ark DSL
  - Estimated duration: 5min
  - Estimated tokens: 8000

### Port predicates to stdlib
- **ID**: ADV001-T010
- **Description**: Create `R:/Sandbox/ark/dsl/stdlib/predicate.ark` with v1 predicates
  (is-empty, is-null, starts-with, ends-with, contains, matches-regex, is-within,
  is-equal-to, is-greater-than, is-less-than).
- **Files**:
  - `R:/Sandbox/ark/dsl/stdlib/predicate.ark` (NEW)
- **Acceptance Criteria**:
  - `python ark.py parse dsl/stdlib/predicate.ark` succeeds
  - At least 10 predicates present
- **Target Conditions**: TC-009, TC-012
- **Depends On**: [ADV001-T006]
- **Evaluation**:
  - Access requirements: Write on predicate.ark, Bash
  - Skill set: Ark DSL
  - Estimated duration: 15min
  - Estimated tokens: 20000

### Expression primitive → target map
- **ID**: ADV001-T011
- **Description**: Create `R:/Sandbox/ark/tools/codegen/expression_primitives.py` with the
  `EXPR_PRIMITIVES` dict mapping each primitive (`abs`, `str-lower`, `str-len`, `pow`, etc.)
  to Rust method/function syntax. Entry shape: `{name: {"rust": "...", "kind": "unary|binary|method|fn", "arity": N}}`.
  Covers every primitive referenced in the v1 stdlib.
- **Files**:
  - `R:/Sandbox/ark/tools/codegen/expression_primitives.py` (NEW)
- **Acceptance Criteria**:
  - Every stdlib expression's chain-referenced primitive is present in the map
  - No duplicate keys
  - `python -c "from expression_primitives import EXPR_PRIMITIVES; print(len(EXPR_PRIMITIVES))"` returns >= 25
- **Target Conditions**: TC-010, TC-011
- **Depends On**: [ADV001-T009, ADV001-T010]
- **Evaluation**:
  - Access requirements: Write on expression_primitives.py, Bash
  - Skill set: Python, Rust primitive knowledge
  - Estimated duration: 20min
  - Estimated tokens: 25000
