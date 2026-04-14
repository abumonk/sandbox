## Entities

### DiagramDef
- kind: String ("diagram")
- name: String (unique identifier)
- diagram_type: String (DiagramType enum value: mermaid, flowchart, architecture, sequence, etc.)
- source: String (Mermaid/diagram markup content)
- render_config: String? (name reference to a RenderConfigDef)
- description: String?
- data_fields: [DataField]
- Relations: references RenderConfigDef via render_config; targeted by VisualReviewDef

### PreviewDef
- kind: String ("preview")
- name: String (unique identifier)
- source: String (HTML content)
- viewport: String (ViewportSize enum value: mobile, tablet, desktop, custom)
- mode: String (PreviewMode enum value: static, interactive, responsive)
- render_config: String? (name reference to a RenderConfigDef)
- description: String?
- data_fields: [DataField]
- Relations: references RenderConfigDef via render_config; targeted by VisualReviewDef

### AnnotationDef
- kind: String ("annotation")
- name: String (unique identifier)
- target: String (name reference to a diagram, preview, or screenshot)
- elements: [AnnotationElementDef] (list of annotation elements with kind, position, label, color)
- description: String?
- data_fields: [DataField]
- Relations: references DiagramDef/PreviewDef/ScreenshotDef via target

### AnnotationElementDef
- kind: String (AnnotationType enum value: rect, arrow, text, blur, segment, highlight, circle, freehand)
- position: dict (x, y, width, height or start/end for arrows)
- label: String?
- color: String?
- opacity: Float?
- Relations: contained by AnnotationDef

### VisualReviewDef
- kind: String ("visual_review")
- name: String (unique identifier)
- target: String (name reference to a diagram, preview, or screenshot)
- render_config: String? (name reference to a RenderConfigDef)
- feedback_mode: String (approve_reject, annotate, full)
- description: String?
- data_fields: [DataField]
- Relations: references DiagramDef/PreviewDef/ScreenshotDef via target; produces ReviewFeedback

### ScreenshotDef
- kind: String ("screenshot")
- name: String (unique identifier)
- path: String? (file path to screenshot image)
- source: String? (description of screenshot source)
- tags: [String] (VisualTag enum values)
- description: String?
- data_fields: [DataField]
- Relations: targeted by AnnotationDef and VisualReviewDef

### VisualSearchDef
- kind: String ("visual_search")
- name: String (unique identifier)
- search_mode: String (SearchMode enum value: keyword, tag, semantic, combined)
- query: String? (search query text)
- tags: [String] (VisualTag enum values for filtering)
- max_results: Int? (maximum results to return, default 10)
- description: String?
- data_fields: [DataField]
- Relations: queries ScreenshotDef catalog

### RenderConfigDef
- kind: String ("render_config")
- name: String (unique identifier)
- format: String (RenderFormat enum value: svg, png, html, pdf)
- width: Int? (output width in pixels)
- height: Int? (output height in pixels)
- theme: String? (theme name: default, dark, forest, neutral)
- scale: Float? (scale factor, default 1.0)
- description: String?
- data_fields: [DataField]
- Relations: referenced by DiagramDef, PreviewDef, VisualReviewDef

### ArkFile (extended)
- diagrams: {String: DiagramDef} (name -> diagram index)
- previews: {String: PreviewDef} (name -> preview index)
- annotations: {String: AnnotationDef} (name -> annotation index)
- visual_reviews: {String: VisualReviewDef} (name -> visual review index)
- screenshots: {String: ScreenshotDef} (name -> screenshot index)
- visual_searches: {String: VisualSearchDef} (name -> visual search index)
- render_configs: {String: RenderConfigDef} (name -> render config index)
- (existing fields unchanged)
