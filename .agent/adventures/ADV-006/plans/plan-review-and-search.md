# Review Loop, Screenshot Manager, Visual Search

## Designs Covered
- design-review-loop: Visual review cycle orchestration
- design-screenshot-manager: Screenshot library management
- design-visual-search: Semantic search over visual artifacts

## Tasks

### Create review loop orchestrator
- **ID**: ADV006-T009
- **Description**: Create `ark/tools/visual/review_loop.py`. Implement `run_review()`, `create_review_manifest()`, `wait_for_feedback()`, `parse_feedback()`. Support three feedback modes (approve_reject, annotate, full). File-based communication with JSON manifests and feedback files.
- **Files**: `ark/tools/visual/review_loop.py`
- **Acceptance Criteria**:
  - Creates valid review manifest JSON with target artifact path
  - Feedback parsing handles all FeedbackStatus variants
  - Timeout-based waiting with configurable duration
  - Feedback template provides correct structure
  - Works without GUI (file-based only)
- **Target Conditions**: TC-015, TC-016
- **Depends On**: [ADV006-T006, ADV006-T007]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: python, json, file-based IPC
  - Estimated duration: 20min
  - Estimated tokens: 25000

### Create screenshot manager
- **ID**: ADV006-T010
- **Description**: Create `ark/tools/visual/screenshot_manager.py`. Implement `register_screenshot()`, `load_catalog()`, `save_catalog()`, `list_screenshots()`, `get_screenshot()`, `generate_catalog_index()`. Manage JSON catalog file for screenshot metadata and tagging.
- **Files**: `ark/tools/visual/screenshot_manager.py`
- **Acceptance Criteria**:
  - Registers screenshot entries in catalog correctly
  - Catalog load/save round-trip preserves data
  - Tag-based filtering works
  - HTML catalog index generated with entry listing
  - Creates empty catalog when none exists
- **Target Conditions**: TC-018, TC-019
- **Depends On**: [ADV006-T005]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: python, json
  - Estimated duration: 15min
  - Estimated tokens: 18000

### Create visual search module
- **ID**: ADV006-T011
- **Description**: Create `ark/tools/visual/search.py`. Implement `execute_search()`, `keyword_search()`, `tag_search()`, `combined_search()`, `score_result()`. v1 uses text-based keyword + tag matching. SearchMode.semantic returns empty results with warning.
- **Files**: `ark/tools/visual/search.py`
- **Acceptance Criteria**:
  - Keyword search returns correct matches from catalog
  - Tag search filters correctly by tag intersection
  - Combined search uses weighted scoring
  - Results capped at max_results
  - SearchMode.semantic returns graceful "not implemented" warning
- **Target Conditions**: TC-020, TC-021
- **Depends On**: [ADV006-T010]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: python, text search
  - Estimated duration: 15min
  - Estimated tokens: 18000
