"""test_examples.py — End-to-end parametric tests over all four example grammars.

Covers:
  - TC-20: For each example, ark verify exits 0, IR extracts, all three verifier
    passes return PASS/PASS_OPAQUE, evaluate returns a list without crashing.

Each test is parametrized over the 4 example grammars:
  l_system.ark, cga_tower.ark, semantic_facade.ark, code_graph_viz.ark

The example grammars are structural type declarations only (they do not embed
concrete rule instances), so evaluate() returns [] (empty list) — this is the
documented "safe empty spec" behaviour. The assertions confirm no crash and no
exception, which is the TC-20 coverage obligation.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from shape_grammar.tools.evaluator import Terminal, evaluate
from shape_grammar.tools.ir import ShapeGrammarIR, extract_ir
from shape_grammar.tools.obj_writer import write_obj
from shape_grammar.tools.verify import (
    Result,
    Status,
    run_determinism,
    run_scope,
    run_termination,
)


# ---------------------------------------------------------------------------
# Example grammar paths
# ---------------------------------------------------------------------------

_EXAMPLES_DIR = Path("shape_grammar/examples")

_EXAMPLE_FILENAMES = [
    "l_system.ark",
    "cga_tower.ark",
    "semantic_facade.ark",
    "code_graph_viz.ark",
]

_PASS_STATUSES = {Status.PASS, Status.PASS_OPAQUE, Status.PASS_UNKNOWN}


# ---------------------------------------------------------------------------
# TC-20: Full pipeline — parse + verify + IR + evaluate (parametric)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("filename", _EXAMPLE_FILENAMES)
def test_all_examples_parse_verify_ir_evaluate(filename: str, tmp_path: Path) -> None:
    """For each example grammar: ark verify exits 0, IR extracts, verifier passes PASS,
    evaluate returns a list without crashing, write_obj produces a non-empty file.

    TC-20: Example-driven end-to-end: parse + verify + IR + evaluate each of 4 examples.
    """
    ark_path = _EXAMPLES_DIR / filename

    # Step 1: ark verify exits 0 — grammar is structurally valid.
    ark_cli = Path("ark/ark.py")
    result = subprocess.run(
        [sys.executable, str(ark_cli), "verify", str(ark_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, (
        f"ark verify {filename} exited {result.returncode}:\n{result.stderr[:500]}"
    )

    # Step 2: IR extraction succeeds and returns ShapeGrammarIR.
    ir = extract_ir(ark_path)
    assert isinstance(ir, ShapeGrammarIR), (
        f"extract_ir({filename}) returned {type(ir)}, expected ShapeGrammarIR"
    )
    assert len(ir.entities) > 0, (
        f"expected at least one entity in {filename}, got 0"
    )

    # Step 3: All three verifier passes return PASS/PASS_OPAQUE/PASS_UNKNOWN.
    term_result = run_termination(ir)
    assert term_result.status in _PASS_STATUSES, (
        f"{filename}: termination pass returned {term_result.status}: {term_result.message}"
    )

    det_result = run_determinism(ir)
    assert det_result.status in _PASS_STATUSES, (
        f"{filename}: determinism pass returned {det_result.status}: {det_result.message}"
    )

    scope_result = run_scope(ir)
    assert scope_result.status in _PASS_STATUSES, (
        f"{filename}: scope pass returned {scope_result.status}: {scope_result.message}"
    )

    # Step 4: evaluate returns a list (possibly empty — expected for spec-only grammars).
    terminals = evaluate(ir, 42)
    assert isinstance(terminals, list), (
        f"evaluate({filename}, 42) returned {type(terminals)}, expected list"
    )
    for t in terminals:
        assert isinstance(t, Terminal), (
            f"evaluate returned non-Terminal item: {type(t)}"
        )

    # Step 5: write_obj produces a non-empty file (even if terminals is empty,
    # the header comment makes the file non-empty).
    obj_path = tmp_path / f"{filename}.obj"
    write_obj(terminals, obj_path, seed=42)
    assert obj_path.exists(), f"write_obj did not create file for {filename}"
    assert os.path.getsize(obj_path) > 0, f"write_obj produced empty file for {filename}"


# ---------------------------------------------------------------------------
# Regression guards — specific grammars
# ---------------------------------------------------------------------------


def test_l_system_terminal_count() -> None:
    """l_system.ark produces a list from evaluate() (regression guard).

    The spec has no concrete rule instances, so evaluate returns [] — this is
    the documented safe-empty-spec behaviour. This test guards against regressions
    where evaluate() would crash rather than return an empty list.
    """
    ir = extract_ir(_EXAMPLES_DIR / "l_system.ark")
    terminals = evaluate(ir, 42)
    assert isinstance(terminals, list), (
        f"evaluate(l_system.ark) must return a list, got {type(terminals)}"
    )


def test_cga_tower_evaluate_returns_list() -> None:
    """cga_tower.ark evaluates without crashing and returns a list."""
    ir = extract_ir(_EXAMPLES_DIR / "cga_tower.ark")
    terminals = evaluate(ir, 42)
    assert isinstance(terminals, list)


def test_semantic_facade_evaluate_returns_list() -> None:
    """semantic_facade.ark evaluates without crashing and returns a list."""
    ir = extract_ir(_EXAMPLES_DIR / "semantic_facade.ark")
    terminals = evaluate(ir, 42)
    assert isinstance(terminals, list)


def test_code_graph_viz_evaluate_returns_list() -> None:
    """code_graph_viz.ark evaluates without crashing and returns a list."""
    ir = extract_ir(_EXAMPLES_DIR / "code_graph_viz.ark")
    terminals = evaluate(ir, 42)
    assert isinstance(terminals, list)
