# Evolution Runner and CLI Integration

## Designs Covered
- design-evolution-runner: Full evolution loop orchestration and CLI

## Tasks

### Implement evolution runner
- **ID**: ADV004-T010
- **Description**: Create tools/evolution/evolution_runner.py that orchestrates the full evolution pipeline: target loading, dataset building, optimization, constraint checking, benchmark gating, and result reporting.
- **Files**: ark/tools/evolution/evolution_runner.py
- **Acceptance Criteria**:
  - run_evolution() executes full pipeline from EvolutionContext to EvolutionReport
  - Correctly resolves cross-references between evolution items
  - Stops on constraint violation with enforcement=block
  - Includes default_mutate_fn and default_judge_fn stubs
  - EvolutionContext and EvolutionReport dataclasses defined
  - Fitness trajectory tracked across generations
- **Target Conditions**: TC-023, TC-024, TC-025
- **Depends On**: [ADV004-T008, ADV004-T009]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, system integration
  - Estimated duration: 30min
  - Estimated tokens: 35000

### Integrate evolution CLI commands
- **ID**: ADV004-T011
- **Description**: Add `ark evolution run` and `ark evolution status` subcommands to ark.py. Wire up to evolution_runner.py. Follow existing CLI patterns (ark studio codegen/verify).
- **Files**: ark/ark.py
- **Acceptance Criteria**:
  - `ark evolution run <spec.ark>` parses spec and runs evolution
  - `ark evolution run <spec.ark> --run <name>` runs specific evolution_run
  - `ark evolution status <spec.ark>` shows status of all evolution_run items
  - Error handling: clear messages for missing files, unknown runs
  - Sys.path includes tools/evolution/
- **Target Conditions**: TC-026, TC-027
- **Depends On**: [ADV004-T010]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, cli-design
  - Estimated duration: 20min
  - Estimated tokens: 20000
