# ADV001-T002: Extend pest grammar with pipe and expression/predicate items - Design

## Approach

Add 10 new grammar rules to `R:/Sandbox/ark/dsl/grammar/ark.pest` that implement the pipe expression operator (`|>`), parameter reference sigils (`@var`, `[a.b]`, `#name[n]`, `{expr}`), kebab-case function identifiers inside pipe stages, and top-level `expression` / `predicate` item definitions. Wire them into the existing precedence chain and item rule.

## Target Files

- `R:/Sandbox/ark/dsl/grammar/ark.pest` - All changes in this single file

## Implementation Steps

### Step 1: Add `expression_def` and `predicate_def` to the `item` rule (line 21-29)

Change the `item` rule to include the two new top-level items. They must appear **before** `verify_def` so the parser tries them before falling through to verify:

```pest
item = _{
    abstraction_def
  | class_def
  | instance_def
  | island_def
  | bridge_def
  | registry_def
  | expression_def
  | predicate_def
  | verify_def
}
```

### Step 2: Add `expression_def` and `predicate_def` rules (after `verify_def` block, after line 120)

Insert a new section after the VERIFY section (line 120):

```pest
// ============================================================
// EXPRESSION & PREDICATE ITEMS
// ============================================================

expression_def = { "expression" ~ ident ~ "{" ~ expression_body ~ "}" }
predicate_def  = { "predicate"  ~ ident ~ "{" ~ predicate_body  ~ "}" }

expression_body = { "in:" ~ typed_field_list ~ "out:" ~ type_expr ~ "chain:" ~ expression }
predicate_body  = { "in:" ~ typed_field_list ~ "check:" ~ expression }
```

**Notes:**
- `expression_body` uses `expression` (not a separate `chain_expr`) because `expression` already wraps the full precedence chain -- after Step 3, it will wrap `pipe_expr` which wraps `or_expr`, so pipe chains work naturally inside `chain:`.
- `predicate_body.check` also uses `expression` -- the Bool type constraint is enforced at the semantic level (type-checker), not the grammar level.
- Both use `typed_field_list` for their `in:` clause, reusing the existing rule at line 223.

### Step 3: Wire `pipe_expr` into the expression precedence chain (lines 145-146)

The current chain is:
```
expression -> or_expr -> and_expr -> cmp_expr -> add_expr -> mul_expr -> unary_expr -> atom
```

Change to:
```
expression -> pipe_expr -> or_expr -> and_expr -> cmp_expr -> add_expr -> mul_expr -> unary_expr -> atom
```

This makes `|>` the **lowest precedence** binary operator (below `or`), which is correct: `x |> f or y` parses as `(x |> f) or y`, and `a or b |> f` parses as `(a or b) |> f`.

Replace lines 145-146:
```pest
// OLD:
expression = { or_expr }

// NEW:
expression = { pipe_expr }
pipe_expr  = { or_expr ~ ("|>" ~ pipe_stage)* }
```

### Step 4: Add `pipe_stage` and `pipe_fn_ident` rules (immediately after `pipe_expr`)

```pest
pipe_stage    = { pipe_fn_ident ~ call_tail? }
pipe_fn_ident = @{ (ASCII_ALPHA | "_") ~ (ASCII_ALPHANUMERIC | "_")* ~ ("-" ~ (ASCII_ALPHA | "_") ~ (ASCII_ALPHANUMERIC | "_")*)* }
```

**pest-specific notes on `pipe_fn_ident`:**
- The `@{ ... }` (atomic) modifier is critical: it prevents implicit whitespace consumption between the identifier parts and hyphens. Without atomic, `text - to` (with spaces) would match, which is wrong.
- The rule allows standard identifiers (`clamp`, `abs`) AND kebab-case identifiers (`text-to-lower`, `null-to-zero`, `first-of-month`).
- Each hyphenated segment must start with a letter or underscore (not a digit), preventing ambiguity with subtraction: `foo-3` would NOT match as a kebab ident because `3` fails `(ASCII_ALPHA | "_")`.
- This rule is ONLY referenced from `pipe_stage`, so kebab-case identifiers are syntactically impossible outside pipe contexts. The existing `ident` rule (line 236) is unchanged and does NOT allow hyphens.

### Step 5: Add parameter reference rules to `atom` (lines 164-173)

Add the four parameter reference forms to the `atom` rule, **before** `path_call_expr` so sigils take lexical priority:

```pest
atom = _{
    paren_expr
  | array_expr
  | for_all_expr
  | number_expr
  | string_expr
  | true_expr
  | false_expr
  | var_ref
  | prop_ref
  | idx_ref
  | nested_ref
  | path_call_expr
}
```

### Step 6: Add parameter reference rule definitions (after `for_all_expr`, before `path_call_expr` definition, around line 182)

```pest
// Parameter references (Expressif-style sigils)
var_ref    = ${ "@" ~ ident }
prop_ref   = { "[" ~ ident ~ ("." ~ ident)+ ~ "]" }
idx_ref    = ${ "#" ~ ident ~ "[" ~ number ~ "]" }
nested_ref = { "{" ~ expression ~ "}" }
```

**pest-specific notes:**
- `var_ref` uses `${ ... }` (compound atomic): no implicit whitespace between `@` and the identifier, but the inner `ident` rule is still visible in the parse tree. This ensures `@ foo` (with space) does NOT match, but the `ident` child node is accessible in `parse.rs`.
- `idx_ref` also uses `${ ... }` for the same reason: `# items [ 0 ]` should not match, but `#items[0]` should, and the inner `ident` and `number` nodes must be accessible.
- `prop_ref` does NOT need compound-atomic because the `[` and `]` brackets already delimit it unambiguously. Whitespace inside brackets is fine: `[ a.b.c ]` is acceptable.
- `prop_ref` requires `("." ~ ident)+` (at least two path segments) -- a single-ident `[x]` remains an `array_expr`. This avoids ambiguity with existing array literal syntax.
- `nested_ref` uses `{ ... }` braces. This is safe because `nested_ref` only appears in `atom`, and the existing `enum_constraint` rule (line 208) only appears after `$data` type declarations. There is no ambiguity because the parser tries `atom` alternatives in order, and `nested_ref` contains an `expression` while `enum_constraint` requires comma-separated values after a `type_expr`.

### Collision Analysis

| New rule | Potential collision | Resolution |
|----------|-------------------|------------|
| `var_ref` (`@ident`) | `@in`, `@out` keywords | No collision: `@in` and `@out` are matched by `in_port` / `out_port` rules at the entity_member level, never inside `atom`. `var_ref` only appears inside expressions. |
| `prop_ref` (`[a.b.c]`) | `array_expr` (`[expr, ...]`) | No collision: `prop_ref` requires dotted identifiers (`ident ~ ("." ~ ident)+`), while `array_expr` contains arbitrary expressions. Single `[x]` stays `array_expr`. Ordering in `atom` puts `array_expr` before `prop_ref`. |
| `idx_ref` (`#name[n]`) | `#process` keyword | No collision: `#process` is matched by `process_rule` at entity_member level. `idx_ref` only appears inside expressions via `atom`. |
| `nested_ref` (`{expr}`) | `enum_constraint` (`{v1, v2}`) | No collision: `enum_constraint` is referenced only from `constraint` (line 206), which is referenced only from `data_field`. `nested_ref` is in `atom`, a completely separate parse path. |
| `pipe_fn_ident` (kebab-case) | `ident` (no hyphens) | No collision: `pipe_fn_ident` is only referenced from `pipe_stage`. The existing `ident` rule is unchanged. |
| `"|>"` operator | No existing `|>` usage | Clean introduction. The existing `or` keyword is textual, not `|`-based. |

### Complete Rule Placement Summary

| Rule | Insert after | Line reference |
|------|-------------|----------------|
| `expression_def`, `predicate_def` in `item` | after `registry_def` | line 28 |
| `expression_def`, `predicate_def` definitions | after `verify_def` block (line 120) | new section |
| `expression_body`, `predicate_body` | with their parent defs | same new section |
| `pipe_expr` | replaces `expression` body | line 145 |
| `pipe_stage`, `pipe_fn_ident` | after `pipe_expr` | new lines after 146 |
| `var_ref`, `prop_ref`, `idx_ref`, `nested_ref` in `atom` | before `path_call_expr` | line 172-173 |
| `var_ref`, `prop_ref`, `idx_ref`, `nested_ref` definitions | after `for_all_expr` def | after line 182 |

## Testing Strategy

Per the test strategy document, this task's grammar changes are validated by:
- `cargo build -p ark-dsl` -- grammar compiles (acceptance criterion)
- `cargo test -p ark-dsl` -- existing tests still pass (acceptance criterion)
- Rule names match design 02 exactly (acceptance criterion)

Downstream tasks (T004, T005, T006, T022) will write the actual parse tests that exercise these rules through the Python and Rust parsers.

## Risks

1. **`prop_ref` vs `array_expr` ordering in `atom`**: `array_expr` is listed first, so `[x]` will always match as an array. But `[a.b]` starts with `[` too -- pest will try `array_expr` first and succeed (treating `a.b` as a dotted path expression inside brackets). To fix this, `prop_ref` must come BEFORE `array_expr` in the `atom` rule, OR the `prop_ref` rule must be structured so it does not conflict. Since `prop_ref` requires `ident ~ ("." ~ ident)+` (purely identifiers with dots, no operators), and `array_expr` allows arbitrary expressions, the safest approach is: put `prop_ref` BEFORE `array_expr` in `atom`. pest tries alternatives in order and `prop_ref` will only match when the content is strictly dotted identifiers.

2. **pest implicit whitespace**: The WHITESPACE rule is silent (`_{ ... }`), so pest automatically allows whitespace between tokens in non-atomic rules. This means `x |> f` works with or without spaces. But inside `@{ ... }` and `${ ... }` rules, NO whitespace is consumed -- critical for `pipe_fn_ident`, `var_ref`, and `idx_ref`.

3. **`nested_ref` recursion**: `nested_ref` contains `expression`, which contains `pipe_expr`, which contains `or_expr`, etc. This is safe PEG recursion (no left-recursion). The `{` brace is the unambiguous entry token.
