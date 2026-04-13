"""ark_dispatch — map backlog Tasks to Claude Code subagent roles.

Reads a parsed ArkFile AST (as JSON dict) and produces a dispatch plan:
which ready `Task` should be executed next, by which `Subagent`, in
what priority order. The plan is PURE DATA — it does not spawn agents,
modify the backlog file, or run anything. It is meant to be consumed
by a human (or by Claude Code inside an active session) who then
actually invokes the Task tool with the chosen subagent.

Why no auto-spawn
-----------------
Claude Code subagents can only be invoked via the Task tool from inside
a live agent turn — a standalone Python script has no way to start one.
What this tool DOES give you is the reconciled "next task → right
subagent" mapping derived from the spec itself, so the orchestration
decision is reproducible and spec-driven rather than ad-hoc.

Task classes are identified by direct inheritance from `Task`; same for
Subagent classes. Field values come from each class's `$data` defaults.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ============================================================
# Extraction helpers
# ============================================================

def _default_value(field: dict) -> Any:
    """Pull a plain-Python default out of a $data field AST node.

    String defaults keep their surrounding quotes in the AST, so we
    strip them here for ergonomic access.
    """
    default = field.get("default")
    if not isinstance(default, dict):
        return None
    kind = default.get("expr")
    if kind == "number":
        return default.get("value")
    if kind == "bool":
        return default.get("value")
    if kind == "string":
        v = default.get("value", "")
        if isinstance(v, str) and len(v) >= 2 and v[0] == '"' and v[-1] == '"':
            return v[1:-1]
        return v
    if kind == "ident":
        return default.get("name")
    return None


def _inherits_from(item: dict, ancestor: str) -> bool:
    """Direct-inheritance check. Transitive chains are out of MVP scope."""
    inherits = item.get("inherits") or []
    return ancestor in inherits


def _fields_as_dict(item: dict) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for f in item.get("data_fields", []) or []:
        name = f.get("name")
        if name:
            out[name] = _default_value(f)
    return out


# ============================================================
# Collection
# ============================================================

def collect_tasks(ast: dict) -> List[Dict[str, Any]]:
    """Return every class inheriting directly from `Task`, flattened to
    a dict `{class_name, id, title, priority, status, phase, agent}`.
    """
    tasks: List[Dict[str, Any]] = []
    for item in ast.get("items", []) or []:
        if item.get("kind") != "class":
            continue
        if not _inherits_from(item, "Task"):
            continue
        fields = _fields_as_dict(item)
        tasks.append({
            "class_name": item.get("name", "?"),
            "id": fields.get("id"),
            "title": fields.get("title"),
            "priority": fields.get("priority"),
            "status": fields.get("status"),
            "phase": fields.get("phase"),
            "agent": fields.get("agent"),
        })
    return tasks


def collect_subagents(ast: dict) -> List[Dict[str, Any]]:
    """Return every class inheriting directly from `Subagent`."""
    agents: List[Dict[str, Any]] = []
    for item in ast.get("items", []) or []:
        if item.get("kind") != "class":
            continue
        if not _inherits_from(item, "Subagent"):
            continue
        fields = _fields_as_dict(item)
        agents.append({
            "class_name": item.get("name", "?"),
            "name": fields.get("name"),
            "role": fields.get("role"),
            "capacity": fields.get("capacity"),
            "busy": fields.get("busy"),
        })
    return agents


# ============================================================
# Routing
# ============================================================

def find_ready(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ready = status `todo`. Returns a new list sorted by (priority asc,
    class_name asc). Tasks with no priority go last.
    """
    ready = [t for t in tasks if t.get("status") == "todo"]

    def _key(t: Dict[str, Any]):
        pri = t.get("priority")
        pri_rank = pri if isinstance(pri, (int, float)) else 999
        return (pri_rank, t.get("class_name") or "")

    return sorted(ready, key=_key)


def assign_subagent(task: Dict[str, Any],
                    subagents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Pick a Subagent for a Task.

    The task's `agent` field matches against each subagent's `name` first,
    then its `role`. First match wins (list order). Returns None when no
    subagent matches — caller decides whether that's a configuration
    error or a fallback to a default.
    """
    wanted = task.get("agent")
    if not wanted:
        return None
    for sa in subagents:
        if sa.get("name") == wanted:
            return sa
    for sa in subagents:
        if sa.get("role") == wanted:
            return sa
    return None


# ============================================================
# Rendering
# ============================================================

def build_plan(ast: dict) -> Dict[str, Any]:
    """Top-level: collect, filter, assign, return a structured plan."""
    tasks = collect_tasks(ast)
    subagents = collect_subagents(ast)
    ready = find_ready(tasks)
    dispatch: List[Dict[str, Any]] = []
    for t in ready:
        sa = assign_subagent(t, subagents)
        dispatch.append({
            "task": t,
            "subagent": sa,
            "resolved": sa is not None,
        })
    return {
        "total_tasks": len(tasks),
        "ready_count": len(ready),
        "subagents_known": len(subagents),
        "dispatch": dispatch,
    }


def render(plan: Dict[str, Any]) -> str:
    """Human-readable dispatch report."""
    lines: List[str] = []
    lines.append(
        f"tasks: {plan['total_tasks']} total · {plan['ready_count']} ready · "
        f"{plan['subagents_known']} subagent classes known"
    )
    lines.append("")
    if not plan["dispatch"]:
        lines.append("(nothing ready)")
        return "\n".join(lines)
    for entry in plan["dispatch"]:
        t = entry["task"]
        sa = entry["subagent"]
        pri = t.get("priority")
        pri_s = f"p{pri}" if pri is not None else "p?"
        agent = sa.get("name") if sa else f"<unresolved '{t.get('agent')}'>"
        title = t.get("title") or t.get("id") or t.get("class_name")
        lines.append(f"  [{pri_s}] {t.get('class_name')} → {agent}")
        lines.append(f"        {title}")
    return "\n".join(lines)
