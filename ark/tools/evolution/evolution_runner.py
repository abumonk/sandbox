"""
evolution_runner.py — Orchestrates the full evolution pipeline.

Ties together all evolution components:
  - Target loading (file content)
  - Dataset building (dataset_builder)
  - Fitness evaluation (fitness)
  - Optimization loop (optimizer)
  - Constraint checking (constraint_checker)
  - Benchmark gating

No external LLM dependency — uses callback-based architecture:
  - mutate_fn(content: str, generation: int, feedback: str) -> str
  - judge_fn(variant_content: str, test_case: dict, dimension: str) -> float
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from tools.evolution.dataset_builder import build_dataset
from tools.evolution.fitness import (
    EvalResult,
    FitnessResult,
    default_judge_fn,
    evaluate_dataset,
)
from tools.evolution.optimizer import (
    OptimizerConfig,
    OptimizeResult,
    default_mutate_fn,
    optimize,
)
from tools.evolution.constraint_checker import (
    ConstraintResult,
    check_all_constraints,
    should_block,
)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class EvolutionContext:
    """All resolved configuration needed to run one evolution loop.

    Attributes:
        target:      evolution_target AST dict (must contain 'file_ref' and 'name').
        optimizer:   optimizer AST dict (engine, iterations, population_size, etc.).
        dataset:     eval_dataset AST dict (source, path, num_cases, splits, etc.).
        fitness_fn:  fitness_function AST dict (dimensions, weights, method, etc.).
        gate:        benchmark_gate AST dict (tolerance/threshold for gating).
        constraints: List of constraint AST dicts (type, threshold, enforcement, ...).
    """

    target: Dict[str, Any]
    optimizer: Dict[str, Any]
    dataset: Dict[str, Any]
    fitness_fn: Dict[str, Any]
    gate: Dict[str, Any]
    constraints: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EvolutionReport:
    """Summary of a completed (or failed/blocked) evolution run.

    Attributes:
        target_name:        Name of the evolution target (from AST).
        best_variant:       Content string of the best variant found.
        best_fitness:       Aggregate fitness score of the best variant.
        fitness_trajectory: Best fitness per generation across the run.
        generations:        Number of generations actually executed.
        constraint_results: ConstraintResult list from the best variant check.
        benchmark_passed:   True if best_fitness meets the gate tolerance.
        status:             "complete" | "blocked" | "gated_out" | "error".
    """

    target_name: str
    best_variant: str
    best_fitness: float
    fitness_trajectory: List[float]
    generations: int
    constraint_results: List[ConstraintResult]
    benchmark_passed: bool
    status: str


# ---------------------------------------------------------------------------
# Reference resolution
# ---------------------------------------------------------------------------


def resolve_context(evolution_run: Dict[str, Any], ark_file: Any) -> EvolutionContext:
    """Resolve cross-references in an evolution_run AST item.

    Looks up target_ref, optimizer_ref, dataset_ref, gate_ref, and any
    constraint_refs by name inside the ArkFile indices.  The ArkFile object
    is expected to expose dict-like index attributes (or plain dicts) keyed by
    item name.  Supported index attribute names:

      - ``evolution_targets``  / ``targets``
      - ``optimizers``
      - ``eval_datasets``      / ``datasets``
      - ``fitness_functions``  / ``fitness_fns``
      - ``benchmark_gates``    / ``gates``
      - ``constraints``

    Args:
        evolution_run: Dict with keys like 'target_ref', 'optimizer_ref',
                       'dataset_ref', 'fitness_fn_ref', 'gate_ref',
                       and optionally 'constraint_refs' (list of names).
        ark_file:      Parsed ArkFile object or dict containing named indices.

    Returns:
        EvolutionContext with all references resolved to their AST dicts.

    Raises:
        ValueError: If any required reference cannot be resolved.
    """

    def _lookup(index_names: List[str], ref_key: str) -> Dict[str, Any]:
        """Try multiple index attribute names; raise ValueError on miss."""
        ref_value = evolution_run.get(ref_key)
        if not ref_value:
            raise ValueError(
                f"evolution_run is missing required reference key {ref_key!r}."
            )
        for attr in index_names:
            index = getattr(ark_file, attr, None)
            if index is None and isinstance(ark_file, dict):
                index = ark_file.get(attr)
            if index is not None:
                item = index.get(ref_value) if hasattr(index, "get") else None
                if item is not None:
                    return item
        raise ValueError(
            f"Could not resolve {ref_key}={ref_value!r}. "
            f"Checked indices: {index_names}."
        )

    target = _lookup(["evolution_targets", "targets"], "target_ref")
    optimizer = _lookup(["optimizers"], "optimizer_ref")
    dataset = _lookup(["eval_datasets", "datasets"], "dataset_ref")
    fitness_fn = _lookup(["fitness_functions", "fitness_fns"], "fitness_fn_ref")
    gate = _lookup(["benchmark_gates", "gates"], "gate_ref")

    # Constraints are optional — resolve each if present
    constraint_refs: List[str] = evolution_run.get("constraint_refs", [])
    constraints: List[Dict[str, Any]] = []
    for ref in constraint_refs:
        found = False
        for attr in ["constraints"]:
            index = getattr(ark_file, attr, None)
            if index is None and isinstance(ark_file, dict):
                index = ark_file.get(attr)
            if index is not None:
                item = index.get(ref) if hasattr(index, "get") else None
                if item is not None:
                    constraints.append(item)
                    found = True
                    break
        if not found:
            raise ValueError(
                f"Could not resolve constraint_ref={ref!r}. "
                "Checked index: 'constraints'."
            )

    return EvolutionContext(
        target=target,
        optimizer=optimizer,
        dataset=dataset,
        fitness_fn=fitness_fn,
        gate=gate,
        constraints=constraints,
    )


# ---------------------------------------------------------------------------
# Pipeline helpers
# ---------------------------------------------------------------------------


def _load_target_content(target: Dict[str, Any]) -> Optional[str]:
    """Read the target file content from disk.

    Returns None if the file does not exist or cannot be read.
    """
    file_ref = target.get("file_ref") or target.get("path") or target.get("file")
    if not file_ref:
        return None
    try:
        return Path(file_ref).read_text(encoding="utf-8")
    except (OSError, FileNotFoundError):
        return None


def _build_optimizer_config(optimizer_spec: Dict[str, Any]) -> OptimizerConfig:
    """Convert an optimizer AST dict to an OptimizerConfig."""
    return OptimizerConfig(
        engine=optimizer_spec.get("engine", "gepa"),
        iterations=int(optimizer_spec.get("iterations", 5)),
        population_size=int(optimizer_spec.get("population_size", 4)),
        mutation_strategy=optimizer_spec.get("mutation_strategy", "reflective"),
        convergence_threshold=float(
            optimizer_spec.get("convergence_threshold", 0.01)
        ),
        convergence_patience=int(
            optimizer_spec.get("convergence_patience", 3)
        ),
    )


def _check_benchmark_gate(best_fitness: float, gate: Dict[str, Any]) -> bool:
    """Return True if best_fitness satisfies the benchmark gate.

    The gate spec may carry a 'tolerance' or 'threshold' key (float in
    [0.0, 1.0]).  The variant passes when best_fitness >= that value.
    """
    tolerance = gate.get("tolerance") or gate.get("threshold") or gate.get("min_fitness")
    if tolerance is None:
        # No threshold specified — always pass
        return True
    return best_fitness >= float(tolerance)


# ---------------------------------------------------------------------------
# Default callbacks (delegating to module-level defaults)
# ---------------------------------------------------------------------------


def default_mutate_fn_wrapper(content: str, generation: int, feedback: str = "") -> str:
    """Delegate to optimizer.default_mutate_fn."""
    return default_mutate_fn(content, generation, feedback)


def default_judge_fn_wrapper(
    variant_content: str,
    test_case: dict,
    dimension: str,
) -> float:
    """Delegate to fitness.default_judge_fn."""
    return default_judge_fn(variant_content, test_case, dimension)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_evolution(
    context: EvolutionContext,
    mutate_fn: Optional[Callable[[str, int, str], str]] = None,
    judge_fn: Optional[Callable[[str, dict, str], float]] = None,
) -> EvolutionReport:
    """Execute the full evolution pipeline and return an EvolutionReport.

    Pipeline steps:
      1. Load target file content.
      2. Build evaluation dataset.
      3. Create eval_fn that wraps fitness scoring.
      4. Build OptimizerConfig from context.optimizer.
      5. Run optimizer loop.
      6. Check constraints on the best variant.
      7. Apply benchmark gate.
      8. Return EvolutionReport.

    Args:
        context:   Resolved EvolutionContext (all refs already resolved).
        mutate_fn: Optional mutation callback; defaults to default_mutate_fn.
        judge_fn:  Optional judge callback; defaults to default_judge_fn.

    Returns:
        EvolutionReport describing the outcome.
    """
    if mutate_fn is None:
        mutate_fn = default_mutate_fn_wrapper
    if judge_fn is None:
        judge_fn = default_judge_fn_wrapper

    target_name: str = context.target.get("name", "<unnamed>")

    # --- Step 1: Load target file content ---
    initial_content = _load_target_content(context.target)
    if initial_content is None:
        file_ref = (
            context.target.get("file_ref")
            or context.target.get("path")
            or context.target.get("file")
            or "<unknown>"
        )
        return EvolutionReport(
            target_name=target_name,
            best_variant="",
            best_fitness=0.0,
            fitness_trajectory=[],
            generations=0,
            constraint_results=[],
            benchmark_passed=False,
            status="error",
        )

    # --- Step 2: Build dataset ---
    dataset = build_dataset(context.dataset)

    # --- Step 3: Build eval_fn using fitness scoring ---
    rubric_dimensions: List[str] = context.fitness_fn.get("dimensions", [])
    weights: Dict[str, float] = context.fitness_fn.get("weights", {})
    agg_method: str = context.fitness_fn.get("method", "weighted_sum")

    # Ensure weights cover all dimensions (default to 1.0)
    for dim in rubric_dimensions:
        weights.setdefault(dim, 1.0)

    def eval_fn(content: str) -> float:
        """Score content against the full dataset and return mean fitness."""
        result: EvalResult = evaluate_dataset(
            variant_content=content,
            dataset=dataset,
            rubric_dimensions=rubric_dimensions,
            weights=weights,
            judge_fn=judge_fn,
            method=agg_method,
        )
        return result.mean_fitness

    # --- Step 4: Build OptimizerConfig ---
    optimizer_config = _build_optimizer_config(context.optimizer)

    # --- Step 5: Run optimizer ---
    optimize_result: OptimizeResult = optimize(
        initial_content=initial_content,
        config=optimizer_config,
        eval_fn=eval_fn,
        mutate_fn=mutate_fn,
    )

    best_content: str = optimize_result.best_variant.get("content", "")
    best_fitness: float = optimize_result.best_variant.get("fitness", 0.0)
    fitness_trajectory: List[float] = optimize_result.fitness_trajectory
    generations_run: int = optimize_result.generations_run

    # --- Step 6: Check constraints on best variant ---
    constraint_results: List[ConstraintResult] = check_all_constraints(
        original_content=initial_content,
        variant_content=best_content,
        constraints_list=context.constraints,
    )

    # --- Step 7: Determine status from constraints ---
    if should_block(constraint_results):
        return EvolutionReport(
            target_name=target_name,
            best_variant=best_content,
            best_fitness=best_fitness,
            fitness_trajectory=fitness_trajectory,
            generations=generations_run,
            constraint_results=constraint_results,
            benchmark_passed=False,
            status="blocked",
        )

    # --- Step 8: Benchmark gate ---
    benchmark_passed = _check_benchmark_gate(best_fitness, context.gate)
    status = "complete" if benchmark_passed else "gated_out"

    return EvolutionReport(
        target_name=target_name,
        best_variant=best_content,
        best_fitness=best_fitness,
        fitness_trajectory=fitness_trajectory,
        generations=generations_run,
        constraint_results=constraint_results,
        benchmark_passed=benchmark_passed,
        status=status,
    )
