# Plan: Indexer Implementation

## Designs Covered
- design-python-indexer: Python Indexer

## Tasks

### Implement in-memory graph store
- **ID**: ADV002-T007
- **Description**: Create `R:/Sandbox/ark/tools/codegraph/__init__.py` and
  `R:/Sandbox/ark/tools/codegraph/graph_store.py`. The graph store implements:
  - Node storage (dict by name, with type and properties)
  - Edge storage (list of Edge dicts)
  - Name index for O(1) lookup
  - Query methods: get_node, get_edges_from, get_edges_to, get_nodes_by_type
  - Transitive closure (BFS) for reachability queries
  - Serialization to/from JSON matching the CodeGraph schema
- **Files**:
  - `R:/Sandbox/ark/tools/codegraph/__init__.py` (NEW)
  - `R:/Sandbox/ark/tools/codegraph/graph_store.py` (NEW)
- **Acceptance Criteria**:
  - Module imports without error
  - Can add nodes and edges, query by type, serialize to JSON
  - Transitive closure works (tested manually or via unit test)
- **Target Conditions**: TC-015
- **Depends On**: [ADV002-T001]
- **Evaluation**:
  - Access requirements: Read+Write tools/codegraph/
  - Skill set: Python, graph data structures
  - Estimated duration: 20min
  - Estimated tokens: 25000

### Implement Python source parser
- **ID**: ADV002-T008
- **Description**: Create `R:/Sandbox/ark/tools/codegraph/python_parser.py`. Uses
  Python `ast` module to extract:
  - `ast.FunctionDef` / `ast.AsyncFunctionDef` -> Function nodes
  - `ast.ClassDef` -> Class nodes with methods
  - `ast.Import` / `ast.ImportFrom` -> ImportEdge
  - `ast.Call` in function bodies -> CallEdge (best-effort name resolution)
  - Decorator extraction
  - Module-level info (path, line count)
  Returns list of nodes and edges in GraphStore-compatible format.
- **Files**:
  - `R:/Sandbox/ark/tools/codegraph/python_parser.py` (NEW)
- **Acceptance Criteria**:
  - Parses `R:/Sandbox/ark/ark.py` and extracts functions
  - Parses `R:/Sandbox/ark/tools/parser/ark_parser.py` and extracts classes + methods
  - Returns well-formed node/edge dicts
- **Target Conditions**: TC-012
- **Depends On**: [ADV002-T007]
- **Evaluation**:
  - Access requirements: Read+Write tools/codegraph/
  - Skill set: Python ast module, code analysis
  - Estimated duration: 25min
  - Estimated tokens: 35000

### Implement Rust source parser
- **ID**: ADV002-T009
- **Description**: Create `R:/Sandbox/ark/tools/codegraph/rust_parser.py`. Uses regex
  patterns to extract structural elements from Rust source:
  - `(pub\s+)?fn\s+(\w+)` -> Function nodes
  - `(pub\s+)?struct\s+(\w+)` -> Class-equivalent nodes
  - `(pub\s+)?enum\s+(\w+)` -> Class-equivalent nodes
  - `impl(\s+\w+)?\s+(\w+)` -> method grouping
  - `use\s+(.+);` -> ImportEdge
  - Function call patterns -> CallEdge (best-effort)
  Returns list of nodes and edges.
- **Files**:
  - `R:/Sandbox/ark/tools/codegraph/rust_parser.py` (NEW)
- **Acceptance Criteria**:
  - Parses `R:/Sandbox/ark/dsl/src/lib.rs` and extracts structs/enums
  - Parses `R:/Sandbox/ark/orchestrator/src/main.rs` and extracts functions
  - Returns well-formed node/edge dicts
- **Target Conditions**: TC-013
- **Depends On**: [ADV002-T007]
- **Evaluation**:
  - Access requirements: Read+Write tools/codegraph/
  - Skill set: Python regex, Rust syntax knowledge
  - Estimated duration: 20min
  - Estimated tokens: 30000

### Implement .ark file parser adapter
- **ID**: ADV002-T010
- **Description**: Create `R:/Sandbox/ark/tools/codegraph/ark_parser_adapter.py`. Wraps
  the existing `ark_parser.py` to produce graph nodes:
  - `abstraction`, `class`, `instance` -> ArkEntity nodes
  - `island` -> ArkEntity with contains edges
  - `bridge` -> Edge(ark_bridge)
  - `expression`, `predicate` -> ArkEntity nodes
  - `inherits` -> InheritsEdge
  - `@in/@out` ports -> metadata on nodes
  Returns list of nodes and edges.
- **Files**:
  - `R:/Sandbox/ark/tools/codegraph/ark_parser_adapter.py` (NEW)
- **Acceptance Criteria**:
  - Parses `R:/Sandbox/ark/specs/root.ark` and extracts islands, classes, bridges
  - Parses `R:/Sandbox/ark/dsl/stdlib/types.ark` and extracts structs/enums
  - Returns well-formed node/edge dicts
- **Target Conditions**: TC-014
- **Depends On**: [ADV002-T007]
- **Evaluation**:
  - Access requirements: Read+Write tools/codegraph/, Read tools/parser/
  - Skill set: Python, Ark AST structure
  - Estimated duration: 20min
  - Estimated tokens: 25000

### Implement complexity calculator
- **ID**: ADV002-T011
- **Description**: Create `R:/Sandbox/ark/tools/codegraph/complexity.py`. Calculates
  cyclomatic complexity:
  - Python: walk `ast` tree, count `if/elif/for/while/try/except/with/and/or/assert`
  - Rust: regex count of `if|match|for|while|loop|&&|\|\|`
  - Returns Complexity dict per function
- **Files**:
  - `R:/Sandbox/ark/tools/codegraph/complexity.py` (NEW)
- **Acceptance Criteria**:
  - Correct complexity for a simple Python function (linear = 1)
  - Correct complexity for a branchy function (if/else/for = 3+)
- **Target Conditions**: TC-016
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read+Write tools/codegraph/
  - Skill set: Python ast, software metrics
  - Estimated duration: 15min
  - Estimated tokens: 15000

### Implement main indexer and CLI integration
- **ID**: ADV002-T012
- **Description**: Create `R:/Sandbox/ark/tools/codegraph/indexer.py` as the main entry
  point. Orchestrates: walk directory -> dispatch to language parsers -> merge into
  GraphStore -> compute complexity -> serialize. Edit `R:/Sandbox/ark/ark.py` to add
  `codegraph` subcommand with sub-commands: `index`, `query`, `stats`.
  Add `tools/codegraph/` to sys.path in ark.py.
- **Files**:
  - `R:/Sandbox/ark/tools/codegraph/indexer.py` (NEW)
  - `R:/Sandbox/ark/ark.py` (EDIT — add codegraph subcommand)
- **Acceptance Criteria**:
  - `python ark.py codegraph index R:/Sandbox/ark/tools/` produces JSON output
  - `python ark.py codegraph stats` after indexing shows node/edge counts
  - `python ark.py codegraph query callers parse` finds callers
- **Target Conditions**: TC-017
- **Depends On**: [ADV002-T008, ADV002-T009, ADV002-T010, ADV002-T011]
- **Evaluation**:
  - Access requirements: Read+Write tools/codegraph/, Read+Write ark.py, Bash
  - Skill set: Python CLI design, file walking
  - Estimated duration: 25min
  - Estimated tokens: 35000
