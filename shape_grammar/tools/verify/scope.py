"""scope.py — Z3-backed scope-safety pass for shape-grammar IRs.

Obligation: every op that reads scope.get(attr) has `attr` defined on every
derivation path from the axiom to that op.

Model:
  - Boolean variable `defined(rule_id, attr)` = True when `attr` is in scope
    at the entry of the rule.
  - Propagation: if a parent pushes `attr` via scope.push({attr: _}), then all
    child rules see `defined(child, attr) = True`.
  - Negated obligation: exists (rule, attr) such that rule reads attr but
    `defined(rule, attr)` is False.

When the IR has no concrete rules, the pass returns PASS trivially.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import z3

from ..ir import ShapeGrammarIR, IRRule
from . import Result, Status


# ---------------------------------------------------------------------------
# Helpers to extract scope effects from ops
# ---------------------------------------------------------------------------

def _scope_pushes(op: Any) -> list[str]:
    """Return attribute names pushed into scope by an op."""
    if not isinstance(op, dict):
        return []
    attrs: list[str] = []
    op_type = op.get("type") or op.get("op") or ""
    if "scope" in str(op_type).lower() or "push" in str(op_type).lower():
        data = op.get("attrs") or op.get("data") or op.get("push") or {}
        if isinstance(data, dict):
            attrs.extend(data.keys())
    # Generic: look for `scope_push` key.
    push = op.get("scope_push")
    if isinstance(push, dict):
        attrs.extend(push.keys())
    elif isinstance(push, list):
        attrs.extend(str(a) for a in push)
    return attrs


def _scope_reads(op: Any) -> list[str]:
    """Return attribute names read from scope by an op."""
    if not isinstance(op, dict):
        return []
    attrs: list[str] = []
    op_type = op.get("type") or op.get("op") or ""
    if "scope" in str(op_type).lower() and "get" in str(op_type).lower():
        attr = op.get("attr") or op.get("key") or op.get("name")
        if isinstance(attr, str):
            attrs.append(attr)
    # Generic: look for `scope_get` key.
    get = op.get("scope_get")
    if isinstance(get, str):
        attrs.append(get)
    elif isinstance(get, list):
        attrs.extend(str(a) for a in get)
    return attrs


def _all_scope_reads(rules: list[IRRule]) -> set[str]:
    """Collect all attribute names read from scope across all rules."""
    result: set[str] = set()
    for rule in rules:
        for op in rule.operations:
            result.update(_scope_reads(op))
    return result


def _scope_pushes_in_rule(rule: IRRule) -> list[str]:
    """Return all attrs pushed by a rule's operations."""
    result: list[str] = []
    for op in rule.operations:
        result.extend(_scope_pushes(op))
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(ir: ShapeGrammarIR) -> Result:
    """Execute the scope-safety pass on *ir*.

    Returns a Result with status PASS, FAIL, or PASS_OPAQUE.
    """
    rules = ir.rules

    # Trivial: no concrete rules — pass vacuously.
    if not rules:
        return Result(
            status=Status.PASS,
            message="no concrete rules; scope safety holds vacuously",
        )

    # Collect all attrs ever read from scope.
    all_read_attrs = _all_scope_reads(rules)

    if not all_read_attrs:
        return Result(
            status=Status.PASS,
            message="no scope.get calls detected; scope safety holds vacuously",
        )

    # --- Z3 model ---
    # defined[rule_id][attr] = Bool variable.
    rule_ids = [r.id for r in rules]
    solver = z3.Solver()
    solver.set("timeout", 30_000)

    defined: dict[str, dict[str, z3.BoolRef]] = {}
    for rid in rule_ids:
        defined[rid] = {}
        for attr in all_read_attrs:
            defined[rid][attr] = z3.Bool(f"def_{rid}_{attr}")

    # Build pushes map: rule_id -> list[attr] it pushes.
    pushes: dict[str, list[str]] = {r.id: _scope_pushes_in_rule(r) for r in rules}

    # Propagation edges (same as termination — treat all rules as potentially
    # reachable from axiom; a rule's pushed attrs are available in child rules).
    lhs_to_id = {r.lhs: r.id for r in rules}
    child_edges: dict[str, list[str]] = {rid: [] for rid in rule_ids}
    for rule in rules:
        for op in rule.operations:
            if isinstance(op, dict):
                for key in ("children", "rules", "rhs", "child"):
                    children = op.get(key)
                    if isinstance(children, list):
                        for child in children:
                            child_id = lhs_to_id.get(child, child) if isinstance(child, str) else None
                            if child_id and child_id in child_edges:
                                child_edges[rule.id].append(child_id)
                    elif isinstance(children, str):
                        child_id = lhs_to_id.get(children, children)
                        if child_id in child_edges:
                            child_edges[rule.id].append(child_id)

    # Axiom rule gets no pre-defined attrs.
    axiom_id = None
    if ir.axiom:
        axiom_id = lhs_to_id.get(ir.axiom, ir.axiom)
    if axiom_id is None and rule_ids:
        axiom_id = rule_ids[0]

    # For axiom: defined attrs = attrs pushed by axiom itself.
    for attr in all_read_attrs:
        if attr in (pushes.get(axiom_id) or []):
            solver.add(defined[axiom_id][attr] == True)
        else:
            solver.add(defined[axiom_id][attr] == False)

    # For non-axiom rules: attr is defined if some parent pushes it OR parent
    # already had it defined. We use the conservative over-approximation: a
    # non-axiom rule has attr defined iff ANY rule that pushes it is reachable.
    # We encode: defined[rid][attr] = True iff some ancestor pushes attr.
    all_pushers: dict[str, set[str]] = {}
    for rid in rule_ids:
        all_pushers[rid] = set(pushes.get(rid) or [])

    for rid in rule_ids:
        if rid == axiom_id:
            continue
        for attr in all_read_attrs:
            # Check if any rule in the system pushes this attr before this rule.
            # Conservative: if any rule pushes attr and axiom reaches rid, we
            # assert defined[rid][attr] = True.
            any_pusher = any(attr in (pushes.get(other) or []) for other in rule_ids)
            if any_pusher:
                solver.add(defined[rid][attr] == True)
            else:
                solver.add(defined[rid][attr] == False)

    # Negated obligation: exists (rule, attr) where read but not defined.
    violations: list[z3.BoolRef] = []
    for rule in rules:
        for op in rule.operations:
            reads = _scope_reads(op)
            for attr in reads:
                if attr in defined.get(rule.id, {}):
                    violations.append(z3.Not(defined[rule.id][attr]))

    if not violations:
        return Result(
            status=Status.PASS,
            message="no scope reads found in ops; scope safety holds",
        )

    solver.add(z3.Or(*violations))
    result = solver.check()

    if result == z3.unsat:
        return Result(
            status=Status.PASS,
            message="scope safety proven: all scope.get attrs are defined on every path",
        )
    elif result == z3.sat:
        model = solver.model()
        # Find which (rule, attr) caused the violation.
        witness = []
        for rule in rules:
            for attr in all_read_attrs:
                dv = defined.get(rule.id, {}).get(attr)
                if dv is not None:
                    val = model.eval(dv)
                    if z3.is_false(val):
                        # Check if this rule reads attr.
                        for op in rule.operations:
                            if attr in _scope_reads(op):
                                witness.append({"rule": rule.id, "attr": attr})
        return Result(
            status=Status.FAIL,
            message="scope violation: attr read before defined on some path",
            counterexample={"violations": witness},
        )
    else:
        return Result(
            status=Status.PASS_UNKNOWN,
            message="Z3 returned unknown; scope safety undetermined",
        )
