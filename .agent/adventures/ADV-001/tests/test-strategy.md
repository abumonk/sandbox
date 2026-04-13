# ADV-001 Test Strategy — Expressif Expression & Predication System

## Overview

This document maps every target condition (TC-001 through TC-030) from the ADV-001 manifest
to specific test files, test functions, proof commands, and test runners. Tests are grouped
by subsystem to match the Ark project's existing conventions.

### Conventions (aligned with `R:/Sandbox/ark/tests/conftest.py`)

- **pytest** is the primary test runner for Python code
- Fixtures `parse_src` (source string -> AST dict) and `parse_file` (file path -> AST dict) are session-scoped in `conftest.py`
- Test files follow `test_{subsystem}_{feature}.py` naming
- Helper functions prefixed with `_` (e.g., `_cls()`, `_process_body()`) wrap boilerplate
- AST assertions use plain dict comparisons against JSON-round-tripped output
- **cargo test** runs Rust-side tests via `cargo test -p ark-dsl`
- All test files live under `R:/Sandbox/ark/tests/`
- All commands assume `cd R:/Sandbox/ark` as working directory

---

## Tests by Subsystem

### 1. Parser Tests

#### `tests/test_parser_pipe.py` (pytest)

| TC | Test Function | Description |
|----|--------------|-------------|
| TC-003 | `test_bare_pipe_parses` | `x \|> f` produces `Pipe` AST node |
| TC-003 | `test_chained_pipe_left_associative` | `x \|> f \|> g` is left-associative |
| TC-003 | `test_pipe_with_extra_args` | `x \|> f(y, z)` passes extra args |
| TC-003 | `test_pipe_precedence_with_arithmetic` | `x \|> f + 1` parses as `(x \|> f) + 1` |
| TC-004 | `test_var_ref_at_sigil` | `@var` produces `ParamRef::Var` |
| TC-004 | `test_prop_ref_bracket_dotted` | `[a.b.c]` produces `ParamRef::Prop` |
| TC-004 | `test_idx_ref_hash_sigil` | `#items[0]` produces `ParamRef::Idx` |
| TC-004 | `test_nested_ref_braces` | `{a + b}` produces `ParamRef::Nested` |
| TC-006 | `test_kebab_inside_pipe` | `s \|> text-to-lower` accepted inside pipe stage |
| TC-006 | `test_kebab_outside_pipe_errors` | `a = text-to-lower` rejected outside pipe |

**Proof command:**
```bash
cd R:/Sandbox/ark && pytest tests/test_parser_pipe.py -q
```

#### `tests/test_parser_expression_items.py` (pytest)

| TC | Test Function | Description |
|----|--------------|-------------|
| TC-001 | `test_expression_item_parses` | `expression Foo { in: ..., out: ..., chain: ... }` -> `Item::Expression` |
| TC-002 | `test_predicate_item_parses` | `predicate Bar { in: ..., check: ... }` -> `Item::Predicate` |
| TC-007 | `test_expression_all_fields_populated` | All fields (name, inputs, output, chain) present in AST |
| TC-007 | `test_predicate_all_fields_populated` | All fields (name, inputs, check) present in AST |
| TC-008 | `test_missing_chain_clause_errors` | Missing `chain:` -> `ArkParseError` with file:line:col |
| TC-008 | `test_missing_out_clause_errors` | Missing `out:` on expression -> error with location |
| TC-008 | `test_malformed_predicate_errors` | Malformed predicate -> error with location |

**Proof command:**
```bash
cd R:/Sandbox/ark && pytest tests/test_parser_expression_items.py -q
```

#### Parser parity (TC-005): pytest + cargo test

| TC | Test Function | File | Runner |
|----|--------------|------|--------|
| TC-005 | `test_python_rust_parity_expression` | `tests/test_parser_pipe.py` | pytest |
| TC-005 | `test_expression_def_parse` | `dsl/src/parse.rs` (inline `#[cfg(test)]`) | cargo test |

**Proof command:**
```bash
cd R:/Sandbox/ark && cargo test -p ark-dsl && pytest tests/test_parser_pipe.py -q
```

---

### 2. Stdlib Tests

#### `tests/test_stdlib_expression.py` (pytest)

| TC | Test Function | Description |
|----|--------------|-------------|
| TC-009 | `test_import_stdlib_expression_resolves` | `import stdlib.expression` populates expression index |
| TC-009 | `test_import_stdlib_predicate_resolves` | `import stdlib.predicate` populates predicate index |
| TC-010 | `test_numeric_primitives_complete` | Every v1 numeric expression has a valid `EXPR_PRIMITIVES` entry |
| TC-011 | `test_text_primitives_complete` | Every v1 text expression has a valid `EXPR_PRIMITIVES` entry |
| TC-012 | `test_predicates_bool` | Every v1 predicate parses with Bool-typed `check:` |

**Proof command:**
```bash
cd R:/Sandbox/ark && pytest tests/test_stdlib_expression.py -q
```

---

### 3. Verify Tests

#### `tests/test_verify_expression.py` (pytest)

| TC | Test Function | Description |
|----|--------------|-------------|
| TC-013 | `test_numeric_pipe_verifies` | Numeric pipe chain translates to Z3 and returns PASS |
| TC-015 | `test_opaque_primitive_pass_opaque` | Opaque primitives (regex, temporal, file-io) report PASS_OPAQUE |
| TC-016 | `test_user_expression_inline` | User-defined expressions inline in verifier when called from process bodies |
| TC-017 | `test_unknown_stage_error` | Unknown pipe stage produces error with fuzzy suggestions |

**Proof command:**
```bash
cd R:/Sandbox/ark && pytest tests/test_verify_expression.py -q
```

#### `tests/test_verify_predicate.py` (pytest)

| TC | Test Function | Description |
|----|--------------|-------------|
| TC-014 | `test_predicate_check_in_z3_verify` | Predicate `check:` expressions participate in Z3 verify blocks |
| TC-014 | `test_predicate_satisfiability` | Predicate satisfiability check returns sat with witness |

**Proof command:**
```bash
cd R:/Sandbox/ark && pytest tests/test_verify_predicate.py -q
```

---

### 4. Codegen Tests

#### `tests/test_codegen_expression.py` (pytest)

| TC | Test Function | Description |
|----|--------------|-------------|
| TC-018 | `test_expression_emits_pub_fn` | `codegen --target rust` emits one `pub fn` per expression item |
| TC-019 | `test_numeric_rust_valid` | Every numeric stdlib expression emits compilable Rust |
| TC-020 | `test_text_rust_valid` | Every text stdlib expression emits compilable Rust |
| TC-021 | `test_predicate_emits_bool_fn` | Every predicate emits `pub fn ... -> bool` |
| TC-022 | `test_inline_pipe_in_process_body` | Inline pipes inside process bodies emit valid Rust |
| TC-023 | `test_cpp_stub_raises` | C++ / Proto codegen raises `NotImplementedError` with follow-up note |

**Proof command:**
```bash
cd R:/Sandbox/ark && pytest tests/test_codegen_expression.py -q
```

---

### 5. Pipeline / Integration Tests

#### `tests/test_pipeline_expression.py` (pytest)

| TC | Test Function | Description |
|----|--------------|-------------|
| TC-024 | `test_expression_ark_end_to_end` | `specs/test_expression.ark` parses, verifies, and codegens end-to-end |
| TC-024 | `test_pipeline_exits_zero` | `python ark.py pipeline specs/test_expression.ark --target rust` exits 0 |
| TC-024 | `test_pipeline_output_contains_fns` | Output `.rs` contains `pub fn normalize_name`, `pub fn is_valid_name` |

**Proof command:**
```bash
cd R:/Sandbox/ark && pytest tests/test_pipeline_expression.py -q
```

---

### 6. Cross-cutting / Meta Tests

#### Full test suite (TC-025): pytest

| TC | Test Function | File | Runner |
|----|--------------|------|--------|
| TC-025 | (all tests) | `tests/` | pytest |

**Proof command:**
```bash
cd R:/Sandbox/ark && pytest tests/ -q
```

#### Rust AST tests (TC-026): cargo test

| TC | Test Function | File | Runner |
|----|--------------|------|--------|
| TC-026 | `test_expression_def_parse` | `dsl/src/parse.rs` | cargo test |
| TC-026 | `test_predicate_def_parse` | `dsl/src/parse.rs` | cargo test |
| TC-026 | `test_pipe_expr_round_trip` | `dsl/src/parse.rs` | cargo test |

**Proof command:**
```bash
cd R:/Sandbox/ark && cargo test -p ark-dsl
```

#### Example spec parsing (TC-027): manual/CLI

| TC | Test Function | File | Runner |
|----|--------------|------|--------|
| TC-027 | N/A (CLI invocation) | `specs/examples/expressif_examples.ark` | CLI |

**Proof command:**
```bash
cd R:/Sandbox/ark && python ark.py parse specs/examples/expressif_examples.ark
```

#### Coverage (TC-028): pytest + coverage

| TC | Test Function | File | Runner |
|----|--------------|------|--------|
| TC-028 | N/A (coverage metric) | `tests/test_*expression*.py tests/test_*predicate*.py` | coverage |

**Proof command:**
```bash
cd R:/Sandbox/ark && coverage run -m pytest tests/test_*expression*.py tests/test_*predicate*.py && coverage report --fail-under=80
```

#### Documentation (TC-029): manual verification

| TC | Test Function | File | Runner |
|----|--------------|------|--------|
| TC-029 | N/A | `docs/DSL_SPEC.md` | manual |

**Proof command:**
```
read R:/Sandbox/ark/docs/DSL_SPEC.md, confirm section exists and cites stdlib files
```

#### Backlog (TC-030): autotest/CLI

| TC | Test Function | File | Runner |
|----|--------------|------|--------|
| TC-030 | N/A (verify invocation) | `specs/meta/backlog.ark` | CLI |

**Proof command:**
```bash
cd R:/Sandbox/ark && python ark.py verify specs/meta/backlog.ark
```

---

## Complete TC-to-Test Mapping

| TC | Subsystem | Test File | Test Function(s) | Runner | Type |
|----|-----------|-----------|-------------------|--------|------|
| TC-001 | parser | `test_parser_expression_items.py` | `test_expression_item_parses` | pytest | autotest |
| TC-002 | parser | `test_parser_expression_items.py` | `test_predicate_item_parses` | pytest | autotest |
| TC-003 | parser | `test_parser_pipe.py` | `test_bare_pipe_parses`, `test_chained_pipe_left_associative`, `test_pipe_with_extra_args`, `test_pipe_precedence_with_arithmetic` | pytest | autotest |
| TC-004 | parser | `test_parser_pipe.py` | `test_var_ref_at_sigil`, `test_prop_ref_bracket_dotted`, `test_idx_ref_hash_sigil`, `test_nested_ref_braces` | pytest | autotest |
| TC-005 | parser | `test_parser_pipe.py` + `dsl/src/parse.rs` | `test_python_rust_parity_expression` + Rust inline tests | pytest + cargo | autotest |
| TC-006 | parser | `test_parser_pipe.py` | `test_kebab_inside_pipe`, `test_kebab_outside_pipe_errors` | pytest | autotest |
| TC-007 | parser | `test_parser_expression_items.py` | `test_expression_all_fields_populated`, `test_predicate_all_fields_populated` | pytest | autotest |
| TC-008 | parser | `test_parser_expression_items.py` | `test_missing_chain_clause_errors`, `test_missing_out_clause_errors`, `test_malformed_predicate_errors` | pytest | autotest |
| TC-009 | stdlib | `test_stdlib_expression.py` | `test_import_stdlib_expression_resolves`, `test_import_stdlib_predicate_resolves` | pytest | autotest |
| TC-010 | stdlib | `test_stdlib_expression.py` | `test_numeric_primitives_complete` | pytest | autotest |
| TC-011 | stdlib | `test_stdlib_expression.py` | `test_text_primitives_complete` | pytest | autotest |
| TC-012 | stdlib | `test_stdlib_expression.py` | `test_predicates_bool` | pytest | autotest |
| TC-013 | verify | `test_verify_expression.py` | `test_numeric_pipe_verifies` | pytest | autotest |
| TC-014 | verify | `test_verify_predicate.py` | `test_predicate_check_in_z3_verify`, `test_predicate_satisfiability` | pytest | autotest |
| TC-015 | verify | `test_verify_expression.py` | `test_opaque_primitive_pass_opaque` | pytest | autotest |
| TC-016 | verify | `test_verify_expression.py` | `test_user_expression_inline` | pytest | autotest |
| TC-017 | verify | `test_verify_expression.py` | `test_unknown_stage_error` | pytest | autotest |
| TC-018 | codegen | `test_codegen_expression.py` | `test_expression_emits_pub_fn` | pytest | autotest |
| TC-019 | codegen | `test_codegen_expression.py` | `test_numeric_rust_valid` | pytest | autotest |
| TC-020 | codegen | `test_codegen_expression.py` | `test_text_rust_valid` | pytest | autotest |
| TC-021 | codegen | `test_codegen_expression.py` | `test_predicate_emits_bool_fn` | pytest | autotest |
| TC-022 | codegen | `test_codegen_expression.py` | `test_inline_pipe_in_process_body` | pytest | autotest |
| TC-023 | codegen | `test_codegen_expression.py` | `test_cpp_stub_raises` | pytest | autotest |
| TC-024 | pipeline | `test_pipeline_expression.py` | `test_expression_ark_end_to_end`, `test_pipeline_exits_zero`, `test_pipeline_output_contains_fns` | pytest | autotest |
| TC-025 | pipeline | `tests/` (all) | (all test files) | pytest | autotest |
| TC-026 | pipeline | `dsl/src/parse.rs` | Rust inline `#[cfg(test)]` tests | cargo test | autotest |
| TC-027 | pipeline | `specs/examples/expressif_examples.ark` | N/A (CLI) | CLI | autotest |
| TC-028 | pipeline | coverage metric | N/A | coverage | autotest |
| TC-029 | docs | `docs/DSL_SPEC.md` | N/A | manual | manual |
| TC-030 | pipeline | `specs/meta/backlog.ark` | N/A (CLI) | CLI | autotest |

---

## New Test Files Summary

| File | Tests | Subsystem | Dependencies |
|------|-------|-----------|-------------|
| `tests/test_parser_pipe.py` | ~10 | parser | Grammar + parser changes (T002, T004, T005, T006) |
| `tests/test_parser_expression_items.py` | ~7 | parser | Grammar + AST changes (T003, T004, T006) |
| `tests/test_stdlib_expression.py` | ~5 | stdlib | Stdlib files + primitives (T007-T011) |
| `tests/test_verify_expression.py` | ~4 | verify | Verify extensions (T012-T015) |
| `tests/test_verify_predicate.py` | ~2 | verify | Verify extensions (T012, T013) |
| `tests/test_codegen_expression.py` | ~6 | codegen | Codegen extensions (T016-T019) |
| `tests/test_pipeline_expression.py` | ~3 | pipeline | All subsystems (T020, T021) |
| `dsl/src/parse.rs` (inline tests) | ~3 | parser (Rust) | Rust AST changes (T003, T004) |

**Total: ~40 test functions across 7 new Python files + 1 Rust test module extension**

---

## Execution Order

Tests should be developed in dependency order matching the task plan:

1. **Parser tests** (T022, T023) -- after grammar/parser tasks (T002-T006)
2. **Stdlib tests** (T024) -- after stdlib tasks (T007-T011)
3. **Verify tests** (T025, T026) -- after verify tasks (T012-T015)
4. **Codegen tests** (T027) -- after codegen tasks (T016-T019)
5. **Pipeline tests** (T028) -- after example specs (T020, T021)
6. **Full suite run** (T029) -- after all above
7. **Rust parity tests** (T030) -- can run in parallel with Python tests

---

## Runner Summary

| Runner | TCs | Count |
|--------|-----|-------|
| pytest | TC-001 through TC-025, TC-028 | 26 |
| cargo test | TC-005 (partial), TC-026 | 2 |
| CLI (python ark.py) | TC-027, TC-030 | 2 |
| manual | TC-029 | 1 |

Note: TC-005 uses both pytest and cargo test. TC-028 uses pytest via coverage wrapper.
