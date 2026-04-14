# Visual Codegen — Design

## Overview
Create `tools/codegen/visual_codegen.py` that generates output artifacts from visual items: Mermaid `.mmd` files from diagrams, HTML preview files from previews, annotation overlay JSON from annotations, review CLI commands from visual_review specs, and screenshot catalog index from screenshot metadata.

## Target Files
- `ark/tools/codegen/visual_codegen.py` — Visual domain code generation module

## Approach

### Generated Artifacts

| Item Type | Output | Description |
|-----------|--------|-------------|
| diagram | `{name}.mmd` | Mermaid markup file |
| preview | `{name}.html` | Self-contained HTML preview |
| annotation | `{name}_overlay.json` | Annotation overlay JSON |
| visual_review | `{name}_review.sh` | Review CLI command script |
| screenshot | `catalog_index.html` | Screenshot catalog HTML index |
| render_config | `{name}_config.json` | Render configuration JSON |

### Functions
```python
def gen_visual(ark_file, out_dir: Path = None) -> dict:
    """Generate all visual artifacts from an ArkFile.
    
    Returns:
        {"filename": "content"} dict
    """

def gen_diagram_mmd(diagram: dict) -> str:
    """Generate Mermaid markup from a diagram item."""

def gen_preview_html(preview: dict) -> str:
    """Generate self-contained HTML from a preview item."""

def gen_annotation_json(annotation: dict) -> str:
    """Generate annotation overlay JSON from an annotation item."""

def gen_review_script(visual_review: dict) -> str:
    """Generate a review CLI script from a visual_review item."""

def gen_catalog_index(screenshots: list) -> str:
    """Generate an HTML catalog index from screenshot items."""

def gen_render_config_json(render_config: dict) -> str:
    """Generate render configuration JSON."""
```

### Design Decisions
- Follows `studio_codegen.py` pattern (function takes ArkFile, returns filename->content dict)
- Output files written to `out_dir` if specified, otherwise returned as dict
- Review script generates `ark visual review` commands
- Catalog index is a static HTML page with thumbnail grid
- New codegen target: `visual` alongside existing `rust`/`cpp`/`proto`/`studio`

## Dependencies
- design-grammar-dsl-surface (visual items must parse)
- design-visual-runner (CLI integration)

## Target Conditions
- TC-030: Codegen produces `.mmd` files from diagram items
- TC-031: Codegen produces `.html` files from preview items
- TC-032: Codegen produces annotation overlay JSON from annotation items
- TC-033: Codegen produces render config JSON from render_config items
