"""
Unit tests for translate_expr extensions: pipe and param_ref AST nodes.
"""

import pytest
from z3 import Real, Int, Solver, sat, unsat, IntVal, RealVal, is_int_value, simplify

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.verify.ark_verify import (
    translate_expr, translate_pipe, translate_param_ref, apply_stage,
    inline_expression, apply_opaque, build_expr_registry,
    SymbolTable, NATIVE_PRIMITIVES, OPAQUE_PRIMITIVES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def num(v):
    return {"expr": "number", "value": v}


def syms_with(names):
    """Build a SymbolTable with the given names as Real vars."""
    s = SymbolTable()
    for n in names:
        s.add_real(n)
    return s


def z3_equal(a, b) -> bool:
    """Check if two Z3 expressions are provably equal."""
    s = Solver()
    s.add(a != b)
    return s.check() == unsat


# ---------------------------------------------------------------------------
# 1. Simple numeric pipe: head=5, stages=[add(3)] → 8
# ---------------------------------------------------------------------------

def test_pipe_simple_add():
    expr = {
        "expr": "pipe",
        "head": num(5),
        "stages": [
            {"name": "add", "args": [num(3)]}
        ],
    }
    syms = SymbolTable()
    result = translate_expr(expr, syms)
    # 5 + 3 = 8
    assert z3_equal(result, IntVal(8))


# ---------------------------------------------------------------------------
# 2. Multi-stage pipe: head=10, sub(3), mul(2) → 14
# ---------------------------------------------------------------------------

def test_pipe_multi_stage():
    expr = {
        "expr": "pipe",
        "head": num(10),
        "stages": [
            {"name": "sub", "args": [num(3)]},
            {"name": "mul", "args": [num(2)]},
        ],
    }
    syms = SymbolTable()
    result = translate_expr(expr, syms)
    # (10 - 3) * 2 = 14
    assert z3_equal(result, IntVal(14))


# ---------------------------------------------------------------------------
# 3. Abs pipe: head=-5 → 5
# ---------------------------------------------------------------------------

def test_pipe_abs():
    expr = {
        "expr": "pipe",
        "head": num(-5),
        "stages": [{"name": "abs", "args": []}],
    }
    syms = SymbolTable()
    result = translate_expr(expr, syms)
    assert z3_equal(result, IntVal(5))


# ---------------------------------------------------------------------------
# 4. Neg pipe: head=3 → -3
# ---------------------------------------------------------------------------

def test_pipe_neg():
    expr = {
        "expr": "pipe",
        "head": num(3),
        "stages": [{"name": "neg", "args": []}],
    }
    syms = SymbolTable()
    result = translate_expr(expr, syms)
    assert z3_equal(result, IntVal(-3))


# ---------------------------------------------------------------------------
# 5. Clamp-range: head=15, clamp-range(0, 10) → 10
# ---------------------------------------------------------------------------

def test_pipe_clamp_range():
    expr = {
        "expr": "pipe",
        "head": num(15),
        "stages": [{"name": "clamp-range", "args": [num(0), num(10)]}],
    }
    syms = SymbolTable()
    result = translate_expr(expr, syms)
    assert z3_equal(result, IntVal(10))


# ---------------------------------------------------------------------------
# 6. ParamRef var
# ---------------------------------------------------------------------------

def test_param_ref_var():
    syms = syms_with(["x"])
    expr = {"expr": "param_ref", "ref_kind": "var", "name": "x"}
    result = translate_expr(expr, syms)
    # Should resolve to the same Z3 var as syms.get("x")
    assert z3_equal(result, syms.get("x"))


# ---------------------------------------------------------------------------
# 7. ParamRef prop
# ---------------------------------------------------------------------------

def test_param_ref_prop():
    syms = SymbolTable()
    syms.add_real("a.b")
    expr = {"expr": "param_ref", "ref_kind": "prop", "parts": ["a", "b"]}
    result = translate_expr(expr, syms)
    assert z3_equal(result, syms.get("a.b"))


# ---------------------------------------------------------------------------
# 8. ParamRef idx
# ---------------------------------------------------------------------------

def test_param_ref_idx():
    from z3 import is_expr
    syms = SymbolTable()
    expr = {"expr": "param_ref", "ref_kind": "idx", "name": "items", "index": 2}
    result = translate_expr(expr, syms)
    # Should be a Z3 expression (Select application)
    assert is_expr(result)


# ---------------------------------------------------------------------------
# 9. ParamRef nested
# ---------------------------------------------------------------------------

def test_param_ref_nested():
    syms = SymbolTable()
    expr = {
        "expr": "param_ref",
        "ref_kind": "nested",
        "inner": num(42),
    }
    result = translate_expr(expr, syms)
    assert z3_equal(result, IntVal(42))


# ---------------------------------------------------------------------------
# 10. Opaque stage: str-lower produces a Z3 expression (no crash)
# ---------------------------------------------------------------------------

def test_pipe_opaque_stage():
    from z3 import is_expr, StringVal
    syms = SymbolTable()
    syms.vars["s"] = __import__("z3").String("s")
    expr = {
        "expr": "pipe",
        "head": {"expr": "ident", "name": "s"},
        "stages": [{"name": "str-lower", "args": []}],
    }
    result = translate_expr(expr, syms)
    assert is_expr(result)


# ---------------------------------------------------------------------------
# 11. Unknown stage raises ValueError with helpful message
# ---------------------------------------------------------------------------

def test_pipe_unknown_stage_raises():
    syms = SymbolTable()
    expr = {
        "expr": "pipe",
        "head": num(1),
        "stages": [{"name": "totally-unknown-stage", "args": []}],
    }
    with pytest.raises(ValueError, match="Unknown pipe stage"):
        translate_expr(expr, syms)


# ---------------------------------------------------------------------------
# 12. User-defined expression inlining via expr_registry
# ---------------------------------------------------------------------------

def test_pipe_user_defined_expression():
    """Register a simple doubling expression, pipe through it."""
    # Expression: double(x) = x * 2
    expr_def = {
        "item": "expression",
        "name": "double",
        "inputs": [{"name": "x"}],
        "chain": {
            "expr": "binop",
            "op": "*",
            "left": {"expr": "ident", "name": "x"},
            "right": num(2),
        },
    }
    registry = build_expr_registry([expr_def])
    syms = SymbolTable()
    expr = {
        "expr": "pipe",
        "head": num(7),
        "stages": [{"name": "double", "args": []}],
    }
    result = translate_expr(expr, syms, expr_registry=registry)
    # 7 * 2 = 14
    assert z3_equal(result, IntVal(14))


# ---------------------------------------------------------------------------
# 13. Recursive expression detection raises ValueError
# ---------------------------------------------------------------------------

def test_recursive_expression_raises():
    # Expression referencing itself
    expr_def = {
        "item": "expression",
        "name": "recurse",
        "inputs": [{"name": "x"}],
        "chain": {
            "expr": "pipe",
            "head": {"expr": "ident", "name": "x"},
            "stages": [{"name": "recurse", "args": []}],
        },
    }
    registry = build_expr_registry([expr_def])
    syms = SymbolTable()
    expr = {
        "expr": "pipe",
        "head": num(1),
        "stages": [{"name": "recurse", "args": []}],
    }
    with pytest.raises(ValueError, match="Recursive expression"):
        translate_expr(expr, syms, expr_registry=registry)


# ---------------------------------------------------------------------------
# 14. build_expr_registry filters non-expression items
# ---------------------------------------------------------------------------

def test_build_expr_registry():
    items = [
        {"item": "expression", "name": "foo"},
        {"item": "class", "name": "Bar"},
        {"item": "expression", "name": "baz"},
    ]
    registry = build_expr_registry(items)
    assert set(registry.keys()) == {"foo", "baz"}


# ---------------------------------------------------------------------------
# 15. Pipe with no stages returns head value
# ---------------------------------------------------------------------------

def test_pipe_no_stages():
    syms = SymbolTable()
    expr = {
        "expr": "pipe",
        "head": num(99),
        "stages": [],
    }
    result = translate_expr(expr, syms)
    assert z3_equal(result, IntVal(99))
