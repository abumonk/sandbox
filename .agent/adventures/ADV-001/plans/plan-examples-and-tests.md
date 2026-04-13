# Plan: Example Specs & Test Suite

## Designs Covered
- 06_examples_and_tests

## Tasks

### Example spec: specs/test_expression.ark
- **ID**: ADV001-T020
- **Description**: Create `R:/Sandbox/ark/specs/test_expression.ark` matching the listing in
  design 06 — declares `normalize_name` expression, `is_valid_name` predicate, uses both in a
  `class Player`, and has a `verify` block. This file is the smoke spec for end-to-end.
- **Files**:
  - `R:/Sandbox/ark/specs/test_expression.ark` (NEW)
- **Acceptance Criteria**:
  - `python ark.py parse specs/test_expression.ark` succeeds
  - `python ark.py verify specs/test_expression.ark` runs without Z3 errors
  - `python ark.py codegen specs/test_expression.ark --target rust` produces a .rs file
- **Target Conditions**: TC-024
- **Depends On**: [ADV001-T011, ADV001-T015, ADV001-T019]
- **Evaluation**:
  - Access requirements: Write on test_expression.ark, Bash
  - Skill set: Ark DSL authoring
  - Estimated duration: 10min
  - Estimated tokens: 15000

### Example spec: specs/examples/expressif_examples.ark
- **ID**: ADV001-T021
- **Description**: Create `R:/Sandbox/ark/specs/examples/expressif_examples.ark` porting the
  three headline examples from Expressif README (text-to-lower |> pad-right, starts-with AND
  ends-with, numeric is-within). Inline-documented with comments tying each example to the
  original Expressif snippet.
- **Files**:
  - `R:/Sandbox/ark/specs/examples/expressif_examples.ark` (NEW)
- **Acceptance Criteria**:
  - `python ark.py parse specs/examples/expressif_examples.ark` succeeds
- **Target Conditions**: TC-027
- **Depends On**: [ADV001-T020]
- **Evaluation**:
  - Access requirements: Write, Bash
  - Skill set: Ark DSL
  - Estimated duration: 10min
  - Estimated tokens: 12000

### Pytest: parser pipe tests
- **ID**: ADV001-T022
- **Description**: Create `R:/Sandbox/ark/tests/test_parser_pipe.py` with tests from design
  06 (bare pipe, left-associativity, extra args, precedence mix, kebab-case inside/outside
  stages, nested refs, param ref tagging).
- **Files**:
  - `R:/Sandbox/ark/tests/test_parser_pipe.py` (NEW)
- **Acceptance Criteria**:
  - `pytest tests/test_parser_pipe.py -q` all pass
  - At least 10 test cases
- **Target Conditions**: TC-003, TC-004, TC-006, TC-025
- **Depends On**: [ADV001-T006]
- **Evaluation**:
  - Access requirements: Write, Bash
  - Skill set: pytest, Ark AST
  - Estimated duration: 20min
  - Estimated tokens: 30000

### Pytest: parser expression/predicate item tests
- **ID**: ADV001-T023
- **Description**: Create `R:/Sandbox/ark/tests/test_parser_expression_items.py` asserting
  expression and predicate items parse, error on missing clauses, and populate
  `expression_index` / `predicate_index` correctly.
- **Files**:
  - `R:/Sandbox/ark/tests/test_parser_expression_items.py` (NEW)
- **Acceptance Criteria**:
  - `pytest tests/test_parser_expression_items.py -q` all pass
  - At least 6 test cases
- **Target Conditions**: TC-001, TC-002, TC-007, TC-008, TC-025
- **Depends On**: [ADV001-T006]
- **Evaluation**:
  - Access requirements: Write, Bash
  - Skill set: pytest
  - Estimated duration: 15min
  - Estimated tokens: 22000

### Pytest: stdlib expression tests
- **ID**: ADV001-T024
- **Description**: Create `R:/Sandbox/ark/tests/test_stdlib_expression.py` — asserts `import
  stdlib.expression` resolves, every declared expression has a matching `EXPR_PRIMITIVES`
  entry, no two expressions mangle to the same Rust identifier.
- **Files**:
  - `R:/Sandbox/ark/tests/test_stdlib_expression.py` (NEW)
- **Acceptance Criteria**:
  - `pytest tests/test_stdlib_expression.py -q` all pass
- **Target Conditions**: TC-009, TC-010, TC-011, TC-012, TC-025
- **Depends On**: [ADV001-T011]
- **Evaluation**:
  - Access requirements: Write, Bash
  - Skill set: pytest
  - Estimated duration: 12min
  - Estimated tokens: 18000

### Pytest: verify expression tests
- **ID**: ADV001-T025
- **Description**: Create `R:/Sandbox/ark/tests/test_verify_expression.py` with tests for
  pipe translation, expression inlining, unknown-stage error, opaque primitive reporting.
- **Files**:
  - `R:/Sandbox/ark/tests/test_verify_expression.py` (NEW)
- **Acceptance Criteria**:
  - `pytest tests/test_verify_expression.py -q` all pass
  - At least 5 test cases including opaque primitive
- **Target Conditions**: TC-013, TC-015, TC-016, TC-017, TC-025
- **Depends On**: [ADV001-T015]
- **Evaluation**:
  - Access requirements: Write, Bash
  - Skill set: pytest, Z3
  - Estimated duration: 20min
  - Estimated tokens: 30000

### Pytest: verify predicate tests
- **ID**: ADV001-T026
- **Description**: Create `R:/Sandbox/ark/tests/test_verify_predicate.py` with satisfiability
  and tautology checks.
- **Files**:
  - `R:/Sandbox/ark/tests/test_verify_predicate.py` (NEW)
- **Acceptance Criteria**:
  - `pytest tests/test_verify_predicate.py -q` all pass
  - At least 3 test cases
- **Target Conditions**: TC-014, TC-025
- **Depends On**: [ADV001-T015]
- **Evaluation**:
  - Access requirements: Write, Bash
  - Skill set: pytest, Z3
  - Estimated duration: 15min
  - Estimated tokens: 22000

### Pytest: codegen expression tests
- **ID**: ADV001-T027
- **Description**: Create `R:/Sandbox/ark/tests/test_codegen_expression.py` asserting each
  v1 numeric / text expression produces expected Rust, predicate produces `-> bool`,
  inline pipes in process bodies codegen correctly, C++/Proto stubs raise with expected msg.
- **Files**:
  - `R:/Sandbox/ark/tests/test_codegen_expression.py` (NEW)
- **Acceptance Criteria**:
  - `pytest tests/test_codegen_expression.py -q` all pass
- **Target Conditions**: TC-018, TC-019, TC-020, TC-021, TC-022, TC-023, TC-025
- **Depends On**: [ADV001-T019]
- **Evaluation**:
  - Access requirements: Write, Bash
  - Skill set: pytest, Rust snippet assertions
  - Estimated duration: 25min
  - Estimated tokens: 40000

### Pytest: end-to-end pipeline test
- **ID**: ADV001-T028
- **Description**: Create `R:/Sandbox/ark/tests/test_pipeline_expression.py` invoking
  `python ark.py pipeline specs/test_expression.ark --target rust` as a subprocess and
  asserting exit code 0 + presence of `pub fn normalize_name`, `pub fn is_valid_name`,
  and `struct Player` in the generated output.
- **Files**:
  - `R:/Sandbox/ark/tests/test_pipeline_expression.py` (NEW)
- **Acceptance Criteria**:
  - Test passes
  - On failure, captures stdout/stderr for debugging
- **Target Conditions**: TC-024, TC-025
- **Depends On**: [ADV001-T020, ADV001-T027]
- **Evaluation**:
  - Access requirements: Write, Bash (subprocess)
  - Skill set: pytest, subprocess
  - Estimated duration: 15min
  - Estimated tokens: 20000

### Implement automated tests for ADV-001
- **ID**: ADV001-T029
- **Description**: Final aggregation task. Verify all TC rows map to a passing test. Run the
  full suite: `pytest R:/Sandbox/ark/tests/ -q` and `cargo test -p ark-dsl` from
  `R:/Sandbox/ark/`. Measure coverage: `coverage run -m pytest tests/test_*expression*.py
  tests/test_*predicate*.py && coverage report`. Assert >=80%. Record results in
  `R:/Sandbox/.agent/adventures/ADV-001/tests/test-results.md`.
- **Files**:
  - `R:/Sandbox/.agent/adventures/ADV-001/tests/test-results.md` (NEW)
- **Acceptance Criteria**:
  - All TCs marked `proof_method: autotest` have a passing test
  - Full pytest suite green
  - cargo test green
  - Coverage >=80% for expression/predicate modules
- **Target Conditions**: TC-025, TC-028
- **Depends On**: [ADV001-T022, ADV001-T023, ADV001-T024, ADV001-T025, ADV001-T026, ADV001-T027, ADV001-T028]
- **Evaluation**:
  - Access requirements: Bash (pytest, cargo, coverage), Write test-results.md
  - Skill set: test orchestration, coverage
  - Estimated duration: 25min
  - Estimated tokens: 40000

### Rust inline AST tests for Pipe/Expression/Predicate
- **ID**: ADV001-T030
- **Description**: Extend `#[cfg(test)] mod tests` in `R:/Sandbox/ark/dsl/src/parse.rs` (or
  `lib.rs`) with round-trip tests: parse a small string, assert AST structure, then
  serialize to JSON and deserialize, asserting equivalence. Cover pipe, param refs,
  expression_def, predicate_def.
- **Files**:
  - `R:/Sandbox/ark/dsl/src/parse.rs`
- **Acceptance Criteria**:
  - `cargo test -p ark-dsl` green
  - At least 6 new #[test] functions
- **Target Conditions**: TC-005, TC-026
- **Depends On**: [ADV001-T004]
- **Evaluation**:
  - Access requirements: Edit parse.rs, Bash (cargo test)
  - Skill set: Rust, serde, pest test patterns
  - Estimated duration: 20min
  - Estimated tokens: 30000
