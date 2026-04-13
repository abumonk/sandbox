# Reflexive Indexing — Design

## Overview

Run the code graph indexer over Ark's own source tree to produce the first real consumer
of the feature. Index `R:/Sandbox/ark/tools/` (Python), `R:/Sandbox/ark/dsl/src/` and
`R:/Sandbox/ark/orchestrator/src/` (Rust), and `R:/Sandbox/ark/specs/` plus
`R:/Sandbox/ark/dsl/stdlib/` (.ark files). Produce a saved graph JSON and verify it.

This is the "dogfood" step that proves the system works end-to-end.

## Target Files

- `R:/Sandbox/ark/specs/infra/ark_self_graph.ark` (NEW) — instance of CodeGraphIsland
  configured to index Ark itself
- `R:/Sandbox/ark/tools/codegraph/self_index.py` (NEW) — script to run self-indexing
  and save results
- Output: `R:/Sandbox/ark/specs/generated/code_graph.json` (generated artifact)

## Approach

### Self-Index Configuration

```ark
instance ark_self_graph: CodeIndexer {
  source_tree = "R:/Sandbox/ark"
  languages = ["python", "rust", "ark"]
}
```

### Self-Index Script

`self_index.py` orchestrates:
1. Walk `tools/` for `.py` files → Python indexer
2. Walk `dsl/src/`, `orchestrator/src/`, `codegen/src/`, `verify/src/`, `runtime/src/`
   for `.rs` files → Rust indexer
3. Walk `specs/`, `dsl/stdlib/` for `.ark` files → Ark adapter
4. Merge all results into a single CodeGraph
5. Serialize to `specs/generated/code_graph.json`
6. Print summary statistics

### Expected Graph Size

Estimates from file listing:
- ~25 Python files → ~150 functions, ~30 classes
- ~10 Rust files → ~50 functions, ~15 structs
- ~20 .ark files → ~60 entities, ~10 islands, ~5 bridges
- ~300 call edges, ~50 import edges, ~20 inheritance edges

### Validation Queries

After indexing, run sample queries:
- `callers("parse")` — should find ark.py and test files
- `dead_code()` — identify any unreferenced functions
- `complexity(> 10)` — find complex functions
- `subclasses("Transformer")` — find Lark transformer subclasses

## Dependencies

- design-python-indexer (indexer tools must work)
- design-graph-island (island/instance definitions)

## Target Conditions

- TC-024: Self-indexing over `R:/Sandbox/ark/` produces a non-empty graph JSON
- TC-025: Graph contains nodes from all three languages (Python, Rust, .ark)
- TC-026: At least one query (callers, dead_code, or complexity) returns meaningful results
