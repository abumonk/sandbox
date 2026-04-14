# Reflexive Visualization & Visualizer Extension — Design

## Overview
Author `specs/infra/visual_island.ark` describing the visual communication island (Ark's own visual pipeline as a declarative spec). Extend the existing visualizer to render the visual pipeline itself. Author example visual specs that visualize Ark's own architecture.

## Target Files
- `ark/specs/infra/visual_island.ark` — Visual island spec (Ark describes its own visual layer)
- `ark/specs/examples/visual_examples.ark` — Example visual specs (diagrams of Ark architecture)
- `ark/tools/visualizer/ark_visualizer.py` — Extend to render visual pipeline items
- `ark/specs/root.ark` — Register VisualIsland in SystemRegistry

## Approach

### Visual Island Spec
Define the visual communication island following the island pattern from `root.ark`:

```ark
import stdlib.types
import stdlib.visual

island VisualIsland {
    strategy: code
    description: "Visual communication and human-in-the-loop review subsystem."
    
    contains: [MermaidRenderer, HtmlPreviewer, Annotator, ReviewLoop, 
               ScreenshotManager, VisualSearch]
    
    @in{ visual_spec: Path }
    #process[strategy: code] {
        description: "Process visual specs through render -> review -> feedback pipeline"
    }
    @out[]{ review_result: String }
}
```

### Example Visual Specs
Create diagrams of Ark's own architecture using the new visual items:
- Architecture overview diagram (islands + bridges)
- Pipeline flow diagram (parse -> verify -> codegen -> graph)
- Visual pipeline itself (specs -> renderers -> review -> feedback)

### Visualizer Extension
Add visual item rendering to `generate_graph_data()`:
- Diagram nodes (type indicator, connection to render_config)
- Preview nodes (viewport indicator)
- Visual review nodes (target connection, feedback status)
- Screenshot nodes (thumbnail placeholder)
- Render config nodes (configuration details)

### Design Decisions
- Reflexive use-case: Ark visualizes its own visual pipeline
- Visual island registered in root.ark's SystemRegistry
- Example specs serve as integration test fixtures
- Visualizer extension follows existing LOD pattern

## Dependencies
- design-grammar-dsl-surface (all visual items)
- design-visual-runner (CLI integration for running examples)
- design-visual-codegen (generating outputs from example specs)

## Target Conditions
- TC-034: Visual island spec parses and verifies without errors
- TC-035: Example visual specs produce valid rendered output
- TC-036: Visualizer renders visual pipeline items in HTML graph
- TC-037: VisualIsland registered in root.ark SystemRegistry
