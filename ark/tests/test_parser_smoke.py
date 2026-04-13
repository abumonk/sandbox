"""Smoke tests that parse real .ark spec files on disk. These pin the
contract against committed specs so unexpected regressions in either
parser or specs surface immediately.
"""

import pytest


def test_parses_test_minimal(parse_file, ark_root):
    ast = parse_file(ark_root / "specs" / "test_minimal.ark")
    assert len(ast["items"]) >= 1
    kinds = {i["kind"] for i in ast["items"]}
    # test_minimal.ark covers several kinds — at least an abstraction+class
    assert "abstraction" in kinds or "class" in kinds


def test_parses_backlog_spec(parse_file, ark_root):
    ast = parse_file(ark_root / "specs" / "meta" / "backlog.ark")
    # backlog.ark grows every tick as tasks complete — pin the lower bound
    # and the required shape instead of an exact count. Import resolution
    # prepends stdlib types (primitive/struct/enum); filter those out.
    local_kinds = ("abstraction", "class", "instance", "island",
                   "bridge", "registry", "verify")
    local = [i for i in ast["items"] if i["kind"] in local_kinds]
    assert len(local) >= 22, f"expected >= 22 local items, got {len(local)}"
    # Required shape: the living instance + its island + verify block.
    names = {i.get("name") for i in local}
    assert "Backlog" in names
    assert "ArkBacklog" in names
    assert any(i["kind"] == "instance" and i.get("name") == "ArkBacklog"
               for i in local)


def test_parses_rust_port_spec(parse_file, ark_root):
    ast = parse_file(ark_root / "specs" / "pipeline" / "rust_port.ark")
    assert len(ast["items"]) >= 10
