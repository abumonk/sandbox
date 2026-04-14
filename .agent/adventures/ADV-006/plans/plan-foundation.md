# Foundation — Schema, Grammar, Parser

## Designs Covered
- design-stdlib-visual-schema: Stdlib type definitions for visual entities
- design-grammar-dsl-surface: Grammar extensions and parser support for visual items

## Tasks

### Create stdlib/visual.ark type definitions
- **ID**: ADV006-T002
- **Description**: Create the visual stdlib file with enum and struct definitions for DiagramType, PreviewMode, AnnotationType, FeedbackStatus, RenderFormat, ViewportSize, SearchMode, VisualTag, RenderConfig, Position, ArrowEndpoints, AnnotationElement, ReviewFeedback, ScreenshotMeta, SearchQuery, SearchResult.
- **Files**: `ark/dsl/stdlib/visual.ark`
- **Acceptance Criteria**:
  - All 8 enums and 8 structs defined and well-formed
  - File parses via `python ark.py parse dsl/stdlib/visual.ark`
  - Types consistent with existing stdlib patterns (types.ark, studio.ark)
- **Target Conditions**: TC-001, TC-002
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: ark-dsl
  - Estimated duration: 15min
  - Estimated tokens: 15000

### Extend Lark grammar with visual item rules
- **ID**: ADV006-T003
- **Description**: Add grammar rules for diagram_def, preview_def, annotation_def, visual_review_def, screenshot_def, visual_search_def, render_config_def to ark_grammar.lark. Add supporting statement rules (diagram_type_stmt, source_stmt, viewport_stmt, mode_stmt, target_stmt, element_stmt, feedback_mode_stmt, tags_stmt, search_mode_stmt, query_stmt, max_results_stmt, format_stmt, width_stmt, height_stmt, theme_stmt, scale_stmt). Update the item rule to include all 7 new alternatives.
- **Files**: `ark/tools/parser/ark_grammar.lark`
- **Acceptance Criteria**:
  - All 7 new item rules syntactically correct Lark EBNF
  - All supporting statement rules added
  - Existing .ark files still parse (no regressions)
  - New rules follow existing naming conventions
- **Target Conditions**: TC-003, TC-006
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: lark-grammar, ark-dsl
  - Estimated duration: 20min
  - Estimated tokens: 25000

### Extend pest grammar with visual item rules
- **ID**: ADV006-T004
- **Description**: Mirror the Lark grammar changes in dsl/grammar/ark.pest. Add pest PEG rules for all 7 new visual items and supporting statements.
- **Files**: `ark/dsl/grammar/ark.pest`
- **Acceptance Criteria**:
  - Pest rules mirror Lark rules for all 7 items
  - Pest syntax is correct
  - Existing pest rules unchanged
- **Target Conditions**: TC-004
- **Depends On**: [ADV006-T003]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: pest-peg, ark-dsl
  - Estimated duration: 15min
  - Estimated tokens: 20000

### Add parser AST dataclasses and transformer for visual items
- **ID**: ADV006-T005
- **Description**: Add DiagramDef, PreviewDef, AnnotationDef, VisualReviewDef, ScreenshotDef, VisualSearchDef, RenderConfigDef dataclasses to ark_parser.py. Add transformer methods for all new grammar rules. Update ArkFile with diagrams/previews/annotations/visual_reviews/screenshots/visual_searches/render_configs index dicts and _build_indices().
- **Files**: `ark/tools/parser/ark_parser.py`
- **Acceptance Criteria**:
  - All 7 new dataclasses added with correct fields
  - Transformer methods produce correct AST dicts for all new item types
  - ArkFile indices populated for all visual item types
  - `python ark.py parse` works on .ark files with visual items
- **Target Conditions**: TC-005, TC-007
- **Depends On**: [ADV006-T003]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, lark-parser, ark-dsl
  - Estimated duration: 25min
  - Estimated tokens: 40000
