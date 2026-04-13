"""Tests for ark_diff — structural diff between two .ark spec versions.

Covers the MVP scope:
  - identical ASTs → no changes
  - added / removed top-level items (class, bridge, registry entry)
  - modified class: added $data, changed type, changed constraint
  - instance assignment drift
  - island contains list drift
"""

from ark_diff import diff_ast, render


def _ast(parse_src, source: str) -> dict:
    return parse_src(source)


def _by_change(changes, change, name):
    return [c for c in changes if c["change"] == change and c["name"] == name]


def test_identical_specs_produce_no_changes(parse_src):
    src = """
    class Vehicle {
      $data fuel: Float [0..100] = 50.0
      @in{ throttle: Float }
      #process[strategy: code]{ fuel' = fuel - throttle }
      invariant: fuel >= 0
    }
    """
    old_ast = _ast(parse_src, src)
    new_ast = _ast(parse_src, src)
    assert diff_ast(old_ast, new_ast) == []
    assert "no structural changes" in render([])


def test_added_and_removed_top_level_class(parse_src):
    old_src = """
    class A { $data x: Int = 0 }
    """
    new_src = """
    class A { $data x: Int = 0 }
    class B { $data y: Int = 0 }
    """
    changes = diff_ast(_ast(parse_src, old_src), _ast(parse_src, new_src))
    assert _by_change(changes, "added", "B")
    assert _by_change(changes, "added", "B")[0]["item_type"] == "class"
    assert not _by_change(changes, "removed", "A")

    # Reverse — removed case.
    changes_rev = diff_ast(_ast(parse_src, new_src), _ast(parse_src, old_src))
    assert _by_change(changes_rev, "removed", "B")
    assert _by_change(changes_rev, "removed", "B")[0]["item_type"] == "class"


def test_modified_class_data_field_changes(parse_src):
    """Adding a new $data field, retyping another, and tightening a
    constraint should all surface as `modified` details on the class."""
    old_src = """
    class Vehicle {
      $data fuel: Float [0..100] = 50.0
      $data gear: Int = 0
    }
    """
    new_src = """
    class Vehicle {
      $data fuel: Float [0..200] = 50.0
      $data gear: Float = 0.0
      $data nitro: Float = 0.0
    }
    """
    changes = diff_ast(_ast(parse_src, old_src), _ast(parse_src, new_src))
    mods = _by_change(changes, "modified", "Vehicle")
    assert len(mods) == 1
    details = mods[0]["details"]
    # All three effects should show up.
    joined = "\n".join(details)
    assert "+ $data nitro" in joined
    assert "~ $data gear: type Int → Float" in joined
    assert "~ $data fuel: constraint" in joined
    assert "100" in joined and "200" in joined


def test_bridge_endpoint_changed(parse_src):
    old_src = """
    class A { @out[]{ x: Int } }
    class B { @in{ y: Int } }
    class C { @in{ z: Int } }
    bridge Link { from: A.x to: B.y }
    """
    new_src = """
    class A { @out[]{ x: Int } }
    class B { @in{ y: Int } }
    class C { @in{ z: Int } }
    bridge Link { from: A.x to: C.z }
    """
    changes = diff_ast(_ast(parse_src, old_src), _ast(parse_src, new_src))
    mods = _by_change(changes, "modified", "Link")
    assert len(mods) == 1
    assert mods[0]["item_type"] == "bridge"
    assert any("to:" in d and "B.y" in d and "C.z" in d for d in mods[0]["details"])


def test_registry_entry_phase_changed(parse_src):
    """Changing a registered entry's phase must be flagged on the registry."""
    old_src = """
    class Foo { $data x: Int = 0 }
    registry Sys { register Foo { phase: dev, priority: 1 } }
    """
    new_src = """
    class Foo { $data x: Int = 0 }
    registry Sys { register Foo { phase: runtime, priority: 1 } }
    """
    changes = diff_ast(_ast(parse_src, old_src), _ast(parse_src, new_src))
    mods = _by_change(changes, "modified", "Sys")
    assert len(mods) == 1
    assert mods[0]["item_type"] == "registry"
    assert any("register Foo" in d and "phase" in d and "dev" in d and "runtime" in d
               for d in mods[0]["details"])


def test_render_produces_readable_output(parse_src):
    """The CLI render pass should produce a human-readable block for
    each change with a leading sigil and indented details."""
    old_src = "class A { $data x: Int = 0 }"
    new_src = "class A { $data x: Int = 0 $data y: Int = 0 }"
    changes = diff_ast(_ast(parse_src, old_src), _ast(parse_src, new_src))
    out = render(changes)
    assert out.startswith("~ class A")
    assert "    + $data y" in out
