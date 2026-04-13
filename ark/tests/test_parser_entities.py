"""Unit tests for each top-level ARK entity kind.

Every test parses a small inline .ark snippet and asserts on the shape of
the resulting JSON AST dict. One test per entity kind — this pins the
public contract of the parser at the entity level.
"""

import pytest


# ---------------------------------------------------------------
# abstraction / class
# ---------------------------------------------------------------

def test_parses_abstraction(parse_src):
    ast = parse_src("abstraction Contract { }")
    assert len(ast["items"]) == 1
    item = ast["items"][0]
    assert item["kind"] == "abstraction"
    assert item["name"] == "Contract"
    assert item["inherits"] == []
    assert item["data_fields"] == []


def test_parses_class(parse_src):
    ast = parse_src("class Vehicle { $data speed: Float = 0 }")
    item = ast["items"][0]
    assert item["kind"] == "class"
    assert item["name"] == "Vehicle"
    assert len(item["data_fields"]) == 1
    f = item["data_fields"][0]
    assert f["name"] == "speed"
    assert f["type"]["name"] == "Float"
    assert f["default"] == {"expr": "number", "value": 0}


def test_parses_class_with_inherits(parse_src):
    ast = parse_src("class Truck : Vehicle { }")
    item = ast["items"][0]
    assert item["kind"] == "class"
    assert item["name"] == "Truck"
    assert "Vehicle" in item["inherits"]


# ---------------------------------------------------------------
# instance
# ---------------------------------------------------------------

def test_parses_instance(parse_src):
    ast = parse_src("instance v1 : Vehicle { speed = 10 }")
    item = ast["items"][0]
    assert item["kind"] == "instance"
    assert item["name"] == "v1"
    assert item["class_name"] == "Vehicle"
    assert len(item["assignments"]) == 1
    a = item["assignments"][0]
    # target is a dotted_path_or_ident → single-ident becomes {"expr":"ident"}
    assert a["target"]["expr"] == "ident"
    assert a["target"]["name"] == "speed"
    assert a["value"] == {"expr": "number", "value": 10}


# ---------------------------------------------------------------
# island
# ---------------------------------------------------------------

def test_parses_island(parse_src):
    src = """
    island World {
      strategy: code
      contains: [A, B]
    }
    """
    ast = parse_src(src)
    item = ast["items"][0]
    assert item["kind"] == "island"
    assert item["name"] == "World"
    assert item["strategy"] == "code"
    assert item["contains"] == ["A", "B"]


# ---------------------------------------------------------------
# bridge
# ---------------------------------------------------------------

def test_parses_bridge(parse_src):
    src = """
    bridge B {
      from: A.out
      to: C.in
    }
    """
    ast = parse_src(src)
    item = ast["items"][0]
    assert item["kind"] == "bridge"
    assert item["name"] == "B"
    assert item["from_port"] == "A.out"
    assert item["to_port"] == "C.in"
    assert item["contract"] is None


def test_parses_bridge_with_contract(parse_src):
    src = """
    bridge B {
      from: A.out
      to: C.in
      contract {
        invariant: x > 0
      }
    }
    """
    ast = parse_src(src)
    item = ast["items"][0]
    assert item["kind"] == "bridge"
    assert item["contract"] is not None
    assert len(item["contract"]["invariants"]) == 1
    inv = item["contract"]["invariants"][0]
    assert inv["expr"] == "binop"
    assert inv["op"] == ">"


# ---------------------------------------------------------------
# registry
# ---------------------------------------------------------------

def test_parses_registry(parse_src):
    src = """
    registry Reg {
      register X { phase: build, priority: 1 }
    }
    """
    ast = parse_src(src)
    item = ast["items"][0]
    assert item["kind"] == "registry"
    assert item["name"] == "Reg"
    assert len(item["entries"]) == 1
    entry = item["entries"][0]
    assert entry["name"] == "X"
    keys = {p["key"] for p in entry["meta"]}
    assert keys == {"phase", "priority"}


# ---------------------------------------------------------------
# verify
# ---------------------------------------------------------------

def test_parses_verify(parse_src):
    src = """
    verify T {
      check c1: x >= 0
    }
    """
    ast = parse_src(src)
    item = ast["items"][0]
    assert item["kind"] == "verify"
    assert item["target"] == "T"
    assert len(item["checks"]) == 1
    c = item["checks"][0]
    assert c["name"] == "c1"
    assert c["expr"]["expr"] == "binop"
    assert c["expr"]["op"] == ">="


# ---------------------------------------------------------------
# import
# ---------------------------------------------------------------

def test_parses_import(parse_src):
    src = "import stdlib.types\nclass C {}"
    ast = parse_src(src)
    assert len(ast["imports"]) == 1
    assert ast["imports"][0] == ["stdlib", "types"]
    # Entity still parses alongside the import
    assert any(i["kind"] == "class" and i["name"] == "C" for i in ast["items"])
