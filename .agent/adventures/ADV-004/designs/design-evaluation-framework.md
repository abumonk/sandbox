# Evaluation Framework — Design

## Overview
Implement the evaluation framework in `tools/evolution/` that provides dataset building and LLM-as-judge fitness scoring. This is the "measure" component of the evolution loop: given a variant, produce a fitness score using configurable rubrics.

## Target Files
- `ark/tools/evolution/__init__.py` — Package init
- `ark/tools/evolution/dataset_builder.py` — Generates eval datasets from .ark skill definitions
- `ark/tools/evolution/fitness.py` — LLM-as-judge scoring with configurable rubrics

## Approach

### dataset_builder.py
Generates evaluation datasets from various sources:

1. **Synthetic generation**: Reads a skill/prompt file, uses a structured template to generate test cases. Each test case has `input`, `expected_behavior`, and `rubric_hints`. No actual LLM calls — generates structured JSON templates that can be filled by an external LLM or by hand.
2. **Golden set loading**: Reads hand-curated JSONL files.
3. **Auto-eval generation**: For code targets, reads the code and generates input/output pairs based on function signatures.

Output format: JSONL with fields `{id, input, expected, rubric_hints, source, split}`.

Split assignment uses the ratios from `eval_dataset` specs (train/val/test). Deterministic shuffling via seed.

Key functions:
- `build_dataset(eval_dataset_ast, target_file_path) -> list[dict]` — main entry point
- `generate_synthetic(skill_content, count) -> list[dict]` — template-based synthetic cases
- `load_golden(path) -> list[dict]` — load JSONL golden set
- `assign_splits(cases, train, val, test, seed) -> list[dict]` — assign split labels

### fitness.py
LLM-as-judge scoring framework:

1. **Rubric-based scoring**: Takes a variant output and scores it against rubric dimensions.
2. **Configurable dimensions**: Each dimension has name, weight, description. Scores are 0.0-1.0.
3. **Aggregation**: Supports weighted_sum, min, harmonic methods.
4. **No external LLM dependency**: Provides a `score()` function that accepts a `judge_fn` callback. The callback can be an LLM call, a regex matcher, or a deterministic evaluator.

Key functions:
- `score_variant(variant_output, expected, rubric_dimensions, judge_fn) -> FitnessResult` — score a single variant against one test case
- `aggregate_scores(scores, method) -> float` — combine dimension scores
- `evaluate_dataset(variant_fn, dataset, rubric, judge_fn) -> EvalResult` — score variant across full dataset
- `FitnessResult` dataclass: `{dimension_scores: dict[str, float], aggregated: float, penalties: list[str]}`
- `EvalResult` dataclass: `{mean_fitness: float, per_case: list[FitnessResult], pass_rate: float}`

### Design Decisions
- No LLM SDK dependency — fitness.py uses callback injection for the judge function
- Dataset builder produces JSONL (industry standard for eval datasets)
- Deterministic split assignment ensures reproducibility
- Rubric dimensions from fitness_function AST map directly to scoring calls

## Dependencies
- design-evolution-schema (types used in scoring)
- design-dsl-surface (AST structures for eval_dataset and fitness_function)

## Target Conditions
- TC-008: dataset_builder.py generates valid JSONL from synthetic source
- TC-009: dataset_builder.py correctly assigns splits summing to expected proportions
- TC-010: fitness.py scores a variant against rubric dimensions producing 0.0-1.0 scores
- TC-011: fitness.py aggregation methods (weighted_sum, min, harmonic) compute correctly
- TC-012: evaluate_dataset processes full dataset and returns mean fitness
