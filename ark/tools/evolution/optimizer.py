"""
optimizer.py — GEPA-style text mutation optimizer for variant evolution.

Implements a population-based optimization loop with Pareto-front selection,
convergence detection, and multiple engine modes (GEPA, MIPROv2, Darwinian).

No external LLM dependency — uses callback-based architecture:
  - eval_fn(content: str) -> float   (0.0–1.0)
  - mutate_fn(content: str, generation: int, feedback: str) -> str
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Population:
    """Represents a generation of variant candidates."""

    variants: List[Dict]
    """List of variant dicts, each with keys: 'content', 'fitness', 'generation', 'parent'."""

    generation: int
    """Current generation index (0-based)."""


@dataclass
class OptimizerConfig:
    """Configuration for the optimization loop."""

    engine: str
    """Optimization engine: 'gepa', 'miprov2', or 'darwinian'."""

    iterations: int
    """Maximum number of generations to run."""

    population_size: int
    """Maximum population size per generation."""

    mutation_strategy: str
    """Mutation strategy: 'reflective', 'random', or 'crossover'."""

    convergence_threshold: float = 0.01
    """Minimum fitness improvement required to avoid convergence trigger."""

    convergence_patience: int = 3
    """Number of generations without improvement before stopping early."""


@dataclass
class OptimizeResult:
    """Result of an optimization run."""

    best_variant: Dict
    """The variant dict with the highest fitness achieved."""

    fitness_trajectory: List[float]
    """Best fitness value recorded at each generation."""

    generations_run: int
    """Total number of generations executed."""

    converged: bool
    """True if early stopping was triggered by convergence detection."""

    final_population: Population
    """The final population at the end of optimization."""


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def default_mutate_fn(content: str, generation: int, feedback: str = "") -> str:
    """Simple placeholder mutation: appends a generation tag to content.

    This is a placeholder for LLM-based reflective mutation.  Replace with
    a real callable that uses *feedback* to guide targeted text changes.

    Args:
        content: The variant text to mutate.
        generation: Current generation number (1-based when called from loop).
        feedback: Structured feedback string from fitness evaluation.

    Returns:
        Mutated content string.
    """
    return f"{content} [mutated-gen-{generation}]"


def select_pareto_front(variants: List[Dict], objectives: List[str]) -> List[Dict]:
    """Return the non-dominated subset (Pareto front) of *variants*.

    A variant V is dominated if there exists another variant W such that:
      - W is >= V on all objectives, AND
      - W is >  V on at least one objective.

    Variants that are not dominated by any other variant form the Pareto front.

    If *objectives* is empty or variants have no matching keys, every variant
    is treated as non-dominated (no dominance relationship can be established).

    Args:
        variants: List of variant dicts.  Each dict may carry per-dimension
            fitness scores under the keys named in *objectives*.  Falls back
            to the scalar ``'fitness'`` key when a named objective is absent.
        objectives: List of dimension/objective names to compare.

    Returns:
        Subset of *variants* that form the Pareto front.  Order is
        preserved relative to the input list.
    """
    if not variants:
        return []

    if not objectives:
        # No objectives defined — every variant is non-dominated.
        return list(variants)

    def scores_for(variant: Dict) -> List[float]:
        """Extract objective scores for a variant."""
        result = []
        for obj in objectives:
            if obj in variant:
                result.append(float(variant[obj]))
            else:
                # Fall back to scalar fitness
                result.append(float(variant.get("fitness", 0.0)))
        return result

    n = len(variants)
    dominated = [False] * n

    for i in range(n):
        if dominated[i]:
            continue
        si = scores_for(variants[i])
        for j in range(n):
            if i == j or dominated[j]:
                continue
            sj = scores_for(variants[j])
            # Check if j dominates i
            all_ge = all(sj[k] >= si[k] for k in range(len(objectives)))
            any_gt = any(sj[k] > si[k] for k in range(len(objectives)))
            if all_ge and any_gt:
                dominated[i] = True
                break

    return [v for v, dom in zip(variants, dominated) if not dom]


# ---------------------------------------------------------------------------
# Engine implementations
# ---------------------------------------------------------------------------


def _optimize_gepa(
    initial_content: str,
    config: OptimizerConfig,
    eval_fn: Callable[[str], float],
    mutate_fn: Callable[[str, int, str], str],
) -> OptimizeResult:
    """GEPA engine: reflective mutation with failure-analysis feedback.

    Each generation:
    1. Evaluate all variants.
    2. Build structured feedback (fitness score + generation info).
    3. Select top 50% as parents.
    4. Mutate each parent with feedback to create offspring.
    5. Merge parents + offspring, cap at population_size.
    6. Check convergence.
    """
    # Initialise population
    seed_variant: Dict = {
        "content": initial_content,
        "fitness": 0.0,
        "generation": 0,
        "parent": None,
    }
    population = Population(variants=[seed_variant], generation=0)

    fitness_trajectory: List[float] = []
    no_improvement_count = 0
    prev_best_fitness: Optional[float] = None
    converged = False

    for gen in range(1, config.iterations + 1):
        population.generation = gen

        # --- Evaluate ---
        for variant in population.variants:
            variant["fitness"] = eval_fn(variant["content"])

        # Best fitness this generation
        best_fitness = max(v["fitness"] for v in population.variants)
        fitness_trajectory.append(best_fitness)

        # --- Convergence check ---
        if prev_best_fitness is not None:
            improvement = best_fitness - prev_best_fitness
            if improvement < config.convergence_threshold:
                no_improvement_count += 1
            else:
                no_improvement_count = 0
        prev_best_fitness = best_fitness

        if no_improvement_count >= config.convergence_patience:
            converged = True
            break

        # --- Select parents (top 50%) ---
        sorted_variants = sorted(
            population.variants, key=lambda v: v["fitness"], reverse=True
        )
        n_parents = max(1, len(sorted_variants) // 2)
        parents = sorted_variants[:n_parents]

        # --- Mutate with reflective feedback ---
        offspring: List[Dict] = []
        for parent in parents:
            feedback = (
                f"fitness={parent['fitness']:.4f}; "
                f"generation={gen}; "
                f"strategy={config.mutation_strategy}"
            )
            new_content = mutate_fn(parent["content"], gen, feedback)
            offspring.append(
                {
                    "content": new_content,
                    "fitness": 0.0,
                    "generation": gen,
                    "parent": parent["content"],
                }
            )

        # --- Merge and cap population ---
        all_variants = sorted_variants + offspring
        population.variants = all_variants[: config.population_size]

    # Final evaluation pass to ensure fitness is current
    for variant in population.variants:
        if variant["fitness"] == 0.0:
            variant["fitness"] = eval_fn(variant["content"])

    best_variant = max(population.variants, key=lambda v: v["fitness"])

    return OptimizeResult(
        best_variant=best_variant,
        fitness_trajectory=fitness_trajectory,
        generations_run=population.generation,
        converged=converged,
        final_population=population,
    )


def _optimize_miprov2(
    initial_content: str,
    config: OptimizerConfig,
    eval_fn: Callable[[str], float],
    mutate_fn: Callable[[str, int, str], str],
) -> OptimizeResult:
    """MIPROv2 engine: history-based mutation selection.

    Maintains a full history of all evaluated variants.  Each generation,
    selects candidates from the top percentile of the history (upper-confidence-
    bound heuristic) rather than just the current population.

    This emulates MIPROv2's Bayesian-inspired search without an actual
    Bayesian optimisation library.
    """
    seed_variant: Dict = {
        "content": initial_content,
        "fitness": 0.0,
        "generation": 0,
        "parent": None,
    }

    # Full history of all evaluated variants across all generations
    history: List[Dict] = [seed_variant]
    # Current active population
    population = Population(variants=[seed_variant], generation=0)

    fitness_trajectory: List[float] = []
    no_improvement_count = 0
    prev_best_fitness: Optional[float] = None
    converged = False

    for gen in range(1, config.iterations + 1):
        population.generation = gen

        # --- Evaluate current population ---
        for variant in population.variants:
            if variant["fitness"] == 0.0:
                variant["fitness"] = eval_fn(variant["content"])

        # Add newly evaluated variants to history
        existing_contents = {v["content"] for v in history}
        for variant in population.variants:
            if variant["content"] not in existing_contents:
                history.append(variant)
                existing_contents.add(variant["content"])

        # Best fitness this generation
        best_fitness = max(v["fitness"] for v in population.variants)
        fitness_trajectory.append(best_fitness)

        # --- Convergence check ---
        if prev_best_fitness is not None:
            improvement = best_fitness - prev_best_fitness
            if improvement < config.convergence_threshold:
                no_improvement_count += 1
            else:
                no_improvement_count = 0
        prev_best_fitness = best_fitness

        if no_improvement_count >= config.convergence_patience:
            converged = True
            break

        # --- Select from history (top percentile, UCB-style) ---
        # Sort history by fitness, select top 25% as parent candidates
        sorted_history = sorted(history, key=lambda v: v["fitness"], reverse=True)
        n_top = max(1, len(sorted_history) // 4)
        top_candidates = sorted_history[:n_top]

        # Select parents from top candidates (up to half population_size)
        n_parents = max(1, config.population_size // 2)
        parents = (top_candidates * ((n_parents // len(top_candidates)) + 1))[
            :n_parents
        ]

        # --- Mutate selected parents ---
        offspring: List[Dict] = []
        for parent in parents:
            feedback = (
                f"history_size={len(history)}; "
                f"fitness={parent['fitness']:.4f}; "
                f"generation={gen}; "
                f"engine=miprov2"
            )
            new_content = mutate_fn(parent["content"], gen, feedback)
            offspring.append(
                {
                    "content": new_content,
                    "fitness": 0.0,
                    "generation": gen,
                    "parent": parent["content"],
                }
            )

        # --- Update population ---
        # Combine best from history + new offspring
        best_from_history = sorted_history[: config.population_size // 2]
        population.variants = (best_from_history + offspring)[: config.population_size]

    # Final evaluation pass
    for variant in population.variants:
        if variant["fitness"] == 0.0:
            variant["fitness"] = eval_fn(variant["content"])

    best_variant = max(population.variants, key=lambda v: v["fitness"])

    return OptimizeResult(
        best_variant=best_variant,
        fitness_trajectory=fitness_trajectory,
        generations_run=population.generation,
        converged=converged,
        final_population=population,
    )


def _optimize_darwinian(
    initial_content: str,
    config: OptimizerConfig,
    eval_fn: Callable[[str], float],
    mutate_fn: Callable[[str, int, str], str],
) -> OptimizeResult:
    """Darwinian code evolution engine — NOT YET IMPLEMENTED.

    Phase 4 / future work.  Would take code files as variants and apply
    AST-level mutations (function body replacement) validated via test suite.

    Raises:
        NotImplementedError: Always.
    """
    raise NotImplementedError("Darwinian code evolution not yet implemented")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def optimize(
    initial_content: str,
    config: OptimizerConfig,
    eval_fn: Callable[[str], float],
    mutate_fn: Optional[Callable[[str, int, str], str]] = None,
) -> OptimizeResult:
    """Run the optimization loop using the engine specified in *config*.

    Dispatches to one of ``_optimize_gepa``, ``_optimize_miprov2``, or
    ``_optimize_darwinian`` based on ``config.engine``.

    Args:
        initial_content: The seed text variant to start optimization from.
        config: ``OptimizerConfig`` controlling engine, iterations, etc.
        eval_fn: Callback ``(content: str) -> float`` returning a fitness
            score in [0.0, 1.0].
        mutate_fn: Optional callback ``(content, generation, feedback) -> str``
            producing a mutated variant.  Defaults to
            :func:`default_mutate_fn` when ``None``.

    Returns:
        An :class:`OptimizeResult` describing the best variant found,
        fitness trajectory, and final population.

    Raises:
        ValueError: If ``config.engine`` is not a recognised value.
        NotImplementedError: If ``config.engine == 'darwinian'``.
    """
    if mutate_fn is None:
        mutate_fn = default_mutate_fn

    engine = config.engine.lower()

    if engine == "gepa":
        return _optimize_gepa(initial_content, config, eval_fn, mutate_fn)
    elif engine == "miprov2":
        return _optimize_miprov2(initial_content, config, eval_fn, mutate_fn)
    elif engine == "darwinian":
        return _optimize_darwinian(initial_content, config, eval_fn, mutate_fn)
    else:
        raise ValueError(
            f"Unknown engine {engine!r}. Supported: 'gepa', 'miprov2', 'darwinian'."
        )
