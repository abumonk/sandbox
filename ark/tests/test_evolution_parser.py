"""
Tests for evolution parser — TC-001 through TC-007.

Validates that evolution.ark parses cleanly, all 7 item kinds parse via Lark,
existing files are unaffected, the transformer produces correct AST dataclasses,
and ArkFile indices are populated correctly.
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_PARSER_DIR = REPO_ROOT / "tools" / "parser"
if str(_PARSER_DIR) not in sys.path:
    sys.path.insert(0, str(_PARSER_DIR))

from ark_parser import parse as ark_parse, to_json as ark_to_json  # noqa: E402
from ark_parser import (  # noqa: E402
    EvolutionTargetDef,
    EvalDatasetDef,
    FitnessFunctionDef,
    OptimizerDef,
    BenchmarkGateDef,
    EvolutionRunDef,
    EvolutionConstraintDef,
)

EVOLUTION_ARK = REPO_ROOT / "dsl" / "stdlib" / "evolution.ark"


def parse_snippet(source: str):
    """Parse an inline ARK snippet and return the ArkFile object."""
    return ark_parse(source)


def parse_snippet_ast(source: str) -> dict:
    """Parse an inline ARK snippet and return the AST dict."""
    ark_file = ark_parse(source)
    return json.loads(ark_to_json(ark_file))


# ============================================================
# TC-001: evolution.ark parses without errors
# ============================================================

def test_stdlib_parse():
    """TC-001: dsl/stdlib/evolution.ark parses via ArkParser without raising exceptions."""
    if not EVOLUTION_ARK.exists():
        pytest.skip("dsl/stdlib/evolution.ark not found")
    source = EVOLUTION_ARK.read_text(encoding="utf-8")
    ark_file = ark_parse(source, file_path=EVOLUTION_ARK)
    ast = json.loads(ark_to_json(ark_file))
    assert "items" in ast
    assert len(ast["items"]) > 0


# ============================================================
# TC-002: All enum/struct definitions match stdlib patterns
# ============================================================

@pytest.fixture(scope="module")
def evolution_ast():
    """Parse evolution.ark once and return the AST dict."""
    if not EVOLUTION_ARK.exists():
        pytest.skip("dsl/stdlib/evolution.ark not found")
    source = EVOLUTION_ARK.read_text(encoding="utf-8")
    ark_file = ark_parse(source, file_path=EVOLUTION_ARK)
    return json.loads(ark_to_json(ark_file))


def test_stdlib_syntax(evolution_ast):
    """TC-002: evolution.ark contains required enum and struct types."""
    items = evolution_ast["items"]
    item_names = {i.get("name") for i in items}
    # Enums
    assert "EvolutionTier" in item_names
    assert "OptimizerEngine" in item_names
    assert "DataSource" in item_names
    # Structs
    assert "FitnessScore" in item_names
    assert "Variant" in item_names
    assert "RunResult" in item_names


def test_evolution_tier_enum_values(evolution_ast):
    """EvolutionTier has skill, tool_desc, system_prompt, code variants."""
    items = evolution_ast["items"]
    enums = {i["name"]: i for i in items if i.get("kind") == "enum"}
    tier = enums.get("EvolutionTier")
    assert tier is not None
    variants = [v["name"] if isinstance(v, dict) else v for v in tier.get("variants", [])]
    assert "skill" in variants
    assert "tool_desc" in variants
    assert "system_prompt" in variants
    assert "code" in variants


def test_optimizer_engine_enum_values(evolution_ast):
    """OptimizerEngine has gepa, miprov2, darwinian variants."""
    items = evolution_ast["items"]
    enums = {i["name"]: i for i in items if i.get("kind") == "enum"}
    eng = enums.get("OptimizerEngine")
    assert eng is not None
    variants = [v["name"] if isinstance(v, dict) else v for v in eng.get("variants", [])]
    assert "gepa" in variants
    assert "miprov2" in variants
    assert "darwinian" in variants


def test_data_source_enum_values(evolution_ast):
    """DataSource has synthetic, session_db, golden, auto_eval variants."""
    items = evolution_ast["items"]
    enums = {i["name"]: i for i in items if i.get("kind") == "enum"}
    ds = enums.get("DataSource")
    assert ds is not None
    variants = [v["name"] if isinstance(v, dict) else v for v in ds.get("variants", [])]
    assert "synthetic" in variants
    assert "session_db" in variants
    assert "golden" in variants
    assert "auto_eval" in variants


# ============================================================
# TC-003: Lark grammar parses all 7 new item kinds
# ============================================================

def test_lark_parse_all_items():
    """TC-003: All 7 evolution item kinds parse via Lark grammar without errors."""
    snippets = [
        # 1. evolution_target
        """
evolution_target MyTarget {
    tier: skill
    file_ref: "skills/test.md"
}
""",
        # 2. eval_dataset
        """
eval_dataset MyDataset {
    source: "synthetic"
    split: { train: 0.7, val: 0.15, test: 0.15 }
}
""",
        # 3. fitness_function
        """
fitness_function MyFitness {
    dimension quality { weight: 0.6 }
    dimension brevity { weight: 0.4 }
    aggregation: weighted_sum
}
""",
        # 4. optimizer
        """
optimizer MyOptimizer {
    engine: gepa
    iterations: 5
    population_size: 4
    mutation_strategy: reflective
}
""",
        # 5. benchmark_gate
        """
benchmark_gate MyGate {
    benchmark: "TBLite"
    tolerance: 0.75
    pass_criteria: "mean_fitness >= tolerance"
}
""",
        # 6. evolution_run
        """
evolution_run MyRun {
    target: MyTarget
    optimizer: MyOptimizer
    dataset: MyDataset
    gate: MyGate
    status: pending
}
""",
        # 7. constraint
        """
constraint MySizeLimit {
    type: size_limit
    threshold: 1.2
    enforcement: block
}
""",
    ]
    for snippet in snippets:
        try:
            ark_file = parse_snippet(snippet)
            assert ark_file is not None
        except Exception as e:
            pytest.fail(f"Failed to parse snippet: {e}\nSnippet: {snippet[:80]}")


def test_evolution_target_parses():
    """evolution_target item kind parses without errors."""
    src = """
evolution_target SkillTarget {
    tier: skill
    file_ref: "skills/coding.md"
}
"""
    ark_file = parse_snippet(src)
    kinds = {type(item).__name__ for item in ark_file.items}
    assert "EvolutionTargetDef" in kinds


def test_eval_dataset_parses():
    """eval_dataset item kind parses without errors."""
    src = """
eval_dataset CodingDataset {
    source: "synthetic"
}
"""
    ark_file = parse_snippet(src)
    kinds = {type(item).__name__ for item in ark_file.items}
    assert "EvalDatasetDef" in kinds


def test_optimizer_parses():
    """optimizer item kind parses without errors."""
    src = """
optimizer GEPAOptimizer {
    engine: gepa
    iterations: 10
    population_size: 5
    mutation_strategy: reflective
}
"""
    ark_file = parse_snippet(src)
    kinds = {type(item).__name__ for item in ark_file.items}
    assert "OptimizerDef" in kinds


# ============================================================
# TC-005: Existing .ark files still parse after grammar extension
# ============================================================

def test_existing_files_parse():
    """TC-005: Representative existing .ark files parse after grammar extension."""
    files_to_check = [
        REPO_ROOT / "specs" / "meta" / "ark_studio.ark",
        REPO_ROOT / "dsl" / "stdlib" / "studio.ark",
        REPO_ROOT / "dsl" / "stdlib" / "types.ark",
    ]
    for p in files_to_check:
        if not p.exists():
            continue  # Skip files that don't exist
        source = p.read_text(encoding="utf-8")
        try:
            ark_file = ark_parse(source, file_path=p)
            ast = json.loads(ark_to_json(ark_file))
            assert len(ast["items"]) >= 1, f"{p} produced empty items list"
        except Exception as e:
            pytest.fail(f"Failed to parse existing file {p}: {e}")


def test_test_minimal_still_parses():
    """test_minimal.ark still parses after grammar changes."""
    p = REPO_ROOT / "specs" / "test_minimal.ark"
    if not p.exists():
        pytest.skip("test_minimal.ark not found")
    source = p.read_text(encoding="utf-8")
    ark_file = ark_parse(source, file_path=p)
    ast = json.loads(ark_to_json(ark_file))
    assert len(ast["items"]) >= 1


# ============================================================
# TC-006: Parser produces correct AST dataclasses
# ============================================================

def test_ast_dataclasses():
    """TC-006: Parsing each item kind snippet produces the correct AST dataclass."""
    # evolution_target
    src = 'evolution_target Tgt { tier: skill }'
    ark_file = parse_snippet(src)
    tgts = [i for i in ark_file.items if isinstance(i, EvolutionTargetDef)]
    assert len(tgts) == 1
    assert tgts[0].name == "Tgt"

    # eval_dataset
    src = 'eval_dataset DS { source: "synthetic" }'
    ark_file = parse_snippet(src)
    dss = [i for i in ark_file.items if isinstance(i, EvalDatasetDef)]
    assert len(dss) == 1
    assert dss[0].name == "DS"

    # fitness_function
    src = 'fitness_function FF { aggregation: weighted_sum }'
    ark_file = parse_snippet(src)
    ffs = [i for i in ark_file.items if isinstance(i, FitnessFunctionDef)]
    assert len(ffs) == 1
    assert ffs[0].name == "FF"

    # optimizer
    src = 'optimizer Opt { engine: gepa iterations: 3 population_size: 2 mutation_strategy: reflective }'
    ark_file = parse_snippet(src)
    opts = [i for i in ark_file.items if isinstance(i, OptimizerDef)]
    assert len(opts) == 1
    assert opts[0].name == "Opt"

    # benchmark_gate
    src = 'benchmark_gate Gate { benchmark: "TestBench" tolerance: 0.8 }'
    ark_file = parse_snippet(src)
    gates = [i for i in ark_file.items if isinstance(i, BenchmarkGateDef)]
    assert len(gates) == 1
    assert gates[0].name == "Gate"


def test_ast_evolution_run_dataclass():
    """evolution_run produces EvolutionRunDef with correct fields."""
    src = """
evolution_run Run1 {
    target: Tgt
    optimizer: Opt
    dataset: DS
    gate: Gate
    status: pending
}
"""
    ark_file = parse_snippet(src)
    runs = [i for i in ark_file.items if isinstance(i, EvolutionRunDef)]
    assert len(runs) == 1
    assert runs[0].name == "Run1"
    assert runs[0].status == "pending"


def test_ast_constraint_dataclass():
    """constraint produces EvolutionConstraintDef with correct fields."""
    src = """
constraint SizeLimit {
    type: size_limit
    threshold: 1.2
    enforcement: block
}
"""
    ark_file = parse_snippet(src)
    constraints = [i for i in ark_file.items if isinstance(i, EvolutionConstraintDef)]
    assert len(constraints) == 1
    assert constraints[0].name == "SizeLimit"


# ============================================================
# TC-007: ArkFile indices are populated correctly
# ============================================================

def test_arkfile_indices():
    """TC-007: Parsing a multi-item .ark snippet populates all evolution indices."""
    src = """
evolution_target T1 { tier: skill }
eval_dataset D1 { source: "synthetic" }
fitness_function F1 { aggregation: weighted_sum }
optimizer O1 { engine: gepa iterations: 3 population_size: 2 mutation_strategy: reflective }
benchmark_gate G1 { benchmark: "Bench" tolerance: 0.8 }
evolution_run R1 {
    target: T1
    optimizer: O1
    dataset: D1
    gate: G1
    status: pending
}
constraint C1 {
    type: size_limit
    threshold: 1.2
    enforcement: block
}
"""
    ark_file = parse_snippet(src)

    assert "T1" in ark_file.evolution_targets
    assert "D1" in ark_file.eval_datasets
    assert "F1" in ark_file.fitness_functions
    assert "O1" in ark_file.optimizers
    assert "G1" in ark_file.benchmark_gates
    assert "R1" in ark_file.evolution_runs
    assert "C1" in ark_file.evolution_constraints
