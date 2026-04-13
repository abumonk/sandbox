# Graph Verification — Design

## Overview

Extend the Z3 verifier (`ark_verify.py` and `expression_smt.py`) to support structural
integrity checks on the code graph: no dangling edges, no inheritance cycles, all declared
exports reachable, and dependency-graph acyclicity where required.

## Target Files

- `R:/Sandbox/ark/tools/verify/ark_verify.py` — extend to handle graph invariants
- `R:/Sandbox/ark/tools/verify/expression_smt.py` — add SMT translations for graph predicates
- `R:/Sandbox/ark/specs/infra/code_graph.ark` — verify block with graph checks

## Approach

### Verify Block in code_graph.ark

```ark
verify CodeGraphInvariants {
  // No edge references a node that does not exist
  check no_dangling_edges:
    for_all graph.edges as e:
      e.source in graph.index and e.target in graph.index

  // Inheritance graph is acyclic
  check no_inheritance_cycles:
    not has-cycles(graph |> graph-filter-edges(inherits_from))

  // All declared exports are reachable from at least one entry point
  check exports_reachable:
    for_all graph.functions as f where f.is_exported:
      is-reachable("__entry__", f.name, graph)

  // Bridge contracts: source and target types match
  check bridge_type_match:
    for_all graph.edges as e where e.kind == ark_bridge:
      type_compatible(e.source, e.target)
}
```

### SMT Translation Strategy

Graph invariants cannot be fully encoded in SMT (graphs are infinite-domain).
Strategy:

1. **Bounded checking**: for a given graph instance, enumerate all edges and assert
   membership constraints as finite conjunctions. This works for concrete graphs
   produced by the indexer.

2. **Opaque predicates**: `has-cycles`, `is-reachable` are registered as opaque
   Z3 functions. The verifier can check structural well-formedness but not
   semantic correctness — result is `PASS_OPAQUE`.

3. **Concrete graph mode**: when a graph JSON is available (from `ark codegraph index`),
   load it and check all invariants concretely. This is the primary verification path.

### Integration with ark_verify.py

Add a new verification mode: `verify_graph(graph_json, verify_block)` that:
1. Loads the graph JSON
2. Creates Z3 variables for each node and edge
3. Asserts all `check` statements
4. Returns PASS/FAIL per check

## Dependencies

- design-graph-schema (struct definitions for type checking)
- design-graph-island (verify block location)

## Target Conditions

- TC-018: "no dangling edges" invariant is expressible and checkable
- TC-019: "no inheritance cycles" check works on a concrete graph
- TC-020: Verification integrates with `python ark.py verify specs/infra/code_graph.ark`
