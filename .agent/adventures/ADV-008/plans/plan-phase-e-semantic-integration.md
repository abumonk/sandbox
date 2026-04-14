# Phase E — Semantic Rendering + Integration

## Designs Covered
- design-semantic-rendering
- design-integrations
- design-evaluator (validation)

## Tasks

### Example grammars (4 examples)
- **ID**: ADV008-T15
- **Description**: Author the 4 example grammars as `.ark` islands: `l_system.ark` (simplest, single self-recursing rule with depth bound), `cga_tower.ark` (split + extrude classic tower), `semantic_facade.ark` (Prototype 1), `code_graph_viz.ark` (Prototype 2 — uses code_graph.ark as input). All four must verify under vanilla `ark verify` and parse via the IR module.
- **Files**: `shape_grammar/examples/l_system.ark`, `shape_grammar/examples/cga_tower.ark`, `shape_grammar/examples/semantic_facade.ark`, `shape_grammar/examples/code_graph_viz.ark`
- **Acceptance Criteria**:
  - All 4 files exist.
  - `for f in shape_grammar/examples/*.ark; do python ark/ark.py verify "$f"; done` all exit 0.
  - `python -m shape_grammar.tools.ir <each>` succeeds on each.
- **Target Conditions**: TC-17
- **Depends On**: [ADV008-T07, ADV008-T13]
- **Evaluation**:
  - Access requirements: Read (shape_grammar/specs/, ark/specs/infra/code_graph.ark), Write (shape_grammar/examples/), Bash (`ark verify`, python)
  - Skill set: Ark DSL, shape grammar authoring
  - Estimated duration: 30min
  - Estimated tokens: 60000

### Semantic-rendering research document
- **ID**: ADV008-T16
- **Description**: Author `.agent/adventures/ADV-008/research/semantic-rendering.md` per `design-semantic-rendering.md` § Research document structure. Must contain exactly two `### Prototype` sections with full step-by-step recipes plus proof commands (one for `semantic_facade.ark`, one for `code_graph_viz.ark`).
- **Files**: `.agent/adventures/ADV-008/research/semantic-rendering.md`
- **Acceptance Criteria**:
  - File exists.
  - `grep -c "### Prototype" research/semantic-rendering.md == 2`.
  - Each prototype has a runnable proof command using `python -m shape_grammar.tools.evaluator`.
- **Target Conditions**: TC-09
- **Depends On**: [ADV008-T13, ADV008-T15]
- **Evaluation**:
  - Access requirements: WebSearch, Read (shape_grammar/, designs/), Write (research/)
  - Skill set: research, technical writing, rendering domain literacy
  - Estimated duration: 30min
  - Estimated tokens: 55000

### Integration adapters
- **ID**: ADV008-T17
- **Description**: Implement `shape_grammar/tools/integrations/{visualizer_adapter,impact_adapter,diff_adapter}.py` per `design-integrations.md`. Each adapter shells out to the corresponding `ark` CLI command and augments output with shape-grammar semantics. No edits to `ark/` source.
- **Files**: `shape_grammar/tools/integrations/__init__.py`, `shape_grammar/tools/integrations/visualizer_adapter.py`, `shape_grammar/tools/integrations/impact_adapter.py`, `shape_grammar/tools/integrations/diff_adapter.py`
- **Acceptance Criteria**:
  - All three adapters expose their public function.
  - Each adapter raises `AdapterError` with a "see research/ark-as-host-feasibility.md" hint if Ark output shape changes.
  - End-to-end smoke: each adapter run on `examples/cga_tower.ark` produces a non-empty result.
- **Target Conditions**: TC-11, TC-12, TC-13
- **Depends On**: [ADV008-T13, ADV008-T15]
- **Evaluation**:
  - Access requirements: Read (ark/tools/), Write (shape_grammar/tools/integrations/), Bash (`ark graph|impact|diff`, python)
  - Skill set: Python, subprocess wrapping
  - Estimated duration: 30min
  - Estimated tokens: 60000

### Evaluator + semantic + integrations + examples tests
- **ID**: ADV008-T18
- **Description**: Write the remaining test files per `tests/test-strategy.md`: `test_evaluator.py` (deterministic round-trip, max-depth guard, OBJ output), `test_semantic.py` (label inheritance, propagation, prototype-1 label set), `test_integrations.py` (each adapter's smoke + error-path), `test_examples.py` (parametric: parse + verify + IR-extract + evaluate each example).
- **Files**: `shape_grammar/tests/test_evaluator.py`, `shape_grammar/tests/test_semantic.py`, `shape_grammar/tests/test_integrations.py`, `shape_grammar/tests/test_examples.py`
- **Acceptance Criteria**:
  - `pytest shape_grammar/tests/ -q` green (combined with test_ir.py + test_verifier.py from T09).
  - All TCs with `proof_method: autotest` have a passing test.
- **Target Conditions**: TC-05, TC-07, TC-08, TC-14, TC-19, TC-20
- **Depends On**: [ADV008-T09, ADV008-T13, ADV008-T15, ADV008-T17]
- **Evaluation**:
  - Access requirements: Read (shape_grammar/), Write (shape_grammar/tests/), Bash (pytest)
  - Skill set: pytest
  - Estimated duration: 30min
  - Estimated tokens: 70000

### Final validation + Ark-untouched proof
- **ID**: ADV008-T19
- **Description**: Run the full end-to-end verification sequence from the pre-approved plan § "Verification — End-to-End": (0) `git diff --stat master -- ark/` empty, (1) `ark verify shape_grammar/specs/shape_grammar.ark`, (2) parse + verify all 4 examples, (3) `pytest shape_grammar/tests/ -v`, (4) round-trip `cga_tower.ark` to OBJ, (5) `cargo check` Rust skeleton. Capture results in `.agent/adventures/ADV-008/research/final-validation.md`. Update manifest. **Mandatory test implementation task closure.**
- **Files**: `.agent/adventures/ADV-008/research/final-validation.md`
- **Acceptance Criteria**:
  - All 6 verification steps green.
  - `git diff --stat master -- ark/` produces empty output (TC-10 proof).
  - Validation report logged with command output for each step.
- **Target Conditions**: TC-10, TC-21
- **Depends On**: [ADV008-T09, ADV008-T14, ADV008-T16, ADV008-T17, ADV008-T18]
- **Evaluation**:
  - Access requirements: Read (shape_grammar/, ark/), Write (research/), Bash (git, ark, pytest, cargo, python)
  - Skill set: integration testing, validation
  - Estimated duration: 25min
  - Estimated tokens: 45000
