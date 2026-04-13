# Grammar & Parser Extensions — Design

## Overview

Extend the two parallel Ark grammars (pest for Rust, Lark for Python) and their AST builders
to accept the new expression / predicate syntax from `01_dsl_surface.md`. The canonical rule is
**grammar parity**: every production added to `ark.pest` must have a corresponding Lark rule and
vice versa. The test suite (`R:/Sandbox/ark/tests/test_parser_expressions.py`) enforces this by
round-tripping the same inputs through both parsers.

## Target Files

- `R:/Sandbox/ark/dsl/grammar/ark.pest` — add rules, wire into precedence
- `R:/Sandbox/ark/dsl/src/lib.rs` — extend `Expr`, add `ExpressionDef`, `PredicateDef`,
  `PipeStage`, `ParamRef`, `RefKind`
- `R:/Sandbox/ark/dsl/src/parse.rs` — new `*_from_pair` functions
- `R:/Sandbox/ark/tools/parser/ark_grammar.lark` — mirror the pest grammar
- `R:/Sandbox/ark/tools/parser/ark_parser.py` — extend `Transformer` with new methods and
  dataclass emitters; mirror JSON schema

## Grammar changes (pest — canonical)

### New top-level items

```pest
item = _{
    abstraction_def
  | class_def
  | instance_def
  | island_def
  | bridge_def
  | registry_def
  | verify_def
  | expression_def        // NEW
  | predicate_def         // NEW
}

expression_def = { "expression" ~ ident ~ "{" ~ expression_body ~ "}" }
predicate_def  = { "predicate"  ~ ident ~ "{" ~ predicate_body  ~ "}" }

expression_body = { "in:" ~ typed_field_list ~ "out:" ~ type_expr ~ "chain:" ~ chain_expr }
predicate_body  = { "in:" ~ typed_field_list ~ "check:" ~ expression }
```

### Pipe operator

Threaded at a new precedence level sitting just above `or_expr` so boolean combinators still
form the outermost layer:

```pest
expression = { pipe_expr }
pipe_expr  = { or_expr ~ ("|>" ~ pipe_stage)* }
pipe_stage = { pipe_fn_ident ~ call_tail? }
pipe_fn_ident = @{ ident ~ ("-" ~ ident)* }   // supports text-to-lower, null-to-zero, etc.
```

Note the `pipe_fn_ident` rule: Expressif function names are kebab-case (`text-to-lower`,
`first-of-month`). Ark's existing `ident` rule only allows `[a-zA-Z_][a-zA-Z0-9_']*`. We need
kebab-case **inside pipe stages only** to stay Expressif-compatible.

### Parameter references

```pest
param_ref = _{ var_ref | prop_ref | idx_ref | nested_ref }
var_ref    = ${ "@" ~ ident }
prop_ref   = { "[" ~ ident ~ ("." ~ ident)+ ~ "]" }    // dotted only — single-ident stays array_expr
idx_ref    = ${ "#" ~ ident ~ "[" ~ number ~ "]" }
nested_ref = { "{" ~ expression ~ "}" }
```

Added to `atom` rule **before** `path_call_expr` so sigils take priority over bare idents.

### Grammar parity (Lark)

Mirror every rule verbatim in `ark_grammar.lark`. Lark's precedence uses `?` prefix on rules;
the pipe rule is inserted between `?expr` and `?or_expr`. Transformer method `pipe_expr` builds
a `{"expr": "pipe", "head": ..., "stages": [...]}` dict.

## AST additions (Rust)

In `R:/Sandbox/ark/dsl/src/lib.rs`:

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Expr {
    // ... existing variants
    Pipe(Box<Expr>, Vec<PipeStage>),
    ParamRef(RefKind, String, Vec<String>, Option<i64>),  // kind, head, dotted parts, idx
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RefKind { Var, Prop, Idx, Nested }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PipeStage {
    pub name: String,            // e.g., "text-to-lower"
    pub args: Vec<Expr>,         // extra args beyond the piped value
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExpressionDef {
    pub name: String,
    pub inputs: Vec<TypedField>,
    pub output: TypeExpr,
    pub chain: Expr,             // always a Pipe or a single atom
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PredicateDef {
    pub name: String,
    pub inputs: Vec<TypedField>,
    pub check: Expr,             // must type-check to Bool
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "kind")]
pub enum Item {
    // ... existing variants
    Expression(ExpressionDef),
    Predicate(PredicateDef),
}
```

## AST additions (Python, `ark_parser.py`)

Mirror the dataclass shapes exactly so JSON output from both parsers is bitwise identical.
Add dataclasses `ExpressionDef`, `PredicateDef`, `PipeStage`, and pipe/paramref expression
node emitters. The `Transformer` in `ark_parser.py` around line 380 (`fn_call`) is the
anchor point for the new `pipe_expr`, `pipe_stage`, `var_ref`, `prop_ref`, `idx_ref`,
`nested_ref` methods.

## Parity test

Add `R:/Sandbox/ark/tests/test_parser_pipe.py` that feeds identical source strings to both
Python and Rust parsers (via `cargo run --bin ark-dsl-parse --` shim or by reading AST from
the Rust test binary) and asserts the JSON outputs match. For v1, a Python-only test is
acceptable because both grammars are hand-mirrored; a parity harness is added in a follow-up.

## Target Conditions

- TC-003 — `|>` operator parses left-associative (covered here via grammar task)
- TC-004 — parameter reference sigils parse into tagged nodes
- TC-006 — kebab-case function names inside pipe stages accepted; rejected outside pipe stages
- TC-007 — `expression` and `predicate` top-level items reach the AST with all fields populated
- TC-008 — Error messages for malformed pipe / param-ref include file:line:col via `ArkParseError`

## Dependencies

- `01_dsl_surface.md` (this design implements the surface proposal)

## Risks

- **Kebab-case idents** are a lexical escape hatch. Must be scoped strictly to pipe stages to
  avoid confusion (`x-y` should still be "x minus y" in arithmetic contexts). pest atomic rule
  `pipe_fn_ident` achieves this; Lark needs an equivalent rule used only in `pipe_stage`.
- **`{expression}` nested refs** collide with existing `{...}` block syntax (enum constraint,
  type inline enum, memory stmt body). Parsing context determines which applies — safe because
  `nested_ref` only appears in argument position inside a `pipe_stage` or `param_ref` slot.
- **Error UX**: `ArkParseError` already supports snippet+caret (see
  `R:/Sandbox/ark/tools/parser/ark_parser.py:24-55`). New rules must use the same error path.
