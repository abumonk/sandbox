# Visual Verification — Design

## Overview
Create `tools/verify/visual_verify.py` implementing Z3-based verification checks for visual communication items. Follows the existing studio_verify.py pattern as a separate domain module.

## Target Files
- `ark/tools/verify/visual_verify.py` — Visual domain Z3 verifier

## Approach

### Z3 Checks

1. **Diagram type validity** — Every `diagram` item's `type` field references a valid DiagramType enum variant.

2. **Visual review target resolution** — Every `visual_review` item's `target` references an existing diagram, preview, or screenshot name in the same file.

3. **Annotation bounds check** — When annotation element positions are specified and viewport bounds are known, all coordinates must be within bounds (x >= 0, y >= 0, x + width <= viewport_width, y + height <= viewport_height).

4. **Render config validity** — Render config items have positive integer width/height, scale > 0, and format is a valid RenderFormat variant.

5. **Review cycle acyclicity** — Visual review items must not form circular feedback loops. Uses Z3 ordinals (same pattern as studio escalation acyclicity from ADV-003).

### Functions
```python
def verify_visual(ast_json: dict) -> dict:
    """Run all visual verification checks.
    
    Returns:
        {"checks": [{"check": str, "status": str, "message": str}], 
         "summary": {"passed": int, "failed": int, "total": int}}
    """

def check_diagram_types(items: list) -> list:
    """Verify all diagram types are valid DiagramType variants."""

def check_review_targets(items: list, all_names: set) -> list:
    """Verify all visual_review targets reference existing items."""

def check_annotation_bounds(items: list) -> list:
    """Z3: verify annotation coordinates within viewport bounds."""

def check_render_configs(items: list) -> list:
    """Z3: verify render config constraints (positive dimensions, valid format)."""

def check_review_acyclicity(items: list) -> list:
    """Z3: verify no circular review feedback loops using ordinal assignment."""
```

### Design Decisions
- Separate module `visual_verify.py` (following `studio_verify.py` pattern)
- Called from the pipeline when `--target visual` or when visual items are detected
- Z3 ordinals for acyclicity (following Z3 ordinals decision from ADV-003)
- PASS_OPAQUE for complex rendering semantics (following ADV-002 decision)
- Return format matches `ark_verify.py` conventions

## Dependencies
- design-grammar-dsl-surface (visual items must parse)

## Target Conditions
- TC-025: Every diagram references a valid DiagramType
- TC-026: Every visual_review references an existing target
- TC-027: Annotation coordinates validated within bounds (Z3)
- TC-028: Render configs have valid positive dimensions (Z3)
- TC-029: Review cycles verified acyclic (Z3 ordinals)
