# Grammar & DSL Surface for Visual Items — Design

## Overview
Extend both the Lark and pest grammars to support 7 new visual communication items: `diagram`, `preview`, `annotation`, `visual_review`, `screenshot`, `visual_search`, and `render_config`. Also extend the parser with corresponding AST dataclasses and transformer methods.

## Target Files
- `ark/tools/parser/ark_grammar.lark` — Add 7 new item rules + supporting statements
- `ark/dsl/grammar/ark.pest` — Mirror Lark grammar extensions in pest PEG
- `ark/tools/parser/ark_parser.py` — Add dataclasses, transformer methods, ArkFile indices

## Approach

### New Grammar Rules (Lark)

```lark
// 7. diagram — named visual artifact
diagram_def: "diagram" IDENT "{" diagram_body "}"
diagram_body: diagram_member*
diagram_member: diagram_type_stmt
              | source_stmt
              | render_config_stmt
              | description_stmt
              | data_field

diagram_type_stmt: "type:" IDENT
source_stmt: "source:" STRING
render_config_stmt: "render:" IDENT

// 8. preview — HTML component preview
preview_def: "preview" IDENT "{" preview_body "}"
preview_body: preview_member*
preview_member: source_stmt
              | viewport_stmt
              | mode_stmt
              | render_config_stmt
              | description_stmt
              | data_field

viewport_stmt: "viewport:" IDENT
mode_stmt: "mode:" IDENT

// 9. annotation — markup layer on image
annotation_def: "annotation" IDENT "{" annotation_body "}"
annotation_body: annotation_member*
annotation_member: target_stmt
                 | element_stmt
                 | description_stmt
                 | data_field

target_stmt: "target:" IDENT
element_stmt: "element:" IDENT "(" meta_pair_list ")"

// 10. visual_review — review cycle
visual_review_def: "visual_review" IDENT "{" visual_review_body "}"
visual_review_body: visual_review_member*
visual_review_member: target_stmt
                    | render_config_stmt
                    | feedback_mode_stmt
                    | description_stmt
                    | data_field

feedback_mode_stmt: "feedback_mode:" IDENT

// 11. screenshot — captured image with metadata
screenshot_def: "screenshot" IDENT "{" screenshot_body "}"
screenshot_body: screenshot_member*
screenshot_member: path_stmt
                 | source_stmt
                 | tags_stmt
                 | description_stmt
                 | data_field

tags_stmt: "tags:" "[" ident_list "]"

// 12. visual_search — semantic search query
visual_search_def: "visual_search" IDENT "{" visual_search_body "}"
visual_search_body: visual_search_member*
visual_search_member: search_mode_stmt
                    | query_stmt
                    | tags_stmt
                    | max_results_stmt
                    | description_stmt
                    | data_field

search_mode_stmt: "search_mode:" IDENT
query_stmt: "query:" STRING
max_results_stmt: "max_results:" NUMBER

// 13. render_config — output configuration
render_config_def: "render_config" IDENT "{" render_config_body "}"
render_config_body: render_config_member*
render_config_member: format_stmt
                    | width_stmt
                    | height_stmt
                    | theme_stmt
                    | scale_stmt
                    | description_stmt
                    | data_field

format_stmt: "format:" IDENT
width_stmt: "width:" NUMBER
height_stmt: "height:" NUMBER
theme_stmt: "theme:" STRING
scale_stmt: "scale:" NUMBER
```

Update the `item` rule to include all 7 new alternatives.

### Pest Grammar
Mirror all Lark rules as pest PEG rules following existing conventions (silent `_{}` for item, etc.).

### Parser Dataclasses

New dataclasses:
- `DiagramDef(kind, name, diagram_type, source, render_config, description, data_fields)`
- `PreviewDef(kind, name, source, viewport, mode, render_config, description, data_fields)`
- `AnnotationDef(kind, name, target, elements, description, data_fields)`
- `VisualReviewDef(kind, name, target, render_config, feedback_mode, description, data_fields)`
- `ScreenshotDef(kind, name, path, source, tags, description, data_fields)`
- `VisualSearchDef(kind, name, search_mode, query, tags, max_results, description, data_fields)`
- `RenderConfigDef(kind, name, format, width, height, theme, scale, description, data_fields)`

### ArkFile Extensions
- Add `diagrams`, `previews`, `annotations`, `visual_reviews`, `screenshots`, `visual_searches`, `render_configs` index dicts
- Update `_build_indices()` to populate them

### Design Decisions
- Follow dual-grammar parity pattern (ADV-001 pattern)
- Reuse existing statement rules where possible (`path_stmt`, `description_stmt`, `data_field`)
- New statements (`source_stmt`, `viewport_stmt`, etc.) share naming conventions with studio items
- `element_stmt` uses meta_pair_list for flexible annotation element parameters
- `target_stmt` references a diagram/preview/screenshot by IDENT

## Dependencies
- design-stdlib-visual-schema (types must exist for type references)

## Target Conditions
- TC-003: Lark grammar accepts all 7 new item types without errors
- TC-004: Pest grammar mirrors Lark grammar for all 7 items
- TC-005: Parser produces correct AST for each new item type
- TC-006: Existing .ark files parse without regression
- TC-007: ArkFile indices populated for diagrams, previews, annotations, visual_reviews, screenshots
