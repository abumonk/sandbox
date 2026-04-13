# Plan: Reflexive Indexing & Tests

## Designs Covered
- design-reflexive-indexing: Reflexive Indexing

## Tasks

### Create self-indexing script and ark_self_graph.ark
- **ID**: ADV002-T015
- **Description**: Create `R:/Sandbox/ark/tools/codegraph/self_index.py` that indexes
  Ark's own source tree (tools/*.py, dsl/src/*.rs, orchestrator/src/*.rs, specs/*.ark,
  dsl/stdlib/*.ark) and saves the result to `specs/generated/code_graph.json`. Create
  `R:/Sandbox/ark/specs/infra/ark_self_graph.ark` with an instance definition.
  Run the script and verify output.
- **Files**:
  - `R:/Sandbox/ark/tools/codegraph/self_index.py` (NEW)
  - `R:/Sandbox/ark/specs/infra/ark_self_graph.ark` (NEW)
  - `R:/Sandbox/ark/specs/generated/code_graph.json` (GENERATED)
- **Acceptance Criteria**:
  - Script runs without errors
  - Output JSON is non-empty and contains nodes from all 3 languages
  - At least 100 nodes total in the graph
- **Target Conditions**: TC-024, TC-025
- **Depends On**: [ADV002-T012]
- **Evaluation**:
  - Access requirements: Read+Write tools/codegraph/, specs/, Bash
  - Skill set: Python, file I/O
  - Estimated duration: 20min
  - Estimated tokens: 25000

### Run sample queries on self-indexed graph
- **ID**: ADV002-T016
- **Description**: After self-indexing, run sample queries via the CLI and verify they
  return meaningful results:
  - `python ark.py codegraph query callers parse` — should find ark.py references
  - `python ark.py codegraph query dead-code` — should find some unreferenced functions
  - `python ark.py codegraph query complexity --threshold 10` — should find complex functions
  Document results in a brief report.
- **Files**:
  - No new files (CLI execution only)
- **Acceptance Criteria**:
  - At least one query returns non-empty, meaningful results
  - Results make structural sense (callers of `parse` should include test files)
- **Target Conditions**: TC-026
- **Depends On**: [ADV002-T015]
- **Evaluation**:
  - Access requirements: Bash for CLI commands
  - Skill set: code analysis interpretation
  - Estimated duration: 10min
  - Estimated tokens: 15000

### Implement automated tests for ADV-002
- **ID**: ADV002-T017
- **Description**: Implement all tests from the test strategy (T001). Create test files:
  - `R:/Sandbox/ark/tests/test_codegraph_store.py` — graph store unit tests
  - `R:/Sandbox/ark/tests/test_codegraph_python.py` — Python parser tests
  - `R:/Sandbox/ark/tests/test_codegraph_rust.py` — Rust parser tests
  - `R:/Sandbox/ark/tests/test_codegraph_ark.py` — Ark adapter tests
  - `R:/Sandbox/ark/tests/test_codegraph_queries.py` — query expression tests
  - `R:/Sandbox/ark/tests/test_codegraph_verify.py` — verification tests
  - `R:/Sandbox/ark/tests/test_codegraph_integration.py` — end-to-end integration
  Each TC with `proof_method: autotest` must have a passing test. Run all tests.
- **Files**:
  - `R:/Sandbox/ark/tests/test_codegraph_store.py` (NEW)
  - `R:/Sandbox/ark/tests/test_codegraph_python.py` (NEW)
  - `R:/Sandbox/ark/tests/test_codegraph_rust.py` (NEW)
  - `R:/Sandbox/ark/tests/test_codegraph_ark.py` (NEW)
  - `R:/Sandbox/ark/tests/test_codegraph_queries.py` (NEW)
  - `R:/Sandbox/ark/tests/test_codegraph_verify.py` (NEW)
  - `R:/Sandbox/ark/tests/test_codegraph_integration.py` (NEW)
- **Acceptance Criteria**:
  - All test files exist and are syntactically valid
  - `pytest tests/test_codegraph_*.py -q` passes with 0 failures
  - Every TC with proof_method: autotest has at least one test
- **Target Conditions**: TC-028
- **Depends On**: [ADV002-T001, ADV002-T012, ADV002-T013, ADV002-T014, ADV002-T015, ADV002-T016]
- **Evaluation**:
  - Access requirements: Read+Write tests/, Bash for pytest
  - Skill set: pytest, Python testing
  - Estimated duration: 30min
  - Estimated tokens: 45000
