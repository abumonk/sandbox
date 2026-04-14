---
id: ADV-006
title: Snip-style Visual Communication Layer in Ark DSL
state: completed
created: 2026-04-13T00:00:00Z
updated: 2026-04-13T15:00:00Z
tasks: [ADV006-T001, ADV006-T002, ADV006-T003, ADV006-T004, ADV006-T005, ADV006-T006, ADV006-T007, ADV006-T008, ADV006-T009, ADV006-T010, ADV006-T011, ADV006-T012, ADV006-T013, ADV006-T014, ADV006-T015, ADV006-T016, ADV006-T017, ADV006-T018, ADV006-T019]
depends_on: [ADV-003]
---

## Concept

Review the Snip project (https://github.com/rixinhahaha/snip) — a desktop application providing a visual communication layer between humans and AI agents with diagram rendering, screenshot annotation, and AI-powered organization — and define/implement an Ark-native equivalent.

### What Snip does

- **Purpose**: visual communication layer between humans and AI coding agents — agents render diagrams and previews for human review instead of describing them textually.
- **Rendering capabilities**:
  - Mermaid diagram rendering and review.
  - HTML component preview rendering.
  - Image annotation and markup tools.
  - Screenshot capture with spatial annotations (rectangles, arrows, text, blur).
- **AI agent integration**: works with Claude Code, Cursor, Windsurf, and Cline — agents write content to a file, invoke `snip render` or `snip open`, tool blocks until user provides feedback (approval, annotations, changes), returns structured JSON for iteration.
- **MCP server**: for agents without shell access, provides tool interface.
- **Screenshot tools**: system-wide capture shortcuts, annotation toolset (blur, segmentation, drawing), local AI-powered organization via Ollama.
- **Semantic search**: local vision models power screenshot search and automatic categorization/tagging.
- **Stack**: Electron 33, Fabric.js 7, Mermaid.js 11, Ollama (local LLM), HuggingFace Transformers.js, SlimSAM (ONNX).
- **Privacy**: all AI runs locally — no cloud APIs needed for core features.

### Goal in Ark

Define and implement a **visual communication subsystem as an Ark island** so that Ark pipelines can declare visual outputs (diagrams, previews, annotations), render them through a unified visual layer, and collect structured human feedback — all described declaratively and verified by the Ark pipeline.

Concretely:

- **DSL surface** — introduce Ark items to describe:
  - `diagram` — a named visual artifact with type (mermaid, flowchart, architecture, sequence), source content, and rendering config.
  - `preview` — an HTML/component preview with source, viewport config, and interaction mode.
  - `annotation` — markup layer on an image/screenshot with spatial elements (rect, arrow, text, blur, segment).
  - `visual_review` — a review cycle: render visual → present to user → collect feedback (approve/reject/annotate) → return structured result.
  - `screenshot` — a captured image with metadata (timestamp, source, tags) and optional AI-generated description.
  - `visual_search` — a semantic search query over screenshot/diagram library using embeddings.
  - `render_config` — output format, resolution, theme, and layout settings for visual artifacts.
  - `feedback` — structured response from human review: approval status, annotations, free-text comments, change requests.
- **Schema** — Ark `struct`/`enum` definitions in `dsl/stdlib/visual.ark` for: DiagramType, PreviewMode, AnnotationType, FeedbackStatus, RenderFormat, ViewportSize, SearchMode, VisualTag.
- **Rendering framework** — `tools/visual/` containing:
  - `mermaid_renderer.py` — renders Mermaid diagram specs to SVG/PNG (uses mermaid CLI or inline JS).
  - `html_previewer.py` — renders HTML previews to screenshots (simplified: generates self-contained HTML files).
  - `annotator.py` — applies annotation layers to images (rectangles, arrows, text overlays using Pillow).
  - `review_loop.py` — orchestrates visual review cycle: render → present → collect feedback → return JSON.
  - `screenshot_manager.py` — manages screenshot library with metadata and tagging.
  - `search.py` — semantic search over visual artifacts using text embeddings (simplified: keyword + tag matching for v1).
  - `visual_runner.py` — top-level orchestrator: reads visual specs, dispatches to renderers, manages review cycles.
- **Reflexive use-case** — visualize Ark's own architecture:
  - Generate Mermaid diagrams from island/bridge topology.
  - Render architecture overview from `root.ark` + orchestrator specs.
  - Annotate the existing visualizer output with review feedback.
- **Verification** — Z3 checks:
  - Every diagram references a valid DiagramType.
  - Every visual_review references an existing diagram or preview.
  - Annotation coordinates are within viewport bounds (when bounds are specified).
  - Render configs have valid resolution values (positive integers, within limits).
  - Review cycles are acyclic (no circular feedback loops).
- **Codegen** — generate:
  - Mermaid `.mmd` files from `diagram` items.
  - HTML preview files from `preview` items.
  - Annotation overlay JSON from `annotation` items.
  - Review CLI commands from `visual_review` specs.
  - Screenshot index/catalog from `screenshot` metadata.
- **Visualization** — extend the visualizer to render the visual pipeline itself: diagram sources → renderers → review cycles → feedback, with preview thumbnails.

### Why this matters

Ark already generates code, verifies specs, and visualizes structure. What it lacks is a **human-in-the-loop visual review** capability. Today, reviewing generated output requires reading text diffs or running external tools manually. A visual communication island gives Ark a declarative way to say "render this diagram, show it to the human, collect their feedback" — closing the loop between generation and review. The upstream Snip project provides the pattern (render → review → structured feedback); Ark provides the declarative substrate to make visual reviews compositional, verifiable, and reproducible.

## Target Conditions
| ID | Description | Source | Design | Plan | Task(s) | Proof Method | Proof Command | Status |
|----|-------------|--------|--------|------|---------|-------------|---------------|--------|
| TC-001 | stdlib/visual.ark parses without errors | concept | design-stdlib-visual-schema | plan-foundation | T002 | autotest | `pytest tests/test_visual_schema.py -k test_visual_ark_parses` | pending |
| TC-002 | All visual enums and structs well-formed and referenceable | concept | design-stdlib-visual-schema | plan-foundation | T002 | autotest | `pytest tests/test_visual_schema.py -k test_visual_types` | pending |
| TC-003 | Lark grammar accepts all 7 new visual item types | concept | design-grammar-dsl-surface | plan-foundation | T003 | autotest | `pytest tests/test_visual_parser.py -k test_grammar_items` | pending |
| TC-004 | Pest grammar mirrors Lark for all 7 visual items | concept | design-grammar-dsl-surface | plan-foundation | T004 | manual | Review pest grammar rules match Lark | pending |
| TC-005 | Parser produces correct AST for each visual item type | concept | design-grammar-dsl-surface | plan-foundation | T005 | autotest | `pytest tests/test_visual_parser.py -k test_ast_dataclasses` | pending |
| TC-006 | Existing .ark files parse without regression | concept | design-grammar-dsl-surface | plan-foundation | T003 | autotest | `pytest tests/test_parser_smoke.py` | pending |
| TC-007 | ArkFile indices populated for visual items | concept | design-grammar-dsl-surface | plan-foundation | T005 | autotest | `pytest tests/test_visual_parser.py -k test_arkfile_indices` | pending |
| TC-008 | Mermaid renderer generates valid .mmd files | concept | design-mermaid-renderer | plan-renderers | T006 | autotest | `pytest tests/test_visual_renderer.py -k test_mermaid_mmd` | pending |
| TC-009 | Renderer handles all DiagramType variants | concept | design-mermaid-renderer | plan-renderers | T006 | autotest | `pytest tests/test_visual_renderer.py -k test_diagram_types` | pending |
| TC-010 | Invalid Mermaid source produces meaningful errors | concept | design-mermaid-renderer | plan-renderers | T006 | autotest | `pytest tests/test_visual_renderer.py -k test_mermaid_errors` | pending |
| TC-011 | HTML previewer generates valid self-contained HTML | concept | design-html-previewer | plan-renderers | T007 | autotest | `pytest tests/test_visual_renderer.py -k test_html_preview` | pending |
| TC-012 | Viewport sizes correctly configured | concept | design-html-previewer | plan-renderers | T007 | autotest | `pytest tests/test_visual_renderer.py -k test_viewports` | pending |
| TC-013 | Annotator applies rect, arrow, text, blur elements | concept | design-annotator | plan-renderers | T008 | autotest | `pytest tests/test_visual_renderer.py -k test_annotator` | pending |
| TC-014 | Annotation coordinates validated against bounds | concept | design-annotator | plan-renderers | T008 | autotest | `pytest tests/test_visual_renderer.py -k test_bounds` | pending |
| TC-015 | Review loop creates valid manifest JSON | concept | design-review-loop | plan-review-and-search | T009 | autotest | `pytest tests/test_visual_renderer.py -k test_review_manifest` | pending |
| TC-016 | Feedback parsing handles all FeedbackStatus variants | concept | design-review-loop | plan-review-and-search | T009 | autotest | `pytest tests/test_visual_renderer.py -k test_feedback_parse` | pending |
| TC-017 | Review cycles prevent circular feedback | design | design-review-loop | plan-verification | T014 | autotest | `pytest tests/test_visual_verify.py -k test_review_acyclicity` | pending |
| TC-018 | Screenshot manager registers entries correctly | concept | design-screenshot-manager | plan-review-and-search | T010 | autotest | `pytest tests/test_visual_renderer.py -k test_screenshot_register` | pending |
| TC-019 | Catalog persistence round-trip works | concept | design-screenshot-manager | plan-review-and-search | T010 | autotest | `pytest tests/test_visual_renderer.py -k test_catalog_roundtrip` | pending |
| TC-020 | Keyword search returns correct matches | concept | design-visual-search | plan-review-and-search | T011 | autotest | `pytest tests/test_visual_renderer.py -k test_keyword_search` | pending |
| TC-021 | Tag search filters by tag intersection | concept | design-visual-search | plan-review-and-search | T011 | autotest | `pytest tests/test_visual_renderer.py -k test_tag_search` | pending |
| TC-022 | Visual runner dispatches diagrams to mermaid renderer | concept | design-visual-runner | plan-runner-and-cli | T012 | autotest | `pytest tests/test_visual_integration.py -k test_runner_diagrams` | pending |
| TC-023 | Visual runner dispatches previews to html previewer | concept | design-visual-runner | plan-runner-and-cli | T012 | autotest | `pytest tests/test_visual_integration.py -k test_runner_previews` | pending |
| TC-024 | CLI ark visual subcommand works | concept | design-visual-runner | plan-runner-and-cli | T013 | autotest | `pytest tests/test_visual_integration.py -k test_cli_visual` | pending |
| TC-025 | Every diagram references valid DiagramType | concept | design-visual-verification | plan-verification | T014 | autotest | `pytest tests/test_visual_verify.py -k test_diagram_type_valid` | pending |
| TC-026 | Every visual_review references existing target | concept | design-visual-verification | plan-verification | T014 | autotest | `pytest tests/test_visual_verify.py -k test_review_target` | pending |
| TC-027 | Annotation coordinates within bounds (Z3) | concept | design-visual-verification | plan-verification | T014 | autotest | `pytest tests/test_visual_verify.py -k test_annotation_bounds_z3` | pending |
| TC-028 | Render configs have valid positive dimensions (Z3) | concept | design-visual-verification | plan-verification | T014 | autotest | `pytest tests/test_visual_verify.py -k test_render_config_z3` | pending |
| TC-029 | Review cycles acyclic (Z3 ordinals) | concept | design-visual-verification | plan-verification | T014 | autotest | `pytest tests/test_visual_verify.py -k test_review_acyclic_z3` | pending |
| TC-030 | Codegen produces .mmd from diagram items | concept | design-visual-codegen | plan-codegen | T016 | autotest | `pytest tests/test_visual_codegen.py -k test_codegen_mmd` | pending |
| TC-031 | Codegen produces .html from preview items | concept | design-visual-codegen | plan-codegen | T016 | autotest | `pytest tests/test_visual_codegen.py -k test_codegen_html` | pending |
| TC-032 | Codegen produces annotation JSON | concept | design-visual-codegen | plan-codegen | T016 | autotest | `pytest tests/test_visual_codegen.py -k test_codegen_annotation` | pending |
| TC-033 | Codegen produces render config JSON | concept | design-visual-codegen | plan-codegen | T016 | autotest | `pytest tests/test_visual_codegen.py -k test_codegen_render_config` | pending |
| TC-034 | Visual island spec parses and verifies | concept | design-reflexive-visualization | plan-reflexive-specs | T017 | autotest | `pytest tests/test_visual_integration.py -k test_visual_island_spec` | pending |
| TC-035 | Example visual specs produce rendered output | concept | design-reflexive-visualization | plan-reflexive-specs | T017 | autotest | `pytest tests/test_visual_integration.py -k test_example_specs` | pending |
| TC-036 | Visualizer renders visual pipeline items | concept | design-reflexive-visualization | plan-reflexive-specs | T018 | autotest | `pytest tests/test_visual_integration.py -k test_visualizer_visual` | pending |
| TC-037 | VisualIsland registered in root.ark | concept | design-reflexive-visualization | plan-reflexive-specs | T017 | poc | `python ark.py parse specs/root.ark` | pending |

## Evaluations
| Task | Access Requirements | Skill Set | Est. Duration | Est. Tokens | Est. Cost | Actual Duration | Actual Tokens | Actual Cost | Variance |
|------|-------------------|-----------|---------------|-------------|-----------|-----------------|---------------|-------------|----------|
| ADV006-T001 | Read, Write, Glob, Grep | test design, pytest, ark-dsl | 20min | 20000 | $0.30 | - | - | - | - |
| ADV006-T002 | Read, Write, Bash | ark-dsl | 15min | 15000 | $0.23 | - | - | - | - |
| ADV006-T003 | Read, Write, Bash | lark-grammar, ark-dsl | 20min | 25000 | $0.38 | - | - | - | - |
| ADV006-T004 | Read, Write | pest-peg, ark-dsl | 15min | 20000 | $0.30 | - | - | - | - |
| ADV006-T005 | Read, Write, Bash | python, lark-parser, ark-dsl | 25min | 40000 | $0.60 | - | - | - | - |
| ADV006-T006 | Read, Write, Bash | python, mermaid | 20min | 25000 | $0.38 | - | - | - | - |
| ADV006-T007 | Read, Write | python, html, css | 15min | 20000 | $0.30 | - | - | - | - |
| ADV006-T008 | Read, Write | python, pillow/PIL | 20min | 25000 | $0.38 | - | - | - | - |
| ADV006-T009 | Read, Write | python, json, file-based IPC | 20min | 25000 | $0.38 | - | - | - | - |
| ADV006-T010 | Read, Write | python, json | 15min | 18000 | $0.27 | - | - | - | - |
| ADV006-T011 | Read, Write | python, text search | 15min | 18000 | $0.27 | - | - | - | - |
| ADV006-T012 | Read, Write | python, pipeline architecture | 20min | 30000 | $0.45 | - | - | - | - |
| ADV006-T013 | Read, Write, Bash | python, CLI design | 15min | 20000 | $0.30 | - | - | - | - |
| ADV006-T014 | Read, Write, Bash | python, z3-solver, SMT | 25min | 35000 | $0.53 | - | - | - | - |
| ADV006-T015 | Read, Write, Bash | python, CLI integration | 10min | 12000 | $0.18 | - | - | - | - |
| ADV006-T016 | Read, Write, Bash | python, codegen patterns | 20min | 30000 | $0.45 | - | - | - | - |
| ADV006-T017 | Read, Write, Bash | ark-dsl, architecture | 20min | 25000 | $0.38 | - | - | - | - |
| ADV006-T018 | Read, Write, Bash | python, d3.js, HTML | 20min | 25000 | $0.38 | - | - | - | - |
| ADV006-T019 | Read, Write, Bash, Glob, Grep | pytest, python, z3, ark-dsl | 30min | 80000 | $1.20 | - | - | - | - |
| **TOTAL** | | | **360min** | **488000** | **$7.27** | - | - | - | - |

## Environment
- **Project**: ARK (Architecture Kernel) — declarative MMO game-engine DSL
- **Workspace**: R:/Sandbox (Ark tree at R:/Sandbox/ark)
- **Repo**: local (no git remote)
- **Branch**: local (not a git repo)
- **PC**: TTT
- **Platform**: Windows 11 Pro 10.0.26200
- **Runtime**: Node v24.12.0 (project runtime: Python 3 + Rust/Cargo)
- **Shell**: bash
