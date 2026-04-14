"""
Tests for evolution codegen — TC-028 through TC-031.

Tests that evolution_codegen.py generates valid JSONL templates,
Python scoring skeletons, run configs, and that the CLI codegen path works.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_CODEGEN_DIR = REPO_ROOT / "tools" / "codegen"
_PARSER_DIR = REPO_ROOT / "tools" / "parser"
for _d in [str(_CODEGEN_DIR), str(_PARSER_DIR)]:
    if _d not in sys.path:
        sys.path.insert(0, _d)

from evolution_codegen import (  # noqa: E402
    gen_dataset_jsonl,
    gen_scoring_script,
    gen_run_config,
    generate,
)


# ============================================================
# Helpers / fixtures
# ============================================================

@pytest.fixture
def simple_dataset():
    """A minimal eval_dataset AST dict."""
    return {
        "kind": "eval_dataset",
        "name": "TestDataset",
        "source": "synthetic",
        "splits": {"train": 0.7, "val": 0.15, "test": 0.15},
        "scoring_rubric": "accuracy",
        "data_fields": [],
        "description": "A test dataset",
    }


@pytest.fixture
def simple_fitness():
    """A minimal fitness_function AST dict."""
    return {
        "kind": "fitness_function",
        "name": "TestFitness",
        "dimensions": [
            {"name": "correctness", "weight": 0.6, "metric": "exact_match"},
            {"name": "clarity", "weight": 0.4, "metric": "human_eval"},
        ],
        "aggregation": "weighted_average",
        "data_fields": [],
        "description": "Test fitness function",
    }


@pytest.fixture
def simple_run():
    """A minimal evolution_run AST dict."""
    return {
        "kind": "evolution_run",
        "name": "TestRun",
        "target_ref": "TestTarget",
        "optimizer_ref": "TestOptimizer",
        "dataset_ref": "TestDataset",
        "gate_ref": "TestGate",
        "status": "pending",
        "data_fields": [],
        "description": "A test run",
    }


@pytest.fixture
def ark_file_dict(simple_dataset, simple_fitness, simple_run):
    """A mock ark_file dict with all indices populated."""
    return {
        "evolution_targets": {
            "TestTarget": {"name": "TestTarget", "file": "skills/test.md"},
        },
        "optimizers": {
            "TestOptimizer": {"name": "TestOptimizer", "engine": "gepa",
                              "iterations": 5, "population_size": 4,
                              "mutation_strategy": "reflective"},
        },
        "eval_datasets": {
            "TestDataset": simple_dataset,
        },
        "benchmark_gates": {
            "TestGate": {"name": "TestGate", "benchmark": "TBLite",
                         "tolerance": 0.8, "pass_criteria": ">=0.8"},
        },
    }


# ============================================================
# TC-028: gen_dataset_jsonl generates valid JSONL
# ============================================================

def test_dataset_jsonl(simple_dataset):
    """TC-028: gen_dataset_jsonl produces JSONL with required keys per line."""
    jsonl = gen_dataset_jsonl(simple_dataset)
    lines = [l for l in jsonl.split("\n") if l.strip()]

    assert len(lines) > 0
    for line in lines:
        record = json.loads(line)  # must be valid JSON
        assert "id" in record
        assert "input" in record
        assert "expected" in record
        assert "rubric_hints" in record
        assert "source" in record
        assert "split" in record


def test_dataset_jsonl_split_proportions(simple_dataset):
    """JSONL lines split proportions match the AST-specified ratios."""
    jsonl = gen_dataset_jsonl(simple_dataset)
    lines = [l for l in jsonl.split("\n") if l.strip()]
    splits = [json.loads(l)["split"] for l in lines]
    total = len(splits)

    train_count = splits.count("train")
    # 70% of total ± 1 case
    assert abs(train_count - round(0.7 * total)) <= 1


def test_dataset_jsonl_valid_json(simple_dataset):
    """All lines in the generated JSONL are valid JSON."""
    jsonl = gen_dataset_jsonl(simple_dataset)
    for line in jsonl.split("\n"):
        if line.strip():
            json.loads(line)  # Raises if invalid


def test_dataset_jsonl_source_field(simple_dataset):
    """JSONL records contain the source field from the dataset spec."""
    jsonl = gen_dataset_jsonl(simple_dataset)
    lines = [l for l in jsonl.split("\n") if l.strip()]
    first = json.loads(lines[0])
    assert first["source"] == "synthetic"


# ============================================================
# TC-029: gen_scoring_script produces valid Python
# ============================================================

def test_scoring_script(simple_fitness):
    """TC-029: gen_scoring_script produces a Python file with required elements."""
    script = gen_scoring_script(simple_fitness)

    assert "RUBRIC_DIMENSIONS" in script
    assert "AGGREGATION" in script
    assert "def score(" in script
    # Dimension names should appear
    assert "correctness" in script
    assert "clarity" in script


def test_scoring_script_is_valid_python(simple_fitness):
    """Generated scoring script compiles without SyntaxError."""
    script = gen_scoring_script(simple_fitness)
    try:
        compile(script, "<test_scoring_script>", "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated scoring script has SyntaxError: {e}\n\n{script}")


def test_scoring_script_weight_constants(simple_fitness):
    """Generated script contains WEIGHT_ constants for each dimension."""
    script = gen_scoring_script(simple_fitness)
    assert "WEIGHT_CORRECTNESS" in script
    assert "WEIGHT_CLARITY" in script


def test_scoring_script_aggregation_present(simple_fitness):
    """AGGREGATION constant contains the spec aggregation method."""
    script = gen_scoring_script(simple_fitness)
    assert "weighted_average" in script


# ============================================================
# TC-030: gen_run_config produces valid JSON with required keys
# ============================================================

def test_run_config(simple_run, ark_file_dict):
    """TC-030: gen_run_config produces a valid JSON file with required keys."""
    config_json = gen_run_config(simple_run, ark_file_dict)
    config = json.loads(config_json)  # must be valid JSON

    assert "target" in config or "target_file" in config
    assert "dataset" in config or "dataset_path" in config
    assert "optimizer" in config
    assert "gate" in config


def test_run_config_is_valid_json(simple_run, ark_file_dict):
    """gen_run_config output is parseable as JSON."""
    config_json = gen_run_config(simple_run, ark_file_dict)
    config = json.loads(config_json)
    assert isinstance(config, dict)


def test_run_config_run_name(simple_run, ark_file_dict):
    """Generated run config contains the run name."""
    config_json = gen_run_config(simple_run, ark_file_dict)
    config = json.loads(config_json)
    assert config.get("run_name") == "TestRun"


def test_run_config_references_resolved(simple_run, ark_file_dict):
    """gen_run_config resolves references to their AST dicts."""
    config_json = gen_run_config(simple_run, ark_file_dict)
    config = json.loads(config_json)
    # Target should be resolved (not just the ref string)
    assert config["target"]["name"] == "TestTarget"
    assert config["optimizer"]["name"] == "TestOptimizer"


# ============================================================
# TC-031: CLI codegen e2e (requires evolution_skills.ark spec)
# ============================================================

@pytest.mark.integration
def test_codegen_e2e(tmp_path):
    """TC-031: ark codegen --target evolution exits 0 and generates files."""
    spec_path = REPO_ROOT / "specs" / "meta" / "evolution_skills.ark"
    if not spec_path.exists():
        pytest.skip("specs/meta/evolution_skills.ark not found")

    out_dir = tmp_path / "evo_codegen_out"
    result = subprocess.run(
        ["python", "ark.py", "codegen", str(spec_path),
         "--target", "evolution", "--out", str(out_dir)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"ark codegen failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    # At least one output file should exist
    output_files = list(out_dir.rglob("*"))
    assert len([f for f in output_files if f.is_file()]) >= 1


# ============================================================
# Additional: generate() orchestrator with dict AST
# ============================================================

def test_generate_dict_ast():
    """generate() with dict AST produces artifacts for all item kinds."""
    ast_json = {
        "items": [
            {
                "kind": "eval_dataset",
                "name": "SampleDS",
                "source": "synthetic",
                "splits": {"train": 0.8, "test": 0.2},
                "scoring_rubric": "quality",
                "data_fields": [],
                "description": "",
            },
            {
                "kind": "fitness_function",
                "name": "SampleFF",
                "dimensions": [{"name": "quality", "weight": 1.0, "metric": "custom"}],
                "aggregation": "weighted_average",
                "data_fields": [],
                "description": "",
            },
            {
                "kind": "evolution_run",
                "name": "SampleRun",
                "target_ref": "T1",
                "optimizer_ref": "O1",
                "dataset_ref": "SampleDS",
                "gate_ref": "G1",
                "status": "pending",
                "data_fields": [],
                "description": "",
            },
        ]
    }
    artifacts = generate(ast_json)
    assert "datasets/SampleDS.jsonl" in artifacts
    assert "scoring/SampleFF_scorer.py" in artifacts
    assert "runs/SampleRun_config.json" in artifacts


def test_generate_writes_to_disk(tmp_path):
    """generate() with output_dir writes files to disk."""
    ast_json = {
        "items": [
            {
                "kind": "eval_dataset",
                "name": "DiskDS",
                "source": "synthetic",
                "splits": {"train": 1.0},
                "scoring_rubric": "",
                "data_fields": [],
                "description": "",
            },
        ]
    }
    generate(ast_json, output_dir=tmp_path)
    assert (tmp_path / "datasets" / "DiskDS.jsonl").exists()
