"""
ARK DSL Parser
Парсит .ark файлы → AST (Python dict) → JSON
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from lark import Lark, Transformer, v_args, Token, Tree
from lark.exceptions import (
    UnexpectedInput,
    UnexpectedToken,
    UnexpectedCharacters,
    UnexpectedEOF,
)


# ============================================================
# PARSE ERROR REPORTING
# ============================================================

class ArkParseError(Exception):
    """User-facing parse error with source position and snippet."""

    def __init__(self, message: str, file_path: Optional[str], line: int,
                 column: int, snippet: str, caret: str,
                 expected: Optional[list] = None):
        super().__init__(message)
        self.message = message
        self.file_path = file_path
        self.line = line
        self.column = column
        self.snippet = snippet  # pre-formatted multi-line context block
        self.caret = caret      # caret line (e.g. "    ^^^^^ expected ...")
        self.expected = expected or []

    def format_report(self) -> str:
        path = self.file_path if self.file_path else "<string>"
        out = [f"error: {self.message}",
               f"  --> {path}:{self.line}:{self.column}",
               "      |"]
        # The snippet builder returns context lines WITH the caret line
        # already interleaved after the offending line, so we just append
        # the whole block.  If for any reason there is no snippet, fall
        # back to a stand-alone caret so the report always contains '^'.
        if self.snippet:
            out.append(self.snippet.rstrip("\n"))
            if self.caret and self.caret not in self.snippet:
                out.append(self.caret.rstrip("\n"))
        else:
            out.append(self.caret.rstrip("\n") if self.caret else "      ^")
        return "\n".join(out)


def _build_snippet(source: str, line: int, column: int,
                   expected: Optional[list] = None,
                   bad_token: Optional[str] = None) -> tuple:
    """Return (snippet_block, caret_line) for the given error position."""
    src_lines = source.split("\n")
    if not src_lines:
        return ("", "")
    # 1-based line → 0-based index, clamp.
    idx = max(0, min(len(src_lines) - 1, line - 1))
    start = max(0, idx - 2)
    end = min(len(src_lines), idx + 2)
    width = len(str(end))
    out = []
    caret_line = ""
    for i in range(start, end):
        ln = i + 1
        prefix = f"{ln:>{width}} | "
        out.append(prefix + src_lines[i])
        if i == idx:
            # caret under the offending column (1-based)
            col = max(1, column)
            span = max(1, len(bad_token) if bad_token else 1)
            pad = " " * (len(prefix) + col - 1)
            hint = ""
            if expected:
                shown = " | ".join(sorted(str(e) for e in expected)[:6])
                more = "" if len(expected) <= 6 else f" | ... (+{len(expected)-6})"
                hint = f" expected {shown}{more}"
            caret_line = pad + ("^" * span) + hint
            out.append(caret_line)
    # `out` contains source context with the caret line interleaved
    # directly after the offending line.  We return the whole block as
    # `snippet`, and also return the bare caret line separately so
    # callers (and tests) can introspect it.
    return ("\n".join(out), caret_line)


def _lark_to_ark_error(exc: UnexpectedInput, source: str,
                       file_path: Optional[str]) -> ArkParseError:
    """Convert a Lark UnexpectedInput exception → ArkParseError."""
    line = getattr(exc, "line", 1) or 1
    column = getattr(exc, "column", 1) or 1
    expected = None
    bad_token = None
    if isinstance(exc, UnexpectedToken):
        tok = getattr(exc, "token", None)
        bad_token = str(tok) if tok is not None else None
        message = f"unexpected token {bad_token!r}" if bad_token else "unexpected token"
        exp = getattr(exc, "expected", None) or getattr(exc, "accepts", None)
        if exp:
            expected = list(exp)
    elif isinstance(exc, UnexpectedCharacters):
        ch = source[exc.pos_in_stream] if getattr(exc, "pos_in_stream", None) is not None and exc.pos_in_stream < len(source) else ""
        bad_token = ch
        message = f"unexpected character {ch!r}" if ch else "unexpected character"
        exp = getattr(exc, "allowed", None)
        if exp:
            expected = list(exp)
    elif isinstance(exc, UnexpectedEOF):
        message = "unexpected end of file (did you forget a closing '}'?)"
        exp = getattr(exc, "expected", None)
        if exp:
            expected = list(exp)
        # Point at the last line.
        src_lines = source.split("\n")
        if src_lines:
            line = len(src_lines)
            column = max(1, len(src_lines[-1]) + 1)
    else:
        message = str(exc).splitlines()[0] if str(exc) else "parse error"

    snippet, caret = _build_snippet(source, line, column, expected, bad_token)
    return ArkParseError(
        message=message,
        file_path=file_path,
        line=line,
        column=column,
        snippet=snippet,
        caret=caret,
        expected=expected,
    )

# ============================================================
# AST DATACLASSES
# ============================================================

@dataclass
class TypedField:
    name: str
    type: dict

@dataclass
class MetaPair:
    key: str
    value: dict

@dataclass
class InPort:
    kind: str = "in_port"
    fields: list = field(default_factory=list)

@dataclass
class OutPort:
    kind: str = "out_port"
    meta: list = field(default_factory=list)
    fields: list = field(default_factory=list)

@dataclass
class ProcessRule:
    kind: str = "process"
    meta: list = field(default_factory=list)
    pre: list = field(default_factory=list)
    post: list = field(default_factory=list)
    body: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class DataField:
    kind: str = "data"
    name: str = ""
    type: dict = field(default_factory=dict)
    constraint: Optional[dict] = None
    default: Optional[dict] = None

@dataclass
class EntityDef:
    kind: str = ""  # "abstraction" or "class"
    name: str = ""
    inherits: list = field(default_factory=list)
    data_fields: list = field(default_factory=list)
    in_ports: list = field(default_factory=list)
    out_ports: list = field(default_factory=list)
    processes: list = field(default_factory=list)
    invariants: list = field(default_factory=list)
    temporals: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class InstanceDef:
    kind: str = "instance"
    name: str = ""
    class_name: str = ""
    assignments: list = field(default_factory=list)

@dataclass
class IslandDef:
    kind: str = "island"
    name: str = ""
    strategy: Optional[str] = None
    memory: list = field(default_factory=list)
    contains: list = field(default_factory=list)
    in_ports: list = field(default_factory=list)
    out_ports: list = field(default_factory=list)
    processes: list = field(default_factory=list)
    classes: list = field(default_factory=list)
    data_fields: list = field(default_factory=list)
    invariants: list = field(default_factory=list)
    temporals: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class BridgeDef:
    kind: str = "bridge"
    name: str = ""
    from_port: str = ""
    to_port: str = ""
    contract: Optional[dict] = None

@dataclass
class RegistryDef:
    kind: str = "registry"
    name: str = ""
    entries: list = field(default_factory=list)

@dataclass
class VerifyDef:
    kind: str = "verify"
    target: str = ""
    checks: list = field(default_factory=list)

@dataclass
class PrimitiveDef:
    kind: str = "primitive"
    name: str = ""
    description: Optional[str] = None

@dataclass
class StructDef:
    kind: str = "struct"
    name: str = ""
    fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class EnumDef:
    kind: str = "enum"
    name: str = ""
    variants: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class ExpressionDef:
    kind: str = "expression"
    name: str = ""
    inputs: list = field(default_factory=list)    # List of typed_field dicts
    output: dict = field(default_factory=dict)     # type_expr dict
    chain: dict = field(default_factory=dict)      # expr dict (pipe or single atom)
    description: Optional[str] = None

@dataclass
class PredicateDef:
    kind: str = "predicate"
    name: str = ""
    inputs: list = field(default_factory=list)    # List of typed_field dicts
    check: dict = field(default_factory=dict)      # expr dict (must type-check to Bool)
    description: Optional[str] = None

@dataclass
class PipeStage:
    name: str = ""          # kebab-case allowed, e.g. "text-to-lower"
    args: list = field(default_factory=list)  # extra args beyond piped value

@dataclass
class ArkFile:
    imports: list = field(default_factory=list)
    items: list = field(default_factory=list)
    # --- Indices built by _build_indices() after parsing/import resolution ---
    # Top-level classes only (not island-nested).
    classes: dict = field(default_factory=dict)         # name -> EntityDef
    # Instances grouped by their declared class_name. Includes orphans
    # (instances whose class_name isn't declared) — caller can detect this
    # by checking `class_name not in ark_file.classes`.
    instances: dict = field(default_factory=dict)       # class_name -> [InstanceDef]
    # Per-island nested classes: island_name -> {class_name -> EntityDef}.
    # Separate map so top-level and island-scoped names can't collide.
    island_classes: dict = field(default_factory=dict)
    # Expression and predicate indices: name -> index into items list.
    expression_index: dict = field(default_factory=dict)  # name -> int index
    predicate_index: dict = field(default_factory=dict)   # name -> int index

    def instances_of(self, class_name: str) -> list:
        """Return the list of instances declared for `class_name`, or []."""
        return self.instances.get(class_name, [])


# ============================================================
# LARK TRANSFORMER → AST
# ============================================================

class ArkTransformer(Transformer):
    """Converts Lark parse tree → ARK AST dataclasses"""

    # --- Primitives ---

    def IDENT(self, token):
        return str(token)

    def NUMBER(self, token):
        s = str(token)
        return float(s) if '.' in s else int(s)

    def STRING(self, items):
        # STRING matches: "content" → we get the inner content
        return str(items)

    # --- Expressions ---

    def ident_expr(self, items):
        return {"expr": "ident", "name": items[0]}

    def data_ref_expr(self, items):
        # `$data IDENT` is an explicit marker that this identifier refers
        # to a $data field of the enclosing entity. Semantically equivalent
        # to a bare IDENT — so we lower it to the same ident-expr shape.
        return {"expr": "ident", "name": str(items[0])}

    def number_expr(self, items):
        return {"expr": "number", "value": items[0]}

    def string_expr(self, items):
        return {"expr": "string", "value": items[0]}

    def true_expr(self, _):
        return {"expr": "bool", "value": True}

    def false_expr(self, _):
        return {"expr": "bool", "value": False}

    def path_expr(self, items):
        return items[0]  # dotted_path already handled

    def paren_expr(self, items):
        return items[0]

    def array_expr(self, items):
        return {"expr": "array", "elements": items[0] if items else []}

    @staticmethod
    def _fold_fixed_op(items, op):
        """Left-fold for operators that don't carry an op token (or/and)."""
        result = items[0]
        for rhs in items[1:]:
            result = {"expr": "binop", "op": op, "left": result, "right": rhs}
        return result

    @staticmethod
    def _fold_token_op(items):
        """Left-fold for (operand OP operand OP operand ...) flat lists."""
        result = items[0]
        i = 1
        while i + 1 < len(items):
            op = str(items[i])
            rhs = items[i + 1]
            result = {"expr": "binop", "op": op, "left": result, "right": rhs}
            i += 2
        return result

    def or_expr(self, items):
        if len(items) == 1:
            return items[0]
        return self._fold_fixed_op(items, "or")

    def and_expr(self, items):
        if len(items) == 1:
            return items[0]
        return self._fold_fixed_op(items, "and")

    def cmp_expr(self, items):
        if len(items) == 1:
            return items[0]
        return self._fold_token_op(items)

    def add_expr(self, items):
        if len(items) == 1:
            return items[0]
        return self._fold_token_op(items)

    def mul_expr(self, items):
        if len(items) == 1:
            return items[0]
        return self._fold_token_op(items)

    def temporal_expr(self, items):
        return {"expr": "temporal", "op": str(items[0]), "operand": items[1]}

    def not_expr(self, items):
        return {"expr": "unary", "op": "not", "operand": items[0]}

    def fn_call(self, items):
        name = items[0]
        args = items[1] if len(items) > 1 else []
        if isinstance(name, dict) and name.get("expr") == "path":
            name_str = ".".join(name["parts"])
        else:
            name_str = str(name)
        return {"expr": "call", "name": name_str, "args": args}

    def for_all_expr(self, items):
        ty = items[0]
        var = items[1]
        rest = items[2:]
        cond = None
        body = rest[-1] if rest else None
        if len(rest) > 1:
            cond = rest[0]
        return {"expr": "for_all", "type": ty, "var": var, "condition": cond, "body": body}

    # --- Pipe expressions ---

    def pipe_expr(self, items):
        if len(items) == 1:
            return items[0]  # no pipe, pass through
        head = items[0]
        stages = [{"name": s.name, "args": s.args} for s in items[1:]]
        return {"expr": "pipe", "head": head, "stages": stages}

    def pipe_stage(self, items):
        name = items[0]  # string from pipe_fn_ident
        args = items[1] if len(items) > 1 else []
        return PipeStage(name=name, args=args)

    def pipe_fn_ident(self, items):
        return "-".join(str(i) for i in items)

    # --- Param refs ---

    def var_ref(self, items):
        return {"expr": "param_ref", "ref_kind": "var", "name": str(items[0])}

    def prop_ref(self, items):
        parts = [str(i) for i in items]
        return {"expr": "param_ref", "ref_kind": "prop", "parts": parts}

    def idx_ref(self, items):
        return {"expr": "param_ref", "ref_kind": "idx", "name": str(items[0]), "index": items[1]}

    def nested_ref(self, items):
        return {"expr": "param_ref", "ref_kind": "nested", "inner": items[0]}

    # --- Paths ---

    def dotted_path(self, items):
        return {"expr": "path", "parts": [str(i) for i in items]}

    def dotted_path_or_ident(self, items):
        parts = [str(i) for i in items]
        if len(parts) == 1:
            return {"expr": "ident", "name": parts[0]}
        return {"expr": "path", "parts": parts}

    # --- Types ---

    def named_type(self, items):
        return {"type": "named", "name": items[0]}

    def generic_type(self, items):
        return {"type": "generic", "name": items[0], "param": items[1]}

    def array_type(self, items):
        ty = items[0]
        size = items[1] if len(items) > 1 else None
        return {"type": "array", "element": ty, "size": size}

    def type_expr(self, items):
        return items[0]

    # --- Constraints ---

    def range_constraint(self, items):
        return {"constraint": "range", "min": items[0], "max": items[1]}

    def enum_constraint(self, items):
        return {"constraint": "enum", "values": items[0]}

    def constraint(self, items):
        return items[0]

    def default_value(self, items):
        return items[0]

    # --- Meta ---

    def meta_pair(self, items):
        return {"key": items[0], "value": items[1]}

    def meta_pair_list(self, items):
        return list(items)

    def meta_brackets(self, items):
        return items[0] if items else []

    # --- Fields & Lists ---

    def typed_field(self, items):
        return {"name": items[0], "type": items[1]}

    def typed_field_list(self, items):
        return list(items)

    def ident_list(self, items):
        return [str(i) for i in items]

    def expr_list(self, items):
        return list(items)

    # --- Four Primitives ---

    def in_port(self, items):
        fields = items[0] if items else []
        return InPort(fields=fields)

    def empty_meta(self, items):
        return items[0] if items else []

    def out_port(self, items):
        meta = []
        fields = []
        for item in items:
            if isinstance(item, list) and item and isinstance(item[0], dict) and "key" in item[0]:
                meta = item
            elif isinstance(item, list):
                fields = item
        return OutPort(meta=meta, fields=fields)

    def process_rule(self, items):
        meta = []
        rule = ProcessRule()
        for item in items:
            if isinstance(item, list) and item and isinstance(item[0], dict) and "key" in item[0]:
                meta = item
            elif isinstance(item, ProcessRule):
                rule = item
                break
        rule.meta = meta
        return rule

    def process_stmt(self, items):
        # Unwrap the single child (pre_stmt, post_stmt, assignment, for_all_stmt,
        # condition_stmt, description_stmt, or bare expr).
        return items[0]

    def process_body(self, items):
        rule = ProcessRule()
        for item in items:
            if isinstance(item, dict):
                s = item.get("_stmt")
                if s == "pre":
                    rule.pre.append(item["expr"])
                elif s == "post":
                    rule.post.append(item["expr"])
                elif s == "description":
                    rule.description = item["value"]
                else:
                    # assignment, for_all, condition, or bare expression
                    rule.body.append(item)
        return rule

    def pre_stmt(self, items):
        return {"_stmt": "pre", "expr": items[0]}

    def post_stmt(self, items):
        return {"_stmt": "post", "expr": items[0]}

    def requires_stmt(self, items):
        # `requires:` is a semantic alias for `pre:` — both are preconditions.
        return {"_stmt": "pre", "expr": items[0]}

    def data_field(self, items):
        name = items[0]
        ty = items[1]
        constraint = None
        default = None
        for item in items[2:]:
            if isinstance(item, dict) and "constraint" in item:
                constraint = item
            else:
                default = item
        return DataField(name=name, type=ty, constraint=constraint, default=default)

    # --- Statements ---

    def strategy_stmt(self, items):
        return {"_stmt": "strategy", "value": items[0]}

    def memory_stmt(self, items):
        return {"_stmt": "memory", "entries": list(items)}

    def memory_entry(self, items):
        return {"name": items[0], "args": list(items[1:])}

    def contains_stmt(self, items):
        return {"_stmt": "contains", "value": items[0]}

    def description_stmt(self, items):
        return {"_stmt": "description", "value": items[0]}

    def invariant_stmt(self, items):
        return {"_stmt": "invariant", "expr": items[0]}

    def temporal_stmt(self, items):
        return {"_stmt": "temporal", "expr": items[0]}

    def assignment(self, items):
        return {"_stmt": "assignment", "target": items[0], "value": items[1]}

    def for_all_stmt(self, items):
        return {"_stmt": "for_all", "type": items[0], "var": items[1],
                "condition": items[2] if len(items) > 3 else None,
                "body": items[-1]}

    def condition_stmt(self, items):
        return {"_stmt": "condition", "expr": items[0], "body": items[1]}

    # --- Entity definitions ---

    def _collect_entity_members(self, items):
        """Common collector for entity body members"""
        result = {
            "data_fields": [], "in_ports": [], "out_ports": [],
            "processes": [], "invariants": [], "temporals": [],
            "description": None, "classes": [],
        }
        for item in items:
            if isinstance(item, InPort):
                result["in_ports"].append(item)
            elif isinstance(item, OutPort):
                result["out_ports"].append(item)
            elif isinstance(item, ProcessRule):
                result["processes"].append(item)
            elif isinstance(item, DataField):
                result["data_fields"].append(item)
            elif isinstance(item, EntityDef):
                result["classes"].append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "invariant":
                    result["invariants"].append(item["expr"])
                elif s == "temporal":
                    result["temporals"].append(item["expr"])
                elif s == "description":
                    result["description"] = item["value"]
        return result

    def entity_body(self, items):
        return items

    def entity_member(self, items):
        return items[0]

    def abstraction_def(self, items):
        name = items[0]
        inherits = []
        members = []
        for item in items[1:]:
            if isinstance(item, list) and item and isinstance(item[0], str):
                inherits = item
            elif isinstance(item, list):
                members = item
        m = self._collect_entity_members(members)
        m.pop("classes", None)
        return EntityDef(kind="abstraction", name=name, inherits=inherits, **m)

    def class_def(self, items):
        name = items[0]
        inherits = []
        members = []
        for item in items[1:]:
            if isinstance(item, list) and item and isinstance(item[0], str):
                inherits = item
            elif isinstance(item, list):
                members = item
        m = self._collect_entity_members(members)
        m.pop("classes", None)
        return EntityDef(kind="class", name=name, inherits=inherits, **m)

    def instance_def(self, items):
        name = items[0]
        class_name = items[1]
        assignments = []
        for item in items[2:]:
            if isinstance(item, dict) and item.get("_stmt") == "assignment":
                assignments.append({"target": item["target"], "value": item["value"]})
        return InstanceDef(name=name, class_name=class_name, assignments=assignments)

    def inherits(self, items):
        return items[0]

    # --- Island ---

    def island_def(self, items):
        name = items[0]
        members = items[1] if len(items) > 1 else []
        island = IslandDef(name=name)
        m = self._collect_entity_members(members)
        island.in_ports = m["in_ports"]
        island.out_ports = m["out_ports"]
        island.processes = m["processes"]
        island.data_fields = m["data_fields"]
        island.classes = m["classes"]
        island.invariants = m["invariants"]
        island.temporals = m["temporals"]
        island.description = m["description"]
        for item in members:
            if isinstance(item, dict):
                s = item.get("_stmt")
                if s == "strategy":
                    island.strategy = item["value"]
                elif s == "contains":
                    island.contains = item["value"]
                elif s == "memory":
                    island.memory = item["entries"]
        return island

    def island_body(self, items):
        return items

    def island_member(self, items):
        return items[0]

    # --- Bridge ---

    def bridge_def(self, items):
        name = items[0]
        bridge = BridgeDef(name=name)
        # items[1] is a list produced by bridge_body; flatten it.
        body = items[1] if len(items) > 1 else []
        for item in body:
            if isinstance(item, dict):
                s = item.get("_stmt")
                if s == "from":
                    bridge.from_port = item["value"]
                elif s == "to":
                    bridge.to_port = item["value"]
                elif s == "contract":
                    bridge.contract = item
        return bridge

    def bridge_body(self, items):
        return list(items)

    def from_stmt(self, items):
        path = items[0]
        if isinstance(path, dict) and path.get("expr") == "path":
            return {"_stmt": "from", "value": ".".join(path["parts"])}
        return {"_stmt": "from", "value": str(path)}

    def to_stmt(self, items):
        path = items[0]
        if isinstance(path, dict) and path.get("expr") == "path":
            return {"_stmt": "to", "value": ".".join(path["parts"])}
        return {"_stmt": "to", "value": str(path)}

    def contract_block(self, items):
        inv = []
        temp = []
        for item in items:
            if isinstance(item, dict):
                if item.get("_stmt") == "invariant":
                    inv.append(item["expr"])
                elif item.get("_stmt") == "temporal":
                    temp.append(item["expr"])
        return {"_stmt": "contract", "invariants": inv, "temporals": temp}

    def contract_member(self, items):
        return items[0]

    # --- Registry ---

    def registry_def(self, items):
        name = items[0]
        entries = [i for i in items[1:] if isinstance(i, dict)]
        return RegistryDef(name=name, entries=entries)

    def register_stmt(self, items):
        name = items[0]
        meta = items[1] if len(items) > 1 else []
        return {"name": name, "meta": meta}

    # --- Verify ---

    def verify_def(self, items):
        target = items[0]
        checks = [i for i in items[1:] if isinstance(i, dict)]
        return VerifyDef(target=target, checks=checks)

    def check_stmt(self, items):
        return {"name": items[0], "expr": items[1]}

    # --- Stdlib type declarations ---

    def primitive_def(self, items):
        return PrimitiveDef(name=str(items[0]))

    def struct_field(self, items):
        return {"name": str(items[0]), "type": items[1]}

    def struct_field_list(self, items):
        return list(items)

    def struct_def(self, items):
        name = str(items[0])
        fields_list = []
        for item in items[1:]:
            if isinstance(item, list):
                fields_list = item
                break
        return StructDef(name=name, fields=fields_list)

    def enum_param_typed(self, items):
        return {"name": str(items[0]), "type": items[1]}

    def enum_param_bare(self, items):
        return {"name": str(items[0]), "type": None}

    def enum_variant_params(self, items):
        return list(items)

    def enum_variant(self, items):
        name = str(items[0])
        params = items[1] if len(items) > 1 else []
        return {"name": name, "params": params}

    def enum_variant_list(self, items):
        return list(items)

    def enum_def(self, items):
        name = str(items[0])
        variants = []
        for item in items[1:]:
            if isinstance(item, list):
                variants = item
                break
        return EnumDef(name=name, variants=variants)

    def map_type(self, items):
        return {"type": "map", "key": items[0], "value": items[1]}

    def inline_enum_type(self, items):
        return {"type": "inline_enum", "values": items[0]}

    # --- Expression / Predicate definitions ---

    def def_ident(self, items):
        """Kebab-case name rule: IDENT ('-' IDENT)* → joined string."""
        return "-".join(str(i) for i in items)

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

    # --- Import ---

    def item(self, items):
        return items[0]

    def import_stmt(self, items):
        path = items[0]
        if isinstance(path, dict) and path.get("expr") == "path":
            return path["parts"]
        return [str(path)]

    # --- Top level ---

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


# ============================================================
# PARSER API
# ============================================================

_GRAMMAR_PATH = Path(__file__).parent / "ark_grammar.lark"

# ARK project root (parent of tools/) — used by import resolver.
_ARK_ROOT = Path(__file__).resolve().parent.parent.parent

def get_parser() -> Lark:
    """Create or return cached Lark parser"""
    grammar_text = _GRAMMAR_PATH.read_text(encoding="utf-8")
    return Lark(grammar_text, parser="earley", propagate_positions=True)

def _parse_no_resolve(source: str, file_path: Optional[str] = None) -> ArkFile:
    """Parse source text into ArkFile AST without resolving imports.

    Raises ArkParseError (never a raw Lark exception) on syntax errors.
    """
    parser = get_parser()
    try:
        tree = parser.parse(source)
    except UnexpectedInput as exc:
        raise _lark_to_ark_error(exc, source, file_path) from None
    transformer = ArkTransformer()
    return transformer.transform(tree)

def _resolve_import_path(parts, base_dir: Path) -> Optional[Path]:
    """Resolve import dotted-path parts to an absolute .ark file path.

    Import like `stdlib.types` maps to `<ark_root>/dsl/stdlib/types.ark`.
    Returns None if no candidate file exists on disk.
    """
    if not parts:
        return None
    # Primary convention: dsl/<p0>/<p1>/.../<pN>.ark under the ARK project root.
    candidates = [
        _ARK_ROOT / "dsl" / Path(*parts[:-1]) / f"{parts[-1]}.ark",
        base_dir / Path(*parts[:-1]) / f"{parts[-1]}.ark",
    ]
    for cand in candidates:
        if cand.is_file():
            return cand.resolve()
    return None

def import_resolve(ark_file: ArkFile, file_path: Optional[Path],
                   visited: Optional[set] = None) -> ArkFile:
    """Recursively load imported .ark files and merge their items.

    For each import in `ark_file.imports`, resolve it to a file under
    `<ark_root>/dsl/...`, parse it, recurse, and PREPEND its items to the
    current file's items list (stdlib items appear first).

    - `file_path`: absolute path of the file that produced `ark_file`, used
      as a secondary base for resolution and for circular-import tracking.
    - `visited`: set of absolute import paths already loaded in this chain;
      prevents circular / duplicate re-parsing.
    - Missing files emit a stderr warning but do not crash.
    - Import files that fail to parse emit a stderr warning and are skipped.
    """
    if visited is None:
        visited = set()
    if file_path is not None:
        try:
            visited.add(Path(file_path).resolve())
        except OSError:
            pass

    base_dir = Path(file_path).resolve().parent if file_path else _ARK_ROOT

    prepended: list = []
    for imp in ark_file.imports:
        parts = list(imp) if isinstance(imp, (list, tuple)) else [str(imp)]
        resolved = _resolve_import_path(parts, base_dir)
        if resolved is None:
            print(f"[ark_parser] warning: import '{'.'.join(parts)}' "
                  f"could not be resolved (looked under {_ARK_ROOT / 'dsl'})",
                  file=sys.stderr)
            continue
        if resolved in visited:
            continue
        visited.add(resolved)
        try:
            sub_source = resolved.read_text(encoding="utf-8")
            sub_ast = _parse_no_resolve(sub_source, file_path=str(resolved))
        except ArkParseError:
            # Re-raise with the imported file's path already set by
            # _parse_no_resolve — caller will see a clean report.
            raise
        except Exception as e:
            print(f"[ark_parser] warning: failed to parse import "
                  f"'{'.'.join(parts)}' at {resolved}: {e}", file=sys.stderr)
            continue
        sub_ast = import_resolve(sub_ast, resolved, visited)
        prepended.extend(sub_ast.items)

    if prepended:
        ark_file.items = prepended + list(ark_file.items)
    return ark_file

def _build_indices(ark_file: ArkFile) -> ArkFile:
    """Populate ArkFile.classes / instances / island_classes from items.

    Pure-additive: `items` is left untouched. Duplicate class names shadow
    (last-wins) with an insertion-order-preserving dict, matching how the
    rest of the codebase resolves names. Orphan instances (class_name not
    declared) still land in `instances` — consumers can detect them by
    checking `class_name not in ark_file.classes`.
    """
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


def parse(source: str, file_path=None) -> ArkFile:
    """Parse .ark source → ArkFile AST.

    If `file_path` is provided, import statements like `import stdlib.types`
    are resolved relative to the ARK project root and their items merged in.
    Without a file_path, import resolution is skipped (a debug note is
    written to stderr if any imports were declared).
    """
    ark_file = _parse_no_resolve(source, file_path=str(file_path) if file_path else None)
    if file_path is None:
        if ark_file.imports:
            print("[ark_parser] debug: parse() called without file_path; "
                  "skipping import resolution", file=sys.stderr)
        return _build_indices(ark_file)
    return _build_indices(import_resolve(ark_file, Path(file_path)))

def to_json(ark_file: ArkFile) -> str:
    """Serialize ArkFile → JSON"""
    def convert(obj):
        if hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        elif isinstance(obj, list):
            return [convert(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        return obj
    return json.dumps(convert(ark_file), indent=2, ensure_ascii=False)


# ============================================================
# CLI
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python ark_parser.py <file.ark> [--json] [--tree]")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    source = filepath.read_text(encoding="utf-8")

    if "--tree" in sys.argv:
        # Raw parse tree (for debugging grammar)
        parser = get_parser()
        tree = parser.parse(source)
        print(tree.pretty())
    else:
        # Full AST → JSON
        ark_file = parse(source, file_path=filepath)
        print(to_json(ark_file))

if __name__ == "__main__":
    main()
