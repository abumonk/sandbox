"""test_evaluator.py — Tests for shape_grammar.tools.evaluator, ops, scope, rng, obj_writer.

Covers:
  - TC-05: Deterministic round-trip under fixed seed.
  - TC-07: grammar -> evaluator -> OBJ produces non-empty file.
  - TC-19: RNG determinism: SeededRng(42).fork("a") reproduces identical sequence.
  - Additional: RNG fork isolation, scope inheritance/override, ExtrudeOp, SplitOp,
    max_depth guard, OBJ group directives, negative test for invalid seed.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from shape_grammar.tools.evaluator import Terminal, evaluate, EvaluationError
from shape_grammar.tools.ir import IRRule, ShapeGrammarIR
from shape_grammar.tools.obj_writer import write_obj
from shape_grammar.tools.ops import ExtrudeOp, SplitOp, TERMINAL
from shape_grammar.tools.rng import SeededRng
from shape_grammar.tools.scope import Scope, ScopeStack


# ---------------------------------------------------------------------------
# Helpers — synthetic IRs for tests that don't need .ark files
# ---------------------------------------------------------------------------


def _simple_terminal_ir(max_depth: int = 5) -> ShapeGrammarIR:
    """Return a minimal IR with a single terminal rule A."""
    return ShapeGrammarIR(
        source_file="__test__",
        max_depth=max_depth,
        seed=42,
        axiom="A",
        rules=[IRRule(id="A", lhs="A", is_terminal=True, operations=[])],
    )


def _two_rule_ir(max_depth: int = 5) -> ShapeGrammarIR:
    """Return an IR with two terminal rules and an axiom that inserts via IOp."""
    return ShapeGrammarIR(
        source_file="__test__",
        max_depth=max_depth,
        seed=42,
        axiom="Root",
        rules=[
            IRRule(
                id="Root",
                lhs="Root",
                is_terminal=False,
                operations=[
                    {"kind": "i", "id": "Root_i1", "asset_path": "assets/a.obj"},
                    {"kind": "i", "id": "Root_i2", "asset_path": "assets/b.obj"},
                ],
                label="building",
            ),
        ],
    )


def _recursive_ir(max_depth: int = 3) -> ShapeGrammarIR:
    """IR where rule A recurses via ExtrudeOp (depth-bounded)."""
    return ShapeGrammarIR(
        source_file="__test__",
        max_depth=max_depth,
        seed=42,
        axiom="A",
        rules=[
            IRRule(
                id="A",
                lhs="A",
                is_terminal=False,
                operations=[
                    {"kind": "extrude", "id": "A_extrude", "height": 1.0, "symbol": "A"},
                ],
                label="level",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# TC-05: Deterministic round-trip
# ---------------------------------------------------------------------------


def test_deterministic_roundtrip(rng_seed: int) -> None:
    """Two calls to evaluate(ir, seed=42) must return identical terminal lists.

    TC-05: Python evaluator round-trip is deterministic under fixed seed.
    Uses two different IRs to give the test more coverage.
    """
    ir1 = _simple_terminal_ir()
    result1a = evaluate(ir1, rng_seed)
    result1b = evaluate(ir1, rng_seed)
    assert result1a == result1b, "simple terminal IR: two runs differ"

    ir2 = _two_rule_ir()
    result2a = evaluate(ir2, rng_seed)
    result2b = evaluate(ir2, rng_seed)
    assert result2a == result2b, "two-rule IR: two runs differ"


def test_different_seeds_may_differ() -> None:
    """Different seeds may yield different results; at minimum each is a valid list."""
    ir = _recursive_ir()
    r1 = evaluate(ir, 1)
    r2 = evaluate(ir, 99999)
    # Both must be lists of Terminals.
    assert isinstance(r1, list)
    assert isinstance(r2, list)
    for t in r1 + r2:
        assert isinstance(t, Terminal)


# ---------------------------------------------------------------------------
# TC-19: RNG determinism
# ---------------------------------------------------------------------------


def test_rng_determinism(rng_seed: int) -> None:
    """SeededRng(42).fork("a") called twice must produce the same 10-value sequence.

    TC-19: RNG determinism — independent construction, same sequence.
    """
    rng_a = SeededRng(rng_seed).fork("a")
    rng_b = SeededRng(rng_seed).fork("a")
    seq_a = [rng_a.random() for _ in range(10)]
    seq_b = [rng_b.random() for _ in range(10)]
    assert seq_a == seq_b, f"fork('a') sequences differ: {seq_a} vs {seq_b}"


def test_rng_fork_isolation() -> None:
    """fork('a') and fork('b') from the same parent must produce distinct sequences."""
    parent = SeededRng(42)
    rng_a = parent.fork("a")
    rng_b = parent.fork("b")
    seq_a = [rng_a.random() for _ in range(10)]
    seq_b = [rng_b.random() for _ in range(10)]
    assert seq_a != seq_b, "fork('a') and fork('b') produced identical sequences"


# ---------------------------------------------------------------------------
# Scope tests
# ---------------------------------------------------------------------------


def test_scope_inheritance() -> None:
    """A child scope must inherit attrs from its parent."""
    parent = Scope.identity().push({"color": "red"})
    child = parent.push()  # no override
    assert child.get("color") == "red", "child did not inherit parent color"


def test_scope_override() -> None:
    """A child scope that overrides a key must shadow the parent's value."""
    parent = Scope.identity().push({"color": "red"})
    child = parent.push({"color": "blue"})
    assert child.get("color") == "blue", "child override did not take effect"
    assert parent.get("color") == "red", "parent scope was mutated by child push"


# ---------------------------------------------------------------------------
# Op tests
# ---------------------------------------------------------------------------


def test_extrude_op_applies() -> None:
    """ExtrudeOp(height=5.0).apply() yields one child scope with size.z == 5.0."""
    op = ExtrudeOp(id="test_extrude", height=5.0)
    scope = Scope.identity()
    rng = SeededRng(42)
    children = op.apply(scope, rng, "wall")
    assert len(children) == 1, f"expected 1 child, got {len(children)}"
    child_scope, child_symbol, child_label = children[0]
    assert child_scope.size[2] == 5.0, f"expected size.z=5.0, got {child_scope.size[2]}"


def test_split_op_yields_n_children() -> None:
    """SplitOp(axis='x', sizes=[1.0, 2.0, 1.0]).apply() yields exactly 3 children."""
    op = SplitOp(id="test_split", axis="x", sizes=[1.0, 2.0, 1.0])
    scope = Scope.identity()
    rng = SeededRng(42)
    children = op.apply(scope, rng, "facade")
    assert len(children) == 3, f"expected 3 children from SplitOp, got {len(children)}"


# ---------------------------------------------------------------------------
# Max-depth guard (negative test)
# ---------------------------------------------------------------------------


def test_max_depth_guard() -> None:
    """An IR that would recurse forever is still bounded by max_depth.

    The evaluator prunes branches at max_depth: the output is a finite list
    of terminals, never an EvaluationError under normal operation.
    This tests the max_depth mechanism using the unbounded fixture pattern
    (a self-recursing rule with max_depth set low).
    """
    ir = _recursive_ir(max_depth=4)
    # Must not hang or raise; must return a list.
    result = evaluate(ir, 42)
    assert isinstance(result, list)
    # Depth of every terminal's provenance must be <= max_depth.
    for t in result:
        assert len(t.provenance) <= 4, (
            f"terminal provenance depth {len(t.provenance)} exceeds max_depth=4"
        )


# ---------------------------------------------------------------------------
# TC-07: OBJ round-trip
# ---------------------------------------------------------------------------


def test_grammar_to_obj_nonempty(tmp_path: Path, rng_seed: int) -> None:
    """evaluate -> write_obj -> file exists and is non-empty.

    TC-07: End-to-end grammar -> evaluator -> OBJ produces non-empty file.
    """
    ir = _simple_terminal_ir()
    terminals = evaluate(ir, rng_seed)
    out_obj = tmp_path / "out.obj"
    write_obj(terminals, out_obj, seed=rng_seed)
    assert out_obj.exists(), "OBJ file was not created"
    assert os.path.getsize(out_obj) > 0, "OBJ file is empty"


def test_obj_groups_match_labels(tmp_path: Path) -> None:
    """write_obj on terminals with two distinct labels must emit two 'g' directives."""
    scope = Scope.identity()
    terminals = [
        Terminal(scope=scope, tag="t1", label="wall", provenance=[]),
        Terminal(scope=scope, tag="t2", label="window", provenance=[]),
    ]
    out_obj = tmp_path / "groups.obj"
    write_obj(terminals, out_obj)
    content = out_obj.read_text(encoding="utf-8")
    g_lines = [line for line in content.splitlines() if line.startswith("g ")]
    assert len(g_lines) == 2, f"expected 2 'g' group lines, found {g_lines}"
    group_names = {line.split()[1] for line in g_lines}
    assert "wall" in group_names
    assert "window" in group_names


# ---------------------------------------------------------------------------
# Negative tests
# ---------------------------------------------------------------------------


def test_evaluate_invalid_seed_raises() -> None:
    """evaluate(ir, 'not-an-int') must raise TypeError (from SeededRng)."""
    ir = _simple_terminal_ir()
    with pytest.raises(TypeError):
        evaluate(ir, "not-an-int")  # type: ignore[arg-type]


def test_evaluate_empty_grammar_returns_empty_list() -> None:
    """evaluate on an IR with no rules returns [] without raising."""
    ir = ShapeGrammarIR(source_file="__test__", max_depth=5, seed=42, axiom="A", rules=[])
    result = evaluate(ir, 42)
    assert result == [], f"expected [], got {result}"
