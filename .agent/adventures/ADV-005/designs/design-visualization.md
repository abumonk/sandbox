# Agent Visualization — Design

## Overview
Extend the Ark visualizer (`tools/visualizer/ark_visualizer.py`) to render agent architecture diagrams: agent <-> gateway <-> platforms, with execution backend and skill inventory panels.

## Target Files
- `ark/tools/visualizer/ark_visualizer.py` — Extend with agent graph generation

## Approach

### Graph Nodes
- **Agent** node (central, colored distinctly)
- **Platform** nodes (one per platform, grouped)
- **Gateway** node (hub connecting agent to platforms)
- **ExecutionBackend** nodes (connected to agent)
- **Skill** nodes (inventory panel, grouped by status)
- **ModelConfig** node (connected to agent)
- **CronTask** nodes (connected to agent + delivery platform)

### Graph Edges
- Agent -> Gateway (labeled "messaging")
- Gateway -> Platform (labeled per route format)
- Agent -> ExecutionBackend (labeled "execution")
- Agent -> ModelConfig (labeled "model")
- Agent -> Skill (labeled "skill inventory")
- CronTask -> Agent (labeled "scheduled by")
- CronTask -> Platform (labeled "delivers to")

### Rendering
Extend `generate_graph_data()` to detect agent items and add them to the graph data structure. The HTML renderer already handles arbitrary nodes/edges, so the main work is:

1. Detect agent-related items in AST
2. Generate node entries with appropriate colors/shapes
3. Generate edge entries with labels
4. Group skills into a sub-cluster by status

### Color Scheme
- Agent: #4A90D9 (blue)
- Platform: #7B68EE (purple)
- Gateway: #20B2AA (teal)
- ExecutionBackend: #FF8C00 (orange)
- Skill: #32CD32 (green), #FFD700 (improving), #808080 (deprecated)
- ModelConfig: #DC143C (crimson)
- CronTask: #9370DB (medium purple)

### Design Decisions
- Reuse existing visualizer infrastructure (D3.js force graph)
- Agent-specific nodes get distinct shapes: agent=diamond, gateway=hexagon
- Skills grouped in a collapsible panel (LOD level 2+)
- No new dependencies; all within existing HTML template

## Dependencies
- design-dsl-surface (parser must produce agent items in AST)

## Target Conditions
- TC-035: Visualizer generates graph data with agent nodes and edges
- TC-036: HTML output renders agent architecture with correct colors and labels
