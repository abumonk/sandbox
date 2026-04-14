# Optimizer Engine — Design

## Overview
Implement the GEPA-inspired text mutation optimizer in `tools/evolution/optimizer.py`. This is the "evolve" component: given a population of text variants and their fitness scores, produce the next generation through reflective mutation, crossover, and selection.

## Target Files
- `ark/tools/evolution/optimizer.py` — GEPA-style text mutation optimizer

## Approach

### Core Algorithm (Simplified GEPA)
No DSPy dependency. Pure Python with callback-based LLM calls.

1. **Initialize**: Load seed variant (current content of evolution target).
2. **Evaluate**: Score all variants in population using fitness framework.
3. **Select**: Pareto-front selection — keep variants that are non-dominated across all rubric dimensions.
4. **Mutate**: For each selected variant:
   - **Reflective analysis**: Generate a structured mutation prompt that describes what the variant does well and poorly (based on per-case fitness scores).
   - **Targeted mutation**: Apply the mutation (text replacement, insertion, deletion) guided by the reflection.
   - Mutation is a text operation — the callback `mutate_fn(variant_text, reflection) -> new_text` handles the actual transformation.
5. **Crossover** (optional): Combine strong segments from two high-fitness variants.
6. **Repeat** for N iterations or until convergence.

### Key Classes and Functions

```python
@dataclass
class Population:
    variants: list[Variant]
    generation: int
    best_fitness: float

class OptimizerConfig:
    engine: str            # "gepa", "miprov2", "darwinian"
    iterations: int
    population_size: int
    mutation_strategy: str  # "reflective", "random", "guided", "crossover"
    convergence_threshold: float = 0.01

def optimize(
    seed_content: str,
    config: OptimizerConfig,
    eval_fn: Callable[[str], EvalResult],
    mutate_fn: Callable[[str, str], str],
    constraint_fn: Callable[[str], list[str]],
) -> OptimizeResult:
    """Main optimization loop."""

def select_pareto_front(variants: list[Variant], scores: dict) -> list[Variant]:
    """Non-dominated sorting for multi-objective selection."""

def generate_reflection(variant: Variant, eval_result: EvalResult) -> str:
    """Generate structured reflection text for mutation guidance."""
```

### MIPROv2 Mode (Simplified)
For `engine: miprov2`, use a simpler Bayesian-inspired approach:
- Maintain a history of (mutation, fitness_delta) pairs
- Select mutations that historically improve fitness
- No actual Bayesian optimization library — uses a simple upper-confidence-bound heuristic

### Darwinian Mode (Future/Stub)
For `engine: darwinian`, provide a stub that:
- Takes code files as variants
- Applies AST-level mutations (function body replacement)
- Validates via test suite
- Marked as Phase 4 / future work — raises NotImplementedError with clear message

### Design Decisions
- Callback-based architecture: `mutate_fn` and `eval_fn` are injected, keeping the optimizer pure logic
- Pareto-front selection supports multi-objective optimization (multiple rubric dimensions)
- Convergence detection: stop early if best fitness doesn't improve by threshold for 3 generations
- Population is capped at `population_size`; excess variants are pruned by fitness rank

## Dependencies
- design-evaluation-framework (fitness scoring used in optimization loop)

## Target Conditions
- TC-013: Optimizer runs a full loop (init -> evaluate -> select -> mutate -> evaluate) for at least 2 generations
- TC-014: Pareto-front selection correctly identifies non-dominated variants
- TC-015: Convergence detection stops optimization when improvement is below threshold
- TC-016: MIPROv2 engine mode uses history-based mutation selection
- TC-017: Darwinian engine mode raises NotImplementedError with clear message
