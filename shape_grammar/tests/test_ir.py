"""test_ir.py — Tests for shape_grammar.tools.ir.

Covers:
  - Round-trip extraction from all three spec islands (TC-03).
  - Structural field assertions on the canonical shape_grammar.ark island.
  - Negative / error paths: IRError raised for missing island, missing
    operations, non-positive max_depth (AC: at least one negative test).
  - Provenance dict structure.
  - Empty-island edge case (no entities).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from shape_grammar.tools.ir import (
    IRError,
    IRRule,
    ShapeGrammarIR,
    extract_ir,
    require_island,
    require_populated,
    validate_rules,
)


# ---------------------------------------------------------------------------
# TC-03: Round-trip extraction from each spec island
# ---------------------------------------------------------------------------


def test_ir_roundtrip_each_spec_island(spec_path: Path) -> None:
    """Parametrized over shape_grammar.ark / operations.ark / semantic.ark.

    Asserts that extract_ir() returns a ShapeGrammarIR (not None, not an
    exception) and that the entity list is non-empty for each spec.
    """
    ir = extract_ir(spec_path)
    assert isinstance(ir, ShapeGrammarIR), (
        f"extract_ir({spec_path.name}) returned {type(ir)}, expected ShapeGrammarIR"
    )
    assert isinstance(ir.source_file, str) and ir.source_file
    assert len(ir.entities) > 0, (
        f"expected at least one entity from {spec_path.name}, got 0"
    )


def test_ir_roundtrip_shape_grammar_island_name() -> None:
    """shape_grammar.ark declares an island; island_name must be 'ShapeGrammar'."""
    ir = extract_ir(Path("shape_grammar/specs/shape_grammar.ark"))
    assert ir.island_name == "ShapeGrammar"


def test_ir_roundtrip_operations_no_island() -> None:
    """operations.ark has no island; island_name must be None."""
    ir = extract_ir(Path("shape_grammar/specs/operations.ark"))
    assert ir.island_name is None


def test_ir_roundtrip_semantic_no_island() -> None:
    """semantic.ark has no island; island_name must be None."""
    ir = extract_ir(Path("shape_grammar/specs/semantic.ark"))
    assert ir.island_name is None


# ---------------------------------------------------------------------------
# TC-03: Field-level assertions on canonical IR
# ---------------------------------------------------------------------------


def test_ir_fields_populated(canonical_ir: ShapeGrammarIR) -> None:
    """Asserts shape_grammar.ark island carries max_depth, seed, axiom fields."""
    ir = canonical_ir
    # max_depth: the spec declares Int [1..100]; extract_ir captures this as
    # an IRRange dict (since no concrete default is set).
    assert ir.max_depth is not None, "max_depth must be populated from spec"
    # seed: declared Int [0..2147483647]; also captured as IRRange dict.
    assert ir.seed is not None, "seed must be populated from spec"
    # axiom: declared String (no default); should be present (possibly None value
    # if no default, but the field itself must have been seen).
    # We test that entities include a ShapeGrammar island with an axiom field.
    island_entity = next((e for e in ir.entities if e.kind == "island"), None)
    assert island_entity is not None, "ShapeGrammar island entity must be present"
    field_names = [f.name for f in island_entity.fields]
    assert "max_depth" in field_names
    assert "seed" in field_names
    assert "axiom" in field_names


def test_ir_entity_count_shape_grammar() -> None:
    """shape_grammar.ark declares exactly 7 entities (Shape, Rule, Operation,
    AttrEntry, Scope, Terminal, ShapeGrammar)."""
    ir = extract_ir(Path("shape_grammar/specs/shape_grammar.ark"))
    assert len(ir.entities) == 7, (
        f"expected 7 entities from shape_grammar.ark, got {len(ir.entities)}: "
        f"{[e.name for e in ir.entities]}"
    )


def test_ir_entity_count_operations() -> None:
    """operations.ark declares exactly 10 entities."""
    ir = extract_ir(Path("shape_grammar/specs/operations.ark"))
    assert len(ir.entities) == 10, (
        f"expected 10 entities from operations.ark, got {len(ir.entities)}: "
        f"{[e.name for e in ir.entities]}"
    )


def test_ir_entity_count_semantic() -> None:
    """semantic.ark declares exactly 2 entities (SemanticLabel, Provenance)."""
    ir = extract_ir(Path("shape_grammar/specs/semantic.ark"))
    assert len(ir.entities) == 2, (
        f"expected 2 entities from semantic.ark, got {len(ir.entities)}: "
        f"{[e.name for e in ir.entities]}"
    )


def test_ir_scope_entity_has_five_fields() -> None:
    """Scope entity in shape_grammar.ark must have 5 $data fields."""
    ir = extract_ir(Path("shape_grammar/specs/shape_grammar.ark"))
    scope = next((e for e in ir.entities if e.name == "Scope"), None)
    assert scope is not None, "Scope entity not found"
    assert len(scope.fields) == 5, (
        f"expected 5 Scope fields, got {len(scope.fields)}: "
        f"{[f.name for f in scope.fields]}"
    )


def test_ir_extrude_op_entity_has_range() -> None:
    """ExtrudeOp.height in operations.ark should carry a range constraint."""
    ir = extract_ir(Path("shape_grammar/specs/operations.ark"))
    extrude = next((e for e in ir.entities if e.name == "ExtrudeOp"), None)
    assert extrude is not None, "ExtrudeOp entity not found"
    height_field = next((f for f in extrude.fields if f.name == "height"), None)
    assert height_field is not None, "ExtrudeOp.height field not found"
    assert height_field.range is not None, (
        "ExtrudeOp.height should carry range [0.001 .. 1000.0]"
    )


# ---------------------------------------------------------------------------
# Negative tests (AC requirement: at least one per file)
# ---------------------------------------------------------------------------


def test_ir_missing_island_raises(tmp_path: Path) -> None:
    """IRError raised when require_island() is called on an island-less IR.

    Constructs a minimal .ark with no island declaration, extracts IR, then
    asserts that require_island() raises IRError.
    """
    ark_file = tmp_path / "no_island.ark"
    ark_file.write_text(
        "// no island here\n"
        "class Foo {\n"
        "    $data x: Int\n"
        "}\n",
        encoding="utf-8",
    )
    ir = extract_ir(ark_file)
    assert ir.island_name is None, "Expected no island in this file"
    with pytest.raises(IRError, match="no ShapeGrammar island found"):
        require_island(ir)


def test_ir_missing_operations_raises() -> None:
    """IRError raised when a concrete rule in ir.rules has no operations.

    Directly constructs a ShapeGrammarIR with an empty-operations rule and
    asserts validate_rules() raises IRError.
    """
    ir = ShapeGrammarIR(
        source_file="synthetic",
        rules=[
            IRRule(id="r_bad", lhs="A", operations=[]),
        ],
    )
    with pytest.raises(IRError, match="rule r_bad has no operations"):
        validate_rules(ir)


def test_ir_nonpositive_max_depth_raises() -> None:
    """IRError raised when the island declares max_depth <= 0.

    Directly constructs a ShapeGrammarIR with island_name set and an
    integer max_depth of 0 and asserts require_populated() raises IRError.
    """
    # Build a minimal ShapeGrammarIR that looks like it came from a file
    # with max_depth: 0 (invalid — must be positive).
    ir = ShapeGrammarIR(
        source_file="synthetic",
        island_name="ShapeGrammar",
        max_depth=0,
        entities=[
            # Need at least one entity so require_populated doesn't error
            # on the "no entities" check first.
            __import__("shape_grammar.tools.ir", fromlist=["IREntity"]).IREntity(
                name="Rule", kind="class"
            )
        ],
    )
    with pytest.raises(IRError, match="max_depth must be positive Int"):
        require_populated(ir)


def test_ir_empty_island_raises() -> None:
    """IRError raised when require_populated() is called on an IR with no entities.

    Uses a ShapeGrammarIR with an empty entities list (as if extracted from
    a completely empty .ark file).
    """
    ir = ShapeGrammarIR(source_file="empty.ark", entities=[])
    with pytest.raises(IRError, match="no ShapeGrammar island found"):
        require_populated(ir)


def test_ir_nonexistent_file_raises() -> None:
    """IRError raised when the source file does not exist."""
    with pytest.raises(IRError, match="file not found"):
        extract_ir(Path("shape_grammar/specs/does_not_exist.ark"))


# ---------------------------------------------------------------------------
# Provenance / serialisation sanity
# ---------------------------------------------------------------------------


def test_ir_serialises_to_json(canonical_ir: ShapeGrammarIR) -> None:
    """The canonical IR must round-trip through to_json_dict without error."""
    from shape_grammar.tools.ir import to_json_dict

    d = to_json_dict(canonical_ir)
    # Must be JSON-serialisable.
    serialised = json.dumps(d, default=str)
    assert isinstance(serialised, str) and len(serialised) > 0

    # Must preserve island name.
    assert d.get("island_name") == "ShapeGrammar"


def test_ir_provenance_is_dict(canonical_ir: ShapeGrammarIR) -> None:
    """provenance field must be a dict (may be empty for spec-level extraction)."""
    assert isinstance(canonical_ir.provenance, dict)
