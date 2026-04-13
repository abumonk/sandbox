---
adventure_id: ADV-002
status: pending_approval
created: 2026-04-13T10:30:00Z
approved: null
passes_completed: 4
validation_gaps: 0
---

# Permission Requests — ADV-002: CodeGraphContext-style Code Knowledge Graph in Ark DSL

## Summary

38 permission entries across 17 tasks and 3 agent roles (planner, coder, qa-tester). All
4 analysis passes complete. 0 validation gaps. The Ark project has no git remote, so no
remote git operations are required. Python (lark-parser, z3-solver pre-installed) and
Rust (cargo workspace at `R:/Sandbox/ark/`) are the runtime substrates.

## Pass 1 — Codebase Tooling Scan

Discovered tooling from the Ark project:

- `R:/Sandbox/ark/ark.py` — unified CLI: parse, verify, codegen, impact, diff, watch,
  dispatch, pipeline, graph, and the new `codegraph` subcommand
- `R:/Sandbox/ark/Cargo.toml` — Rust workspace; `cargo build`, `cargo test`
- `R:/Sandbox/ark/tests/conftest.py` — pytest fixtures; `pytest tests/ -q`
- Python deps: `lark-parser`, `z3-solver` (pre-installed)
- No linter, formatter, .env files, or CI workflows configured
- No new external dependencies required (uses only Python stdlib `ast`, `re`, `json`,
  `pathlib`, `os`, `sys`)

## Pass 2 — Plan-Driven Analysis

Per-task execution paths:

- **T001** (planner): Read designs, Write test-strategy.md. No Bash.
- **T002** (coder): Write stdlib .ark file → `python ark.py parse dsl/stdlib/code_graph.ark`
- **T003** (coder): Write specs .ark files, Edit root.ark → `python ark.py parse specs/infra/code_graph.ark`, `python ark.py parse specs/root.ark`
- **T004** (coder): Write stdlib queries .ark → `python ark.py parse dsl/stdlib/code_graph_queries.ark`
- **T005** (coder): Edit expression_primitives.py → `pytest tests/test_codegen_expression.py`, `python ark.py codegen dsl/stdlib/code_graph_queries.ark --target rust`
- **T006** (coder): Edit verify tools → `python ark.py verify dsl/stdlib/code_graph_queries.ark`
- **T007** (coder): Write graph_store.py → `python -c "from tools.codegraph.graph_store import GraphStore"`
- **T008** (coder): Write python_parser.py → `python -c "from tools.codegraph.python_parser import ..."`
- **T009** (coder): Write rust_parser.py → `python -c "from tools.codegraph.rust_parser import ..."`
- **T010** (coder): Write ark_parser_adapter.py → `python -c "from tools.codegraph.ark_parser_adapter import ..."`
- **T011** (coder): Write complexity.py → `python -c "from tools.codegraph.complexity import ..."`
- **T012** (coder): Write indexer.py, Edit ark.py → `python ark.py codegraph index R:/Sandbox/ark/tools/`
- **T013** (coder): Edit ark_verify.py → `pytest tests/test_codegraph_verify.py`
- **T014** (coder): Edit ark_visualizer.py, Write codegraph/visualizer.py, Edit ark.py → `python ark.py codegraph graph R:/Sandbox/ark/tools/`
- **T015** (coder): Write self_index.py, Write ark_self_graph.ark → `python tools/codegraph/self_index.py`
- **T016** (coder): Run CLI queries → `python ark.py codegraph query callers parse`
- **T017** (qa-tester): Write test files → `pytest tests/test_codegraph_*.py -q`

## Pass 3 — Historical Pattern Match

`.agent/knowledge/` files are empty (patterns, decisions, issues all have only headers).
ADV-001 permissions (read above) established these relevant patterns:

- `pytest -q` may hit Unicode-encoding issues on Windows; `ark.py` reconfigures stdout.
- All `cargo` and `python ark.py` commands must be run from `R:/Sandbox/ark/` (workspace root).
- No historical permission gaps recorded (ADV-001 was first adventure, completed cleanly).

Defensive additions:
- Python `ast` module is stdlib — no install needed.
- New `tools/codegraph/` directory creation is implicit in Write operations.
- Generated output to `specs/generated/` is a write-only operation.

## Pass 4 — Cross-Validation Matrix

| Task | Agent | Stage | Read | Write | Shell | MCP | External | Verified |
|------|-------|-------|------|-------|-------|-----|----------|----------|
| T001 | planner | planning | designs/** | adv/tests/test-strategy.md | - | - | - | Y |
| T002 | coder | implementing | types.ark, expression.ark | dsl/stdlib/code_graph.ark | python ark.py parse | - | - | Y |
| T003 | coder | implementing | code_graph.ark, root.ark | specs/infra/code_graph.ark, root.ark | python ark.py parse | - | - | Y |
| T004 | coder | implementing | code_graph.ark, expression.ark | dsl/stdlib/code_graph_queries.ark | python ark.py parse | - | - | Y |
| T005 | coder | implementing | expression_primitives.py | expression_primitives.py | pytest, python ark.py codegen | - | - | Y |
| T006 | coder | implementing | expression_smt.py, ark_verify.py | expression_smt.py, ark_verify.py | python ark.py verify | - | - | Y |
| T007 | coder | implementing | - | tools/codegraph/__init__.py, graph_store.py | python -c | - | - | Y |
| T008 | coder | implementing | ark.py, ark_parser.py | tools/codegraph/python_parser.py | python -c | - | - | Y |
| T009 | coder | implementing | dsl/src/lib.rs | tools/codegraph/rust_parser.py | python -c | - | - | Y |
| T010 | coder | implementing | ark_parser.py | tools/codegraph/ark_parser_adapter.py | python -c | - | - | Y |
| T011 | coder | implementing | - | tools/codegraph/complexity.py | python -c | - | - | Y |
| T012 | coder | implementing | graph_store, parsers | tools/codegraph/indexer.py, ark.py | python ark.py codegraph | - | - | Y |
| T013 | coder | implementing | ark_verify.py, graph_store.py | ark_verify.py | pytest | - | - | Y |
| T014 | coder | implementing | ark_visualizer.py | ark_visualizer.py, codegraph/visualizer.py, ark.py | python ark.py codegraph graph | - | - | Y |
| T015 | coder | implementing | indexer.py, all source | self_index.py, ark_self_graph.ark, code_graph.json | python self_index.py | - | - | Y |
| T016 | coder | implementing | code_graph.json | - | python ark.py codegraph query | - | - | Y |
| T017 | qa-tester | reviewing | tests/*, tools/codegraph/* | tests/test_codegraph_*.py | pytest | - | - | Y |

Validation checks:
1. Every task has at least one permission entry: YES (all 17 tasks covered)
2. Every shell command from Pass 1 covered: YES (python ark.py, pytest)
3. Every proof_command in TCs covered: YES (all pytest/ark.py commands)
4. Every file in task files has R/W permission: YES
5. Task dependencies — predecessor output readable: YES
6. Git operations: N/A (current-branch mode, no remote)

## Requests

### Shell Access
| # | Agent | Stage | Command | Reason | Tasks |
|---|-------|-------|---------|--------|-------|
| 1 | coder | implementing | `python ark.py parse <file>` | Parse .ark files to verify syntax | T002, T003, T004 |
| 2 | coder | implementing | `python ark.py verify <file>` | Verify graph expressions/invariants | T006 |
| 3 | coder | implementing | `python ark.py codegen <file> --target rust` | Generate Rust from graph queries | T005 |
| 4 | coder | implementing | `python -c "import ..."` | Smoke-test Python module imports | T007-T011 |
| 5 | coder | implementing | `python ark.py codegraph index <path>` | Run indexer CLI | T012, T015, T016 |
| 6 | coder | implementing | `python ark.py codegraph query <type> <arg>` | Run query CLI | T016 |
| 7 | coder | implementing | `python ark.py codegraph graph <path>` | Generate graph visualization | T014 |
| 8 | coder | implementing | `python ark.py codegraph stats` | Show graph statistics | T012 |
| 9 | coder | implementing | `python tools/codegraph/self_index.py` | Run self-indexing script | T015 |
| 10 | coder | implementing | `pytest tests/test_codegen_expression.py -q` | Regression check on codegen | T005 |
| 11 | coder | implementing | `pytest tests/test_codegraph_verify.py -q` | Test graph verification | T013 |
| 12 | qa-tester | reviewing | `pytest tests/test_codegraph_*.py -q` | Run all code graph tests | T017 |
| 13 | qa-tester | reviewing | `pytest tests/ -q` | Full regression suite | T017 |

### File Access
| # | Agent | Stage | Scope | Mode | Reason | Tasks |
|---|-------|-------|-------|------|--------|-------|
| 1 | planner | planning | `.agent/adventures/ADV-002/designs/**` | read | Read design docs for test strategy | T001 |
| 2 | planner | planning | `.agent/adventures/ADV-002/tests/test-strategy.md` | write | Create test strategy | T001 |
| 3 | coder | implementing | `R:/Sandbox/ark/dsl/stdlib/*.ark` | read+write | Create/read schema and query files | T002, T004 |
| 4 | coder | implementing | `R:/Sandbox/ark/specs/infra/*.ark` | read+write | Create island/bridge specs | T003, T015 |
| 5 | coder | implementing | `R:/Sandbox/ark/specs/root.ark` | read+write | Register CodeGraphIsland | T003 |
| 6 | coder | implementing | `R:/Sandbox/ark/tools/codegen/expression_primitives.py` | read+write | Add graph primitives | T005 |
| 7 | coder | implementing | `R:/Sandbox/ark/tools/verify/ark_verify.py` | read+write | Add graph verification | T006, T013 |
| 8 | coder | implementing | `R:/Sandbox/ark/tools/verify/expression_smt.py` | read+write | Extend SMT for graph types | T006 |
| 9 | coder | implementing | `R:/Sandbox/ark/tools/codegraph/**` | read+write | Create all indexer modules | T007-T012, T014, T015 |
| 10 | coder | implementing | `R:/Sandbox/ark/ark.py` | read+write | Add codegraph subcommand | T012, T014 |
| 11 | coder | implementing | `R:/Sandbox/ark/tools/visualizer/ark_visualizer.py` | read+write | Extend for code graph | T014 |
| 12 | coder | implementing | `R:/Sandbox/ark/specs/generated/code_graph.json` | write | Save self-index output | T015 |
| 13 | coder | implementing | `R:/Sandbox/ark/tools/parser/ark_parser.py` | read | Reference for adapter | T010 |
| 14 | coder | implementing | `R:/Sandbox/ark/dsl/src/lib.rs` | read | Reference for Rust parser | T009 |
| 15 | qa-tester | reviewing | `R:/Sandbox/ark/tests/test_codegraph_*.py` | write | Create test files | T017 |
| 16 | qa-tester | reviewing | `R:/Sandbox/ark/tools/codegraph/**` | read | Read implementation for testing | T017 |
| 17 | qa-tester | reviewing | `R:/Sandbox/ark/tests/conftest.py` | read | Read fixtures | T017 |

### MCP Tools
| # | Agent | Stage | Tool | Reason | Tasks |
|---|-------|-------|------|--------|-------|
| (none required) | - | - | - | - | - |

### External Access
| # | Agent | Stage | Type | Target | Reason | Tasks |
|---|-------|-------|------|--------|--------|-------|
| (none required) | - | - | - | - | - | - |

## Historical Notes

ADV-001 completed with 0 permission gaps. The same Python+Rust+.ark tooling stack is
reused here. No additional dependencies need installation. The main new surface is the
`tools/codegraph/` directory tree, which is purely additive (no existing files conflict).

## Approval
- [ ] Approved by user
- [ ] Approved with modifications: {notes}
- [ ] Denied: {reason}
