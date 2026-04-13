"""
Unit tests for predicate verification:
  - build_pred_registry
  - translate_expr / translate_pipe used in predicate-style check expressions
  - Satisfiability, tautology, pipe stages, opaque stages
"""

import pytest
from z3 import (
    Real, Int, Bool, Solver, sat, unsat, IntVal, RealVal, simplify, is_true, Not,
)
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.verify.ark_verify import (
    translate_expr, translate_pipe, build_pred_registry,
    SymbolTable, NATIVE_PRIMITIVES, OPAQUE_PRIMITIVES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def num(v):
    return {"expr": "number", "value": v}


def z3_equal(a, b) -> bool:
    """Check if two Z3 expressions are provably equal."""
    s = Solver()
    s.add(a != b)
    return s.check() == unsat


def z3_satisfiable(formula) -> bool:
    """Return True if the formula has at least one model."""
    s = Solver()
    s.add(formula)
    return s.check() == sat


def z3_tautology(formula) -> bool:
    """Return True if the formula is valid (true in all models)."""
    s = Solver()
    s.add(Not(formula))
    return s.check() == unsat


# ---------------------------------------------------------------------------
# 1. test_predicate_check_satisfiable
#    A predicate `check: x > 0` should produce a satisfiable Z3 formula.
# ---------------------------------------------------------------------------

def test_predicate_check_satisfiable():
    syms = SymbolTable()
    x = syms.add_real("x")
    expr = {
        "expr": "binop",
        "op": ">",
        "left": {"expr": "ident", "name": "x"},
        "right": num(0),
    }
    formula = translate_expr(expr, syms)
    assert z3_satisfiable(formula), "x > 0 must be satisfiable (x=1 is a model)"


# ---------------------------------------------------------------------------
# 2. test_predicate_check_tautology
#    A predicate `check: x == x` (always true) should be a tautology.
# ---------------------------------------------------------------------------

def test_predicate_check_tautology():
    syms = SymbolTable()
    syms.add_real("x")
    expr = {
        "expr": "binop",
        "op": "==",
        "left": {"expr": "ident", "name": "x"},
        "right": {"expr": "ident", "name": "x"},
    }
    formula = translate_expr(expr, syms)
    assert z3_tautology(formula), "x == x must be a tautology"


# ---------------------------------------------------------------------------
# 3. test_predicate_with_pipe_stage
#    A predicate using a pipe stage `x |> abs` followed by `> 0` translates
#    correctly: for x = -5, abs(x) > 0 is true.
# ---------------------------------------------------------------------------

def test_predicate_with_pipe_stage():
    syms = SymbolTable()
    syms.add_int("x")

    # Pipe: -5 |> abs  →  5
    pipe_expr = {
        "expr": "pipe",
        "head": num(-5),
        "stages": [{"name": "abs", "args": []}],
    }
    abs_val = translate_expr(pipe_expr, syms)

    # Check abs_val > 0
    check_formula = abs_val > 0
    assert z3_tautology(check_formula), "abs(-5) > 0 must be a tautology"

    # Also check that the abs pipe of a symbolic variable yields satisfiable > 0
    pipe_sym = {
        "expr": "pipe",
        "head": {"expr": "ident", "name": "x"},
        "stages": [{"name": "abs", "args": []}],
    }
    abs_sym = translate_expr(pipe_sym, syms)
    sat_formula = abs_sym > 0
    assert z3_satisfiable(sat_formula), "abs(x) > 0 must be satisfiable"


# ---------------------------------------------------------------------------
# 4. test_predicate_with_opaque_stage
#    A predicate using an opaque stage (str-is-empty on a string) should
#    produce a Z3 expression without crashing.
# ---------------------------------------------------------------------------

def test_predicate_with_opaque_stage():
    from z3 import is_expr, String

    syms = SymbolTable()
    syms.add_string("s")

    # Use str-lower (an opaque primitive) — result should be a Z3 expr
    pipe_expr = {
        "expr": "pipe",
        "head": {"expr": "ident", "name": "s"},
        "stages": [{"name": "str-lower", "args": []}],
    }
    result = translate_expr(pipe_expr, syms)
    assert is_expr(result), "Opaque str-lower stage must produce a Z3 expression"

    # The result should be satisfiable (we just need no crash, not a proof)
    s = Solver()
    # We can't easily assert equality but we verify it is a valid Z3 term
    assert result is not None


# ---------------------------------------------------------------------------
# 5. test_predicate_registry_lookup
#    Build a pred registry, verify entries are found by name.
# ---------------------------------------------------------------------------

def test_predicate_registry_lookup():
    items = [
        {
            "item": "predicate",
            "name": "is_positive",
            "check": {
                "expr": "binop",
                "op": ">",
                "left": {"expr": "ident", "name": "x"},
                "right": num(0),
            },
        },
        {
            "item": "predicate",
            "name": "is_nonneg",
            "check": {
                "expr": "binop",
                "op": ">=",
                "left": {"expr": "ident", "name": "x"},
                "right": num(0),
            },
        },
        # Non-predicate item — should be filtered out
        {"item": "class", "name": "Vehicle"},
    ]

    registry = build_pred_registry(items)

    assert "is_positive" in registry, "is_positive must be in registry"
    assert "is_nonneg" in registry, "is_nonneg must be in registry"
    assert "Vehicle" not in registry, "class items must not appear in pred registry"
    assert len(registry) == 2, "Registry must contain exactly 2 predicate entries"

    # Verify we can actually use the retrieved predicate's check expression
    syms = SymbolTable()
    syms.add_real("x")
    check_expr = registry["is_positive"]["check"]
    formula = translate_expr(check_expr, syms)
    assert z3_satisfiable(formula), "is_positive check must be satisfiable"


# ---------------------------------------------------------------------------
# 6. test_predicate_not_satisfiable
#    A contradictory predicate `x > 0 and x < 0` should not be satisfiable.
# ---------------------------------------------------------------------------

def test_predicate_not_satisfiable():
    syms = SymbolTable()
    syms.add_real("x")
    expr = {
        "expr": "binop",
        "op": "and",
        "left": {
            "expr": "binop",
            "op": ">",
            "left": {"expr": "ident", "name": "x"},
            "right": num(0),
        },
        "right": {
            "expr": "binop",
            "op": "<",
            "left": {"expr": "ident", "name": "x"},
            "right": num(0),
        },
    }
    formula = translate_expr(expr, syms)
    assert not z3_satisfiable(formula), "x > 0 and x < 0 must be unsatisfiable"


# ---------------------------------------------------------------------------
# 7. test_predicate_registry_empty_on_no_predicates
#    build_pred_registry returns empty dict when no predicate items exist.
# ---------------------------------------------------------------------------

def test_predicate_registry_empty_on_no_predicates():
    items = [
        {"item": "class", "name": "Foo"},
        {"item": "expression", "name": "bar"},
    ]
    registry = build_pred_registry(items)
    assert registry == {}, "Registry must be empty when no predicate items are present"
