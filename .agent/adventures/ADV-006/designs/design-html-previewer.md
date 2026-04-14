# HTML Previewer — Design

## Overview
Create `tools/visual/html_previewer.py` that renders HTML preview specs from parsed `preview` items to self-contained HTML files. Supports viewport configuration and static/interactive modes.

## Target Files
- `ark/tools/visual/html_previewer.py` — HTML preview rendering module

## Approach

### Rendering Strategy
Generate self-contained HTML files from preview items. The source content is embedded in an HTML template with viewport meta tags, optional interactive features, and configured styling.

### Functions
```python
def render_preview(preview_ast: dict, render_config: dict, out_dir: Path) -> dict:
    """Render a preview item to a self-contained HTML file.
    
    Returns:
        {"html_path": Path, "viewport": str, "mode": str}
    """

def generate_html_template(source: str, viewport: str, mode: str, theme: str) -> str:
    """Generate self-contained HTML with viewport configuration."""

VIEWPORT_SIZES = {
    "mobile": (375, 667),
    "tablet": (768, 1024),
    "desktop": (1920, 1080),
}
```

### Design Decisions
- Self-contained HTML (inline CSS/JS, no external dependencies)
- Viewport meta tag set according to ViewportSize enum
- Static mode: rendered HTML snapshot; Interactive mode: includes JS event handlers
- Theme support via CSS variables in the template

## Dependencies
- design-grammar-dsl-surface (preview item must parse)

## Target Conditions
- TC-011: HTML previewer generates valid self-contained HTML files
- TC-012: Viewport sizes correctly configured (mobile/tablet/desktop/custom)
