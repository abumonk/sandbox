# Plan: Grammar & AST Extensions

## Designs Covered
- 01_dsl_surface
- 02_grammar_parser

## Tasks

### Design test strategy for ADV-001
- **ID**: ADV001-T001
- **Description**: Design automated tests covering all target conditions with
  `proof_method: autotest`. Create `R:/Sandbox/.agent/adventures/ADV-001/tests/test-strategy.md`
  describing test files, pytest / cargo commands, and how each TC maps to a specific test. Read
  designs 01-06 first. Output the strategy doc and a TC→test mapping table.
- **Files**:
  - `R:/Sandbox/.agent/adventures/ADV-001/tests/test-strategy.md` (NEW)
- **Acceptance Criteria**:
  - File exists and lists every TC-### from the manifest
  - Each TC has a proof_command using `python ark.py ...` or `pytest ...` or `cargo test ...`
  - Test files are grouped by subsystem (parser, verify, codegen, pipeline)
- **Target Conditions**: TC-025 (planning surface)
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read adventure designs
  - Skill set: test planning, pytest, cargo
  - Estimated duration: 15min
  - Estimated tokens: 15000

### Extend Rust pest grammar with pipe and expression/predicate items
- **ID**: ADV001-T002
- **Description**: Edit `R:/Sandbox/ark/dsl/grammar/ark.pest` to add `pipe_expr`, `pipe_stage`,
  `pipe_fn_ident` (kebab-case atomic), `var_ref`, `prop_ref`, `idx_ref`, `nested_ref`,
  `expression_def`, `predicate_def`. Wire `pipe_expr` into the precedence stack so
  `expression = { pipe_expr }` and `pipe_expr = { or_expr ~ ("|>" ~ pipe_stage)* }`. Add
  `expression_def` and `predicate_def` to the `item` rule. Keep existing tests green.
- **Files**:
  - `R:/Sandbox/ark/dsl/grammar/ark.pest`
- **Acceptance Criteria**:
  - Grammar compiles (`cargo build -p ark-dsl` succeeds)
  - `cargo test -p ark-dsl` — existing tests still pass
  - New rules present and named exactly as in design 02
- **Target Conditions**: TC-003, TC-004, TC-006, TC-007
- **Depends On**: [ADV001-T001]
- **Evaluation**:
  - Access requirements: Read+Edit on `ark.pest`, Bash for `cargo build` / `cargo test`
  - Skill set: Rust, pest PEG grammar
  - Estimated duration: 25min
  - Estimated tokens: 35000

### Extend Rust AST (lib.rs) with Pipe, ParamRef, ExpressionDef, PredicateDef
- **ID**: ADV001-T003
- **Description**: Edit `R:/Sandbox/ark/dsl/src/lib.rs` to add new `Expr` variants,
  `RefKind`, `PipeStage`, `ExpressionDef`, `PredicateDef`, new `Item` variants,
  `expression_index` and `predicate_index` on `ArkFile`. Update `ArkFile::class` and add
  `expression()` / `predicate()` helper accessors. Ensure `Serialize` / `Deserialize` still
  work and existing `ast_roundtrips_json` test passes.
- **Files**:
  - `R:/Sandbox/ark/dsl/src/lib.rs`
- **Acceptance Criteria**:
  - `cargo build -p ark-dsl` clean
  - `cargo test -p ark-dsl` existing tests pass
  - New types derive Debug/Clone/Serialize/Deserialize
- **Target Conditions**: TC-001, TC-002, TC-005
- **Depends On**: [ADV001-T002]
- **Evaluation**:
  - Access requirements: Read+Edit on lib.rs, Bash for cargo
  - Skill set: Rust, serde, AST design
  - Estimated duration: 20min
  - Estimated tokens: 30000

### Rust parse.rs: AST builders for pipe, param refs, expression/predicate items
- **ID**: ADV001-T004
- **Description**: Edit `R:/Sandbox/ark/dsl/src/parse.rs` to add `pipe_expr_from_pair`,
  `pipe_stage_from_pair`, `param_ref_from_pair`, `expression_def_from_pair`,
  `predicate_def_from_pair`. Extend `file_from_pair` to accept the new top-level items. Extend
  `build_indices` to populate `expression_index` and `predicate_index`. Add inline
  `#[cfg(test)] mod tests` entries asserting parse round-trip for each new form.
- **Files**:
  - `R:/Sandbox/ark/dsl/src/parse.rs`
- **Acceptance Criteria**:
  - `cargo test -p ark-dsl` passes all new tests
  - `parse_ark_file("expression Foo { in: x: Float, out: Float, chain: x |> abs }")` produces
    `Item::Expression` with correct name and fields
  - Duplicate expression name uses last-wins in index
- **Target Conditions**: TC-001, TC-002, TC-003, TC-004, TC-007
- **Depends On**: [ADV001-T003]
- **Evaluation**:
  - Access requirements: Read+Edit on parse.rs, Bash for cargo test
  - Skill set: Rust, pest pairs traversal
  - Estimated duration: 30min
  - Estimated tokens: 60000

### Extend Python Lark grammar with pipe and expression/predicate items
- **ID**: ADV001-T005
- **Description**: Mirror pest grammar changes in
  `R:/Sandbox/ark/tools/parser/ark_grammar.lark`. Add `pipe_expr`, `pipe_stage`,
  `pipe_fn_ident`, `var_ref`, `prop_ref`, `idx_ref`, `nested_ref`, `expression_def`,
  `predicate_def`. Wire into `?expr` precedence below `?or_expr`. Add `expression_def` and
  `predicate_def` to `item` rule.
- **Files**:
  - `R:/Sandbox/ark/tools/parser/ark_grammar.lark`
- **Acceptance Criteria**:
  - Grammar loads without errors in Lark
  - `python ark.py parse specs/test_minimal.ark` still succeeds (regression)
- **Target Conditions**: TC-003, TC-004, TC-005, TC-007
- **Depends On**: [ADV001-T001]
- **Evaluation**:
  - Access requirements: Read+Edit on ark_grammar.lark, Bash for `python ark.py parse`
  - Skill set: Lark EBNF, grammar parity
  - Estimated duration: 25min
  - Estimated tokens: 35000

### Python parser transformer for pipe / param refs / expression items
- **ID**: ADV001-T006
- **Description**: Edit `R:/Sandbox/ark/tools/parser/ark_parser.py` to add dataclasses
  `ExpressionDef`, `PredicateDef`, `PipeStage`, and transformer methods `pipe_expr`,
  `pipe_stage`, `var_ref`, `prop_ref`, `idx_ref`, `nested_ref`, `expression_def`,
  `predicate_def`. Update JSON serialization so node shapes match the Rust JSON exactly.
  Extend the import-resolution path to accept `stdlib.expression` and `stdlib.predicate`.
- **Files**:
  - `R:/Sandbox/ark/tools/parser/ark_parser.py`
- **Acceptance Criteria**:
  - `pytest tests/test_parser_*.py -q` passes existing tests (regression)
  - `python ark.py parse specs/test_minimal.ark` still succeeds
  - New transformer methods emit dicts matching schema from `schemas/entities.md`
- **Target Conditions**: TC-001, TC-002, TC-003, TC-004, TC-005, TC-007, TC-008, TC-009
- **Depends On**: [ADV001-T005]
- **Evaluation**:
  - Access requirements: Read+Edit on ark_parser.py, Bash for pytest / ark.py
  - Skill set: Python, Lark Transformer, dataclasses
  - Estimated duration: 30min
  - Estimated tokens: 60000
