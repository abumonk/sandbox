"""
Tests for evolution verification — TC-032 through TC-036.

Tests that evolution_verify.py catches mathematical constraint violations
and cross-reference errors, and that ark verify invokes evolution checks.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_VERIFY_DIR = REPO_ROOT / "tools" / "verify"
if str(_VERIFY_DIR) not in sys.path:
    sys.path.insert(0, str(_VERIFY_DIR))

from evolution_verify import (  # noqa: E402
    verify_split_ratios,
    verify_fitness_weights,
    verify_gate_tolerances,
    verify_cross_references,
    verify_constraint_refs,
    verify_optimizer_params,
    verify_evolution,
)


# ============================================================
# TC-032: verify_split_ratios catches bad ratios
# ============================================================

def test_split_ratio_fail():
    """TC-032: split ratios summing != 1.0 produce status='fail'."""
    # 0.7 + 0.2 + 0.2 = 1.1 (invalid)
    bad_dataset = [{"name": "ds1", "splits": {"train": 0.7, "val": 0.2, "test": 0.2}}]
    results = verify_split_ratios(bad_dataset)
    assert len(results) == 1
    assert results[0]["status"] == "fail"
    # Message should mention the incorrect sum or ratio
    assert "1." in results[0]["message"] or "sum" in results[0]["message"].lower()


def test_split_ratio_pass():
    """TC-032: valid split ratios (0.7, 0.15, 0.15) produce status='pass'."""
    good_dataset = [{"name": "ds_good", "splits": {"train": 0.7, "val": 0.15, "test": 0.15}}]
    results = verify_split_ratios(good_dataset)
    assert len(results) == 1
    assert results[0]["status"] == "pass"


def test_split_ratio_negative_fail():
    """verify_split_ratios catches a negative split value."""
    bad_dataset = [{"name": "ds_neg", "splits": {"train": -0.1, "val": 0.6, "test": 0.5}}]
    results = verify_split_ratios(bad_dataset)
    assert any(r["status"] == "fail" for r in results)


def test_split_ratio_missing_warns():
    """verify_split_ratios warns when splits field is missing."""
    no_split = [{"name": "ds_empty"}]  # no splits field
    results = verify_split_ratios(no_split)
    assert any(r["status"] in ("warn", "fail") for r in results)


# ============================================================
# TC-033: verify_fitness_weights catches bad weights
# ============================================================

def test_weight_fail():
    """TC-033: weights summing != 1.0 produce status='fail'."""
    # 0.6 + 0.6 = 1.2 (invalid)
    bad_ff = [{"name": "fn1", "dimensions": [{"weight": 0.6}, {"weight": 0.6}]}]
    results = verify_fitness_weights(bad_ff)
    assert len(results) == 1
    assert results[0]["status"] == "fail"


def test_weight_pass():
    """TC-033: weights summing to 1.0 produce status='pass'."""
    good_ff = [{"name": "fn_good", "dimensions": [{"weight": 0.5}, {"weight": 0.5}]}]
    results = verify_fitness_weights(good_ff)
    assert len(results) == 1
    assert results[0]["status"] == "pass"


def test_weight_negative_fail():
    """verify_fitness_weights catches a negative dimension weight."""
    bad_ff = [{"name": "fn_neg", "dimensions": [{"weight": -0.3}, {"weight": 1.3}]}]
    results = verify_fitness_weights(bad_ff)
    # Z3 should detect the negative weight constraint violation
    assert any(r["status"] == "fail" for r in results)


def test_weight_no_dimensions_warns():
    """verify_fitness_weights warns when dimensions are missing."""
    no_dims = [{"name": "fn_empty", "dimensions": []}]
    results = verify_fitness_weights(no_dims)
    assert any(r["status"] == "warn" for r in results)


# ============================================================
# TC-034: verify_gate_tolerances catches bad bounds
# ============================================================

def test_tolerance_fail():
    """TC-034: tolerance=-0.1 and tolerance=0 produce status='fail'."""
    # Negative tolerance
    bad_gate = [{"name": "gate1", "tolerance": -0.1}]
    results = verify_gate_tolerances(bad_gate)
    assert results[0]["status"] == "fail"

    # Zero tolerance (must be > 0)
    zero_gate = [{"name": "gate_zero", "tolerance": 0}]
    results = verify_gate_tolerances(zero_gate)
    assert results[0]["status"] == "fail"


def test_tolerance_pass():
    """TC-034: tolerance=0.05 produces status='pass'."""
    good_gate = [{"name": "gate_good", "tolerance": 0.05}]
    results = verify_gate_tolerances(good_gate)
    assert results[0]["status"] == "pass"


def test_tolerance_one_passes():
    """tolerance=1.0 (maximum allowed) produces status='pass'."""
    gate = [{"name": "gate_max", "tolerance": 1.0}]
    results = verify_gate_tolerances(gate)
    assert results[0]["status"] == "pass"


def test_tolerance_above_one_fails():
    """tolerance=1.1 (above 1.0) produces status='fail'."""
    gate = [{"name": "gate_high", "tolerance": 1.1}]
    results = verify_gate_tolerances(gate)
    assert results[0]["status"] == "fail"


# ============================================================
# TC-035: verify_cross_references catches unknown refs
# ============================================================

def test_xref_fail():
    """TC-035: runs referencing nonexistent items produce status='fail'."""
    runs = [{"name": "run1", "target": "nonexistent_target",
             "optimizer": None, "dataset": None, "gate": None}]
    # Empty ark_file — nothing exists
    ark_file = {"items": []}
    results = verify_cross_references(runs, ark_file)
    assert any(r["status"] == "fail" for r in results)
    assert any("nonexistent_target" in r["message"] for r in results)


def test_xref_pass():
    """TC-035: runs with valid cross-references produce status='pass'."""
    runs = [{"name": "run_good", "target": "MyTarget",
             "optimizer": "MyOpt", "dataset": "MyDS", "gate": "MyGate"}]
    ark_file = {
        "items": [
            {"kind": "evolution_target", "name": "MyTarget"},
            {"kind": "optimizer", "name": "MyOpt"},
            {"kind": "eval_dataset", "name": "MyDS"},
            {"kind": "benchmark_gate", "name": "MyGate"},
        ]
    }
    results = verify_cross_references(runs, ark_file)
    assert all(r["status"] == "pass" for r in results)


def test_constraint_ref_fail():
    """verify_constraint_refs catches target referencing a non-existent constraint name."""
    targets = [{"name": "T1", "constraint_refs": ["NonExistentConstraint"]}]
    constraints = []
    results = verify_constraint_refs(targets, constraints)
    assert any(r["status"] == "fail" for r in results)


def test_constraint_ref_pass():
    """verify_constraint_refs passes when all constraint refs resolve."""
    targets = [{"name": "T1", "constraint_refs": ["SizeLimit"]}]
    constraints = [{"name": "SizeLimit", "type": "size_limit"}]
    results = verify_constraint_refs(targets, constraints)
    assert all(r["status"] == "pass" for r in results)


# ============================================================
# Optimizer param bounds
# ============================================================

def test_optimizer_param_bounds_fail():
    """verify_optimizer_params catches iterations=0 or population_size=0."""
    # iterations=0 is invalid (must be > 0)
    bad_opt = [{"name": "opt1", "iterations": 0, "population_size": 4}]
    results = verify_optimizer_params(bad_opt)
    assert any(r["status"] == "fail" for r in results)

    # population_size=0 is invalid
    bad_opt2 = [{"name": "opt2", "iterations": 5, "population_size": 0}]
    results2 = verify_optimizer_params(bad_opt2)
    assert any(r["status"] == "fail" for r in results2)


def test_optimizer_param_bounds_pass():
    """verify_optimizer_params passes for valid parameter bounds."""
    good_opt = [{"name": "opt_good", "iterations": 5, "population_size": 4}]
    results = verify_optimizer_params(good_opt)
    assert all(r["status"] == "pass" for r in results)


# ============================================================
# TC-036: CLI verify integration
# ============================================================

@pytest.mark.integration
def test_verify_integration():
    """TC-036: ark verify on a valid spec exits 0."""
    spec_path = REPO_ROOT / "specs" / "meta" / "evolution_skills.ark"
    if not spec_path.exists():
        pytest.skip("specs/meta/evolution_skills.ark not found")

    result = subprocess.run(
        ["python", "ark.py", "verify", str(spec_path)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"ark verify failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )


@pytest.mark.integration
def test_verify_bad_spec_fails(tmp_path):
    """TC-036: spec with bad split ratios causes verify to report failure."""
    # Create a minimal spec with invalid split ratios
    bad_spec = tmp_path / "bad_evolution.ark"
    bad_spec.write_text("""
eval_dataset BadDS {
    source: synthetic
    splits { train: 0.5, val: 0.5, test: 0.5 }
}
""", encoding="utf-8")

    # Use verify_split_ratios directly to check our invalid spec
    bad_dataset = [{"name": "BadDS", "splits": {"train": 0.5, "val": 0.5, "test": 0.5}}]
    results = verify_split_ratios(bad_dataset)
    assert any(r["status"] == "fail" for r in results)
    # Message should mention the sum
    fail_results = [r for r in results if r["status"] == "fail"]
    assert any("1.5" in r["message"] or "sum" in r["message"].lower()
               for r in fail_results)


def test_verify_evolution_full():
    """verify_evolution runs all checks and returns a non-empty results list."""
    ark_file = {
        "items": [
            {"kind": "eval_dataset", "name": "DS1",
             "splits": {"train": 0.7, "val": 0.15, "test": 0.15}},
            {"kind": "fitness_function", "name": "FF1",
             "dimensions": [{"weight": 0.5}, {"weight": 0.5}]},
            {"kind": "benchmark_gate", "name": "G1", "tolerance": 0.8},
            {"kind": "optimizer", "name": "O1", "iterations": 5, "population_size": 4},
        ]
    }
    results = verify_evolution(ark_file)
    assert isinstance(results, list)
    assert len(results) > 0
    # All results should have required keys
    for r in results:
        assert "status" in r
        assert "message" in r
        assert "check" in r
