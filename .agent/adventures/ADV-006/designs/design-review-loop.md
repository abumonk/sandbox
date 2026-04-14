# Visual Review Loop — Design

## Overview
Create `tools/visual/review_loop.py` that orchestrates the visual review cycle: render a visual artifact, present it to the user, collect structured feedback (approve/reject/annotate), and return JSON. This is the core human-in-the-loop mechanism.

## Target Files
- `ark/tools/visual/review_loop.py` — Review cycle orchestration module

## Approach

### Review Cycle Flow
1. Receive `visual_review` item from AST
2. Resolve the target (diagram, preview, or screenshot by name)
3. Render the target using the appropriate renderer
4. Generate a review manifest JSON file (path, metadata, feedback template)
5. Write the review manifest to a well-known location
6. Wait for feedback file (polling or file-based signaling)
7. Parse structured feedback JSON
8. Return feedback result to the pipeline

### Functions
```python
def run_review(visual_review_ast: dict, rendered_artifacts: dict, 
               out_dir: Path, timeout_seconds: int = 300) -> dict:
    """Orchestrate a visual review cycle.
    
    Args:
        visual_review_ast: Parsed visual_review item
        rendered_artifacts: Map of artifact name -> rendered path
        out_dir: Output directory for review files
        timeout_seconds: Max wait for feedback (default 5 minutes)
    
    Returns:
        {"status": str, "feedback": dict, "annotations": list, "duration_ms": int}
    """

def create_review_manifest(target_path: Path, review_name: str, 
                           feedback_mode: str, out_dir: Path) -> Path:
    """Create the review manifest JSON for human consumption."""

def wait_for_feedback(feedback_path: Path, timeout: int) -> dict:
    """Poll for feedback file. Returns parsed feedback or timeout result."""

def parse_feedback(feedback_path: Path) -> dict:
    """Parse structured feedback JSON file."""

FEEDBACK_TEMPLATE = {
    "status": "pending",    # pending | approved | rejected | changes_requested
    "comments": "",
    "annotations": [],
    "change_requests": []
}
```

### Design Decisions
- File-based communication (no GUI dependency) — review manifests and feedback as JSON files
- Timeout-based waiting with configurable duration
- Feedback template provides structure for human response
- Supports three feedback modes: `approve_reject` (binary), `annotate` (with markup), `full` (all fields)
- Review cycles are tracked to prevent circular feedback (acyclicity check in verification)

## Dependencies
- design-mermaid-renderer (renders diagrams for review)
- design-html-previewer (renders previews for review)
- design-annotator (applies annotation feedback)

## Target Conditions
- TC-015: Review loop creates valid manifest JSON with target artifact path
- TC-016: Feedback parsing handles all FeedbackStatus variants
- TC-017: Review cycle prevents circular feedback (acyclicity verification)
