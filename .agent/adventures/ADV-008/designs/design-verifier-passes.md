# Verifier Passes — Design

## Overview

Three Z3-backed passes run *after* `ark verify` succeeds on a shape-grammar `.ark` file. They enforce:

1. **Termination** — derivation depth is statically bounded by `max_depth`; every expansion consumes depth.
2. **Determinism** — evaluation under the same seed is reproducible; no wall-clock / env / unordered set operations.
3. **Scope safety** — every op reads only attributes that are definitely in scope at that point.

Each pass is a standalone Python module invokable via CLI. They never modify Ark; they consume the IR produced by `tools/ir.py`.

## Target Files

- `shape_grammar/tools/verify/__init__.py` — package init + CLI dispatch.
- `shape_grammar/tools/verify/termination.py`
- `shape_grammar/tools/verify/determinism.py`
- `shape_grammar/tools/verify/scope.py`
- `shape_grammar/tests/test_verifier.py`

## Approach

### Termination pass

Builds Z3 model:
- Integer variable `depth(node)` for every rule-expansion node.
- Constraint: `depth(child) = depth(parent) + 1`.
- Constraint: `depth(axiom) = 0`.
- Obligation: `forall node: depth(node) <= max_depth` is valid, i.e. `exists node: depth(node) > max_depth` is UNSAT.

If any rule has a self-expansion without base case, Z3 returns a counter-example derivation that exceeds `max_depth`. Pass uses ADV-002's `PASS_OPAQUE` convention for loops whose bound is data-dependent (e.g. a `SplitOp` with `count: Int` field sourced from a user attr).

### Determinism pass

Obligations:
- Every `#process` body references only: `$data` fields, op inputs, or `SeededRng.fork(label)` where `label` is a literal string. No wall-clock calls, no env reads, no un-seeded randomness.
- Every operation's output ordering is a pure function of the scope + seed. Implemented by checking that no op is declared with `strategy: tensor` + `unordered: true` (no such construct in the grammar; assert its absence).
- Seed threading: every grammar has exactly one `$data seed: Int` field at the island level.

Method: structural check on IR + Z3 obligation `forall seed1, seed2: seed1 = seed2 => evaluation(seed1) = evaluation(seed2)` (modeled symbolically over operation invocation sequence).

### Scope pass

Obligations:
- For every op that reads `scope.get(attr_name)`, there exists an ancestor rule on the derivation path that has `scope.push({attr_name: _})`.
- For every op that writes `scope.push(...)`, the attrs written are type-consistent with the abstraction's declared scope type.

Method: symbolic path analysis over rule graph + Z3 check that the "attr is defined" predicate holds on every reachable path.

## CLI

```bash
python -m shape_grammar.tools.verify termination <spec.ark>
python -m shape_grammar.tools.verify determinism <spec.ark>
python -m shape_grammar.tools.verify scope <spec.ark>
python -m shape_grammar.tools.verify all <spec.ark>          # runs all three
```

Exit codes:
- 0: all passes `PASS` or `PASS_OPAQUE`.
- 1: a pass `FAIL`s (prints counter-example).
- 2: IR load error (usually Ark parse/verify already failed — user should run `ark verify` first).

## Dependencies

- Reuses `z3-solver` (Ark's dependency).
- Reuses ADV-002's `PASS_OPAQUE` convention for data-dependent unknowns.
- Reuses ADV-003's Z3 ordinal pattern for acyclicity checks on the rule graph.

## Target Conditions Covered

- TC-04a — termination pass passes on all 4 examples.
- TC-04b — determinism pass passes on all 4 examples.
- TC-04c — scope pass passes on all 4 examples.
- TC-04d — termination pass FAILs on a deliberate unbounded-derivation counterexample test.
