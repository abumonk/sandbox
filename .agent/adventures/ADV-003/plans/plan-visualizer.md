# Visualization — Org-Chart

## Designs Covered
- design-visualizer-orgchart: Org-chart visualization for studio hierarchies

## Tasks

### Add org-chart rendering to visualizer
- **ID**: ADV003-T010
- **Description**: Extend ark_visualizer.py to extract studio/role data from AST and render an org-chart. Add tier-based node grouping, escalation edges, role coloring by tier, and a toggle between entity-graph and org-chart views in the HTML template.
- **Files**: tools/visualizer/ark_visualizer.py
- **Acceptance Criteria**:
  - Org-chart nodes render for all roles grouped by tier
  - Escalation edges displayed as directional arrows
  - Tier-based coloring (Director=gold, Lead=blue, Specialist=green)
  - Toggle button switches between entity-graph and org-chart
  - LOD levels work (zoom out=summary, zoom in=details)
- **Target Conditions**: TC-020, TC-021, TC-022
- **Depends On**: [ADV003-T005]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, d3js, html
  - Estimated duration: 25min
  - Estimated tokens: 30000
