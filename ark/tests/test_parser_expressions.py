"""Unit tests for ARK expression parsing — precedence, chaining, calls,
literals, strings. All expressions are exercised inside a minimal class
or invariant, since expressions aren't top-level.
"""

import pytest


def _cls(parse_src, body: str) -> dict:
    return parse_src("class C { " + body + " }")["items"][0]


def _process_body(cls):
    assert len(cls["processes"]) == 1
    return cls["processes"][0]["body"]


# ---------------------------------------------------------------
# Arithmetic precedence / left-fold
# ---------------------------------------------------------------

def test_arithmetic_left_folds(parse_src):
    # `a + b * c + d` → ((a + (b*c)) + d)
    cls = _cls(parse_src, "#process[strategy: code]{ x = a + b * c + d }")
    body = _process_body(cls)
    assert len(body) == 1
    assign = body[0]
    assert assign["_stmt"] == "assignment"
    rhs = assign["value"]
    # Outermost binop is +
    assert rhs["expr"] == "binop"
    assert rhs["op"] == "+"
    # Right operand is the trailing `d`
    assert rhs["right"] == {"expr": "ident", "name": "d"}
    # Left operand is (a + (b*c)) — itself a + binop
    left = rhs["left"]
    assert left["expr"] == "binop"
    assert left["op"] == "+"
    assert left["left"] == {"expr": "ident", "name": "a"}
    # And the nested right is a * binop
    assert left["right"]["expr"] == "binop"
    assert left["right"]["op"] == "*"


# ---------------------------------------------------------------
# Comparison + boolean chaining
# ---------------------------------------------------------------

def test_comparison_chain(parse_src):
    cls = _cls(parse_src, "invariant: a <= b and b <= c")
    inv = cls["invariants"][0]
    # Outermost is `and`, with two <= children
    assert inv["expr"] == "binop"
    assert inv["op"] == "and"
    assert inv["left"]["op"] == "<="
    assert inv["right"]["op"] == "<="


# ---------------------------------------------------------------
# Dotted path function call
# ---------------------------------------------------------------

def test_path_call(parse_src):
    cls = _cls(parse_src, "#process[strategy: code]{ x = foo.bar(1, 2) }")
    body = _process_body(cls)
    rhs = body[0]["value"]
    assert rhs["expr"] == "call"
    assert rhs["name"] == "foo.bar"
    assert len(rhs["args"]) == 2
    assert rhs["args"][0] == {"expr": "number", "value": 1}
    assert rhs["args"][1] == {"expr": "number", "value": 2}


# ---------------------------------------------------------------
# Boolean literals
# ---------------------------------------------------------------

def test_boolean_literals(parse_src):
    cls_t = _cls(parse_src, "invariant: true")
    cls_f = _cls(parse_src, "invariant: false")
    assert cls_t["invariants"][0] == {"expr": "bool", "value": True}
    assert cls_f["invariants"][0] == {"expr": "bool", "value": False}


# ---------------------------------------------------------------
# String literal
# ---------------------------------------------------------------

def test_string_literal(parse_src):
    cls = _cls(parse_src, 'description: "hello"')
    # description_stmt is collected into entity.description
    assert cls["description"] is not None
    assert "hello" in cls["description"]
