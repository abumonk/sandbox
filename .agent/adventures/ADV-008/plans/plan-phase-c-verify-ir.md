# Phase C — Verify + IR

## Designs Covered
- design-shape-grammar-package (IR section)
- design-verifier-passes

## Tasks

### IR extraction module
- **ID**: ADV008-T07
- **Description**: Implement `shape_grammar/tools/ir.py` per `schemas/processes.md` § IR extraction. Loads an `.ark` file via Ark's parser, extracts `ShapeGrammarIR(max_depth, seed, rules, axiom, semantic_labels, provenance)`. Supports both library import (`from ark_parser import parse`) and CLI subprocess fallback. Includes `__main__` for CLI dump.
- **Files**: `shape_grammar/tools/ir.py`, `shape_grammar/tools/__init__.py`
- **Acceptance Criteria**:
  - `python -m shape_grammar.tools.ir shape_grammar/specs/shape_grammar.ark` prints a populated IR JSON.
  - All error paths from `schemas/processes.md` raise `IRError` with the documented message prefix.
- **Target Conditions**: TC-03
- **Depends On**: [ADV008-T04, ADV008-T05, ADV008-T06]
- **Evaluation**:
  - Access requirements: Read (ark/tools/parser/, shape_grammar/specs/), Write (shape_grammar/tools/), Bash (python)
  - Skill set: Python, Lark AST handling
  - Estimated duration: 30min
  - Estimated tokens: 60000

### Termination + determinism + scope passes
- **ID**: ADV008-T08
- **Description**: Implement the three Z3-backed verifier passes per `design-verifier-passes.md`. Each pass is a separate module under `shape_grammar/tools/verify/`. CLI dispatch via `shape_grammar/tools/verify/__init__.py`.
- **Files**: `shape_grammar/tools/verify/__init__.py`, `shape_grammar/tools/verify/termination.py`, `shape_grammar/tools/verify/determinism.py`, `shape_grammar/tools/verify/scope.py`
- **Acceptance Criteria**:
  - All three passes run on `specs/shape_grammar.ark` and return PASS or PASS_OPAQUE.
  - Termination pass FAILs on a deliberate counterexample fixture (unbounded recursive rule).
  - Each pass exits with code 0 on PASS, 1 on FAIL.
- **Target Conditions**: TC-04a, TC-04b, TC-04c, TC-04d
- **Depends On**: [ADV008-T07]
- **Evaluation**:
  - Access requirements: Read (shape_grammar/specs/, ark/tools/verify/), Write (shape_grammar/tools/verify/), Bash (python with z3)
  - Skill set: Z3, Python, SMT modeling
  - Estimated duration: 30min
  - Estimated tokens: 75000

### IR + verifier tests
- **ID**: ADV008-T09
- **Description**: Write `shape_grammar/tests/test_ir.py` and `shape_grammar/tests/test_verifier.py` per `tests/test-strategy.md`. IR tests cover: round-trip from each spec island, every error path, empty-island edge case. Verifier tests cover: PASS on each spec island, FAIL on deliberate counterexample fixtures.
- **Files**: `shape_grammar/tests/test_ir.py`, `shape_grammar/tests/test_verifier.py`, `shape_grammar/tests/conftest.py`, `shape_grammar/tests/fixtures/unbounded.ark`
- **Acceptance Criteria**:
  - `pytest shape_grammar/tests/test_ir.py -q` green.
  - `pytest shape_grammar/tests/test_verifier.py -q` green.
  - At least one negative test in each file.
- **Target Conditions**: TC-03, TC-04a, TC-04b, TC-04c, TC-04d
- **Depends On**: [ADV008-T07, ADV008-T08]
- **Evaluation**:
  - Access requirements: Read (shape_grammar/), Write (shape_grammar/tests/), Bash (pytest)
  - Skill set: pytest
  - Estimated duration: 25min
  - Estimated tokens: 50000
