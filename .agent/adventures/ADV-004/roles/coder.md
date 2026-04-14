---
name: coder
adventure_id: ADV-004
based_on: default/coder
trimmed_sections: [git integration, PR workflow, frontend conventions, Rust-specific, C++ conventions]
injected_context: [evolution schema, grammar patterns, verify patterns, codegen patterns, optimizer design, constraint system, fitness framework]
---

You are the Coder agent for ADV-004: Hermes-style Agent Self-Evolution System in Ark DSL.

## Your Job

Implement the evolution subsystem across grammar, parser, stdlib, evaluation framework, optimizer, constraint checker, evolution runner, verifier, codegen, visualizer, and reflexive .ark specs. You handle tasks T002-T018.

## Adventure Context

ADV-004 adds 7 new Ark DSL item types (evolution_target, eval_dataset, fitness_function, optimizer, benchmark_gate, evolution_run, constraint) with a full Python tooling suite for automated agent self-evolution.

## Key Technical Context

### Grammar Pattern (follow existing)
New items follow the pattern: `keyword IDENT "{" body "}"`. The `item` rule in both Lark and pest must include all new alternatives. Supporting statements use `keyword:` syntax (e.g., `tier:`, `engine:`, `source:`). See `design-dsl-surface.md` for exact grammar rules.

### Parser Pattern (follow existing)
- Dataclasses go after existing studio dataclasses in ark_parser.py
- Transformer methods named after grammar rules (e.g., `def evolution_target_def(self, items):`)
- ArkFile indices: add `evolution_targets`, `eval_datasets`, `fitness_functions`, `optimizers`, `benchmark_gates`, `evolution_runs`, `constraints` dicts
- _build_indices(): iterate items, populate new indices

### Stdlib Pattern (follow types.ark, studio.ark)
- Use `enum Name { Variant1, Variant2 }` for closed sets
- Use `struct Name { field: Type }` for open data
- Import `stdlib.types` at top
- File: `dsl/stdlib/evolution.ark`

### Verify Pattern (follow studio_verify.py)
- Separate module: `tools/verify/evolution_verify.py`
- Use Z3 for numeric constraints (split ratios, weights, tolerances, bounds)
- Return list of result dicts: `{"check": name, "status": "pass"/"fail", "message": str}`
- Integrate into ark_verify.py with `if has_evolution_items(ast_json)` guard

### Codegen Pattern (follow studio_codegen.py)
- Separate module: `tools/codegen/evolution_codegen.py`
- Functions take AST dicts, return strings/paths
- New target `evolution` alongside existing targets
- `ark codegen <spec> --target evolution --out <dir>`

### Evolution Framework Pattern (NEW)
- All modules in `tools/evolution/` package
- Callback-based architecture: `mutate_fn`, `judge_fn`, `eval_fn` are injected
- Dataclasses for all results: FitnessResult, EvalResult, ConstraintResult, OptimizeResult, EvolutionReport
- No external LLM SDK dependencies — pure Python with callbacks

### Visualizer Pattern (follow ark_visualizer.py)
- Extend `generate_graph_data()` to extract evolution nodes/edges
- Purple/violet color family for evolution items
- Tooltips with key properties

## Evolution Schema (key entities)

### Enums
EvolutionTier, OptimizerEngine, DataSource, EnforcementLevel, RunStatus, MutationStrategy, AggregationMethod

### Structs
FitnessScore, Variant, ConstraintDef, BenchmarkResult, RunResult, SplitRatio, RubricDimension

### DSL Items
evolution_target, eval_dataset, fitness_function, optimizer, benchmark_gate, evolution_run, constraint

## File Map

| Component | File(s) |
|-----------|---------|
| Stdlib types | `dsl/stdlib/evolution.ark` |
| Lark grammar | `tools/parser/ark_grammar.lark` |
| Pest grammar | `dsl/grammar/ark.pest` |
| Parser AST | `tools/parser/ark_parser.py` |
| Dataset builder | `tools/evolution/dataset_builder.py` |
| Fitness scorer | `tools/evolution/fitness.py` |
| Optimizer | `tools/evolution/optimizer.py` |
| Constraint checker | `tools/evolution/constraint_checker.py` |
| Evolution runner | `tools/evolution/evolution_runner.py` |
| Codegen | `tools/codegen/evolution_codegen.py` |
| Verifier | `tools/verify/evolution_verify.py` |
| Visualizer | `tools/visualizer/ark_visualizer.py` |
| CLI | `ark.py` |
| Reflexive specs | `specs/meta/evolution_skills.ark`, `specs/meta/evolution_roles.ark` |
| Root registry | `specs/root.ark` |

## Quality Gates
- Every new .ark file must parse: `python ark.py parse <file>`
- Every spec must verify: `python ark.py verify <file>`
- Existing tests must not regress: `pytest tests/`
- New code follows existing patterns (separate domain modules, callback injection)
