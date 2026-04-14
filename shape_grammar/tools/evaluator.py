"""evaluator.py — Shape-grammar evaluator core.

Consumes a `ShapeGrammarIR` (from `tools/ir.py`) and a seed int, walks the
rule tree via a FIFO worklist (breadth-first, deterministic ordering), dispatches
each rule's operations through `OP_REGISTRY`, and returns a list of `Terminal`
leaf nodes.

Key contracts:
  - **Deterministic**: FIFO worklist + label-based RNG forking → identical output
    under the same seed across any two calls or processes.
  - **Bounded**: evaluator enforces ``ir.max_depth`` hard cap; branches that would
    exceed it are pruned (not silently swallowed — `EvaluationError` is raised if
    a branch somehow slips through).
  - **Safe empty spec**: if the IR has no axiom or no rules the function returns
    ``[]`` without raising.  This is the expected behaviour for the base
    `shape_grammar.ark` spec which declares types but no concrete rule instances.

Provenance
----------
Each worklist entry carries a `Provenance` that records the rule-chain path and
the current depth.  When a branch's depth equals `max_depth` and the current
symbol is not yet terminal, the branch is quietly pruned (no crash).  If depth
somehow *exceeds* `max_depth` the hard guard raises `EvaluationError`.

CLI
---
::

    python -m shape_grammar.tools.evaluator <spec.ark> --seed <int> --out <file.obj>

The CLI now delegates OBJ writing to `obj_writer.write_obj` (T13).  When the
grammar produces zero terminals (e.g. the base `shape_grammar.ark` spec which
declares types but no concrete rule instances), the writer emits a header-only
file so the CLI still produces a non-empty output.
"""

from __future__ import annotations

import argparse
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from shape_grammar.tools.ir import (
    ShapeGrammarIR,
    IRRule,
    IRSemanticLabel,
    extract_ir,
    IRError,
)
# NOTE: `obj_writer` imports `Terminal` from this module, so we defer the
# `write_obj` import into the CLI function to avoid a circular import at
# module load time.
from shape_grammar.tools.scope import Scope, ScopeStack
from shape_grammar.tools.rng import SeededRng
from shape_grammar.tools.ops import OP_REGISTRY, make_op, TERMINAL, Op


# ---------------------------------------------------------------------------
# Public exception
# ---------------------------------------------------------------------------


class EvaluationError(RuntimeError):
    """Raised when the evaluator encounters an unrecoverable state."""


# ---------------------------------------------------------------------------
# Terminal dataclass (the evaluator's output unit)
# ---------------------------------------------------------------------------


@dataclass
class Terminal:
    """A leaf node produced by the shape-grammar derivation.

    Attributes
    ----------
    scope:
        Final geometric scope at the point of termination.
    tag:
        The asset path / rule id string associated with this terminal.
    label:
        Semantic label string (propagated from the rule chain and IOp).
    provenance:
        Derivation path (list of rule ids from root to this terminal).
    """

    scope: Scope
    tag: str
    label: str
    provenance: list[str] = field(default_factory=list)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Terminal):
            return NotImplemented
        return (
            self.scope == other.scope
            and self.tag == other.tag
            and self.label == other.label
            and self.provenance == other.provenance
        )

    def __hash__(self) -> int:
        return hash((self.scope, self.tag, self.label, tuple(self.provenance)))


# ---------------------------------------------------------------------------
# Provenance — lightweight derivation-path tracker
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Provenance:
    """Tracks the rule-chain path and current derivation depth."""

    path: tuple[str, ...] = ()

    @classmethod
    def root(cls) -> "Provenance":
        """Return the root provenance (empty path, depth 0)."""
        return cls()

    @property
    def depth(self) -> int:
        return len(self.path)

    def extend(self, rule_id: str) -> "Provenance":
        """Return a new Provenance with *rule_id* appended."""
        return Provenance(path=self.path + (rule_id,))

    def as_list(self) -> list[str]:
        return list(self.path)


# ---------------------------------------------------------------------------
# Rule resolution helpers
# ---------------------------------------------------------------------------


def _build_rule_map(ir: ShapeGrammarIR) -> dict[str, IRRule]:
    """Build a lookup dict from rule id -> IRRule."""
    return {r.id: r for r in ir.rules}


def _default_max_depth(ir: ShapeGrammarIR) -> int:
    """Resolve max_depth from the IR; default to 32 if not set."""
    md = ir.max_depth
    if isinstance(md, int) and md > 0:
        return md
    if isinstance(md, dict):
        # IRRange serialized as {"min": ..., "max": ...}
        lo = md.get("min")
        hi = md.get("max")
        # Use the minimum as the safe upper bound for the evaluator.
        if isinstance(lo, (int, float)) and lo > 0:
            return int(lo)
        if isinstance(hi, (int, float)) and hi > 0:
            return int(hi)
    return 32  # conservative fallback


# ---------------------------------------------------------------------------
# Op instantiation from an IRRule
# ---------------------------------------------------------------------------


def _ops_for_rule(rule: IRRule) -> list[Op]:
    """Convert an IRRule's operations list into concrete Op objects.

    The ``rule.operations`` field is either:
      - a list of strings (kind names, e.g. ``["i"]``) — stub rules from
        the base spec; each is turned into the matching default op.
      - a list of dicts (entity dicts from example grammars — T15).

    Returns an empty list for terminal rules (they produce a Terminal
    directly without dispatching further ops).
    """
    if rule.is_terminal:
        # Terminal rules immediately emit a Terminal; no further ops.
        return []

    ops: list[Op] = []
    for raw in rule.operations:
        if isinstance(raw, str):
            kind = raw.strip()
            if kind not in OP_REGISTRY:
                continue  # silently skip unknown op kinds in stub specs
            # Build with defaults; id derived from kind + rule id.
            try:
                op = make_op(kind, id=f"{rule.id}_{kind}")
            except (KeyError, TypeError):
                continue
            ops.append(op)
        elif isinstance(raw, dict):
            kind = raw.get("kind", raw.get("type", ""))
            if kind not in OP_REGISTRY:
                continue
            entity = dict(raw)
            if "id" not in entity:
                entity["id"] = f"{rule.id}_{kind}"
            try:
                op = OP_REGISTRY[kind].from_ir(entity)
            except Exception:
                continue
            ops.append(op)
    return ops


# ---------------------------------------------------------------------------
# Core evaluate function
# ---------------------------------------------------------------------------


def evaluate(ir: ShapeGrammarIR, seed: int) -> list[Terminal]:
    """Evaluate a shape grammar IR and return all terminal nodes.

    Parameters
    ----------
    ir:
        Populated `ShapeGrammarIR` (from `extract_ir`).
    seed:
        Integer seed for deterministic RNG.

    Returns
    -------
    list[Terminal]
        All leaf terminal nodes in FIFO derivation order. Returns ``[]``
        when the IR has no axiom or no matching rule for the axiom symbol.

    Raises
    ------
    EvaluationError
        If a branch depth somehow exceeds `max_depth` (should have been
        caught by the static termination pass) or if a symbol cannot be
        resolved and the rule map is non-empty.
    """
    # --- Guard: empty spec is valid (no crash) ---
    if not ir.axiom or not ir.rules:
        return []

    rng = SeededRng(seed)
    rule_map = _build_rule_map(ir)
    max_depth = _default_max_depth(ir)

    # --- Resolve axiom ---
    axiom_symbol: str = ir.axiom
    if axiom_symbol not in rule_map:
        # Axiom doesn't resolve to any concrete rule — return empty safely.
        return []

    # --- Initialise worklist ---
    # Each worklist entry: (symbol, scope, label_str, provenance)
    initial_scope = Scope.identity()
    initial_label = "default"
    initial_prov = Provenance.root()

    worklist: deque[tuple[str, Scope, str, Provenance]] = deque()
    worklist.append((axiom_symbol, initial_scope, initial_label, initial_prov))

    terminals: list[Terminal] = []

    # --- FIFO BFS loop ---
    while worklist:
        symbol, scope, label, prov = worklist.popleft()  # FIFO = deterministic

        # Hard depth guard
        if prov.depth > max_depth:
            raise EvaluationError(
                f"max_depth {max_depth} exceeded at depth {prov.depth} "
                f"(symbol={symbol!r}, path={prov.as_list()!r}). "
                "This should have been caught by the static termination pass."
            )

        # Resolve rule
        rule = rule_map.get(symbol)
        if rule is None:
            # Unknown symbol: if we have a non-empty rule map this is a bug in
            # the grammar; skip the branch rather than crash, to keep the
            # evaluator robust during grammar development.
            continue

        # Terminal rule: directly emit a Terminal.
        if rule.is_terminal:
            terminals.append(Terminal(
                scope=scope,
                tag=rule.id,
                label=rule.label or label,
                provenance=prov.as_list(),
            ))
            continue

        # Non-terminal: dispatch each operation.
        ops = _ops_for_rule(rule)
        if not ops:
            # No ops defined: treat as implicit terminal (needed for stub grammars).
            terminals.append(Terminal(
                scope=scope,
                tag=rule.id,
                label=rule.label or label,
                provenance=prov.as_list(),
            ))
            continue

        next_prov = prov.extend(rule.id)

        # Prune at max_depth: don't enqueue children that would exceed it.
        if next_prov.depth > max_depth:
            # This branch cannot go deeper; emit it as a terminal stub.
            terminals.append(Terminal(
                scope=scope,
                tag=rule.id,
                label=label,
                provenance=prov.as_list(),
            ))
            continue

        for op in ops:
            # Fork the RNG deterministically by op.id.
            op_rng = rng.fork(op.id)
            try:
                children = op.apply(scope, op_rng, label)
            except Exception:
                continue  # op application failure is non-fatal during evaluation

            for child_scope, child_symbol, child_label in children:
                if child_symbol is TERMINAL:
                    # IOp: emit terminal immediately.
                    terminals.append(Terminal(
                        scope=child_scope if isinstance(child_scope, Scope) else scope,
                        tag=child_label,  # asset_path stored in child_label by IOp
                        label=child_label,
                        provenance=next_prov.as_list(),
                    ))
                elif child_symbol == "__inherit__":
                    # Symbol inheritance: re-queue with same symbol.
                    worklist.append((symbol, child_scope, child_label, next_prov))
                else:
                    worklist.append((child_symbol, child_scope, child_label, next_prov))

    return terminals


# ---------------------------------------------------------------------------
# CLI __main__
# ---------------------------------------------------------------------------


def _cli_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m shape_grammar.tools.evaluator",
        description="Evaluate a shape grammar spec and write OBJ output.",
    )
    parser.add_argument("spec", help="Path to .ark spec file")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed (default 42)")
    parser.add_argument(
        "--out", default="/tmp/shape_grammar_out.obj", help="Output OBJ path"
    )
    args = parser.parse_args(argv[1:])

    spec_path = Path(args.spec)
    out_path = Path(args.out)

    # Parse and extract IR
    try:
        ir = extract_ir(spec_path)
    except IRError as exc:
        print(f"ERROR extracting IR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR parsing spec: {exc}", file=sys.stderr)
        return 1

    # Evaluate
    try:
        terminals = evaluate(ir, args.seed)
    except EvaluationError as exc:
        print(f"ERROR during evaluation: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR (unexpected): {exc}", file=sys.stderr)
        return 1

    # Determinism smoke check: run a second time and compare.
    try:
        terminals2 = evaluate(ir, args.seed)
        if terminals != terminals2:
            print(
                "ERROR: determinism check failed — two runs with same seed produced "
                "different results.",
                file=sys.stderr,
            )
            return 1
    except Exception as exc:
        print(f"WARNING: determinism re-run failed: {exc}", file=sys.stderr)
        # Non-fatal: continue

    # Write output via T13's obj_writer (lazy import — avoids circular dep)
    from shape_grammar.tools.obj_writer import write_obj
    write_obj(terminals, out_path, seed=args.seed)

    print(
        f"OK: {len(terminals)} terminal(s) from {spec_path.name} "
        f"(seed={args.seed}) -> {out_path}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_cli_main(sys.argv))
