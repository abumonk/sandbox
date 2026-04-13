# DSL Surface for Expression & Predication — Design

## Overview

Expressif (https://github.com/Seddryck/Expressif) models **two** small value-level DSLs:

1. **Expression** — left-to-right scalar pipelines: `"@x | text-to-lower | text-to-pad-right(@n, *)"`.
   Each stage is a unary function; the left operand flows into the first argument slot, additional
   arguments are literals, `@variables`, `[object-props]`, `#collection-idx`, or nested `{...}` calls.
2. **Predicate** — boolean combinators: `"starts-with(Nik) |AND ends-with(sla) |OR empty-or-null"`
   with `!` negation and `{...}` grouping. Predicates operate on a single subject value.

This document defines how these forms are **embedded into Ark DSL** so `.ark` specs can express
value transformations declaratively and the existing pipeline (parse -> verify -> codegen) can
target them. Concept source: `R:/Sandbox/.agent/adventures/ADV-001/manifest.md` lines 12-41.

The current Ark expression grammar (`R:/Sandbox/ark/dsl/grammar/ark.pest:145-192`,
`R:/Sandbox/ark/tools/parser/ark_grammar.lark:158-186`) already supports:

- precedence-climbed arithmetic / comparison / boolean
- `fn_call` via `path_call_expr` / `fn_call` rule
- dotted paths, literals, arrays

What it does **not** yet support:

- A pipeline operator (`|`) that threads a value through multiple unary functions
- Expressif-style parameter-reference classes beyond bare identifiers (`@var`, `[prop]`, `#idx`, `{nested}`)
- First-class predicate combinators that are **structurally distinct** from boolean expressions
  so that a pipeline (`subject |> chain`) followed by a predicate (`is-matching pat`) can be
  type-checked as a single unit rather than as a generic arithmetic tree

## Embedding model (open design question #1)

The manifest explicitly defers this decision. Two viable shapes:

### Option A: Top-level `expression` / `predicate` items

Adds two new top-level keywords to the grammar:

```ark
expression AgeScore {
  in:  last_seen: DateTime
  out: Int
  chain: last_seen | age | clamp(0, 30)
}

predicate IsRecent {
  in:  last_seen: DateTime
  chain: last_seen | age
  check: is-within [0;14[
}
```

**Pros**

- Reusable — a named `expression` can be referenced from any `#process` body or `invariant`
- Clean Z3 surface: each item maps to a single SMT function declaration
- Codegen can emit one Rust function / C++ method per expression, and call it from process bodies

**Cons**

- Two new top-level keywords → extends `item` rule in both grammars
- Users have to declare before use — slightly more verbose for one-shot usage

### Option B: Inline inside `#process` / `invariant` only

Treat the pipe operator as an expression-level infix:

```ark
class Player {
  #process[]{
    score' = last_seen | age | clamp(0, 30)
    requires: (name | text-to-lower | starts-with "nik")
  }
  invariant: last_seen | age | is-within [0;14[
}
```

**Pros**

- Smaller grammar diff — only a new operator rule at the top of `or_expr`
- No new top-level vocabulary

**Cons**

- No reuse: the same chain must be re-typed everywhere
- Z3 translation has to inline the chain at every use site
- Ambiguity with bitwise-or `|` if Ark ever grows one

### Option C (recommended): Both

Allow both forms. The top-level item is just sugar for a named lambda; the inline form desugars
to an anonymous lambda at the use site. Recommendation with justification: **Option C** — the
top-level form unblocks reuse and verification-friendly codegen, while inline form keeps simple
cases readable. Grammar cost is small because both forms share the same underlying chain parser.

**DECISION REQUIRED BEFORE IMPLEMENTATION.** The default adopted by this plan is Option C.

## Syntax proposal (Option C concrete)

### Pipe operator

Introduce `|>` as the pipe operator (NOT bare `|`, because `|` collides with existing `or_expr`
in some potential future bitwise extension and visually hides behind `||`). The shell-like
`|>` also matches F#, Elixir, OCaml conventions which Ark users are likely to recognize.

```
chain_expr = { pipe_head ~ ("|>" ~ pipe_stage)* }
pipe_head  = _{ atom }
pipe_stage = { ident ~ call_tail? }   // stage is a function name, optionally with extra args
```

The left operand of each `|>` becomes the **implicit first argument** of the stage. Additional
arguments go in `call_tail`. Example: `x |> clamp(0, 30)` desugars to `clamp(x, 0, 30)`.

### Parameter reference classes (Expressif compat)

Expressif distinguishes four reference forms. Ark already has dotted paths and bare idents. We
add explicit sigils so the parser can tag the reference kind in the AST:

| Expressif | Ark form | AST kind |
|-----------|----------|----------|
| `@variable` | `@variable` (already reserved in `@in` — reuse as **variable reference** in expression context) | `ParamRef::Var` |
| `[object.prop]` | `[path.prop]` | `ParamRef::Prop` |
| `#collection[idx]` | `#name[idx]` | `ParamRef::Idx` |
| `{nested()}` | `{nested_expr}` | `ParamRef::Nested` |
| literal | bare literal (number/string/bool) | `Expr::Literal` |

**Collision risk**: `@` is currently the `@in` / `@out` prefix at the item level but NOT inside
expressions, so repurposing `@ident` as a variable reference inside chain expressions is safe.
The grammar distinguishes by context: inside `expression` / `predicate` / inside a `|>`
pipe-stage argument position. The Rust parser tracks this via a rule alias, not a mode switch.

### Predicate combinators

Expressif uses `|AND`, `|OR`, `|XOR` pipe-prefixed boolean ops and `!` for negation. Ark
already has `and`, `or`, `not`. To avoid splitting vocabulary, **predicates reuse Ark's existing
boolean operators** — but the `check:` clause inside a `predicate` item must evaluate to a
`Bool` (statically checked). This means `predicate` items are NOT a new expression sub-language;
they are expressions whose return type is constrained to `Bool`.

```ark
predicate IsNikSomething {
  in: name: String
  check: (name |> text-to-lower |> starts-with("nik"))
       and (name |> ends-with("sla"))
}
```

## Target Files

- `R:/Sandbox/ark/dsl/grammar/ark.pest` — add `pipe_expr`, `param_ref`, `expression_def`,
  `predicate_def`, thread `|>` into precedence climbing above `or_expr` (or equal precedence,
  TBD during grammar task)
- `R:/Sandbox/ark/tools/parser/ark_grammar.lark` — mirror Rust changes
- `R:/Sandbox/ark/dsl/src/lib.rs` — extend `Expr` enum with `Pipe(Box<Expr>, Vec<PipeStage>)`
  and `ParamRef(RefKind, String)`; add `Item::Expression(ExpressionDef)` and
  `Item::Predicate(PredicateDef)`
- `R:/Sandbox/ark/dsl/src/parse.rs` — transformer rules for new nodes
- `R:/Sandbox/ark/tools/parser/ark_parser.py` — mirror the Python AST with `{"expr": "pipe", ...}`
  and `{"expr": "param_ref", ...}` node shapes
- `R:/Sandbox/ark/docs/DSL_SPEC.md` — append `## Expression and Predicate subsystem` section

## Target Conditions (feed into manifest TC table)

- TC-001 — `.ark` files can declare top-level `expression Name { in: ..., out: T, chain: ... }`
  items and the Rust parser emits `Item::Expression(ExpressionDef)` for them.
- TC-002 — `.ark` files can declare top-level `predicate Name { in: ..., check: ... }` items
  where `check` evaluates to `Bool`.
- TC-003 — The `|>` operator can be used inside any expression context (assignment rhs,
  invariant, pre/post, expression item chain) and parses as left-associative.
- TC-004 — Parameter references `@var`, `[prop.path]`, `#name[idx]`, `{nested}` parse into
  tagged AST nodes distinguishable from plain identifiers.
- TC-005 — The Python (`ark_parser.py`) and Rust (`parse.rs`) parsers produce equivalent JSON
  AST for all expression / predicate forms (round-trip parity).

## Dependencies

None — this is the foundational design. All other designs reference this one.

## Risks

- **Grammar ambiguity**: `[...]` is already used for `array_expr`, `meta_brackets`, constraints,
  and `@out[...]`. Adding `[prop.path]` param refs must not conflict. Mitigation: require
  dotted content `[IDENT ("." IDENT)+]` for prop refs (single-ident stays `array_expr`) OR
  use a distinct sigil (`$[prop]`). Decide during grammar task (Option decision).
- **`@` sigil overload**: inside chain stage args, `@name` is a variable ref; at item level,
  `@in` / `@out` are port primitives. Disambiguation is positional — no runtime cost.
- **Operator precedence of `|>`**: must be LOWER than function call (so `x |> f(y)` parses as
  `pipe(x, call(f,y))`) but HIGHER than comparison (so `x |> f > 0` is `(pipe x f) > 0`).

## Open Questions Flagged

1. **Embedding model** — Option A / B / C above. Default: **C**. USER DECISION REQUIRED.
2. **Prop-ref sigil** — bare `[x.y]` vs `$[x.y]` vs other. Default: bare `[x.y.z]` (dotted only),
   leaving single-ident `[x]` to remain an array literal.
3. **`|>` vs `|`** — default `|>` for readability. Only bikeshed if user prefers bare `|`.
