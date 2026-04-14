# Mermaid Renderer — Design

## Overview
Create `tools/visual/mermaid_renderer.py` that renders Mermaid diagram specs from parsed `diagram` items to SVG or PNG output files. This is the primary rendering backend for architecture, sequence, flowchart, and other Mermaid-supported diagram types.

## Target Files
- `ark/tools/visual/__init__.py` — Package init for visual tools
- `ark/tools/visual/mermaid_renderer.py` — Mermaid rendering module

## Approach

### Rendering Strategy
For v1, generate `.mmd` (Mermaid markup) files from diagram item source content. Optionally invoke the `mmdc` (mermaid-cli) command if available to produce SVG/PNG output. If `mmdc` is not installed, output the `.mmd` file with instructions.

### Functions
```python
def render_mermaid(diagram_ast: dict, render_config: dict, out_dir: Path) -> dict:
    """Render a diagram item to .mmd and optionally .svg/.png.
    
    Args:
        diagram_ast: Parsed diagram item from AST
        render_config: Render configuration (format, theme, etc.)
        out_dir: Output directory
    
    Returns:
        {"mmd_path": Path, "output_path": Path|None, "format": str}
    """

def generate_mermaid_source(diagram_type: str, source: str) -> str:
    """Generate valid Mermaid markup from diagram type and source content."""

def validate_mermaid_syntax(mmd_content: str) -> list[str]:
    """Basic syntax validation of Mermaid markup. Returns list of errors."""
```

### Integration
- Called by `visual_runner.py` when processing `diagram` items with type `mermaid`
- Output stored under `generated/visual/` directory
- Supports themes: default, dark, forest, neutral

### Design Decisions
- Generate `.mmd` files as the primary output (always works, no dependencies)
- SVG/PNG rendering is optional (requires `mmdc` CLI tool)
- Validate Mermaid syntax with basic checks (graph/sequenceDiagram keywords, bracket matching)
- Theme applied via Mermaid configuration JSON

## Dependencies
- design-grammar-dsl-surface (diagram item must parse)

## Target Conditions
- TC-008: Mermaid renderer generates valid `.mmd` files from diagram items
- TC-009: Renderer handles all DiagramType variants (flowchart, sequence, architecture, etc.)
- TC-010: Invalid Mermaid source produces meaningful error messages
