# DSL Surface — Grammar and Parser for Evolution Items — Design

## Overview
Extend the Ark DSL grammar (Lark EBNF and pest PEG) with 7 new top-level item kinds for the evolution subsystem: `evolution_target`, `eval_dataset`, `fitness_function`, `optimizer`, `benchmark_gate`, `evolution_run`, and `constraint`. Add corresponding parser AST dataclasses and transformer methods.

## Target Files
- `ark/tools/parser/ark_grammar.lark` — Add Lark rules for 7 new items
- `ark/dsl/grammar/ark.pest` — Mirror pest PEG rules for 7 new items
- `ark/tools/parser/ark_parser.py` — Add 7 AST dataclasses + transformer methods + ArkFile indices

## Approach

### New Grammar Rules

Each new item follows existing Ark pattern (`keyword IDENT "{" body "}"`) with keyword-colon statements inside:

```
// 1. evolution_target — entity to optimize
evolution_target_def: "evolution_target" IDENT "{" evolution_target_body "}"
evolution_target_body: evolution_target_member*
evolution_target_member: tier_stmt | file_ref_stmt | description_stmt
    | data_field | constraint_ref_stmt | version_stmt

file_ref_stmt: "file:" STRING
constraint_ref_stmt: "constraints:" "[" ident_list "]"
version_stmt: "version:" STRING

// 2. eval_dataset — evaluation dataset definition
eval_dataset_def: "eval_dataset" IDENT "{" eval_dataset_body "}"
eval_dataset_body: eval_dataset_member*
eval_dataset_member: source_stmt | split_stmt | scoring_ref_stmt
    | description_stmt | data_field | size_stmt

source_stmt: "source:" IDENT
split_stmt: "split:" expr "," expr "," expr
scoring_ref_stmt: "scoring:" IDENT
size_stmt: "size:" expr

// 3. fitness_function — scoring specification
fitness_function_def: "fitness_function" IDENT "{" fitness_function_body "}"
fitness_function_body: fitness_function_member*
fitness_function_member: dimension_stmt | aggregation_stmt
    | penalty_stmt | description_stmt | data_field

dimension_stmt: "dimension" IDENT "{" "weight:" expr ("," "description:" STRING)? "}"
aggregation_stmt: "aggregation:" IDENT
penalty_stmt: "penalty:" STRING

// 4. optimizer — optimizer configuration
optimizer_def: "optimizer" IDENT "{" optimizer_body "}"
optimizer_body: optimizer_member*
optimizer_member: engine_stmt | iterations_stmt | population_stmt
    | mutation_stmt | description_stmt | data_field

engine_stmt: "engine:" IDENT
iterations_stmt: "iterations:" expr
population_stmt: "population:" expr
mutation_stmt: "mutation:" IDENT

// 5. benchmark_gate — validation gate
benchmark_gate_def: "benchmark_gate" IDENT "{" benchmark_gate_body "}"
benchmark_gate_body: benchmark_gate_member*
benchmark_gate_member: benchmark_ref_stmt | tolerance_stmt
    | pass_criteria_stmt | description_stmt | data_field

benchmark_ref_stmt: "benchmark:" STRING
tolerance_stmt: "tolerance:" expr
pass_criteria_stmt: "pass_criteria:" STRING

// 6. evolution_run — run instance
evolution_run_def: "evolution_run" IDENT "{" evolution_run_body "}"
evolution_run_body: evolution_run_member*
evolution_run_member: target_ref_stmt | optimizer_ref_stmt
    | dataset_ref_stmt | gate_ref_stmt | status_stmt
    | description_stmt | data_field

target_ref_stmt: "target:" IDENT
optimizer_ref_stmt: "optimizer:" IDENT
dataset_ref_stmt: "dataset:" IDENT
gate_ref_stmt: "gate:" IDENT
status_stmt: "status:" IDENT

// 7. constraint — safety constraint
constraint_def: "constraint" IDENT "{" constraint_body "}"
constraint_body: constraint_member*
constraint_member: kind_stmt | enforcement_stmt | threshold_stmt
    | description_stmt | data_field

kind_stmt: "kind:" IDENT
enforcement_stmt: "enforcement:" IDENT
threshold_stmt: "threshold:" expr
```

### Integration into `item` Rule
Add all 7 to the `item` rule in both grammars:
```
item: ... | evolution_target_def | eval_dataset_def | fitness_function_def
    | optimizer_def | benchmark_gate_def | evolution_run_def | constraint_def
```

### Parser AST Dataclasses
Add 7 new dataclasses:
- `EvolutionTargetDef` (tier, file, constraints, version, description, data_fields)
- `EvalDatasetDef` (source, split_train/val/test, scoring, size, description, data_fields)
- `FitnessFunctionDef` (dimensions, aggregation, penalties, description, data_fields)
- `OptimizerDef` (engine, iterations, population, mutation, description, data_fields)
- `BenchmarkGateDef` (benchmark, tolerance, pass_criteria, description, data_fields)
- `EvolutionRunDef` (target, optimizer, dataset, gate, status, description, data_fields)
- `ConstraintDef` (kind, enforcement, threshold, description, data_fields)

### ArkFile Extensions
Add indices: `evolution_targets`, `eval_datasets`, `fitness_functions`, `optimizers`, `benchmark_gates`, `evolution_runs`, `constraints` (all `{name: dict}` maps). Update `_build_indices()`.

## Dependencies
- design-evolution-schema (type definitions used in the DSL items)

## Target Conditions
- TC-003: Lark grammar parses all 7 new item kinds without errors
- TC-004: Pest grammar mirrors Lark for all 7 new item kinds
- TC-005: Existing .ark files continue to parse after grammar changes (no regressions)
- TC-006: Parser produces correct AST dicts for all 7 evolution item types
- TC-007: ArkFile indices are populated for all evolution items
