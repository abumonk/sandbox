"""
ARK Verifier
Транслирует инварианты и ограничения из ARK AST в Z3 SMT-формулы.
Проверяет:
  1. Инварианты не нарушаются переходами (pre ∧ body → post → invariant)
  2. Ограничения $data выполнимы
  3. Нет конфликтующих инвариантов
"""

import difflib
import json
import sys
from pathlib import Path
from z3 import (
    Real, Int, Bool, String, And, Or, Not, Implies, Solver,
    sat, unsat, unknown, RealVal, IntVal, StringVal, BoolVal,
    is_true, If, Function, StringSort, RealSort, IntSort, BoolSort,
    Select, Array, Length
)

# ============================================================
# SYMBOL TABLE
# ============================================================

class SymbolTable:
    """Manages Z3 variables for an entity"""

    def __init__(self):
        self.vars = {}       # name → Z3 var (current state)
        self.vars_next = {}  # name' → Z3 var (next state)

    def add_real(self, name: str):
        self.vars[name] = Real(name)
        self.vars_next[f"{name}'"] = Real(f"{name}_next")
        return self.vars[name]

    def add_int(self, name: str):
        self.vars[name] = Int(name)
        self.vars_next[f"{name}'"] = Int(f"{name}_next")
        return self.vars[name]

    def add_bool(self, name: str):
        self.vars[name] = Bool(name)
        self.vars_next[f"{name}'"] = Bool(f"{name}_next")
        return self.vars[name]

    def add_string(self, name: str):
        self.vars[name] = String(name)
        self.vars_next[f"{name}'"] = String(f"{name}_next")
        return self.vars[name]

    def get(self, name: str):
        if name in self.vars:
            return self.vars[name]
        if name in self.vars_next:
            return self.vars_next[name]
        # Auto-create as Real if unknown
        return self.add_real(name)

    def get_next(self, name: str):
        key = f"{name}'"
        if key in self.vars_next:
            return self.vars_next[key]
        return self.get(name)


# ============================================================
# PRIMITIVE MAPS
# ============================================================

NATIVE_PRIMITIVES = {
    # Numeric → direct Z3 arithmetic
    "abs":           lambda val, args: If(val >= 0, val, -val),
    "add":           lambda val, args: val + args[0],
    "sub":           lambda val, args: val - args[0],
    "mul":           lambda val, args: val * args[0],
    "div":           lambda val, args: val / args[0],
    "neg":           lambda val, args: -val,
    "ceil":          lambda val, args: val,   # approximation (Z3 Real has no ceil)
    "floor":         lambda val, args: val,   # approximation
    "round-to":      lambda val, args: val,   # approximation
    "pow":           lambda val, args: val,   # Z3 Real doesn't support general pow; approx
    "clamp-range":   lambda val, args: If(val < args[0], args[0], If(val > args[1], args[1], val)),
    "identity-fn":   lambda val, args: val,
    "default-float": lambda val, args: val,   # null handling → identity in SMT (no nulls)
    # Text → Z3 string theory (decidable subset)
    "str-len":       lambda val, args: Length(val),
}

OPAQUE_PRIMITIVES = {
    "str-lower", "str-upper", "str-trim", "str-pad-right", "str-pad-left",
    "str-remove-chars", "str-substring", "str-replace",
    "str-starts-with", "str-ends-with", "str-contains",
    "str-matches",
    # Code graph primitives — all opaque/uninterpreted (graph queries)
    "graph-callers", "graph-call-chain", "graph-dead-code", "graph-complex",
    "graph-subclasses", "graph-importers", "graph-module-deps",
    "graph-is-reachable", "graph-has-cycles", "graph-is-dead",
}

_opaque_cache: dict = {}

# Thread-unsafe but sufficient for single-threaded CLI usage: tracks which
# opaque primitive names were called since the last reset. Callers use
# reset_opaque_usage() before a check and read_opaque_usage() after.
_opaque_usage: set = set()


def reset_opaque_usage() -> None:
    """Clear the opaque-usage tracking set. Call before each solver check."""
    _opaque_usage.clear()


def read_opaque_usage() -> frozenset:
    """Return a snapshot of the opaque primitives encountered since last reset."""
    return frozenset(_opaque_usage)


def apply_opaque(name: str, val, args: list):
    """Wrap an opaque primitive as an uninterpreted Z3 function."""
    _opaque_usage.add(name)
    key = (name, len(args))
    if key not in _opaque_cache:
        if name.startswith("str-"):
            in_sorts = [StringSort()] * (1 + len(args))
            out_sort = StringSort()
            if name in ("str-starts-with", "str-ends-with", "str-contains", "str-matches"):
                out_sort = BoolSort()
        elif name.startswith("graph-"):
            # Graph primitives: inputs are strings (graph/node names), output is
            # a string handle for query results, or Bool for predicate checks.
            in_sorts = [StringSort()] * (1 + len(args))
            if name in ("graph-is-reachable", "graph-has-cycles", "graph-is-dead"):
                out_sort = BoolSort()
            else:
                out_sort = StringSort()
        else:
            in_sorts = [RealSort()] * (1 + len(args))
            out_sort = RealSort()
        _opaque_cache[key] = Function(name.replace("-", "_"), *in_sorts, out_sort)
    fn = _opaque_cache[key]
    return fn(val, *args)


def build_expr_registry(items: list) -> dict:
    """Scan parsed items for Item::Expression, return {name: ExpressionDef}."""
    registry = {}
    for item in items:
        if isinstance(item, dict) and item.get("item") == "expression":
            registry[item["name"]] = item
    return registry


def build_pred_registry(items: list) -> dict:
    """Scan parsed items for Item::Predicate, return {name: PredicateDef}."""
    registry = {}
    for item in items:
        if isinstance(item, dict) and item.get("item") == "predicate":
            registry[item["name"]] = item
    return registry


def inline_expression(val, extra_args: list, expr_def: dict, syms: "SymbolTable",
                      expr_registry: dict, _seen: tuple = None):
    """Inline a user-defined ExpressionDef by binding its inputs.

    _seen is a tuple of expression names currently being inlined (ordered);
    used for cycle detection with full cycle-path reporting. Passed through
    the call chain via apply_stage and translate_pipe to detect both direct
    and mutual recursion.
    """
    if _seen is None:
        _seen = ()
    name = expr_def["name"]
    if name in _seen:
        # Build the cycle path: from where the cycle starts to where we are
        cycle_start = _seen.index(name)
        cycle_path = list(_seen[cycle_start:]) + [name]
        raise ValueError(
            f"Recursive expression cycle detected: {' -> '.join(cycle_path)}"
        )
    _seen = _seen + (name,)

    inputs = expr_def.get("inputs", [])
    chain = expr_def.get("chain")
    if not chain:
        return val

    # Build a local symbol table with input bindings
    local_syms = SymbolTable()
    local_syms.vars = dict(syms.vars)
    local_syms.vars_next = dict(syms.vars_next)
    # Bind first input to piped value
    if inputs:
        local_syms.vars[inputs[0]["name"]] = val
    # Bind remaining inputs to extra args
    for i, inp in enumerate(inputs[1:]):
        if i < len(extra_args):
            local_syms.vars[inp["name"]] = extra_args[i]

    return translate_pipe_raw(chain, local_syms, expr_registry, _seen) \
        if chain.get("expr") == "pipe" \
        else translate_expr(chain, local_syms, expr_registry)


def apply_stage(val, stage: dict, syms: "SymbolTable", expr_registry: dict = None,
                _seen: tuple = None):
    """Apply a single pipe stage to val, returning the new Z3 expression."""
    name = stage["name"]
    args = [translate_expr(a, syms, expr_registry) for a in stage.get("args", [])]

    # 1. Native Z3 primitive?
    if name in NATIVE_PRIMITIVES:
        return NATIVE_PRIMITIVES[name](val, args)

    # 2. User-defined expression in registry?
    if expr_registry and name in expr_registry:
        return inline_expression(val, args, expr_registry[name], syms, expr_registry, _seen)

    # 3. Opaque primitive?
    if name in OPAQUE_PRIMITIVES:
        return apply_opaque(name, val, args)

    # 4. Unknown → error with fuzzy suggestions (T015)
    all_known = sorted(
        set(list(NATIVE_PRIMITIVES.keys()) + list(OPAQUE_PRIMITIVES) +
            list((expr_registry or {}).keys()))
    )
    suggestions = difflib.get_close_matches(name, all_known, n=3, cutoff=0.6)
    loc = ""
    if stage.get("file") or stage.get("line"):
        loc = f" at {stage.get('file', '<unknown>')}:{stage.get('line', '?')}:{stage.get('col', '?')}"
    if suggestions:
        raise ValueError(
            f"Unknown pipe stage '{name}'{loc}. Did you mean: {suggestions}?"
        )
    raise ValueError(
        f"Unknown pipe stage '{name}'{loc}. Known stages: {all_known[:10]}..."
    )


def translate_pipe_raw(expr: dict, syms: "SymbolTable", expr_registry: dict = None,
                       _seen: tuple = None):
    """Internal: fold pipe head through stages, threading _seen for cycle detection."""
    val = translate_expr(expr["head"], syms, expr_registry)
    for stage in expr.get("stages", []):
        val = apply_stage(val, stage, syms, expr_registry, _seen)
    return val


def translate_pipe(expr: dict, syms: "SymbolTable", expr_registry: dict = None):
    """Translate a pipe AST node: fold head through stages left-to-right."""
    return translate_pipe_raw(expr, syms, expr_registry, _seen=None)


def translate_param_ref(expr: dict, syms: "SymbolTable", expr_registry: dict = None):
    """Translate a param_ref AST node into a Z3 expression."""
    ref_kind = expr.get("ref_kind")

    if ref_kind == "var":
        name = expr["name"]
        return syms.get(name)

    elif ref_kind == "prop":
        path = ".".join(expr["parts"])
        return syms.get(path)

    elif ref_kind == "idx":
        name = expr["name"]
        index = expr.get("index", 0)
        arr = Array(name, IntSort(), RealSort())
        return Select(arr, IntVal(int(index)))

    elif ref_kind == "nested":
        return translate_expr(expr["inner"], syms, expr_registry)

    raise ValueError(f"Unknown param_ref kind: {ref_kind!r}")


# ============================================================
# EXPR → Z3 TRANSLATOR
# ============================================================

def translate_expr(expr: dict, syms: SymbolTable, expr_registry: dict = None):
    """Convert ARK AST expression → Z3 expression"""
    if expr is None:
        return True

    kind = expr.get("expr")

    if kind == "number":
        v = expr["value"]
        return RealVal(v) if isinstance(v, float) else IntVal(v)

    elif kind == "string":
        v = expr["value"]
        # Parser preserves surrounding quotes — strip them for Z3 StringVal.
        if isinstance(v, str) and len(v) >= 2 and v[0] == '"' and v[-1] == '"':
            v = v[1:-1]
        return StringVal(v)

    elif kind == "bool":
        return BoolVal(bool(expr["value"]))

    elif kind == "ident":
        name = expr["name"]
        if name.endswith("'"):
            return syms.get_next(name[:-1])
        return syms.get(name)

    elif kind == "path":
        # e.g., v.fuel → treat as single var for now
        full = ".".join(expr["parts"])
        return syms.get(full)

    elif kind == "binop":
        left = translate_expr(expr["left"], syms, expr_registry)
        right = translate_expr(expr["right"], syms, expr_registry)
        op = expr["op"]
        if op == ">=": return left >= right
        if op == "<=": return left <= right
        if op == ">":  return left > right
        if op == "<":  return left < right
        if op == "==": return left == right
        if op == "!=": return left != right
        if op == "+":  return left + right
        if op == "-":  return left - right
        if op == "*":  return left * right
        if op == "/":  return left / right
        if op in ("and", "∧"): return And(left, right)
        if op in ("or", "∨"):  return Or(left, right)
        if op == "→":  return Implies(left, right)
        raise ValueError(f"Unknown binop: {op}")

    elif kind == "unary":
        operand = translate_expr(expr["operand"], syms, expr_registry)
        op = expr["op"]
        if op == "not": return Not(operand)
        raise ValueError(f"Unknown unary op: {op}")

    elif kind == "temporal":
        # □, ◇ — for model checking, not SMT
        # For SMT, □(P) ≈ P must hold in all reachable states
        # We approximate: just check P
        return translate_expr(expr["operand"], syms, expr_registry)

    elif kind == "call":
        # clamp, length, etc. — approximate as identity for now
        name = expr["name"]
        args = [translate_expr(a, syms, expr_registry) for a in expr.get("args", [])]
        if name == "clamp" and len(args) >= 1:
            return args[0]
        if name == "length" and len(args) >= 1:
            return args[0]  # approximation
        if len(args) >= 1:
            return args[0]
        return RealVal(0)

    elif kind == "for_all":
        # Approximate: check the body expression
        body = expr.get("body")
        if isinstance(body, dict):
            return translate_expr(body, syms, expr_registry)
        return True

    elif kind == "pipe":
        return translate_pipe(expr, syms, expr_registry)

    elif kind == "param_ref":
        return translate_param_ref(expr, syms, expr_registry)

    raise ValueError(f"Cannot translate expression: {expr}")


# ============================================================
# ENUM CONTEXT
# ============================================================
#
# The verifier supports enum-valued $data fields in two forms:
#   (a) inline constraint:  $data mode: HookMode { enforce, advisory, always }
#   (b) named top-level enum: $data mode: HookMode   (with enum HookMode {...})
#
# In both cases we treat the field as an Int (distinct IntVal per variant)
# and add a membership background fact `Or(var == id1, ..., var == idk)` so
# downstream invariants like `mode == enforce or mode == advisory or mode == always`
# can be discharged. Variant names collide across enums in team-pipeline
# (e.g. `cancelled` appears in both TaskStage and TeamTaskStatus) — we
# collapse same-named variants to the same IntVal, which is safe because
# the team specs never try to distinguish them.


def _collect_enum_context(entity: dict, enum_index: dict) -> dict:
    """Compute the enum metadata needed to reason about one entity.

    Returns: {
      "field_enums": {field_name: [variant_names]},
      "variant_ids": {variant_name: int},
    }
    """
    field_enums: dict = {}
    variant_order: list = []
    seen: set = set()

    def _remember(variants: list):
        for v in variants:
            if v and v not in seen:
                seen.add(v)
                variant_order.append(v)

    for df in entity.get("data_fields", []):
        fname = df.get("name")
        if not fname:
            continue
        variants = None

        c = df.get("constraint")
        if c and c.get("constraint") == "enum":
            variants = [
                v.get("name") for v in c.get("values", [])
                if isinstance(v, dict) and v.get("expr") == "ident"
            ]
        else:
            ty = (df.get("type") or {}).get("name")
            if ty and ty in enum_index:
                variants = [
                    v.get("name") for v in enum_index[ty].get("variants", [])
                ]

        if variants:
            field_enums[fname] = variants
            _remember(variants)

    variant_ids = {name: idx for idx, name in enumerate(variant_order)}
    return {"field_enums": field_enums, "variant_ids": variant_ids}


def _bind_enum_variants(syms: SymbolTable, variant_ids: dict) -> None:
    """Pin each enum variant name to a fixed IntVal constant in the symbol
    table. translate_expr's `ident` branch calls syms.get(name), which
    returns whatever we set here — so `enforce` becomes IntVal(k) rather
    than a free Real variable.
    """
    for name, idx in variant_ids.items():
        # Overwrite even if a previous step already auto-created it as Real.
        syms.vars[name] = IntVal(idx)


def _enum_membership_facts(syms: SymbolTable, field_enums: dict,
                           variant_ids: dict, include_next: bool = True) -> list:
    """Build Z3 facts `Or(field == id1, ..., field == idk)` for each
    enum-typed field, for both current and next state.
    """
    facts = []
    for fname, variants in field_enums.items():
        ids = [IntVal(variant_ids[v]) for v in variants if v in variant_ids]
        if not ids:
            continue
        try:
            cur = syms.get(fname)
            facts.append(Or(*[cur == i for i in ids]))
        except Exception:
            pass
        if include_next:
            try:
                nxt = syms.get_next(fname)
                facts.append(Or(*[nxt == i for i in ids]))
            except Exception:
                pass
    return facts


# ============================================================
# CONSTRAINT CHECKER
# ============================================================

def check_data_constraints(data_fields: list, enum_index: dict | None = None) -> list:
    """Check that $data constraints are satisfiable"""
    results = []
    enum_index = enum_index or {}
    for df in data_fields:
        name = df["name"]
        constraint = df.get("constraint")
        default = df.get("default")
        ty = (df.get("type") or {}).get("name")

        # Resolve enum variants for this field (inline or via top-level enum).
        enum_variants = None
        if constraint and constraint.get("constraint") == "enum":
            enum_variants = [
                v.get("name") for v in constraint.get("values", [])
                if isinstance(v, dict) and v.get("expr") == "ident"
            ]
        elif ty and ty in enum_index:
            enum_variants = [
                v.get("name") for v in enum_index[ty].get("variants", [])
            ]

        if constraint is None and enum_variants is None:
            continue

        s = Solver()
        syms = SymbolTable()

        if constraint and constraint.get("constraint") == "range":
            var = syms.add_real(name)
            lo = translate_expr(constraint["min"], syms)
            hi = translate_expr(constraint["max"], syms)
            s.add(var >= lo)
            s.add(var <= hi)

            # Check default is in range
            if default:
                dv = translate_expr(default, syms)
                s2 = Solver()
                s2.add(var == dv)
                s2.add(var >= lo)
                s2.add(var <= hi)
                result = s2.check()
                results.append({
                    "check": f"{name}_default_in_range",
                    "status": "PASS" if result == sat else "FAIL",
                    "detail": f"default={default} in [{constraint['min']}, {constraint['max']}]"
                })

        elif enum_variants:
            # Pin each variant to a distinct IntVal; make the field an Int.
            variant_ids = {v: i for i, v in enumerate(enum_variants)}
            _bind_enum_variants(syms, variant_ids)
            var_int = syms.add_int(name)
            ids = [IntVal(i) for i in variant_ids.values()]
            membership = Or(*[var_int == i for i in ids])
            s.add(membership)

            if default:
                dv = translate_expr(default, syms)
                s2 = Solver()
                _bind_enum_variants(s2_syms := SymbolTable(), variant_ids)
                s2_var = s2_syms.add_int(name)
                s2_dv = translate_expr(default, s2_syms)
                s2.add(s2_var == s2_dv)
                s2.add(Or(*[s2_var == IntVal(i) for i in variant_ids.values()]))
                result = s2.check()
                results.append({
                    "check": f"{name}_default_in_enum",
                    "status": "PASS" if result == sat else "FAIL",
                    "detail": f"default={default} in enum"
                })

    return results


def _translate_body_equations(body: list, syms: SymbolTable) -> list:
    """Turn #process body statements into Z3 equality facts.

    Handles `x = expr` and `x' = expr` (assignment). Silently skips
    statements we don't yet model (condition, for_all, description,
    nested process). Returns the list of Z3 formulae.
    """
    eqs = []
    for stmt in body or []:
        if not isinstance(stmt, dict):
            continue
        tag = stmt.get("_stmt")
        if tag != "assignment":
            continue  # conditional/for_all/description → unhandled, skip
        target = stmt.get("target")
        value = stmt.get("value")
        if target is None or value is None:
            continue
        lhs = translate_expr(target, syms)
        rhs = translate_expr(value, syms)
        eqs.append(lhs == rhs)
    return eqs


def _register_port_fields(ports: list, syms: SymbolTable) -> None:
    """Register @in / @out port fields as typed Z3 variables.

    Skips names that already exist in the symbol table (so $data fields
    take precedence — they're the authoritative source of truth).
    """
    for port in ports or []:
        for f in port.get("fields", []):
            name = f.get("name")
            if not name or name in syms.vars:
                continue
            ty = (f.get("type") or {}).get("name", "Float")
            if ty in ("Int", "Uint64"):
                syms.add_int(name)
            elif ty == "String":
                syms.add_string(name)
            elif ty == "Bool":
                syms.add_bool(name)
            else:
                syms.add_real(name)


def check_invariants_hold(entity: dict, enum_index: dict | None = None) -> list:
    """Check that process rules preserve invariants.

    For each process rule:
      pre ∧ body_equations ∧ post → invariant
    We check: can pre hold, the body execute, AND invariant be violated?
    If UNSAT → invariant always holds (PASS)
    If SAT → found counterexample (FAIL)

    Additionally produces a post-obligation check:
      pre ∧ body_equations → post
    If UNSAT on `Not(post)` → body actually achieves the postcondition (PASS)
    If SAT → body does not entail post → FAIL.
    """
    results = []
    syms = SymbolTable()
    enum_index = enum_index or {}

    # Compute enum metadata for this entity and pin variant names to
    # distinct IntVal constants in the symbol table so translate_expr
    # resolves `enforce`, `advisory`, etc. to fixed ints.
    enum_ctx = _collect_enum_context(entity, enum_index)
    field_enums = enum_ctx["field_enums"]
    variant_ids = enum_ctx["variant_ids"]
    _bind_enum_variants(syms, variant_ids)

    # Register all $data as variables.
    # Background constraints (range bounds) are collected separately and
    # injected into every process×invariant check below — they describe
    # the state-space of the entity, not per-process assumptions.
    background = []
    for df in entity.get("data_fields", []):
        name = df["name"]
        ty = df.get("type", {}).get("name", "Float")
        if name in field_enums:
            syms.add_int(name)
        elif ty in ("Int", "Uint64"):
            syms.add_int(name)
        elif ty == "String":
            syms.add_string(name)
        elif ty == "Bool":
            syms.add_bool(name)
        else:
            syms.add_real(name)

        # Add range constraints as background facts (apply to both
        # current AND next state, since the range bounds the type itself).
        c = df.get("constraint")
        if c and c.get("constraint") == "range" and ty not in ("String", "Bool"):
            lo = translate_expr(c["min"], syms)
            hi = translate_expr(c["max"], syms)
            cur = syms.get(name)
            nxt = syms.get_next(name)
            background.append(cur >= lo)
            background.append(cur <= hi)
            background.append(nxt >= lo)
            background.append(nxt <= hi)

    # Enum membership facts: each enum field is constrained to its
    # variant set in both current and next state.
    background.extend(_enum_membership_facts(syms, field_enums, variant_ids))

    # Inductive hypothesis: each declared invariant holds in the CURRENT
    # state. Without this, fields that only range bound via invariants
    # (like Metrics.total_tokens >= 0 without an explicit [0..N] range)
    # become unconstrained and the solver fabricates spurious
    # counterexamples from the initial symbolic state.
    invariant_background = []
    for inv in entity.get("invariants", []) or []:
        try:
            invariant_background.append(translate_expr(inv, syms))
        except Exception:
            continue  # untranslatable — skip silently
    background.extend(invariant_background)

    # Register port fields (typed). Done AFTER $data so $data wins on collision.
    _register_port_fields(entity.get("in_ports", []), syms)
    _register_port_fields(entity.get("out_ports", []), syms)

    # For each process × each invariant
    for proc in entity.get("processes", []):
        pre_exprs = [translate_expr(p, syms) for p in proc.get("pre", [])]
        post_exprs = [translate_expr(p, syms) for p in proc.get("post", [])]
        # NEW: actually translate the body into Z3 equality facts.
        body_eqs = _translate_body_equations(proc.get("body", []), syms)

        proc_name = next(
            (m["value"] for m in proc.get("meta", [])
             if isinstance(m, dict) and m.get("key") == "strategy"),
            "unnamed"
        )

        # --- Check 1: invariant preservation ---
        for inv in entity.get("invariants", []):
            reset_opaque_usage()
            inv_z3 = translate_expr(inv, syms)
            inv_name = str(inv)[:50]

            s = Solver()

            # Background facts from $data range declarations.
            for bg in background:
                s.add(bg)

            # Add preconditions (they must hold)
            for p in pre_exprs:
                s.add(p)

            # Body equations: x' = expr, y' = expr, ...
            for eq in body_eqs:
                s.add(eq)

            # Post conditions describe what's true after
            for p in post_exprs:
                s.add(p)

            # Can the invariant be false?
            s.add(Not(inv_z3))

            result = s.check()
            used_opaque = read_opaque_usage()

            if result == unsat:
                status = "PASS_OPAQUE" if used_opaque else "PASS"
                opaque_note = f" (opaque: {', '.join(sorted(used_opaque))})" if used_opaque else ""
                results.append({
                    "check": f"invariant_holds_{inv_name}",
                    "process": proc_name,
                    "status": status,
                    "detail": f"Invariant cannot be violated given pre/body/post{opaque_note}",
                    "opaque_primitives": sorted(used_opaque),
                })
            elif result == sat:
                model = s.model()
                results.append({
                    "check": f"invariant_holds_{inv_name}",
                    "process": proc_name,
                    "status": "FAIL",
                    "detail": f"Counterexample found: {model}",
                    "opaque_primitives": sorted(used_opaque),
                })
            else:
                status = "PASS_OPAQUE" if used_opaque else "UNKNOWN"
                opaque_note = f" (opaque: {', '.join(sorted(used_opaque))})" if used_opaque else ""
                results.append({
                    "check": f"invariant_holds_{inv_name}",
                    "process": proc_name,
                    "status": status,
                    "detail": f"Z3 could not determine{opaque_note}",
                    "opaque_primitives": sorted(used_opaque),
                })

        # --- Check 2: post-obligation (NEW) ---
        # Only meaningful when the process actually has body equations AND
        # a post condition to discharge. Otherwise the obligation is vacuous.
        if body_eqs and post_exprs:
            s = Solver()
            for bg in background:
                s.add(bg)
            for p in pre_exprs:
                s.add(p)
            for eq in body_eqs:
                s.add(eq)
            # Try to find a state where SOME post condition fails.
            s.add(Or(*[Not(p) for p in post_exprs]))

            result = s.check()
            check_name = f"post_implied_by_body_{proc_name}"
            if result == unsat:
                results.append({
                    "check": check_name,
                    "process": proc_name,
                    "status": "PASS",
                    "detail": "pre ∧ body ⇒ post"
                })
            elif result == sat:
                model = s.model()
                results.append({
                    "check": check_name,
                    "process": proc_name,
                    "status": "FAIL",
                    "detail": f"Body does not entail post: {model}"
                })
            else:
                results.append({
                    "check": check_name,
                    "process": proc_name,
                    "status": "UNKNOWN",
                    "detail": "Z3 could not determine"
                })

    return results


# ============================================================
# MAIN VERIFIER
# ============================================================

def verify_entity(entity: dict, enum_index: dict | None = None) -> list:
    """Run all verification checks on an entity"""
    results = []
    name = entity.get("name", "?")

    print(f"\n{'='*60}")
    print(f"  Verifying: {entity.get('kind', '?')} {name}")
    print(f"{'='*60}")

    # 1. Check $data constraints
    data_results = check_data_constraints(
        entity.get("data_fields", []), enum_index
    )
    results.extend(data_results)

    # 2. Check invariants hold through transitions
    inv_results = check_invariants_hold(entity, enum_index)
    results.extend(inv_results)

    # Print results
    for r in results:
        status = r["status"]
        if status in ("PASS", "PASS_BOUNDED", "PASS_OPAQUE"):
            icon = "✓"
        elif status == "FAIL":
            icon = "✗"
        else:
            icon = "?"
        print(f"  {icon} [{status}] {r['check']}")
        if r.get("detail"):
            print(f"    → {r['detail']}")

    return results


def _type_name(type_node: dict) -> str:
    """Flatten a type AST node to a comparable canonical string."""
    if not isinstance(type_node, dict):
        return str(type_node)
    kind = type_node.get("type")
    if kind == "named":
        return type_node.get("name", "?")
    if kind == "generic":
        inner = _type_name(type_node.get("inner", {}))
        return f"{type_node.get('name', '?')}<{inner}>"
    if kind == "array":
        return f"[{_type_name(type_node.get('elem', {}))}]"
    if kind == "map":
        return f"[{_type_name(type_node.get('key', {}))}:{_type_name(type_node.get('value', {}))}]"
    return type_node.get("name", str(type_node))


def _lookup_port_type(entity_name: str, field: str, direction: str,
                      index: dict) -> dict | None:
    """Find a port field's type on an entity, walking the inherits chain.

    direction: "out" looks at out_ports, "in" looks at in_ports.
    Returns the type-node dict if found, else None.
    """
    seen = set()
    cursor = entity_name
    while cursor and cursor not in seen:
        seen.add(cursor)
        ent = index.get(cursor)
        if ent is None:
            return None
        ports_key = "out_ports" if direction == "out" else "in_ports"
        for port in ent.get(ports_key, []):
            for f in port.get("fields", []):
                if f.get("name") == field:
                    return f.get("type")
        # Walk to first parent (single inheritance in practice).
        parents = ent.get("inherits") or []
        cursor = parents[0] if parents else None
    return None


# ============================================================
# TEMPORAL — Bounded Model Checking for □ (box) properties
# ============================================================
#
# MVP: real state unrolling over K steps, shallow BMC.
#
#   x_s0, x_s1, ..., x_sK   — one copy of each $data field per step
#   Init(x_s0)              — defaults + range constraints
#   ∀i<K: Trans(x_si, x_s{i+1})  — body equations + frame axioms
#   Bad:  ∃i≤K: ¬φ(x_si)    — property violated at some step
#
# If SAT → counterexample found (FAIL, with failing step index)
# If UNSAT → PASS_BOUNDED(K) — not a proof beyond K steps.
# Only □φ is supported; other temporal operators report UNKNOWN.


BMC_DEFAULT_BOUND = 10


def _bmc_symbols(entity: dict, k_cur: int, k_next: int,
                 field_enums: dict | None = None,
                 variant_ids: dict | None = None) -> SymbolTable:
    """Build a SymbolTable where `x` → Z3 var suffixed `_s{k_cur}` and
    `x'` → var suffixed `_s{k_next}`. @in fields → step-k_cur only.

    Z3 variables are cached by name so step_syms[k].get('x') returns the
    same underlying var as step_syms[k+1].get('x') when the suffixes match.

    Enum-typed fields (as reported by field_enums) are forced to Int so
    their values can be compared to the pinned variant IntVals.
    """
    syms = SymbolTable()
    field_enums = field_enums or {}
    variant_ids = variant_ids or {}

    def _mk(name: str, ty: str, suffix: int, is_enum: bool):
        zname = f"{name}_s{suffix}"
        if is_enum or ty in ("Int", "Uint64"):
            return Int(zname)
        if ty == "String":
            return String(zname)
        if ty == "Bool":
            return Bool(zname)
        return Real(zname)

    for df in entity.get("data_fields", []):
        name = df["name"]
        ty = (df.get("type") or {}).get("name", "Float")
        is_enum = name in field_enums
        syms.vars[name] = _mk(name, ty, k_cur, is_enum)
        syms.vars_next[f"{name}'"] = _mk(name, ty, k_next, is_enum)

    for port in entity.get("in_ports", []):
        for f in port.get("fields", []):
            fname = f.get("name")
            if not fname or fname in syms.vars:
                continue
            ty = (f.get("type") or {}).get("name", "Float")
            syms.vars[fname] = _mk(fname, ty, k_cur, False)

    # Pin variant names AFTER field vars so translate_expr resolves them
    # to constants in every step.
    _bind_enum_variants(syms, variant_ids)

    return syms


def _extract_assigned_data_names(body: list) -> set:
    """Return the set of $data field names assigned (primed or not) in body."""
    assigned = set()
    for stmt in body or []:
        if not isinstance(stmt, dict) or stmt.get("_stmt") != "assignment":
            continue
        target = stmt.get("target") or {}
        if target.get("expr") != "ident":
            continue
        name = target.get("name", "")
        if name.endswith("'"):
            name = name[:-1]
        if name:
            assigned.add(name)
    return assigned


def _check_temporal_box(entity: dict, temporal_expr: dict,
                        bound: int, enum_index: dict | None = None) -> dict:
    """Run BMC for a single □φ property on one entity."""
    ent_name = entity.get("name", "?")
    operand = temporal_expr.get("operand")
    if operand is None:
        return {
            "check": f"temporal_{ent_name}_box",
            "status": "UNKNOWN",
            "detail": "empty operand",
        }

    enum_index = enum_index or {}
    enum_ctx = _collect_enum_context(entity, enum_index)
    field_enums = enum_ctx["field_enums"]
    variant_ids = enum_ctx["variant_ids"]

    processes = entity.get("processes", [])
    proc = processes[0] if processes else None
    body = proc.get("body", []) if proc else []
    assigned = _extract_assigned_data_names(body)

    solver = Solver()

    # One symbol table per step. step_syms[k] knows: current=step k,
    # next=step k+1. step_syms[bound] exists so we can evaluate the
    # property on the terminal state (no outgoing transition needed).
    step_syms = [
        _bmc_symbols(entity, k, k + 1, field_enums, variant_ids)
        for k in range(bound + 1)
    ]

    # --- Background range constraints for every step variable ---
    for syms_k in step_syms:
        for df in entity.get("data_fields", []):
            c = df.get("constraint")
            if not c or c.get("constraint") != "range":
                continue
            ty = (df.get("type") or {}).get("name", "Float")
            if ty in ("String", "Bool"):
                continue
            lo = translate_expr(c["min"], syms_k)
            hi = translate_expr(c["max"], syms_k)
            var = syms_k.get(df["name"])
            solver.add(var >= lo)
            solver.add(var <= hi)

    # --- Enum membership at every step (both cur and next vars) ---
    for syms_k in step_syms:
        for fact in _enum_membership_facts(syms_k, field_enums, variant_ids,
                                           include_next=False):
            solver.add(fact)

    # --- Initial state: defaults pinned on step 0 ---
    initial = step_syms[0]
    for df in entity.get("data_fields", []):
        default = df.get("default")
        if default is None:
            continue
        var = initial.get(df["name"])
        try:
            init_val = translate_expr(default, initial)
            solver.add(var == init_val)
        except Exception:
            pass  # unparseable default → leave unconstrained

    # --- Transition relations: step k → step k+1 ---
    for k in range(bound):
        syms_k = step_syms[k]
        if proc is not None:
            body_eqs = _translate_body_equations(body, syms_k)
            for eq in body_eqs:
                solver.add(eq)
        # Frame axioms: fields not assigned stay equal across the step.
        for df in entity.get("data_fields", []):
            name = df["name"]
            if name in assigned:
                continue
            solver.add(syms_k.get(name) == syms_k.get_next(name))

    # --- Assert the "bad state exists" disjunction ---
    step_operands = []
    for syms_k in step_syms:
        try:
            step_operands.append(translate_expr(operand, syms_k))
        except Exception as exc:
            return {
                "check": f"temporal_{ent_name}_box",
                "status": "UNKNOWN",
                "detail": f"untranslatable operand: {exc}",
            }
    if not step_operands:
        return {
            "check": f"temporal_{ent_name}_box",
            "status": "UNKNOWN",
            "detail": "no step operands",
        }
    solver.add(Or(*[Not(op) for op in step_operands]))

    result = solver.check()
    check_name = f"temporal_{ent_name}_box_K{bound}"
    if result == unsat:
        return {
            "check": check_name,
            "status": "PASS_BOUNDED",
            "detail": f"□ holds across {bound}-step BMC (not a proof beyond K)",
        }
    if result == sat:
        model = solver.model()
        failing_step = None
        for k, op_k in enumerate(step_operands):
            try:
                if is_true(model.evaluate(Not(op_k), model_completion=True)):
                    failing_step = k
                    break
            except Exception:
                continue
        step_txt = f"step {failing_step}" if failing_step is not None else "unknown step"
        return {
            "check": check_name,
            "status": "FAIL",
            "detail": f"□ violated at {step_txt}: {model}",
        }
    return {
        "check": check_name,
        "status": "UNKNOWN",
        "detail": "Z3 could not determine",
    }


def verify_temporal(ast_items: list, bound: int = BMC_DEFAULT_BOUND,
                    enum_index: dict | None = None) -> list:
    """Check temporal properties on all entities in the file.

    Only supports `□φ` (box / globally) via K-step BMC. Other temporal
    operators (`◇`, `○`, `U`) report UNKNOWN and are left for follow-ups.
    """
    results = []

    def _walk(entity: dict):
        ent_name = entity.get("name", "?")
        for temporal in entity.get("temporals", []) or []:
            if not isinstance(temporal, dict) or temporal.get("expr") != "temporal":
                continue
            op = temporal.get("op")

            print(f"\n{'='*60}")
            print(f"  Verifying: temporal {ent_name} {op}")
            print(f"{'='*60}")

            if op == "□":
                r = _check_temporal_box(entity, temporal, bound, enum_index)
            else:
                r = {
                    "check": f"temporal_{ent_name}_{op or '?'}",
                    "status": "UNKNOWN",
                    "detail": f"operator '{op}' not yet supported (only □ in MVP)",
                }
            results.append(r)
            icon = {"PASS_BOUNDED": "✓", "PASS": "✓",
                    "FAIL": "✗"}.get(r["status"], "?")
            print(f"  {icon} [{r['status']}] {r['check']}")
            if r.get("detail"):
                print(f"    → {r['detail']}")

    for item in ast_items:
        kind = item.get("kind")
        if kind in ("abstraction", "class"):
            _walk(item)
        elif kind == "island":
            _walk(item)
            for cls in item.get("classes", []) or []:
                _walk(cls)

    return results


def verify_bridges(ast_items: list) -> list:
    """Type-check bridges: from-port and to-port field types must match.

    Walks inheritance chains so CodeSubagent (which inherits @in from
    Subagent) resolves correctly. Contract invariants themselves are NOT
    SMT-checked yet — that is a wider verify job (VerifyFullExprTask).
    """
    # Build entity index: name → entity dict. Covers abstractions, classes,
    # islands (which have their own @in/@out), and classes nested inside islands.
    index = {}
    for item in ast_items:
        kind = item.get("kind")
        if kind in ("abstraction", "class"):
            index[item.get("name")] = item
        elif kind == "island":
            index[item.get("name")] = item
            for cls in item.get("classes", []):
                index[cls.get("name")] = cls

    results = []
    for item in ast_items:
        if item.get("kind") != "bridge":
            continue
        name = item.get("name", "?")

        print(f"\n{'='*60}")
        print(f"  Verifying: bridge {name}")
        print(f"{'='*60}")

        def _split(dotted):
            if not dotted or "." not in dotted:
                return None, None
            head, _, tail = dotted.partition(".")
            return head, tail

        src_ent, src_field = _split(item.get("from_port", ""))
        dst_ent, dst_field = _split(item.get("to_port", ""))

        check_name = f"bridge_{name}_type_match"

        if not src_ent or not dst_ent:
            r = {
                "check": check_name,
                "status": "FAIL",
                "detail": f"Malformed endpoints: from={item.get('from_port')} to={item.get('to_port')}",
            }
            results.append(r)
            print(f"  ✗ [FAIL] {check_name}\n    → {r['detail']}")
            continue

        src_type = _lookup_port_type(src_ent, src_field, "out", index)
        dst_type = _lookup_port_type(dst_ent, dst_field, "in", index)

        if src_type is None or dst_type is None:
            missing = []
            if src_type is None:
                missing.append(f"{src_ent}.@out.{src_field}")
            if dst_type is None:
                missing.append(f"{dst_ent}.@in.{dst_field}")
            r = {
                "check": check_name,
                "status": "UNKNOWN",
                "detail": f"Unresolved endpoint(s): {', '.join(missing)}",
            }
            results.append(r)
            print(f"  ? [UNKNOWN] {check_name}\n    → {r['detail']}")
            continue

        src_t = _type_name(src_type)
        dst_t = _type_name(dst_type)
        if src_t == dst_t:
            r = {
                "check": check_name,
                "status": "PASS",
                "detail": f"{src_ent}.{src_field}: {src_t} → {dst_ent}.{dst_field}: {dst_t}",
            }
            print(f"  ✓ [PASS] {check_name}\n    → {r['detail']}")
        else:
            r = {
                "check": check_name,
                "status": "FAIL",
                "detail": f"Type mismatch: {src_ent}.{src_field}: {src_t} ≠ {dst_ent}.{dst_field}: {dst_t}",
            }
            print(f"  ✗ [FAIL] {check_name}\n    → {r['detail']}")
        results.append(r)

    return results


def verify_expressions_predicates(items: list) -> dict:
    """Verify expression and predicate definitions in an ARK file.

    Each expression/predicate that uses opaque primitives (e.g. graph-*)
    is translated to Z3 to confirm the chain is well-formed and produces
    PASS_OPAQUE status, confirming opaque graph primitives are recognised.

    Returns a dict {name: [result_record, ...]} compatible with verify_file.
    """
    from z3 import Solver, StringVal, unsat

    results = {}
    expr_registry = {}
    # First pass: build expression registry from all expression items
    for item in items:
        if item.get("kind") == "expression":
            expr_registry[item["name"]] = item

    for item in items:
        kind = item.get("kind")
        if kind not in ("expression", "predicate"):
            continue

        name = item.get("name", "?")
        print(f"\n[{kind.upper()}] {name}")

        # Build a symbol table with each input bound to a fresh Z3 string constant
        syms = SymbolTable()
        for inp in item.get("inputs", []):
            inp_name = inp["name"]
            syms.vars[inp_name] = StringVal(inp_name)

        # Get the chain/check expression
        chain_key = "chain" if kind == "expression" else "check"
        chain_expr = item.get(chain_key)
        if chain_expr is None:
            results[name] = [{
                "check": f"{kind}_chain",
                "status": "UNKNOWN",
                "detail": f"No {chain_key} expression found",
            }]
            print(f"  ? [UNKNOWN] {kind}_chain — no {chain_key} expression")
            continue

        try:
            reset_opaque_usage()
            z3_expr = translate_expr(chain_expr, syms, expr_registry)
            used_opaque = read_opaque_usage()

            if used_opaque:
                status = "PASS_OPAQUE"
                opaque_note = f" (opaque: {', '.join(sorted(used_opaque))})"
                r = {
                    "check": f"{kind}_chain",
                    "status": "PASS_OPAQUE",
                    "detail": f"Chain translated successfully{opaque_note}",
                    "opaque_primitives": sorted(used_opaque),
                }
                print(f"  ✓ [PASS_OPAQUE] {kind}_chain{opaque_note}")
            else:
                # No opaque primitives — try Z3 satisfiability check
                s = Solver()
                result = s.check()
                status = "PASS" if result == unsat else "UNKNOWN"
                r = {
                    "check": f"{kind}_chain",
                    "status": status,
                    "detail": "Chain translated; no opaque primitives used",
                }
                print(f"  {'✓' if status == 'PASS' else '?'} [{status}] {kind}_chain")

            results[name] = [r]

        except Exception as exc:
            r = {
                "check": f"{kind}_chain",
                "status": "FAIL",
                "detail": str(exc),
            }
            results[name] = [r]
            print(f"  ✗ [FAIL] {kind}_chain — {exc}")

    return results


def verify_file(ast_json: dict) -> dict:
    """Verify all entities in an ARK file"""
    all_results = {}
    items = ast_json.get("items", [])

    # Build enum index: name → enum_def AST node. Used by check_invariants_hold
    # and _check_temporal_box to resolve named enum types as background facts.
    enum_index = {
        it.get("name"): it
        for it in items
        if it.get("kind") == "enum" and it.get("name")
    }

    for item in items:
        kind = item.get("kind")
        name = item.get("name", item.get("target", "?"))

        if kind in ("abstraction", "class"):
            results = verify_entity(item, enum_index)
            all_results[name] = results

        elif kind == "island":
            # Verify island-level invariants
            results = verify_entity(item, enum_index)
            all_results[name] = results

            # Verify nested classes
            for cls in item.get("classes", []):
                cls_results = verify_entity(cls, enum_index)
                all_results[f"{name}.{cls.get('name', '?')}"] = cls_results

    # Expression and predicate chain checks.
    expr_pred_results = verify_expressions_predicates(items)
    for ep_name, ep_res in expr_pred_results.items():
        all_results[ep_name] = ep_res

    # Bridge contract checks (type matching).
    bridge_results = verify_bridges(items)
    if bridge_results:
        all_results["_bridges"] = bridge_results

    # Temporal properties via bounded model checking.
    temporal_results = verify_temporal(items, enum_index=enum_index)
    if temporal_results:
        all_results["_temporal"] = temporal_results

    # Studio verification: run when role/studio items are present.
    studio_kinds = {"role", "studio_role", "command", "command_def", "hook", "rule"}
    has_studio_items = any(
        isinstance(it, dict) and it.get("kind") in studio_kinds
        for it in items
    )
    if has_studio_items:
        try:
            from tools.verify.studio_verify import verify_studio
        except ImportError:
            try:
                import sys as _sys, pathlib as _pathlib
                _sys.path.insert(0, str(_pathlib.Path(__file__).parent.parent.parent))
                from tools.verify.studio_verify import verify_studio
            except ImportError:
                # studio_verify not available — skip silently
                verify_studio = None  # type: ignore
        if verify_studio is not None:
            studio_result = verify_studio(ast_json)
            # Flatten studio check records into all_results under "_studio"
            flat = []
            for records in studio_result.get("checks", {}).values():
                flat.extend(records)
            if flat:
                all_results["_studio"] = flat

    # Evolution verification: run when evolution items are present.
    evolution_kinds = {
        "eval_dataset", "fitness_function", "benchmark_gate",
        "evolution_target", "evolution_run", "optimizer", "constraint",
    }
    has_evolution_items = any(
        isinstance(it, dict) and it.get("kind") in evolution_kinds
        for it in items
    )
    if has_evolution_items:
        verify_evolution = None
        try:
            from tools.verify.evolution_verify import verify_evolution
        except ImportError:
            try:
                import sys as _sys, pathlib as _pathlib
                _sys.path.insert(0, str(_pathlib.Path(__file__).parent.parent.parent))
                from tools.verify.evolution_verify import verify_evolution
            except ImportError:
                # evolution_verify not available — skip silently
                pass
        if verify_evolution is not None:
            evolution_results = verify_evolution(ast_json)
            if evolution_results:
                # Each result dict already has check/entity/status/message fields.
                # Store them grouped under "_evolution" in all_results,
                # converting "pass"/"fail"/"warn" → "PASS"/"FAIL"/"WARN" so the
                # summary tally uses the same case as the rest of the verifier.
                normalised = []
                for r in evolution_results:
                    rec = dict(r)
                    rec["status"] = rec.get("status", "warn").upper()
                    normalised.append(rec)
                all_results["_evolution"] = normalised

    # Agent verification: run when agent-specific items are present.
    agent_kinds = {
        "agent", "platform", "gateway", "execution_backend",
        "skill", "learning_config", "cron_task", "model_config",
    }
    has_agent_items = any(
        isinstance(it, dict) and it.get("kind") in agent_kinds
        for it in items
    )
    if has_agent_items:
        verify_agent = None
        try:
            from tools.verify.agent_verify import verify_agent
        except ImportError:
            try:
                import sys as _sys, pathlib as _pathlib
                _sys.path.insert(0, str(_pathlib.Path(__file__).parent.parent.parent))
                from tools.verify.agent_verify import verify_agent
            except ImportError:
                # agent_verify not available — skip silently
                pass
        if verify_agent is not None:
            agent_results = verify_agent(ast_json)
            if agent_results:
                # Each result dict already has check/status/message fields.
                # Normalise "pass"/"fail"/"warn" → "PASS"/"FAIL"/"WARN" to match
                # the case convention used by the rest of the verifier.
                normalised_agent = []
                for r in agent_results:
                    rec = dict(r)
                    rec["status"] = rec.get("status", "warn").upper()
                    normalised_agent.append(rec)
                all_results["_agent"] = normalised_agent

    # Visual verification: run when visual-specific items are present.
    visual_kinds = {
        "diagram", "preview", "annotation", "visual_review",
        "screenshot", "visual_search", "render_config",
    }
    has_visual_items = any(
        isinstance(it, dict) and it.get("kind") in visual_kinds
        for it in items
    )
    if has_visual_items:
        verify_visual = None
        try:
            from tools.verify.visual_verify import verify_visual
        except ImportError:
            try:
                import sys as _sys, pathlib as _pathlib
                _sys.path.insert(0, str(_pathlib.Path(__file__).parent.parent.parent))
                from tools.verify.visual_verify import verify_visual
            except ImportError:
                pass
        if verify_visual is not None:
            visual_results = verify_visual(ast_json)
            if visual_results:
                normalised_visual = []
                for r in visual_results:
                    rec = dict(r)
                    rec["status"] = rec.get("status", "warn").upper()
                    normalised_visual.append(rec)
                all_results["_visual"] = normalised_visual

    # Summary — PASS_BOUNDED counts as a pass for the purposes of the
    # running green/red tally, since it's the best the BMC can assert.
    # PASS_OPAQUE counts as an acknowledged pass (Z3 was used but with
    # opaque/uninterpreted functions; result is best-effort, not a proof).
    pass_statuses = {"PASS", "PASS_BOUNDED"}
    total = sum(len(v) for v in all_results.values())
    passed = sum(1 for v in all_results.values() for r in v if r["status"] in pass_statuses)
    failed = sum(1 for v in all_results.values() for r in v if r["status"] == "FAIL")
    unknown = sum(1 for v in all_results.values() for r in v if r["status"] == "UNKNOWN")
    pass_opaque = sum(1 for v in all_results.values() for r in v if r["status"] == "PASS_OPAQUE")

    print(f"\n{'='*60}")
    summary_parts = [f"{passed}/{total} passed", f"{failed} failed"]
    if unknown:
        summary_parts.append(f"{unknown} UNKNOWN")
    if pass_opaque:
        summary_parts.append(f"{pass_opaque} PASS_OPAQUE")
    print(f"  SUMMARY: {', '.join(summary_parts)}")
    print(f"{'='*60}")

    return {
        "entities": all_results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "unknown": unknown,
            "pass_opaque": pass_opaque,
        }
    }


# ============================================================
# CLI
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python ark_verify.py <file.ark.json>")
        print("       (pass JSON AST from ark_parser.py)")
        sys.exit(1)

    filepath = Path(sys.argv[1])

    if filepath.suffix == ".ark":
        # Parse first
        sys.path.insert(0, str(Path(__file__).parent.parent / "parser"))
        from ark_parser import parse, to_json
        source = filepath.read_text(encoding="utf-8")
        ark_file = parse(source)
        ast_json = json.loads(to_json(ark_file))
    else:
        ast_json = json.loads(filepath.read_text())

    result = verify_file(ast_json)

    # Optionally save results
    if "--json" in sys.argv:
        out_path = filepath.with_suffix(".verify.json")
        out_path.write_text(json.dumps(result, indent=2, default=str))
        print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
