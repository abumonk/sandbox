---
id: ADV-002
title: CodeGraphContext-style Code Knowledge Graph in Ark DSL
state: completed
created: 2026-04-11T00:00:00Z
updated: 2026-04-11T00:00:00Z
tasks: [ADV002-T001, ADV002-T002, ADV002-T003, ADV002-T004, ADV002-T005, ADV002-T006, ADV002-T007, ADV002-T008, ADV002-T009, ADV002-T010, ADV002-T011, ADV002-T012, ADV002-T013, ADV002-T014, ADV002-T015, ADV002-T016, ADV002-T017]
depends_on: [ADV-001]
---

## Concept

Review the CodeGraphContext (CGC) project (https://github.com/CodeGraphContext/CodeGraphContext) — a dual CLI + MCP server that transforms source repositories into **queryable code knowledge graphs** — and define/implement an Ark-native equivalent.

### What CGC does

- **Purpose**: turn a code repository into a directed graph of functions, classes, methods, parameters, inheritance, calls, and imports, so developers *and* AI assistants can answer "who calls what" questions structurally instead of via grep.
- **Two surfaces**:
  1. **CLI toolkit** — `cgc index <path>`, `cgc analyze callers <fn>`, `cgc analyze complexity`, `cgc analyze dead-code`, `cgc find pattern "<q>"`, `cgc watch <path>`.
  2. **MCP server** — `cgc mcp setup` / `cgc mcp start`, giving Claude/Cursor/Windsurf natural-language queries ("find who calls authenticate()", "show the call chain for payment processing").
- **Data model**: functions, classes, methods, parameters, signatures, inheritance hierarchies, call edges, import edges, complexity metrics.
- **Storage backends**: KùzuDB (Windows default), FalkorDB Lite (Unix default), Neo4j (enterprise).
- **Languages indexed**: Python, JavaScript, TypeScript, Java, C/C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, Dart, Perl (14).
- **Features**: live watcher, pre-indexed `.cgc` bundles, dead-code detection, complexity analysis, interactive web visualiser.

### Goal in Ark

Define and implement a **code-graph subsystem as an Ark `island`** so that any Ark-described codebase (and, reflexively, Ark's own `.ark` specs) can be indexed, queried, and visualised through the existing Ark pipeline (parse → verify → codegen → graph).

Concretely:

- **DSL surface** — model `CodeGraph` as an Ark island with:
  - `abstraction CodeIndex` — contract: `@in { source_tree: Path }`, `@out { graph: CodeGraph }`, invariants on graph well-formedness (no dangling edges, acyclic inheritance).
  - `class GraphStore` — backend strategy (`kuzu` | `falkor` | `neo4j` | `in_memory`).
  - `class Watcher` — file-watcher class that emits delta events.
  - `bridge` ports to Ark's existing `#process` and `Orchestrator` so indexing becomes a pipeline stage.
- **Schema** — Ark `struct` definitions for `Function`, `Class`, `Method`, `Parameter`, `CallEdge`, `ImportEdge`, `InheritsEdge`, `Module`, `Complexity`. These live in `dsl/stdlib/code_graph.ark`.
- **Queries** — Ark-native query expressions: `callers(@fn)`, `call_chain(@entry)`, `dead_code()`, `complexity(> @threshold)`. Leverage (or co-develop with) ADV-001's expression/predicate layer if present, otherwise define inline.
- **Ingestion** — a `cgc-ingest` tool under `tools/codegraph/` that parses the 14 languages (initially Python + Rust + `.ark` itself) and produces Ark-conformant graph data.
- **MCP surface** — expose Ark's code graph via an MCP skill so Claude Code can query it during `.ark` authoring ("who references `Vehicle` across `specs/game/`?").
- **Verification** — Z3 checks on the graph: no broken `depends_on`, no cycles where disallowed, all declared exports reachable.
- **Visualization** — reuse `tools/visualizer/ark_visualizer.py` to render the code graph alongside the existing Ark entity graph (shared LOD model).
- **Reflexive use-case** — run the indexer over `R:/Sandbox/ark/specs/` and `R:/Sandbox/ark/tools/` so the first real consumer of the feature is Ark itself.

### Why this matters

Ark already understands **its own** spec graph (entities, bridges, islands). It does **not** yet understand the **code that implements it** — the Python tools, the Rust crates, and how `.ark` features depend on them. A code-graph island closes that loop: Ark becomes introspective, can answer impact questions across both spec and implementation, and gains a shared substrate for an MCP query surface that any agent (Claude Code included) can reach during authoring.

## Target Conditions
| ID | Description | Source | Design | Plan | Task(s) | Proof Method | Proof Command | Status |
|----|-------------|--------|--------|------|---------|-------------|---------------|--------|

## Evaluations
| Task | Access Requirements | Skill Set | Est. Duration | Est. Tokens | Est. Cost | Actual Duration | Actual Tokens | Actual Cost | Variance |
|------|-------------------|-----------|---------------|-------------|-----------|-----------------|---------------|-------------|----------|

## Environment
- **Project**: ARK (Architecture Kernel) — declarative MMO game-engine DSL
- **Workspace**: R:/Sandbox (Ark tree at R:/Sandbox/ark)
- **Repo**: local (no git remote)
- **Branch**: local (not a git repo)
- **PC**: TTT
- **Platform**: Windows 11 Pro 10.0.26200
- **Runtime**: Node v24.12.0 (project runtime: Python 3 + Rust/Cargo)
- **Shell**: bash
