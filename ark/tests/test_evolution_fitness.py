"""
Tests for evolution fitness module — TC-008 through TC-012.

Tests that dataset_builder.py generates valid evaluation datasets and
fitness.py scores variants correctly.
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_EVOLUTION_DIR = REPO_ROOT / "tools" / "evolution"
if str(_EVOLUTION_DIR) not in sys.path:
    sys.path.insert(0, str(_EVOLUTION_DIR))

from dataset_builder import (  # noqa: E402
    build_dataset,
    generate_synthetic,
    assign_splits,
    load_golden,
    save_jsonl,
)
from fitness import (  # noqa: E402
    score_variant,
    aggregate_scores,
    evaluate_dataset,
    FitnessResult,
    EvalResult,
)


# ============================================================
# TC-008: Dataset builder generates valid synthetic cases
# ============================================================

def test_dataset_synthetic():
    """TC-008: build_dataset with source: synthetic returns valid JSONL-serializable cases."""
    spec = {
        "source": "synthetic",
        "path": "",
        "num_cases": 5,
        "splits": {"train": 0.7, "val": 0.15, "test": 0.15},
    }
    cases = build_dataset(spec, seed=42)
    assert isinstance(cases, list)
    assert len(cases) == 5
    for case in cases:
        assert "id" in case
        assert "input" in case
        assert "expected_output" in case
        assert "source" in case
        assert "split" in case
        # Verify JSON serializable
        json.dumps(case)


def test_dataset_size_matches_spec():
    """Number of returned cases matches num_cases in dataset spec."""
    for n in [3, 7, 10, 20]:
        spec = {"source": "synthetic", "path": "", "num_cases": n}
        cases = build_dataset(spec, seed=42)
        assert len(cases) == n, f"Expected {n} cases, got {len(cases)}"


def test_synthetic_determinism():
    """generate_synthetic is deterministic: same seed gives same output."""
    content = "This is test content. It has multiple sentences."
    cases1 = generate_synthetic(content, num_cases=5, seed=42)
    cases2 = generate_synthetic(content, num_cases=5, seed=42)
    assert [c["id"] for c in cases1] == [c["id"] for c in cases2]
    assert [c["input"] for c in cases1] == [c["input"] for c in cases2]


def test_synthetic_empty_content():
    """generate_synthetic with empty content still generates cases."""
    cases = generate_synthetic("", num_cases=3, seed=42)
    assert len(cases) == 3
    for case in cases:
        assert "id" in case
        assert "source" in case
        assert case["source"] == "synthetic"


# ============================================================
# TC-009: Dataset builder assigns splits correctly
# ============================================================

def test_dataset_splits():
    """TC-009: assign_splits produces proportions within ±1 case and sums to total."""
    cases = [{"id": f"c{i}"} for i in range(20)]
    result = assign_splits(cases, {"train": 0.7, "val": 0.15, "test": 0.15}, seed=42)

    assert set(result.keys()) == {"train", "val", "test"}
    total = sum(len(v) for v in result.values())
    assert total == 20

    # Proportions within ±1 case
    assert abs(len(result["train"]) - 14) <= 1
    assert abs(len(result["val"]) - 3) <= 1
    assert abs(len(result["test"]) - 3) <= 1


def test_splits_all_cases_covered():
    """All cases appear in exactly one split."""
    cases = [{"id": f"c{i}"} for i in range(10)]
    result = assign_splits(cases, {"train": 0.8, "test": 0.2}, seed=99)
    all_ids = set()
    for split_cases in result.values():
        for c in split_cases:
            all_ids.add(c["id"])
    expected_ids = {f"c{i}" for i in range(10)}
    assert all_ids == expected_ids


def test_split_field_in_build_dataset():
    """Every case from build_dataset has a split field with valid value."""
    spec = {"source": "synthetic", "path": "", "num_cases": 10,
            "splits": {"train": 0.7, "val": 0.15, "test": 0.15}}
    cases = build_dataset(spec, seed=42)
    valid_splits = {"train", "val", "test"}
    for case in cases:
        assert case["split"] in valid_splits


# ============================================================
# TC-010: Fitness scorer produces 0.0–1.0 scores
# ============================================================

def test_score_variant():
    """TC-010: score_variant returns FitnessResult with all scores in [0.0, 1.0]."""
    def keyword_judge(variant, test_case, dimension):
        """Return 0.8 for any query — deterministic stub."""
        return 0.8

    test_case = {"input": "test", "expected": "answer"}
    dims = ["accuracy", "clarity", "brevity"]
    result = score_variant("some output", test_case, dims, keyword_judge)

    assert isinstance(result, FitnessResult)
    for dim, score in result.dimensions.items():
        assert 0.0 <= score <= 1.0, f"Score for {dim!r} out of range: {score}"
    assert 0.0 <= result.aggregate <= 1.0


def test_score_variant_clamps_out_of_range():
    """score_variant clamps judge_fn values that exceed [0.0, 1.0]."""
    def bad_judge(variant, test_case, dimension):
        return 1.5  # Out of range

    test_case = {"input": "x"}
    result = score_variant("v", test_case, ["dim1"], bad_judge)
    assert result.dimensions["dim1"] == 1.0  # clamped to 1.0


def test_score_variant_empty_dims():
    """score_variant with empty dimensions returns aggregate 0.0."""
    result = score_variant("v", {}, [], lambda v, t, d: 0.5)
    assert result.aggregate == 0.0
    assert result.dimensions == {}


# ============================================================
# TC-011: Aggregation methods compute correctly
# ============================================================

def test_aggregation():
    """TC-011: aggregate_scores computes weighted_sum, min, and harmonic correctly."""
    scores = {"a": 0.8, "b": 0.4}
    weights = {"a": 0.6, "b": 0.4}

    # weighted_sum: (0.8*0.6 + 0.4*0.4) / (0.6 + 0.4) = (0.48 + 0.16) / 1.0 = 0.64
    ws = aggregate_scores(scores, weights, method="weighted_sum")
    assert abs(ws - 0.64) < 1e-6

    # min: min(0.8, 0.4) = 0.4
    mn = aggregate_scores(scores, weights, method="min")
    assert abs(mn - 0.4) < 1e-6

    # harmonic: sum(w) / sum(w/s) = 1.0 / (0.6/0.8 + 0.4/0.4) = 1.0 / (0.75 + 1.0) = 0.5714...
    hm = aggregate_scores(scores, weights, method="harmonic")
    expected_harmonic = 1.0 / (0.6 / 0.8 + 0.4 / 0.4)
    assert abs(hm - expected_harmonic) < 1e-6


def test_aggregation_equal_weights():
    """weighted_sum with equal weights equals simple mean."""
    scores = {"a": 0.6, "b": 0.9}
    weights = {"a": 1.0, "b": 1.0}
    result = aggregate_scores(scores, weights, method="weighted_sum")
    assert abs(result - 0.75) < 1e-6


def test_aggregation_min_returns_minimum():
    """min aggregation returns the minimum across all dimensions."""
    scores = {"x": 0.9, "y": 0.3, "z": 0.7}
    weights = {"x": 1.0, "y": 1.0, "z": 1.0}
    result = aggregate_scores(scores, weights, method="min")
    assert abs(result - 0.3) < 1e-6


def test_aggregation_unknown_method():
    """aggregate_scores raises ValueError for unknown method."""
    with pytest.raises(ValueError, match="Unknown aggregation method"):
        aggregate_scores({"a": 0.5}, {"a": 1.0}, method="nonexistent")


# ============================================================
# TC-012: evaluate_dataset returns mean fitness
# ============================================================

def test_evaluate_dataset():
    """TC-012: evaluate_dataset returns EvalResult with mean_fitness equal to mean of per-case aggregates."""
    # Build a dataset with known cases
    dataset = [{"id": "c0", "input": "x", "expected": "y"}] * 4

    # Judge returns fixed scores: 0.8 for accuracy, 0.6 for clarity
    def fixed_judge(variant, test_case, dim):
        return {"accuracy": 0.8, "clarity": 0.6}.get(dim, 0.5)

    dims = ["accuracy", "clarity"]
    weights = {"accuracy": 0.5, "clarity": 0.5}
    result = evaluate_dataset("variant content", dataset, dims, weights, fixed_judge)

    assert isinstance(result, EvalResult)
    assert result.dataset_size == 4
    assert len(result.scores) == 4
    # weighted_sum: (0.8*0.5 + 0.6*0.5) = 0.7
    assert abs(result.mean_fitness - 0.7) < 1e-6


def test_evaluate_dataset_empty():
    """evaluate_dataset with empty dataset returns mean_fitness=0.0."""
    result = evaluate_dataset("v", [], ["dim"], {}, lambda v, t, d: 0.5)
    assert result.mean_fitness == 0.0
    assert result.dataset_size == 0


def test_evaluate_dataset_single_case():
    """evaluate_dataset with one case returns that case's aggregate as mean_fitness."""
    dataset = [{"input": "q", "expected": "a"}]
    result = evaluate_dataset("v", dataset, ["dim"], {"dim": 1.0},
                              lambda v, t, d: 0.75)
    assert abs(result.mean_fitness - 0.75) < 1e-6


# ============================================================
# Golden set loading
# ============================================================

def test_golden_load(tmp_path):
    """load_golden parses a JSONL file and returns list of dicts."""
    jsonl_file = tmp_path / "golden.jsonl"
    cases = [
        {"id": "g0", "input": "test", "expected": "answer"},
        {"id": "g1", "input": "foo", "expected": "bar"},
    ]
    jsonl_file.write_text("\n".join(json.dumps(c) for c in cases), encoding="utf-8")

    loaded = load_golden(str(jsonl_file))
    assert len(loaded) == 2
    assert loaded[0]["id"] == "g0"
    assert loaded[1]["id"] == "g1"
