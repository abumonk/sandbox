# Stdlib Catalogue — Design

## Overview

Port the Expressif function / predicate library into Ark stdlib as `.ark` declarations under
`R:/Sandbox/ark/dsl/stdlib/`. Each function is declared with input / output types and a
`strategy:` metadata key that tells codegen how to emit it (`code`, `verified`, `script`).

The existing stdlib lives at `R:/Sandbox/ark/dsl/stdlib/types.ark` (types only). This adventure
adds two new files: `expression.ark` (numeric / temporal / text / file functions) and
`predicate.ark` (boolean predicates).

## Scope for v1 (open design question #3)

Expressif's full library is large (~80 functions + ~30 predicates). Two options:

### Option A: Full parity (all categories)
Numeric + temporal + text + file-io + special. ~110 stdlib entries.

**Pros**: complete port, nothing deferred.
**Cons**: temporal functions require chrono-like runtime dependency; file-io touches host
filesystem and is hard to verify in Z3; large surface to test.

### Option B (recommended): Core subset for v1
Numeric + text + special + predicates. Temporal and file-io deferred to ADV-00?.

**Pros**: decidable in Z3 (no filesystem, no clock); smaller test surface; shippable in one
adventure; the deferred categories become a follow-up adventure with clean boundaries.
**Cons**: users must wait for full parity.

**DECISION REQUIRED.** Default: **Option B**.

## Catalogue — v1 core subset

### Numeric expressions (`dsl/stdlib/expression.ark`)

```ark
expression absolute { in: x: Float, out: Float, chain: x |> abs }
expression add      { in: x: Float, y: Float, out: Float, chain: x |> add(y) }
expression subtract { in: x: Float, y: Float, out: Float, chain: x |> sub(y) }
expression multiply { in: x: Float, y: Float, out: Float, chain: x |> mul(y) }
expression divide   { in: x: Float, y: Float, out: Float, chain: x |> div(y) }
expression ceiling  { in: x: Float, out: Float, chain: x |> ceil }
expression floor    { in: x: Float, out: Float, chain: x |> floor }
expression round    { in: x: Float, digits: Int, out: Float, chain: x |> round-to(digits) }
expression power    { in: x: Float, exp: Float, out: Float, chain: x |> pow(exp) }
expression clamp    { in: x: Float, lo: Float, hi: Float, out: Float, chain: x |> clamp-range(lo, hi) }
expression negate   { in: x: Float, out: Float, chain: x |> neg }
```

### Text expressions

```ark
expression text-to-lower   { in: s: String, out: String, chain: s |> str-lower }
expression text-to-upper   { in: s: String, out: String, chain: s |> str-upper }
expression text-trim       { in: s: String, out: String, chain: s |> str-trim }
expression text-length     { in: s: String, out: Int, chain: s |> str-len }
expression text-pad-right  { in: s: String, n: Int, ch: String, out: String, chain: s |> str-pad-right(n, ch) }
expression text-pad-left   { in: s: String, n: Int, ch: String, out: String, chain: s |> str-pad-left(n, ch) }
expression text-remove-chars { in: s: String, chars: String, out: String, chain: s |> str-remove-chars(chars) }
expression text-substring  { in: s: String, start: Int, len: Int, out: String, chain: s |> str-substring(start, len) }
expression text-replace    { in: s: String, old: String, new: String, out: String, chain: s |> str-replace(old, new) }
```

### Special / null-handling

```ark
expression null-to-zero  { in: x: Float, out: Float, chain: x |> default-float(0.0) }
expression null-to-value { in: x: Float, v: Float, out: Float, chain: x |> default-float(v) }
expression neutral       { in: x: Float, out: Float, chain: x |> identity-fn }
```

### Predicates (`dsl/stdlib/predicate.ark`)

```ark
predicate is-empty     { in: s: String, check: s |> str-len == 0 }
predicate is-null      { in: x: Float, check: x |> is-null-float }
predicate starts-with  { in: s: String, prefix: String, check: s |> str-starts-with(prefix) }
predicate ends-with    { in: s: String, suffix: String, check: s |> str-ends-with(suffix) }
predicate contains     { in: s: String, needle: String, check: s |> str-contains(needle) }
predicate matches-regex{ in: s: String, pattern: String, check: s |> str-matches(pattern) }
predicate is-within    { in: x: Float, lo: Float, hi: Float, check: x >= lo and x < hi }
predicate is-equal-to  { in: x: Float, y: Float, check: x == y }
predicate is-greater-than { in: x: Float, y: Float, check: x > y }
predicate is-less-than    { in: x: Float, y: Float, check: x < y }
```

## Primitive shims

The `chain:` body references primitive operators like `abs`, `str-lower`, `str-len`, `pow`.
These are the **target-language-provided** primitives that codegen maps to Rust / C++ /
Protobuf. They do NOT need a `.ark` declaration — they live in the codegen type map. This
design proposes a new file `R:/Sandbox/ark/tools/codegen/expression_primitives.py` that holds:

```python
EXPR_PRIMITIVES = {
    "abs":         {"rust": "f32::abs",            "cpp": "std::fabs",       "kind": "unary"},
    "str-lower":   {"rust": ".to_lowercase()",     "cpp": ".to_lower()",     "kind": "method"},
    "str-len":     {"rust": ".len() as i32",       "cpp": ".Len()",          "kind": "method"},
    # ...
}
```

Codegen task (design 05) consumes this map.

## Target Files

- `R:/Sandbox/ark/dsl/stdlib/expression.ark` — NEW: ~23 expression declarations
- `R:/Sandbox/ark/dsl/stdlib/predicate.ark` — NEW: ~10 predicate declarations
- `R:/Sandbox/ark/tools/codegen/expression_primitives.py` — NEW: primitive → target map
- `R:/Sandbox/ark/tools/parser/ark_parser.py` — import resolution for the new stdlib files
  (the import mechanism already exists per ImportResolutionTask, just needs the new file
  names registered)

## Target Conditions

- TC-009 — `import stdlib.expression` resolves and all declared expressions are available in
  the AST's `classes_index`-equivalent lookup (a new `expression_index` / `predicate_index`)
- TC-010 — Every v1 numeric expression has a valid target-language mapping in
  `EXPR_PRIMITIVES`
- TC-011 — Every v1 text expression has a valid target-language mapping
- TC-012 — Every v1 predicate parses with `check:` producing a `Bool`-typed AST node

## Dependencies

- `01_dsl_surface.md` — requires `expression` / `predicate` item syntax
- `02_grammar_parser.md` — requires grammars + AST for those items

## Risks

- **Primitive naming drift**: `abs` in Ark stdlib vs `f32::abs` in Rust — codegen must map
  correctly. Mitigation: the primitive table is the single source of truth, and a test
  iterates all v1 stdlib entries and asserts each referenced primitive has an entry.
- **Type polymorphism**: `abs` works on `Int` and `Float`. v1 takes the pragmatic path of
  declaring separate entries or using a generic type parameter only where the existing Ark
  type system supports it (named generics exist in `types.ark` but only one-level). For v1,
  declare `Float` variants; `Int` variants are a follow-up.

## Open Questions Flagged

1. **Stdlib scope** — A (full) vs B (core subset). Default: **B**. USER DECISION REQUIRED.
2. **Int variants** — emit parallel `*-int` entries for numeric ops, or wait for generics?
   Default: wait. Covered in follow-up adventure.
