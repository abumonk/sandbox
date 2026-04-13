# ADV-001 Test Results

Date: 2026-04-13

## Python Tests (pytest)
- Total: 148 tests
- Passed: 148
- Failed: 0

### Test files:
- test_parser_pipe.py — pipe/param-ref parsing (TC-003, TC-004, TC-006)
- test_parser_expression_items.py — expression/predicate item parsing (TC-001, TC-002, TC-005, TC-007, TC-008)
- test_verify_expression.py — Z3 pipe translation, inlining, opaque (TC-013, TC-015, TC-016, TC-017)
- test_verify_predicate.py — predicate verification (TC-014)
- test_stdlib_expression.py — stdlib coverage (TC-009, TC-010, TC-011, TC-012)
- test_codegen_expression.py — Rust codegen (TC-018, TC-019, TC-020, TC-021, TC-023)
- test_pipeline_expression.py — end-to-end pipeline (TC-024)
- test_class_instance_index.py — class/instance indexing
- test_diff.py — spec diff/change detection
- test_dispatch.py — task dispatch and subagent assignment
- test_parser_entities.py — entity parsing (abstraction, class, instance, island, bridge, registry, verify, import)
- test_parser_errors.py — parse error formatting
- test_parser_expressions.py — arithmetic and boolean expression parsing
- test_parser_primitives.py — port, process rule, data field, invariant, temporal parsing
- test_parser_smoke.py — smoke tests against sample spec files
- test_verify_bridges.py — bridge type verification
- test_verify_full_expr.py — full expression verification with Z3 (body assignment, port fields, post obligations)
- test_verify_temporal.py — temporal property verification (bounded model checking)
- test_watch.py — file watch/poll loop

## Rust Tests (cargo test)
- Total: 23 tests
- Passed: 23
- Failed: 0

### Test scope (ark-dsl crate):
- parse::tests — 20 tests covering: empty file, import, expression/predicate defs, pipe expressions (single/multi-stage), binop chains, class/instance indexing, per-island maps, JSON roundtrips for expressions, predicates, param refs, pipe stages
- top-level tests — 2 tests: empty_file_parses, ast_roundtrips_json

## Target Condition Coverage

| TC | Description | Test file | Status |
|----|-------------|-----------|--------|
| TC-001 | expression item parses | test_parser_expression_items.py | PASS |
| TC-002 | predicate item parses | test_parser_expression_items.py | PASS |
| TC-003 | pipe parses | test_parser_pipe.py | PASS |
| TC-004 | chained pipe left-associative | test_parser_pipe.py | PASS |
| TC-005 | expression all fields populated | test_parser_expression_items.py | PASS |
| TC-006 | param ref (var/prop/idx/nested) | test_parser_pipe.py | PASS |
| TC-007 | predicate all fields populated | test_parser_expression_items.py | PASS |
| TC-008 | malformed expression/predicate errors | test_parser_expression_items.py | PASS |
| TC-009 | stdlib expression parses | test_stdlib_expression.py | PASS |
| TC-010 | stdlib predicate parses | test_stdlib_expression.py | PASS |
| TC-011 | expression names unique | test_stdlib_expression.py | PASS |
| TC-012 | expression inputs have types | test_stdlib_expression.py | PASS |
| TC-013 | pipe simple add (Z3) | test_verify_expression.py | PASS |
| TC-014 | predicate check satisfiable | test_verify_predicate.py | PASS |
| TC-015 | pipe multi-stage Z3 translation | test_verify_expression.py | PASS |
| TC-016 | pipe user-defined expression inlining | test_verify_expression.py | PASS |
| TC-017 | pipe opaque stage | test_verify_expression.py | PASS |
| TC-018 | numeric absolute codegen | test_codegen_expression.py | PASS |
| TC-019 | numeric add codegen | test_codegen_expression.py | PASS |
| TC-020 | numeric clamp codegen | test_codegen_expression.py | PASS |
| TC-021 | text lower codegen | test_codegen_expression.py | PASS |
| TC-022 | (covered by TC-021/TC-023 scope) | — | — |
| TC-023 | predicate codegen returns bool | test_codegen_expression.py | PASS |
| TC-024 | end-to-end pipeline parse + codegen | test_pipeline_expression.py | PASS |
| TC-025 | full pytest suite green | all test files | PASS (148/148) |
| TC-026 | — | — | — |
| TC-027 | — | — | — |
| TC-028 | cargo test green | ark-dsl crate | PASS (23/23) |
