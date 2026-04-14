# Screenshot Manager — Design

## Overview
Create `tools/visual/screenshot_manager.py` that manages a screenshot library with metadata, tagging, and indexing. Handles `screenshot` items from the AST and maintains a catalog JSON file for querying.

## Target Files
- `ark/tools/visual/screenshot_manager.py` — Screenshot management module

## Approach

### Screenshot Catalog
Maintain a JSON catalog file (`visual_catalog.json`) in the output directory that indexes all screenshots with metadata, tags, and descriptions.

### Functions
```python
def register_screenshot(screenshot_ast: dict, catalog_path: Path) -> dict:
    """Register a screenshot item in the catalog.
    
    Returns:
        {"id": str, "path": Path, "tags": list, "registered": bool}
    """

def load_catalog(catalog_path: Path) -> dict:
    """Load the screenshot catalog. Creates empty catalog if not found."""

def save_catalog(catalog: dict, catalog_path: Path) -> None:
    """Save the screenshot catalog to disk."""

def list_screenshots(catalog: dict, tags: list = None) -> list:
    """List screenshots, optionally filtered by tags."""

def get_screenshot(catalog: dict, name: str) -> dict:
    """Get a screenshot entry by name."""

def generate_catalog_index(catalog: dict, out_dir: Path) -> Path:
    """Generate an HTML index page for the screenshot catalog."""
```

### Catalog Schema
```json
{
    "version": 1,
    "screenshots": {
        "name": {
            "path": "relative/path.png",
            "timestamp": "ISO8601",
            "source": "description of source",
            "tags": ["architecture", "workflow"],
            "description": "human-readable description",
            "width": 1920,
            "height": 1080
        }
    }
}
```

### Design Decisions
- JSON catalog for persistence (no database dependency)
- Screenshots referenced by name (IDENT from the AST)
- Tags use VisualTag enum values for consistency
- HTML index page generated for browsing catalog
- Catalog is append-only (no automatic deletion)

## Dependencies
- design-grammar-dsl-surface (screenshot item must parse)

## Target Conditions
- TC-018: Screenshot manager registers entries in catalog correctly
- TC-019: Catalog persistence (load/save round-trip) works correctly
