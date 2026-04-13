# Org-Chart Visualization — Design

## Overview
Extend the Ark visualizer to render studio hierarchy org-charts alongside the existing entity/bridge graphs. The org-chart shows roles organized by tier with escalation edges.

## Target Files
- `tools/visualizer/ark_visualizer.py` — Add studio org-chart rendering to generate_graph_data() and the HTML template

## Approach

### Graph Data Extraction
When studio items are present in the AST, extract:
- Nodes: one per role, colored by tier (Director=gold, Lead=blue, Specialist=green)
- Groups: tier-based horizontal bands
- Edges: escalates_to links (upward arrows), same-tier collaboration lines
- Studio container as a bounding box

### LOD Levels
- LOD 0 (zoomed out): Studio name + tier count summary
- LOD 1 (medium): Roles as labeled nodes grouped by tier
- LOD 2 (zoomed in): Full role details (skills, tools, responsibilities)

### HTML/JS Integration
Add a new `renderOrgChart()` function in the HTML template that uses d3.js force-directed layout with tier-based y-axis constraints. Add a toggle button to switch between entity graph and org-chart views.

### Data Shape
```json
{
  "orgchart": {
    "studio": "ArkStudio",
    "tiers": [
      {
        "level": 1, "name": "Directors",
        "roles": [{"name": "...", "escalates_to": null, "skills": [...]}]
      }
    ],
    "edges": [
      {"from": "Implementer", "to": "TechLead", "type": "escalation"}
    ]
  }
}
```

## Dependencies
- design-parser-support (need parsed studio AST)

## Target Conditions
- TC-020: Org-chart nodes render for all roles grouped by tier
- TC-021: Escalation edges render correctly between roles
- TC-022: LOD toggle works between entity graph and org-chart
