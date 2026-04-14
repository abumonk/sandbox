# Reflexive Specs & Visualizer Extension

## Designs Covered
- design-reflexive-visualization: Visual island spec, example specs, visualizer extension

## Tasks

### Author visual island spec and example visual specs
- **ID**: ADV006-T017
- **Description**: Create `ark/specs/infra/visual_island.ark` defining the visual communication island with classes for MermaidRenderer, HtmlPreviewer, Annotator, ReviewLoop, ScreenshotManager, VisualSearch. Create `ark/specs/examples/visual_examples.ark` with example diagrams of Ark's own architecture (island topology, pipeline flow, visual pipeline itself). Register VisualIsland in `ark/specs/root.ark` SystemRegistry.
- **Files**: `ark/specs/infra/visual_island.ark`, `ark/specs/examples/visual_examples.ark`, `ark/specs/root.ark`
- **Acceptance Criteria**:
  - Visual island spec parses via `python ark.py parse`
  - Visual island verifies via `python ark.py visual verify`
  - Example specs produce rendered output via `ark visual render`
  - VisualIsland registered in root.ark SystemRegistry
  - Example diagrams accurately represent Ark architecture
- **Target Conditions**: TC-034, TC-035, TC-037
- **Depends On**: [ADV006-T002, ADV006-T005, ADV006-T014, ADV006-T016]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: ark-dsl, architecture knowledge
  - Estimated duration: 20min
  - Estimated tokens: 25000

### Extend visualizer for visual pipeline items
- **ID**: ADV006-T018
- **Description**: Update `ark/tools/visualizer/ark_visualizer.py` to render visual items in the HTML graph. Add diagram nodes (with type indicator), preview nodes (viewport indicator), visual_review nodes (target connection, feedback status), screenshot nodes, and render_config nodes. Follow existing LOD pattern.
- **Files**: `ark/tools/visualizer/ark_visualizer.py`
- **Acceptance Criteria**:
  - Diagram items appear as nodes in HTML graph
  - Preview items appear with viewport indicators
  - Visual review items show target connections
  - Screenshot items appear with tags
  - Render config items linked to referencing items
  - No regression in existing visualizer behavior
- **Target Conditions**: TC-036
- **Depends On**: [ADV006-T005]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, d3.js, HTML visualization
  - Estimated duration: 20min
  - Estimated tokens: 25000
