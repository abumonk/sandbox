## Processes

### VisualPipelineProcess
1. Parse .ark file containing visual items
2. Extract visual items by type (diagrams, previews, annotations, visual_reviews, screenshots, visual_searches, render_configs)
3. Resolve render_config references (named configs referenced by other items)
4. Dispatch rendering: diagrams -> mermaid_renderer, previews -> html_previewer
5. Process annotations: annotation items -> annotator (apply to rendered targets)
6. Register screenshots: screenshot items -> screenshot_manager (update catalog)
7. Execute searches: visual_search items -> search (query catalog)
8. Run review loops: visual_review items -> review_loop (render -> present -> feedback)
9. Collect results and report
Error paths: Parse failure (exit 2), renderer failure (skip item, log error), feedback timeout (return timeout status), missing target reference (verification error)

### MermaidRenderProcess
1. Read diagram item from AST
2. Extract diagram_type and source content
3. Generate Mermaid markup (.mmd file)
4. Validate Mermaid syntax (basic structural checks)
5. Optionally invoke mmdc CLI for SVG/PNG output
6. Return rendered artifact path
Error paths: Invalid diagram_type (error), malformed Mermaid source (error with diagnostics), mmdc not installed (warning, return .mmd only)

### HTMLPreviewProcess
1. Read preview item from AST
2. Extract source content and viewport configuration
3. Generate self-contained HTML template with viewport meta tags
4. Apply theme and mode settings
5. Write HTML file to output directory
6. Return rendered artifact path
Error paths: Invalid viewport value (fallback to desktop), empty source (error)

### AnnotationProcess
1. Read annotation item from AST
2. Resolve target image (diagram output, preview capture, or screenshot)
3. Load base image from resolved path
4. Iterate annotation elements in order
5. Apply each element (rect, arrow, text, blur, etc.)
6. Validate element bounds against image dimensions
7. Save annotated output image
8. Return annotated artifact path
Error paths: Target not found (error), image load failure (error), element out of bounds (warning, clamp to bounds)

### ReviewCycleProcess
1. Read visual_review item from AST
2. Resolve target artifact (must be already rendered)
3. Create review manifest JSON (artifact path, metadata, feedback template)
4. Write manifest to well-known location
5. Wait for feedback file (poll with timeout)
6. Parse structured feedback JSON
7. Validate feedback against FeedbackStatus enum
8. Return feedback result to pipeline
Error paths: Target not rendered yet (error), feedback timeout (return timeout result), invalid feedback JSON (error with parse details)

### ScreenshotRegistrationProcess
1. Read screenshot item from AST
2. Load or create screenshot catalog JSON
3. Register screenshot entry with metadata and tags
4. Save updated catalog
5. Optionally generate HTML catalog index
Error paths: Screenshot file not found (warning, register metadata only), catalog corruption (recreate from scratch)

### VisualSearchProcess
1. Read visual_search item from AST
2. Load screenshot catalog
3. Dispatch to search mode (keyword, tag, combined)
4. Score and rank results
5. Cap at max_results
6. Return ranked result list
Error paths: Empty catalog (return empty results), unsupported search mode "semantic" (warning, return empty)

### VisualVerificationProcess
1. Extract all visual items from AST JSON
2. Check diagram types against DiagramType enum variants
3. Check visual_review targets reference existing items
4. Z3: check annotation bounds within viewport constraints
5. Z3: check render_config dimensions are positive
6. Z3: check review cycle acyclicity via ordinal assignment
7. Aggregate results and return summary
Error paths: Z3 solver timeout (UNKNOWN status), missing items for reference checks (FAIL with details)
