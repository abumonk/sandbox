"""Tests for ARK stdlib expression and predicate files.

Verifies that:
- dsl/stdlib/expression.ark parses cleanly with 23 expression items
- dsl/stdlib/predicate.ark parses cleanly with 10 predicate items
- Structural invariants hold (chain, check, unique names, primitives mapping)
- No Rust identifier collisions when names are mangled to snake_case
"""

import sys
from pathlib import Path

import pytest

_ARK_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ARK_ROOT / "tools" / "codegen"))
from expression_primitives import EXPR_PRIMITIVES  # noqa: E402

_EXPRESSION_FILE = _ARK_ROOT / "dsl" / "stdlib" / "expression.ark"
_PREDICATE_FILE = _ARK_ROOT / "dsl" / "stdlib" / "predicate.ark"

EXPECTED_EXPRESSION_COUNT = 23
EXPECTED_PREDICATE_COUNT = 10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stage_names(chain: dict) -> list:
    """Extract pipe stage primitive names from a chain AST node."""
    if chain and chain.get("expr") == "pipe":
        return [s["name"] for s in chain.get("stages", [])]
    return []


def _expressions(ast: dict) -> list:
    return [item for item in ast["items"] if item["kind"] == "expression"]


def _predicates(ast: dict) -> list:
    return [item for item in ast["items"] if item["kind"] == "predicate"]


# ---------------------------------------------------------------------------
# Fixtures — parse stdlib files once per session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def expression_ast(ark_root):
    """Parsed AST of dsl/stdlib/expression.ark."""
    import json
    import sys as _sys
    _parser_dir = str(ark_root / "tools" / "parser")
    if _parser_dir not in _sys.path:
        _sys.path.insert(0, _parser_dir)
    from ark_parser import parse as _parse, to_json as _to_json
    source = _EXPRESSION_FILE.read_text(encoding="utf-8")
    ark_file = _parse(source, file_path=_EXPRESSION_FILE)
    return json.loads(_to_json(ark_file))


@pytest.fixture(scope="session")
def predicate_ast(ark_root):
    """Parsed AST of dsl/stdlib/predicate.ark."""
    import json
    import sys as _sys
    _parser_dir = str(ark_root / "tools" / "parser")
    if _parser_dir not in _sys.path:
        _sys.path.insert(0, _parser_dir)
    from ark_parser import parse as _parse, to_json as _to_json
    source = _PREDICATE_FILE.read_text(encoding="utf-8")
    ark_file = _parse(source, file_path=_PREDICATE_FILE)
    return json.loads(_to_json(ark_file))


# ---------------------------------------------------------------------------
# 1. test_stdlib_expression_parses
# ---------------------------------------------------------------------------

def test_stdlib_expression_parses(parse_file):
    """expression.ark parses with no errors and produces 23 expression items."""
    ast = parse_file(_EXPRESSION_FILE)
    errors = ast.get("errors", [])
    assert errors == [], f"Parse errors: {errors}"
    exprs = _expressions(ast)
    assert len(exprs) == EXPECTED_EXPRESSION_COUNT, (
        f"Expected {EXPECTED_EXPRESSION_COUNT} expressions, got {len(exprs)}: "
        f"{[e['name'] for e in exprs]}"
    )


# ---------------------------------------------------------------------------
# 2. test_stdlib_predicate_parses
# ---------------------------------------------------------------------------

def test_stdlib_predicate_parses(parse_file):
    """predicate.ark parses with no errors and produces 10 predicate items."""
    ast = parse_file(_PREDICATE_FILE)
    errors = ast.get("errors", [])
    assert errors == [], f"Parse errors: {errors}"
    preds = _predicates(ast)
    assert len(preds) == EXPECTED_PREDICATE_COUNT, (
        f"Expected {EXPECTED_PREDICATE_COUNT} predicates, got {len(preds)}: "
        f"{[p['name'] for p in preds]}"
    )


# ---------------------------------------------------------------------------
# 3. test_expression_has_chain
# ---------------------------------------------------------------------------

def test_expression_has_chain(expression_ast):
    """Every expression item has a non-null chain field."""
    exprs = _expressions(expression_ast)
    for expr in exprs:
        assert expr.get("chain") is not None, (
            f"Expression '{expr['name']}' has null chain"
        )


# ---------------------------------------------------------------------------
# 4. test_predicate_has_check
# ---------------------------------------------------------------------------

def test_predicate_has_check(predicate_ast):
    """Every predicate item has a non-null check field."""
    preds = _predicates(predicate_ast)
    for pred in preds:
        assert pred.get("check") is not None, (
            f"Predicate '{pred['name']}' has null check"
        )


# ---------------------------------------------------------------------------
# 5. test_expression_names_unique
# ---------------------------------------------------------------------------

def test_expression_names_unique(expression_ast):
    """All expression names are unique."""
    names = [e["name"] for e in _expressions(expression_ast)]
    assert len(names) == len(set(names)), (
        f"Duplicate expression names found: "
        f"{[n for n in names if names.count(n) > 1]}"
    )


# ---------------------------------------------------------------------------
# 6. test_predicate_names_unique
# ---------------------------------------------------------------------------

def test_predicate_names_unique(predicate_ast):
    """All predicate names are unique."""
    names = [p["name"] for p in _predicates(predicate_ast)]
    assert len(names) == len(set(names)), (
        f"Duplicate predicate names found: "
        f"{[n for n in names if names.count(n) > 1]}"
    )


# ---------------------------------------------------------------------------
# 7. test_every_expression_has_primitives_entry
# ---------------------------------------------------------------------------

def test_every_expression_has_primitives_entry(expression_ast):
    """Every pipe stage in each expression chain maps to a known EXPR_PRIMITIVES entry."""
    exprs = _expressions(expression_ast)
    missing = []
    for expr in exprs:
        chain = expr.get("chain")
        for stage_name in _stage_names(chain):
            if stage_name not in EXPR_PRIMITIVES:
                missing.append((expr["name"], stage_name))
    assert missing == [], (
        f"Primitive(s) not in EXPR_PRIMITIVES: {missing}"
    )


# ---------------------------------------------------------------------------
# 8. test_no_rust_name_collision
# ---------------------------------------------------------------------------

def test_no_rust_name_collision(expression_ast, predicate_ast):
    """Mangling all expression+predicate names to snake_case yields no duplicates."""
    expr_names = [e["name"] for e in _expressions(expression_ast)]
    pred_names = [p["name"] for p in _predicates(predicate_ast)]
    all_names = expr_names + pred_names
    mangled = [name.replace("-", "_") for name in all_names]
    assert len(mangled) == len(set(mangled)), (
        f"Rust snake_case name collision detected: "
        f"{[n for n in mangled if mangled.count(n) > 1]}"
    )


# ---------------------------------------------------------------------------
# 9. test_expression_index_populated
# ---------------------------------------------------------------------------

def test_expression_index_populated(expression_ast):
    """expression_index has all 23 entries."""
    idx = expression_ast.get("expression_index", {})
    assert len(idx) == EXPECTED_EXPRESSION_COUNT, (
        f"expression_index has {len(idx)} entries, expected {EXPECTED_EXPRESSION_COUNT}"
    )
    # All expression names must appear in the index
    expr_names = {e["name"] for e in _expressions(expression_ast)}
    assert expr_names == set(idx.keys()), (
        f"expression_index keys mismatch: "
        f"missing={expr_names - set(idx.keys())}, "
        f"extra={set(idx.keys()) - expr_names}"
    )


# ---------------------------------------------------------------------------
# 10. test_predicate_index_populated
# ---------------------------------------------------------------------------

def test_predicate_index_populated(predicate_ast):
    """predicate_index has all 10 entries."""
    idx = predicate_ast.get("predicate_index", {})
    assert len(idx) == EXPECTED_PREDICATE_COUNT, (
        f"predicate_index has {len(idx)} entries, expected {EXPECTED_PREDICATE_COUNT}"
    )
    pred_names = {p["name"] for p in _predicates(predicate_ast)}
    assert pred_names == set(idx.keys()), (
        f"predicate_index keys mismatch: "
        f"missing={pred_names - set(idx.keys())}, "
        f"extra={set(idx.keys()) - pred_names}"
    )


# ---------------------------------------------------------------------------
# 11. test_expression_inputs_have_types
# ---------------------------------------------------------------------------

def test_expression_inputs_have_types(expression_ast):
    """Every expression input field has a type dict with a 'type' or 'name' key."""
    exprs = _expressions(expression_ast)
    for expr in exprs:
        for inp in expr.get("inputs", []):
            type_info = inp.get("type")
            assert type_info is not None, (
                f"Expression '{expr['name']}' input '{inp.get('name')}' has no type"
            )
            assert isinstance(type_info, dict), (
                f"Expression '{expr['name']}' input '{inp.get('name')}' type is not a dict"
            )
            # The type dict must have at least one of 'type' or 'name' key
            assert "type" in type_info or "name" in type_info, (
                f"Expression '{expr['name']}' input '{inp.get('name')}' type dict "
                f"has neither 'type' nor 'name' key: {type_info}"
            )
