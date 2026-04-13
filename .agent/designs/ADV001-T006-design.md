# Python Parser Transformer for Pipe / Param Refs / Expression Items - Design

## Approach

Extend `ark_parser.py` with new dataclasses and `ArkTransformer` methods to handle the Lark tree nodes produced by T005's grammar additions. The grammar (already committed) produces `pipe_expr`, `pipe_stage`, `pipe_fn_ident`, `var_ref`, `prop_ref`, `idx_ref`, `nested_ref`, `expression_def`, `predicate_def`, `expression_body`, and `predicate_body` tree nodes. This task adds transformer methods to convert those tree nodes into Python dicts/dataclasses that serialize to JSON matching the schema in `entities.md`.

## Target Files

- `R:/Sandbox/ark/tools/parser/ark_parser.py` — Add dataclasses, transformer methods, update `start()`, `_build_indices()`, import resolution, and JSON serialization

## New Dataclasses

Add after `EnumDef` (line 255), before the `ArkFile` class:

### `ExpressionDef`
```python
@dataclass
class ExpressionDef:
    kind: str = "expression"
    name: str = ""
    inputs: list = field(default_factory=list)    # List of typed_field dicts
    output: dict = field(default_factory=dict)     # type_expr dict
    chain: dict = field(default_factory=dict)      # expr dict (pipe or single atom)
    description: Optional[str] = None
```

### `PredicateDef`
```python
@dataclass
class PredicateDef:
    kind: str = "predicate"
    name: str = ""
    inputs: list = field(default_factory=list)    # List of typed_field dicts
    check: dict = field(default_factory=dict)      # expr dict (must type-check to Bool)
    description: Optional[str] = None
```

### `PipeStage` (not a top-level item, used in pipe expressions)
```python
@dataclass
class PipeStage:
    name: str = ""          # kebab-case allowed, e.g. "text-to-lower"
    args: list = field(default_factory=list)  # extra args beyond piped value
```

Note: `ParamRef` and `RefKind` are NOT separate dataclasses. They are represented as expression dicts (like all other expressions in the Python parser). This matches the existing pattern where expressions are plain dicts with an `"expr"` key.

## New Transformer Methods

### `pipe_expr(self, items)` — after `fn_call` method (~line 387)

The grammar rule `pipe_expr: or_expr ("|>" pipe_stage)*` produces children: `[or_expr_result, pipe_stage_1, pipe_stage_2, ...]`. Since `pipe_expr` is NOT `?`-prefixed, it always fires.

```python
def pipe_expr(self, items):
    if len(items) == 1:
        return items[0]  # no pipe, pass through
    head = items[0]
    stages = [asdict(s) if hasattr(s, '__dataclass_fields__') else s for s in items[1:]]
    return {"expr": "pipe", "head": head, "stages": stages}
```

- When only one child: pass through (no wrapping) — identical to `or_expr` pattern
- When multiple children: first is the head expression, rest are PipeStage objects from `pipe_stage` method
- JSON shape: `{"expr": "pipe", "head": <expr>, "stages": [{"name": "...", "args": [...]}]}`

### `pipe_stage(self, items)` — immediately after `pipe_expr`

Grammar: `pipe_stage: pipe_fn_ident "(" expr_list? ")" | pipe_fn_ident`

```python
def pipe_stage(self, items):
    name = items[0]  # string from pipe_fn_ident
    args = items[1] if len(items) > 1 else []
    return PipeStage(name=name, args=args)
```

- `items[0]` is the joined kebab-case name from `pipe_fn_ident`
- `items[1]` (if present) is the `expr_list` result (a list of expr dicts)
- Returns a `PipeStage` dataclass instance

### `pipe_fn_ident(self, items)` — immediately after `pipe_stage`

Grammar: `pipe_fn_ident: IDENT ("-" IDENT)*`

Lark passes IDENT tokens as children. The "-" literal is consumed by the grammar but not passed as a child (it's a quoted literal, not a terminal). So items = `["text", "to", "lower"]` for `text-to-lower`.

```python
def pipe_fn_ident(self, items):
    return "-".join(str(i) for i in items)
```

- Joins all IDENT parts with hyphens to reconstruct the kebab-case name

### `var_ref(self, items)` — in the expressions section, before `fn_call`

Grammar: `var_ref: "@" IDENT`

The `"@"` literal is consumed; only IDENT arrives as child.

```python
def var_ref(self, items):
    return {"expr": "param_ref", "ref_kind": "var", "name": str(items[0])}
```

- JSON: `{"expr": "param_ref", "ref_kind": "var", "name": "variable_name"}`

### `prop_ref(self, items)`

Grammar: `prop_ref: "[" IDENT ("." IDENT)+ "]"`

Brackets and dots are consumed; items = list of IDENT tokens.

```python
def prop_ref(self, items):
    parts = [str(i) for i in items]
    return {"expr": "param_ref", "ref_kind": "prop", "parts": parts}
```

- JSON: `{"expr": "param_ref", "ref_kind": "prop", "parts": ["a", "b", "c"]}`

### `idx_ref(self, items)`

Grammar: `idx_ref: "#" IDENT "[" NUMBER "]"`

`#`, `[`, `]` consumed; items = [IDENT, NUMBER].

```python
def idx_ref(self, items):
    return {"expr": "param_ref", "ref_kind": "idx", "name": str(items[0]), "index": items[1]}
```

- JSON: `{"expr": "param_ref", "ref_kind": "idx", "name": "collection", "index": 0}`

### `nested_ref(self, items)`

Grammar: `nested_ref: "{" expr "}"`

Braces consumed; items = [inner_expr].

```python
def nested_ref(self, items):
    return {"expr": "param_ref", "ref_kind": "nested", "inner": items[0]}
```

- JSON: `{"expr": "param_ref", "ref_kind": "nested", "inner": <expr>}`

### `expression_def(self, items)` — in the entity definitions section

Grammar: `expression_def: "expression" IDENT "{" expression_body "}"` where `expression_body: "in:" typed_field_list "out:" type_expr "chain:" expr`

The `expression_body` rule produces 3 children: `[typed_field_list, type_expr, expr]`. The transformer receives `expression_def` items as `[IDENT, expression_body_result]`. But since `expression_body` is a named rule, we need a transformer method for it too, or let it pass through as a Tree.

Better approach: add an `expression_body` transformer that returns a tuple/dict, then use it in `expression_def`.

```python
def expression_body(self, items):
    # items: [typed_field_list, type_expr, chain_expr]
    return {"inputs": items[0], "output": items[1], "chain": items[2]}

def expression_def(self, items):
    name = str(items[0])
    body = items[1]
    return ExpressionDef(
        name=name,
        inputs=body["inputs"],
        output=body["output"],
        chain=body["chain"],
    )
```

### `predicate_def(self, items)`

Grammar: `predicate_def: "predicate" IDENT "{" predicate_body "}"` where `predicate_body: "in:" typed_field_list "check:" expr`

```python
def predicate_body(self, items):
    # items: [typed_field_list, check_expr]
    return {"inputs": items[0], "check": items[1]}

def predicate_def(self, items):
    name = str(items[0])
    body = items[1]
    return PredicateDef(
        name=name,
        inputs=body["inputs"],
        check=body["check"],
    )
```

## Changes to Existing Methods

### `start(self, items)` — line 813

Add `ExpressionDef` and `PredicateDef` to the isinstance check:

```python
def start(self, items):
    imports = []
    ark_items = []
    for item in items:
        if isinstance(item, list) and item and isinstance(item[0], str):
            imports.append(item)
        elif isinstance(item, (EntityDef, InstanceDef, IslandDef,
                               BridgeDef, RegistryDef, VerifyDef,
                               PrimitiveDef, StructDef, EnumDef,
                               ExpressionDef, PredicateDef)):
            ark_items.append(item)
    return ArkFile(imports=imports, items=ark_items)
```

### `ArkFile` dataclass — line 258

Add two new index fields:

```python
@dataclass
class ArkFile:
    imports: list = field(default_factory=list)
    items: list = field(default_factory=list)
    classes: dict = field(default_factory=dict)
    instances: dict = field(default_factory=dict)
    island_classes: dict = field(default_factory=dict)
    expression_index: dict = field(default_factory=dict)    # name -> index into items
    predicate_index: dict = field(default_factory=dict)     # name -> index into items
```

### `_build_indices(ark_file)` — line 926

Add expression and predicate index construction:

```python
def _build_indices(ark_file: ArkFile) -> ArkFile:
    classes: dict = {}
    instances: dict = {}
    island_classes: dict = {}
    expression_index: dict = {}
    predicate_index: dict = {}
    for idx, item in enumerate(ark_file.items):
        if isinstance(item, EntityDef) and item.kind == "class":
            classes[item.name] = item
        elif isinstance(item, InstanceDef):
            instances.setdefault(item.class_name, []).append(item)
        elif isinstance(item, IslandDef):
            nested: dict = {}
            for nested_item in getattr(item, "classes", []) or []:
                if isinstance(nested_item, EntityDef) and nested_item.kind == "class":
                    nested[nested_item.name] = nested_item
            if nested:
                island_classes[item.name] = nested
        elif isinstance(item, ExpressionDef):
            expression_index[item.name] = idx
        elif isinstance(item, PredicateDef):
            predicate_index[item.name] = idx
    ark_file.classes = classes
    ark_file.instances = instances
    ark_file.island_classes = island_classes
    ark_file.expression_index = expression_index
    ark_file.predicate_index = predicate_index
    return ark_file
```

**Important note**: The current `_build_indices` iterates without `enumerate` and stores EntityDef objects directly in `classes` (not indices). To maintain backward compatibility, do NOT change the classes/instances pattern. Only use `enumerate` index for expression_index/predicate_index. Keep the existing `classes[item.name] = item` pattern. This means expression_index and predicate_index store integer indices while classes stores objects -- a small inconsistency but safe.

## Import Resolution

The import resolver `_resolve_import_path` already handles `import stdlib.X` by mapping to `<ark_root>/dsl/stdlib/X.ark`. For `import stdlib.expression` and `import stdlib.predicate`:

1. Create files: `R:/Sandbox/ark/dsl/stdlib/expression.ark` and `R:/Sandbox/ark/dsl/stdlib/predicate.ark` -- but this is NOT T006 scope (it's a separate stdlib catalogue task). T006 only needs to ensure the parser can handle ExpressionDef/PredicateDef items when they arrive via import resolution.

2. The existing `import_resolve` function in `ark_parser.py` already handles this generically:
   - It parses the imported file via `_parse_no_resolve`
   - Merges `sub_ast.items` into `ark_file.items`
   - Since `_parse_no_resolve` uses `ArkTransformer` which now handles `expression_def` and `predicate_def`, any imported `.ark` file containing these items will be correctly parsed and merged.
   - `_build_indices` runs AFTER import resolution, so merged items from imports are included in the indices.

No changes to import resolution code are needed -- it's already generic enough.

## JSON Serialization

The `to_json` function uses `asdict()` for dataclasses, which handles `ExpressionDef`, `PredicateDef`, and `PipeStage` automatically. The `PipeStage` inside a pipe expression dict needs explicit handling since it's nested inside a plain dict. The `pipe_expr` transformer method should convert PipeStage to dict before embedding:

In `pipe_expr`:
```python
stages = [{"name": s.name, "args": s.args} for s in items[1:]]
```

This produces clean JSON without the dataclass-to-dict overhead.

### Expected JSON shapes

**Pipe expression**:
```json
{
  "expr": "pipe",
  "head": {"expr": "ident", "name": "x"},
  "stages": [
    {"name": "text-to-lower", "args": []},
    {"name": "trim", "args": [{"expr": "number", "value": 5}]}
  ]
}
```

**Var ref**: `{"expr": "param_ref", "ref_kind": "var", "name": "amount"}`

**Prop ref**: `{"expr": "param_ref", "ref_kind": "prop", "parts": ["order", "total"]}`

**Idx ref**: `{"expr": "param_ref", "ref_kind": "idx", "name": "items", "index": 0}`

**Nested ref**: `{"expr": "param_ref", "ref_kind": "nested", "inner": {"expr": "ident", "name": "x"}}`

**ExpressionDef** (as item, via `asdict`):
```json
{
  "kind": "expression",
  "name": "NormalizeAmount",
  "inputs": [{"name": "raw", "type": {"type": "named", "name": "Float"}}],
  "output": {"type": "named", "name": "Float"},
  "chain": {"expr": "pipe", "head": ..., "stages": [...]},
  "description": null
}
```

**PredicateDef**:
```json
{
  "kind": "predicate",
  "name": "IsPositive",
  "inputs": [{"name": "val", "type": {"type": "named", "name": "Float"}}],
  "check": {"expr": "binop", "op": ">", "left": ..., "right": ...},
  "description": null
}
```

## Implementation Steps

1. Add `ExpressionDef`, `PredicateDef`, `PipeStage` dataclasses after `EnumDef` (line 255)
2. Add `expression_index` and `predicate_index` fields to `ArkFile` dataclass (line 258-270)
3. Add transformer methods in order:
   a. `pipe_expr` — after existing `fn_call` method (line 387)
   b. `pipe_stage` — after `pipe_expr`
   c. `pipe_fn_ident` — after `pipe_stage`
   d. `var_ref`, `prop_ref`, `idx_ref`, `nested_ref` — group together after `pipe_fn_ident`
   e. `expression_body`, `expression_def` — in entity definitions section (~line 740 area)
   f. `predicate_body`, `predicate_def` — right after `expression_def`
4. Update `start()` method isinstance tuple to include `ExpressionDef, PredicateDef`
5. Update `_build_indices()` to populate `expression_index` and `predicate_index` using `enumerate`
6. Verify JSON serialization works (PipeStage inside pipe dict must be plain dict, not dataclass)

## Testing Strategy

- Run `pytest tests/test_parser_*.py -q` to ensure no regressions
- Run `python ark.py parse specs/test_minimal.ark` for smoke test
- Manual validation: parse a source string containing `expression`, `predicate`, pipe `|>`, and param refs (`@x`, `[a.b]`, `#c[0]`, `{expr}`) -- this will be covered by T022 (pipe tests)
- Key edge cases to verify:
  - Single-child pipe_expr passthrough (no `|>` present)
  - Kebab-case fn names: `text-to-lower`
  - Empty args vs with-args pipe stages
  - Prop ref requires 2+ dotted parts (single `[x]` stays as array_expr)

## Risks

1. **PipeStage serialization**: If `pipe_expr` returns PipeStage dataclasses embedded in a dict, `to_json`'s `convert` function may not recurse into dict values containing dataclasses. Mitigation: convert PipeStage to dict inline in `pipe_expr` method (as designed above).

2. **pipe_fn_ident children**: Lark may or may not pass the literal `"-"` as a child. Need to verify. If it does, filter out non-IDENT tokens. The design assumes literals are consumed (standard Lark behavior for quoted strings).

3. **Backward compatibility of _build_indices**: The current code does not use `enumerate`. Adding `enumerate` changes the loop variable. Must be careful to keep existing `classes[item.name] = item` pattern unchanged. The expression_index/predicate_index use integer indices -- a divergence from the existing pattern but matching the Rust side's `BTreeMap<String, usize>`.
