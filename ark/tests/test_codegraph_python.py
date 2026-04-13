"""Tests for the Python parser in tools/codegraph/python_parser.py."""
import sys
from pathlib import Path

import pytest

_ARK_ROOT = Path(__file__).resolve().parent.parent
_CODEGRAPH = _ARK_ROOT / "tools" / "codegraph"
if str(_CODEGRAPH) not in sys.path:
    sys.path.insert(0, str(_CODEGRAPH))

from python_parser import parse_python_source, parse_python_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nodes_by_type(nodes, node_type):
    return [n for n in nodes if n["type"] == node_type]


def _edges_by_kind(edges, kind):
    return [e for e in edges if e["kind"] == kind]


def _node_names(nodes):
    return {n["name"] for n in nodes}


# ---------------------------------------------------------------------------
# Module node
# ---------------------------------------------------------------------------

def test_module_node_always_present():
    nodes, _ = parse_python_source("x = 1", "mymod")
    modules = _nodes_by_type(nodes, "module")
    assert len(modules) == 1
    assert modules[0]["name"] == "mymod"


def test_module_node_name_matches_argument():
    nodes, _ = parse_python_source("", "some_module")
    modules = _nodes_by_type(nodes, "module")
    assert modules[0]["name"] == "some_module"


# ---------------------------------------------------------------------------
# Function parsing
# ---------------------------------------------------------------------------

_FUNCTION_SRC = """\
def greet(name):
    return "hello " + name

def farewell(name):
    return "bye " + name
"""


def test_top_level_functions_detected():
    nodes, _ = parse_python_source(_FUNCTION_SRC, "greetings")
    fns = _nodes_by_type(nodes, "function")
    names = _node_names(fns)
    assert "greetings.greet" in names
    assert "greetings.farewell" in names


def test_function_count():
    nodes, _ = parse_python_source(_FUNCTION_SRC, "greetings")
    fns = _nodes_by_type(nodes, "function")
    assert len(fns) == 2


def test_function_node_has_module_field():
    nodes, _ = parse_python_source(_FUNCTION_SRC, "greetings")
    fn = next(n for n in nodes if n["name"] == "greetings.greet")
    assert fn["module"] == "greetings"


def test_function_node_has_line_numbers():
    nodes, _ = parse_python_source(_FUNCTION_SRC, "greetings")
    fn = next(n for n in nodes if n["name"] == "greetings.greet")
    assert fn["line"] == 1
    fn2 = next(n for n in nodes if n["name"] == "greetings.farewell")
    assert fn2["line"] == 4


# ---------------------------------------------------------------------------
# Class parsing
# ---------------------------------------------------------------------------

_CLASS_SRC = """\
class Animal:
    def speak(self):
        return "..."

class Dog(Animal):
    def speak(self):
        bark()
        return "woof"
"""


def test_classes_detected():
    nodes, _ = parse_python_source(_CLASS_SRC, "animals")
    classes = _nodes_by_type(nodes, "class")
    names = _node_names(classes)
    assert "animals.Animal" in names
    assert "animals.Dog" in names


def test_methods_inside_class_are_methods_not_functions():
    nodes, _ = parse_python_source(_CLASS_SRC, "animals")
    methods = _nodes_by_type(nodes, "method")
    names = _node_names(methods)
    # Both Animal.speak and Dog.speak are methods
    assert "animals.Animal.speak" in names
    assert "animals.Dog.speak" in names


def test_methods_not_classified_as_functions():
    nodes, _ = parse_python_source(_CLASS_SRC, "animals")
    fns = _nodes_by_type(nodes, "function")
    names = _node_names(fns)
    assert "animals.Animal.speak" not in names
    assert "animals.Dog.speak" not in names


# ---------------------------------------------------------------------------
# Inheritance edges
# ---------------------------------------------------------------------------

def test_inheritance_edge_emitted():
    nodes, edges = parse_python_source(_CLASS_SRC, "animals")
    inherit_edges = _edges_by_kind(edges, "inherits")
    # Dog(Animal) → inherits edge from Dog to Animal
    assert any(e["source"] == "animals.Dog" and e["target"] == "Animal"
               for e in inherit_edges)


def test_no_inheritance_edge_for_base_class():
    nodes, edges = parse_python_source(_CLASS_SRC, "animals")
    inherit_edges = _edges_by_kind(edges, "inherits")
    # Animal has no base → no inherits edge from Animal
    assert not any(e["source"] == "animals.Animal" for e in inherit_edges)


def test_multiple_inheritance():
    src = """\
class A:
    pass

class B:
    pass

class C(A, B):
    pass
"""
    nodes, edges = parse_python_source(src, "multi")
    inherit_edges = _edges_by_kind(edges, "inherits")
    sources = [(e["source"], e["target"]) for e in inherit_edges]
    assert ("multi.C", "A") in sources
    assert ("multi.C", "B") in sources


# ---------------------------------------------------------------------------
# Call edges
# ---------------------------------------------------------------------------

_CALL_SRC = """\
def helper():
    pass

def main():
    helper()
    print("done")
    helper()
"""


def test_call_edges_emitted():
    nodes, edges = parse_python_source(_CALL_SRC, "prog")
    call_edges = _edges_by_kind(edges, "calls")
    sources = {e["source"] for e in call_edges}
    targets = {e["target"] for e in call_edges}
    assert "prog.main" in sources
    assert "helper" in targets
    assert "print" in targets


def test_multiple_calls_to_same_target():
    """Two calls to helper() should produce two call edges."""
    nodes, edges = parse_python_source(_CALL_SRC, "prog")
    call_edges = [e for e in edges
                  if e["kind"] == "calls" and e["target"] == "helper"]
    assert len(call_edges) == 2


def test_method_call_edges():
    """Calls inside a method use the method as source."""
    src = """\
class Foo:
    def bar(self):
        helper()
        self.baz()

    def baz(self):
        pass
"""
    nodes, edges = parse_python_source(src, "mod")
    call_edges = _edges_by_kind(edges, "calls")
    sources = {e["source"] for e in call_edges}
    assert "mod.Foo.bar" in sources


# ---------------------------------------------------------------------------
# Import edges
# ---------------------------------------------------------------------------

_IMPORT_SRC = """\
import os
import sys as system
from pathlib import Path
from collections import defaultdict, OrderedDict
"""


def test_import_edges_from_plain_import():
    nodes, edges = parse_python_source(_IMPORT_SRC, "mymod")
    import_edges = _edges_by_kind(edges, "imports")
    targets = {e["target"] for e in import_edges}
    assert "os" in targets


def test_import_as_uses_alias():
    nodes, edges = parse_python_source(_IMPORT_SRC, "mymod")
    import_edges = _edges_by_kind(edges, "imports")
    targets = {e["target"] for e in import_edges}
    # 'import sys as system' → target is 'system'
    assert "system" in targets


def test_from_import_creates_dotted_target():
    nodes, edges = parse_python_source(_IMPORT_SRC, "mymod")
    import_edges = _edges_by_kind(edges, "imports")
    targets = {e["target"] for e in import_edges}
    assert "pathlib.Path" in targets


def test_from_import_multiple_names():
    nodes, edges = parse_python_source(_IMPORT_SRC, "mymod")
    import_edges = _edges_by_kind(edges, "imports")
    targets = {e["target"] for e in import_edges}
    assert "collections.defaultdict" in targets
    assert "collections.OrderedDict" in targets


def test_import_edge_source_is_module():
    nodes, edges = parse_python_source(_IMPORT_SRC, "mymod")
    import_edges = _edges_by_kind(edges, "imports")
    for e in import_edges:
        assert e["source"] == "mymod"


# ---------------------------------------------------------------------------
# Comprehensive snippet
# ---------------------------------------------------------------------------

_COMPREHENSIVE_SRC = """\
import json
from pathlib import Path

class Base:
    def base_method(self):
        json.dumps({})

class Child(Base):
    def child_method(self):
        self.base_method()

def standalone(x):
    p = Path(x)
    return p
"""


def test_comprehensive_node_counts():
    nodes, edges = parse_python_source(_COMPREHENSIVE_SRC, "comp")
    assert len(_nodes_by_type(nodes, "module")) == 1
    assert len(_nodes_by_type(nodes, "class")) == 2
    assert len(_nodes_by_type(nodes, "method")) == 2
    assert len(_nodes_by_type(nodes, "function")) == 1


def test_comprehensive_inheritance():
    nodes, edges = parse_python_source(_COMPREHENSIVE_SRC, "comp")
    inherit = _edges_by_kind(edges, "inherits")
    assert any(e["source"] == "comp.Child" and e["target"] == "Base"
               for e in inherit)


def test_comprehensive_imports():
    nodes, edges = parse_python_source(_COMPREHENSIVE_SRC, "comp")
    imports = _edges_by_kind(edges, "imports")
    targets = {e["target"] for e in imports}
    assert "json" in targets
    assert "pathlib.Path" in targets


def test_comprehensive_call_edges_present():
    nodes, edges = parse_python_source(_COMPREHENSIVE_SRC, "comp")
    calls = _edges_by_kind(edges, "calls")
    assert len(calls) > 0


# ---------------------------------------------------------------------------
# Syntax error handling
# ---------------------------------------------------------------------------

def test_syntax_error_returns_empty():
    nodes, edges = parse_python_source("def broken(", "bad")
    assert nodes == []
    assert edges == []


# ---------------------------------------------------------------------------
# parse_python_file
# ---------------------------------------------------------------------------

def test_parse_python_file(tmp_path):
    src = """\
def add(a, b):
    return a + b

def sub(a, b):
    return a - b
"""
    f = tmp_path / "myfile.py"
    f.write_text(src, encoding="utf-8")
    nodes, edges = parse_python_file(f)
    names = _node_names(nodes)
    # module name derived from file stem
    assert "myfile" in names
    assert "myfile.add" in names
    assert "myfile.sub" in names
