# Example Specs & Test Strategy — Design

## Overview

Deliver runnable `.ark` specs under `R:/Sandbox/ark/specs/` that exercise every new feature,
plus a unit test suite under `R:/Sandbox/ark/tests/` mirroring Expressif's own coverage
(from https://github.com/Seddryck/Expressif/tree/main/Expressif.Testing).

Existing test conventions (see `R:/Sandbox/ark/tests/conftest.py`):
- Uses pytest
- `parse_src` fixture parses source strings → AST dict
- `parse_file` fixture parses files
- Test files follow `test_parser_*.py`, `test_verify_*.py` pattern
- Rust tests: `cargo test -p ark-dsl` (from `R:/Sandbox/ark/`)

## Example specs

### `R:/Sandbox/ark/specs/test_expression.ark`

Minimal end-to-end: declares a user expression, a user predicate, uses both inside a class
process body, and has a `verify` block that exercises both the expression and the predicate.

```ark
import stdlib.types
import stdlib.expression
import stdlib.predicate

expression normalize_name {
  in: name: String
  out: String
  chain: name |> text-trim |> text-to-lower
}

predicate is_valid_name {
  in: name: String
  check: (name |> text-length) > 0 and (name |> text-length) < 64
}

class Player {
  $data name: String = ""
  $data score: Float [0..100] = 0.0

  @in{ raw_name: String, delta: Float }

  #process[strategy: code]{
    pre: raw_name |> is_valid_name
    name' = raw_name |> normalize_name
    score' = (score + delta) |> clamp(0.0, 100.0)
    post: name' |> text-length > 0
  }

  @out[]{ name': String, score': Float }
}

verify PlayerExpression {
  check score_bounded: score >= 0 and score <= 100
  check normalize_is_lower: for_all String as n: (n |> normalize_name |> text-to-upper) != n
                            or (n |> text-length) == 0
}
```

### `R:/Sandbox/ark/specs/examples/expressif_examples.ark`

Ports the headline examples from the Expressif README:

- `@myVar |> text-to-lower |> text-pad-right(@count, "*")`
- `"starts-with(Nik) |AND ends-with(sla)"` → `(name |> starts-with("Nik")) and (name |> ends-with("sla"))`
- Numeric interval check: `x |> is-within(0.0, 20.0)`

## Unit tests

### `R:/Sandbox/ark/tests/test_parser_pipe.py`

Tests (Python parser):
- bare pipe parses: `x |> f`
- chained pipe is left-associative: `x |> f |> g` → `Pipe(Pipe(x,f),g)` logically
- pipe with extra args: `x |> f(y, z)`
- pipe mixes with arithmetic precedence: `x |> f + 1` → `(x |> f) + 1`
- kebab-case inside stages: `s |> text-to-lower`
- kebab outside stages is rejected: `a = text-to-lower` → parse error (must use pipe form)
- nested refs: `x |> clamp({a + b}, 100)`
- `@var`, `[a.b]`, `#items[0]` param refs tagged correctly

### `R:/Sandbox/ark/tests/test_parser_expression_items.py`

- `expression Foo { in: x: Float, out: Float, chain: x |> abs }` parses as `Item::Expression`
- `predicate Bar { in: s: String, check: s |> starts-with("x") }` parses as `Item::Predicate`
- Missing `chain:` → error with line:col
- Missing `out:` on expression → error
- `check:` that doesn't return Bool → deferred to verify step, but warn in parser

### `R:/Sandbox/ark/tests/test_stdlib_expression.py`

- `import stdlib.expression` resolves all entries
- Every declared expression has a matching `EXPR_PRIMITIVES` entry
- No two expressions mangle to the same Rust identifier

### `R:/Sandbox/ark/tests/test_verify_expression.py`

- `verify` block referencing a user expression translates to Z3 without error
- Tautology check on a simple numeric chain returns PASS
- Unknown pipe stage → clear error listing available stages

### `R:/Sandbox/ark/tests/test_verify_predicate.py`

- Predicate satisfiability check (`check sat: is_valid_name`) returns `sat` with a witness
- Predicate tautology check on `x > 0 or x <= 0` returns `PASS_TAUTOLOGY`

### `R:/Sandbox/ark/tests/test_codegen_expression.py`

- Each v1 numeric expression produces expected Rust `pub fn`
- Each v1 text expression produces expected Rust `pub fn`
- Predicate produces `pub fn ... -> bool`
- Pipe inside process body inlines correctly
- C++ / Proto raise `NotImplementedError` with the expected message

### `R:/Sandbox/ark/tests/test_pipeline_expression.py`

End-to-end: `python ark.py pipeline specs/test_expression.ark --target rust` exits 0 and
produces a `.rs` file containing `pub fn normalize_name`, `pub fn is_valid_name`, and the
existing `struct Player`.

### Rust-side parser tests

In `R:/Sandbox/ark/dsl/src/parse.rs` (inline `#[cfg(test)] mod tests`):

- `parse_ark_file("expression Foo { in: x: Float, out: Float, chain: x |> abs }")` → Ok with
  `Item::Expression(ExpressionDef { name: "Foo", .. })`
- Same for predicate
- Pipe expression round-trips through `ast_to_json` / `json_to_ast`

Run via `cargo test -p ark-dsl` from `R:/Sandbox/ark/`.

## Target Files

- `R:/Sandbox/ark/specs/test_expression.ark` — NEW
- `R:/Sandbox/ark/specs/examples/expressif_examples.ark` — NEW
- `R:/Sandbox/ark/tests/test_parser_pipe.py` — NEW
- `R:/Sandbox/ark/tests/test_parser_expression_items.py` — NEW
- `R:/Sandbox/ark/tests/test_stdlib_expression.py` — NEW
- `R:/Sandbox/ark/tests/test_verify_expression.py` — NEW
- `R:/Sandbox/ark/tests/test_verify_predicate.py` — NEW
- `R:/Sandbox/ark/tests/test_codegen_expression.py` — NEW
- `R:/Sandbox/ark/tests/test_pipeline_expression.py` — NEW
- `R:/Sandbox/ark/dsl/src/parse.rs` — EXTEND inline `tests` module

## Target Conditions

- TC-024 — `R:/Sandbox/ark/specs/test_expression.ark` parses, verifies, and codegens end-to-end
  via `python ark.py pipeline specs/test_expression.ark --target rust`
- TC-025 — All new pytest files pass under `pytest R:/Sandbox/ark/tests/ -q`
- TC-026 — `cargo test -p ark-dsl` passes all new Rust AST tests
- TC-027 — `specs/examples/expressif_examples.ark` parses cleanly as a documentation example
- TC-028 — Total test coverage for expression / predicate code paths is >= 80% line coverage
  (measured via `coverage run -m pytest tests/test_*expression*.py tests/test_*predicate*.py`)

## Dependencies

- All of 01-05 (this design validates every other design)

## Risks

- **Rust test compilation dependency**: `cargo check` on generated Rust may require the
  runtime crate scaffold to be buildable. Mitigation: use `rustc --crate-type=lib` on the
  single generated file with stub type aliases for missing imports.
- **Coverage target drift**: 80% is a floor, not a ceiling. If a primitive is hard to cover
  (e.g., opaque regex), skip with documented rationale rather than gaming the metric.
