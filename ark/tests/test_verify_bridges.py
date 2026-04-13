"""Tests for bridge contract verification (BridgeContractTask).

Focus: type-matching between @out source field and @in destination field,
including inheritance chain walking.
"""

import json

from ark_verify import verify_bridges


def _items(parse_src, source: str) -> list:
    return parse_src(source)["items"]


def test_bridge_matching_types_passes(parse_src):
    src = """
    abstraction Producer {
      @out[]{ msg: String }
    }
    abstraction Consumer {
      @in{ msg: String }
    }
    bridge Link {
      from: Producer.msg
      to:   Consumer.msg
    }
    """
    results = verify_bridges(_items(parse_src, src))
    assert len(results) == 1
    r = results[0]
    assert r["status"] == "PASS"
    assert r["check"] == "bridge_Link_type_match"


def test_bridge_mismatched_types_fails(parse_src):
    src = """
    abstraction Producer {
      @out[]{ msg: Int }
    }
    abstraction Consumer {
      @in{ msg: String }
    }
    bridge Link {
      from: Producer.msg
      to:   Consumer.msg
    }
    """
    results = verify_bridges(_items(parse_src, src))
    assert results[0]["status"] == "FAIL"
    assert "Int" in results[0]["detail"]
    assert "String" in results[0]["detail"]


def test_bridge_walks_inheritance_for_ports(parse_src):
    """CodeSubagent-style case: child re-declares @out but inherits @in.
    The bridge must still resolve through the parent's @in.
    """
    src = """
    abstraction Base {
      @in{ assignment: String }
    }
    class Child : Base {
      @out[]{ result: String }
    }
    abstraction Src {
      @out[]{ payload: String }
    }
    bridge Dispatch {
      from: Src.payload
      to:   Child.assignment
    }
    """
    results = verify_bridges(_items(parse_src, src))
    assert results[0]["status"] == "PASS", results[0]


def test_bridge_unresolved_endpoint_is_unknown(parse_src):
    """If an endpoint entity or field is missing, we don't FAIL (the file
    may be a partial spec) — we mark UNKNOWN with a diagnostic.
    """
    src = """
    abstraction Producer {
      @out[]{ msg: String }
    }
    bridge Link {
      from: Producer.msg
      to:   Ghost.inbox
    }
    """
    results = verify_bridges(_items(parse_src, src))
    assert results[0]["status"] == "UNKNOWN"
    assert "Ghost" in results[0]["detail"]


def test_bridge_resolves_island_ports(parse_src):
    """Islands carry their own @in/@out and must be indexed like entities."""
    src = """
    abstraction Sink {
      @in{ tick: Float }
    }
    island Phys {
      strategy: tensor
      @out[]{ tick: Float }
    }
    bridge Feed {
      from: Phys.tick
      to:   Sink.tick
    }
    """
    results = verify_bridges(_items(parse_src, src))
    assert results[0]["status"] == "PASS"
