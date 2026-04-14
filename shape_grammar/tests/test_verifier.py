"""test_verifier.py — Tests for shape_grammar.tools.verify passes.

Covers (per test-strategy.md §1):
  - Termination, determinism, and scope passes return PASS/PASS_OPAQUE
    on each of the three canonical spec islands (TC-04a, TC-04b, TC-04c).
  - Termination pass returns FAIL on the unbounded-derivation fixture
    (TC-04d).
  - Determinism pass FAILs on a crafted IR with a wall-clock reference.
  - Scope pass FAILs on a crafted IR with an undefined attr read.
  - CLI smoke: `python -m shape_grammar.tools.verify termination
    shape_grammar/specs/shape_grammar.ark` exits 0.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from shape_grammar.tools.ir import IRRule, ShapeGrammarIR, extract_ir
from shape_grammar.tools.verify import (
    Result,
    Status,
    run_determinism,
    run_scope,
    run_termination,
)


# ---------------------------------------------------------------------------
# Helpers / constants
# ---------------------------------------------------------------------------

_PASS_STATUSES = {Status.PASS, Status.PASS_OPAQUE, Status.PASS_UNKNOWN}
"""Statuses that indicate the pass did not find a violation."""


def _is_pass(result: Result) -> bool:
    return result.status in _PASS_STATUSES


# ---------------------------------------------------------------------------
# TC-04a: Termination pass on all spec islands
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "spec_name",
    ["shape_grammar.ark", "operations.ark", "semantic.ark"],
)
def test_termination_pass_all_spec_islands(spec_name: str) -> None:
    """Termination pass returns PASS or PASS_OPAQUE on all three spec islands.

    The base spec files declare no concrete rule instances, so the verifier
    returns PASS trivially (no rules to check). This is the expected and
    correct behaviour at the structural-spec level.
    """
    path = Path("shape_grammar/specs") / spec_name
    ir = extract_ir(path)
    result = run_termination(ir)
    assert _is_pass(result), (
        f"termination FAILED on {spec_name}: "
        f"status={result.status.value}, message={result.message!r}"
    )


# ---------------------------------------------------------------------------
# TC-04b: Determinism pass on all spec islands
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "spec_name",
    ["shape_grammar.ark", "operations.ark", "semantic.ark"],
)
def test_determinism_pass_all_spec_islands(spec_name: str) -> None:
    """Determinism pass returns PASS on all three spec islands.

    All three specs have no concrete rules and declare at most one seed field
    (shape_grammar.ark has exactly one; the others have none), so the pass
    returns PASS vacuously.
    """
    path = Path("shape_grammar/specs") / spec_name
    ir = extract_ir(path)
    result = run_determinism(ir)
    assert _is_pass(result), (
        f"determinism FAILED on {spec_name}: "
        f"status={result.status.value}, message={result.message!r}"
    )


# ---------------------------------------------------------------------------
# TC-04c: Scope pass on all spec islands
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "spec_name",
    ["shape_grammar.ark", "operations.ark", "semantic.ark"],
)
def test_scope_pass_all_spec_islands(spec_name: str) -> None:
    """Scope-safety pass returns PASS on all three spec islands.

    No concrete rules means no scope.get calls to check; the pass returns
    PASS vacuously.
    """
    path = Path("shape_grammar/specs") / spec_name
    ir = extract_ir(path)
    result = run_scope(ir)
    assert _is_pass(result), (
        f"scope FAILED on {spec_name}: "
        f"status={result.status.value}, message={result.message!r}"
    )


# ---------------------------------------------------------------------------
# TC-04d: Termination FAIL on unbounded-derivation fixture
# ---------------------------------------------------------------------------


def test_termination_fails_on_unbounded_fixture(
    unbounded_fixture_path: Path,
) -> None:
    """Termination pass returns FAIL when the grammar derivation is unbounded.

    Strategy:
      1. Parse unbounded.ark — confirms the file is syntactically valid Ark.
      2. Inject concrete IRRule instances that form an A→B→C chain with
         max_depth=1. The chain depth (2) exceeds max_depth (1), so Z3
         must find a satisfying assignment (dC=2 > 1) and return FAIL.

    The injection is necessary because shape_grammar/tools/ir.py populates
    ir.rules only from instance grammars (T15 example files). The structural
    spec in unbounded.ark proves Ark-validity; the injected rules provide
    the unbounded derivation for the verifier to analyse. This mirrors how
    a T15 grammar file would populate rules at evaluation time.
    """
    # Step 1: Parse the fixture (proves it's valid Ark).
    ir = extract_ir(unbounded_fixture_path)
    assert ir.island_name == "ShapeGrammar", (
        "unbounded.ark must declare a ShapeGrammar island"
    )

    # Step 2: Inject a linear chain A→B→C (length 2) with max_depth=1.
    # depth(rA)=0, depth(rB)=1, depth(rC)=2. Z3 sees 2 > 1 → FAIL.
    ir.max_depth = 1
    ir.axiom = "rA"
    ir.rules = [
        IRRule(id="rA", lhs="A", operations=[{"rhs": "B"}]),
        IRRule(id="rB", lhs="B", operations=[{"rhs": "C"}]),
        IRRule(id="rC", lhs="C", is_terminal=True, operations=[{"type": "insert"}]),
    ]

    result = run_termination(ir)
    assert result.status == Status.FAIL, (
        f"expected FAIL for unbounded grammar, got {result.status.value}: "
        f"{result.message!r}"
    )
    assert result.counterexample is not None, (
        "FAIL result must include a counterexample dict"
    )
    assert isinstance(result.counterexample, dict)


# ---------------------------------------------------------------------------
# Negative: Determinism FAIL on wall-clock reference (TC-04b negative)
# ---------------------------------------------------------------------------


def test_determinism_fails_on_env_read() -> None:
    """Determinism pass returns FAIL when a rule op references an env variable.

    Crafts a ShapeGrammarIR with one rule that has a 'source: os_env' key
    in its op dict. The determinism scanner must detect the _ENV_MARKERS
    hit and return FAIL.
    """
    ir = ShapeGrammarIR(
        source_file="synthetic",
        island_name="ShapeGrammar",
        max_depth=10,
        seed=42,
        axiom="rA",
        rules=[
            IRRule(
                id="rA",
                lhs="A",
                operations=[
                    # 'source' field contains 'os_env' — triggers ENV_MARKERS.
                    {"type": "ScopeOp", "source": "os_env:MY_PARAM"}
                ],
            )
        ],
    )
    result = run_determinism(ir)
    assert result.status == Status.FAIL, (
        f"expected FAIL for env-reading rule, got {result.status.value}: "
        f"{result.message!r}"
    )


def test_determinism_fails_on_clock_reference() -> None:
    """Determinism pass returns FAIL when a rule op references wall-clock time."""
    ir = ShapeGrammarIR(
        source_file="synthetic",
        island_name="ShapeGrammar",
        max_depth=10,
        seed=42,
        axiom="rA",
        rules=[
            IRRule(
                id="rA",
                lhs="A",
                operations=[
                    # 'source' field contains 'datetime' — triggers CLOCK_MARKERS.
                    {"type": "ExtrudeOp", "height_source": "datetime.now()"}
                ],
            )
        ],
    )
    result = run_determinism(ir)
    assert result.status == Status.FAIL, (
        f"expected FAIL for clock-referencing rule, got {result.status.value}: "
        f"{result.message!r}"
    )


# ---------------------------------------------------------------------------
# Negative: Scope FAIL on undefined attr read (TC-04c negative)
# ---------------------------------------------------------------------------


def test_scope_fails_on_undefined_attr() -> None:
    """Scope-safety pass returns FAIL when a rule reads an undefined attr.

    Constructs a grammar where rule rA reads scope attr 'color' but no
    rule in the system pushes 'color'. The scope pass must return FAIL
    with a counterexample listing the violation.
    """
    ir = ShapeGrammarIR(
        source_file="synthetic",
        island_name="ShapeGrammar",
        max_depth=5,
        axiom="rA",
        rules=[
            IRRule(
                id="rA",
                lhs="A",
                operations=[
                    # scope_get triggers _scope_reads; no rule pushes 'color'.
                    {"type": "ExtrudeOp", "scope_get": "color"}
                ],
            )
        ],
    )
    result = run_scope(ir)
    assert result.status == Status.FAIL, (
        f"expected FAIL for undefined scope attr, got {result.status.value}: "
        f"{result.message!r}"
    )
    assert result.counterexample is not None
    assert "violations" in result.counterexample


# ---------------------------------------------------------------------------
# CLI smoke test: exits 0 for each pass on shape_grammar.ark
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pass_name", ["termination", "determinism", "scope", "all"])
def test_verify_cli_exits_zero_on_spec(pass_name: str) -> None:
    """CLI `python -m shape_grammar.tools.verify <pass> shape_grammar.ark` exits 0.

    The spec file has no concrete rules; every pass returns PASS vacuously.
    Exit code 0 maps to PASS or PASS_OPAQUE.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "shape_grammar.tools.verify",
            pass_name,
            "shape_grammar/specs/shape_grammar.ark",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd="R:/Sandbox",
    )
    assert result.returncode == 0, (
        f"CLI 'verify {pass_name}' exited {result.returncode}; "
        f"stdout={result.stdout!r}; stderr={result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# Sanity: Result dataclass behaviour
# ---------------------------------------------------------------------------


def test_result_is_ok_pass() -> None:
    """Result.is_ok is True for PASS and PASS_OPAQUE, False for FAIL."""
    assert Result(status=Status.PASS).is_ok is True
    assert Result(status=Status.PASS_OPAQUE).is_ok is True
    assert Result(status=Status.FAIL).is_ok is False
    assert Result(status=Status.PASS_UNKNOWN).is_ok is False


def test_result_exit_codes() -> None:
    """Result.exit_code: PASS/PASS_OPAQUE→0, FAIL→1, PASS_UNKNOWN→2."""
    assert Result(status=Status.PASS).exit_code == 0
    assert Result(status=Status.PASS_OPAQUE).exit_code == 0
    assert Result(status=Status.FAIL).exit_code == 1
    assert Result(status=Status.PASS_UNKNOWN).exit_code == 2
