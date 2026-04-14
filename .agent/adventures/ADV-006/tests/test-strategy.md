# ADV-006 Test Strategy — Visual Communication Layer

## Overview

This document maps every target condition (TC-001 through TC-037) from the ADV-006 manifest
to specific test files, test functions, proof commands, and test runners. Tests are grouped
by subsystem following the Ark project's existing conventions (established in ADV-001 through
ADV-005).

### Conventions (aligned with `R:/Sandbox/ark/tests/conftest.py`)

- **pytest** is the primary test runner for all Python code
- Fixtures `parse_src`, `parse_file`, and `ark_root` are available from `conftest.py`
- Test files follow `test_visual_{subsystem}.py` naming
- All test files live under `R:/Sandbox/ark/tests/`
- All commands assume `cd R:/Sandbox/ark` as working directory
- CLI tests use `subprocess.run(['python', 'ark.py', ...], cwd=REPO_ROOT)` and assert `returncode == 0`
- Unit tests use direct Python API calls (no subprocess overhead)
- `@pytest.mark.integration` marks tests requiring real spec files on disk
- A `REPO_ROOT` constant at the top of each test file points to `R:/Sandbox/ark/`
- Visual tool modules are imported from `tools/visual/` (added to `sys.path` in test module setup)

## Proof Methods

- **autotest** — automated pytest or CLI command with deterministic pass/fail
- **poc** — proof-of-concept command that must produce non-trivial output (human judges output)
- **manual** — human inspection of generated artifact

---

## Tests by Subsystem

### 1. Schema Tests — `tests/test_visual_schema.py`

Covers TC-001 and TC-002. Tests that `dsl/stdlib/visual.ark` parses without errors and that all
enum/struct definitions are well-formed and referenceable.

**Fixture approach**: Parse the real file at `dsl/stdlib/visual.ark` using `ArkParser` (via
`parse_file` fixture). Inspect the returned `ArkFile` object for presence and correctness of all
expected enum and struct items. Additional functions verify each enum's variants individually.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-001 | `test_visual_ark_parses` | `dsl/stdlib/visual.ark` parses via `ArkParser` without raising exceptions; result is a non-None `ArkFile` with at least one item |
| TC-002 | `test_visual_types` | All expected enums and structs are present: enums `DiagramType`, `PreviewMode`, `AnnotationType`, `FeedbackStatus`, `RenderFormat`, `SearchMode`, `VisualTag`; structs `ViewportSize`, `RenderConfig`, `Feedback` — verified by name lookup in `arkfile` |

Additional test functions (supporting TC-002):
- `test_diagram_type_variants` — `DiagramType` has `mermaid`, `flowchart`, `architecture`, `sequence` variants
- `test_preview_mode_variants` — `PreviewMode` has `static`, `interactive`, `responsive` variants
- `test_annotation_type_variants` — `AnnotationType` has `rect`, `arrow`, `text`, `blur`, `segment` variants
- `test_feedback_status_variants` — `FeedbackStatus` has `approved`, `rejected`, `pending`, `annotated` variants
- `test_render_format_variants` — `RenderFormat` has `svg`, `png`, `html`, `json` variants
- `test_search_mode_variants` — `SearchMode` has `keyword`, `tag`, `semantic` variants
- `test_visual_tag_variants` — `VisualTag` has at least `diagram`, `preview`, `screenshot`, `annotation` variants
- `test_viewport_size_struct_fields` — `ViewportSize` struct has `width` and `height` fields
- `test_render_config_struct_fields` — `RenderConfig` struct has `format`, `resolution`, `theme`, `layout` fields
- `test_feedback_struct_fields` — `Feedback` struct has `status`, `annotations`, `comments`, `change_requests` fields

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_schema.py::test_visual_ark_parses -q
cd R:/Sandbox/ark && pytest tests/test_visual_schema.py::test_visual_types -q
cd R:/Sandbox/ark && pytest tests/test_visual_schema.py -q
```

---

### 2. Parser Tests — `tests/test_visual_parser.py`

Covers TC-003 through TC-007. Tests that the Lark grammar handles all 7 new visual item types,
that the Pest grammar mirrors them, that the parser produces correct AST dataclasses, that
`ArkFile` indices are populated, and that existing `.ark` files parse without regression.

**Fixture approach**: In-memory `.ark` snippet strings for each of the 7 item kinds. Parser
tests instantiate `ArkParser`, call `parse()` on the snippet, and assert no exception is raised.
AST tests assert field values on the returned dataclasses. Regression tests call the parser on
real files under `dsl/stdlib/` and `specs/`. Index tests parse a multi-item snippet and inspect
the `arkfile` attribute dict.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-003 | `test_grammar_items` | One snippet per item kind — `diagram`, `preview`, `annotation`, `visual_review`, `screenshot`, `visual_search`, `render_config` — all parse without errors via the Lark grammar |
| TC-004 | (manual inspection) | Pest grammar `ark.pest` mirrors all 7 new Lark rules — human counts rule definitions in `dsl/grammar/ark.pest` |
| TC-005 | `test_ast_dataclasses` | Parsing each item kind snippet produces the correct AST dataclass: `DiagramDef`, `PreviewDef`, `AnnotationDef`, `VisualReviewDef`, `ScreenshotDef`, `VisualSearchDef`, `RenderConfigDef` — key fields (name, type/mode, source/content) match the input snippet |
| TC-006 | `test_parser_smoke` (or `test_parser_regression`) | Representative existing `.ark` files (`specs/root.ark`, `dsl/stdlib/types.ark`, `specs/game/vehicle_physics.ark`) still parse after the grammar extension with no exceptions |
| TC-007 | `test_arkfile_indices` | Parsing a multi-item `.ark` snippet populates `arkfile.diagrams`, `arkfile.previews`, `arkfile.annotations`, `arkfile.visual_reviews`, `arkfile.screenshots`, `arkfile.visual_searches`, `arkfile.render_configs` with correct name keys |

Additional test functions (supporting TC-003/TC-005):
- `test_diagram_item_fields` — parsed `DiagramDef` has `name`, `type`, `source`, `render_config` fields
- `test_preview_item_fields` — parsed `PreviewDef` has `name`, `source`, `viewport`, `mode` fields
- `test_annotation_item_fields` — parsed `AnnotationDef` has `name`, `target`, `elements`, `bounds` fields
- `test_visual_review_item_fields` — parsed `VisualReviewDef` has `name`, `target`, `mode`, `feedback` fields
- `test_screenshot_item_fields` — parsed `ScreenshotDef` has `name`, `path`, `timestamp`, `tags` fields
- `test_visual_search_item_fields` — parsed `VisualSearchDef` has `name`, `query`, `mode`, `filters` fields
- `test_render_config_item_fields` — parsed `RenderConfigDef` has `name`, `format`, `width`, `height`, `theme` fields

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_parser.py::test_grammar_items -q
cd R:/Sandbox/ark && pytest tests/test_visual_parser.py::test_ast_dataclasses -q
cd R:/Sandbox/ark && pytest tests/test_visual_parser.py::test_arkfile_indices -q
cd R:/Sandbox/ark && pytest tests/test_visual_parser.py::test_parser_smoke -q
cd R:/Sandbox/ark && pytest tests/test_visual_parser.py -q
```

---

### 3. Renderer Tests — `tests/test_visual_renderer.py`

Covers TC-008 through TC-021. Tests all rendering subsystems: Mermaid renderer, HTML previewer,
annotator, review loop, screenshot manager, and search engine.

**Fixture approach**: Unit tests import directly from `tools/visual/`. Mermaid and HTML renderer
tests use in-memory spec dicts and assert on the structure of returned file-path strings or
output content. Annotator tests use a small synthetic image created via `PIL.Image.new()` to
avoid depending on real image files. Review loop tests use a stub `render_fn` that returns a
fixed string path. Screenshot manager tests use `tmp_path` (pytest built-in) for catalog
persistence. Search tests use a small in-memory catalog dict.

#### 3a. Mermaid Renderer (TC-008 through TC-010)

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-008 | `test_mermaid_mmd` | `MermaidRenderer.render(diagram_spec)` with a valid `flowchart` spec returns a string path ending in `.mmd`; the file at that path contains `graph` or `flowchart` syntax (content round-trip check) |
| TC-009 | `test_diagram_types` | Calling `MermaidRenderer.render()` with each `DiagramType` variant (`mermaid`, `flowchart`, `architecture`, `sequence`) succeeds without raising; the output `.mmd` file header matches the expected diagram type keyword |
| TC-010 | `test_mermaid_errors` | `MermaidRenderer.render(spec)` with an empty or `None` source raises `VisualRenderError` (or returns a result with `error` field set); the exception/error message contains a human-readable description |

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_renderer.py::test_mermaid_mmd -q
cd R:/Sandbox/ark && pytest tests/test_visual_renderer.py::test_diagram_types -q
cd R:/Sandbox/ark && pytest tests/test_visual_renderer.py::test_mermaid_errors -q
```

#### 3b. HTML Previewer (TC-011 through TC-012)

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-011 | `test_html_preview` | `HtmlPreviewer.render(preview_spec)` with a minimal HTML source returns a path to a self-contained `.html` file; file content includes `<!DOCTYPE html>` and the original source HTML embedded within it |
| TC-012 | `test_viewports` | `HtmlPreviewer.render(spec)` with `ViewportSize(width=1280, height=720)` produces HTML containing `width: 1280px` (or viewport meta tag); with `ViewportSize(width=375, height=812)` (mobile) produces correspondingly constrained HTML |

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_renderer.py::test_html_preview -q
cd R:/Sandbox/ark && pytest tests/test_visual_renderer.py::test_viewports -q
```

#### 3c. Annotator (TC-013 through TC-014)

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-013 | `test_annotator` | `Annotator.apply(image_path, elements)` with a list containing one element of each type (`rect`, `arrow`, `text`, `blur`) returns a path to an output image file; the file is a valid PNG (Pillow can reopen it without error) |
| TC-014 | `test_bounds` | `Annotator.apply(image_path, elements, bounds=(100, 100))` with an element whose coordinates exceed `(100, 100)` raises `AnnotationBoundsError` or clips and returns a warning; elements fully within bounds succeed without warning |

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_renderer.py::test_annotator -q
cd R:/Sandbox/ark && pytest tests/test_visual_renderer.py::test_bounds -q
```

#### 3d. Review Loop (TC-015 through TC-016)

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-015 | `test_review_manifest` | `ReviewLoop.run(visual_spec, render_fn=stub, feedback_fn=stub_approved)` returns a dict with keys `status`, `render_path`, `feedback`, `timestamp`; `status` is `"approved"` when `feedback_fn` returns `FeedbackStatus.approved` |
| TC-016 | `test_feedback_parse` | `ReviewLoop.parse_feedback(raw_dict)` correctly maps `{"status": "approved"}`, `{"status": "rejected"}`, `{"status": "annotated", "annotations": [...]}`, and `{"status": "pending"}` to the corresponding `FeedbackStatus` variants; unknown status raises `ValueError` |

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_renderer.py::test_review_manifest -q
cd R:/Sandbox/ark && pytest tests/test_visual_renderer.py::test_feedback_parse -q
```

#### 3e. Screenshot Manager (TC-018 through TC-019)

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-018 | `test_screenshot_register` | `ScreenshotManager.register(path, tags=["diagram", "mermaid"])` adds an entry to the catalog with `path`, `tags`, `timestamp` fields; `get(path)` returns the registered entry with all fields intact |
| TC-019 | `test_catalog_roundtrip` | `ScreenshotManager(catalog_path=tmp_path/"catalog.json").register(...)` persists the catalog to disk; a new `ScreenshotManager(catalog_path=...)` loaded from the same file returns the same entry via `get()` |

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_renderer.py::test_screenshot_register -q
cd R:/Sandbox/ark && pytest tests/test_visual_renderer.py::test_catalog_roundtrip -q
```

#### 3f. Search (TC-020 through TC-021)

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-020 | `test_keyword_search` | `VisualSearch.search(query="architecture", mode=SearchMode.keyword, catalog=catalog_dict)` with a catalog containing entries whose descriptions include "architecture" returns those entries; entries without the keyword are excluded |
| TC-021 | `test_tag_search` | `VisualSearch.search(query=None, mode=SearchMode.tag, tags=["mermaid", "diagram"], catalog=catalog_dict)` returns only entries whose `tags` include all specified tags; entries matching only one tag or neither are excluded |

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_renderer.py::test_keyword_search -q
cd R:/Sandbox/ark && pytest tests/test_visual_renderer.py::test_tag_search -q
```

**Full renderer suite proof command:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_renderer.py -q
```

---

### 4. Verification Tests — `tests/test_visual_verify.py`

Covers TC-025 through TC-029 and TC-017. Tests that `tools/verify/visual_verify.py` catches
invalid DiagramType references, invalid `visual_review` targets, annotation coordinate violations
(via Z3), invalid render config dimensions (via Z3), and review cycle acyclicity (via Z3).

**Fixture approach**: Direct unit tests against `visual_verify.py` functions using in-memory AST
dicts. "Failing" tests assert the returned result list contains at least one entry with
`status="fail"` and a meaningful `message`. "Passing" tests assert all entries have `status="pass"`.
Z3 constraint tests construct minimal constraint objects and pass them to the Z3-backed verifier.
Acyclicity tests build a small graph dict mapping review names to their target references.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-017 | `test_review_acyclicity` | `verify_review_cycles(reviews)` where `review_a.target = "review_b"` and `review_b.target = "review_a"` returns `status="fail"` with a message mentioning "cycle"; a non-cyclic chain `review_a → diagram_x` returns `status="pass"` |
| TC-025 | `test_diagram_type_valid` | `verify_diagram_types([diagram_ast], valid_types=DiagramType.values())` with `diagram.type = "mermaid"` returns `status="pass"`; with `diagram.type = "unknown_type"` returns `status="fail"` with message mentioning the invalid type name |
| TC-026 | `test_review_target` | `verify_review_targets([review_ast], all_visual_items)` where `review.target = "nonexistent_diagram"` returns `status="fail"`; where `review.target` names an existing `diagram` or `preview` item returns `status="pass"` |
| TC-027 | `test_annotation_bounds_z3` | `verify_annotation_bounds_z3([annotation_ast])` with annotation elements whose `x=50, y=50` and `bounds=(100, 100)` returns `status="pass"`; with `x=150, y=50` (exceeds width) returns `status="fail"` with Z3 counterexample detail |
| TC-028 | `test_render_config_z3` | `verify_render_config_z3([render_config_ast])` with `width=1920, height=1080` returns `status="pass"`; with `width=0` returns `status="fail"`; with `width=-1` returns `status="fail"`; with `width=100001` (exceeds max) returns `status="fail"` |
| TC-029 | `test_review_acyclic_z3` | `verify_review_acyclic_z3(reviews)` assigns Z3 ordinal variables to each review; a cyclic graph (A→B→A) produces `unsat` / `status="fail"`; an acyclic graph (A→B→diagram) returns `status="pass"` |

Additional test functions:
- `test_diagram_type_all_valid_variants` — each valid `DiagramType` variant passes `verify_diagram_types` without fail
- `test_review_target_preview_valid` — `visual_review.target` referencing a `preview` item (not only `diagram`) passes
- `test_annotation_bounds_edge_exactly_at_bound` — element at exactly `(width, height)` boundary is accepted
- `test_render_config_z3_max_dimension` — boundary dimension (e.g., `width=10000`) passes; `width=10001` fails
- `test_review_acyclic_z3_longer_chain` — chain of 5 acyclic reviews all pass; adding a back-edge to the first fails

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_verify.py::test_diagram_type_valid -q
cd R:/Sandbox/ark && pytest tests/test_visual_verify.py::test_review_target -q
cd R:/Sandbox/ark && pytest tests/test_visual_verify.py::test_annotation_bounds_z3 -q
cd R:/Sandbox/ark && pytest tests/test_visual_verify.py::test_render_config_z3 -q
cd R:/Sandbox/ark && pytest tests/test_visual_verify.py::test_review_acyclic_z3 -q
cd R:/Sandbox/ark && pytest tests/test_visual_verify.py -q
```

---

### 5. Codegen Tests — `tests/test_visual_codegen.py`

Covers TC-030 through TC-033. Tests that `tools/codegen/visual_codegen.py` generates `.mmd`
files from `diagram` items, `.html` files from `preview` items, annotation overlay JSON from
`annotation` items, and render config JSON from `render_config` items.

**Fixture approach**: Direct unit tests against `visual_codegen.py` functions using in-memory
AST dicts. Output is written to `tmp_path` (pytest built-in). Tests assert on the existence of
the output file, its extension, and key structural content (e.g., JSON decodeable, HTML tag
present, `.mmd` preamble line). No real Ark file parsing needed — tests construct minimal AST
dicts directly.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-030 | `test_codegen_mmd` | `codegen_diagram(diagram_ast, out_dir=tmp_path)` with a `diagram` AST dict containing `name="arch_overview"`, `type="flowchart"`, `source="graph LR; A-->B"` writes a file `arch_overview.mmd` in `tmp_path`; file content starts with `graph` or `flowchart`; the source content is present verbatim |
| TC-031 | `test_codegen_html` | `codegen_preview(preview_ast, out_dir=tmp_path)` with a `preview` AST dict containing `name="component_preview"`, `source="<div>Hello</div>"` writes `component_preview.html` in `tmp_path`; file starts with `<!DOCTYPE html>`; the source `<div>` is embedded in the body |
| TC-032 | `test_codegen_annotation` | `codegen_annotation(annotation_ast, out_dir=tmp_path)` with an `annotation` AST dict containing `name="review_markup"`, `elements=[{type: "rect", x:10, y:10, w:50, h:50}]` writes `review_markup.json` in `tmp_path`; JSON decodes to a dict with `name` and `elements` keys; the element list contains the rect |
| TC-033 | `test_codegen_render_config` | `codegen_render_config(render_config_ast, out_dir=tmp_path)` with a `render_config` AST dict writes `{name}.json` in `tmp_path`; JSON decodes to a dict with `format`, `width`, `height`, `theme` keys matching the input AST |

Additional test functions:
- `test_codegen_mmd_all_diagram_types` — `codegen_diagram` with each `DiagramType` variant produces a non-empty `.mmd` file
- `test_codegen_html_viewport_meta` — `codegen_preview` with `viewport={width:375, height:812}` embeds a viewport meta tag or CSS width constraint
- `test_codegen_annotation_multiple_elements` — annotation with `rect`, `arrow`, `text`, `blur` elements all appear in the output JSON
- `test_codegen_render_config_format_field` — `RenderFormat.svg` maps to `"svg"` in the output JSON `format` field

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_codegen.py::test_codegen_mmd -q
cd R:/Sandbox/ark && pytest tests/test_visual_codegen.py::test_codegen_html -q
cd R:/Sandbox/ark && pytest tests/test_visual_codegen.py::test_codegen_annotation -q
cd R:/Sandbox/ark && pytest tests/test_visual_codegen.py::test_codegen_render_config -q
cd R:/Sandbox/ark && pytest tests/test_visual_codegen.py -q
```

---

### 6. Integration Tests — `tests/test_visual_integration.py`

Covers TC-022 through TC-024 and TC-034 through TC-037. Tests end-to-end workflows: the visual
runner dispatching to renderers, the `ark visual` CLI subcommand, the visual island spec
parsing and verification, example specs producing rendered output, the extended visualizer
rendering visual pipeline items, and `VisualIsland` registration in `root.ark`.

**Fixture approach**: Runner tests use minimal in-memory spec lists and stub renderer functions
to avoid I/O in the unit path. CLI tests use `subprocess.run(['python', 'ark.py', 'visual', ...])`.
Spec and island tests are `@pytest.mark.integration` — they operate on real files in `specs/` and
`dsl/stdlib/` on disk. Visualizer tests call `ark_visualizer.py` functions directly on a small
in-memory `ArkFile` that includes `diagram` and `visual_review` items.

#### 6a. Visual Runner (TC-022 through TC-023)

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-022 | `test_runner_diagrams` | `VisualRunner.run(specs)` where `specs` contains two `diagram` items calls the mermaid renderer once per diagram; verified by replacing `runner.mermaid_renderer.render` with a spy and asserting `call_count == 2` after `run()` |
| TC-023 | `test_runner_previews` | `VisualRunner.run(specs)` where `specs` contains two `preview` items calls the HTML previewer once per preview; verified by replacing `runner.html_previewer.render` with a spy and asserting `call_count == 2` after `run()` |

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_integration.py::test_runner_diagrams -q
cd R:/Sandbox/ark && pytest tests/test_visual_integration.py::test_runner_previews -q
```

#### 6b. CLI (TC-024)

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-024 | `test_cli_visual` | `subprocess.run(['python', 'ark.py', 'visual', '--help'], cwd=REPO_ROOT)` returns `returncode == 0` and `stdout` contains `"visual"` and `"render"`; `subprocess.run(['python', 'ark.py', 'visual', 'specs/visual_example.ark'], cwd=REPO_ROOT)` returns `returncode == 0` |

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_integration.py::test_cli_visual -q
```

#### 6c. Reflexive Specs (TC-034 through TC-035)

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-034 | `test_visual_island_spec` | `parse_file("specs/visual_island.ark")` returns an `ArkFile` with at least one `island` item named `VisualIsland`; `verify("specs/visual_island.ark")` returns all checks passing (`status="pass"` for all verify results) |
| TC-035 | `test_example_specs` | `VisualRunner.run_file("specs/visual_example.ark")` with at least one `diagram` or `preview` item produces at least one output file in the designated output directory; no exceptions are raised during the run |

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_integration.py::test_visual_island_spec -q
cd R:/Sandbox/ark && pytest tests/test_visual_integration.py::test_example_specs -q
```

#### 6d. Visualizer Extension (TC-036)

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-036 | `test_visualizer_visual` | `ark_visualizer.generate_graph(arkfile)` with an `ArkFile` containing `diagram` and `visual_review` items returns an HTML string that contains node labels for the diagram name and the review name; the HTML graph includes edges between `diagram` → renderer and `visual_review` → diagram source |

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_integration.py::test_visualizer_visual -q
```

#### 6e. Root Registration (TC-037)

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-037 | `test_visual_island_in_root` | `subprocess.run(['python', 'ark.py', 'parse', 'specs/root.ark'], cwd=REPO_ROOT, capture_output=True)` returns `returncode == 0`; the JSON output contains an item with `name = "VisualIsland"` and `kind = "island"` in the registry |

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_integration.py::test_visual_island_in_root -q
python ark.py parse specs/root.ark
```

**Full integration suite proof command:**
```bash
cd R:/Sandbox/ark && pytest tests/test_visual_integration.py -q
cd R:/Sandbox/ark && pytest tests/test_visual_integration.py -m "not integration" -q
cd R:/Sandbox/ark && pytest tests/test_visual_integration.py -m integration -q
```

---

## TC Coverage Summary

| TC | Test File | Test Function | Proof Method |
|----|-----------|---------------|--------------|
| TC-001 | test_visual_schema.py | `test_visual_ark_parses` | autotest |
| TC-002 | test_visual_schema.py | `test_visual_types` | autotest |
| TC-003 | test_visual_parser.py | `test_grammar_items` | autotest |
| TC-004 | test_visual_parser.py | (manual inspection) | manual |
| TC-005 | test_visual_parser.py | `test_ast_dataclasses` | autotest |
| TC-006 | test_visual_parser.py | `test_parser_smoke` | autotest |
| TC-007 | test_visual_parser.py | `test_arkfile_indices` | autotest |
| TC-008 | test_visual_renderer.py | `test_mermaid_mmd` | autotest |
| TC-009 | test_visual_renderer.py | `test_diagram_types` | autotest |
| TC-010 | test_visual_renderer.py | `test_mermaid_errors` | autotest |
| TC-011 | test_visual_renderer.py | `test_html_preview` | autotest |
| TC-012 | test_visual_renderer.py | `test_viewports` | autotest |
| TC-013 | test_visual_renderer.py | `test_annotator` | autotest |
| TC-014 | test_visual_renderer.py | `test_bounds` | autotest |
| TC-015 | test_visual_renderer.py | `test_review_manifest` | autotest |
| TC-016 | test_visual_renderer.py | `test_feedback_parse` | autotest |
| TC-017 | test_visual_verify.py | `test_review_acyclicity` | autotest |
| TC-018 | test_visual_renderer.py | `test_screenshot_register` | autotest |
| TC-019 | test_visual_renderer.py | `test_catalog_roundtrip` | autotest |
| TC-020 | test_visual_renderer.py | `test_keyword_search` | autotest |
| TC-021 | test_visual_renderer.py | `test_tag_search` | autotest |
| TC-022 | test_visual_integration.py | `test_runner_diagrams` | autotest |
| TC-023 | test_visual_integration.py | `test_runner_previews` | autotest |
| TC-024 | test_visual_integration.py | `test_cli_visual` | autotest |
| TC-025 | test_visual_verify.py | `test_diagram_type_valid` | autotest |
| TC-026 | test_visual_verify.py | `test_review_target` | autotest |
| TC-027 | test_visual_verify.py | `test_annotation_bounds_z3` | autotest |
| TC-028 | test_visual_verify.py | `test_render_config_z3` | autotest |
| TC-029 | test_visual_verify.py | `test_review_acyclic_z3` | autotest |
| TC-030 | test_visual_codegen.py | `test_codegen_mmd` | autotest |
| TC-031 | test_visual_codegen.py | `test_codegen_html` | autotest |
| TC-032 | test_visual_codegen.py | `test_codegen_annotation` | autotest |
| TC-033 | test_visual_codegen.py | `test_codegen_render_config` | autotest |
| TC-034 | test_visual_integration.py | `test_visual_island_spec` | autotest |
| TC-035 | test_visual_integration.py | `test_example_specs` | autotest |
| TC-036 | test_visual_integration.py | `test_visualizer_visual` | autotest |
| TC-037 | test_visual_integration.py | `test_visual_island_in_root` | poc |

**Total: 37 TCs mapped — 36 autotest, 1 manual (TC-004 Pest grammar inspection)**

---

## Full Suite Proof Command

```bash
cd R:/Sandbox/ark && pytest tests/test_visual_schema.py tests/test_visual_parser.py tests/test_visual_renderer.py tests/test_visual_verify.py tests/test_visual_codegen.py tests/test_visual_integration.py -q
```

Or to run all visual tests at once:

```bash
cd R:/Sandbox/ark && pytest tests/test_visual_*.py -q
```
