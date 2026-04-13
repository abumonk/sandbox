# ADV-002 Test Strategy

## Overview

This document maps every target condition (TC-001 through TC-028) from the ADV-002 manifest
to a proof method, proof command, test file assignment, and subsystem grouping.

## Proof Methods

- **autotest** — automated pytest or CLI command with deterministic pass/fail
- **poc** — proof-of-concept command that must produce non-trivial output (human judges "meaningful")
- **manual** — human inspection of generated artifact

## Test File Assignments by Subsystem

### Parse Commands (no dedicated test file -- direct CLI invocation)

| TC | Description | Proof Method | Proof Command |
|----|-------------|-------------|---------------|
| TC-001 | code_graph.ark parses cleanly | autotest | `python ark.py parse dsl/stdlib/code_graph.ark` |
| TC-002 | All struct fields use defined types | autotest | `python ark.py parse dsl/stdlib/code_graph.ark` |
| TC-004 | specs/infra/code_graph.ark parses without errors | autotest | `python ark.py parse specs/infra/code_graph.ark` |
| TC-005 | CodeGraphIsland registered in root.ark SystemRegistry | autotest | `python ark.py parse specs/root.ark` |
| TC-006 | Bridge between CodeGraphIsland and Orchestrator defined | autotest | `python ark.py parse specs/infra/code_graph.ark` |
| TC-008 | code_graph_queries.ark parses without errors | autotest | `python ark.py parse dsl/stdlib/code_graph_queries.ark` |
| TC-010 | Graph query expressions compile to Rust via codegen | autotest | `python ark.py codegen dsl/stdlib/code_graph_queries.ark --target rust` |
| TC-011 | Graph predicates verify via Z3 (PASS_OPAQUE) | autotest | `python ark.py verify dsl/stdlib/code_graph_queries.ark` |

### `test_codegraph_queries.py` -- Query Expressions and Schema

| TC | Description | Proof Method | Proof Command | Test Function(s) |
|----|-------------|-------------|---------------|------------------|
| TC-003 | Schema covers Function, Class, Method, Module, Parameter, Edge, Complexity | autotest | `pytest tests/test_codegraph_queries.py -k schema -q` | `test_schema_covers_required_types` |
| TC-009 | All graph-* primitives registered in EXPR_PRIMITIVES | autotest | `pytest tests/test_codegraph_queries.py -k primitives -q` | `test_graph_primitives_registered` |

### `test_codegraph_store.py` -- Graph Store

| TC | Description | Proof Method | Proof Command | Test Function(s) |
|----|-------------|-------------|---------------|------------------|
| TC-015 | Graph store supports add/query/serialize operations | autotest | `pytest tests/test_codegraph_store.py -q` | `test_add_node`, `test_add_edge`, `test_query_by_name`, `test_query_by_type`, `test_incoming_edges`, `test_outgoing_edges`, `test_serialize_json`, `test_deserialize_json`, `test_no_duplicate_nodes` |

### `test_codegraph_python.py` -- Python Parser

| TC | Description | Proof Method | Proof Command | Test Function(s) |
|----|-------------|-------------|---------------|------------------|
| TC-012 | Python indexer extracts functions, classes, methods, imports | autotest | `pytest tests/test_codegraph_python.py -q` | `test_extract_functions`, `test_extract_classes`, `test_extract_methods`, `test_extract_imports`, `test_extract_call_edges`, `test_extract_decorators` |
| TC-016 | Complexity calculator produces cyclomatic complexity for Python | autotest | `pytest tests/test_codegraph_python.py -k complexity -q` | `test_cyclomatic_simple_function`, `test_cyclomatic_branching`, `test_cyclomatic_nested` |

### `test_codegraph_rust.py` -- Rust Parser

| TC | Description | Proof Method | Proof Command | Test Function(s) |
|----|-------------|-------------|---------------|------------------|
| TC-013 | Rust indexer extracts functions, structs, impls, use statements | autotest | `pytest tests/test_codegraph_rust.py -q` | `test_extract_functions`, `test_extract_structs`, `test_extract_impl_blocks`, `test_extract_use_statements`, `test_extract_call_edges`, `test_pub_visibility` |

### `test_codegraph_ark.py` -- Ark Adapter

| TC | Description | Proof Method | Proof Command | Test Function(s) |
|----|-------------|-------------|---------------|------------------|
| TC-014 | Ark adapter extracts entities, islands, bridges, expressions | autotest | `pytest tests/test_codegraph_ark.py -q` | `test_extract_abstractions`, `test_extract_classes`, `test_extract_islands`, `test_extract_bridges`, `test_extract_expressions`, `test_extract_predicates`, `test_inherits_edges`, `test_port_references` |

### `test_codegraph_verify.py` -- Verification

| TC | Description | Proof Method | Proof Command | Test Function(s) |
|----|-------------|-------------|---------------|------------------|
| TC-018 | No-dangling-edges invariant checkable on concrete graph | autotest | `pytest tests/test_codegraph_verify.py -k dangling -q` | `test_dangling_edge_detected`, `test_clean_graph_passes_dangling_check` |
| TC-019 | No-inheritance-cycles check works on concrete graph | autotest | `pytest tests/test_codegraph_verify.py -k cycles -q` | `test_cycle_detected`, `test_acyclic_graph_passes` |

### `test_codegraph_integration.py` -- End-to-End / Reflexive

| TC | Description | Proof Method | Proof Command | Test Function(s) |
|----|-------------|-------------|---------------|------------------|
| TC-024 | Self-indexing produces non-empty graph JSON | autotest | `pytest tests/test_codegraph_integration.py -k self_index -q` | `test_self_index_nonempty` |
| TC-025 | Graph contains nodes from all three languages (Python, Rust, .ark) | autotest | `pytest tests/test_codegraph_integration.py -k languages -q` | `test_graph_has_python_nodes`, `test_graph_has_rust_nodes`, `test_graph_has_ark_nodes` |

### CLI Commands (direct invocation, no pytest file)

| TC | Description | Proof Method | Proof Command |
|----|-------------|-------------|---------------|
| TC-017 | `ark codegraph index` CLI subcommand works end-to-end | autotest | `python ark.py codegraph index R:/Sandbox/ark/tools/codegraph/` |
| TC-021 | `ark codegraph graph` produces a valid HTML file | autotest | `python ark.py codegraph graph R:/Sandbox/ark/tools/codegraph/` |

### Manual Inspection

| TC | Description | Proof Method | Proof Command |
|----|-------------|-------------|---------------|
| TC-007 | No-dangling-edges invariant expressed in verify block | manual | Inspect verify block in `specs/infra/code_graph.ark` |
| TC-022 | HTML contains code-graph nodes with correct styling | manual | Inspect generated HTML for function/class nodes |
| TC-023 | LOD switching works in visualization | manual | Open HTML, zoom in/out to verify LOD |
| TC-027 | Test strategy document exists and covers all TCs | manual | Inspect this file (`test-strategy.md`) |

### Proof-of-Concept

| TC | Description | Proof Method | Proof Command |
|----|-------------|-------------|---------------|
| TC-020 | Verification integrates with ark.py verify for code_graph.ark | poc | `python ark.py verify specs/infra/code_graph.ark` |
| TC-026 | At least one query returns meaningful results on self-indexed graph | poc | `python ark.py codegraph query callers parse` |

### Aggregate

| TC | Description | Proof Method | Proof Command |
|----|-------------|-------------|---------------|
| TC-028 | All autotest TCs have passing tests | autotest | `pytest tests/test_codegraph_*.py -q` |

## Summary by Proof Method

| Method | Count | TC IDs |
|--------|-------|--------|
| autotest | 21 | TC-001, TC-002, TC-003, TC-004, TC-005, TC-006, TC-008, TC-009, TC-010, TC-011, TC-012, TC-013, TC-014, TC-015, TC-016, TC-017, TC-018, TC-019, TC-021, TC-024, TC-025, TC-028 |
| poc | 2 | TC-020, TC-026 |
| manual | 4 | TC-007, TC-022, TC-023, TC-027 |

## Test Files Summary

| Test File | TCs Covered | Subsystem |
|-----------|-------------|-----------|
| `tests/test_codegraph_store.py` | TC-015 | Graph store CRUD and serialization |
| `tests/test_codegraph_python.py` | TC-012, TC-016 | Python AST parser + complexity |
| `tests/test_codegraph_rust.py` | TC-013 | Rust regex parser |
| `tests/test_codegraph_ark.py` | TC-014 | Ark adapter (wraps ark_parser) |
| `tests/test_codegraph_queries.py` | TC-003, TC-009 | Schema coverage + EXPR_PRIMITIVES |
| `tests/test_codegraph_verify.py` | TC-018, TC-019 | Graph invariant checks |
| `tests/test_codegraph_integration.py` | TC-024, TC-025 | End-to-end self-indexing |

## Tooling

- **Framework**: pytest (already used by Ark)
- **Fixtures**: each parser test file creates small in-memory source snippets, parses them, asserts on extracted nodes/edges
- **Integration tests**: use `R:/Sandbox/ark/` as the real source tree
- **CLI tests**: subprocess calls to `python ark.py codegraph ...`, assert exit code 0 and output file existence

## Execution Order

Tests should run in dependency order:
1. `test_codegraph_store.py` -- foundational data structure
2. `test_codegraph_queries.py` -- schema and primitives
3. `test_codegraph_python.py` -- first parser
4. `test_codegraph_rust.py` -- second parser
5. `test_codegraph_ark.py` -- third parser
6. `test_codegraph_verify.py` -- invariant checks (needs store + parser)
7. `test_codegraph_integration.py` -- end-to-end (needs all of the above)
8. Parse/CLI commands -- run last as they need all components installed
