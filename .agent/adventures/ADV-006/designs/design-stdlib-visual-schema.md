# Stdlib Visual Schema — Design

## Overview
Create `dsl/stdlib/visual.ark` defining struct and enum types for diagrams, previews, annotations, visual reviews, screenshots, visual search, render configs, and feedback. These are the data-model types that `.ark` specs reference when declaring visual communication artifacts.

## Target Files
- `ark/dsl/stdlib/visual.ark` — New stdlib file with all visual-related struct/enum definitions

## Approach

### Type Definitions

```ark
import stdlib.types

// ============================================================
// ENUMS
// ============================================================

// Diagram types supported by the visual layer
enum DiagramType {
    mermaid,
    flowchart,
    architecture,
    sequence,
    class_diagram,
    state,
    er,
    gantt
}

// Preview interaction modes
enum PreviewMode {
    static,         // rendered screenshot only
    interactive,    // live HTML with interaction
    responsive      // responsive viewport testing
}

// Annotation element types
enum AnnotationType {
    rect,
    arrow,
    text,
    blur,
    segment,
    highlight,
    circle,
    freehand
}

// Feedback status from human review
enum FeedbackStatus {
    pending,
    approved,
    rejected,
    changes_requested,
    annotated
}

// Render output format
enum RenderFormat {
    svg,
    png,
    html,
    pdf
}

// Viewport size presets
enum ViewportSize {
    mobile,       // 375x667
    tablet,       // 768x1024
    desktop,      // 1920x1080
    custom        // user-specified dimensions
}

// Search mode for visual search
enum SearchMode {
    keyword,      // text-based keyword matching
    tag,          // tag-based filtering
    semantic,     // embedding-based similarity (v2)
    combined      // keyword + tag
}

// Visual artifact tags for categorization
enum VisualTag {
    architecture,
    workflow,
    data_model,
    ui_mockup,
    screenshot,
    annotation,
    review,
    diagram
}

// ============================================================
// STRUCTS
// ============================================================

// Render configuration for visual artifacts
struct RenderConfig {
    format: RenderFormat,
    width: Int,
    height: Int,
    theme: String,
    background: String,
    scale: Float
}

// Spatial position for annotation elements
struct Position {
    x: Int,
    y: Int,
    width: Int,
    height: Int
}

// Arrow endpoint pair
struct ArrowEndpoints {
    start_x: Int,
    start_y: Int,
    end_x: Int,
    end_y: Int
}

// Annotation element (spatial markup on an image)
struct AnnotationElement {
    kind: AnnotationType,
    position: Position,
    label: String,
    color: String,
    opacity: Float
}

// Feedback response from human review
struct ReviewFeedback {
    status: FeedbackStatus,
    comments: String,
    annotations: [AnnotationElement],
    change_requests: [String],
    reviewer: String,
    timestamp: String
}

// Screenshot metadata
struct ScreenshotMeta {
    path: Path,
    timestamp: String,
    source: String,
    tags: [VisualTag],
    description: String,
    width: Int,
    height: Int
}

// Visual search query
struct SearchQuery {
    mode: SearchMode,
    query: String,
    tags: [VisualTag],
    max_results: Int
}

// Search result entry
struct SearchResult {
    path: Path,
    score: Float,
    tags: [VisualTag],
    description: String
}
```

### Design Decisions
- Use enums for closed sets (DiagramType, PreviewMode, AnnotationType, FeedbackStatus, RenderFormat, ViewportSize, SearchMode, VisualTag)
- Use structs for open data (RenderConfig, Position, AnnotationElement, ReviewFeedback, ScreenshotMeta, SearchQuery, SearchResult)
- Keep it flat — these types are referenced by grammar-level items (diagram, preview, annotation, visual_review, screenshot, visual_search)
- Follow existing stdlib pattern from types.ark and studio.ark

## Dependencies
- None (stdlib is standalone)

## Target Conditions
- TC-001: `dsl/stdlib/visual.ark` parses without errors via `python ark.py parse`
- TC-002: All enum and struct definitions are well-formed and referenceable from specs
