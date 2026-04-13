# Process Schemas — ADV-001

## Processes

### ParsePipeExpression
Transform source text with `|>` operators into a `Pipe` AST node.

1. Consume `or_expr` as the head
2. While next token is `|>`, consume `pipe_stage` (kebab-ident + optional `call_tail`)
3. Emit `Expr::Pipe(head, [stage1, stage2, ...])`

Error paths:
- `|>` with no right-hand stage → "expected pipe stage after `|>`"
- stage name containing invalid chars → parse error with caret at offending column

### ParseExpressionItem
Transform `expression Foo { in: ..., out: T, chain: ... }` into `Item::Expression`.

1. Match `expression` keyword
2. Consume identifier as name
3. Consume `{`
4. Consume `in:` typed_field_list
5. Consume `out:` type_expr
6. Consume `chain:` expression (must be pipe-or-atom)
7. Consume `}`
8. Emit `Item::Expression(ExpressionDef { ... })`

Error paths:
- Missing `in:` → error "expression must declare input fields"
- Missing `out:` → error "expression must declare output type"
- Missing `chain:` → error "expression body must contain `chain:`"
- Duplicate expression name → error "expression `Foo` already declared at line N"

### BuildExpressionIndex
Populate `ArkFile.expression_index` and `predicate_index`.

1. Iterate `file.items`
2. For each `Item::Expression(def)`: insert `def.name → idx` into `expression_index`
3. For each `Item::Predicate(def)`: insert `def.name → idx` into `predicate_index`
4. Detect duplicates (last-wins, matching existing `classes_index` behaviour at
   `R:/Sandbox/ark/dsl/src/parse.rs:34-63`)

### TranslatePipeToZ3
Recursively translate a `Pipe` node into a Z3 expression.

1. Translate `head` via `translate_expr` → `val`
2. For each stage:
   a. Look up stage name in `expr_registry` (registered ExpressionDef items)
   b. If found: alpha-rename inputs, recursively translate `chain:` with `val` bound to first input
   c. If primitive: apply target Z3 op (add/mul/str.len/etc.)
   d. If opaque: wrap in `Function` uninterpreted symbol, mark verify result as PASS_OPAQUE
3. Return final Z3 expression

Error paths:
- Unknown stage name → raise with message listing valid alternatives (fuzzy match top-3)
- Cycle in expression registry → raise "expression `Foo` recursively references itself"
- Arity mismatch → raise "stage `clamp` expects 2 args, got 1"

### CodegenRustExpression
Emit Rust function for `ExpressionDef`.

1. Mangle name: `text-to-lower` → `text_to_lower`
2. Emit signature: `pub fn {name}({input1}: {ty1}, ...) -> {out}`
3. Body: desugar `chain:` right-to-left into nested function calls via `EXPR_PRIMITIVES`
4. If chain > 4 stages: emit `let` bindings per stage
5. Wrap in `#[inline]` attribute

Error paths:
- Name collision after mangling → hard error, abort codegen
- Missing primitive mapping → hard error naming the missing primitive

### CodegenRustPredicate
Emit Rust function returning `bool`.

1. Mangle name
2. Signature: `pub fn {name}({inputs}) -> bool`
3. Body: desugar `check:` expression to Rust bool expression
4. `#[inline]` attribute

### VerifyPredicateSatisfiability
Check that a predicate has at least one satisfying input.

1. Build fresh Z3 solver
2. Declare Z3 symbols for each input field
3. Translate `check:` → Z3 formula
4. Assert the formula
5. Run `solver.check()`
6. Report: `sat` (predicate satisfiable, return witness), `unsat` (predicate unsatisfiable),
   `unknown` (opaque primitives involved)
