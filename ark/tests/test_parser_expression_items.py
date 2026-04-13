"""Tests for expression_def and predicate_def parsing.

Covers:
- TC-001: expression item parses correctly (in/out/chain fields present)
- TC-002: predicate item parses correctly (in/check fields present)
- TC-007: all fields (name, inputs, output, chain / check) populated
- TC-008: missing chain clause produces parse error
          missing out clause on expression produces parse error
          malformed predicate produces parse error
- TC-025: kebab-case names in def_ident parse correctly
          multiple expressions populate expression_index correctly
          multiple predicates populate predicate_index correctly
"""

import sys
from pathlib import Path

import pytest

_ARK_ROOT = Path(__file__).resolve().parent.parent
_PARSER_DIR = _ARK_ROOT / "tools" / "parser"
if str(_PARSER_DIR) not in sys.path:
    sys.path.insert(0, str(_PARSER_DIR))

from ark_parser import parse, ArkParseError  # noqa: E402


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------

def _parse(source: str) -> dict:
    """Parse source string and return the JSON-round-tripped AST dict."""
    import json
    from ark_parser import to_json
    ark_file = parse(source)
    return json.loads(to_json(ark_file))


# ---------------------------------------------------------------
# TC-001: expression item parses
# ---------------------------------------------------------------

def test_expression_item_parses(parse_src):
    """An expression def produces an item with kind == 'expression'."""
    src = """
expression numeric_abs {
  in: x: Float
  out: Float
  chain: x |> abs
}
"""
    ast = parse_src(src)
    items = ast["items"]
    assert len(items) == 1
    item = items[0]
    assert item["kind"] == "expression"


# ---------------------------------------------------------------
# TC-002: predicate item parses
# ---------------------------------------------------------------

def test_predicate_item_parses(parse_src):
    """A predicate def produces an item with kind == 'predicate'."""
    src = """
predicate is_positive {
  in: x: Float
  check: x > 0
}
"""
    ast = parse_src(src)
    items = ast["items"]
    assert len(items) == 1
    item = items[0]
    assert item["kind"] == "predicate"


# ---------------------------------------------------------------
# TC-007: expression — all fields populated
# ---------------------------------------------------------------

def test_expression_all_fields_populated(parse_src):
    """Expression AST node has name, inputs, output, and chain fields."""
    src = """
expression numeric_add {
  in: x: Float, y: Float
  out: Float
  chain: x |> add(y)
}
"""
    ast = parse_src(src)
    item = ast["items"][0]
    assert item["kind"] == "expression"
    assert item["name"] == "numeric_add"

    # inputs is a list of typed fields
    assert isinstance(item["inputs"], list)
    assert len(item["inputs"]) == 2
    assert item["inputs"][0]["name"] == "x"
    assert item["inputs"][0]["type"]["name"] == "Float"
    assert item["inputs"][1]["name"] == "y"
    assert item["inputs"][1]["type"]["name"] == "Float"

    # output is a type expression
    assert item["output"]["name"] == "Float"

    # chain is a pipe expression
    chain = item["chain"]
    assert chain["expr"] == "pipe"
    assert chain["head"] == {"expr": "ident", "name": "x"}
    assert len(chain["stages"]) == 1
    assert chain["stages"][0]["name"] == "add"


# ---------------------------------------------------------------
# TC-007: predicate — all fields populated
# ---------------------------------------------------------------

def test_predicate_all_fields_populated(parse_src):
    """Predicate AST node has name, inputs, and check fields."""
    src = """
predicate is_within_range {
  in: x: Float, lo: Float, hi: Float
  check: x >= lo and x < hi
}
"""
    ast = parse_src(src)
    item = ast["items"][0]
    assert item["kind"] == "predicate"
    assert item["name"] == "is_within_range"

    # inputs
    assert isinstance(item["inputs"], list)
    assert len(item["inputs"]) == 3
    assert item["inputs"][0]["name"] == "x"
    assert item["inputs"][1]["name"] == "lo"
    assert item["inputs"][2]["name"] == "hi"

    # check is an expression
    check = item["check"]
    assert check["expr"] == "binop"
    assert check["op"] == "and"


# ---------------------------------------------------------------
# TC-008: missing chain clause produces parse error
# ---------------------------------------------------------------

def test_missing_chain_clause_errors():
    """An expression body without 'chain:' is a syntax error."""
    src = """
expression broken_expr {
  in: x: Float
  out: Float
}
"""
    with pytest.raises(ArkParseError) as excinfo:
        parse(src)
    err = excinfo.value
    assert err.line >= 1
    assert err.column >= 1


# ---------------------------------------------------------------
# TC-008: missing out clause produces parse error
# ---------------------------------------------------------------

def test_missing_out_clause_errors():
    """An expression body without 'out:' is a syntax error."""
    src = """
expression bad_expr {
  in: x: Float
  chain: x |> abs
}
"""
    with pytest.raises(ArkParseError) as excinfo:
        parse(src)
    err = excinfo.value
    report = err.format_report()
    assert "error:" in report


# ---------------------------------------------------------------
# TC-008: malformed predicate produces parse error
# ---------------------------------------------------------------

def test_malformed_predicate_errors():
    """A predicate body without 'check:' is a syntax error."""
    src = """
predicate bad_pred {
  in: x: Float
}
"""
    with pytest.raises(ArkParseError) as excinfo:
        parse(src)
    err = excinfo.value
    assert err.line >= 1


# ---------------------------------------------------------------
# TC-025: kebab-case name in def_ident parses
# ---------------------------------------------------------------

def test_kebab_case_name_in_expression(parse_src):
    """Expression names with hyphens (def_ident) parse correctly."""
    src = """
expression text-to-lower {
  in: s: String
  out: String
  chain: s |> str-lower
}
"""
    ast = parse_src(src)
    item = ast["items"][0]
    assert item["kind"] == "expression"
    assert item["name"] == "text-to-lower"


def test_kebab_case_name_in_predicate(parse_src):
    """Predicate names with hyphens (def_ident) parse correctly."""
    src = """
predicate is-empty {
  in: s: String
  check: s |> str-is-empty
}
"""
    ast = parse_src(src)
    item = ast["items"][0]
    assert item["kind"] == "predicate"
    assert item["name"] == "is-empty"


# ---------------------------------------------------------------
# expression_index and predicate_index populated correctly
# ---------------------------------------------------------------

def test_multiple_expressions_populate_index(parse_src):
    """Multiple expression defs all appear in expression_index."""
    src = """
expression expr_a {
  in: x: Float
  out: Float
  chain: x |> abs
}

expression expr_b {
  in: x: Float
  out: Float
  chain: x |> neg
}
"""
    ast = parse_src(src)
    idx = ast["expression_index"]
    assert "expr_a" in idx
    assert "expr_b" in idx
    # Indices are distinct integer positions into items
    assert idx["expr_a"] != idx["expr_b"]


def test_multiple_predicates_populate_index(parse_src):
    """Multiple predicate defs all appear in predicate_index."""
    src = """
predicate pred_a {
  in: x: Float
  check: x > 0
}

predicate pred_b {
  in: x: Float
  check: x < 0
}
"""
    ast = parse_src(src)
    idx = ast["predicate_index"]
    assert "pred_a" in idx
    assert "pred_b" in idx
    assert idx["pred_a"] != idx["pred_b"]
