# Visualization — Design

## Overview
Extend the Ark visualizer to render evolution pipeline graphs: directed graphs showing the flow from evolution_target through dataset, optimizer, candidates, gate, to output. Also render fitness trajectory charts for completed runs.

## Target Files
- `ark/tools/visualizer/ark_visualizer.py` — Extend with evolution pipeline graph rendering

## Approach

### Evolution Pipeline Graph

Extend `generate_graph_data()` to extract evolution nodes and edges:

**Nodes:**
- `evolution_target` — kind: "evolution_target", tier info
- `eval_dataset` — kind: "eval_dataset", source type
- `fitness_function` — kind: "fitness_function", dimension count
- `optimizer` — kind: "optimizer", engine type
- `benchmark_gate` — kind: "benchmark_gate", tolerance
- `evolution_run` — kind: "evolution_run", status
- `constraint` — kind: "constraint", enforcement level

**Edges (from evolution_run references):**
- evolution_run -> evolution_target (edge kind: "evolves")
- evolution_run -> eval_dataset (edge kind: "uses_dataset")
- evolution_run -> optimizer (edge kind: "uses_optimizer")
- evolution_run -> benchmark_gate (edge kind: "gates_through")
- evolution_target -> constraint (edge kind: "constrained_by")
- eval_dataset -> fitness_function (edge kind: "scored_by")

### Visual Styling
- Evolution nodes get a distinct color group (purple/violet family to distinguish from existing blue/green entity nodes)
- Edge styles: dashed for constraint edges, solid for data flow edges
- Node shapes: evolution items rendered as rounded rectangles (vs circles for entities)

### HTML Template Extension
Add evolution-specific rendering in the d3.js template:
- Color mapping for evolution node kinds
- Tooltip showing key properties (tier, engine, tolerance, etc.)
- LOD level 3 (zoomed in): show all fields
- LOD level 2: show name + kind
- LOD level 1 (zoomed out): show only evolution_run nodes as summary

### Design Decisions
- Reuse existing d3.js force-directed layout — evolution nodes participate in the same graph
- No separate HTML page — evolution items appear alongside entity/island/studio nodes
- Fitness trajectory charts are deferred to codegen reports (markdown tables, not d3)
- Keep visualization read-only (no interactive evolution triggering from the graph)

## Dependencies
- design-dsl-surface (evolution AST items for graph data extraction)

## Target Conditions
- TC-037: Visualizer extracts evolution nodes and edges from parsed AST
- TC-038: Generated HTML includes evolution-specific color coding and tooltips
- TC-039: `ark graph <spec>` renders evolution items when present in spec
