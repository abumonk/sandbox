"""Tests for ArkFile.classes / instances / island_classes indices.

The parser builds a pure-additive index after assembling `items`, so that
downstream consumers can look up classes and their instances in O(1)
instead of scanning the flat items list.

Focus: the index is correctly populated, preserves source order for
multi-instance classes, handles orphan instances, and keeps island-nested
classes in a separate per-island map (no collision with top-level names).
"""


def test_top_level_classes_indexed(parse_src):
    src = """
    abstraction Movable { @in{ dt: Float } }
    class Car : Movable { $data speed: Float = 0.0 }
    class Plane : Movable { $data altitude: Float = 0.0 }
    """
    ast = parse_src(src)
    classes = ast["classes"]
    assert set(classes.keys()) == {"Car", "Plane"}
    assert classes["Car"]["kind"] == "class"
    assert classes["Car"]["name"] == "Car"
    # abstractions are NOT indexed as classes
    assert "Movable" not in classes


def test_instances_grouped_by_class_name(parse_src):
    """Multiple instances of the same class must be grouped & source-ordered."""
    src = """
    class Vehicle { $data fuel: Float = 50.0 }
    instance V1 : Vehicle { fuel = 10.0 }
    instance V2 : Vehicle { fuel = 20.0 }
    instance V3 : Vehicle { fuel = 30.0 }
    """
    ast = parse_src(src)
    grouped = ast["instances"]
    assert list(grouped.keys()) == ["Vehicle"]
    assert len(grouped["Vehicle"]) == 3
    names = [inst["name"] for inst in grouped["Vehicle"]]
    assert names == ["V1", "V2", "V3"]  # source order preserved


def test_orphan_instance_indexed_even_if_class_missing(parse_src):
    """If an instance's class isn't declared in this file, it still gets
    indexed — consumers can detect the orphan by checking `classes`.
    """
    src = """
    class Known { $data x: Int = 0 }
    instance K : Known { x = 1 }
    instance Orphan : Ghost { }
    """
    ast = parse_src(src)
    assert "Known" in ast["classes"]
    assert "Ghost" not in ast["classes"]
    # Orphan still in the instances map
    assert "Ghost" in ast["instances"]
    assert len(ast["instances"]["Ghost"]) == 1
    assert ast["instances"]["Ghost"][0]["name"] == "Orphan"
    # Known instance indexed alongside
    assert len(ast["instances"]["Known"]) == 1


def test_island_classes_in_separate_per_island_map(parse_src):
    """Nested classes live in island_classes[island_name], keeping them
    scoped and preventing collision with a top-level class of the same name.
    """
    src = """
    class Task { $data status: String = "todo" }
    island Backlog {
      strategy: script
      class Task { $data status: String = "done" }
    }
    island Other {
      strategy: code
      class Helper { $data count: Int = 0 }
    }
    """
    ast = parse_src(src)

    # Top-level Task is intact and not shadowed by Backlog's nested Task.
    assert "Task" in ast["classes"]
    assert ast["classes"]["Task"]["data_fields"][0]["default"]["value"] == '"todo"'

    # Per-island index keyed by island name, then class name.
    islands = ast["island_classes"]
    assert "Backlog" in islands
    assert "Task" in islands["Backlog"]
    # Nested Task has its own default value — not the top-level one.
    assert islands["Backlog"]["Task"]["data_fields"][0]["default"]["value"] == '"done"'
    assert "Other" in islands
    assert "Helper" in islands["Other"]
    # Top-level instances map is NOT polluted by island-scoped classes.
    assert "Helper" not in ast["classes"]
