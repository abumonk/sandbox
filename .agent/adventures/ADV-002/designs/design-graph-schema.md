# Code Graph Schema — Design

## Overview

Define the core data model for the code knowledge graph as Ark `struct` and `enum`
declarations in `dsl/stdlib/code_graph.ark`. This provides the typed node and edge
definitions that all other components (indexer, queries, visualizer, verifier) operate on.

The schema draws from CGC's data model (Function, Class, Method, Module nodes with CALLS,
INHERITS, IMPORTS edges) but adapts it to Ark's type system and adds Ark-specific node
kinds (ArkEntity, ArkIsland, ArkBridge) so the graph can represent both implementation
code and `.ark` specs in a unified structure.

## Target Files

- `R:/Sandbox/ark/dsl/stdlib/code_graph.ark` (NEW) — struct/enum declarations for all
  node types, edge types, complexity metrics, and the top-level CodeGraph container.

## Approach

### Node Types (structs)

```
struct Module       { name, path, language, repo_path, line_count }
struct Function     { name, module, path, line, end_line, params, return_type, complexity, decorators }
struct Class        { name, module, path, line, end_line, bases, methods, fields }
struct Method       { name, class_name, module, path, line, end_line, params, return_type, complexity, is_static }
struct Parameter    { name, type_name, default_val, position }
struct Variable     { name, scope, type_name, line }
```

### Ark-Specific Node Types

```
struct ArkEntity    { name, kind (abstraction|class|instance|island|bridge|registry), file, inherits, ports }
struct ArkExpression { name, in_types, out_type, chain_stages }
struct ArkPredicate { name, in_types, check_body }
```

### Edge Types (enum + structs)

```
enum EdgeKind { calls, inherits_from, imports, contains, overrides, references, ark_bridge, ark_contains }
struct Edge         { source, target, kind, file, line }
struct CallEdge     { caller, callee, file, line, is_dynamic }
struct InheritsEdge { child, parent, file, line }
struct ImportEdge   { importer, imported, file, line, alias }
```

### Container

```
struct CodeGraph    { modules, functions, classes, methods, edges, metadata }
struct GraphMetadata { repo_path, indexed_at, language_stats, node_count, edge_count }
```

### Complexity

```
struct Complexity   { function_name, cyclomatic, cognitive, loc, halstead_volume }
```

## Dependencies

None (foundational schema).

## Target Conditions

- TC-001: `code_graph.ark` parses cleanly via `python ark.py parse dsl/stdlib/code_graph.ark`
- TC-002: All struct fields use types already defined in `types.ark` or in `code_graph.ark` itself
- TC-003: Schema covers Function, Class, Method, Module, Parameter, Edge, Complexity at minimum
