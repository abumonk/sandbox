# Annotator — Design

## Overview
Create `tools/visual/annotator.py` that applies annotation layers to images. Supports rectangles, arrows, text overlays, blur regions, highlights, and circles using Pillow (PIL). Reads `annotation` items from the AST and produces annotated image files.

## Target Files
- `ark/tools/visual/annotator.py` — Image annotation module

## Approach

### Annotation Pipeline
1. Load base image (screenshot, rendered diagram, preview capture)
2. Parse annotation elements from the AST
3. Apply each element in order (layered compositing)
4. Save annotated output image

### Functions
```python
def annotate_image(annotation_ast: dict, base_image_path: Path, out_dir: Path) -> dict:
    """Apply annotations from an annotation item to a base image.
    
    Returns:
        {"output_path": Path, "element_count": int, "errors": list}
    """

def draw_rect(draw, position: dict, color: str, opacity: float) -> None:
    """Draw a rectangle annotation."""

def draw_arrow(draw, endpoints: dict, color: str, width: int) -> None:
    """Draw an arrow annotation."""

def draw_text(draw, position: dict, label: str, color: str, font_size: int) -> None:
    """Draw a text annotation."""

def apply_blur(image, position: dict, radius: int) -> Image:
    """Apply Gaussian blur to a rectangular region."""

def draw_highlight(draw, position: dict, color: str, opacity: float) -> None:
    """Draw a semi-transparent highlight rectangle."""

def validate_bounds(position: dict, image_size: tuple) -> list[str]:
    """Validate annotation coordinates within image bounds."""
```

### Design Decisions
- Pillow (PIL) for image manipulation — no heavy dependencies
- Elements applied in order (painter's algorithm)
- Blur uses PIL's GaussianBlur filter on a cropped region
- Bounds validation returns warnings, does not block rendering (clamp to image bounds)
- Output format matches input format (PNG for PNG, etc.)

## Dependencies
- design-grammar-dsl-surface (annotation item must parse)

## Target Conditions
- TC-013: Annotator applies rect, arrow, text, blur elements correctly
- TC-014: Annotation coordinates validated against viewport/image bounds
