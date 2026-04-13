# Graph Visualization — Design

## Overview

Extend the existing `ark_visualizer.py` to render code graph data alongside the existing
Ark entity graph. Add a new LOD level for code-graph nodes (functions, classes, call edges)
and integrate with the existing d3-based HTML visualization.

## Target Files

- `R:/Sandbox/ark/tools/visualizer/ark_visualizer.py` — extend `generate_graph_data()`
  to accept code graph JSON and merge nodes/edges
- `R:/Sandbox/ark/tools/codegraph/visualizer.py` (NEW) — code-graph-specific visualization
  helpers (color schemes, node shapes, filtering)
- `R:/Sandbox/ark/ark.py` — add `codegraph graph` subcommand

## Approach

### Extended Graph Data

The existing visualizer produces nodes with `kind` field (abstraction, class, island,
bridge). Extend to include:
- `kind: "function"` — blue circles, smaller than entity nodes
- `kind: "cg_class"` — purple circles (distinct from Ark class)
- `kind: "module"` — green rectangles
- `kind: "method"` — small blue dots inside class groups

Edge kinds extended:
- `kind: "calls"` — dashed arrows
- `kind: "imports"` — dotted arrows
- `kind: "cg_inherits"` — solid arrows (distinct color from Ark inherits)

### LOD Levels

- **LOD 1 (zoomed out)**: modules only, import edges between them
- **LOD 2 (medium)**: modules + classes, inheritance + import edges
- **LOD 3 (zoomed in)**: all nodes including functions/methods, call edges visible

### CLI Integration

```
ark codegraph graph <path> [--output graph.html]
```

Indexes the path, generates graph data, produces HTML visualization.

### Combined View

When run on an `.ark` file that has both Ark entities and a code graph, the visualizer
produces a unified view with two node groups (Ark entities on top, code graph below)
connected by bridge edges where Ark entities reference implementation code.

## Dependencies

- design-python-indexer (produces graph data to visualize)

## Target Conditions

- TC-021: `ark codegraph graph` produces a valid HTML file
- TC-022: HTML contains code-graph nodes (functions, classes) with correct styling
- TC-023: LOD switching works (zoom in/out changes visible detail level)
