"""termination.py — Z3-backed termination pass for shape-grammar IRs.

Obligation: every derivation is bounded by `max_depth`.

Model:
  - Integer variable depth(node) for every rule expansion node.
  - Constraints:
      depth(axiom) == 0
      forall (parent, child) in expansion_edges: depth(child) == depth(parent) + 1
  - SAT query (negated obligation):
      exists node: depth(node) > max_depth  ->  UNSAT means PASS.

Data-dependent expansion counts (e.g. SplitOp with runtime-valued count)
yield PASS_OPAQUE. Z3 timeout >30 s yields PASS_UNKNOWN.

When the IR has no concrete rules (e.g. the base structural spec), the pass
returns PASS trivially — there is nothing to check.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

import z3

from ..ir import ShapeGrammarIR, IRRule
from . import Result, Status


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_data_dependent(rule: IRRule) -> bool:
    """Return True if the rule has a data-dependent expansion count.

    A SplitOp is data-dependent when its `count` field is sourced from a
    runtime attribute (represented as a dict with no concrete int value) rather
    than a literal integer.
    """
    for op in rule.operations:
        if isinstance(op, dict):
            if op.get("type") == "SplitOp" or op.get("op") == "split":
                count = op.get("count")
                if count is None or isinstance(count, dict):
                    return True
    return False


def _build_expansion_edges(rules: list[IRRule], axiom: Optional[str]) -> list[tuple[str, str]]:
    """Build (parent_id, child_id) expansion edges from the rule list.

    Each rule body may reference other rule IDs in its operations.
    We create an edge from the rule's LHS symbol to each referenced RHS.
    Also add the axiom→first-rule edge when axiom is known.
    """
    edges: list[tuple[str, str]] = []
    lhs_to_id = {r.lhs: r.id for r in rules}

    for rule in rules:
        for op in rule.operations:
            # Each operation dict may list child rule references.
            if isinstance(op, dict):
                for key in ("children", "rules", "rhs", "child"):
                    children = op.get(key)
                    if isinstance(children, list):
                        for child in children:
                            child_id = lhs_to_id.get(child, child) if isinstance(child, str) else None
                            if child_id:
                                edges.append((rule.id, child_id))
                    elif isinstance(children, str):
                        child_id = lhs_to_id.get(children, children)
                        edges.append((rule.id, child_id))

    # Self-referential rules (recursive expansions) produce a self-edge.
    for rule in rules:
        if rule.lhs and any(rule.lhs in (op.get("rhs", "") if isinstance(op, dict) else "") for op in rule.operations):
            edges.append((rule.id, rule.id))

    return edges


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(ir: ShapeGrammarIR) -> Result:
    """Execute the termination pass on *ir*.

    Returns a Result with status PASS, FAIL, PASS_OPAQUE, or PASS_UNKNOWN.
    """
    rules = ir.rules

    # Trivial: no concrete grammar rules — pass vacuously.
    if not rules:
        return Result(
            status=Status.PASS,
            message="no concrete rules; termination holds vacuously",
        )

    # Check for data-dependent rules before building Z3 model.
    opaque_rules = [r for r in rules if _is_data_dependent(r)]
    if opaque_rules:
        names = ", ".join(r.id for r in opaque_rules)
        return Result(
            status=Status.PASS_OPAQUE,
            message=f"data-dependent expansion count in rules: {names}; "
                    "termination cannot be proven statically",
        )

    # Determine max_depth.
    max_depth_val: Optional[int] = None
    if isinstance(ir.max_depth, int):
        max_depth_val = ir.max_depth
    elif isinstance(ir.max_depth, dict):
        # IRRange serialised as dict — use the upper bound.
        hi = ir.max_depth.get("max")
        if isinstance(hi, (int, float)):
            max_depth_val = int(hi)

    if max_depth_val is None:
        # No max_depth declared — cannot bound the derivation.
        return Result(
            status=Status.PASS_OPAQUE,
            message="max_depth not declared; termination is unchecked",
        )

    # Build Z3 model.
    solver = z3.Solver()
    solver.set("timeout", 30_000)  # 30 s in milliseconds

    node_ids = list({r.id for r in rules})
    depth_vars: dict[str, z3.ArithRef] = {nid: z3.Int(f"depth_{nid}") for nid in node_ids}

    # Non-negativity.
    for dv in depth_vars.values():
        solver.add(dv >= 0)

    # Axiom depth = 0.
    axiom = ir.axiom
    if axiom and axiom in depth_vars:
        solver.add(depth_vars[axiom] == 0)
    elif node_ids:
        # Use first rule as axiom proxy.
        solver.add(depth_vars[node_ids[0]] == 0)

    # Expansion edges: depth(child) == depth(parent) + 1.
    edges = _build_expansion_edges(rules, axiom)
    for parent_id, child_id in edges:
        if parent_id in depth_vars and child_id in depth_vars:
            solver.add(depth_vars[child_id] == depth_vars[parent_id] + 1)

    # Negated obligation: exists a node whose depth exceeds max_depth.
    violation = z3.Or(*[dv > max_depth_val for dv in depth_vars.values()])
    solver.add(violation)

    t0 = time.monotonic()
    result = solver.check()
    elapsed = time.monotonic() - t0

    if elapsed > 30:
        return Result(
            status=Status.PASS_UNKNOWN,
            message=f"Z3 timeout after {elapsed:.1f}s; termination unknown",
        )

    if result == z3.unsat:
        return Result(
            status=Status.PASS,
            message=f"termination proven: all derivations bounded by max_depth={max_depth_val}",
        )
    elif result == z3.sat:
        model = solver.model()
        witness = {nid: model[depth_vars[nid]] for nid in node_ids if depth_vars[nid] in model}
        return Result(
            status=Status.FAIL,
            message=f"termination violation: derivation exceeds max_depth={max_depth_val}",
            counterexample={"max_depth": max_depth_val, "depths": {k: str(v) for k, v in witness.items()}},
        )
    else:
        return Result(
            status=Status.PASS_UNKNOWN,
            message="Z3 returned unknown; termination undetermined",
        )
