# Plan: Query Expressions

## Designs Covered
- design-query-expressions: Query Expressions

## Tasks

### Create code_graph_queries.ark with graph query expressions and predicates
- **ID**: ADV002-T004
- **Description**: Create `R:/Sandbox/ark/dsl/stdlib/code_graph_queries.ark` with 7
  expression definitions (callers, call_chain, dead_code, complex_functions, subclasses,
  importers, module_deps) and 3 predicate definitions (is-reachable, has-cycles, is-dead).
  Each uses pipe syntax with `graph-*` primitives. Verify it parses.
- **Files**:
  - `R:/Sandbox/ark/dsl/stdlib/code_graph_queries.ark` (NEW)
- **Acceptance Criteria**:
  - File parses without errors
  - Contains 7 expressions and 3 predicates
  - All use the `|>` pipe syntax with `graph-*` stage names
- **Target Conditions**: TC-008
- **Depends On**: [ADV002-T002]
- **Evaluation**:
  - Access requirements: Read+Write dsl/stdlib/, Bash for `python ark.py parse`
  - Skill set: Ark DSL expression/predicate syntax
  - Estimated duration: 15min
  - Estimated tokens: 20000

### Register graph query primitives in EXPR_PRIMITIVES
- **ID**: ADV002-T005
- **Description**: Edit `R:/Sandbox/ark/tools/codegen/expression_primitives.py` to add
  entries for all `graph-*` pipe stages: graph-callers, graph-call-chain, graph-dead-code,
  graph-complex, graph-subclasses, graph-importers, graph-module-deps, graph-filter-edges,
  graph-is-reachable, graph-has-cycles, graph-is-dead. Each entry needs `rust` template,
  `kind` (fn), and `arity`. Verify existing tests still pass.
- **Files**:
  - `R:/Sandbox/ark/tools/codegen/expression_primitives.py` (EDIT)
- **Acceptance Criteria**:
  - All 11 graph-* primitives registered
  - `pytest tests/test_codegen_expression.py -q` passes (no regression)
  - `python ark.py codegen dsl/stdlib/code_graph_queries.ark --target rust` runs
- **Target Conditions**: TC-009, TC-010
- **Depends On**: [ADV002-T004]
- **Evaluation**:
  - Access requirements: Read+Write expression_primitives.py, Bash for pytest
  - Skill set: Python, codegen primitives map
  - Estimated duration: 15min
  - Estimated tokens: 20000

### Verify graph query expressions via Z3
- **ID**: ADV002-T006
- **Description**: Run `python ark.py verify dsl/stdlib/code_graph_queries.ark` and
  confirm all expressions/predicates get `PASS_OPAQUE` status (graph primitives are
  opaque). If the verifier chokes on unknown types (CodeGraph, [Function], etc.), add
  minimal type stubs to the expression_smt.py or ark_verify.py type resolution path.
- **Files**:
  - `R:/Sandbox/ark/tools/verify/expression_smt.py` (possible EDIT)
  - `R:/Sandbox/ark/tools/verify/ark_verify.py` (possible EDIT)
- **Acceptance Criteria**:
  - `python ark.py verify dsl/stdlib/code_graph_queries.ark` runs without crash
  - All expressions/predicates produce PASS_OPAQUE (not FAIL)
- **Target Conditions**: TC-011
- **Depends On**: [ADV002-T005]
- **Evaluation**:
  - Access requirements: Read+Write verify tools, Bash for ark.py verify
  - Skill set: Z3, SMT translation, Ark verifier
  - Estimated duration: 20min
  - Estimated tokens: 30000
