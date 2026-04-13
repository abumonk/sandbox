"""ark_diff — structural diff between two .ark spec versions.

Compares two parsed ArkFile ASTs (as JSON dicts) and produces a list of
`Change` records describing what was added, removed, or modified.

Matching strategy
-----------------
Top-level items are matched by `(kind, name)`. No rename detection — a
renamed class shows up as one removed + one added entry. That's fine for
the MVP; rename heuristics are a future task.

Change shape
------------
Each change is a dict:

    {
        "change":    "added" | "removed" | "modified",
        "item_type": "class" | "abstraction" | "instance" | "island" |
                     "bridge" | "registry" | "verify",
        "name":      "<item name>",
        "details":   [str, ...]   # only for "modified"
    }

Fields compared (MVP depth):
  - class/abstraction: $data fields, @in/@out ports, #process count,
                       invariants count, temporals count
  - instance:          class_name, assignment targets
  - island:            strategy, contains, data fields, ports, processes
  - bridge:            from_port, to_port, contract presence
  - registry:          entry set and each entry's phase/priority
  - verify:            target and checks count

Body-level statement diff, expression diff, and rename detection are
explicitly out of scope for MVP and noted on the CLI.
"""

from typing import Any, Dict, List, Tuple


# ============================================================
# Small helpers
# ============================================================

def _type_str(type_node: Any) -> str:
    """Canonicalize a type AST node to a comparable string."""
    if not isinstance(type_node, dict):
        return str(type_node)
    kind = type_node.get("type")
    if kind == "named":
        return type_node.get("name", "?")
    if kind == "generic":
        return f"{type_node.get('name', '?')}<{_type_str(type_node.get('inner', {}))}>"
    if kind == "array":
        return f"[{_type_str(type_node.get('elem', {}))}]"
    if kind == "map":
        return f"[{_type_str(type_node.get('key', {}))}:{_type_str(type_node.get('value', {}))}]"
    return type_node.get("name", str(type_node))


def _expr_str(expr: Any) -> str:
    """Flatten an expression node to a short human-readable form."""
    if expr is None:
        return ""
    if not isinstance(expr, dict):
        return str(expr)
    kind = expr.get("expr")
    if kind == "number":
        return str(expr.get("value"))
    if kind == "string":
        return str(expr.get("value"))
    if kind == "bool":
        return str(expr.get("value"))
    if kind == "ident":
        return str(expr.get("name", "?"))
    if kind == "path":
        return ".".join(expr.get("parts", []))
    if kind == "binop":
        return f"({_expr_str(expr.get('left'))} {expr.get('op')} {_expr_str(expr.get('right'))})"
    if kind == "unary":
        return f"({expr.get('op')} {_expr_str(expr.get('operand'))})"
    if kind == "temporal":
        return f"{expr.get('op')}({_expr_str(expr.get('operand'))})"
    if kind == "call":
        args = ", ".join(_expr_str(a) for a in expr.get("args", []))
        return f"{expr.get('name')}({args})"
    return kind or "?"


def _constraint_str(c: Any) -> str:
    if not isinstance(c, dict):
        return ""
    if c.get("constraint") == "range":
        return f"[{_expr_str(c.get('min'))}..{_expr_str(c.get('max'))}]"
    if c.get("constraint") == "enum":
        vals = ", ".join(_expr_str(v) for v in c.get("values", []))
        return f"{{{vals}}}"
    return ""


def _key(item: Dict[str, Any]) -> Tuple[str, str]:
    return (item.get("kind", "?"), item.get("name", item.get("target", "?")))


def _index(items: List[Dict[str, Any]]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    out: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for item in items:
        out[_key(item)] = item
    return out


# ============================================================
# Per-item shallow diffs (all return list[str] of change lines)
# ============================================================

def _diff_data_fields(old: list, new: list) -> List[str]:
    """Diff a pair of $data field lists.

    Detects added/removed fields, type changes, default changes,
    constraint changes. Matches by field name.
    """
    lines: List[str] = []
    old_by = {f.get("name"): f for f in (old or [])}
    new_by = {f.get("name"): f for f in (new or [])}

    for name in sorted(new_by.keys() - old_by.keys()):
        f = new_by[name]
        lines.append(f"+ $data {name}: {_type_str(f.get('type'))}")
    for name in sorted(old_by.keys() - new_by.keys()):
        f = old_by[name]
        lines.append(f"- $data {name}: {_type_str(f.get('type'))}")
    for name in sorted(old_by.keys() & new_by.keys()):
        a = old_by[name]
        b = new_by[name]
        at = _type_str(a.get("type"))
        bt = _type_str(b.get("type"))
        if at != bt:
            lines.append(f"~ $data {name}: type {at} → {bt}")
        ac = _constraint_str(a.get("constraint"))
        bc = _constraint_str(b.get("constraint"))
        if ac != bc:
            lines.append(f"~ $data {name}: constraint {ac or '<none>'} → {bc or '<none>'}")
        ad = _expr_str(a.get("default"))
        bd = _expr_str(b.get("default"))
        if ad != bd:
            lines.append(f"~ $data {name}: default {ad or '<none>'} → {bd or '<none>'}")
    return lines


def _port_fields(port_list: list) -> Dict[str, str]:
    """Flatten a list of ports into {field_name: type_str}."""
    out: Dict[str, str] = {}
    for p in port_list or []:
        for f in p.get("fields", []):
            name = f.get("name")
            if name:
                out[name] = _type_str(f.get("type"))
    return out


def _diff_ports(tag: str, old: list, new: list) -> List[str]:
    lines: List[str] = []
    a = _port_fields(old)
    b = _port_fields(new)
    for name in sorted(b.keys() - a.keys()):
        lines.append(f"+ {tag} {name}: {b[name]}")
    for name in sorted(a.keys() - b.keys()):
        lines.append(f"- {tag} {name}: {a[name]}")
    for name in sorted(a.keys() & b.keys()):
        if a[name] != b[name]:
            lines.append(f"~ {tag} {name}: type {a[name]} → {b[name]}")
    return lines


def _diff_entity(old: dict, new: dict) -> List[str]:
    """Diff a class or abstraction."""
    lines: List[str] = []
    lines.extend(_diff_data_fields(old.get("data_fields", []), new.get("data_fields", [])))
    lines.extend(_diff_ports("@in", old.get("in_ports", []), new.get("in_ports", [])))
    lines.extend(_diff_ports("@out", old.get("out_ports", []), new.get("out_ports", [])))

    old_procs = len(old.get("processes", []) or [])
    new_procs = len(new.get("processes", []) or [])
    if old_procs != new_procs:
        lines.append(f"~ #process count: {old_procs} → {new_procs}")

    old_inv = len(old.get("invariants", []) or [])
    new_inv = len(new.get("invariants", []) or [])
    if old_inv != new_inv:
        lines.append(f"~ invariants count: {old_inv} → {new_inv}")

    old_tmp = len(old.get("temporals", []) or [])
    new_tmp = len(new.get("temporals", []) or [])
    if old_tmp != new_tmp:
        lines.append(f"~ temporals count: {old_tmp} → {new_tmp}")

    old_inh = list(old.get("inherits") or [])
    new_inh = list(new.get("inherits") or [])
    if old_inh != new_inh:
        lines.append(f"~ inherits: {old_inh or '<none>'} → {new_inh or '<none>'}")
    return lines


def _diff_instance(old: dict, new: dict) -> List[str]:
    lines: List[str] = []
    if old.get("class_name") != new.get("class_name"):
        lines.append(
            f"~ class: {old.get('class_name')} → {new.get('class_name')}"
        )
    old_assigns = {
        (a.get("target") or {}).get("name") if isinstance(a.get("target"), dict) else a.get("target"):
            _expr_str(a.get("value"))
        for a in (old.get("assignments") or [])
        if isinstance(a, dict)
    }
    new_assigns = {
        (a.get("target") or {}).get("name") if isinstance(a.get("target"), dict) else a.get("target"):
            _expr_str(a.get("value"))
        for a in (new.get("assignments") or [])
        if isinstance(a, dict)
    }
    for name in sorted(new_assigns.keys() - old_assigns.keys()):
        lines.append(f"+ assign {name} = {new_assigns[name]}")
    for name in sorted(old_assigns.keys() - new_assigns.keys()):
        lines.append(f"- assign {name} = {old_assigns[name]}")
    for name in sorted(old_assigns.keys() & new_assigns.keys()):
        if old_assigns[name] != new_assigns[name]:
            lines.append(
                f"~ assign {name}: {old_assigns[name]} → {new_assigns[name]}"
            )
    return lines


def _diff_island(old: dict, new: dict) -> List[str]:
    lines: List[str] = []
    if old.get("strategy") != new.get("strategy"):
        lines.append(
            f"~ strategy: {old.get('strategy')} → {new.get('strategy')}"
        )
    old_c = list(old.get("contains") or [])
    new_c = list(new.get("contains") or [])
    if sorted(old_c) != sorted(new_c):
        added = sorted(set(new_c) - set(old_c))
        removed = sorted(set(old_c) - set(new_c))
        if added:
            lines.append(f"+ contains: {', '.join(added)}")
        if removed:
            lines.append(f"- contains: {', '.join(removed)}")
    lines.extend(_diff_data_fields(old.get("data_fields", []), new.get("data_fields", [])))
    lines.extend(_diff_ports("@in", old.get("in_ports", []), new.get("in_ports", [])))
    lines.extend(_diff_ports("@out", old.get("out_ports", []), new.get("out_ports", [])))
    old_procs = len(old.get("processes", []) or [])
    new_procs = len(new.get("processes", []) or [])
    if old_procs != new_procs:
        lines.append(f"~ #process count: {old_procs} → {new_procs}")
    return lines


def _diff_bridge(old: dict, new: dict) -> List[str]:
    lines: List[str] = []
    if old.get("from_port") != new.get("from_port"):
        lines.append(f"~ from: {old.get('from_port')} → {new.get('from_port')}")
    if old.get("to_port") != new.get("to_port"):
        lines.append(f"~ to: {old.get('to_port')} → {new.get('to_port')}")
    had_contract = bool(old.get("contract"))
    has_contract = bool(new.get("contract"))
    if had_contract != has_contract:
        lines.append(
            f"~ contract: {'present' if had_contract else 'absent'} → "
            f"{'present' if has_contract else 'absent'}"
        )
    return lines


def _registry_entry_key(entry: dict) -> str:
    return entry.get("name", "?") if isinstance(entry, dict) else str(entry)


def _diff_registry(old: dict, new: dict) -> List[str]:
    lines: List[str] = []
    old_entries = {_registry_entry_key(e): e for e in (old.get("entries") or []) if isinstance(e, dict)}
    new_entries = {_registry_entry_key(e): e for e in (new.get("entries") or []) if isinstance(e, dict)}
    for name in sorted(new_entries.keys() - old_entries.keys()):
        lines.append(f"+ register {name}")
    for name in sorted(old_entries.keys() - new_entries.keys()):
        lines.append(f"- register {name}")
    for name in sorted(old_entries.keys() & new_entries.keys()):
        a = old_entries[name]
        b = new_entries[name]
        a_meta = {m.get("key"): _expr_str(m.get("value")) for m in (a.get("meta") or []) if isinstance(m, dict)}
        b_meta = {m.get("key"): _expr_str(m.get("value")) for m in (b.get("meta") or []) if isinstance(m, dict)}
        for k in sorted(set(a_meta) | set(b_meta)):
            if a_meta.get(k) != b_meta.get(k):
                lines.append(
                    f"~ register {name}: {k} {a_meta.get(k, '<none>')} → {b_meta.get(k, '<none>')}"
                )
    return lines


def _diff_verify(old: dict, new: dict) -> List[str]:
    lines: List[str] = []
    if old.get("target") != new.get("target"):
        lines.append(f"~ target: {old.get('target')} → {new.get('target')}")
    old_checks = len(old.get("checks") or [])
    new_checks = len(new.get("checks") or [])
    if old_checks != new_checks:
        lines.append(f"~ checks count: {old_checks} → {new_checks}")
    return lines


_DIFFERS = {
    "class":       _diff_entity,
    "abstraction": _diff_entity,
    "instance":    _diff_instance,
    "island":      _diff_island,
    "bridge":      _diff_bridge,
    "registry":    _diff_registry,
    "verify":      _diff_verify,
}


# ============================================================
# Public entry point
# ============================================================

def diff_ast(old_ast: dict, new_ast: dict) -> List[Dict[str, Any]]:
    """Return a list of Change records describing how `new` differs from `old`.

    Inputs are AST dicts produced by ark_parser.to_json (JSON-deserialized).
    """
    old_items = old_ast.get("items", []) or []
    new_items = new_ast.get("items", []) or []
    old_index = _index(old_items)
    new_index = _index(new_items)

    changes: List[Dict[str, Any]] = []

    # Added
    for key in sorted(new_index.keys() - old_index.keys()):
        kind, name = key
        changes.append({
            "change": "added",
            "item_type": kind,
            "name": name,
            "details": [],
        })

    # Removed
    for key in sorted(old_index.keys() - new_index.keys()):
        kind, name = key
        changes.append({
            "change": "removed",
            "item_type": kind,
            "name": name,
            "details": [],
        })

    # Modified
    for key in sorted(old_index.keys() & new_index.keys()):
        kind, name = key
        differ = _DIFFERS.get(kind)
        if differ is None:
            continue
        details = differ(old_index[key], new_index[key])
        if details:
            changes.append({
                "change": "modified",
                "item_type": kind,
                "name": name,
                "details": details,
            })

    return changes


def render(changes: List[Dict[str, Any]]) -> str:
    """Render a list of Change records to a human-readable string."""
    if not changes:
        return "no structural changes"
    out: List[str] = []
    sigil = {"added": "+", "removed": "-", "modified": "~"}
    for c in changes:
        out.append(
            f"{sigil.get(c['change'], '?')} {c['item_type']} {c['name']}"
        )
        for line in c.get("details", []):
            out.append(f"    {line}")
    return "\n".join(out)
