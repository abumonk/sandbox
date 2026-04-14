# ADV-004 Test Strategy — Hermes-style Agent Self-Evolution System

## Overview

This document maps every target condition (TC-001 through TC-046) from the ADV-004 manifest
to specific test files, test functions, proof commands, and test runners. Tests are grouped
by subsystem following the Ark project's existing conventions (established in ADV-001, ADV-002,
ADV-003).

### Conventions (aligned with `R:/Sandbox/ark/tests/conftest.py`)

- **pytest** is the primary test runner for all Python code
- Fixtures `parse_src` and `parse_file` are session-scoped in `conftest.py`
- Test files follow `test_evolution_{subsystem}.py` naming
- All test files live under `R:/Sandbox/ark/tests/`
- All commands assume `cd R:/Sandbox/ark` as working directory
- CLI tests use `subprocess.run(['python', 'ark.py', ...], cwd=REPO_ROOT)` and assert `returncode == 0`
- Unit tests use direct Python API calls (no subprocess overhead)
- `@pytest.mark.integration` marks tests requiring real spec files on disk
- A `REPO_ROOT` constant at the top of each test file points to `R:/Sandbox/ark/`

## Proof Methods

- **autotest** — automated pytest or CLI command with deterministic pass/fail
- **poc** — proof-of-concept command that must produce non-trivial output (human judges output)
- **manual** — human inspection of generated artifact

---

## Tests by Subsystem

### 1. Parser Tests — `tests/test_evolution_parser.py`

Covers TC-001 through TC-007. Tests that `evolution.ark` parses cleanly, the Lark grammar
handles all 7 new item kinds, existing files are unaffected, the transformer produces correct
AST dataclasses, and ArkFile indices are populated.

**Fixture approach**: In-memory .ark snippet strings for each of the 7 item kinds. Parser tests
instantiate `ArkParser`, call `parse()` on the snippet, and assert no exception. AST tests
assert field values on the returned dataclasses. Regression tests call the parser on real files
under `dsl/stdlib/` and `specs/`. For stdlib tests, parse the real file at
`dsl/stdlib/evolution.ark` and inspect the result.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-001 | `test_stdlib_parse` | `dsl/stdlib/evolution.ark` parses via `ArkParser` without raising exceptions |
| TC-002 | `test_stdlib_syntax` | All enum and struct definitions in `evolution.ark` match existing stdlib patterns — `EvolutionTier`, `OptimizerEngine`, `DataSource`, `FitnessScore`, `RunResult`, `Variant`, `Constraint`, `BenchmarkResult` are present and well-formed |
| TC-003 | `test_lark_parse_all_items` | One snippet per item kind — `evolution_target`, `eval_dataset`, `fitness_function`, `optimizer`, `benchmark_gate`, `evolution_run`, `constraint` — all parse without errors via Lark grammar |
| TC-004 | (manual — inspect pest rules) | Pest grammar `ark.pest` mirrors Lark rules for all 7 items — human inspection |
| TC-005 | `test_existing_files_parse` | Representative existing .ark files (`specs/meta/ark_studio.ark`, `dsl/stdlib/studio.ark`, `dsl/stdlib/types.ark`) still parse after grammar extension |
| TC-006 | `test_ast_dataclasses` | Parsing each item kind snippet produces the correct AST dataclass: `EvolutionTargetDef`, `EvalDatasetDef`, `FitnessFunctionDef`, `OptimizerDef`, `BenchmarkGateDef`, `EvolutionRunDef`, `ConstraintDef` — key fields match input |
| TC-007 | `test_arkfile_indices` | Parsing a multi-item .ark snippet populates `arkfile.evolution_targets`, `arkfile.eval_datasets`, `arkfile.fitness_functions`, `arkfile.optimizers`, `arkfile.benchmark_gates`, `arkfile.evolution_runs`, `arkfile.constraints` with correct keys |

Additional test functions (supporting TC-002):
- `test_evolution_tier_enum_values` — `EvolutionTier` has `skill`, `tool_desc`, `system_prompt`, `code` variants
- `test_optimizer_engine_enum_values` — `OptimizerEngine` has `gepa`, `miprov2`, `darwinian` variants
- `test_data_source_enum_values` — `DataSource` has `synthetic`, `session_db`, `golden`, `auto_eval` variants

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_evolution_parser.py::test_stdlib_parse -q
cd R:/Sandbox/ark && pytest tests/test_evolution_parser.py::test_stdlib_syntax -q
cd R:/Sandbox/ark && pytest tests/test_evolution_parser.py::test_lark_parse_all_items -q
cd R:/Sandbox/ark && pytest tests/test_evolution_parser.py -k "not evolution" -q   # TC-005
cd R:/Sandbox/ark && pytest tests/test_evolution_parser.py::test_ast_dataclasses -q
cd R:/Sandbox/ark && pytest tests/test_evolution_parser.py::test_arkfile_indices -q
```

---

### 2. Fitness Tests — `tests/test_evolution_fitness.py`

Covers TC-008 through TC-012. Tests that `tools/evolution/dataset_builder.py` generates valid
evaluation datasets and that `tools/evolution/fitness.py` scores variants correctly.

**Fixture approach**: Direct unit tests against `dataset_builder.py` and `fitness.py` functions.
Dataset tests use a minimal in-memory `EvalDatasetDef` AST dict and a temp skill file. Fitness
tests use a deterministic `judge_fn` callback (keyword matching) to avoid LLM dependency. All
assertions are on return values — no file I/O except where explicitly testing JSONL output.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-008 | `test_dataset_synthetic` | `build_dataset()` called with `source: synthetic` returns a list of dicts, each with `id`, `input`, `expected`, `rubric_hints`, `source`, `split` fields; output is serializable to valid JSONL |
| TC-009 | `test_dataset_splits` | `assign_splits(cases, train=0.7, val=0.15, test=0.15, seed=42)` produces splits with proportions matching within ±1 case; counts sum to `len(cases)`; every case has a `split` field of `train`, `val`, or `test` |
| TC-010 | `test_score_variant` | `score_variant(variant_output, expected, rubric_dimensions, judge_fn)` returns a `FitnessResult` where every dimension score is in `[0.0, 1.0]` and `aggregated` is in `[0.0, 1.0]` |
| TC-011 | `test_aggregation` | `aggregate_scores(scores, "weighted_sum")` computes weighted sum correctly; `aggregate_scores(scores, "min")` returns the minimum; `aggregate_scores(scores, "harmonic")` returns the harmonic mean |
| TC-012 | `test_evaluate_dataset` | `evaluate_dataset(variant_fn, dataset, rubric, judge_fn)` returns an `EvalResult` with `mean_fitness` equal to the mean of per-case `aggregated` scores |

Additional test functions:
- `test_dataset_size_matches_spec` — number of returned cases matches `size` field in dataset AST
- `test_golden_load` — `load_golden(jsonl_path)` parses a JSONL file and returns list of dicts
- `test_fitness_result_penalties` — `score_variant()` populates `penalties` list when a dimension is below threshold
- `test_eval_result_pass_rate` — `pass_rate` in `EvalResult` equals fraction of cases where `aggregated >= threshold`

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_evolution_fitness.py::test_dataset_synthetic -q
cd R:/Sandbox/ark && pytest tests/test_evolution_fitness.py::test_dataset_splits -q
cd R:/Sandbox/ark && pytest tests/test_evolution_fitness.py::test_score_variant -q
cd R:/Sandbox/ark && pytest tests/test_evolution_fitness.py::test_aggregation -q
cd R:/Sandbox/ark && pytest tests/test_evolution_fitness.py::test_evaluate_dataset -q
```

---

### 3. Optimizer Tests — `tests/test_evolution_optimizer.py`

Covers TC-013 through TC-017. Tests that `tools/evolution/optimizer.py` correctly executes
the GEPA-style loop, Pareto-front selection, convergence detection, MIPROv2 fallback, and
Darwinian stub behavior.

**Fixture approach**: All optimizer tests use stub callbacks. `mutate_fn` is a pure function
that appends a marker to track mutation count. `eval_fn` is deterministic: first call returns
fitness 0.4, subsequent calls return 0.4 + 0.1 × generation (to exercise convergence). No LLM
calls, no subprocess overhead. `OptimizerConfig` is constructed in-memory.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-013 | `test_full_loop` | `optimize(seed, config, eval_fn, mutate_fn, constraint_fn)` with `iterations=2` runs at least 2 full generations (init → evaluate → select → mutate → evaluate); `OptimizeResult.generations == 2` |
| TC-014 | `test_pareto` | `select_pareto_front(variants, scores)` with 4 variants where variant A dominates B on all dimensions returns a front that includes A and excludes B; non-dominated variants C and D are both retained |
| TC-015 | `test_convergence` | `optimize()` with `convergence_threshold=0.001` and an `eval_fn` that returns constant fitness stops before `max_iterations` and sets `OptimizeResult.converged = True` |
| TC-016 | `test_miprov2` | `optimize()` with `engine="miprov2"` invokes history-based selection: the `mutate_fn` receives a `reflection` argument that includes history context after generation 1 |
| TC-017 | `test_darwinian_stub` | `optimize()` with `engine="darwinian"` raises `NotImplementedError` with a message containing "Phase 4" or "not implemented" |

Additional test functions:
- `test_population_size_capped` — population after each generation does not exceed `config.population_size`
- `test_reflection_includes_failure_analysis` — `generate_reflection(variant, eval_result)` returns a string mentioning low-scoring dimensions by name

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_evolution_optimizer.py::test_full_loop -q
cd R:/Sandbox/ark && pytest tests/test_evolution_optimizer.py::test_pareto -q
cd R:/Sandbox/ark && pytest tests/test_evolution_optimizer.py::test_convergence -q
cd R:/Sandbox/ark && pytest tests/test_evolution_optimizer.py::test_miprov2 -q
cd R:/Sandbox/ark && pytest tests/test_evolution_optimizer.py::test_darwinian_stub -q
```

---

### 4. Constraint Tests — `tests/test_evolution_constraint.py`

Covers TC-018 through TC-022. Tests that `tools/evolution/constraint_checker.py` correctly
enforces size limits, semantic preservation, caching compatibility, and that `should_block`
returns the right answer.

**Fixture approach**: Direct unit tests against `constraint_checker.py` functions. Size tests
use plain strings of known length. Semantic preservation tests use a stub `judge_fn` that
returns a configurable score. Caching tests check prefix character equality. All tests are
pure function calls with no subprocess or file I/O.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-018 | `test_size_block` | `check_size_limit(original, evolved, threshold=0.20)` with `evolved` 25% larger than `original` returns `ConstraintResult` with `passed=False` and `enforcement="block"` |
| TC-019 | `test_size_pass` | `check_size_limit(original, evolved, threshold=0.20)` with `evolved` 10% larger than `original` returns `ConstraintResult` with `passed=True` |
| TC-020 | `test_semantic` | `check_semantic_preservation(original, evolved, judge_fn)` calls `judge_fn` with both strings; when `judge_fn` returns 0.6 (below default threshold 0.8), result has `passed=False`; when `judge_fn` returns 0.9, result has `passed=True` |
| TC-021 | `test_caching` | `check_caching_compat(original, evolved, prefix_length=100)` passes when first 100 characters are identical; fails when the evolved prefix diverges from original at character 50 |
| TC-022 | `test_should_block` | `should_block(results)` returns `True` only when at least one result has `passed=False` and `enforcement="block"`; returns `False` when all failures are `enforcement="warn"` or all results pass |

Additional test functions:
- `test_check_all_constraints` — `check_all_constraints(original, evolved, constraints)` runs all applicable checks and returns a list of `ConstraintResult` objects
- `test_warn_constraint_not_blocking` — a failing `warn`-level constraint does not cause `should_block` to return `True`

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_evolution_constraint.py::test_size_block -q
cd R:/Sandbox/ark && pytest tests/test_evolution_constraint.py::test_size_pass -q
cd R:/Sandbox/ark && pytest tests/test_evolution_constraint.py::test_semantic -q
cd R:/Sandbox/ark && pytest tests/test_evolution_constraint.py::test_caching -q
cd R:/Sandbox/ark && pytest tests/test_evolution_constraint.py::test_should_block -q
```

---

### 5. Runner Tests — `tests/test_evolution_runner.py`

Covers TC-023 through TC-025. Tests that `tools/evolution/evolution_runner.py` correctly
orchestrates the full pipeline, resolves cross-references from a parsed .ark spec, and halts
on block constraints.

**Fixture approach**: Tests construct a minimal `EvolutionContext` in-memory (no file parsing).
`mutate_fn` and `judge_fn` are stubs. A minimal dataset (2 cases) and a single-dimension rubric
are used to keep the loop fast (1-2 iterations). Block constraint test uses a `constraint_fn`
stub that returns a failing block constraint.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-023 | `test_full_pipeline` | `run_evolution(context)` with valid `EvolutionContext` completes and returns an `EvolutionReport` with `status` in `{"complete", "gated_out"}`, `generations >= 1`, `best_variant` is a string, and `best_fitness` is a float in `[0.0, 1.0]` |
| TC-024 | `test_resolve_refs` | Given an `ArkFile` with all 7 evolution item types defined by name, the runner resolves each `evolution_run` field (`target`, `optimizer`, `dataset`, `gate`) to the correct AST dict — verified by checking `context.target["name"] == run_ast["target"]` etc. |
| TC-025 | `test_block_constraint` | `run_evolution(context)` with a `constraint_fn` stub that always returns a block failure returns an `EvolutionReport` with `status="failed"` and `constraint_violations` containing at least one entry |

Additional test functions:
- `test_report_fitness_history` — `EvolutionReport.fitness_history` has one entry per generation completed
- `test_report_duration` — `EvolutionReport.duration_ms` is a positive integer

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_evolution_runner.py::test_full_pipeline -q
cd R:/Sandbox/ark && pytest tests/test_evolution_runner.py::test_resolve_refs -q
cd R:/Sandbox/ark && pytest tests/test_evolution_runner.py::test_block_constraint -q
```

---

### 6. Integration Tests — `tests/test_evolution_integration.py`

Covers TC-026 through TC-027 (CLI integration), plus TC-037 through TC-044 (visualizer and
reflexive spec tests). End-to-end tests that parse real spec files, execute CLI commands, and
verify visualizer output.

**Fixture approach**: `subprocess.run` calls to `python ark.py` with real .ark spec files.
Assert exit code and, where applicable, parse stdout JSON. Tests requiring spec files that are
created in later tasks are marked `@pytest.mark.integration` and use `pytest.importorskip` /
`pytest.mark.skipif` so they are skipped gracefully when files do not yet exist.

#### CLI Integration (TC-026, TC-027)

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-026 | `test_cli_run` | `python ark.py evolution run specs/meta/evolution_skills.ark --run <run_name>` exits 0 and prints an `EvolutionReport` summary to stdout |
| TC-027 | `test_cli_status` | `python ark.py evolution status specs/meta/evolution_skills.ark` exits 0 and prints a status table listing all `evolution_run` items with their `status` field |

#### Visualizer (TC-037, TC-038, TC-039)

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-037 | `test_viz_nodes` | Calling the visualizer API on a parsed `evolution_skills.ark` returns a graph dict containing nodes for each evolution item kind; node `type` field matches item kind |
| TC-038 | `test_viz_colors` | Generated HTML from `ark graph specs/meta/evolution_skills.ark` contains CSS color assignments for evolution-specific item types (`evolution_target`, `eval_dataset`, `fitness_function`, `optimizer`, `benchmark_gate`, `evolution_run`, `constraint`) |
| TC-039 | (poc) | `python ark.py graph specs/meta/evolution_skills.ark` exits 0 and produces a `.html` output file with non-empty content — human verifies graph renders evolution pipeline |

#### Reflexive Specs (TC-040 through TC-044)

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-040 | `test_skills_parse` | `python ark.py parse specs/meta/evolution_skills.ark` exits 0; Python API parse also succeeds with no exceptions |
| TC-041 | `test_roles_parse` | `python ark.py parse specs/meta/evolution_roles.ark` exits 0; Python API parse also succeeds with no exceptions |
| TC-042 | `test_reflexive_verify` | `python ark.py verify specs/meta/evolution_skills.ark` and `python ark.py verify specs/meta/evolution_roles.ark` both exit 0 with no error results |
| TC-043 | `test_root_registry` | Parsing `specs/root.ark` confirms both `evolution_skills` and `evolution_roles` spec names appear in the import/registry list |
| TC-044 | `test_reflexive_codegen` | `python ark.py codegen specs/meta/evolution_skills.ark --target evolution --out /tmp/evo_test` exits 0 and generates at least one file in `/tmp/evo_test/` |

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_evolution_integration.py::test_cli_run -q
cd R:/Sandbox/ark && pytest tests/test_evolution_integration.py::test_cli_status -q
cd R:/Sandbox/ark && pytest tests/test_evolution_integration.py::test_viz_nodes -q
cd R:/Sandbox/ark && pytest tests/test_evolution_integration.py::test_viz_colors -q
cd R:/Sandbox/ark && python ark.py graph specs/meta/evolution_skills.ark   # TC-039 poc
cd R:/Sandbox/ark && pytest tests/test_evolution_integration.py::test_skills_parse -q
cd R:/Sandbox/ark && pytest tests/test_evolution_integration.py::test_roles_parse -q
cd R:/Sandbox/ark && pytest tests/test_evolution_integration.py::test_reflexive_verify -q
cd R:/Sandbox/ark && pytest tests/test_evolution_integration.py::test_root_registry -q
cd R:/Sandbox/ark && pytest tests/test_evolution_integration.py::test_reflexive_codegen -q
```

---

### 7. Codegen Tests — `tests/test_evolution_codegen.py`

Covers TC-028 through TC-031. Tests that `tools/codegen/evolution_codegen.py` generates valid
JSONL templates, Python scoring skeletons, JSON config files, and that the CLI end-to-end path
works.

**Fixture approach**: Unit tests against `evolution_codegen.py` functions, using minimal AST
dicts as inputs. Output is returned as a string (or written to `tmp_path`). CLI tests use
`subprocess.run` with a `tmp_path` output directory and assert on exit code and file existence.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-028 | `test_dataset_jsonl` | `gen_dataset_jsonl(dataset_ast, output_dir)` with a 3-case dataset AST produces a `.jsonl` file where each line is valid JSON with keys `id`, `input`, `expected`, `rubric_hints`, `source`, `split`; number of lines matches `size` field |
| TC-029 | `test_scoring_script` | `gen_scoring_script(fitness_ast, output_dir)` produces a `.py` file containing: rubric dimension names and weights as constants, an `aggregation` constant, and a `def score(output, expected)` function skeleton |
| TC-030 | `test_run_config` | `gen_run_config(run_ast, all_items, output_dir)` produces a `.json` file that is valid JSON containing keys `target_file`, `dataset_path`, `optimizer`, `gate`; values match the referenced AST items |
| TC-031 | `test_codegen_e2e` | `python ark.py codegen specs/meta/evolution_skills.ark --target evolution --out <tmp_dir>` exits 0; output directory contains subdirectories `datasets/`, `scoring/`, `runs/`; at least one file exists in each |

Additional test functions:
- `test_dataset_jsonl_split_proportions` — lines in each split match the AST-specified ratios (±1 case)
- `test_scoring_script_is_valid_python` — `compile(source, filename, 'exec')` on the generated script raises no `SyntaxError`
- `test_run_config_is_valid_json` — `json.loads()` on the generated config raises no exception

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_evolution_codegen.py::test_dataset_jsonl -q
cd R:/Sandbox/ark && pytest tests/test_evolution_codegen.py::test_scoring_script -q
cd R:/Sandbox/ark && pytest tests/test_evolution_codegen.py::test_run_config -q
cd R:/Sandbox/ark && pytest tests/test_evolution_codegen.py::test_codegen_e2e -q
```

---

### 8. Verification Tests — `tests/test_evolution_verify.py`

Covers TC-032 through TC-036. Tests that `tools/verify/evolution_verify.py` catches
mathematical constraint violations and cross-reference errors, and that `ark verify` invokes
evolution checks.

**Fixture approach**: Direct unit tests against `evolution_verify.py` functions with in-memory
AST dicts. "Failing" tests assert that the returned result list contains at least one entry
with `status="fail"` and a meaningful `message`. "Passing" tests assert all entries have
`status="pass"`. Integration test (TC-036) uses `subprocess.run`.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-032 | `test_split_ratio_fail` | `verify_split_ratios([{"name": "ds1", "split_train": 0.7, "split_val": 0.2, "split_test": 0.2}])` returns a result with `status="fail"` and message mentioning the incorrect sum; valid ratios `(0.7, 0.15, 0.15)` return `status="pass"` |
| TC-033 | `test_weight_fail` | `verify_fitness_weights([{"name": "fn1", "dimensions": [{"weight": 0.6}, {"weight": 0.6}]}])` returns `status="fail"` for weights summing to 1.2; `[0.5, 0.5]` returns `status="pass"` |
| TC-034 | `test_tolerance_fail` | `verify_gate_tolerances([{"name": "gate1", "tolerance": -0.1}])` returns `status="fail"`; `{"tolerance": 0}` returns `status="fail"`; `{"tolerance": 0.05}` returns `status="pass"` |
| TC-035 | `test_xref_fail` | `verify_cross_references([{"name": "run1", "target": "nonexistent_target", ...}], all_items={})` returns `status="fail"` with message mentioning the unknown reference; valid cross-references return `status="pass"` |
| TC-036 | `test_verify_integration` | `python ark.py verify specs/meta/evolution_skills.ark` exits 0 when the spec is valid; a spec with bad split ratios causes exit code != 0 and stderr/stdout contains the error message |

Additional test functions:
- `test_split_ratio_negative_fail` — `verify_split_ratios` catches a negative split value
- `test_weight_negative_fail` — `verify_fitness_weights` catches a negative dimension weight
- `test_constraint_ref_fail` — `verify_constraint_refs` catches a target referencing a non-existent constraint name
- `test_optimizer_param_bounds_fail` — `verify_optimizer_params` catches `iterations=0` or `population=0`

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_evolution_verify.py::test_split_ratio_fail -q
cd R:/Sandbox/ark && pytest tests/test_evolution_verify.py::test_weight_fail -q
cd R:/Sandbox/ark && pytest tests/test_evolution_verify.py::test_tolerance_fail -q
cd R:/Sandbox/ark && pytest tests/test_evolution_verify.py::test_xref_fail -q
cd R:/Sandbox/ark && pytest tests/test_evolution_verify.py::test_verify_integration -q
```

---

## Complete TC-to-Test Mapping

| TC | Description | Test File | Test Function(s) | Runner | Proof Method |
|----|-------------|-----------|-----------------|--------|-------------|
| TC-001 | evolution.ark parses without errors | `test_evolution_parser.py` | `test_stdlib_parse` | pytest | autotest |
| TC-002 | All enums/structs follow existing stdlib patterns | `test_evolution_parser.py` | `test_stdlib_syntax` | pytest | autotest |
| TC-003 | Lark grammar parses all 7 evolution items | `test_evolution_parser.py` | `test_lark_parse_all_items` | pytest | autotest |
| TC-004 | Pest grammar mirrors Lark for all 7 items | (manual inspection) | N/A | manual | manual |
| TC-005 | Existing .ark files parse after grammar changes | `test_evolution_parser.py` | `test_existing_files_parse` | pytest | autotest |
| TC-006 | Parser produces correct AST for 7 evolution types | `test_evolution_parser.py` | `test_ast_dataclasses` | pytest | autotest |
| TC-007 | ArkFile indices populated for evolution items | `test_evolution_parser.py` | `test_arkfile_indices` | pytest | autotest |
| TC-008 | Dataset builder generates valid JSONL from synthetic | `test_evolution_fitness.py` | `test_dataset_synthetic` | pytest | autotest |
| TC-009 | Dataset builder correctly assigns splits | `test_evolution_fitness.py` | `test_dataset_splits` | pytest | autotest |
| TC-010 | Fitness scorer produces 0.0-1.0 scores per dimension | `test_evolution_fitness.py` | `test_score_variant` | pytest | autotest |
| TC-011 | Aggregation methods compute correctly | `test_evolution_fitness.py` | `test_aggregation` | pytest | autotest |
| TC-012 | evaluate_dataset returns mean fitness | `test_evolution_fitness.py` | `test_evaluate_dataset` | pytest | autotest |
| TC-013 | Optimizer runs full loop for 2+ generations | `test_evolution_optimizer.py` | `test_full_loop` | pytest | autotest |
| TC-014 | Pareto-front selection identifies non-dominated variants | `test_evolution_optimizer.py` | `test_pareto` | pytest | autotest |
| TC-015 | Convergence detection stops optimization | `test_evolution_optimizer.py` | `test_convergence` | pytest | autotest |
| TC-016 | MIPROv2 mode uses history-based selection | `test_evolution_optimizer.py` | `test_miprov2` | pytest | autotest |
| TC-017 | Darwinian mode raises NotImplementedError | `test_evolution_optimizer.py` | `test_darwinian_stub` | pytest | autotest |
| TC-018 | Size limit blocks variants exceeding threshold | `test_evolution_constraint.py` | `test_size_block` | pytest | autotest |
| TC-019 | Size limit passes variants within threshold | `test_evolution_constraint.py` | `test_size_pass` | pytest | autotest |
| TC-020 | Semantic preservation uses judge callback | `test_evolution_constraint.py` | `test_semantic` | pytest | autotest |
| TC-021 | Caching compatibility checks prefix preservation | `test_evolution_constraint.py` | `test_caching` | pytest | autotest |
| TC-022 | should_block returns True only for block failures | `test_evolution_constraint.py` | `test_should_block` | pytest | autotest |
| TC-023 | Runner executes full pipeline to EvolutionReport | `test_evolution_runner.py` | `test_full_pipeline` | pytest | autotest |
| TC-024 | Runner resolves cross-references correctly | `test_evolution_runner.py` | `test_resolve_refs` | pytest | autotest |
| TC-025 | Runner stops on block constraint violation | `test_evolution_runner.py` | `test_block_constraint` | pytest | autotest |
| TC-026 | CLI `ark evolution run` executes evolution | `test_evolution_integration.py` | `test_cli_run` | pytest | autotest |
| TC-027 | CLI `ark evolution status` displays status | `test_evolution_integration.py` | `test_cli_status` | pytest | autotest |
| TC-028 | Codegen produces valid JSONL templates | `test_evolution_codegen.py` | `test_dataset_jsonl` | pytest | autotest |
| TC-029 | Codegen produces Python scoring skeletons | `test_evolution_codegen.py` | `test_scoring_script` | pytest | autotest |
| TC-030 | Codegen produces JSON config files | `test_evolution_codegen.py` | `test_run_config` | pytest | autotest |
| TC-031 | `ark codegen --target evolution` works e2e | `test_evolution_codegen.py` | `test_codegen_e2e` | pytest | autotest |
| TC-032 | Split ratio verification catches bad ratios | `test_evolution_verify.py` | `test_split_ratio_fail` | pytest | autotest |
| TC-033 | Fitness weight verification catches bad weights | `test_evolution_verify.py` | `test_weight_fail` | pytest | autotest |
| TC-034 | Gate tolerance verification catches bad bounds | `test_evolution_verify.py` | `test_tolerance_fail` | pytest | autotest |
| TC-035 | Cross-reference verification catches unknowns | `test_evolution_verify.py` | `test_xref_fail` | pytest | autotest |
| TC-036 | `ark verify` runs evolution checks when present | `test_evolution_verify.py` | `test_verify_integration` | pytest | autotest |
| TC-037 | Visualizer extracts evolution nodes and edges | `test_evolution_integration.py` | `test_viz_nodes` | pytest | autotest |
| TC-038 | Generated HTML includes evolution color coding | `test_evolution_integration.py` | `test_viz_colors` | pytest | autotest |
| TC-039 | `ark graph` renders evolution items | (CLI poc) | N/A | CLI | poc |
| TC-040 | evolution_skills.ark parses without errors | `test_evolution_integration.py` | `test_skills_parse` | pytest | autotest |
| TC-041 | evolution_roles.ark parses without errors | `test_evolution_integration.py` | `test_roles_parse` | pytest | autotest |
| TC-042 | Both reflexive specs pass verify | `test_evolution_integration.py` | `test_reflexive_verify` | pytest | autotest |
| TC-043 | Both specs registered in root.ark | `test_evolution_integration.py` | `test_root_registry` | pytest | autotest |
| TC-044 | Codegen generates from reflexive specs | `test_evolution_integration.py` | `test_reflexive_codegen` | pytest | autotest |
| TC-045 | Test strategy document complete | (manual inspection) | N/A | manual | manual |
| TC-046 | All automated tests pass | `tests/test_evolution_*.py` | (all functions) | pytest | autotest |

---

## Test Files Summary

| Test File | TCs Covered | Subsystem | Implementation Task |
|-----------|-------------|-----------|---------------------|
| `tests/test_evolution_parser.py` | TC-001, TC-002, TC-003, TC-004 (partial), TC-005, TC-006, TC-007 | Grammar, stdlib, parser AST, ArkFile indices | ADV004-T019 (after T002, T003, T005) |
| `tests/test_evolution_fitness.py` | TC-008, TC-009, TC-010, TC-011, TC-012 | Dataset builder, fitness scoring | ADV004-T019 (after T006, T007) |
| `tests/test_evolution_optimizer.py` | TC-013, TC-014, TC-015, TC-016, TC-017 | GEPA optimizer, Pareto selection, convergence | ADV004-T019 (after T008) |
| `tests/test_evolution_constraint.py` | TC-018, TC-019, TC-020, TC-021, TC-022 | Constraint checker, size/semantic/caching/block | ADV004-T019 (after T009) |
| `tests/test_evolution_runner.py` | TC-023, TC-024, TC-025 | Evolution runner, cross-ref resolution, block halt | ADV004-T019 (after T010) |
| `tests/test_evolution_integration.py` | TC-026, TC-027, TC-037–TC-044 | CLI, visualizer, reflexive specs, root.ark | ADV004-T019 (after T011, T014, T015–T018) |
| `tests/test_evolution_codegen.py` | TC-028, TC-029, TC-030, TC-031 | Evolution codegen, JSONL, scoring scripts, JSON config | ADV004-T019 (after T012) |
| `tests/test_evolution_verify.py` | TC-032, TC-033, TC-034, TC-035, TC-036 | Z3 verification, split ratios, weights, tolerances, xrefs | ADV004-T019 (after T013) |

---

## Approximate Test Count by File

| Test File | Named Test Functions | Notes |
|-----------|---------------------|-------|
| `test_evolution_parser.py` | ~12 | 3 primary TCs + stdlib enum checks + dataclass field checks |
| `test_evolution_fitness.py` | ~9 | 5 primary TCs + JSONL validity + pass_rate + golden load |
| `test_evolution_optimizer.py` | ~7 | 5 primary TCs + population cap + reflection content |
| `test_evolution_constraint.py` | ~8 | 5 primary TCs + check_all + warn-only pass-through |
| `test_evolution_runner.py` | ~5 | 3 primary TCs + fitness_history + duration |
| `test_evolution_integration.py` | ~12 | 11 TC-backed tests + TC-039 poc via CLI |
| `test_evolution_codegen.py` | ~7 | 4 primary TCs + split proportion + syntax validity + JSON validity |
| `test_evolution_verify.py` | ~9 | 5 primary TCs + negative split + negative weight + constraint ref + optimizer bounds |
| **Total** | **~69** | Well above minimum; each TC has at least one dedicated test function |

---

## Summary by Proof Method

| Method | Count | TC IDs |
|--------|-------|--------|
| autotest | 43 | TC-001–003, TC-005–044, TC-046 |
| poc | 1 | TC-039 |
| manual | 2 | TC-004, TC-045 |

---

## Tooling

- **Framework**: pytest (existing Ark convention)
- **Fixtures**: `tmp_path` for codegen output; inline .ark snippet strings for grammar/parser/verify
- **Integration marker**: `@pytest.mark.integration` on tests requiring real spec files (evolution_skills.ark, evolution_roles.ark); skip gracefully with `pytest.mark.skipif` when files do not exist
- **CLI tests**: `subprocess.run(['python', 'ark.py', ...], cwd=REPO_ROOT)`, assert `returncode == 0`
- **Stub callbacks**: `mutate_fn`, `judge_fn`, `eval_fn`, `constraint_fn` are deterministic Python functions — no LLM SDK dependency in any test
- **Constants**: `REPO_ROOT = Path('R:/Sandbox/ark')` at top of each file

---

## Execution Order

Tests must be developed in dependency order (matching task wave order):

1. **Wave 1 — Parser** (`test_evolution_parser.py`) — after T002 (evolution.ark), T003 (Lark grammar), T005 (AST dataclasses)
2. **Wave 2 — Fitness** (`test_evolution_fitness.py`) — after T006 (dataset_builder) and T007 (fitness.py)
3. **Wave 3 — Optimizer** (`test_evolution_optimizer.py`) — after T008 (optimizer.py)
4. **Wave 4 — Constraint** (`test_evolution_constraint.py`) — after T009 (constraint_checker.py)
5. **Wave 5 — Verify** (`test_evolution_verify.py`) — after T013 (evolution_verify.py)
6. **Wave 6 — Codegen** (`test_evolution_codegen.py`) — after T012 (evolution_codegen.py)
7. **Wave 7 — Runner** (`test_evolution_runner.py`) — after T010 (evolution_runner.py)
8. **Wave 8 — Integration** (`test_evolution_integration.py`) — after T011 (CLI), T014 (visualizer), T015/T016 (reflexive specs), T017/T018 (root.ark + codegen)

Run all evolution tests: `pytest tests/test_evolution_*.py -q`

---

## TC→File Quick Reference

| TC Range | File | Subsystem |
|----------|------|-----------|
| TC-001–007 | `test_evolution_parser.py` | Grammar, stdlib, parser AST, ArkFile indices |
| TC-008–012 | `test_evolution_fitness.py` | Dataset builder, fitness scoring |
| TC-013–017 | `test_evolution_optimizer.py` | GEPA optimizer engine |
| TC-018–022 | `test_evolution_constraint.py` | Constraint checker |
| TC-023–025 | `test_evolution_runner.py` | Evolution runner orchestration |
| TC-026–027, TC-037–044 | `test_evolution_integration.py` | CLI, visualizer, reflexive specs |
| TC-028–031 | `test_evolution_codegen.py` | Code generation |
| TC-032–036 | `test_evolution_verify.py` | Z3 verification |
| TC-039 | CLI poc | Graph visualizer (human-verified) |
| TC-004, TC-045 | Manual inspection | Pest grammar parity; strategy doc exists |
| TC-046 | `pytest tests/test_evolution_*.py` | Full suite pass (aggregate) |
