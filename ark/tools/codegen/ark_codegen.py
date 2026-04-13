"""
ARK Codegen
Генерирует код из ARK AST:
  - Rust structs (SoA для tensor-островов, AoS для code-островов)
  - C++ classes (UE5-compatible)
  - Protobuf (для сетевых мостов)

Pipeline:  .ark → parse → AST(JSON) → codegen → .rs / .h / .proto
"""

import json
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

# ============================================================
# TYPE MAPPING
# ============================================================

RUST_TYPES = {
    "Float": "f32", "Float16": "f16", "Int": "i32", "Uint64": "u64",
    "Bool": "bool", "String": "String", "Path": "PathBuf",
    "Vec2": "Vec2", "Vec3": "Vec3", "Vec4": "Vec4",
    "Quat": "Quat", "Mat4": "Mat4", "AABB": "AABB",
    "Transform": "Transform", "DeltaTime": "DeltaTime",
    "EntityId": "EntityId", "ServerId": "ServerId", "PlayerId": "PlayerId",
}

CPP_TYPES = {
    "Float": "float", "Float16": "FFloat16", "Int": "int32", "Uint64": "uint64",
    "Bool": "bool", "String": "FString", "Path": "FString",
    "Vec2": "FVector2D", "Vec3": "FVector", "Vec4": "FVector4",
    "Quat": "FQuat", "Mat4": "FMatrix", "AABB": "FBox",
    "Transform": "FTransform", "DeltaTime": "float",
    "EntityId": "uint64", "ServerId": "uint64", "PlayerId": "uint64",
}

PROTO_TYPES = {
    "Float": "float", "Float16": "float", "Int": "int32", "Uint64": "uint64",
    "Bool": "bool", "String": "string", "Path": "string",
    "Vec2": "Vec2", "Vec3": "Vec3", "Vec4": "Vec4",
    "Quat": "Quat", "Transform": "Transform",
    "EntityId": "uint64", "ServerId": "uint64", "PlayerId": "uint64",
}


def map_type(ty: dict, target: str) -> str:
    """Map ARK type → target language type"""
    types = {"rust": RUST_TYPES, "cpp": CPP_TYPES, "proto": PROTO_TYPES}[target]

    kind = ty.get("type")
    if kind == "named":
        return types.get(ty["name"], ty["name"])
    elif kind == "generic":
        inner = map_type(ty["param"], target)
        outer = ty["name"]
        if target == "rust":
            return f"{outer}<{inner}>"
        elif target == "cpp":
            return f"T{outer}<{inner}>" if outer != "Texture2D" else f"UTexture2D*"
        elif target == "proto":
            return inner  # proto doesn't have generics like this
    elif kind == "array":
        inner = map_type(ty["element"], target)
        size = ty.get("size")
        if target == "rust":
            return f"[{inner}; {size}]" if size else f"Vec<{inner}>"
        elif target == "cpp":
            return f"TArray<{inner}>"
        elif target == "proto":
            return f"repeated {inner}"

    return "Unknown"


# ============================================================
# RUST CODEGEN
# ============================================================

def gen_rust_entity(entity: dict, strategy: str = "code") -> str:
    """Generate Rust code for a class/abstraction"""
    name = entity["name"]
    num_type = _dominant_num_type(entity)
    locals_ = _entity_locals(entity)
    lines = []

    # Header
    lines.append(f"// Generated from ARK DSL — do not edit manually")
    lines.append(f"// Entity: {entity['kind']} {name}")
    lines.append(f"// Strategy: {strategy}")
    lines.append(f"")

    if strategy == "tensor":
        lines.extend(_gen_rust_soa(entity, num_type, locals_))
    else:
        lines.extend(_gen_rust_aos(entity))

    # Invariant assertions. Invariants may reference either $data fields
    # (→ `self.field`) or @in port parameters (→ bare local). We include
    # @in fields as method parameters so invariants that reference inputs
    # can still be checked.
    invariants = entity.get("invariants", [])
    if invariants:
        inv_params = []
        for port in entity.get("in_ports", []):
            for field in port.get("fields", []):
                rtype = map_type(field["type"], "rust")
                inv_params.append(f"{field['name']}: {rtype}")
        inv_sig = f"&self, {', '.join(inv_params)}" if inv_params else "&self"

        lines.append(f"")
        lines.append(f"impl {name} {{")
        lines.append(f"    /// Check all invariants. Generated from ARK spec.")
        lines.append(f"    #[inline]")
        lines.append(f"    pub fn check_invariants({inv_sig}) -> bool {{")
        for i, inv in enumerate(invariants):
            rust_expr = _expr_to_rust(inv, "self.", locals_, num_type)
            lines.append(f"        let inv_{i} = {rust_expr};")
        all_invs = " && ".join(f"inv_{i}" for i in range(len(invariants)))
        lines.append(f"        {all_invs}")
        lines.append(f"    }}")
        lines.append(f"}}")

    # Process methods (transition functions)
    processes = entity.get("processes", [])
    if processes:
        lines.append(f"")
        lines.append(f"impl {name} {{")
        for pi, proc in enumerate(processes):
            proc_strategy = _get_meta(proc, "strategy", "code")
            proc_name = f"process_{pi}"

            # Input params from @in ports become method parameters and locals.
            params = []
            for port in entity.get("in_ports", []):
                for field in port.get("fields", []):
                    rtype = map_type(field["type"], "rust")
                    params.append(f"{field['name']}: {rtype}")

            param_str = ", ".join(params)
            sig = f"&mut self, {param_str}" if param_str else "&mut self"
            lines.append(f"    /// Process rule #{pi} (strategy: {proc_strategy})")
            lines.append(f"    #[inline]")
            lines.append(f"    pub fn {proc_name}({sig}) {{")

            # Debug assertions for preconditions
            for pre in proc.get("pre", []):
                rust_pre = _expr_to_rust(pre, "self.", locals_, num_type)
                lines.append(f"        debug_assert!({rust_pre}, \"precondition failed\");")

            # Body
            for stmt in proc.get("body", []):
                if not isinstance(stmt, dict):
                    continue
                s = stmt.get("_stmt")
                if s == "assignment":
                    target = _expr_to_rust(stmt["target"], "self.", locals_, num_type)
                    value = _expr_to_rust(stmt["value"], "self.", locals_, num_type)
                    lines.append(f"        {target} = {value};")
                elif s == "for_all":
                    lines.append(f"        // TODO: for_all {stmt.get('type')} as {stmt.get('var')}")
                elif s == "condition":
                    cond_expr = _expr_to_rust(stmt.get("expr"), "self.", locals_, num_type)
                    lines.append(f"        if {cond_expr} {{")
                    lines.append(f"            // TODO: condition body")
                    lines.append(f"        }}")

            # Debug assertions for postconditions
            for post in proc.get("post", []):
                rust_post = _expr_to_rust(post, "self.", locals_, num_type)
                lines.append(f"        debug_assert!({rust_post}, \"postcondition failed\");")

            lines.append(f"    }}")
        lines.append(f"}}")

    return "\n".join(lines)


def _gen_rust_aos(entity: dict) -> list:
    """AoS struct — standard layout for code strategy"""
    name = entity["name"]
    lines = []

    data_fields = entity.get("data_fields", [])
    has_defaults = any(df.get("default") for df in data_fields)

    # When the spec provides defaults we emit our own `impl Default`, so we
    # must drop `Default` from the derive list to avoid a conflict.
    if has_defaults:
        lines.append(f"#[derive(Debug, Clone)]")
    else:
        lines.append(f"#[derive(Debug, Clone, Default)]")
    lines.append(f"pub struct {name} {{")

    for df in data_fields:
        rtype = map_type(df["type"], "rust")
        comment = ""
        if df.get("default"):
            comment = f"  // default: {_expr_to_rust(df['default'], '')}"
        lines.append(f"    pub {df['name']}: {rtype},{comment}")

    lines.append(f"}}")

    if has_defaults:
        lines.append(f"")
        lines.append(f"impl {name} {{")
        lines.append(f"    /// Construct with spec defaults. Generated from ARK $data defaults.")
        lines.append(f"    #[inline]")
        lines.append(f"    pub fn new() -> Self {{")
        lines.append(f"        Self {{")
        for df in data_fields:
            fname = df["name"]
            if df.get("default"):
                field_num_type = _field_num_type(df)
                val = _expr_to_rust(df["default"], "", set(), field_num_type)
                lines.append(f"            {fname}: {val},")
            else:
                lines.append(f"            {fname}: Default::default(),")
        lines.append(f"        }}")
        lines.append(f"    }}")
        lines.append(f"}}")
        lines.append(f"")
        lines.append(f"impl Default for {name} {{")
        lines.append(f"    #[inline]")
        lines.append(f"    fn default() -> Self {{ Self::new() }}")
        lines.append(f"}}")

    return lines


def _gen_rust_soa(entity: dict, num_type: str = "f32", locals_: set = None) -> list:
    """SoA struct — parallel arrays for tensor strategy"""
    name = entity["name"]
    if locals_ is None:
        locals_ = _entity_locals(entity)
    lines = []

    # Individual struct (still needed for single-entity ops)
    lines.extend(_gen_rust_aos(entity))
    lines.append(f"")

    # SoA batch container
    lines.append(f"/// SoA layout for batch processing (tensor strategy)")
    lines.append(f"#[derive(Debug, Clone)]")
    lines.append(f"pub struct {name}Batch {{")
    lines.append(f"    pub count: usize,")
    for df in entity.get("data_fields", []):
        rtype = map_type(df["type"], "rust")
        lines.append(f"    pub {df['name']}: Vec<{rtype}>,")
    lines.append(f"}}")

    # Batch constructor
    lines.append(f"")
    lines.append(f"impl {name}Batch {{")
    lines.append(f"    pub fn with_capacity(cap: usize) -> Self {{")
    lines.append(f"        Self {{")
    lines.append(f"            count: 0,")
    for df in entity.get("data_fields", []):
        lines.append(f"            {df['name']}: Vec::with_capacity(cap),")
    lines.append(f"        }}")
    lines.append(f"    }}")
    lines.append(f"")

    # Collect field names so we can rewrite `self.fuel` → `self.fuel[i]`
    # inside the generated batch loop.
    field_names = {df["name"] for df in entity.get("data_fields", [])}

    # Build batch process body from the first tensor #process (if any).
    processes = entity.get("processes", [])
    tensor_proc = None
    for proc in processes:
        if _get_meta(proc, "strategy", "code") == "tensor":
            tensor_proc = proc
            break

    # Batch method signature mirrors the #process @in params (plus they're
    # provided to every element).
    params = []
    for port in entity.get("in_ports", []):
        for field in port.get("fields", []):
            rtype = map_type(field["type"], "rust")
            params.append(f"{field['name']}: {rtype}")
    # Ensure we always pass a dt parameter (common for tensor ticks).
    if not any(p.startswith("dt:") for p in params):
        params.append("dt: f32")
    param_str = ", ".join(params)
    sig = f"&mut self, {param_str}" if param_str else "&mut self"

    lines.append(f"    /// Batch process all entities. Generated from #process[strategy: tensor].")
    lines.append(f"    /// Scalar fallback; replace with SIMD/AVX2 for hot loops.")
    lines.append(f"    #[inline]")
    lines.append(f"    pub fn process_all({sig}) {{")

    if tensor_proc is None:
        lines.append(f"        // No tensor #process defined — no-op.")
        lines.append(f"        let _ = ({', '.join(f['name'] for p in entity.get('in_ports', []) for f in p.get('fields', []))});")
    else:
        lines.append(f"        for i in 0..self.count {{")

        def _soa(expr, locals_local):
            """Render expr but rewrite `self.field` → `self.field[i]`."""
            return _expr_to_rust_soa(expr, field_names, locals_local, num_type)

        for pre in tensor_proc.get("pre", []):
            rust_pre = _soa(pre, locals_)
            lines.append(f"            debug_assert!({rust_pre}, \"precondition failed\");")

        for stmt in tensor_proc.get("body", []):
            if not isinstance(stmt, dict):
                continue
            if stmt.get("_stmt") == "assignment":
                target = _soa(stmt["target"], locals_)
                value = _soa(stmt["value"], locals_)
                lines.append(f"            {target} = {value};")

        for post in tensor_proc.get("post", []):
            rust_post = _soa(post, locals_)
            lines.append(f"            debug_assert!({rust_post}, \"postcondition failed\");")

        lines.append(f"        }}")

    lines.append(f"    }}")
    lines.append(f"}}")

    return lines


def _expr_to_rust_soa(expr: dict, field_names: set, locals_: set,
                      num_type: str = "f32") -> str:
    """Render expression in SoA batch context: `self.field` → `self.field[i]`.

    Call parameters (locals_) stay as bare identifiers.
    """
    if expr is None:
        return "true"
    kind = expr.get("expr")
    if kind == "number":
        v = expr["value"]
        if isinstance(v, float):
            return f"{v}_f32"
        return f"{v}_{num_type}"
    elif kind == "bool":
        return "true" if expr["value"] else "false"
    elif kind == "string":
        return f'"{expr["value"]}"'
    elif kind == "ident":
        name = expr["name"].rstrip("'")
        if name in locals_:
            return name
        if name in field_names:
            return f"self.{name}[i]"
        return name
    elif kind == "path":
        parts = expr["parts"]
        head = parts[0].rstrip("'")
        if head in locals_:
            return ".".join([head] + parts[1:])
        if head in field_names:
            rest = "".join(f".{p}" for p in parts[1:])
            return f"self.{head}[i]{rest}"
        return ".".join([head] + parts[1:])
    elif kind == "binop":
        l = _expr_to_rust_soa(expr["left"], field_names, locals_, num_type)
        r = _expr_to_rust_soa(expr["right"], field_names, locals_, num_type)
        op = expr["op"]
        if op == "→":
            return f"(!{l} || {r})"
        return f"({l} {op} {r})"
    elif kind == "unary":
        o = _expr_to_rust_soa(expr["operand"], field_names, locals_, num_type)
        return f"(!{o})" if expr["op"] == "not" else f"({o})"
    elif kind == "temporal":
        return _expr_to_rust_soa(expr["operand"], field_names, locals_, num_type)
    elif kind == "call":
        args = ", ".join(
            _expr_to_rust_soa(a, field_names, locals_, num_type)
            for a in expr.get("args", [])
        )
        return f"{expr['name']}({args})"
    return "/* unknown */"


# ============================================================
# C++ CODEGEN (UE5)
# ============================================================

def gen_cpp_entity(entity: dict, strategy: str = "code") -> tuple:
    """Generate C++ header + source for UE5"""
    name = entity["name"]
    header = []
    source = []

    # Header
    header.append(f"// Generated from ARK DSL — do not edit manually")
    header.append(f"#pragma once")
    header.append(f"")
    header.append(f"#include \"CoreMinimal.h\"")
    header.append(f"#include \"{name}.generated.h\"")
    header.append(f"")

    # UE5 USTRUCT
    header.append(f"USTRUCT(BlueprintType)")
    header.append(f"struct F{name}")
    header.append(f"{{")
    header.append(f"    GENERATED_BODY()")
    header.append(f"")

    for df in entity.get("data_fields", []):
        ctype = map_type(df["type"], "cpp")
        default_val = ""
        if df.get("default"):
            default_val = f" = {_expr_to_cpp(df['default'])}"
        header.append(f"    UPROPERTY(EditAnywhere, BlueprintReadWrite)")
        header.append(f"    {ctype} {df['name']}{default_val};")
        header.append(f"")

    # Check invariants
    header.append(f"    /** Check all invariants. Generated from ARK spec. */")
    header.append(f"    bool CheckInvariants() const;")
    header.append(f"}};")

    # Source
    source.append(f"// Generated from ARK DSL — do not edit manually")
    source.append(f"#include \"{name}.h\"")
    source.append(f"")
    source.append(f"bool F{name}::CheckInvariants() const")
    source.append(f"{{")
    for inv in entity.get("invariants", []):
        cpp_expr = _expr_to_cpp(inv, prefix="")
        source.append(f"    if (!({cpp_expr})) return false;")
    source.append(f"    return true;")
    source.append(f"}}")

    return ("\n".join(header), "\n".join(source))


# ============================================================
# PROTOBUF CODEGEN
# ============================================================

def gen_proto_entity(entity: dict) -> str:
    """Generate .proto message for network bridges"""
    name = entity["name"]
    lines = []

    lines.append(f'syntax = "proto3";')
    lines.append(f"")
    lines.append(f"// Generated from ARK DSL — do not edit manually")
    lines.append(f"")
    lines.append(f"message {name} {{")

    field_num = 1
    for df in entity.get("data_fields", []):
        ptype = map_type(df["type"], "proto")
        lines.append(f"    {ptype} {df['name']} = {field_num};")
        field_num += 1

    lines.append(f"}}")

    # Port messages
    for port_type, ports in [("Input", entity.get("in_ports", [])),
                              ("Output", entity.get("out_ports", []))]:
        for port in ports:
            if port.get("fields"):
                lines.append(f"")
                lines.append(f"message {name}{port_type} {{")
                fn = 1
                for field in port["fields"]:
                    ptype = map_type(field["type"], "proto")
                    lines.append(f"    {ptype} {field['name']} = {fn};")
                    fn += 1
                lines.append(f"}}")

    return "\n".join(lines)


# ============================================================
# ISLAND CODEGEN
# ============================================================

def gen_island(island: dict, target: str = "rust") -> str:
    """Generate code for an entire island"""
    name = island["name"]
    strategy = island.get("strategy", "code")
    lines = []

    lines.append(f"// ============================================================")
    lines.append(f"// Island: {name}")
    lines.append(f"// Strategy: {strategy}")
    lines.append(f"// ============================================================")
    lines.append(f"")

    # Import contained entities that are defined in sibling modules.
    if target == "rust":
        for contained in island.get("contains", []):
            mod = contained.lower()
            if strategy == "tensor":
                lines.append(f"use crate::{mod}::{{{contained}, {contained}Batch}};")
            else:
                lines.append(f"use crate::{mod}::{contained};")
        if island.get("contains"):
            lines.append("")

    # Generate contained classes
    for cls in island.get("classes", []):
        if target == "rust":
            lines.append(gen_rust_entity(cls, strategy))
        lines.append(f"")

    # Island struct itself
    if target == "rust":
        lines.append(f"pub struct {name}Island {{")

        for df in island.get("data_fields", []):
            rtype = map_type(df["type"], "rust")
            lines.append(f"    pub {df['name']}: {rtype},")

        # Contained entity batches
        for contained in island.get("contains", []):
            if strategy == "tensor":
                lines.append(f"    pub {contained.lower()}_batch: {contained}Batch,")
            else:
                lines.append(f"    pub {contained.lower()}s: Vec<{contained}>,")

        lines.append(f"}}")

        # Island update
        lines.append(f"")
        lines.append(f"impl {name}Island {{")

        # Input types from @in
        in_fields = []
        for port in island.get("in_ports", []):
            for field in port.get("fields", []):
                rtype = map_type(field["type"], "rust")
                in_fields.append(f"{field['name']}: {rtype}")

        sig = f"&mut self, {', '.join(in_fields)}" if in_fields else "&mut self"
        lines.append(f"    pub fn update({sig}) {{")
        if strategy == "tensor":
            lines.append(f"        // Tensor batch processing.")
            lines.append(f"        // NOTE: batch signatures are derived from each entity's")
            lines.append(f"        // @in port. Adapt the arguments below to the island's inputs.")
            for contained in island.get("contains", []):
                lines.append(f"        self.{contained.lower()}_batch.process_all(Default::default(), Default::default());")
        else:
            lines.append(f"        // Per-entity processing")
        lines.append(f"    }}")
        lines.append(f"}}")

    return "\n".join(lines)


# ============================================================
# EXPRESSION → LANGUAGE TRANSLATORS
# ============================================================

def _expr_to_rust(expr: dict, prefix: str = "",
                  locals_: set = None, num_type: str = "f32") -> str:
    """Translate an ARK expression AST to Rust source.

    prefix: prepended to identifier references that refer to entity fields
            (typically "self.").
    locals_: names that should NOT get the prefix (function parameters, loop
             vars, etc.).
    num_type: suffix applied to integer literals so they compile cleanly in
              float-dominant contexts (e.g. "f32" → `0_f32`).
    """
    if expr is None:
        return "true"
    if locals_ is None:
        locals_ = set()
    kind = expr.get("expr")
    if kind == "number":
        v = expr["value"]
        if isinstance(v, float):
            return f"{v}_f32"
        # Integer literal — emit with numeric suffix so it coerces cleanly
        # in the dominant numeric context of the entity.
        return f"{v}_{num_type}"
    elif kind == "bool":
        return "true" if expr["value"] else "false"
    elif kind == "string":
        return f'"{expr["value"]}"'
    elif kind == "ident":
        # Strip prime notation (ARK uses `foo'` for "next value of foo").
        name = expr["name"].rstrip("'")
        if name in locals_:
            return name
        return f"{prefix}{name}"
    elif kind == "path":
        parts = expr["parts"]
        head = parts[0].rstrip("'")
        if head in locals_:
            return ".".join([head] + parts[1:])
        return f"{prefix}{'.'.join([head] + parts[1:])}"
    elif kind == "binop":
        l = _expr_to_rust(expr["left"], prefix, locals_, num_type)
        r = _expr_to_rust(expr["right"], prefix, locals_, num_type)
        op = expr["op"]
        if op == "→":
            return f"(!{l} || {r})"
        return f"({l} {op} {r})"
    elif kind == "unary":
        o = _expr_to_rust(expr["operand"], prefix, locals_, num_type)
        return f"(!{o})" if expr["op"] == "not" else f"({o})"
    elif kind == "temporal":
        return _expr_to_rust(expr["operand"], prefix, locals_, num_type)
    elif kind == "call":
        args = ", ".join(
            _expr_to_rust(a, prefix, locals_, num_type) for a in expr.get("args", [])
        )
        return f"{expr['name']}({args})"
    return "/* unknown */"


# Map ARK type names to the dominant numeric category for entity-level
# literal inference. An entity with all-Float fields uses "f32"; otherwise
# fall back to "i32" (matches how fields are generated).
_FLOAT_TYPES = {"Float", "Float16", "DeltaTime"}
_INT_TYPES = {"Int", "Uint64", "EntityId", "ServerId", "PlayerId"}

def _dominant_num_type(entity: dict) -> str:
    """Pick a default numeric suffix for integer literals in this entity.

    If all numeric $data fields are Float-like, use f32. Otherwise i32.
    This is a heuristic sufficient for common cases; mixed entities will
    still compile for same-type operations and only break on the rare
    cross-type literal, which users can handle by writing explicit floats.
    """
    has_float = False
    has_int = False
    for df in entity.get("data_fields", []):
        ty = df.get("type", {})
        if ty.get("type") == "named":
            n = ty.get("name")
            if n in _FLOAT_TYPES:
                has_float = True
            elif n in _INT_TYPES:
                has_int = True
    if has_float and not has_int:
        return "f32"
    if has_int and not has_float:
        return "i32"
    # Mixed or unknown — default to f32, which matches typical #process math.
    return "f32"


def _field_num_type(df: dict) -> str:
    """Numeric suffix for a single $data field's default literal."""
    ty = df.get("type", {})
    if ty.get("type") == "named":
        n = ty.get("name")
        if n in _FLOAT_TYPES:
            return "f32"
        if n == "Uint64":
            return "u64"
        if n in _INT_TYPES:
            return "i32"
    return "f32"


def _entity_locals(entity: dict) -> set:
    """Collect names that are local to #process methods (in-port fields)."""
    locals_ = set()
    for port in entity.get("in_ports", []):
        for field in port.get("fields", []):
            locals_.add(field["name"])
    return locals_


def _expr_to_cpp(expr: dict, prefix: str = "") -> str:
    if expr is None:
        return "true"
    kind = expr.get("expr")
    if kind == "number":
        v = expr["value"]
        return f"{v}f" if isinstance(v, float) else str(v)
    elif kind == "bool":
        return "true" if expr["value"] else "false"
    elif kind == "ident":
        return f"{prefix}{expr['name']}"
    elif kind == "binop":
        l = _expr_to_cpp(expr["left"], prefix)
        r = _expr_to_cpp(expr["right"], prefix)
        return f"({l} {expr['op']} {r})"
    return "/* unknown */"


def _get_meta(proc: dict, key: str, default: str = "") -> str:
    for m in proc.get("meta", []):
        if isinstance(m, dict) and m.get("key") == key:
            v = m["value"]
            if isinstance(v, dict) and v.get("expr") == "ident":
                return v["name"]
            return str(v)
    return default


# ============================================================
# EXPRESSION / PREDICATE CODEGEN
# ============================================================

# Import the primitive map lazily so this module does not require it at
# import time (keeps backward compatibility with tests that don't use
# expression codegen).
def _load_primitives():
    """Return the EXPR_PRIMITIVES dict."""
    import sys as _sys
    from pathlib import Path as _Path
    _codegen_dir = str(_Path(__file__).parent)
    if _codegen_dir not in _sys.path:
        _sys.path.insert(0, _codegen_dir)
    from expression_primitives import EXPR_PRIMITIVES
    return EXPR_PRIMITIVES


def _ark_type_to_rust(type_dict: dict) -> str:
    """Map an ARK type dict to a Rust type string."""
    if type_dict is None:
        return "String"
    if type_dict.get("type") == "named":
        name = type_dict.get("name", "String")
        return RUST_TYPES.get(name, name)
    return "String"


def _render_pipe_chain(head_name: str, stages: list, locals_: set) -> str:
    """Render a pipe chain to a Rust expression string using EXPR_PRIMITIVES.

    head_name: the name of the first variable (receiver).
    stages: list of stage dicts with 'name' and 'args'.
    locals_: set of local variable names (for arg rendering).
    """
    primitives = _load_primitives()
    result = head_name
    for stage in stages:
        prim_name = stage["name"]
        args = stage.get("args", [])
        prim = primitives.get(prim_name)
        if prim is None:
            result = f"{result}.{prim_name}(/* unknown */)"
            continue
        kind = prim["kind"]
        rust_tmpl = prim["rust"]
        # Build arg strings
        arg_strs = []
        for a in args:
            if isinstance(a, dict) and a.get("expr") == "ident":
                arg_strs.append(a["name"])
            elif isinstance(a, dict) and a.get("expr") == "number":
                v = a["value"]
                arg_strs.append(str(v))
            elif isinstance(a, dict) and a.get("expr") == "string":
                arg_strs.append(f'"{a["value"]}"')
            else:
                arg_strs.append("/* arg */")
        # Format placeholders {0}, {1}, ... using positional args.
        # Also support {recv} named placeholder.
        def _fmt(tmpl: str) -> str:
            # Replace {recv} with the current result first (before positional fmt).
            t = tmpl.replace("{recv}", result)
            # Format positional placeholders with arg_strs.
            return t.format(*arg_strs) if arg_strs else t
        if kind in ("method", "predicate"):
            rendered = _fmt(rust_tmpl)
            result = f"{result}{rendered}"
        elif kind == "binary":
            rendered = _fmt(rust_tmpl)
            result = f"({result}{rendered})"
        elif kind == "unary":
            result = rust_tmpl.replace("{self}", result)
        elif kind == "identity":
            pass  # no-op
        elif kind == "fn":
            rendered = _fmt(rust_tmpl)
            result = rendered
        else:
            # fallback: treat as method
            rendered = _fmt(rust_tmpl)
            result = f"{result}{rendered}"
    return result


def gen_rust_expression(item: dict) -> str:
    """Generate a Rust fn for an ARK expression item.

    Returns the full Rust function source as a string.
    """
    name = item["name"].replace("-", "_")
    inputs = item.get("inputs", [])
    output_type = _ark_type_to_rust(item.get("output"))
    # Build parameter list
    params = ", ".join(
        f"{inp['name'].replace('-', '_')}: {_ark_type_to_rust(inp.get('type'))}"
        for inp in inputs
    )
    # Render pipe chain
    chain = item.get("chain")
    if chain and chain.get("expr") == "pipe":
        head = chain.get("head", {})
        head_name = head.get("name", "x") if head.get("expr") == "ident" else "x"
        stages = chain.get("stages", [])
        locals_ = {inp["name"] for inp in inputs}
        body_expr = _render_pipe_chain(head_name, stages, locals_)
    else:
        body_expr = "/* no chain */"
    return (
        f"pub fn {name}({params}) -> {output_type} {{\n"
        f"    {body_expr}\n"
        f"}}"
    )


def gen_rust_predicate(item: dict) -> str:
    """Generate a Rust fn returning bool for an ARK predicate item.

    Returns the full Rust function source as a string.
    """
    name = item["name"].replace("-", "_")
    inputs = item.get("inputs", [])
    # Build parameter list
    params = ", ".join(
        f"{inp['name'].replace('-', '_')}: {_ark_type_to_rust(inp.get('type'))}"
        for inp in inputs
    )
    # Render check chain
    chain = item.get("check")
    if chain and chain.get("expr") == "pipe":
        head = chain.get("head", {})
        head_name = head.get("name", "x") if head.get("expr") == "ident" else "x"
        stages = chain.get("stages", [])
        locals_ = {inp["name"] for inp in inputs}
        body_expr = _render_pipe_chain(head_name, stages, locals_)
    else:
        body_expr = "/* no check */"
    return (
        f"pub fn {name}({params}) -> bool {{\n"
        f"    {body_expr}\n"
        f"}}"
    )


# ============================================================
# FULL FILE CODEGEN
# ============================================================

def codegen_file(ast_json: dict, target: str = "rust", out_dir: Path = None) -> dict:
    """Generate code for all entities in an ARK file.

    Supported targets: rust, cpp, proto, studio.
    For ``studio`` the call is delegated to studio_codegen.gen_studio which
    works on the *parsed* ArkFile object, not the JSON AST.  To keep the
    existing caller interface intact we re-parse the source when the target
    is ``studio`` and the caller passes a raw JSON dict.
    """
    # ------------------------------------------------------------------ studio
    if target == "studio":
        # studio_codegen operates on the ArkFile dataclass, not on JSON.
        # We import lazily so the rest of codegen doesn't depend on the parser.
        try:
            from studio_codegen import gen_studio
        except ImportError:
            from tools.codegen.studio_codegen import gen_studio

        # Reconstruct an ArkFile-like object from the JSON AST using the
        # actual parser so we get real dataclass instances.
        try:
            from ark_parser import parse
        except ImportError:
            from tools.parser.ark_parser import parse

        # The JSON AST doesn't carry the original source, but it does carry
        # the source path when produced via ark.py (stored in the "source"
        # field by some versions of the parser).  Fall back to re-parsing
        # from source_path if available; otherwise build a minimal proxy.
        source = ast_json.get("_source")
        source_path = ast_json.get("_source_path")
        if source:
            ark_file = parse(source, file_path=source_path)
            return gen_studio(ark_file, out_dir)

        # No embedded source — build a lightweight proxy so gen_studio can
        # still extract items from the JSON-serialised structure.
        class _ArkFileProxy:
            def __init__(self, data: dict):
                self.items = []
                self.roles = {}
                self.commands = {}

        proxy = _ArkFileProxy(ast_json)
        results = gen_studio(proxy, out_dir)
        return results

    # -------------------------------------------------------- standard targets
    results = {}

    for item in ast_json.get("items", []):
        kind = item.get("kind")
        name = item.get("name", "unknown")

        if kind in ("abstraction", "class"):
            # Pick the most demanding strategy declared on any #process rule.
            # If anything is tensor/gpu/asm, we need SoA batch codegen.
            strategy = "code"
            for proc in item.get("processes", []):
                s = _get_meta(proc, "strategy", "")
                if s in ("tensor", "gpu_compute", "asm_avx2"):
                    strategy = "tensor"
                    break
            if target == "rust":
                code = gen_rust_entity(item, strategy)
                fname = f"{name.lower()}.rs"
                results[fname] = code
            elif target == "cpp":
                h, cpp = gen_cpp_entity(item, strategy)
                results[f"{name}.h"] = h
                results[f"{name}.cpp"] = cpp
            elif target == "proto":
                proto = gen_proto_entity(item)
                results[f"{name.lower()}.proto"] = proto

        elif kind == "island":
            strategy = item.get("strategy", "code")
            if target == "rust":
                code = gen_island(item, "rust")
                results[f"{name.lower()}_island.rs"] = code

            # Also generate for contained classes
            for cls in item.get("classes", []):
                if target == "rust":
                    code = gen_rust_entity(cls, strategy)
                    results[f"{cls['name'].lower()}.rs"] = code

        elif kind == "expression":
            if target != "rust":
                raise NotImplementedError(
                    f"Expression codegen is only supported for Rust (got '{target}')"
                )
            code = gen_rust_expression(item)
            fname = f"{name.replace('-', '_')}.rs"
            results[fname] = code

        elif kind == "predicate":
            if target != "rust":
                raise NotImplementedError(
                    f"Predicate codegen is only supported for Rust (got '{target}')"
                )
            code = gen_rust_predicate(item)
            fname = f"{name.replace('-', '_')}.rs"
            results[fname] = code

    # Write files
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        for fname, content in results.items():
            (out_dir / fname).write_text(content, encoding="utf-8")
            print(f"  → {out_dir / fname}")

    return results


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ARK Codegen")
    parser.add_argument("input", help=".ark or .json file")
    parser.add_argument("--target", choices=["rust", "cpp", "proto"], default="rust")
    parser.add_argument("--out", help="Output directory", default=None)
    parser.add_argument("--stdout", action="store_true", help="Print to stdout")
    args = parser.parse_args()

    filepath = Path(args.input)

    if filepath.suffix == ".ark":
        sys.path.insert(0, str(Path(__file__).parent.parent / "parser"))
        from ark_parser import parse, to_json
        source = filepath.read_text(encoding="utf-8")
        ark_file = parse(source)
        ast_json = json.loads(to_json(ark_file))
    else:
        ast_json = json.loads(filepath.read_text())

    out_dir = Path(args.out) if args.out else None
    results = codegen_file(ast_json, args.target, out_dir)

    if args.stdout or not out_dir:
        for fname, content in results.items():
            print(f"\n// === {fname} ===")
            print(content)

    print(f"\nGenerated {len(results)} files ({args.target})")


if __name__ == "__main__":
    main()
