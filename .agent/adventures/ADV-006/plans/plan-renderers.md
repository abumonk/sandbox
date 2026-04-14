# Renderers — Mermaid, HTML Previewer, Annotator

## Designs Covered
- design-mermaid-renderer: Mermaid diagram rendering
- design-html-previewer: HTML preview rendering
- design-annotator: Image annotation

## Tasks

### Create visual tools package and Mermaid renderer
- **ID**: ADV006-T006
- **Description**: Create `ark/tools/visual/` package with `__init__.py` and `mermaid_renderer.py`. Implement `render_mermaid()`, `generate_mermaid_source()`, and `validate_mermaid_syntax()`. Support all DiagramType variants. Generate `.mmd` files from diagram items, with optional mmdc CLI invocation for SVG/PNG.
- **Files**: `ark/tools/visual/__init__.py`, `ark/tools/visual/mermaid_renderer.py`
- **Acceptance Criteria**:
  - Package importable: `from visual.mermaid_renderer import render_mermaid`
  - Generates valid .mmd files from diagram AST items
  - Handles all DiagramType variants (mermaid, flowchart, sequence, architecture, etc.)
  - Invalid source returns meaningful error messages
  - Works without mmdc installed (generates .mmd only)
- **Target Conditions**: TC-008, TC-009, TC-010
- **Depends On**: [ADV006-T005]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, mermaid
  - Estimated duration: 20min
  - Estimated tokens: 25000

### Create HTML previewer
- **ID**: ADV006-T007
- **Description**: Create `ark/tools/visual/html_previewer.py`. Implement `render_preview()` and `generate_html_template()`. Support viewport configuration (mobile/tablet/desktop/custom), static and interactive modes, and theme settings. Generate self-contained HTML files.
- **Files**: `ark/tools/visual/html_previewer.py`
- **Acceptance Criteria**:
  - Generates valid self-contained HTML files from preview items
  - Viewport meta tags set correctly for all ViewportSize variants
  - Static mode produces clean HTML, interactive mode includes JS
  - Theme applied via CSS variables
- **Target Conditions**: TC-011, TC-012
- **Depends On**: [ADV006-T005]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: python, html, css
  - Estimated duration: 15min
  - Estimated tokens: 20000

### Create image annotator
- **ID**: ADV006-T008
- **Description**: Create `ark/tools/visual/annotator.py`. Implement `annotate_image()` with support for rect, arrow, text, blur, highlight, circle elements using Pillow (PIL). Implement `validate_bounds()` for coordinate checking. Handle element layering (painter's algorithm).
- **Files**: `ark/tools/visual/annotator.py`
- **Acceptance Criteria**:
  - Applies rect, arrow, text, blur elements to images correctly
  - Bounds validation returns warnings for out-of-bounds coordinates
  - Elements layered in order (painter's algorithm)
  - Works with PNG and JPEG input images
  - Graceful handling when Pillow is not installed (import warning, skip rendering)
- **Target Conditions**: TC-013, TC-014
- **Depends On**: [ADV006-T005]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: python, pillow/PIL, image processing
  - Estimated duration: 20min
  - Estimated tokens: 25000
