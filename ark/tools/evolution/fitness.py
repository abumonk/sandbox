"""
fitness.py — LLM-as-judge scoring framework for rubric-based variant evaluation.

Provides rubric-based scoring, aggregation methods, and dataset-level evaluation.
No external LLM dependency — uses a judge_fn callback for scoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class FitnessResult:
    """Scoring result for a single variant against a single test case."""

    dimensions: Dict[str, float]
    """Mapping of dimension name → score in [0.0, 1.0]."""

    aggregate: float
    """Combined aggregate score in [0.0, 1.0]."""

    method: str
    """Aggregation method used (e.g. 'weighted_sum', 'min', 'harmonic')."""


@dataclass
class EvalResult:
    """Evaluation result for a variant across an entire dataset."""

    mean_fitness: float
    """Mean aggregate fitness across all test cases, in [0.0, 1.0]."""

    scores: List[FitnessResult]
    """Per-case FitnessResult objects."""

    dataset_size: int
    """Number of test cases in the dataset."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _clamp(value: float) -> float:
    """Clamp *value* to the closed interval [0.0, 1.0]."""
    return max(0.0, min(1.0, float(value)))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def default_judge_fn(
    variant_content: str,
    test_case: dict,
    dimension_name: str,
) -> float:
    """Baseline judge that always returns 0.5.

    This is a placeholder for an LLM-as-judge implementation.  Replace with a
    real callable when integrating with an LLM backend.

    Args:
        variant_content: The content/output of the variant being evaluated.
        test_case: A dict with at least ``input`` and ``expected`` keys.
        dimension_name: The rubric dimension being scored.

    Returns:
        Always 0.5 (neutral score).
    """
    return 0.5


def score_variant(
    variant_content: str,
    test_case: dict,
    rubric_dimensions: List[str],
    judge_fn: Callable[[str, dict, str], float],
) -> FitnessResult:
    """Score a single variant against one test case across all rubric dimensions.

    For each dimension, *judge_fn* is called with::

        judge_fn(variant_content, test_case, dimension_name) -> float

    The returned float must be in [0.0, 1.0]; scores are clamped to that range
    regardless.  The aggregate is computed as an unweighted mean so that the
    result is always independent of weight configuration at this stage.

    Args:
        variant_content: The content/output of the variant being evaluated.
        test_case: A dict describing the test case (e.g. ``{input, expected}``).
        rubric_dimensions: Ordered list of dimension names to score.
        judge_fn: Callback ``(variant_content, test_case, dimension_name) -> float``.

    Returns:
        A :class:`FitnessResult` with per-dimension scores and the aggregate.
    """
    if not rubric_dimensions:
        return FitnessResult(dimensions={}, aggregate=0.0, method="weighted_sum")

    dimension_scores: Dict[str, float] = {}
    for dim in rubric_dimensions:
        raw = judge_fn(variant_content, test_case, dim)
        dimension_scores[dim] = _clamp(raw)

    # Compute a simple equal-weight aggregate for convenience; callers that
    # need custom weights should use aggregate_scores() directly.
    agg = aggregate_scores(
        dimension_scores=dimension_scores,
        weights={dim: 1.0 for dim in rubric_dimensions},
        method="weighted_sum",
    )

    return FitnessResult(
        dimensions=dimension_scores,
        aggregate=agg,
        method="weighted_sum",
    )


def aggregate_scores(
    dimension_scores: Dict[str, float],
    weights: Dict[str, float],
    method: str = "weighted_sum",
) -> float:
    """Combine per-dimension scores into a single aggregate value.

    Supported methods:

    - ``"weighted_sum"``: ``sum(score * weight) / sum(weights)``  (normalised so
      result is in [0.0, 1.0] regardless of weight magnitude).
    - ``"min"``: minimum of all dimension scores (ignores weights).
    - ``"harmonic"``: weighted harmonic mean — ``sum(w) / sum(w / score)``; a
      score of 0.0 maps to the floor 0.0 to avoid division by zero.

    Args:
        dimension_scores: Mapping of dimension name → score in [0.0, 1.0].
        weights: Mapping of dimension name → non-negative weight.
        method: Aggregation method; one of ``"weighted_sum"``, ``"min"``,
            ``"harmonic"``.

    Returns:
        Aggregated score clamped to [0.0, 1.0].

    Raises:
        ValueError: If *method* is not recognised or *dimension_scores* is empty.
    """
    if not dimension_scores:
        return 0.0

    if method == "weighted_sum":
        total_weight = sum(weights.get(dim, 1.0) for dim in dimension_scores)
        if total_weight == 0.0:
            return 0.0
        weighted = sum(
            score * weights.get(dim, 1.0)
            for dim, score in dimension_scores.items()
        )
        return _clamp(weighted / total_weight)

    elif method == "min":
        return _clamp(min(dimension_scores.values()))

    elif method == "harmonic":
        # Weighted harmonic mean: sum(w_i) / sum(w_i / s_i)
        # If any score is 0.0 the harmonic mean is 0.0.
        scores = list(dimension_scores.items())
        total_weight = sum(weights.get(dim, 1.0) for dim, _ in scores)
        if total_weight == 0.0:
            return 0.0
        denom = 0.0
        for dim, score in scores:
            w = weights.get(dim, 1.0)
            if score == 0.0:
                return 0.0
            denom += w / score
        return _clamp(total_weight / denom)

    else:
        raise ValueError(
            f"Unknown aggregation method {method!r}. "
            "Supported: 'weighted_sum', 'min', 'harmonic'."
        )


def evaluate_dataset(
    variant_content: str,
    dataset: List[dict],
    rubric_dimensions: List[str],
    weights: Dict[str, float],
    judge_fn: Callable[[str, dict, str], float],
    method: str = "weighted_sum",
) -> EvalResult:
    """Score a variant against every test case in *dataset* and aggregate.

    For each test case, :func:`score_variant` is called to obtain per-dimension
    scores, then :func:`aggregate_scores` is called with *weights* and *method*
    to compute the case-level aggregate.  The mean of those aggregates becomes
    ``EvalResult.mean_fitness``.

    Args:
        variant_content: The content/output of the variant being evaluated.
        dataset: List of test case dicts.
        rubric_dimensions: Ordered list of dimension names to score.
        weights: Mapping of dimension name → weight used for aggregation.
        judge_fn: Callback ``(variant_content, test_case, dimension_name) -> float``.
        method: Aggregation method forwarded to :func:`aggregate_scores`.

    Returns:
        An :class:`EvalResult` with mean fitness, per-case scores, and dataset
        size.
    """
    if not dataset:
        return EvalResult(mean_fitness=0.0, scores=[], dataset_size=0)

    fitness_results: List[FitnessResult] = []
    for test_case in dataset:
        # Score all dimensions via judge_fn.
        dimension_scores: Dict[str, float] = {}
        for dim in rubric_dimensions:
            raw = judge_fn(variant_content, test_case, dim)
            dimension_scores[dim] = _clamp(raw)

        agg = aggregate_scores(
            dimension_scores=dimension_scores,
            weights=weights,
            method=method,
        )
        fitness_results.append(
            FitnessResult(
                dimensions=dimension_scores,
                aggregate=agg,
                method=method,
            )
        )

    mean_fitness = (
        sum(r.aggregate for r in fitness_results) / len(fitness_results)
    )

    return EvalResult(
        mean_fitness=_clamp(mean_fitness),
        scores=fitness_results,
        dataset_size=len(dataset),
    )
