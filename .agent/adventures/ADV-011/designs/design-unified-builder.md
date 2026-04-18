# Unified Builder — Design

## Overview

Specifies the unified transformation layer: one codegen pipeline, one verify
harness with plugin verifiers, one visualizer, one impact/diff surface. The
builder consumes a descriptor AST and produces checked artefacts and
visualisations.

## Target Files

- `.agent/adventures/ADV-011/designs/design-unified-builder.md` (this file)
- `.agent/adventures/ADV-011/research/builder-delta.md` — per-tool delta:
  which current `tools/verify/*`, `tools/codegen/*`, `tools/visualizer/*`
  modules dissolve, merge, or remain. NEW.

## Approach

### 1. Verify harness — single plugin registrar

Current state: one verifier file per domain
(`ark_verify.py`, `studio_verify.py`, `evolution_verify.py`,
`agent_verify.py`, `visual_verify.py`, `graph_verify.py`, `expression_smt.py`).
Each holds domain-specific Z3 passes.

Unified design:

- A single `ark_verify.Harness` with a plugin registry
  `register_pass(name, applies_to, run)`.
- Domain verifiers become plugins (no reduction in Z3 logic — the logic moves;
  the dispatcher unifies).
- Canonical shared passes exposed as stdlib primitives:
  - `verify.dag_acyclicity(node_kind, edge_kind)` — unifies ADV-003 studio
    escalation + ADV-006 visual_review cycle + any future DAG.
  - `verify.opaque_primitive(name, kind)` — unifies PASS_OPAQUE usage across
    ADV-002/003/004/006/008.
  - `verify.numeric_interval(sym, lo, hi)` — unifies ADV-001 numeric predicate
    checks + ADV-004 weights-sum-to-1 + ADV-005 resource-limits-positive +
    ADV-006 viewport-bounds.
  - `verify.reference_exists(ref, target_index)` — unifies every "X references
    an existing Y" check across domains.
- Each domain plugin declares which shared passes it composes plus its
  domain-specific passes (e.g. shape_grammar termination — stays a plugin but
  uses the opaque-primitive registrar).

### 2. Codegen pipeline — one backend per target language

Current state: `ark_codegen.py`, `studio_codegen.py`, `evolution_codegen.py`,
`agent_codegen.py`, `visual_codegen.py`, per-adventure Rust/Python emitters.

Unified design:

- A single `Codegen.Pipeline` with two stages: **normaliser** (AST → canonical
  IR) and **emitter** (IR → target language). The emitter is per-target, not
  per-domain.
- Targets in v1: Python (for runtime tools and stdlib glue), Rust (for the
  ark-dsl crate + orchestrator + runtime). Others stubbed (ADV-001 pattern:
  `NotImplementedError` with a pointer to a follow-up adventure).
- Domain-specific emission (e.g. Claude subagent markdown from `role` items,
  cron entries from `cron_task`) becomes a target like any other:
  `claude-agent-md`, `cron-entry`, `json-config`. Each is a plugin under the
  emitter.

### 3. Visualizer — LOD model unification

`ark_visualizer.py` already renders entity/bridge graphs. Unified design adds
LOD layers for every domain (studio org-chart, evolution pipeline, agent
architecture, visual pipeline, code-graph callers) as *pluggable overlays*
rather than separate tools. The existing `tools/visual/*` rendering code
(mermaid, annotator) stays in its place; the unified visualizer calls it
through the overlay interface.

### 4. Impact + diff — already shared surfaces

`ark_impact.py` and `ark_diff.py` already work at the AST level and need no
per-domain code. They remain as-is. The shape_grammar adapters (ADV-008 T17)
become the canonical "external-consumer adapter" template documented in this
design.

### 5. Dependency direction

Descriptor → Builder (one-way). Builder never imports controller. This
reinforces ADV-008's one-way package dependency pattern at the module level.

## Dependencies

- `design-unified-descriptor.md` (AST contract)
- `design-deduplication-matrix.md` (verify plugin rows)

## Target Conditions

- This design specifies at least the four canonical shared verify passes
  (`dag_acyclicity`, `opaque_primitive`, `numeric_interval`, `reference_exists`).
- `builder-delta.md` classifies every current `tools/verify/*`,
  `tools/codegen/*` module as `KEEP | MERGE-INTO-HARNESS | RETIRE`.
- Every dedup row with `assigned_bucket = builder` is cited at its resolution
  point in this design.
