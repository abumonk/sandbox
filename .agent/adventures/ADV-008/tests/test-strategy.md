# Test Strategy — ADV-008: ShapeML-style Procedural Shape Grammar

**Author**: geometry-engineer (ADV008-T02)
**Date**: 2026-04-14
**Phase**: A (Research & Design)
**Status**: Authored before T07+ implementation starts (satisfies TC-22)

---

## 1. Test File Layout

All test files live under `shape_grammar/tests/` — a sibling directory to `ark/` in `R:/Sandbox/`. The test package depends on the `shape_grammar` package, never on `ark/` internals. Ark is only reached via CLI subprocess or the public `ark_parser` library surface — consistent with ADR-001.

### `shape_grammar/tests/conftest.py`

**Scope**: Shared fixtures available to every test module via pytest's automatic conftest discovery.

**Owned by**: T09 (authored alongside test_ir.py and test_verifier.py; extended by T18).

**Contents**:
- `spec_island_paths` — list of `pathlib.Path` objects for the four canonical example islands (`l_system.ark`, `cga_tower.ark`, `semantic_facade.ark`, `code_graph_viz.ark`).
- `canonical_ir` — a pre-extracted `ShapeGrammarIR` from `l_system.ark` (simplest grammar; serves as baseline for IR shape assertions).
- `rng_seed` — integer fixture pinned to `42`; used by all evaluator and RNG determinism tests.
- `unbounded_fixture_path` — `pathlib.Path` to `shape_grammar/tests/fixtures/unbounded.ark`; used by the negative termination test (TC-04d).

---

### `shape_grammar/tests/test_ir.py`

**Scope**: IR extraction layer — `shape_grammar/tools/ir.py`. Verifies that `extract_ir()` returns a well-formed `ShapeGrammarIR` for every spec island and that error paths raise correctly.

**Owned by**: T09

**Planned test functions**:

| Function | What it covers |
|---|---|
| `test_ir_roundtrip_each_spec_island` | Parametrized over all 4 example islands; asserts `ShapeGrammarIR` is returned, fields non-empty. (TC-03) |
| `test_ir_fields_populated` | Asserts `max_depth > 0`, `seed` is int, `axiom` non-empty, `rules` non-empty on canonical IR. |
| `test_ir_rule_count_l_system` | Asserts exactly N rules for `l_system.ark` (known count). |
| `test_ir_missing_island_raises` | Passes a `.ark` file with no `ShapeGrammar` island; asserts `IRError`. |
| `test_ir_missing_operations_raises` | Passes a rule stub with no `operations` field; asserts `IRError`. |
| `test_ir_nonpositive_max_depth_raises` | Passes island with `max_depth: 0`; asserts `IRError`. |
| `test_ir_provenance_seeds_axiom` | Asserts `provenance` dict has an entry for the axiom key. |

---

### `shape_grammar/tests/test_verifier.py`

**Scope**: Verifier passes — `shape_grammar/tools/verify/termination.py`, `determinism.py`, `scope.py`. Verifies that all three passes PASS on the four example grammars, and that the termination pass correctly FAILs on the `unbounded.ark` counterexample.

**Owned by**: T09

**Planned test functions**:

| Function | What it covers |
|---|---|
| `test_termination_pass_all_examples` | Parametrized over 4 example islands; asserts `verify_termination(ir)` returns PASS or PASS_OPAQUE. (TC-04a) |
| `test_determinism_pass_all_examples` | Parametrized over 4 example islands; asserts `verify_determinism(ir)` returns PASS. (TC-04b) |
| `test_scope_pass_all_examples` | Parametrized over 4 example islands; asserts `verify_scope(ir)` returns PASS. (TC-04c) |
| `test_termination_fails_on_unbounded_fixture` | Loads `fixtures/unbounded.ark`; asserts `verify_termination(ir)` returns FAIL with a counter-example dict. (TC-04d) |
| `test_determinism_fails_on_env_read` | Passes a crafted IR with a wall-clock reference; asserts `verify_determinism(ir)` returns FAIL. |
| `test_scope_fails_on_undefined_attr` | Passes a crafted IR with a `scope.get("missing")` call; asserts `verify_scope(ir)` returns FAIL with a path witness. |
| `test_verify_all_cli_exits_zero` | Subprocess call `python -m shape_grammar.tools.verify all l_system.ark`; asserts exit code 0. |

---

### `shape_grammar/tests/test_evaluator.py`

**Scope**: Python evaluator — `shape_grammar/tools/evaluator.py`, `ops.py`, `scope.py`, `rng.py`, `obj_writer.py`. Verifies deterministic round-trip, RNG reproducibility, OBJ emission, and error paths.

**Owned by**: T18

**Planned test functions**:

| Function | What it covers |
|---|---|
| `test_deterministic_roundtrip` | Calls `evaluate(ir, seed=42)` twice; asserts terminal lists are identical. (TC-05) |
| `test_grammar_to_obj_nonempty` | Calls `evaluate` then `write_obj`; asserts emitted file size > 0. (TC-07) |
| `test_rng_determinism` | Calls `SeededRng(42).fork("a")` twice; asserts both produce same sequence of 10 values. (TC-19) |
| `test_rng_fork_isolation` | Asserts `fork("a")` and `fork("b")` produce distinct sequences. |
| `test_scope_inheritance` | Pushes a scope with `color=red`; asserts child scope inherits `color`. |
| `test_scope_override` | Pushes a scope with `color=red`; child overrides with `color=blue`; asserts override is effective. |
| `test_extrude_op_applies` | Constructs `ExtrudeOp(height=5.0)`; asserts `apply()` yields a child scope with `size.z` updated. |
| `test_split_op_yields_n_children` | Constructs `SplitOp(axis="X", sizes=[1.0, 2.0, 1.0])`; asserts 3 child scopes returned. |
| `test_max_depth_guard` | Feeds IR with `max_depth=0` directly to evaluator; asserts `EvaluationError`. |
| `test_obj_groups_match_labels` | Calls `write_obj` on terminals with two distinct labels; asserts OBJ contains two `g` directives. |

---

### `shape_grammar/tests/test_semantic.py`

**Scope**: Semantic label propagation — `shape_grammar/tools/semantic.py`. Verifies that every terminal carries a non-null label (inherited or overridden) and that provenance chains are complete.

**Owned by**: T18

**Planned test functions**:

| Function | What it covers |
|---|---|
| `test_every_terminal_has_label` | Runs `evaluate` on `semantic_facade.ark`; asserts every terminal has `label.name` non-empty. (TC-08) |
| `test_label_inheritance_propagates` | Verifies a terminal deep in the derivation inherits the root label when no override is present. |
| `test_label_override_wins` | Verifies a rule that overrides label produces a terminal with the overriding label, not the parent's. |
| `test_provenance_chain_depth_matches_derivation` | Asserts `terminal.provenance.depth == len(terminal.provenance.rule_chain)` for all terminals. |
| `test_provenance_root_is_axiom` | Asserts `terminal.provenance.rule_chain[0] == ir.axiom` for all terminals. |
| `test_label_missing_raises` | Constructs a terminal with `label=None`; asserts `propagate()` raises or fills in the default label. |

---

### `shape_grammar/tests/test_integrations.py`

**Scope**: Integration adapters — `shape_grammar/tools/integrations/{visualizer,impact,diff}_adapter.py`. Smoke tests that each adapter completes without error and returns expected structural output. Uses `cga_tower.ark` as input (most representative, no external data deps).

**Owned by**: T18

**Planned test functions**:

| Function | What it covers |
|---|---|
| `test_visualizer_adapter_smoke` | Calls `augment_graph(cga_tower_path, tmp_path / "out.html")`; asserts output HTML exists and contains `class=` injection. (TC-11) |
| `test_impact_adapter_smoke` | Calls `shape_impact(cga_tower_path, "Rule")`; asserts returned dict has keys `impact` and `rule_tree_edges`. (TC-12) |
| `test_diff_adapter_smoke` | Calls `shape_diff(l_system_path, cga_tower_path)`; asserts returned dict has keys `structural_diff` and `rule_diff`. (TC-13) |
| `test_all_adapters_green` | Calls all three adapters in sequence on a single grammar; asserts no adapter raises. (TC-14, umbrella) |
| `test_visualizer_adapter_error_path` | Passes a non-existent file; asserts `AdapterError` is raised with context message. |
| `test_impact_adapter_unknown_entity` | Passes an entity name that doesn't exist in the grammar; asserts empty rule_tree_edges (not an error). |

---

### `shape_grammar/tests/test_examples.py`

**Scope**: End-to-end parametric tests over all four example grammars. Each example is verified to pass the full pipeline: Ark parse → IR extraction → all three verifier passes → evaluate → OBJ non-empty.

**Owned by**: T18

**Planned test functions**:

| Function | What it covers |
|---|---|
| `test_all_examples_parse_verify_ir_evaluate` | Parametrized over 4 islands; for each: `ark verify` exits 0, `extract_ir` succeeds, all 3 verifier passes return PASS/PASS_OPAQUE, `evaluate` returns ≥1 terminal, `write_obj` produces a non-empty file. (TC-20) |
| `test_l_system_terminal_count` | Asserts `l_system.ark` produces exactly N terminals for seed=42 (regression guard). |
| `test_cga_tower_obj_groups` | Asserts `cga_tower.ark` OBJ output contains ≥2 `g` group directives. |
| `test_semantic_facade_has_window_label` | Asserts at least one terminal from `semantic_facade.ark` carries label `window`. |
| `test_code_graph_viz_has_abstraction_label` | Asserts at least one terminal from `code_graph_viz.ark` carries label `abstraction`. |

---

### `shape_grammar/tests/fixtures/unbounded.ark`

**Scope**: Deliberate counterexample for TC-04d. An Ark island that declares a `ShapeGrammar` with a rule that self-recurses with no base case and no depth-decrement — exactly the construct the termination verifier pass must flag as FAIL.

**Owned by**: T09

**Content intent**: Minimal grammar with one rule `A → A` (no terminal exit) and `max_depth: 10`. When fed to `verify_termination`, Z3 must find a derivation of depth 11 (satisfiable) and return FAIL with a counter-example node.

---

## 2. TC → Test-Function Mapping

All `proof_method: autotest` target conditions from the manifest, each mapped to a specific test file and function.

| TC-ID | Description | Test File | Test Function | Assertion Summary |
|-------|-------------|-----------|---------------|-------------------|
| TC-03 | IR extraction returns populated ShapeGrammarIR from every spec island | `test_ir.py` | `test_ir_roundtrip_each_spec_island` | Parametrized over 4 islands; asserts non-None ShapeGrammarIR with non-empty rules, valid max_depth/seed/axiom |
| TC-04a | Termination pass passes on all 4 examples | `test_verifier.py` | `test_termination_pass_all_examples` | Parametrized over 4 islands; result.status in {"PASS", "PASS_OPAQUE"} |
| TC-04b | Determinism pass passes on all 4 examples | `test_verifier.py` | `test_determinism_pass_all_examples` | Parametrized over 4 islands; result.status == "PASS" |
| TC-04c | Scope-safety pass passes on all 4 examples | `test_verifier.py` | `test_scope_pass_all_examples` | Parametrized over 4 islands; result.status == "PASS" |
| TC-04d | Termination pass FAILs on unbounded-derivation counterexample | `test_verifier.py` | `test_termination_fails_on_unbounded_fixture` | result.status == "FAIL"; result.counter_example is not None |
| TC-05 | Python evaluator round-trip is deterministic under fixed seed | `test_evaluator.py` | `test_deterministic_roundtrip` | Two calls with seed=42 produce identical terminal lists |
| TC-07 | End-to-end grammar → evaluator → OBJ produces non-empty file | `test_evaluator.py` | `test_grammar_to_obj_nonempty` | `os.path.getsize(out_obj) > 0` |
| TC-08 | Every terminal carries an inherited-or-overridden semantic label | `test_semantic.py` | `test_every_terminal_has_label` | `all(t.label.name for t in terminals)` over semantic_facade.ark |
| TC-11 | Visualizer adapter produces annotated HTML | `test_integrations.py` | `test_visualizer_adapter_smoke` | Output HTML exists; file contains at least one injected CSS class attribute |
| TC-12 | Impact adapter returns augmented report with rule-tree edges | `test_integrations.py` | `test_impact_adapter_smoke` | Return dict has `"rule_tree_edges"` key; value is a list |
| TC-13 | Diff adapter returns rule-tree structural diff | `test_integrations.py` | `test_diff_adapter_smoke` | Return dict has `"rule_diff"` key with added/removed/modified sub-keys |
| TC-14 | Full integration adapter test suite green | `test_integrations.py` | `test_all_adapters_green` | All three adapters complete without exception; results non-empty |
| TC-19 | RNG determinism: SeededRng(42).fork("a") reproduces identical sequence | `test_evaluator.py` | `test_rng_determinism` | Two independent calls to `SeededRng(42).fork("a")` yield the same 10-element random sequence |
| TC-20 | Example-driven end-to-end: parse + verify + IR + evaluate each of 4 examples | `test_examples.py` | `test_all_examples_parse_verify_ir_evaluate` | Parametrized over 4 islands; full pipeline passes; ≥1 terminal per grammar; OBJ non-empty |
| TC-21 | Full shape_grammar test suite green | (umbrella) | `pytest shape_grammar/tests/ -q` | All tests in all 6 files pass |

---

## 3. Fixture Strategy

All fixtures are defined in `shape_grammar/tests/conftest.py` and auto-injected by pytest.

### `spec_island_paths` (list fixture)

```python
@pytest.fixture
def spec_island_paths(tmp_path) -> list[Path]:
    base = Path("shape_grammar/examples")
    return [
        base / "l_system.ark",
        base / "cga_tower.ark",
        base / "semantic_facade.ark",
        base / "code_graph_viz.ark",
    ]
```

Used by: `test_ir_roundtrip_each_spec_island`, `test_termination_pass_all_examples`, `test_determinism_pass_all_examples`, `test_scope_pass_all_examples`, `test_all_examples_parse_verify_ir_evaluate`.

Parametrization: tests that use this fixture are decorated with `@pytest.mark.parametrize` over the returned list (or the fixture is itself parametrized via `params`).

### `canonical_ir` (ShapeGrammarIR fixture)

```python
@pytest.fixture
def canonical_ir() -> ShapeGrammarIR:
    from shape_grammar.tools.ir import extract_ir
    return extract_ir(Path("shape_grammar/examples/l_system.ark"))
```

Provides a real `ShapeGrammarIR` from the simplest grammar for use in structural assertions. Used by: `test_ir_fields_populated`, `test_ir_rule_count_l_system`, `test_deterministic_roundtrip`, `test_rng_determinism`.

### `rng_seed` (int fixture)

```python
@pytest.fixture
def rng_seed() -> int:
    return 42
```

Pinned constant. All evaluator tests that require a seed use this fixture so the pin is in one place. If the seed must change (e.g. to expose a flaky ordering), it changes here only.

### `unbounded_fixture_path` (Path fixture)

```python
@pytest.fixture
def unbounded_fixture_path() -> Path:
    return Path("shape_grammar/tests/fixtures/unbounded.ark")
```

Resolves the path to the deliberate counterexample fixture. Used exclusively by `test_termination_fails_on_unbounded_fixture` (TC-04d). The fixture file itself is created by T09 when implementing `test_verifier.py`.

---

## 4. Pytest Invocation Commands

Every command below matches its corresponding proof command in the manifest `## Target Conditions` table.

### Per-file commands

```bash
# TC-03: IR extraction
pytest shape_grammar/tests/test_ir.py -q

# TC-04a: Termination pass (positive)
pytest shape_grammar/tests/test_verifier.py -k termination -q

# TC-04b: Determinism pass (positive)
pytest shape_grammar/tests/test_verifier.py -k determinism -q

# TC-04c: Scope pass (positive)
pytest shape_grammar/tests/test_verifier.py -k scope -q

# TC-04d: Termination pass (negative — unbounded fixture)
pytest shape_grammar/tests/test_verifier.py -k unbounded -q

# TC-05 + TC-07 + TC-19: Evaluator suite
pytest shape_grammar/tests/test_evaluator.py -q

# TC-08: Semantic label propagation
pytest shape_grammar/tests/test_semantic.py -q

# TC-11 + TC-12 + TC-13 + TC-14: Integration adapters
pytest shape_grammar/tests/test_integrations.py -q
# Individual adapter smoke tests:
pytest shape_grammar/tests/test_integrations.py -k visualizer -q
pytest shape_grammar/tests/test_integrations.py -k impact -q
pytest shape_grammar/tests/test_integrations.py -k diff -q

# TC-19: RNG determinism only
pytest shape_grammar/tests/test_evaluator.py -k rng_determinism -q

# TC-20: End-to-end examples
pytest shape_grammar/tests/test_examples.py -q
```

### Umbrella command (TC-21)

```bash
pytest shape_grammar/tests/ -q
```

This is the canonical "all green" gate. It must pass before the adventure is declared done (TC-21 closes at adventure-close, owned by T09, T18, T19).

### Verbose / CI variant

```bash
pytest shape_grammar/tests/ -v --tb=short
```

---

## 5. Negative-Test Coverage Guarantee

Every test file in `shape_grammar/tests/` owns at least one negative or error-path test. In `test_ir.py` this means `test_ir_missing_island_raises`, `test_ir_missing_operations_raises`, and `test_ir_nonpositive_max_depth_raises` — each asserting that `IRError` is raised on malformed input. In `test_verifier.py` this means `test_termination_fails_on_unbounded_fixture` (TC-04d) plus `test_determinism_fails_on_env_read` and `test_scope_fails_on_undefined_attr`. In `test_evaluator.py` this means `test_max_depth_guard`, which feeds the evaluator an IR whose `max_depth` is 0 and asserts `EvaluationError`. In `test_semantic.py` this means `test_label_missing_raises`, which asserts that the propagation step either raises or fills in a default label when a terminal has no label at all. In `test_integrations.py` this means `test_visualizer_adapter_error_path` (non-existent file → `AdapterError`) and `test_impact_adapter_unknown_entity` (entity not in grammar → empty edge list, no crash). In `test_examples.py` error coverage is provided by the positive parametric tests themselves: any island that fails `ark verify`, IR extraction, or evaluation will cause the parametrized test to fail with a traceback that identifies which phase and which example broke. This design ensures that a broken implementation cannot silently produce empty output that passes assertions — every module's contract is exercised on both valid and invalid inputs.

---

## 6. Dependency Note — Test Strategy Before Implementation (TC-22)

TC-22 records the pattern "Test strategy authored before implementation starts." ADV008-T02 (this document) is explicitly listed in the plan as a Phase A task with no dependencies (`depends_on: []`). It runs concurrently with T01 (ShapeML research) and T03 (feasibility study) and must complete before T07 (IR implementation) or T08 (verifier passes) can begin. This ordering is enforced in the task graph: T03 depends on [T01, T02], and T07+ depend on T03. The proof command for TC-22 is simply `test -f .agent/adventures/ADV-008/tests/test-strategy.md` — this file's existence at Phase A close, before any `shape_grammar/tools/` code exists, satisfies the condition. Implementer tasks T09 and T18 are then bound by this document: they must write exactly the test functions named here, in exactly the files named here, so that the TC → test-function table above remains accurate at review time.

---

## Appendix: Test File Ownership Summary

| File | Owner Task | TC(s) covered |
|------|-----------|---------------|
| `conftest.py` | T09 (extended by T18) | (shared — supports all) |
| `test_ir.py` | T09 | TC-03 |
| `test_verifier.py` | T09 | TC-04a, TC-04b, TC-04c, TC-04d |
| `test_evaluator.py` | T18 | TC-05, TC-07, TC-19 |
| `test_semantic.py` | T18 | TC-08 |
| `test_integrations.py` | T18 | TC-11, TC-12, TC-13, TC-14 |
| `test_examples.py` | T18 | TC-20 |
| `fixtures/unbounded.ark` | T09 | TC-04d (counterexample) |
| (umbrella) | T09, T18, T19 | TC-21 |
