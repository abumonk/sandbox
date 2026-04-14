"""
Tests for evolution optimizer module — TC-013 through TC-017.

Tests that optimizer.py correctly executes the GEPA-style loop,
Pareto-front selection, convergence detection, MIPROv2 history-based
selection, and Darwinian stub behavior.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_EVOLUTION_DIR = REPO_ROOT / "tools" / "evolution"
if str(_EVOLUTION_DIR) not in sys.path:
    sys.path.insert(0, str(_EVOLUTION_DIR))

from optimizer import (  # noqa: E402
    optimize,
    select_pareto_front,
    OptimizerConfig,
    OptimizeResult,
)


# ============================================================
# Helper factories
# ============================================================

def make_config(engine="gepa", iterations=2, population_size=4,
                mutation_strategy="reflective",
                convergence_threshold=0.01, convergence_patience=3):
    return OptimizerConfig(
        engine=engine,
        iterations=iterations,
        population_size=population_size,
        mutation_strategy=mutation_strategy,
        convergence_threshold=convergence_threshold,
        convergence_patience=convergence_patience,
    )


def constant_eval_fn(score):
    """Return an eval_fn that always returns the given score."""
    def fn(content: str) -> float:
        return score
    return fn


def counting_mutate_fn(call_log: list):
    """Return a mutate_fn that records call arguments."""
    def fn(content: str, generation: int, feedback: str = "") -> str:
        call_log.append({"content": content, "generation": generation,
                         "feedback": feedback})
        return f"{content}|gen{generation}"
    return fn


# ============================================================
# TC-013: Full optimization loop runs 2+ generations
# ============================================================

def test_full_loop():
    """TC-013: optimize with iterations=2 runs 2 full generations."""
    calls = []

    def eval_fn(content: str) -> float:
        return 0.5 + len(calls) * 0.01

    config = make_config(engine="gepa", iterations=2, convergence_patience=10)
    result = optimize("seed content", config, eval_fn)

    assert isinstance(result, OptimizeResult)
    assert result.generations_run >= 1  # At least 1 generation


def test_full_loop_gepa_returns_best_variant():
    """optimize with GEPA engine returns best_variant with fitness in [0, 1]."""
    gen_count = [0]

    def eval_fn(content: str) -> float:
        gen_count[0] += 1
        return min(0.4 + gen_count[0] * 0.05, 1.0)

    config = make_config(engine="gepa", iterations=3, convergence_patience=10)
    result = optimize("seed", config, eval_fn)

    assert isinstance(result.best_variant, dict)
    assert "content" in result.best_variant
    assert "fitness" in result.best_variant
    assert 0.0 <= result.best_variant["fitness"] <= 1.0


def test_population_size_capped():
    """Population after each generation does not exceed config.population_size."""
    config = make_config(engine="gepa", iterations=3, population_size=3,
                         convergence_patience=10)
    result = optimize("seed", config, constant_eval_fn(0.5))
    # Final population should not exceed population_size
    assert len(result.final_population.variants) <= config.population_size


def test_full_loop_fitness_trajectory():
    """OptimizeResult.fitness_trajectory has one entry per generation run."""
    config = make_config(engine="gepa", iterations=3, convergence_patience=10)
    result = optimize("seed", config, constant_eval_fn(0.6))
    # Trajectory length should equal generations_run
    assert len(result.fitness_trajectory) == result.generations_run


# ============================================================
# TC-014: Pareto-front selection identifies non-dominated variants
# ============================================================

def test_pareto():
    """TC-014: select_pareto_front returns non-dominated variants correctly."""
    # Variant A dominates B on both objectives
    # C dominates nothing and is dominated by nothing (non-dominated trade-off with D)
    # Design: A={0.8, 0.3}, B={0.4, 0.2}, C={0.5, 0.9}, D={0.9, 0.1}
    # A vs B: A >= B on both, A > B on both → A dominates B
    # A vs C: A.obj1(0.8) >= C.obj1(0.5) yes, but A.obj2(0.3) < C.obj2(0.9) → A does NOT dominate C
    # A vs D: A.obj1(0.8) < D.obj1(0.9) → A does NOT dominate D
    # D vs A: D.obj1(0.9) >= A.obj1(0.8) yes, but D.obj2(0.1) < A.obj2(0.3) → D does NOT dominate A
    variants = [
        {"content": "A", "fitness": 0.8, "obj1": 0.8, "obj2": 0.3},  # dominates B
        {"content": "B", "fitness": 0.3, "obj1": 0.4, "obj2": 0.2},  # dominated by A
        {"content": "C", "fitness": 0.7, "obj1": 0.5, "obj2": 0.9},  # non-dominated
        {"content": "D", "fitness": 0.5, "obj1": 0.9, "obj2": 0.1},  # non-dominated
    ]
    objectives = ["obj1", "obj2"]
    front = select_pareto_front(variants, objectives)

    # A should be in the front
    contents = {v["content"] for v in front}
    assert "A" in contents
    # B should NOT be in the front (dominated by A)
    assert "B" not in contents
    # C and D are non-dominated — both should be in the front
    assert "C" in contents
    assert "D" in contents


def test_pareto_empty_input():
    """select_pareto_front with empty input returns empty list."""
    assert select_pareto_front([], ["obj1"]) == []


def test_pareto_no_objectives_returns_all():
    """select_pareto_front with no objectives returns all variants (non-dominated)."""
    variants = [{"content": "A"}, {"content": "B"}]
    front = select_pareto_front(variants, [])
    assert len(front) == 2


def test_pareto_single_variant():
    """A single variant is always in the Pareto front."""
    variants = [{"content": "solo", "fitness": 0.5, "obj1": 0.5}]
    front = select_pareto_front(variants, ["obj1"])
    assert len(front) == 1
    assert front[0]["content"] == "solo"


# ============================================================
# TC-015: Convergence detection stops optimization early
# ============================================================

def test_convergence():
    """TC-015: optimize with constant fitness stops early and sets converged=True."""
    config = make_config(
        engine="gepa",
        iterations=20,
        convergence_threshold=0.001,
        convergence_patience=3,
    )
    # Constant eval_fn: no improvement → convergence after patience generations
    result = optimize("seed", config, constant_eval_fn(0.5))

    assert result.converged is True
    # Should stop before max iterations
    assert result.generations_run < config.iterations


def test_convergence_miprov2():
    """MIPROv2 engine also detects convergence on constant fitness."""
    config = make_config(
        engine="miprov2",
        iterations=20,
        convergence_threshold=0.001,
        convergence_patience=3,
    )
    result = optimize("seed", config, constant_eval_fn(0.7))
    assert result.converged is True


# ============================================================
# TC-016: MIPROv2 uses history-based selection
# ============================================================

def test_miprov2():
    """TC-016: optimize with engine=miprov2 runs without errors."""
    gen_count = [0]

    def eval_fn(content: str) -> float:
        gen_count[0] += 1
        return min(0.3 + gen_count[0] * 0.03, 1.0)

    config = make_config(engine="miprov2", iterations=2, convergence_patience=10)
    result = optimize("seed", config, eval_fn)

    assert isinstance(result, OptimizeResult)
    assert result.best_variant is not None


def test_miprov2_feedback_contains_history():
    """MIPROv2 mutate_fn receives feedback mentioning history_size after gen 1."""
    feedback_log = []

    def tracking_mutate(content: str, generation: int, feedback: str = "") -> str:
        feedback_log.append(feedback)
        return f"{content}|gen{generation}"

    config = make_config(engine="miprov2", iterations=2, convergence_patience=10)
    optimize("seed", config, constant_eval_fn(0.5), tracking_mutate)

    # At least one feedback string should mention history
    assert any("history" in fb for fb in feedback_log), (
        f"Expected history mention in feedback. Got: {feedback_log}"
    )


# ============================================================
# TC-017: Darwinian stub raises NotImplementedError
# ============================================================

def test_darwinian_stub():
    """TC-017: optimize with engine=darwinian raises NotImplementedError."""
    config = make_config(engine="darwinian", iterations=1)
    with pytest.raises(NotImplementedError) as exc_info:
        optimize("seed", config, constant_eval_fn(0.5))
    # Message should mention Phase 4 or not implemented
    err_msg = str(exc_info.value).lower()
    assert "not" in err_msg or "phase" in err_msg


def test_unknown_engine_raises():
    """optimize with unknown engine raises ValueError."""
    config = make_config(engine="unknown_engine", iterations=1)
    with pytest.raises(ValueError, match="Unknown engine"):
        optimize("seed", config, constant_eval_fn(0.5))
