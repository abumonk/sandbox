"""Tests for the Rust parser in tools/codegraph/rust_parser.py."""
import sys
from pathlib import Path

import pytest

_ARK_ROOT = Path(__file__).resolve().parent.parent
_CODEGRAPH = _ARK_ROOT / "tools" / "codegraph"
if str(_CODEGRAPH) not in sys.path:
    sys.path.insert(0, str(_CODEGRAPH))

from rust_parser import parse_rust_source, parse_rust_file


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
# Struct extraction
# ---------------------------------------------------------------------------

_STRUCT_SRC = """\
pub struct Foo {
    x: i32,
    y: f32,
}

struct Bar {
    name: String,
}
"""


def test_structs_detected():
    nodes, _ = parse_rust_source(_STRUCT_SRC, "mymod")
    names = _node_names(nodes)
    assert "mymod::Foo" in names
    assert "mymod::Bar" in names


def test_structs_have_class_type():
    nodes, _ = parse_rust_source(_STRUCT_SRC, "mymod")
    class_nodes = _nodes_by_type(nodes, "class")
    names = _node_names(class_nodes)
    assert "mymod::Foo" in names
    assert "mymod::Bar" in names


def test_struct_node_has_module():
    nodes, _ = parse_rust_source(_STRUCT_SRC, "mymod")
    foo = next(n for n in nodes if n["name"] == "mymod::Foo")
    assert foo["module"] == "mymod"


def test_struct_node_has_line():
    nodes, _ = parse_rust_source(_STRUCT_SRC, "mymod")
    foo = next(n for n in nodes if n["name"] == "mymod::Foo")
    assert foo["line"] == 1
    bar = next(n for n in nodes if n["name"] == "mymod::Bar")
    assert bar["line"] == 6


# ---------------------------------------------------------------------------
# Enum extraction
# ---------------------------------------------------------------------------

_ENUM_SRC = """\
pub enum Color {
    Red,
    Green,
    Blue,
}

enum Direction {
    North,
    South,
}
"""


def test_enums_detected():
    nodes, _ = parse_rust_source(_ENUM_SRC, "enums")
    names = _node_names(nodes)
    assert "enums::Color" in names
    assert "enums::Direction" in names


def test_enums_have_class_type():
    nodes, _ = parse_rust_source(_ENUM_SRC, "enums")
    class_nodes = _nodes_by_type(nodes, "class")
    names = _node_names(class_nodes)
    assert "enums::Color" in names
    assert "enums::Direction" in names


# ---------------------------------------------------------------------------
# Function extraction
# ---------------------------------------------------------------------------

_FUNCTION_SRC = """\
fn standalone_fn(x: i32) -> i32 {
    x + 1
}

pub fn public_fn() {
    println!("hello");
}

async fn async_fn() -> String {
    String::new()
}
"""


def test_top_level_functions_detected():
    nodes, _ = parse_rust_source(_FUNCTION_SRC, "fns")
    fns = _nodes_by_type(nodes, "function")
    names = _node_names(fns)
    assert "fns::standalone_fn" in names
    assert "fns::public_fn" in names
    assert "fns::async_fn" in names


def test_top_level_functions_have_function_type():
    nodes, _ = parse_rust_source(_FUNCTION_SRC, "fns")
    for fn_name in ("fns::standalone_fn", "fns::public_fn", "fns::async_fn"):
        node = next(n for n in nodes if n["name"] == fn_name)
        assert node["type"] == "function"


# ---------------------------------------------------------------------------
# impl block — methods
# ---------------------------------------------------------------------------

_IMPL_SRC = """\
struct Counter {
    count: u32,
}

impl Counter {
    pub fn new() -> Self {
        Counter { count: 0 }
    }

    fn increment(&mut self) {
        self.count += 1;
    }

    pub fn value(&self) -> u32 {
        self.count
    }
}
"""


def test_impl_methods_detected():
    nodes, _ = parse_rust_source(_IMPL_SRC, "counter")
    methods = _nodes_by_type(nodes, "method")
    names = _node_names(methods)
    assert "counter::Counter::new" in names
    assert "counter::Counter::increment" in names
    assert "counter::Counter::value" in names


def test_impl_methods_have_method_type():
    nodes, _ = parse_rust_source(_IMPL_SRC, "counter")
    for m_name in ("counter::Counter::new", "counter::Counter::increment"):
        node = next(n for n in nodes if n["name"] == m_name)
        assert node["type"] == "method"


def test_struct_and_methods_both_present():
    nodes, _ = parse_rust_source(_IMPL_SRC, "counter")
    names = _node_names(nodes)
    assert "counter::Counter" in names
    assert "counter::Counter::new" in names


# ---------------------------------------------------------------------------
# impl Trait for Type — methods attributed to the type
# ---------------------------------------------------------------------------

_TRAIT_IMPL_SRC = """\
struct MyStruct;

trait MyTrait {
    fn trait_method(&self);
}

impl MyTrait for MyStruct {
    fn trait_method(&self) {
        do_something();
    }
}
"""


def test_trait_impl_methods_have_method_type():
    """Methods inside impl Trait for Type blocks are classified as method nodes.

    The parser uses the trait name (from ``impl Trait for Type``) as the
    owner qualifier — so the FQN is ``module::TraitName::method_name``.
    """
    nodes, _ = parse_rust_source(_TRAIT_IMPL_SRC, "traitmod")
    methods = _nodes_by_type(nodes, "method")
    names = _node_names(methods)
    # Parser attributes the method to the trait name (group(1) of _RE_IMPL_FOR
    # captures the type after "for", but _RE_IMPL_PLAIN captures the trait name
    # and wins in the dedup step for this pattern).
    assert "traitmod::MyTrait::trait_method" in names


# ---------------------------------------------------------------------------
# use statement → imports edges
# ---------------------------------------------------------------------------

_USE_SRC = """\
use std::collections::HashMap;
use std::io::{Read, Write};

fn main() {}
"""


def test_use_statements_produce_imports_edges():
    _, edges = parse_rust_source(_USE_SRC, "usemod")
    import_edges = _edges_by_kind(edges, "imports")
    assert len(import_edges) >= 2


def test_use_statement_target_content():
    _, edges = parse_rust_source(_USE_SRC, "usemod")
    import_edges = _edges_by_kind(edges, "imports")
    targets = {e["target"] for e in import_edges}
    assert "std::collections::HashMap" in targets


def test_use_statement_source_is_module():
    _, edges = parse_rust_source(_USE_SRC, "usemod")
    import_edges = _edges_by_kind(edges, "imports")
    for e in import_edges:
        assert e["source"] == "usemod"


def test_use_statement_has_line():
    _, edges = parse_rust_source(_USE_SRC, "usemod")
    import_edges = _edges_by_kind(edges, "imports")
    for e in import_edges:
        assert "line" in e


# ---------------------------------------------------------------------------
# Call edges
# ---------------------------------------------------------------------------

_CALL_SRC = """\
fn helper(x: i32) -> i32 {
    x * 2
}

fn main() {
    let result = helper(21);
    println!("{}", result);
}
"""


def test_call_edges_emitted():
    _, edges = parse_rust_source(_CALL_SRC, "callmod")
    call_edges = _edges_by_kind(edges, "calls")
    assert len(call_edges) > 0


def test_call_edge_source_is_caller():
    _, edges = parse_rust_source(_CALL_SRC, "callmod")
    call_edges = _edges_by_kind(edges, "calls")
    sources = {e["source"] for e in call_edges}
    assert "callmod::main" in sources


def test_call_edge_target_is_callee():
    _, edges = parse_rust_source(_CALL_SRC, "callmod")
    call_edges = _edges_by_kind(edges, "calls")
    targets = {e["target"] for e in call_edges}
    assert "helper" in targets


def test_call_keywords_excluded():
    """if, for, while, match etc. should not appear as call targets."""
    src = """\
fn control(x: i32) {
    if x > 0 {
        for i in 0..x {}
    }
    while true {}
    match x {
        _ => {}
    }
}
"""
    _, edges = parse_rust_source(src, "ctrl")
    call_edges = _edges_by_kind(edges, "calls")
    targets = {e["target"] for e in call_edges}
    assert "if" not in targets
    assert "for" not in targets
    assert "while" not in targets
    assert "match" not in targets


# ---------------------------------------------------------------------------
# Comprehensive snippet
# ---------------------------------------------------------------------------

_COMPREHENSIVE_SRC = """\
use std::fmt;

pub struct Point {
    x: f64,
    y: f64,
}

pub enum Shape {
    Circle,
    Square,
}

impl Point {
    pub fn new(x: f64, y: f64) -> Self {
        Point { x, y }
    }

    pub fn distance(&self, other: &Point) -> f64 {
        compute_dist(self.x, self.y, other.x, other.y)
    }
}

fn compute_dist(x1: f64, y1: f64, x2: f64, y2: f64) -> f64 {
    let dx = x1 - x2;
    let dy = y1 - y2;
    sqrt(dx * dx + dy * dy)
}
"""


def test_comprehensive_struct_and_enum():
    nodes, _ = parse_rust_source(_COMPREHENSIVE_SRC, "geo")
    names = _node_names(nodes)
    assert "geo::Point" in names
    assert "geo::Shape" in names


def test_comprehensive_methods():
    nodes, _ = parse_rust_source(_COMPREHENSIVE_SRC, "geo")
    methods = _nodes_by_type(nodes, "method")
    names = _node_names(methods)
    assert "geo::Point::new" in names
    assert "geo::Point::distance" in names


def test_comprehensive_functions():
    nodes, _ = parse_rust_source(_COMPREHENSIVE_SRC, "geo")
    fns = _nodes_by_type(nodes, "function")
    names = _node_names(fns)
    assert "geo::compute_dist" in names


def test_comprehensive_imports():
    _, edges = parse_rust_source(_COMPREHENSIVE_SRC, "geo")
    import_edges = _edges_by_kind(edges, "imports")
    targets = {e["target"] for e in import_edges}
    assert "std::fmt" in targets


def test_comprehensive_call_from_method():
    _, edges = parse_rust_source(_COMPREHENSIVE_SRC, "geo")
    call_edges = _edges_by_kind(edges, "calls")
    sources = {e["source"] for e in call_edges}
    assert "geo::Point::distance" in sources


# ---------------------------------------------------------------------------
# parse_rust_file
# ---------------------------------------------------------------------------

def test_parse_rust_file(tmp_path):
    src = """\
pub struct Greet;

impl Greet {
    pub fn hello() -> &'static str {
        "hello"
    }
}
"""
    f = tmp_path / "greet.rs"
    f.write_text(src, encoding="utf-8")
    nodes, edges = parse_rust_file(f)
    names = _node_names(nodes)
    # module name derived from file stem
    assert "greet::Greet" in names
    assert "greet::Greet::hello" in names
