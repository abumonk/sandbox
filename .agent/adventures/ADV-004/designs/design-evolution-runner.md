# Evolution Runner — Design

## Overview
Implement the full evolution orchestration loop in `tools/evolution/evolution_runner.py` and integrate it into the Ark CLI. This ties together all components: target loading, dataset building, optimization, constraint checking, benchmark gating, and result reporting.

## Target Files
- `ark/tools/evolution/evolution_runner.py` — Orchestrates the full evolution loop
- `ark/ark.py` — Add `ark evolution run` and `ark evolution status` CLI subcommands

## Approach

### Evolution Runner

The runner reads an `evolution_run` AST item and executes the full pipeline:

```
1. Load evolution_target -> read the target file content
2. Load eval_dataset -> build/load the evaluation dataset
3. Load fitness_function -> configure rubric dimensions and aggregation
4. Load optimizer -> configure optimizer engine and parameters
5. Load constraints -> prepare constraint checkers
6. Load benchmark_gate -> prepare gating criteria
7. Run optimizer loop:
   a. Initialize population from seed (target content)
   b. For each generation:
      - Evaluate all variants (fitness scoring)
      - Check constraints on each variant
      - Select survivors (Pareto-front)
      - Mutate survivors to produce next generation
   c. Stop on convergence or max iterations
8. Gate best variant through benchmark
9. Output results:
   - Best variant content
   - Evolution report (generations, fitness trajectory, constraint violations)
   - Pass/fail status
```

### Key Functions

```python
@dataclass
class EvolutionContext:
    target: dict          # evolution_target AST
    dataset: list[dict]   # eval cases
    fitness: dict         # fitness_function AST
    optimizer_config: dict # optimizer AST
    constraints: list[dict] # constraint ASTs
    gate: dict            # benchmark_gate AST
    mutate_fn: Callable   # injected mutation callback
    judge_fn: Callable    # injected judge callback

def run_evolution(context: EvolutionContext) -> EvolutionReport:
    """Execute full evolution pipeline."""

@dataclass
class EvolutionReport:
    status: str           # "complete", "failed", "gated_out"
    generations: int
    best_variant: str     # content of best variant
    best_fitness: float
    fitness_history: list[float]  # best fitness per generation
    constraint_violations: list[str]
    benchmark_result: dict
    duration_ms: int
```

### CLI Integration

Add to `ark.py`:
- `ark evolution run <spec.ark> [--run <run_name>]` — Execute an evolution run defined in the spec
- `ark evolution status <spec.ark>` — Show status of all evolution_run items

The CLI:
1. Parses the .ark file
2. Finds the named evolution_run (or all if no --run flag)
3. Resolves references (target, dataset, optimizer, gate, constraints)
4. Creates EvolutionContext with default callbacks (stub mutate_fn that appends "[evolved]", simple judge_fn)
5. Calls run_evolution()
6. Prints report to stdout

### Default Callbacks
For initial implementation, provide simple default callbacks:
- `default_mutate_fn`: Simple text perturbation (word shuffle, synonym substitution placeholder)
- `default_judge_fn`: Keyword-matching scorer (checks if expected keywords appear in output)

These are replaced by real LLM callbacks in production use.

### Design Decisions
- Runner is dependency-injected: mutate_fn and judge_fn are callbacks, not hardcoded LLM calls
- All AST items are resolved by name from the parsed ArkFile
- Report includes full fitness trajectory for analysis/visualization
- CLI follows existing `ark studio codegen/verify` pattern for subcommands

## Dependencies
- design-dsl-surface (all 7 evolution AST items)
- design-evaluation-framework (dataset_builder, fitness)
- design-optimizer-engine (optimizer)
- design-constraint-system (constraint_checker)

## Target Conditions
- TC-023: Evolution runner executes full pipeline from evolution_run AST to EvolutionReport
- TC-024: Runner correctly resolves cross-references between evolution items (target, dataset, optimizer, gate)
- TC-025: Runner stops on constraint violation with enforcement=block
- TC-026: CLI `ark evolution run` parses spec and executes evolution
- TC-027: CLI `ark evolution status` displays run status from spec
