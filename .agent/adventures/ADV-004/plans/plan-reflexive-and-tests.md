# Reflexive Evolution Specs and Tests

## Designs Covered
- design-reflexive-evolution: Example .ark specs that evolve Ark's own artifacts

## Tasks

### Create evolution_skills.ark reflexive spec
- **ID**: ADV004-T015
- **Description**: Author ark/specs/meta/evolution_skills.ark using all 7 evolution item types to define evolution of Ark's skill files. Include evolution_target, eval_dataset, fitness_function, optimizer, benchmark_gate, constraints, and evolution_run.
- **Files**: ark/specs/meta/evolution_skills.ark
- **Acceptance Criteria**:
  - File uses all 7 evolution item types
  - Parses via `python ark.py parse`
  - Passes `python ark.py verify`
  - Targets .claude/skills/ content
  - Constraints are conservative (Block enforcement, 20% size, 0.8 semantic)
- **Target Conditions**: TC-040, TC-042
- **Depends On**: [ADV004-T005, ADV004-T013]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: ark-dsl
  - Estimated duration: 20min
  - Estimated tokens: 18000

### Create evolution_roles.ark reflexive spec
- **ID**: ADV004-T016
- **Description**: Author ark/specs/meta/evolution_roles.ark to define evolution of Ark's agent role descriptions using GEPA-style reflective loop.
- **Files**: ark/specs/meta/evolution_roles.ark
- **Acceptance Criteria**:
  - File uses all 7 evolution item types
  - Parses via `python ark.py parse`
  - Passes `python ark.py verify`
  - Targets .agent/roles/ content
- **Target Conditions**: TC-041, TC-042
- **Depends On**: [ADV004-T005, ADV004-T013]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: ark-dsl
  - Estimated duration: 15min
  - Estimated tokens: 15000

### Register evolution specs in root.ark
- **ID**: ADV004-T017
- **Description**: Add EvolutionSkills and EvolutionRoles to root.ark SystemRegistry with phase: meta and appropriate priorities.
- **Files**: ark/specs/root.ark
- **Acceptance Criteria**:
  - Both specs registered in SystemRegistry
  - root.ark still parses without errors
  - Priorities are 3 and 4 (after existing studio entries)
- **Target Conditions**: TC-043
- **Depends On**: [ADV004-T015, ADV004-T016]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: ark-dsl
  - Estimated duration: 10min
  - Estimated tokens: 8000

### Run evolution codegen on reflexive specs
- **ID**: ADV004-T018
- **Description**: Execute `ark codegen <spec> --target evolution` on both reflexive specs and verify generated artifacts are correct.
- **Files**: (generated output files)
- **Acceptance Criteria**:
  - Codegen produces dataset JSONL templates for both specs
  - Codegen produces scoring script skeletons
  - Codegen produces run config JSON files
  - No errors during generation
- **Target Conditions**: TC-044
- **Depends On**: [ADV004-T012, ADV004-T015, ADV004-T016]
- **Evaluation**:
  - Access requirements: Read, Bash
  - Skill set: ark-dsl, codegen
  - Estimated duration: 15min
  - Estimated tokens: 12000

### Implement automated tests for Evolution System
- **ID**: ADV004-T019
- **Description**: Implement all tests from test strategy. Create test_evolution_parser.py, test_evolution_verify.py, test_evolution_codegen.py, test_evolution_optimizer.py, test_evolution_constraint.py, test_evolution_fitness.py, test_evolution_runner.py, test_evolution_integration.py. Each TC with proof_method: autotest must have a passing test. Run all tests and verify.
- **Files**: ark/tests/test_evolution_parser.py, ark/tests/test_evolution_verify.py, ark/tests/test_evolution_codegen.py, ark/tests/test_evolution_optimizer.py, ark/tests/test_evolution_constraint.py, ark/tests/test_evolution_fitness.py, ark/tests/test_evolution_runner.py, ark/tests/test_evolution_integration.py
- **Acceptance Criteria**:
  - All 8 test files created with comprehensive test coverage
  - All TC autotests implemented and passing
  - `pytest tests/test_evolution_*.py` passes
  - Full regression: `pytest tests/` passes
  - Minimum 40 test functions across all files
- **Target Conditions**: TC-046
- **Depends On**: [ADV004-T001, ADV004-T002, ADV004-T003, ADV004-T005, ADV004-T006, ADV004-T007, ADV004-T008, ADV004-T009, ADV004-T010, ADV004-T012, ADV004-T013, ADV004-T014, ADV004-T015, ADV004-T016, ADV004-T017, ADV004-T018]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, pytest, ark-dsl
  - Estimated duration: 30min
  - Estimated tokens: 40000
