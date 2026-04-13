# Codegen for Expressions & Predicates — Design

## Overview

Extend `R:/Sandbox/ark/tools/codegen/ark_codegen.py` so that:

1. Each `expression Foo { ... }` item emits a target-language function (Rust `fn`, C++ method,
   Protobuf RPC signature).
2. Each `predicate Bar { ... }` emits a target-language boolean function.
3. Pipe expressions inside `#process` bodies emit as inlined call chains or delegated calls
   to named `expression` functions, depending on whether the chain was declared or inline.

Current codegen structure: type maps at `R:/Sandbox/ark/tools/codegen/ark_codegen.py:21-45`;
RUST / CPP / PROTO entry points follow the pattern `gen_rust_entity`, `gen_rust_soa`,
`gen_cpp_entity`, `gen_proto_entity`. This adventure adds sibling functions `gen_rust_expression`,
`gen_rust_predicate`, and similarly for C++ and Proto.

## Language targets (open design question #2)

### Option A: Rust + C++ + Protobuf in v1
Match the existing codegen coverage.

**Pros**: complete. **Cons**: triples the codegen surface, increases test matrix.

### Option B (recommended): Rust-only v1, C++ and Protobuf deferred
Rust is the primary runtime target (see `R:/Sandbox/ark/Cargo.toml`). C++ / Proto are follow-up.

**Pros**: shippable faster; the decidable-subset Z3 work (design 04) is larger than codegen,
so keeping codegen tight makes the critical path manageable. **Cons**: follow-up adventure
needed; temporary asymmetry in codegen coverage.

**DECISION REQUIRED.** Default: **Option B**.

## Rust codegen

### Expression item

```ark
expression clamp { in: x: Float, lo: Float, hi: Float, out: Float, chain: x |> clamp-range(lo, hi) }
```

Emits:

```rust
#[inline]
pub fn clamp(x: f32, lo: f32, hi: f32) -> f32 {
    x.max(lo).min(hi)
}
```

The pipe chain is desugared at codegen time: `x |> clamp-range(lo, hi)` maps via
`EXPR_PRIMITIVES["clamp-range"]` (defined in `expression_primitives.py`, see design 03) to
`x.max(lo).min(hi)`.

### Predicate item

```ark
predicate is-recent { in: last_seen: Float, days: Float, check: (last_seen |> age) < days }
```

Emits:

```rust
#[inline]
pub fn is_recent(last_seen: f32, days: f32) -> bool {
    age(last_seen) < days
}
```

Note `-` in Ark names becomes `_` in Rust identifiers.

### Pipe inside a process body

```ark
class Player {
  $data last_seen: Float = 0.0
  #process[strategy: code]{
    score' = last_seen |> age |> clamp(0.0, 30.0)
  }
}
```

Emits into the process body:

```rust
self.score = clamp(age(self.last_seen), 0.0, 30.0);
```

The codegen walks the `Pipe` node, emitting nested calls right-to-left. Inline pipes are
**not** extracted into named functions — they inline at the call site. Named `expression`
items are emitted once and called by name.

### ParamRef emission

- `@n` → `self.n` or a local binding, depending on context
- `[a.b.c]` → `self.a.b.c` (dotted field access)
- `#items[3]` → `self.items[3]`
- `{expr}` → recursively emit expr

## C++ and Protobuf (deferred)

For v1 (Rust-only, per Option B), add stub functions `gen_cpp_expression` and
`gen_proto_expression` that raise `NotImplementedError("expression codegen for C++/Proto is
planned in ADV-00?, see designs/05_codegen.md")`. This keeps the dispatch table complete and
produces a useful error for users who try.

## Target Files

- `R:/Sandbox/ark/tools/codegen/ark_codegen.py` — add `gen_rust_expression`,
  `gen_rust_predicate`, `gen_rust_pipe_inline`, extend `gen_rust_process_body` to detect pipes
- `R:/Sandbox/ark/tools/codegen/expression_primitives.py` — NEW, shared with design 03
- `R:/Sandbox/ark/tests/test_codegen_expression.py` — NEW: unit tests asserting generated
  Rust snippets for each stdlib entry

## Target Conditions

- TC-018 — `python ark.py codegen specs/test_expression.ark --target rust` produces a valid
  `.rs` file containing one `pub fn` per declared expression
- TC-019 — Every v1 numeric stdlib expression round-trips: `.ark` → codegen → `cargo check`
  (or at least `rustc --edition 2021 --emit=metadata`) passes
- TC-020 — Every v1 text stdlib expression emits compilable Rust
- TC-021 — Every v1 predicate emits a `pub fn ... -> bool`
- TC-022 — Inline pipes inside process bodies emit correctly and the surrounding `#process`
  body still compiles
- TC-023 — C++ / Proto codegen raises a clear `NotImplementedError` pointing at the follow-up
  adventure (documents the scoping decision)

## Dependencies

- `01_dsl_surface.md`, `02_grammar_parser.md`, `03_stdlib_catalogue.md`

## Risks

- **Identifier mangling**: `text-to-lower` → `text_to_lower`. Must be deterministic and
  collision-free. Mitigation: one mangling function, used everywhere; a test asserts no
  two stdlib entries mangle to the same Rust identifier.
- **Pipe inlining complexity**: deeply nested pipes (>5 stages) produce long Rust
  expressions. Mitigation: for chains > 4 stages, emit a local `let` binding per stage.
- **`f32` vs `f64` drift**: Ark `Float` maps to `f32` (see `ark_codegen.py:21`). All stdlib
  numeric entries must agree. Mitigation: tests assert `f32` in generated output.

## Open Questions Flagged

1. **Language targets** — A (Rust+C+++Proto) vs B (Rust-only). Default: **B**. USER DECISION REQUIRED.
