# Plan: Verification & Codegen

## Designs Covered
- 04_verification
- 05_codegen

## Tasks

### Z3 translation: Pipe & ParamRef nodes
- **ID**: ADV001-T012
- **Description**: Extend `R:/Sandbox/ark/tools/verify/ark_verify.py` `translate_expr`
  dispatch to handle `kind == "pipe"` and `kind == "param_ref"`. Pipe: recursively translate
  head, then fold each stage — native primitives → direct Z3 op, user expressions → inline
  via registry, opaque → uninterpreted Function. ParamRef: delegate to existing
  `SymbolTable` via path join.
- **Files**:
  - `R:/Sandbox/ark/tools/verify/ark_verify.py`
- **Acceptance Criteria**:
  - Existing verify tests still pass (`pytest tests/test_verify_*.py -q`)
  - New unit tests in `test_verify_expression.py` cover pipe translation
- **Target Conditions**: TC-013, TC-015
- **Depends On**: [ADV001-T006]
- **Evaluation**:
  - Access requirements: Read+Edit ark_verify.py, Bash for pytest
  - Skill set: Python, Z3 API, AST traversal
  - Estimated duration: 25min
  - Estimated tokens: 45000

### Expression/Predicate registry + inlining
- **ID**: ADV001-T013
- **Description**: Add `build_expr_registry(ark_file)` and `build_pred_registry(ark_file)` to
  `ark_verify.py`. These walk `items`, collect `ExpressionDef` / `PredicateDef` entries, and
  support cycle detection. Add `inline_expression_def(def, value_expr, syms)` that
  alpha-renames the expression's `chain:` with the incoming value bound to the first input.
  Raise on cycles with a clear error.
- **Files**:
  - `R:/Sandbox/ark/tools/verify/ark_verify.py`
- **Acceptance Criteria**:
  - User-defined expression called from a process body is inlined correctly
  - Mutual recursion detection produces error listing the cycle
- **Target Conditions**: TC-016
- **Depends On**: [ADV001-T012]
- **Evaluation**:
  - Access requirements: Edit ark_verify.py, Bash
  - Skill set: Python, graph cycle detection
  - Estimated duration: 20min
  - Estimated tokens: 35000

### Opaque primitive handling (regex, temporal, file-io)
- **ID**: ADV001-T014
- **Description**: Create `R:/Sandbox/ark/tools/verify/expression_smt.py` with Z3 primitive
  map (`PRIMITIVE_Z3`) and opaque-function declarations. Every primitive marked `opaque:
  true` returns a `Function(...)` uninterpreted symbol and flags the verify result as
  `PASS_OPAQUE`. Print summary: `N checks: X PASS, Y UNKNOWN, Z PASS_OPAQUE`.
- **Files**:
  - `R:/Sandbox/ark/tools/verify/expression_smt.py` (NEW)
  - `R:/Sandbox/ark/tools/verify/ark_verify.py` — import and use
- **Acceptance Criteria**:
  - Regex primitive produces PASS_OPAQUE
  - Final verify report includes a summary line with opaque counts
- **Target Conditions**: TC-015
- **Depends On**: [ADV001-T013]
- **Evaluation**:
  - Access requirements: Write expression_smt.py, Edit ark_verify.py, Bash
  - Skill set: Python, Z3 UF declarations
  - Estimated duration: 20min
  - Estimated tokens: 30000

### Unknown-stage error with fuzzy suggestions
- **ID**: ADV001-T015
- **Description**: When the verifier encounters a pipe stage name not in the registry, raise
  an error listing up to 3 closest matches (using `difflib.get_close_matches`). The error
  should include the file:line:col of the offending stage.
- **Files**:
  - `R:/Sandbox/ark/tools/verify/ark_verify.py`
- **Acceptance Criteria**:
  - Test: `x |> tetx-to-lower` → error "unknown stage `tetx-to-lower`, did you mean: text-to-lower, text-to-upper, ..."
- **Target Conditions**: TC-017
- **Depends On**: [ADV001-T014]
- **Evaluation**:
  - Access requirements: Edit ark_verify.py, Bash
  - Skill set: Python, difflib
  - Estimated duration: 10min
  - Estimated tokens: 15000

### Codegen: Rust functions for ExpressionDef items
- **ID**: ADV001-T016
- **Description**: Add `gen_rust_expression(def)` to `R:/Sandbox/ark/tools/codegen/ark_codegen.py`.
  Mangle `text-to-lower` → `text_to_lower`. Emit `#[inline] pub fn` with signature derived
  from inputs/output. Body: desugar the `chain:` right-to-left into nested calls via
  `EXPR_PRIMITIVES`. For chains >4 stages, emit `let` bindings per stage.
- **Files**:
  - `R:/Sandbox/ark/tools/codegen/ark_codegen.py`
- **Acceptance Criteria**:
  - `python ark.py codegen specs/test_expression.ark --target rust` emits a `pub fn` per
    expression
  - Generated snippet for `clamp` matches expected Rust
- **Target Conditions**: TC-018, TC-019, TC-020
- **Depends On**: [ADV001-T011]
- **Evaluation**:
  - Access requirements: Edit ark_codegen.py, Bash
  - Skill set: Python, Rust codegen
  - Estimated duration: 30min
  - Estimated tokens: 55000

### Codegen: Rust functions for PredicateDef items
- **ID**: ADV001-T017
- **Description**: Add `gen_rust_predicate(def)` that emits `#[inline] pub fn NAME(...) -> bool`
  with the `check:` expression desugared to Rust.
- **Files**:
  - `R:/Sandbox/ark/tools/codegen/ark_codegen.py`
- **Acceptance Criteria**:
  - Generated `is_valid_name` matches expected Rust boolean expression
  - `cargo check` on generated file succeeds (or `rustc --emit=metadata` standalone)
- **Target Conditions**: TC-021
- **Depends On**: [ADV001-T016]
- **Evaluation**:
  - Access requirements: Edit ark_codegen.py, Bash
  - Skill set: Python, Rust
  - Estimated duration: 15min
  - Estimated tokens: 25000

### Codegen: inline pipes inside process bodies
- **ID**: ADV001-T018
- **Description**: Extend `gen_rust_process_body` (or its body-statement switch) to recognize
  `Expr::Pipe` and emit nested calls at the use site. Integration: existing assignments like
  `score' = pipe(...)` become `self.score = ...`.
- **Files**:
  - `R:/Sandbox/ark/tools/codegen/ark_codegen.py`
- **Acceptance Criteria**:
  - `.ark` process body using `|>` codegens to valid Rust
  - Existing `specs/test_minimal.ark` codegen unchanged (regression)
- **Target Conditions**: TC-022
- **Depends On**: [ADV001-T017]
- **Evaluation**:
  - Access requirements: Edit ark_codegen.py, Bash
  - Skill set: Python, Rust
  - Estimated duration: 25min
  - Estimated tokens: 45000

### Codegen: C++/Proto stubs raising NotImplementedError
- **ID**: ADV001-T019
- **Description**: Add `gen_cpp_expression`, `gen_cpp_predicate`, `gen_proto_expression`,
  `gen_proto_predicate` stubs that raise `NotImplementedError` with a message naming the
  follow-up adventure (e.g., "ADV-002+: C++/Proto expression codegen"). Wire into dispatch.
- **Files**:
  - `R:/Sandbox/ark/tools/codegen/ark_codegen.py`
- **Acceptance Criteria**:
  - `python ark.py codegen specs/test_expression.ark --target cpp` raises
    NotImplementedError with a clear message
- **Target Conditions**: TC-023
- **Depends On**: [ADV001-T018]
- **Evaluation**:
  - Access requirements: Edit ark_codegen.py, Bash
  - Skill set: Python
  - Estimated duration: 10min
  - Estimated tokens: 12000
