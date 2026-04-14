# Evaluation Framework and Optimizer Engine

## Designs Covered
- design-evaluation-framework: Dataset builder and fitness scoring
- design-optimizer-engine: GEPA-style optimizer
- design-constraint-system: Constraint checker

## Tasks

### Implement dataset builder
- **ID**: ADV004-T006
- **Description**: Create tools/evolution/dataset_builder.py with functions for synthetic dataset generation, golden set loading, split assignment. Create tools/evolution/__init__.py package init.
- **Files**: ark/tools/evolution/__init__.py, ark/tools/evolution/dataset_builder.py
- **Acceptance Criteria**:
  - build_dataset() generates JSONL-format list of dicts
  - generate_synthetic() creates template test cases from file content
  - load_golden() reads JSONL files
  - assign_splits() distributes cases according to train/val/test ratios
  - Deterministic output with seed parameter
- **Target Conditions**: TC-008, TC-009
- **Depends On**: [ADV004-T005]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python
  - Estimated duration: 25min
  - Estimated tokens: 25000

### Implement fitness scoring
- **ID**: ADV004-T007
- **Description**: Create tools/evolution/fitness.py with rubric-based scoring, aggregation methods, and dataset-level evaluation.
- **Files**: ark/tools/evolution/fitness.py
- **Acceptance Criteria**:
  - score_variant() accepts judge_fn callback and returns FitnessResult
  - aggregate_scores() supports weighted_sum, min, harmonic methods
  - evaluate_dataset() processes full dataset and returns EvalResult with mean fitness
  - FitnessResult and EvalResult dataclasses defined
  - All scores in 0.0-1.0 range
- **Target Conditions**: TC-010, TC-011, TC-012
- **Depends On**: [ADV004-T006]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python
  - Estimated duration: 25min
  - Estimated tokens: 25000

### Implement optimizer engine
- **ID**: ADV004-T008
- **Description**: Create tools/evolution/optimizer.py with GEPA-style optimization loop, Pareto-front selection, convergence detection, and MIPROv2/Darwinian mode stubs.
- **Files**: ark/tools/evolution/optimizer.py
- **Acceptance Criteria**:
  - optimize() runs full loop: init -> evaluate -> select -> mutate for N generations
  - select_pareto_front() correctly identifies non-dominated variants
  - Convergence detection stops when improvement < threshold for 3 generations
  - MIPROv2 mode uses history-based selection
  - Darwinian mode raises NotImplementedError
  - Population, OptimizerConfig, OptimizeResult dataclasses defined
  - Callback-based: mutate_fn and eval_fn are injected
- **Target Conditions**: TC-013, TC-014, TC-015, TC-016, TC-017
- **Depends On**: [ADV004-T007]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, optimization algorithms
  - Estimated duration: 30min
  - Estimated tokens: 35000

### Implement constraint checker
- **ID**: ADV004-T009
- **Description**: Create tools/evolution/constraint_checker.py with size_limit, semantic_preservation, test_suite, and caching_compat constraint checks.
- **Files**: ark/tools/evolution/constraint_checker.py
- **Acceptance Criteria**:
  - check_size_limit() correctly compares variant sizes against threshold
  - check_semantic_preservation() uses judge callback
  - check_caching_compat() verifies prefix preservation
  - check_all_constraints() runs all applicable constraints
  - should_block() returns True only for block-enforcement failures
  - ConstraintResult dataclass defined
- **Target Conditions**: TC-018, TC-019, TC-020, TC-021, TC-022
- **Depends On**: [ADV004-T006]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python
  - Estimated duration: 20min
  - Estimated tokens: 20000
