# Entity Schemas — ADV-001

New AST entities introduced by this adventure. These extend
`R:/Sandbox/ark/dsl/src/lib.rs` and `R:/Sandbox/ark/tools/parser/ark_parser.py`.

## Entities

### ExpressionDef
Top-level `expression Foo { in: ..., out: T, chain: ... }` item.

- name: String (unique within file)
- inputs: Vec<TypedField>    (at least one; first is the piped subject)
- output: TypeExpr
- chain: Expr                 (always `Expr::Pipe` or a single atom)
- description: Option<String>
- Relations: referenced by `Expr::FnCall` / `Expr::Pipe` stages by name; resolved via a new
  `ArkFile.expression_index: BTreeMap<String, usize>` built alongside `classes_index`

### PredicateDef
Top-level `predicate Bar { in: ..., check: ... }` item.

- name: String (unique within file)
- inputs: Vec<TypedField>
- check: Expr                 (must type-check to Bool)
- description: Option<String>
- Relations: `ArkFile.predicate_index: BTreeMap<String, usize>`

### PipeStage (not an Item, an expression sub-node)
One stage in a `|>` chain.

- name: String                (kebab-case allowed, e.g., "text-to-lower")
- args: Vec<Expr>             (extra args beyond the implicit piped value)
- Relations: owned by `Expr::Pipe`

### ParamRef (expression variant)
Tagged parameter reference distinct from bare `Ident`.

- kind: RefKind               (Var | Prop | Idx | Nested)
- head: String                (for Var/Idx the identifier)
- parts: Vec<String>          (for Prop the dotted path)
- index: Option<i64>          (for Idx the numeric index)
- nested: Option<Box<Expr>>   (for Nested the inner expression)

### RefKind (enum)
- Var    — `@variable`
- Prop   — `[a.b.c]`
- Idx    — `#collection[n]`
- Nested — `{expression}`

## Extended enums

### Item (add two variants)
- Abstraction(EntityDef) — existing
- Class(EntityDef) — existing
- Instance(InstanceDef) — existing
- Island(IslandDef) — existing
- Bridge(BridgeDef) — existing
- Registry(RegistryDef) — existing
- Verify(VerifyDef) — existing
- **Expression(ExpressionDef)** — NEW
- **Predicate(PredicateDef)** — NEW

### Expr (add two variants)
- Ident, Number, StringLit, Bool, DottedPath, BinOp, UnaryOp, FnCall, ForAll — existing
- **Pipe(Box<Expr>, Vec<PipeStage>)** — NEW
- **ParamRef(RefKind, String, Vec<String>, Option<i64>)** — NEW

## ArkFile index additions

- `expression_index: BTreeMap<String, usize>` — name → index into `items`
- `predicate_index: BTreeMap<String, usize>` — name → index into `items`

Both populated in `parse::build_indices` alongside existing class/instance indices.
