# Plan: Schema & Island Definitions

## Designs Covered
- design-graph-schema: Code Graph Schema
- design-graph-island: Code Graph Island

## Tasks

### Design test strategy for ADV-002
- **ID**: ADV002-T001
- **Description**: Design automated tests covering all target conditions with
  `proof_method: autotest`. Create test strategy document in
  `R:/Sandbox/.agent/adventures/ADV-002/tests/test-strategy.md`. Define test files,
  frameworks, and commands for each TC. Read all 7 design documents first.
- **Files**:
  - `R:/Sandbox/.agent/adventures/ADV-002/tests/test-strategy.md` (NEW)
- **Acceptance Criteria**:
  - File exists and lists every TC from the manifest
  - Each TC has a proof_command using `python ark.py ...` or `pytest ...`
  - Test files are grouped by subsystem (schema, indexer, query, verify, viz)
- **Target Conditions**: TC-027
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read adventure designs
  - Skill set: test planning, pytest
  - Estimated duration: 15min
  - Estimated tokens: 15000

### Create code_graph.ark stdlib schema
- **ID**: ADV002-T002
- **Description**: Create `R:/Sandbox/ark/dsl/stdlib/code_graph.ark` with all struct and
  enum definitions from the schema design: Module, Function, Class, Method, Parameter,
  Variable, Edge, EdgeKind, CallEdge, InheritsEdge, ImportEdge, ArkEntity, Complexity,
  CodeGraph, GraphMetadata, plus operational types (GraphOp, GraphResult, IndexRequest,
  QueryRequest, QueryResponse). Use only types already in `types.ark` or defined within
  this file. Verify it parses: `python ark.py parse dsl/stdlib/code_graph.ark`.
- **Files**:
  - `R:/Sandbox/ark/dsl/stdlib/code_graph.ark` (NEW)
- **Acceptance Criteria**:
  - File parses without errors
  - Contains all 15+ struct/enum definitions from schema
  - No undefined type references
- **Target Conditions**: TC-001, TC-002, TC-003
- **Depends On**: [ADV002-T001]
- **Evaluation**:
  - Access requirements: Read+Write dsl/stdlib/, Bash for `python ark.py parse`
  - Skill set: Ark DSL syntax, struct/enum declarations
  - Estimated duration: 20min
  - Estimated tokens: 25000

### Create code_graph.ark island and bridge specs
- **ID**: ADV002-T003
- **Description**: Create `R:/Sandbox/ark/specs/infra/code_graph.ark` with:
  `abstraction CodeIndex`, `class GraphStore`, `class CodeIndexer`, `class QueryEngine`,
  `class Watcher`, `island CodeGraphIsland`, `bridge CodeGraph_to_Orchestrator`, and
  `verify CodeGraphInvariants`. Update `R:/Sandbox/ark/specs/root.ark` to register
  CodeGraphIsland in SystemRegistry. Verify both files parse.
- **Files**:
  - `R:/Sandbox/ark/specs/infra/code_graph.ark` (NEW)
  - `R:/Sandbox/ark/specs/root.ark` (EDIT — add register statement)
- **Acceptance Criteria**:
  - `python ark.py parse specs/infra/code_graph.ark` succeeds
  - `python ark.py parse specs/root.ark` succeeds
  - Island contains all 5 classes
  - Bridge connects CodeGraphIsland to Orchestrator
  - Verify block has at least 2 checks
- **Target Conditions**: TC-004, TC-005, TC-006, TC-007
- **Depends On**: [ADV002-T002]
- **Evaluation**:
  - Access requirements: Read+Write specs/, Bash for `python ark.py parse`
  - Skill set: Ark DSL (island, bridge, verify patterns)
  - Estimated duration: 25min
  - Estimated tokens: 30000
