# Visual Runner (Orchestrator) — Design

## Overview
Create `tools/visual/visual_runner.py` as the top-level orchestrator for the visual pipeline. Reads visual specs from parsed AST, dispatches to appropriate renderers/managers, orchestrates review cycles, and integrates with the Ark CLI.

## Target Files
- `ark/tools/visual/visual_runner.py` — Top-level visual pipeline orchestrator
- `ark/ark.py` — Add `visual` CLI subcommand with render/review/search/catalog sub-commands

## Approach

### Visual Pipeline Stages
1. Parse visual items from AST (diagrams, previews, annotations, visual_reviews, screenshots, visual_searches, render_configs)
2. Resolve render_config references (named configs referenced by other items)
3. Dispatch rendering: diagrams -> mermaid_renderer, previews -> html_previewer
4. Process annotations: annotation items -> annotator
5. Register screenshots: screenshot items -> screenshot_manager
6. Execute searches: visual_search items -> search
7. Run review loops: visual_review items -> review_loop
8. Report results

### Functions
```python
def run_visual_pipeline(ark_file, out_dir: Path, mode: str = "all") -> dict:
    """Run the complete visual pipeline on parsed .ark file.
    
    Args:
        ark_file: Parsed ArkFile (from ark_parser)
        out_dir: Output directory for generated artifacts
        mode: "all" | "render" | "review" | "search" | "catalog"
    
    Returns:
        {"diagrams": int, "previews": int, "annotations": int, 
         "reviews": int, "screenshots": int, "searches": int, "errors": list}
    """

def extract_visual_items(ast_json: dict) -> dict:
    """Group visual items by type from AST JSON."""

def resolve_render_configs(items: dict) -> dict:
    """Resolve render_config references to actual config dicts."""

def dispatch_renderers(items: dict, configs: dict, out_dir: Path) -> dict:
    """Dispatch items to appropriate renderers."""
```

### CLI Integration
```
ark visual render   <file.ark> [--out <dir>]  — render all diagrams + previews
ark visual review   <file.ark>                — start review cycles
ark visual search   <file.ark> [--query Q]    — execute visual searches
ark visual catalog  <file.ark> [--out <file>] — generate screenshot catalog
ark visual pipeline <file.ark> [--out <dir>]  — run full visual pipeline
```

### Design Decisions
- visual_runner is the single entry point for all visual operations
- CLI follows existing pattern (cmd_studio, cmd_codegraph)
- Modes allow running subsets of the pipeline (render-only, search-only, etc.)
- Error handling: collect errors, continue processing, report at end
- Output directory structure: `generated/visual/{diagrams,previews,annotations,screenshots}/`

## Dependencies
- All renderer designs (mermaid, html, annotator, review_loop, screenshot_manager, search)

## Target Conditions
- TC-022: Visual runner dispatches diagram items to mermaid renderer
- TC-023: Visual runner dispatches preview items to html previewer
- TC-024: CLI `ark visual` subcommand works with all sub-commands
