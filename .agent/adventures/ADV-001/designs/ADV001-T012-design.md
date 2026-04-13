# Z3 Translation: Pipe and ParamRef Nodes - Design

## Approach

Extend `translate_expr` in `ark_verify.py` to handle two new AST node kinds (`"pipe"` and `"param_ref"`) and add supporting infrastructure for expression registry lookup and primitive-to-Z3 mapping. The implementation follows Option B (decidable subset) from the design doc: numeric primitives get native Z3 ops, text length/equality use Z3 strings, and regex/temporal/file-io are opaque (uninterpreted functions).

## Target Files

- `R:/Sandbox/ark/tools/verify/ark_verify.py` - Add `pipe` and `param_ref` branches to `translate_expr`; add helper functions `translate_pipe`, `translate_param_ref`, `apply_stage`, `build_expr_registry`; add primitive-to-Z3 mapping dict; add `Function` import from z3
- `R:/Sandbox/ark/tests/test_verify_expression.py` - NEW: unit tests for pipe translation, param_ref translation, opaque primitive handling

## Implementation Steps

### 1. Add Z3 imports

Add `Function`, `StringSort`, `RealSort`, `IntSort`, `BoolSort`, `Select`, `Array` to the z3 import line at `ark_verify.py:13-17`.

### 2. Add primitive-to-Z3 mapping (after SymbolTable class, ~line 64)

Define a dict `NATIVE_PRIMITIVES` mapping stage names to Z3 operation lambdas:

```python
NATIVE_PRIMITIVES = {
    # Numeric → direct Z3 arithmetic
    "abs":          lambda val, args: If(val >= 0, val, -val),
    "add":          lambda val, args: val + args[0],
    "sub":          lambda val, args: val - args[0],
    "mul":          lambda val, args: val * args[0],
    "div":          lambda val, args: val / args[0],
    "neg":          lambda val, args: -val,
    "ceil":         lambda val, args: val,   # approximation (Z3 Real has no ceil)
    "floor":        lambda val, args: val,   # approximation
    "round-to":     lambda val, args: val,   # approximation
    "pow":          lambda val, args: val,   # Z3 Real doesn't support general pow; approx
    "clamp-range":  lambda val, args: If(val < args[0], args[0], If(val > args[1], args[1], val)),
    "identity-fn":  lambda val, args: val,
    "default-float": lambda val, args: val,  # null handling → identity in SMT (no nulls)

    # Text → Z3 string theory (decidable subset)
    "str-len":      lambda val, args: Length(val),
}
```

Also add `If` and `Length` to the z3 imports.

### 3. Define opaque primitive set

```python
OPAQUE_PRIMITIVES = {
    "str-lower", "str-upper", "str-trim", "str-pad-right", "str-pad-left",
    "str-remove-chars", "str-substring", "str-replace",
    "str-starts-with", "str-ends-with", "str-contains",
    "str-matches",
    # temporal / file-io deferred
}
```

For each opaque primitive, create an uninterpreted `Function` on first use, cached in a module-level dict `_opaque_cache`.

### 4. Add `build_expr_registry` function

```python
def build_expr_registry(items: list) -> dict:
    """Scan parsed items for Item::Expression, return {name: ExpressionDef}."""
    registry = {}
    for item in items:
        if isinstance(item, dict) and item.get("item") == "expression":
            registry[item["name"]] = item
    return registry
```

This is called once at verify-time (in `verify_file` or the caller). For this task, it can be passed as an optional parameter to `translate_expr` (default `None`), or threaded via a context object. Simplest: add optional `expr_registry=None` parameter to `translate_expr`.

### 5. Extend `translate_expr` for `kind == "pipe"`

Insert new `elif` branch in `translate_expr` (before the final `raise`):

```python
elif kind == "pipe":
    return translate_pipe(expr, syms, expr_registry)
```

Implement `translate_pipe`:

```python
def translate_pipe(expr: dict, syms: SymbolTable, expr_registry: dict = None):
    val = translate_expr(expr["head"], syms, expr_registry)
    for stage in expr.get("stages", []):
        val = apply_stage(val, stage, syms, expr_registry)
    return val
```

Implement `apply_stage`:

```python
def apply_stage(val, stage: dict, syms: SymbolTable, expr_registry: dict = None):
    name = stage["name"]
    args = [translate_expr(a, syms, expr_registry) for a in stage.get("args", [])]

    # 1. Native Z3 primitive?
    if name in NATIVE_PRIMITIVES:
        return NATIVE_PRIMITIVES[name](val, args)

    # 2. User-defined expression in registry?
    if expr_registry and name in expr_registry:
        return inline_expression(val, args, expr_registry[name], syms, expr_registry)

    # 3. Opaque primitive?
    if name in OPAQUE_PRIMITIVES:
        return apply_opaque(name, val, args)

    # 4. Unknown → error with candidates
    candidates = sorted(
        set(list(NATIVE_PRIMITIVES.keys()) + list(OPAQUE_PRIMITIVES) +
            list((expr_registry or {}).keys()))
    )
    raise ValueError(f"Unknown pipe stage '{name}'. Valid stages: {candidates[:5]}...")
```

### 6. Implement `inline_expression`

Alpha-rename the expression's inputs and recursively translate its chain:

```python
def inline_expression(val, extra_args, expr_def, syms, expr_registry, _seen=None):
    """Inline a user-defined ExpressionDef by binding its inputs."""
    _seen = _seen or set()
    name = expr_def["name"]
    if name in _seen:
        raise ValueError(f"Recursive expression: '{name}' references itself")
    _seen = _seen | {name}

    inputs = expr_def.get("inputs", [])
    chain = expr_def.get("chain")
    if not chain:
        return val

    # Build a local symbol table with input bindings
    local_syms = SymbolTable()
    # Copy parent symbols
    local_syms.vars = dict(syms.vars)
    local_syms.vars_next = dict(syms.vars_next)
    # Bind first input to piped value
    if inputs:
        local_syms.vars[inputs[0]["name"]] = val
    # Bind remaining inputs to extra args
    for i, inp in enumerate(inputs[1:]):
        if i < len(extra_args):
            local_syms.vars[inp["name"]] = extra_args[i]

    return translate_expr(chain, local_syms, expr_registry)
```

### 7. Implement `apply_opaque`

```python
_opaque_cache = {}

def apply_opaque(name, val, args):
    """Wrap an opaque primitive as an uninterpreted Z3 function."""
    key = (name, len(args))
    if key not in _opaque_cache:
        # Build sort signature: val_sort, *arg_sorts → result_sort
        # Default: all RealSort for now; refine later
        from z3 import RealSort, StringSort, BoolSort
        # Heuristic: if name starts with "str-", input/output are StringSort
        if name.startswith("str-"):
            in_sorts = [StringSort()] * (1 + len(args))
            out_sort = StringSort()
            if name in ("str-starts-with", "str-ends-with", "str-contains", "str-matches"):
                out_sort = BoolSort()
        else:
            in_sorts = [RealSort()] * (1 + len(args))
            out_sort = RealSort()
        _opaque_cache[key] = Function(name.replace("-", "_"), *in_sorts, out_sort)
    fn = _opaque_cache[key]
    return fn(val, *args)
```

### 8. Extend `translate_expr` for `kind == "param_ref"`

```python
elif kind == "param_ref":
    return translate_param_ref(expr, syms, expr_registry)
```

Implement `translate_param_ref`:

```python
def translate_param_ref(expr: dict, syms: SymbolTable, expr_registry=None):
    ref_kind = expr.get("ref_kind")

    if ref_kind == "var":
        # @variable → same as ident
        name = expr["name"]
        return syms.get(name)

    elif ref_kind == "prop":
        # [a.b.c] → join with dots, delegate to syms.get
        path = ".".join(expr["parts"])
        return syms.get(path)

    elif ref_kind == "idx":
        # #collection[n] → Z3 Array Select
        name = expr["name"]
        index = expr.get("index", 0)
        arr = Array(name, IntSort(), RealSort())
        return Select(arr, IntVal(int(index)))

    elif ref_kind == "nested":
        # {expression} → recursively translate
        return translate_expr(expr["inner"], syms, expr_registry)

    raise ValueError(f"Unknown param_ref kind: {ref_kind}")
```

### 9. Thread `expr_registry` parameter

Update `translate_expr` signature from `def translate_expr(expr: dict, syms: SymbolTable)` to `def translate_expr(expr: dict, syms: SymbolTable, expr_registry: dict = None)`.

Update ALL existing callers of `translate_expr` within `ark_verify.py` to pass through `expr_registry` where available (or leave as None for backward compatibility). Key call sites:
- `_translate_body_equations` (line ~349) - add optional `expr_registry` param
- `check_invariants_hold` (line ~458-459) - pass `expr_registry` if available
- `check_data_constraints` (line ~285-286) - no change needed (no pipes in constraints)

For backward compat, all new params default to `None`, so existing callers work unchanged.

### 10. Write unit tests (`test_verify_expression.py`)

Test cases:
1. **Simple numeric pipe**: `{"expr": "pipe", "head": {"expr": "number", "value": 5}, "stages": [{"name": "add", "args": [{"expr": "number", "value": 3}]}]}` → should equal `IntVal(8)` (or simplify to 8)
2. **Multi-stage pipe**: head=10, stages=[sub(3), mul(2)] → should equal 14
3. **ParamRef var**: `{"expr": "param_ref", "ref_kind": "var", "name": "x"}` → resolves to `syms.get("x")`
4. **ParamRef prop**: `{"expr": "param_ref", "ref_kind": "prop", "parts": ["a", "b"]}` → resolves to `syms.get("a.b")`
5. **ParamRef idx**: `{"expr": "param_ref", "ref_kind": "idx", "name": "items", "index": 2}` → returns Z3 `Select`
6. **ParamRef nested**: recursive translation of inner expr
7. **Opaque stage**: `str-lower` produces an uninterpreted function application (no crash, result is a Z3 expr)
8. **Unknown stage**: raises `ValueError` with helpful message
9. **User-defined expression inline**: register a simple expression in registry, pipe through it
10. **Recursive expression detection**: expression referencing itself raises ValueError

## Integration with Existing Verify Flow

The changes are backward-compatible:
- `translate_expr` gains an optional `expr_registry` parameter (default `None`)
- All existing call paths pass `None` implicitly, hitting no new code
- When `verify_file` is extended (future task) to scan for `Item::Expression` items and build the registry, it passes the registry into the verify calls
- The `build_expr_registry` function is available but not auto-invoked yet (that belongs to the Expression/Predicate verify integration, a separate task)

## Testing Strategy

- Run existing tests: `pytest tests/test_verify_full_expr.py tests/test_verify_bridges.py tests/test_verify_temporal.py` must stay green
- Run new tests: `pytest tests/test_verify_expression.py`
- Each test constructs AST dicts directly (no parser dependency) and calls `translate_expr` / `translate_pipe` to verify Z3 output

## Risks

- **Z3 `If` import**: need to add `If` to the z3 import line; if missed, `clamp-range` and `abs` will fail at runtime
- **Sort mismatches**: piping a String value into a numeric stage (e.g., `"hello" |> add(3)`) will produce a Z3 sort error. For now, let Z3 raise naturally; future work adds type checking before translation
- **`Array` import**: needed for `idx` param_ref; must be added to z3 import line
- **Thread safety of `_opaque_cache`**: not an issue for single-threaded CLI usage
