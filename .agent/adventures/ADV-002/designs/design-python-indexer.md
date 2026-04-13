# Python Indexer — Design

## Overview

Implement a Python-based code indexer under `tools/codegraph/` that parses source files
(Python, Rust, and `.ark`) using AST-based approaches (not tree-sitter, to avoid the
native dependency) and produces Ark-conformant graph data matching the `code_graph.ark`
schema.

CGC uses tree-sitter for 14 languages. We use Python's built-in `ast` module for Python,
a regex/pattern-based approach for Rust (good enough for structural extraction without
a full parser), and the existing `ark_parser.py` for `.ark` files.

## Target Files

- `R:/Sandbox/ark/tools/codegraph/__init__.py` (NEW)
- `R:/Sandbox/ark/tools/codegraph/indexer.py` (NEW) — main indexer entry point
- `R:/Sandbox/ark/tools/codegraph/python_parser.py` (NEW) — Python AST → graph nodes
- `R:/Sandbox/ark/tools/codegraph/rust_parser.py` (NEW) — Rust source → graph nodes
- `R:/Sandbox/ark/tools/codegraph/ark_parser_adapter.py` (NEW) — .ark → graph nodes
  (wraps existing ark_parser.py)
- `R:/Sandbox/ark/tools/codegraph/graph_store.py` (NEW) — in-memory graph data structure
- `R:/Sandbox/ark/tools/codegraph/complexity.py` (NEW) — cyclomatic complexity calculator
- `R:/Sandbox/ark/ark.py` — add `codegraph` subcommand

## Approach

### Python Parser (`python_parser.py`)

Uses `ast.parse()` to walk Python files:
- `ast.FunctionDef` / `ast.AsyncFunctionDef` → Function nodes
- `ast.ClassDef` → Class nodes, with methods extracted
- `ast.Import` / `ast.ImportFrom` → ImportEdge
- Function body analysis: `ast.Call` nodes → CallEdge (name resolution via scope chain)
- `ast.Attribute` calls → method call edges
- Decorators captured as metadata

### Rust Parser (`rust_parser.py`)

Regex/pattern-based extraction (no syn/tree-sitter dependency):
- `fn\s+(\w+)` → Function nodes
- `impl\s+(\w+)` → method grouping
- `struct\s+(\w+)` / `enum\s+(\w+)` → Class-equivalent nodes
- `use\s+(.+);` → ImportEdge
- Function call patterns `(\w+)\(` → CallEdge (best-effort)
- `pub` visibility tracking

### Ark Parser Adapter (`ark_parser_adapter.py`)

Wraps the existing `ark_parser.py`:
- Parse `.ark` files → AST dict
- Map `abstraction`, `class`, `instance` → ArkEntity nodes
- Map `island` → ArkEntity with contains edges
- Map `bridge` → ArkBridge edges
- Map `expression`, `predicate` → ArkExpression/ArkPredicate nodes
- Extract `inherits` → InheritsEdge
- Extract `@in/@out` ports → reference edges

### Graph Store (`graph_store.py`)

In-memory directed graph:
- Adjacency list representation
- Node lookup by name, type, module
- Edge queries: incoming, outgoing, transitive closure
- Serialization to/from JSON (Ark-conformant)

### Complexity Calculator (`complexity.py`)

For Python: walk AST, count branch points (if/elif/for/while/try/except/and/or)
For Rust: regex-count branch keywords
Result: `Complexity` struct per function

### CLI Integration

Add `ark codegraph <path>` subcommand to `ark.py`:
- `ark codegraph index <path>` — index directory, output graph JSON
- `ark codegraph query callers <fn>` — find callers
- `ark codegraph query dead-code` — find dead code
- `ark codegraph query complexity [--threshold N]` — complex functions
- `ark codegraph stats` — node/edge counts

## Dependencies

- design-graph-schema (output schema)

## Target Conditions

- TC-012: Python indexer extracts functions, classes, methods, imports from Python files
- TC-013: Rust indexer extracts functions, structs, impls, use statements from Rust files
- TC-014: Ark adapter extracts entities, islands, bridges, expressions from .ark files
- TC-015: Graph store supports add/query/serialize operations
- TC-016: Complexity calculator produces cyclomatic complexity for Python functions
- TC-017: `ark codegraph index` CLI subcommand works end-to-end on `R:/Sandbox/ark/tools/`
