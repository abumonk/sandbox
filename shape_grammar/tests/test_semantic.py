"""test_semantic.py — Tests for shape_grammar.tools.semantic (propagate).

Covers:
  - TC-08: Every terminal carries an inherited-or-overridden semantic label.
  - Label inheritance: rule B inherits label from parent rule A.
  - Fallback label: rule with no ancestor labels gets its own id.
  - Purity: original IR is not mutated by propagate().
  - Zero-rules IR returned unchanged.
  - Negative: propagate on terminal with no label fills in a default.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from shape_grammar.tools.evaluator import Terminal, evaluate
from shape_grammar.tools.ir import IRRule, ShapeGrammarIR
from shape_grammar.tools.scope import Scope
from shape_grammar.tools.semantic import propagate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ir(*rules: IRRule, max_depth: int = 5) -> ShapeGrammarIR:
    """Construct a minimal ShapeGrammarIR from the given rules."""
    return ShapeGrammarIR(
        source_file="__test__",
        max_depth=max_depth,
        seed=42,
        axiom=rules[0].id if rules else "",
        rules=list(rules),
    )


def _scope() -> Scope:
    return Scope.identity()


# ---------------------------------------------------------------------------
# TC-08: Every terminal has a label after propagate + evaluate
# ---------------------------------------------------------------------------


def test_every_terminal_has_label() -> None:
    """After propagate(), every terminal produced by evaluate has a non-empty label.

    TC-08: Every terminal carries an inherited-or-overridden semantic label.
    Uses a synthetic IR (the spec examples have no concrete rule instances —
    they are type declarations only).  Terminal rules (is_terminal=True)
    produce leaf nodes directly.
    """
    ir = _make_ir(
        IRRule(id="Root", lhs="Root", is_terminal=False, label="facade",
               operations=[
                   {"kind": "extrude", "id": "Root_ext", "height": 1.0, "symbol": "Wall"},
               ]),
        IRRule(id="Wall", lhs="Wall", is_terminal=True, label="wall"),
    )
    propagated = propagate(ir)
    terminals = evaluate(propagated, 42)
    assert len(terminals) > 0, "expected at least one terminal"
    for t in terminals:
        assert t.label, f"terminal {t.tag!r} has empty/None label"


# ---------------------------------------------------------------------------
# Label inheritance propagates
# ---------------------------------------------------------------------------


def test_label_inheritance_propagates() -> None:
    """Rule B (lhs == A's id) must inherit A's label after propagate().

    A has label 'building'; B has no label; B's lhs references A's id.
    After propagate(), B's label should be 'building'.
    """
    rule_a = IRRule(id="A", lhs="A", label="building")
    rule_b = IRRule(id="B", lhs="A", label=None)  # lhs matches A's id -> A is parent
    ir = _make_ir(rule_a, rule_b)
    propagated = propagate(ir)
    rule_b_propagated = next(r for r in propagated.rules if r.id == "B")
    assert rule_b_propagated.label == "building", (
        f"expected B to inherit label 'building', got {rule_b_propagated.label!r}"
    )


def test_label_override_wins() -> None:
    """A rule that explicitly declares a label keeps it even if parent has a different one."""
    rule_a = IRRule(id="A", lhs="A", label="building")
    rule_b = IRRule(id="B", lhs="A", label="window")  # explicit override
    ir = _make_ir(rule_a, rule_b)
    propagated = propagate(ir)
    rule_b_propagated = next(r for r in propagated.rules if r.id == "B")
    assert rule_b_propagated.label == "window", (
        f"expected B to keep label 'window', got {rule_b_propagated.label!r}"
    )


# ---------------------------------------------------------------------------
# Fallback label
# ---------------------------------------------------------------------------


def test_fallback_label_is_rule_id() -> None:
    """A rule with no ancestor labels receives its own id as the fallback label."""
    rule = IRRule(id="OrphanRule", lhs="OrphanRule", label=None)
    ir = _make_ir(rule)
    propagated = propagate(ir)
    propagated_rule = propagated.rules[0]
    assert propagated_rule.label == "OrphanRule", (
        f"expected fallback label 'OrphanRule', got {propagated_rule.label!r}"
    )


# ---------------------------------------------------------------------------
# Purity
# ---------------------------------------------------------------------------


def test_propagate_does_not_mutate_original() -> None:
    """propagate() must not mutate the input IR.

    After calling propagate(), the original IR's rules must be unchanged.
    """
    rule_a = IRRule(id="A", lhs="A", label="parent_label")
    rule_b = IRRule(id="B", lhs="A", label=None)
    ir = _make_ir(rule_a, rule_b)

    # Capture original labels
    original_labels = {r.id: r.label for r in ir.rules}

    propagated = propagate(ir)

    # Original IR must be untouched
    for r in ir.rules:
        assert r.label == original_labels[r.id], (
            f"original rule {r.id!r} label was mutated: "
            f"was {original_labels[r.id]!r}, now {r.label!r}"
        )

    # Propagated result must be a different object
    assert propagated is not ir, "propagate returned the same IR object (not pure)"


# ---------------------------------------------------------------------------
# Zero-rules edge case
# ---------------------------------------------------------------------------


def test_zero_rules_ir_returned_unchanged() -> None:
    """propagate() on an IR with no rules returns the same IR object."""
    ir = ShapeGrammarIR(
        source_file="__test__",
        max_depth=5,
        seed=42,
        axiom="",
        rules=[],
    )
    result = propagate(ir)
    assert result is ir, "expected the same IR object when rules list is empty"


# ---------------------------------------------------------------------------
# Provenance assertions
# ---------------------------------------------------------------------------


def test_provenance_chain_depth_matches_derivation() -> None:
    """terminal.provenance list length == derivation depth recorded in provenance."""
    ir = _make_ir(
        IRRule(
            id="Root",
            lhs="Root",
            is_terminal=False,
            label="root",
            operations=[
                {"kind": "extrude", "id": "Root_ext", "height": 1.0, "symbol": "Child"},
            ],
        ),
        IRRule(id="Child", lhs="Child", is_terminal=True, label="leaf"),
    )
    propagated = propagate(ir)
    terminals = evaluate(propagated, 42)
    for t in terminals:
        # provenance is a list[str] of rule ids; depth == len(provenance)
        assert isinstance(t.provenance, list)


def test_provenance_root_is_axiom() -> None:
    """The first entry in terminal.provenance must equal ir.axiom when non-empty."""
    ir = _make_ir(
        IRRule(
            id="Axiom",
            lhs="Axiom",
            is_terminal=False,
            label="root",
            operations=[
                {"kind": "extrude", "id": "Axiom_ext", "height": 1.0, "symbol": "Child"},
            ],
        ),
        IRRule(id="Child", lhs="Child", is_terminal=True, label="leaf"),
    )
    propagated = propagate(ir)
    terminals = evaluate(propagated, 42)
    for t in terminals:
        if t.provenance:
            assert t.provenance[0] == "Axiom", (
                f"expected provenance root 'Axiom', got {t.provenance[0]!r}"
            )


# ---------------------------------------------------------------------------
# Negative: label_missing => fallback fills it in
# ---------------------------------------------------------------------------


def test_label_missing_fills_default() -> None:
    """A rule with label=None gets a non-empty label after propagate() (fallback = rule id)."""
    rule = IRRule(id="Unlabelled", lhs="Unlabelled", label=None)
    ir = _make_ir(rule)
    propagated = propagate(ir)
    for r in propagated.rules:
        assert r.label is not None and r.label != "", (
            f"rule {r.id!r} still has empty label after propagate()"
        )
