# Visual Codegen

## Designs Covered
- design-visual-codegen: Code generation for visual artifacts

## Tasks

### Create visual codegen module
- **ID**: ADV006-T016
- **Description**: Create `ark/tools/codegen/visual_codegen.py`. Implement `gen_visual()` with per-type generators: `gen_diagram_mmd()`, `gen_preview_html()`, `gen_annotation_json()`, `gen_review_script()`, `gen_catalog_index()`, `gen_render_config_json()`. Follow studio_codegen.py pattern. Add `visual` codegen target to ark.py.
- **Files**: `ark/tools/codegen/visual_codegen.py`, `ark/ark.py`
- **Acceptance Criteria**:
  - Produces `.mmd` files from diagram items
  - Produces `.html` files from preview items
  - Produces annotation overlay JSON from annotation items
  - Produces render config JSON from render_config items
  - `ark codegen <file.ark> --target visual` works
  - Output matches existing codegen conventions (filename->content dict)
- **Target Conditions**: TC-030, TC-031, TC-032, TC-033
- **Depends On**: [ADV006-T005, ADV006-T013]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, codegen patterns
  - Estimated duration: 20min
  - Estimated tokens: 30000
