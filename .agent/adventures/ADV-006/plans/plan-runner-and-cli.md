# Visual Runner & CLI Integration

## Designs Covered
- design-visual-runner: Top-level orchestrator and CLI integration

## Tasks

### Create visual runner orchestrator
- **ID**: ADV006-T012
- **Description**: Create `ark/tools/visual/visual_runner.py`. Implement `run_visual_pipeline()`, `extract_visual_items()`, `resolve_render_configs()`, `dispatch_renderers()`. Orchestrate the full visual pipeline: extract items -> resolve configs -> dispatch renderers -> process annotations -> register screenshots -> execute searches -> run reviews.
- **Files**: `ark/tools/visual/visual_runner.py`
- **Acceptance Criteria**:
  - Dispatches diagram items to mermaid renderer
  - Dispatches preview items to html previewer
  - Processes annotation items through annotator
  - Registers screenshot items in catalog
  - Executes visual search queries
  - Reports results with item counts and errors
  - Supports mode filtering (all, render, review, search, catalog)
- **Target Conditions**: TC-022, TC-023
- **Depends On**: [ADV006-T006, ADV006-T007, ADV006-T008, ADV006-T009, ADV006-T010, ADV006-T011]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: python, pipeline architecture
  - Estimated duration: 20min
  - Estimated tokens: 30000

### Add visual CLI subcommand to ark.py
- **ID**: ADV006-T013
- **Description**: Add `ark visual` subcommand to `ark/ark.py` with sub-commands: `render`, `review`, `search`, `catalog`, `pipeline`. Follow existing pattern from `cmd_studio()` and `cmd_codegraph()`. Add visual tools path to sys.path.
- **Files**: `ark/ark.py`
- **Acceptance Criteria**:
  - `ark visual render <file.ark>` renders diagrams and previews
  - `ark visual review <file.ark>` starts review cycles
  - `ark visual search <file.ark>` executes visual searches
  - `ark visual catalog <file.ark>` generates screenshot catalog
  - `ark visual pipeline <file.ark>` runs full visual pipeline
  - Usage help shown for `ark visual` without arguments
  - No regressions in existing CLI commands
- **Target Conditions**: TC-024
- **Depends On**: [ADV006-T012]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, CLI design
  - Estimated duration: 15min
  - Estimated tokens: 20000
