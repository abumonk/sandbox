# Z3 Verification for Expressions & Predicates — Design

## Overview

Extend `R:/Sandbox/ark/tools/verify/ark_verify.py` to translate the new AST nodes
(`Pipe`, `ParamRef`, `ExpressionDef`, `PredicateDef`) into Z3 SMT formulas so that:

1. `verify` blocks can `check` expression chains for type-safety and range satisfaction
2. Predicates can be checked for satisfiability (`exists input. check(input) = true`)
3. Process bodies that use named expressions get their piped transforms inlined as
   SMT function applications
4. Temporal / file-io primitives that cannot be modeled in pure SMT are marked `opaque`
   and skipped with an explicit warning, rather than failing silently

The current translator lives at `R:/Sandbox/ark/tools/verify/ark_verify.py:69-120` (`translate_expr`).
It dispatches on `expr.kind` for each supported node. We add two new kinds and two new
top-level registrations.

## Open design question #4 — Z3 coverage

Two strategies:

### Option A: Full SMT coverage
Translate every Expressif primitive into Z3, including strings (Z3 has a string theory),
temporal (modeled as Real for "seconds since epoch"), and file-io (stubbed as uninterpreted
functions).

**Pros**: complete verification of everything the user writes.
**Cons**: Z3 string theory is slow and incomplete; temporal modeling leaks host-time semantics;
file-io as UF is technically sound but practically useless.

### Option B (recommended): Decidable subset
- Numeric functions → native Z3 Real / Int arithmetic (decidable, fast).
- Text length / equality → Z3 string theory (supported but bounded).
- Regex / substring → **opaque**: translate as an uninterpreted function `str_matches(s, p)`
  where the verifier reports `unknown` or `PASS_ASSUMED` rather than `sat`.
- Temporal / file-io → **opaque**.

**Pros**: fast, honest about its limits, easy to extend.
**Cons**: some user checks return `unknown` — but that's already accepted for temporal BMC
(see `TemporalBMCTask` in `ark/CLAUDE.md` — returns `PASS_BOUNDED/FAIL/UNKNOWN`).

**DECISION REQUIRED.** Default: **Option B** — aligns with the existing precedent
(`PASS_BOUNDED` / `UNKNOWN` for temporal BMC) and avoids a Z3 performance trap.

## Translation rules

### Pipe

A `Pipe(head, [stage1, stage2, ...])` desugars left-to-right:

```python
def translate_pipe(expr, syms, expr_registry):
    val = translate_expr(expr["head"], syms)
    for stage in expr["stages"]:
        val = apply_stage(val, stage, syms, expr_registry)
    return val
```

`apply_stage` looks up the stage name in `expr_registry` (the set of loaded `ExpressionDef`
items from stdlib + user code). If the stage is a **native numeric primitive**, it is inlined
as Z3 arithmetic. If it is a **user-defined expression**, its `chain:` is recursively
translated with the incoming value bound to the expression's first input. If it is an
**opaque** primitive (regex, temporal, file-io), Z3 uninterpreted function symbols are used:

```python
opaque_str_matches = Function("str_matches", StringSort(), StringSort(), BoolSort())
```

### ParamRef

- `Var("@n")` → translates identically to `Ident("n")` (goes through `SymbolTable.get`).
  The sigil is purely syntactic distinction at parse time; semantics are the same.
- `Prop([a, b, c])` → `syms.get("a.b.c")` (the existing path handling already supports this).
- `Idx("#items", 3)` → uninterpreted array `items[3]`; Z3 `Select(Array(items), IntVal(3))`.
- `Nested(expr)` → recursively translate.

### ExpressionDef registration

On `verify_file` entry, scan all `Item::Expression(def)` items (including imported stdlib)
and register them in `expr_registry`. When `translate_pipe` encounters a stage name matching
a registered expression, it inlines via alpha-renaming of the expression's inputs.

### PredicateDef in verify blocks

```ark
verify Players {
  check recent_players: exists p. is-recent(p.last_seen) = true
}
```

The `is-recent` call is resolved against `pred_registry`, expanded, and its `check:`
substituted into the Z3 assertion.

### Satisfiability check for predicates

A new `verify` check kind: `check satisfiable: is-recent`. Translates to
`Solver.add(Not(is_recent.check))` with assertion: if `unsat`, the predicate is **always
true** (tautology); if `sat`, there exists an input falsifying it (normal predicate).
Alternatively `check tautology: is-recent` for tautology checking.

## Target Files

- `R:/Sandbox/ark/tools/verify/ark_verify.py` — extend `translate_expr` dispatch; add
  `translate_pipe`, `translate_param_ref`, `build_expr_registry`, `inline_expression_def`
- `R:/Sandbox/ark/tools/verify/expression_smt.py` — NEW: numeric / text primitive → Z3
  mapping; opaque function declarations
- `R:/Sandbox/ark/tests/test_verify_expression.py` — NEW: unit tests for pipe translation
- `R:/Sandbox/ark/tests/test_verify_predicate.py` — NEW: predicate satisfiability tests

## Target Conditions

- TC-013 — `python ark.py verify specs/test_expression.ark` resolves a chain of numeric
  primitives into Z3 and reports `PASS` when the `check` is satisfiable
- TC-014 — A predicate `check:` expression translates to Z3 and a `verify` block can assert
  it against test inputs
- TC-015 — Opaque primitives (regex, temporal, file-io) produce `UNKNOWN`/`PASS_OPAQUE`
  rather than crashing or silently passing
- TC-016 — User-defined `expression Foo { ... }` can be called from a process body and the
  verifier inlines its chain for Z3 translation
- TC-017 — Referencing an unknown stage name in a pipe produces an error that pinpoints the
  stage and lists valid candidates

## Dependencies

- `01_dsl_surface.md`, `02_grammar_parser.md`, `03_stdlib_catalogue.md`

## Risks

- **Z3 string theory performance**: even for simple `str.len`, Z3 can be slow. Mitigation:
  bound string length in verification contexts via assumptions, or fall back to opaque.
- **Expression inlining loops**: a user-defined expression that references itself (direct
  or mutual recursion) causes infinite inlining. Mitigation: cycle detection in
  `build_expr_registry` → reject with a clear error.
- **Silent opaque**: if too many primitives are opaque, users lose trust in `verify`. Print
  a summary: `N checks: 5 PASS, 2 UNKNOWN, 3 PASS_OPAQUE (regex, temporal)`.

## Open Questions Flagged

1. **Z3 coverage** — A (full) vs B (decidable subset + opaque). Default: **B**. USER DECISION REQUIRED.
