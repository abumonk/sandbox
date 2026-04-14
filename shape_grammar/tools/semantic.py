"""semantic.py — Semantic label propagation for shape-grammar IR.

Walks the rule tree encoded in a `ShapeGrammarIR` and ensures every rule
carries a meaningful semantic label.  The propagation rules are:

1. If a rule declares an explicit non-empty label, keep it unchanged.
2. If a rule's label is None (or empty) and the rule is reachable from a
   parent rule that carries a label, inherit the nearest ancestor's label
   (``inherits=True`` is the default per ``IRSemanticLabel``).
3. If no ancestor has a label, assign a deterministic fallback equal to the
   rule's own ``id``.

The function is **pure**: it never mutates the input IR.  It returns a new
``ShapeGrammarIR`` (and new ``IRRule`` instances where the label was changed)
using ``dataclasses.replace``.

Handles the edge case of an IR with zero rules (the base `shape_grammar.ark`
spec which only declares types) by returning the input unchanged.

CLI
---
::

    python -m shape_grammar.tools.semantic <file.ark>

Prints the propagated IR as JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Optional

from shape_grammar.tools.ir import (
    ShapeGrammarIR,
    IRRule,
    extract_ir,
    to_json_dict,
    IRError,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_parent_map(rules: list[IRRule]) -> dict[str, list[str]]:
    """Build a map from rule id -> list of parent rule ids.

    A rule P is a *parent* of rule C if C's ``lhs`` symbol appears in P's
    ``operations`` list (as a string op kind or a dict with a ``symbol`` /
    ``successor`` key), or if C's id appears in P's operations as a successor
    symbol.

    In the simple case (stub grammars from the base spec) operations are lists
    of kind strings, not symbol references.  For example grammars (T15) they
    may be dicts with a ``successor`` or ``symbol`` key.

    We also consider the ``lhs``-based chain: if rule A's ``lhs`` matches rule
    B's id, B is A's parent — this handles linear rule chains like
    ``Building -> Floor -> Panel``.
    """
    # id -> IRRule for quick lookup.
    id_to_rule: dict[str, IRRule] = {r.id: r for r in rules}

    # child_id -> set of parent_ids
    parents: dict[str, set[str]] = {r.id: set() for r in rules}

    for rule in rules:
        # Operations may reference successor symbols.
        for op in rule.operations:
            successors: list[str] = []
            if isinstance(op, str):
                # Treat the op kind itself as a potential successor symbol.
                if op in id_to_rule and op != rule.id:
                    successors.append(op)
            elif isinstance(op, dict):
                for key in ("successor", "symbol", "lhs", "rhs", "child"):
                    val = op.get(key)
                    if isinstance(val, str) and val in id_to_rule:
                        successors.append(val)
                    elif isinstance(val, list):
                        for v in val:
                            if isinstance(v, str) and v in id_to_rule:
                                successors.append(v)
            for child_id in successors:
                if child_id != rule.id:
                    parents[child_id].add(rule.id)

        # lhs-based chain: the rule whose id == this rule's lhs is a parent.
        if rule.lhs and rule.lhs in id_to_rule and rule.lhs != rule.id:
            parents[rule.id].add(rule.lhs)

    return {k: list(v) for k, v in parents.items()}


def _find_label_via_parents(
    rule_id: str,
    parent_map: dict[str, list[str]],
    label_map: dict[str, Optional[str]],
    visited: Optional[set[str]] = None,
) -> Optional[str]:
    """Recursively walk parent chain to find the nearest ancestor label.

    Returns ``None`` if no ancestor has a non-empty label.
    Cycle-safe via the ``visited`` set.
    """
    if visited is None:
        visited = set()
    if rule_id in visited:
        return None
    visited.add(rule_id)

    for parent_id in parent_map.get(rule_id, []):
        parent_label = label_map.get(parent_id)
        if parent_label:
            return parent_label
        # Recurse further up.
        inherited = _find_label_via_parents(parent_id, parent_map, label_map, visited)
        if inherited:
            return inherited
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def propagate(ir: ShapeGrammarIR) -> ShapeGrammarIR:
    """Walk the rule tree and return a new IR where every rule has a label.

    Parameters
    ----------
    ir:
        A ``ShapeGrammarIR`` (from ``extract_ir``). Not mutated.

    Returns
    -------
    ShapeGrammarIR
        A new IR instance (via ``dataclasses.replace``) with updated rules.
        Each rule's label is guaranteed to be non-empty/non-None.
        If ``ir.rules`` is empty, returns ``ir`` unchanged.
    """
    if not ir.rules:
        return ir

    rules = list(ir.rules)

    # Build a map of rule id -> declared label (may be None).
    label_map: dict[str, Optional[str]] = {r.id: r.label or None for r in rules}

    # Build parent relationships.
    parent_map = _build_parent_map(rules)

    # First pass: propagate labels from parents to children.
    # Run until stable (labels can chain transitively).
    changed = True
    max_iterations = len(rules) + 1  # safety bound
    iteration = 0
    while changed and iteration < max_iterations:
        changed = False
        iteration += 1
        for rule in rules:
            if label_map[rule.id]:
                continue  # already has a label — skip
            inherited = _find_label_via_parents(rule.id, parent_map, label_map)
            if inherited:
                label_map[rule.id] = inherited
                changed = True

    # Second pass: assign fallback = rule.id for anything still without a label.
    for rule in rules:
        if not label_map[rule.id]:
            label_map[rule.id] = rule.id

    # Build new rule list (only replace rules whose label changed).
    new_rules: list[IRRule] = []
    for rule in rules:
        new_label = label_map[rule.id]
        if new_label != rule.label:
            new_rules.append(replace(rule, label=new_label))
        else:
            new_rules.append(rule)

    return replace(ir, rules=new_rules)


def provenance_for(terminal: "Terminal") -> list[str]:  # type: ignore[name-defined]
    """Return the derivation rule-chain for a terminal.

    Parameters
    ----------
    terminal:
        A ``Terminal`` from ``evaluator.evaluate()``.

    Returns
    -------
    list[str]
        The list of rule ids from root to this terminal's position in the
        derivation tree (may be empty for top-level terminals).
    """
    return list(terminal.provenance)


# ---------------------------------------------------------------------------
# CLI __main__
# ---------------------------------------------------------------------------


def _cli_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m shape_grammar.tools.semantic",
        description="Propagate semantic labels in a shape-grammar IR.",
    )
    parser.add_argument("spec", help="Path to .ark spec file")
    args = parser.parse_args(argv[1:])

    try:
        ir = extract_ir(Path(args.spec))
    except IRError as exc:
        print(f"ERROR extracting IR: {exc}", file=sys.stderr)
        return 1

    propagated = propagate(ir)
    print(json.dumps(to_json_dict(propagated), indent=2, default=str))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_cli_main(sys.argv))
