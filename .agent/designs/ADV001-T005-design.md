# Extend Python Lark Grammar with Pipe and Expression/Predicate Items - Design

## Approach

Mirror the pest grammar's new expression/predicate constructs in `ark_grammar.lark`. The Lark grammar must produce parse trees that the `ArkTransformer` (task T006) can walk to produce identical JSON AST as the Rust parser. This task modifies **only the grammar file**; transformer methods are T006's scope.

Key differences between Lark and pest that affect the translation:
- Lark uses `?rule` (transparent/inline) where pest uses `_{ }` (silent)
- Lark uses `->` aliases for inline alternatives where pest uses named rules
- Lark terminals are UPPERCASE; pest uses `@{ }` for atomic
- Lark regexes use `/pattern/`; pest uses built-in character classes
- Lark has no compound-atomic (`${ }`); we use regex terminals instead

## Target Files

- `R:/Sandbox/ark/tools/parser/ark_grammar.lark` - Add pipe_expr, pipe_stage, pipe_fn_ident, var_ref, prop_ref, idx_ref, nested_ref, expression_def, predicate_def rules

## Implementation Steps

### Step 1: Add `PIPE_FN_IDENT` terminal (after line 238, IDENT terminal)

The kebab-case function identifier used only inside pipe stages. In pest this is `pipe_fn_ident = @{ ident ~ ("-" ~ ident)* }`. In Lark, define a regex terminal:

```lark
PIPE_FN_IDENT: /[a-zA-Z_][a-zA-Z0-9_]*(-[a-zA-Z_][a-zA-Z0-9_]*)*/
```

**Important**: This terminal must be placed AFTER `IDENT` in the grammar. Lark's Earley parser doesn't use terminal ordering for priority in the same way as LALR, but we will scope `PIPE_FN_IDENT` usage to `pipe_stage` only to avoid ambiguity. Actually, for Earley mode, both terminals would match the same prefix for non-kebab names. Better approach: use `IDENT` in pipe_stage and handle kebab-case via a separate rule:

```lark
pipe_fn_ident: IDENT ("-" IDENT)*
```

This is cleaner for Lark -- it's a rule, not a terminal, so it only matches where explicitly referenced. The transformer (T006) will join the parts with hyphens.

### Step 2: Insert `pipe_expr` into the expression precedence chain (lines 158-161)

Current chain:
```
?expr: or_expr
```

New chain -- pipe sits ABOVE `or_expr` so `x |> f or y` parses as `(x |> f) or y`:
```lark
?expr: pipe_expr

pipe_expr: or_expr ("|>" pipe_stage)*
```

This mirrors `pipe_expr = { or_expr ~ ("|>" ~ pipe_stage)* }` from pest design doc line 51. When there are no `|>` tokens, `pipe_expr` produces a single child (the `or_expr` result), which the transformer can pass through. Without `?` prefix, this rule always creates a `pipe_expr` tree node. The transformer will check `len(items)` to decide whether to wrap in a Pipe node or pass through.

### Step 3: Add `pipe_stage` rule (after pipe_expr)

```lark
pipe_stage: pipe_fn_ident "(" expr_list? ")"
          | pipe_fn_ident
```

This mirrors pest's `pipe_stage = { pipe_fn_ident ~ call_tail? }`. The two alternatives handle with-args and without-args cases.

### Step 4: Add parameter reference rules (before the `?atom` rule, around line 170)

Add new alternatives to the `?atom` rule. They must appear BEFORE `fn_call` and `IDENT` alternatives to ensure sigils take priority:

```lark
?atom: "true"                                 -> true_expr
     | "false"                                -> false_expr
     | "$data" IDENT                          -> data_ref_expr
     | var_ref
     | prop_ref
     | idx_ref
     | nested_ref
     | fn_call
     | dotted_path                            -> path_expr
     | IDENT                                  -> ident_expr
     | NUMBER                                 -> number_expr
     | STRING                                 -> string_expr
     | "(" expr ")"                           -> paren_expr
     | "[" expr_list? "]"                     -> array_expr
     | for_all_expr
```

The individual param-ref rules:

```lark
var_ref: "@" IDENT
prop_ref: "[" IDENT ("." IDENT)+ "]"
idx_ref: "#" IDENT "[" NUMBER "]"
nested_ref: "{" expr "}"
```

**Ordering concern for `prop_ref` vs `array_expr`**: Both start with `[`. `prop_ref` requires `IDENT ("." IDENT)+` (dotted path), while `array_expr` uses `expr_list?`. Since `prop_ref` is listed first in `?atom` and has a more specific structure (requires dots), Earley will try both but `prop_ref` wins when content is dotted idents. Single-ident `[x]` still matches only `array_expr`. This matches the design doc decision (01_dsl_surface.md line 195).

**Collision concern for `nested_ref` vs `enum_constraint`**: `{expr}` could conflict with `{expr_list}` in enum_constraint. However, `nested_ref` appears in `?atom` (expression context) while `enum_constraint` appears after `constraint` which follows `type_expr` in `data_field`. These are structurally disjoint parse positions, so no ambiguity.

**Collision concern for `var_ref` vs `@in`/`@out`**: `@in` and `@out` are matched at the statement level (`in_port`, `out_port` rules) with specific keywords `"@in"` and `"@out"`. Inside expressions, `var_ref` matches `"@" IDENT`. Since `in` and `out` are valid IDENTs, `@in` inside an expression context would parse as `var_ref` with name `in`. This is correct -- `@in` as a variable reference inside a pipe stage argument is valid and distinct from the `@in { ... }` port declaration.

### Step 5: Add `expression_def` and `predicate_def` top-level items (after verify_def, around line 121)

```lark
// ============================================================
// EXPRESSION & PREDICATE DEFINITIONS
// ============================================================

expression_def: "expression" IDENT "{" expression_body "}"
predicate_def: "predicate" IDENT "{" predicate_body "}"

expression_body: "in:" typed_field_list "out:" type_expr "chain:" expr
predicate_body: "in:" typed_field_list "check:" expr
```

These mirror the pest rules from the design doc (02_grammar_parser.md lines 38-42).

### Step 6: Wire into `item` rule (line 12-21)

Add two new alternatives:

```lark
item: abstraction_def
    | class_def
    | instance_def
    | island_def
    | bridge_def
    | registry_def
    | verify_def
    | primitive_def
    | struct_def
    | enum_def
    | expression_def
    | predicate_def
```

### Summary of exact line-by-line changes

1. **Lines 12-21 (`item` rule)**: Add `| expression_def` and `| predicate_def` at the end
2. **After line 121 (`verify_def`)**: Insert new section with `expression_def`, `predicate_def`, `expression_body`, `predicate_body` rules
3. **Line 158 (`?expr`)**: Change `?expr: or_expr` to `?expr: pipe_expr`
4. **After line 158**: Insert `pipe_expr`, `pipe_stage`, `pipe_fn_ident` rules
5. **Lines 170-181 (`?atom`)**: Add `var_ref`, `prop_ref`, `idx_ref`, `nested_ref` alternatives before `fn_call`
6. **After `?atom`**: Insert `var_ref`, `prop_ref`, `idx_ref`, `nested_ref` rule definitions

## Integration with Existing `?expr` Precedence Chain

Current chain (lowest to highest precedence):
```
?expr -> ?or_expr -> ?and_expr -> ?cmp_expr -> ?add_expr -> ?mul_expr -> ?unary_expr -> ?atom
```

New chain:
```
?expr -> pipe_expr -> ?or_expr -> ?and_expr -> ?cmp_expr -> ?add_expr -> ?mul_expr -> ?unary_expr -> ?atom
```

`pipe_expr` is NOT `?`-prefixed because:
- When `|>` is present, we need the `pipe_expr` tree node to survive for the transformer
- When `|>` is absent, the transformer's `pipe_expr` method receives `[single_child]` and passes it through

This matches pest where `pipe_expr = { or_expr ~ ("|>" ~ pipe_stage)* }` is a regular (non-silent) rule.

## Lark-Specific Considerations vs Pest

| Aspect | Pest | Lark | Resolution |
|--------|------|------|------------|
| Atomic rules | `@{ }` prevents inner whitespace | Not needed; Lark auto-skips WS via `%ignore WS` | No special handling needed |
| Compound-atomic | `${ }` for path_call_expr | Not available; use rule composition | `pipe_fn_ident` as a rule with explicit IDENT tokens |
| Silent rules | `_{ }` removes from tree | `?rule` makes transparent | Use `?` for precedence-climbing intermediates |
| Terminal priority | Ordered by specificity | Use `IDENT.1` priority syntax or structural scoping | Scope `PIPE_FN_IDENT` usage to pipe_stage only (use rule, not terminal) |
| Operator token | `"|>"` literal | `"|>"` literal | Same |
| `@` prefix | `${ "@" ~ ident }` | `"@" IDENT` in a rule | `var_ref` rule handles it |

## Testing Strategy

- Grammar loads without Lark errors: `python -c "from tools.parser.ark_parser import get_parser; get_parser()"`
- Existing parse still works: `python ark.py parse specs/test_minimal.ark`
- New rules parse correctly: verified by T006 (transformer) and T022 (pipe tests)
- Regression: existing tests in `tests/` continue to pass

## Risks

1. **Earley ambiguity with `[` token**: `prop_ref` and `array_expr` both start with `[`. Earley parser will explore both paths. `prop_ref` requires `IDENT ("." IDENT)+` which is more specific than `expr_list?`. For `[x]` (single ident), only `array_expr` matches since `prop_ref` requires at least one dot. For `[x.y]`, Earley should prefer `prop_ref` because it matches the structure exactly. If ambiguity arises, we can add a negative lookahead or use `?atom` ordering. **Mitigation**: Test both forms in T022.

2. **`nested_ref` with `{expr}` vs other `{...}` uses**: The braces `{...}` appear in `enum_constraint`, `inline_enum_type`, `memory_stmt`, `process_body`, etc. All of these are in structurally distinct parse positions (not inside `?atom`). The only potential confusion is if an expression contains bare `{...}` -- but Ark has no block-expression syntax, so `nested_ref` is the only `{`-prefixed `?atom` alternative. Safe.

3. **`pipe_expr` always wrapping**: Since `pipe_expr` is not `?`-prefixed, every expression will produce a `pipe_expr` tree node even when there's no pipe. The transformer (T006) must handle this by unwrapping single-child pipe_expr nodes. This is the same pattern used in pest where `expression = { pipe_expr }` always wraps.
