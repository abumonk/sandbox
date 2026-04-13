# Extend Rust AST with Pipe, ParamRef, ExpressionDef, PredicateDef - Design

## Approach

Add new types and enum variants to `dsl/src/lib.rs` to represent the Expressif expression and predication system in the Ark AST. This is a pure type-definition task -- no parser logic changes (that is T004). The grammar rules already exist in `ark.pest` (added by T002). This task makes the Rust AST capable of holding the parsed results.

All additions follow existing patterns: derive `Debug, Clone, Serialize, Deserialize`, use `BTreeMap` for indices (consistent with existing `classes_index`), and use `Box<Expr>` for recursive positions.

## Target Files

- `dsl/src/lib.rs` -- Add `RefKind` enum, `PipeStage` struct, `ExpressionDef` struct, `PredicateDef` struct; extend `Expr` enum with `Pipe` and `ParamRef` variants; extend `Item` enum with `Expression` and `Predicate` variants; add `expression_index` and `predicate_index` fields to `ArkFile`; add `expression()` and `predicate()` accessor methods on `ArkFile`
- `dsl/src/parse.rs` -- Extend `build_indices` to populate `expression_index` and `predicate_index` for `Item::Expression` and `Item::Predicate` variants; add `_ => {}` arm update (the existing wildcard already covers new variants, but the new indices need population)

## Implementation Steps

### Step 1: Add `RefKind` enum (lib.rs, after `Constraint` enum ~line 223)

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RefKind {
    Var,
    Prop,
    Idx,
    Nested,
}
```

### Step 2: Add `PipeStage` struct (lib.rs, after `RefKind`)

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PipeStage {
    pub name: String,
    pub args: Vec<Expr>,
}
```

### Step 3: Extend `Expr` enum (lib.rs, line 225-240)

Add two new variants after existing ones:

```rust
Pipe {
    head: Box<Expr>,
    stages: Vec<PipeStage>,
},
ParamRef {
    kind: RefKind,
    name: String,
    path: Vec<String>,
    index: Option<i64>,
    nested: Option<Box<Expr>>,
},
```

Note: Using struct-style variants (not tuple) for clarity. The `ParamRef` fields cover all four `RefKind` cases:
- `Var`: `name` = variable name, rest empty/None
- `Prop`: `path` = dotted segments
- `Idx`: `name` = collection name, `index` = Some(n)
- `Nested`: `nested` = Some(inner_expr)

### Step 4: Add `ExpressionDef` struct (lib.rs, after entities section)

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExpressionDef {
    pub name: String,
    pub inputs: Vec<TypedField>,
    pub output: TypeExpr,
    pub chain: Expr,
    pub description: Option<String>,
}
```

### Step 5: Add `PredicateDef` struct (lib.rs, after `ExpressionDef`)

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PredicateDef {
    pub name: String,
    pub inputs: Vec<TypedField>,
    pub check: Expr,
    pub description: Option<String>,
}
```

### Step 6: Extend `Item` enum (lib.rs, line 73-81)

Add two variants:

```rust
Expression(ExpressionDef),
Predicate(PredicateDef),
```

### Step 7: Add index fields to `ArkFile` (lib.rs, line 24-40)

Add after `island_classes_index`:

```rust
#[serde(default)]
pub expression_index: BTreeMap<String, usize>,
#[serde(default)]
pub predicate_index: BTreeMap<String, usize>,
```

### Step 8: Add accessor methods on `ArkFile` (lib.rs, after `class()` method)

```rust
pub fn expression(&self, name: &str) -> Option<&ExpressionDef> {
    let idx = *self.expression_index.get(name)?;
    match self.items.get(idx)? {
        Item::Expression(def) => Some(def),
        _ => None,
    }
}

pub fn predicate(&self, name: &str) -> Option<&PredicateDef> {
    let idx = *self.predicate_index.get(name)?;
    match self.items.get(idx)? {
        Item::Predicate(def) => Some(def),
        _ => None,
    }
}
```

### Step 9: Extend `build_indices` in parse.rs (line 34-63)

Add clearing and population for the two new indices:

```rust
file.expression_index.clear();
file.predicate_index.clear();
```

And in the match arms:

```rust
Item::Expression(def) => {
    file.expression_index.insert(def.name.clone(), idx);
}
Item::Predicate(def) => {
    file.predicate_index.insert(def.name.clone(), idx);
}
```

### Step 10: Verify compilation

Run `cargo build -p ark-dsl` and `cargo test -p ark-dsl` to ensure:
- All existing tests pass (empty_file_parses, ast_roundtrips_json)
- New types serialize/deserialize correctly
- No compilation errors from new variants in exhaustive matches

## Testing Strategy

1. **Compilation**: `cargo build -p ark-dsl` must succeed cleanly
2. **Existing tests**: `cargo test -p ark-dsl` -- both existing tests must pass
3. **Serialization roundtrip**: The `ast_roundtrips_json` test already validates JSON roundtrip for `ArkFile`; new fields have `#[serde(default)]` so empty files still roundtrip
4. **Manual spot-check**: Construct an `ArkFile` with `Item::Expression` and `Item::Predicate` in items, call `build_indices`, verify `expression()` and `predicate()` return correct references
5. **Exhaustive match audit**: Search parse.rs for any `match` on `Item` or `Expr` that is not using `_ =>` wildcard -- those would fail to compile with new variants (acts as automatic verification)

## Risks

- **Exhaustive matches**: If any code in `parse.rs` or elsewhere matches on `Expr` or `Item` without a wildcard, adding variants will cause compilation errors. The implementer must find and handle these (likely adding placeholder arms or `todo!()` for parser logic deferred to T004).
- **Serde tag collision**: `Item` uses `#[serde(tag = "kind")]` -- new variant names `Expression` and `Predicate` must not collide with existing tag values. They don't (existing: Abstraction, Class, Instance, Island, Bridge, Registry, Verify).
- **`Default` derive on `ArkFile`**: The new `BTreeMap` fields need `#[serde(default)]` and `BTreeMap` implements `Default`, so this is safe.
