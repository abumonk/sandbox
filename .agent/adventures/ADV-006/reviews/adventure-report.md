---
adventure_id: ADV-006
generated_at: 2026-04-13T15:40:00Z
task_count: 19
tc_total: 37
tc_passed: 37
tc_pass_rate: "100%"
total_iterations: 0
knowledge_suggestions_count: 7
---

# Adventure Report: ADV-006

## 1. Executive Summary

| Field | Value |
|-------|-------|
| Adventure | ADV-006 |
| Title | Snip-style Visual Communication Layer in Ark DSL |
| Duration | ~15 hours (2026-04-13T00:00Z to 2026-04-13T15:00Z) |
| Total Cost | ~$3.07 estimated (304,000 tokens in, 44,200 tokens out from 12 tracked agent runs) |
| Tasks | 19/19 completed |
| TC Pass Rate | 37/37 (100%) |

ADV-006 implemented a complete visual communication subsystem for the Ark DSL, inspired by the Snip project. The adventure introduced 7 new DSL item types (diagram, preview, annotation, visual_review, screenshot, visual_search, render_config), extended both Lark and Pest grammars, built 7 tool modules (mermaid renderer, HTML previewer, annotator, review loop, screenshot manager, visual search, visual runner), added Z3 verification checks, codegen support, CLI integration, island specs with root.ark registration, and 83 automated tests across 6 test files. All 19 tasks passed review with zero rework iterations. Final test suite: 993 tests passing.

## 2. Task Results Summary

| Task | Title | Verdict | Key Deliverables |
|------|-------|---------|-----------------|
| ADV006-T001 | Design test strategy | PASSED | Test strategy document mapping 37 TCs to 6 test files |
| ADV006-T002 | stdlib/visual.ark types | PASSED | 8 enums + 8 structs in dsl/stdlib/visual.ark |
| ADV006-T003 | Lark grammar extension | PASSED | 7 visual item rules in ark_grammar.lark |
| ADV006-T004 | Pest grammar extension | PASSED | 7 matching rules in ark.pest |
| ADV006-T005 | Parser AST dataclasses | PASSED | 7 dataclasses + transformer methods + ArkFile indices |
| ADV006-T006 | Mermaid renderer | PASSED | mermaid_renderer.py with render/generate/validate functions |
| ADV006-T007 | HTML previewer | PASSED | html_previewer.py with viewport and theme support |
| ADV006-T008 | Image annotator | PASSED | annotator.py with Pillow + JSON fallback |
| ADV006-T009 | Review loop orchestrator | PASSED | review_loop.py with manifest/feedback/run cycle |
| ADV006-T010 | Screenshot manager | PASSED | screenshot_manager.py with catalog persistence |
| ADV006-T011 | Visual search | PASSED | search.py with keyword/tag/combined/semantic modes |
| ADV006-T012 | Visual runner orchestrator | PASSED | visual_runner.py dispatching to all renderers |
| ADV006-T013 | CLI integration | PASSED | ark visual {pipeline,codegen,verify} subcommands |
| ADV006-T014 | Z3 verification | PASSED | visual_verify.py with 5 Z3 check functions |
| ADV006-T015 | Verify pipeline integration | PASSED | ark visual verify wired into ark.py |
| ADV006-T016 | Visual codegen | PASSED | visual_codegen.py generating .mmd/.html/.json outputs |
| ADV006-T017 | Island specs + root.ark | PASSED | visual_island.ark, visual_examples.ark, root.ark updated |
| ADV006-T018 | Visualizer extension | PASSED | ark_visualizer.py handles visual node types |
| ADV006-T019 | Automated tests (83 tests) | PASSED | 6 test files, 83 visual tests, 993 total passing |

## 3. Architecture Analysis

### Layer Structure

The visual communication layer follows a clean four-layer architecture:

1. **DSL Layer** (T002-T005): Type definitions in stdlib/visual.ark, grammar rules in both Lark and Pest, AST dataclasses and transformer methods in ark_parser.py. This layer establishes the declarative surface -- users write `diagram`, `preview`, `annotation`, etc. items in .ark files.

2. **Tool Layer** (T006-T012): Seven modules under `ark/tools/visual/` implementing rendering, annotation, review orchestration, screenshot management, and search. Each module follows the pattern of a functional API plus an optional class facade. The visual_runner.py orchestrator dispatches parsed AST items to the appropriate tool module.

3. **Pipeline Layer** (T013-T016): CLI integration (`ark visual` subcommand), Z3 verification (5 checks including acyclicity, bounds, and type validity), and codegen (generating .mmd, .html, .json outputs). These integrate into Ark's existing pipeline infrastructure.

4. **Spec Layer** (T017-T018): Self-referential island specs that describe the visual subsystem using the visual DSL itself, plus visualizer extensions to render visual pipeline items in Ark's HTML graph output.

### Design Decisions

- **ViewportSize as enum vs struct**: T002 implemented ViewportSize as an enum of presets (mobile, tablet, desktop, custom) rather than a struct with width/height fields. T007 compensated with a dimension lookup table. This simplifies DSL authoring at the cost of custom dimension flexibility.

- **Pillow optional dependency**: T008 (annotator) uses a try/except import guard for Pillow, falling back to JSON overlay output. This keeps Ark installable without image processing dependencies.

- **Z3 ordinals for review acyclicity**: T014 reused the Z3 ordinal pattern from ADV-003 (studio escalation paths) for verifying visual_review cycles are acyclic. This is consistent with Ark's verification philosophy.

- **Lazy imports in CLI**: T013 uses lazy imports with try/except for all visual sub-modules, enabling graceful degradation if modules are missing.

### Dual Grammar Parity

Both Lark (Python) and Pest (Rust) grammars were extended in lockstep (T003/T004), maintaining Ark's dual-runtime capability. The Pest grammar adds rules at lines 664+ with matching structure to the Lark rules. Cargo check passes cleanly.

## 4. Quality Assessment

### Test Coverage

- **83 visual-specific tests** across 6 test files covering all 37 target conditions
- **993 total tests** passing (910 pre-existing + 83 new), 0 failures
- All autotest proof commands verified by the task reviewer
- TC-004 (Pest grammar parity) verified by manual inspection as specified

### Code Quality Observations

- Consistent error handling patterns across tool modules (try/except with meaningful error messages)
- ArkFile indices cleanly separate visual items from other item types
- The visual_runner uses an `_get_attr` helper to support both dict-form and dataclass-form AST inputs
- Error-collection pattern in visual_runner (continue on exceptions, accumulate errors list) is robust

### Issues Noted

1. **Pre-existing parse failure**: `specs/game/vehicle_physics.ark` fails with "unexpected character '.'" -- unrelated to ADV-006 changes, noted in T003 review
2. **Incomplete metrics tracking**: Only 12 of 19 tasks have agent run metrics recorded (T006, T008, T010, T014, T015, T018, T019 missing). This is a recurring issue (also noted in ADV-002).
3. **ViewportSize type mismatch**: Test strategy expected a struct; implementation used an enum. Not a bug -- both T002 and T007 are consistent -- but represents a design doc vs implementation divergence.

### Rework Iterations

Zero rework iterations across all 19 tasks. Every task passed review on first submission. This continues the pattern established in ADV-003 (14 tasks, zero rework) and validates the design-first approach.

## 5. Issues and Recommendations

### Issues

| # | Severity | Description | Affected Tasks |
|---|----------|-------------|----------------|
| 1 | Low | Pre-existing vehicle_physics.ark parse failure | T003 (noted, not caused by) |
| 2 | Medium | 7/19 tasks missing metrics entries | T006, T008, T010, T014, T015, T018, T019 |
| 3 | Low | ViewportSize enum vs struct divergence from test strategy | T002, T007 |
| 4 | Info | Semantic search mode degrades gracefully (v1 placeholder) | T011 |

### Recommendations

1. **High priority -- Fix metrics tracking gap**: 7 tasks lack agent run metrics. Enforce that every implementer appends to metrics.md before marking complete. Consider adding a pre-review check for metrics presence.

2. **High priority -- Fix vehicle_physics.ark parse failure**: The pre-existing parse failure on `specs/game/vehicle_physics.ark` should be tracked and resolved. It predates ADV-006 but represents a regression in the parser that could mask future issues.

3. **Medium priority -- Semantic search implementation**: The visual search module's semantic mode is a placeholder (v1). If visual artifact search becomes a real use case, implement embedding-based search using a local model.

4. **Medium priority -- Pillow dependency documentation**: The annotator's optional Pillow dependency should be documented in a setup/requirements file so users know to install it for full annotation capability.

5. **Lower priority -- Review task evaluation estimates**: The manifest estimated 360min / $7.27 total cost. Actual tracked runs total ~111min / ~$3.07 (for 12/19 tasks). The per-task estimates were generally conservative, which is fine for budgeting but the variance should be noted for future estimation calibration.

## 6. Knowledge Extraction Suggestions

| # | Type | Target File | Title |
|---|------|-------------|-------|
| 1 | pattern | .agent/knowledge/patterns.md | Visual subsystem as island pattern |
| 2 | pattern | .agent/knowledge/patterns.md | Optional dependency guard pattern |
| 3 | issue | .agent/knowledge/issues.md | Metrics tracking remains incomplete |
| 4 | decision | .agent/knowledge/decisions.md | ViewportSize as enum with lookup table |
| 5 | decision | .agent/knowledge/decisions.md | Visual review acyclicity via Z3 ordinals |
| 6 | feedback | .claude/agent-memory/team-pipeline-implementer/metrics-enforcement.md | Implementers must append metrics |
| 7 | process | (informational) | Pre-review metrics presence check |

### Suggestion 1: Visual subsystem as island pattern
- **Type**: pattern
- **Target File**: `.agent/knowledge/patterns.md`
- **Content**:
  ```
  - **Visual Subsystem as Island**: When adding a major feature domain (visual communication, studio, etc.), structure it as a four-layer island: DSL types + grammar rules -> tool modules -> pipeline integration (CLI, verify, codegen) -> self-referential specs. ADV-006 delivered 19 tasks with zero rework using this pattern. (from ADV-006)
  ```

### Suggestion 2: Optional dependency guard pattern
- **Type**: pattern
- **Target File**: `.agent/knowledge/patterns.md`
- **Content**:
  ```
  - **Optional Dependency Guard**: For tool modules with heavy dependencies (Pillow, mermaid CLI, etc.), use try/except import guards with a `_AVAILABLE` flag and provide a degraded fallback (e.g., JSON overlay instead of image rendering). Keeps Ark installable without optional deps. (from ADV-006)
  ```

### Suggestion 3: Metrics tracking remains incomplete
- **Type**: issue
- **Target File**: `.agent/knowledge/issues.md`
- **Content**:
  ```
  - **Metrics tracking still incomplete**: ADV-006 had 7/19 tasks missing metrics entries, repeating the ADV-002 pattern (7/17 missing). Solution: add a pre-review check that verifies metrics.md has an entry for the task being reviewed. Block review until metrics are recorded. (from ADV-006)
  ```

### Suggestion 4: ViewportSize as enum with lookup table
- **Type**: decision
- **Target File**: `.agent/knowledge/decisions.md`
- **Content**:
  ```
  ## ViewportSize as enum with dimension lookup
  - **Context**: Visual preview items need viewport sizing. A struct with width/height is flexible but verbose in DSL; an enum of presets (mobile, tablet, desktop, custom) is simpler to author.
  - **Decision**: Use an enum of viewport presets with a dimension lookup table in the renderer. Custom sizes are supported via the "custom" variant with explicit dimensions in render_config.
  - **From**: ADV-006
  ```

### Suggestion 5: Visual review acyclicity via Z3 ordinals
- **Type**: decision
- **Target File**: `.agent/knowledge/decisions.md`
- **Content**:
  ```
  ## Z3 ordinals generalized for DAG acyclicity
  - **Context**: Both studio escalation paths (ADV-003) and visual review cycles (ADV-006) need acyclicity verification.
  - **Decision**: Z3 ordinal assignment is the standard Ark pattern for DAG acyclicity checks. Assign each node an integer ordinal; require edges to strictly increase. This generalizes across any item type with directed references.
  - **From**: ADV-003, ADV-006
  ```

### Suggestion 6: Implementers must append metrics
- **Type**: feedback
- **Target File**: `.claude/agent-memory/team-pipeline-implementer/metrics-enforcement.md`
- **Role**: implementer
- **Content**:
  ```
  ---
  name: Metrics enforcement
  description: Implementers must append metrics row to metrics.md before marking task complete
  type: feedback
  ---
  
  Append a metrics row to the adventure's metrics.md before marking any task as complete. This has been a recurring gap across ADV-002 and ADV-006 (7/17 and 7/19 tasks missing respectively). The adventure reviewer cannot produce accurate cost analysis without complete metrics data.
  
  **Why:** Incomplete metrics make cost estimation and process analysis unreliable. The adventure reviewer flags this every time.
  **How to apply:** Before writing "complete:" to the adventure log, append your metrics row: `| implementer | {task-id} | {model} | {tokens_in} | {tokens_out} | {duration} | {turns} | {result} |`
  ```

### Suggestion 7: Pre-review metrics presence check
- **Type**: process
- **Target File**: (informational only -- not auto-applied)
- **Content**: Add a prerequisite check to the task reviewer: before reviewing a task, verify that `metrics.md` contains a row for that task ID. If missing, log a warning (or block review). This closes the loop on the recurring metrics tracking gap without relying solely on implementer discipline.

## 7. Recommendations

Actionable suggestions for future adventures, ordered by priority:

1. **Enforce metrics recording**: Add a pre-review gate that checks for metrics entries. This is the third adventure with incomplete metrics (ADV-001 had task status gaps, ADV-002 and ADV-006 had metrics gaps). Automation is needed since implementer discipline alone is insufficient.

2. **Track pre-existing parse failures**: The vehicle_physics.ark parse failure has persisted since at least ADV-006. Create a dedicated task or issue to fix it before it masks future grammar regressions.

3. **Implement semantic search (v2)**: The visual search module's semantic mode is a stub. If visual artifacts become a real workflow tool, implement embedding-based search. Consider using sentence-transformers for local inference.

4. **Calibrate task estimates**: ADV-006 estimated 360min/$7.27 but actual tracked work was ~111min/$3.07 (for 63% of tasks). Future adventures should use the observed per-task averages (~9min, ~$0.26) as a baseline rather than the current conservative estimates.

5. **Document optional dependencies**: Create a requirements-optional.txt or similar for Pillow, mermaid-cli, and any future optional tool dependencies so users can install the full visual toolchain.

Areas needing hardening or refactoring:
- **Annotator fallback path**: The JSON overlay fallback when Pillow is unavailable should have its own tests to ensure annotation metadata is preserved even without image rendering.
- **Visual runner error reporting**: While errors are collected, there is no structured error output format. Consider aligning with Ark's existing verification result format for consistency.
