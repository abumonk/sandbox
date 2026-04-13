# Code Graph Island — Design

## Overview

Define the `CodeGraphIsland` as an Ark `island` that wraps the graph store, indexer,
query engine, and optional watcher into a single self-contained unit. This follows the
pattern established by `Root` and `Orchestrator` in `specs/root.ark`.

The island exposes `@in` ports for indexing requests and queries, `@out` ports for
query results and graph snapshots, and internal `$data` for the graph store itself.

## Target Files

- `R:/Sandbox/ark/specs/infra/code_graph.ark` (NEW) — island definition with:
  - `abstraction CodeIndex` — indexing contract
  - `class GraphStore` — in-memory graph backend
  - `class CodeIndexer` — concrete indexer implementing CodeIndex
  - `class QueryEngine` — query dispatch
  - `class Watcher` — file-change monitoring (reuses existing `ark watch` pattern)
  - `island CodeGraphIsland` — groups all of the above
  - `bridge CodeGraph_to_Orchestrator` — connects graph island to Orchestrator
  - `verify CodeGraphInvariants` — structural checks

- `R:/Sandbox/ark/specs/root.ark` — register `CodeGraphIsland` in `SystemRegistry`

## Approach

### Abstraction: CodeIndex

```ark
abstraction CodeIndex {
  @in{ source_tree: Path, languages: [String] }
  #process[strategy: code]{
    description: "Index source files into a code graph"
    requires: source_tree != ""
  }
  @out[]{ graph: CodeGraph }
  invariant: graph.modules.length > 0
}
```

### Class: GraphStore

In-memory directed graph with adjacency lists. Backend strategy is `in_memory` for v1;
external backends (kuzu, neo4j) deferred.

```ark
class GraphStore {
  $data nodes: [GraphNode] = []
  $data edges: [Edge] = []
  $data index: [String: Int] = []    // name → node position
  
  @in{ operation: GraphOp }
  #process[strategy: code]{
    // add_node, add_edge, remove_node, query
  }
  @out[]{ result: GraphResult }
  
  invariant: for_all edges as e: e.source in index and e.target in index
}
```

### Class: CodeIndexer

Concrete implementation of CodeIndex. Accepts a source tree path, walks files matching
language globs, delegates to language-specific parsers, and populates a GraphStore.

### Class: QueryEngine

Dispatches query expressions (callers, call_chain, dead_code, complexity) against the
GraphStore. Returns structured results.

### Island: CodeGraphIsland

```ark
island CodeGraphIsland {
  strategy: code
  description: "Code knowledge graph — index, query, visualize source repos"
  contains: [GraphStore, CodeIndexer, QueryEngine, Watcher]
  
  @in{ request: IndexRequest }
  @out[]{ response: QueryResponse }
}
```

### Bridge: CodeGraph_to_Orchestrator

Connects the graph island to the Orchestrator so indexing can be triggered as a pipeline
stage and query results can inform dispatch decisions.

## Dependencies

- design-graph-schema (structs must exist first)

## Target Conditions

- TC-004: `specs/infra/code_graph.ark` parses without errors
- TC-005: Island is registered in `root.ark` SystemRegistry
- TC-006: Bridge between CodeGraphIsland and Orchestrator is defined and passes contract verification
- TC-007: Invariant "no dangling edges" is expressed and verifiable via Z3
