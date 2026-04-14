# Test Strategy & Test Implementation

## Designs Covered
- (all designs — cross-cutting test concern)

## Tasks

### Design test strategy for Visual Communication Layer
- **ID**: ADV006-T001
- **Description**: Design automated tests covering all target conditions with `proof_method: autotest`. Create test strategy document in `tests/test-strategy.md`. Define test files, frameworks, and commands for each TC. Map every TC-001 through TC-037 to specific test functions and pytest files.
- **Files**: `.agent/adventures/ADV-006/tests/test-strategy.md`
- **Acceptance Criteria**:
  - Test strategy document exists at `tests/test-strategy.md` within adventure directory
  - All 37 target conditions mapped to specific test cases
  - Test approach, tooling (pytest), and coverage expectations defined
  - Test files named: `test_visual_schema.py`, `test_visual_parser.py`, `test_visual_verify.py`, `test_visual_codegen.py`, `test_visual_renderer.py`, `test_visual_integration.py`
- **Target Conditions**: TC-001 through TC-037 (strategy covers all)
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read, Write, Glob, Grep
  - Skill set: test design, pytest, ark-dsl
  - Estimated duration: 20min
  - Estimated tokens: 20000

### Implement automated tests for Visual Communication Layer
- **ID**: ADV006-T019
- **Description**: Implement all tests from the test strategy. Each TC with `proof_method: autotest` must have a passing test. Create test files in `ark/tests/`: `test_visual_schema.py`, `test_visual_parser.py`, `test_visual_verify.py`, `test_visual_codegen.py`, `test_visual_renderer.py`, `test_visual_integration.py`. Run all tests and verify.
- **Files**: `ark/tests/test_visual_schema.py`, `ark/tests/test_visual_parser.py`, `ark/tests/test_visual_verify.py`, `ark/tests/test_visual_codegen.py`, `ark/tests/test_visual_renderer.py`, `ark/tests/test_visual_integration.py`, `ark/tests/conftest.py`
- **Acceptance Criteria**:
  - All test files created with test functions per TC mapping
  - `pytest tests/test_visual_*.py` passes with 0 failures
  - Every TC with `proof_method: autotest` has at least one test
  - No regressions in existing test suite (`pytest tests/`)
- **Target Conditions**: TC-001 through TC-037
- **Depends On**: [ADV006-T001, ADV006-T002, ADV006-T003, ADV006-T004, ADV006-T005, ADV006-T006, ADV006-T007, ADV006-T008, ADV006-T009, ADV006-T010, ADV006-T011, ADV006-T012, ADV006-T013, ADV006-T014, ADV006-T015, ADV006-T016, ADV006-T017, ADV006-T018]
- **Evaluation**:
  - Access requirements: Read, Write, Bash, Glob, Grep
  - Skill set: pytest, python, z3-solver, ark-dsl
  - Estimated duration: 30min
  - Estimated tokens: 80000
