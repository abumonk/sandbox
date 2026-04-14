# Foundation — Schema, Grammar, Parser

## Designs Covered
- design-evolution-schema: Stdlib type definitions for evolution entities
- design-dsl-surface: Grammar extensions and parser AST for 7 evolution items

## Tasks

### Design test strategy for Evolution System
- **ID**: ADV004-T001
- **Description**: Design automated tests covering all target conditions. Create test strategy document mapping TCs to test files, frameworks, and commands. Define test approach for evolution schema parsing, verification, codegen, optimizer, and constraint checking.
- **Files**: tests/test-strategy.md
- **Acceptance Criteria**:
  - Test strategy document exists at tests/test-strategy.md
  - All 44 target conditions are mapped to specific test cases
  - Test approach, tooling, and coverage expectations are defined
  - Test files named: test_evolution_parser.py, test_evolution_verify.py, test_evolution_codegen.py, test_evolution_optimizer.py, test_evolution_constraint.py, test_evolution_fitness.py, test_evolution_runner.py, test_evolution_integration.py
- **Target Conditions**: TC-045
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read, Write, Glob, Grep
  - Skill set: test design, pytest, ark-dsl
  - Estimated duration: 15min
  - Estimated tokens: 15000

### Create stdlib/evolution.ark type definitions
- **ID**: ADV004-T002
- **Description**: Create the evolution stdlib file with enum and struct definitions for EvolutionTier, OptimizerEngine, DataSource, EnforcementLevel, RunStatus, MutationStrategy, AggregationMethod, FitnessScore, Variant, ConstraintDef, BenchmarkResult, RunResult, SplitRatio, RubricDimension.
- **Files**: ark/dsl/stdlib/evolution.ark
- **Acceptance Criteria**:
  - All 7 enums and 7 structs defined with correct Ark syntax
  - File parses via `python ark.py parse dsl/stdlib/evolution.ark`
  - Types are consistent with existing stdlib patterns (types.ark, studio.ark)
  - Import stdlib.types at top
- **Target Conditions**: TC-001, TC-002
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: ark-dsl
  - Estimated duration: 15min
  - Estimated tokens: 12000

### Extend Lark grammar with evolution item rules
- **ID**: ADV004-T003
- **Description**: Add grammar rules for evolution_target_def, eval_dataset_def, fitness_function_def, optimizer_def, benchmark_gate_def, evolution_run_def, constraint_def to ark_grammar.lark. Update the item rule to include all 7 new alternatives. Add supporting statement rules (file_ref_stmt, source_stmt, split_stmt, dimension_stmt, engine_stmt, etc.).
- **Files**: ark/tools/parser/ark_grammar.lark
- **Acceptance Criteria**:
  - All 7 new item rules are syntactically correct Lark EBNF
  - All supporting statement rules added
  - Existing .ark files still parse (no regressions)
  - New rules follow existing naming conventions
- **Target Conditions**: TC-003, TC-005
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: lark-grammar, ark-dsl
  - Estimated duration: 25min
  - Estimated tokens: 25000

### Extend pest grammar with evolution item rules
- **ID**: ADV004-T004
- **Description**: Mirror the Lark grammar changes in dsl/grammar/ark.pest. Add pest PEG rules for all 7 new evolution items and their supporting statements.
- **Files**: ark/dsl/grammar/ark.pest
- **Acceptance Criteria**:
  - Pest rules mirror Lark rules for all 7 items
  - Pest syntax is correct
  - Existing pest rules unchanged
- **Target Conditions**: TC-004
- **Depends On**: [ADV004-T003]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: pest-peg, ark-dsl
  - Estimated duration: 20min
  - Estimated tokens: 20000

### Add parser AST dataclasses and transformer for evolution items
- **ID**: ADV004-T005
- **Description**: Add EvolutionTargetDef, EvalDatasetDef, FitnessFunctionDef, OptimizerDef, BenchmarkGateDef, EvolutionRunDef, ConstraintDef dataclasses to ark_parser.py. Add transformer methods for all new grammar rules. Update ArkFile with evolution_targets/eval_datasets/fitness_functions/optimizers/benchmark_gates/evolution_runs/constraints indices and _build_indices().
- **Files**: ark/tools/parser/ark_parser.py
- **Acceptance Criteria**:
  - All 7 new dataclasses added with correct fields
  - Transformer methods produce correct AST dicts
  - ArkFile indices populated for all evolution items
  - Existing parser behavior unchanged
  - Round-trip: parse -> to_json -> contains all evolution fields
- **Target Conditions**: TC-006, TC-007
- **Depends On**: [ADV004-T003]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, lark-transformer, ark-parser
  - Estimated duration: 30min
  - Estimated tokens: 35000
