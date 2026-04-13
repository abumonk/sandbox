# Query Expressions — Design

## Overview

Define Ark-native query expressions for the code graph, leveraging ADV-001's expression
and predicate system. These are declared as `expression` and `predicate` items in a new
stdlib file and can be used in `#process` bodies, `verify` blocks, and by the query engine.

## Target Files

- `R:/Sandbox/ark/dsl/stdlib/code_graph_queries.ark` (NEW) — expression and predicate
  definitions for graph queries
- `R:/Sandbox/ark/tools/codegen/expression_primitives.py` — add graph-query primitives
  to the EXPR_PRIMITIVES map

## Approach

### Expressions

```ark
// Find all callers of a function
expression callers {
  in: fn_name: String, graph: CodeGraph
  out: [Function]
  chain: graph |> graph-callers(fn_name)
}

// Find transitive call chain from an entry point
expression call_chain {
  in: entry: String, graph: CodeGraph
  out: [Function]
  chain: graph |> graph-call-chain(entry)
}

// Find potentially dead code (functions with zero callers)
expression dead_code {
  in: graph: CodeGraph
  out: [Function]
  chain: graph |> graph-dead-code
}

// Get functions exceeding a complexity threshold
expression complex_functions {
  in: graph: CodeGraph, threshold: Int
  out: [Function]
  chain: graph |> graph-complex(threshold)
}

// Find all classes inheriting from a given base
expression subclasses {
  in: base_name: String, graph: CodeGraph
  out: [Class]
  chain: graph |> graph-subclasses(base_name)
}

// Find all importers of a module
expression importers {
  in: module_name: String, graph: CodeGraph
  out: [Module]
  chain: graph |> graph-importers(module_name)
}

// Get module dependency graph
expression module_deps {
  in: module_name: String, graph: CodeGraph
  out: [Module]
  chain: graph |> graph-module-deps(module_name)
}
```

### Predicates

```ark
predicate is-reachable {
  in: source: String, target: String, graph: CodeGraph
  check: graph |> graph-is-reachable(source, target)
}

predicate has-cycles {
  in: graph: CodeGraph
  check: graph |> graph-has-cycles
}

predicate is-dead {
  in: fn_name: String, graph: CodeGraph
  check: graph |> graph-is-dead(fn_name)
}
```

### Primitive Registration

Add entries to `EXPR_PRIMITIVES` for each `graph-*` pipe stage. These will be opaque
primitives for Z3 (returning `PASS_OPAQUE` on verification) but will have concrete
Rust/Python codegen implementations.

```python
"graph-callers": {
    "rust": "graph_callers({self}, {0})",
    "kind": "fn",
    "arity": 1,
},
```

## Dependencies

- design-graph-schema (query types reference CodeGraph, Function, Class, etc.)
- ADV-001 expression/predicate system (pipe syntax, EXPR_PRIMITIVES)

## Target Conditions

- TC-008: `code_graph_queries.ark` parses without errors
- TC-009: Each query expression has a corresponding entry in EXPR_PRIMITIVES
- TC-010: Expressions compile to Rust via codegen (stub implementations acceptable)
- TC-011: Predicates verify via Z3 (PASS_OPAQUE for opaque graph primitives)
