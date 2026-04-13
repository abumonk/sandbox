"""
Studio Verifier
Checks studio-specific invariants in ARK studio hierarchy specs.

Checks:
  1. Escalation acyclicity — no cycles in role.escalates_to graph
  2. Command-role resolution — every command's required_role exists and role
     has sufficient tools for the command
  3. Hook event validity — every hook's event is in the allowed set
  4. Rule constraints — every rule has a non-empty path (glob) and constraint
  5. Rule satisfiability — Z3 SAT check that constraint expressions are
     satisfiable (not trivially false)
  6. Tool permission consistency — no role declares an unauthorised tool
"""

from z3 import (
    Int, Bool, Real, And, Or, Not, Implies, Solver, sat, unsat, IntVal,
    BoolVal, RealVal,
)

# ============================================================
# CONSTANTS
# ============================================================

ALLOWED_HOOK_EVENTS = {
    "pre_commit", "post_commit",
    "pre_push", "post_push",
    "session_start", "session_end",
    "file_change",
    "task_complete",
    "build_start", "build_end",
    "test_start", "test_end",
}

DEFAULT_ALLOWED_TOOLS = {
    "Read", "Write", "Edit", "Glob", "Grep",
    "Bash", "WebSearch", "WebFetch", "MCP",
}


# ============================================================
# CHECK 1: Escalation Acyclicity
# ============================================================

def verify_escalation_acyclicity(roles: list) -> list:
    """Check that the escalation graph (role → escalates_to) is acyclic.

    Uses Z3 Int ordinals: assign each role an integer ordinal and assert that
    for every escalates_to edge (A → B) the ordinal of B is strictly greater
    than the ordinal of A.  If the solver can satisfy all constraints the
    hierarchy is acyclic.  A cycle would make the constraints UNSAT (each node
    in the cycle would need to be both greater-than and less-than another).

    Additional checks:
      - Every escalates_to target must reference an existing role name.
      - Director-tier roles (no escalates_to) are the allowed chain terminals.
      - Director-tier roles must NOT have escalates_to set.

    Returns a list of error strings; empty list means all checks passed.
    """
    errors: list[str] = []

    if not roles:
        return errors

    # Build name → role mapping
    role_map: dict[str, dict] = {}
    for role in roles:
        name = role.get("name") or role.get("role")
        if not name:
            continue
        role_map[name] = role

    known_names = set(role_map.keys())

    # Identify Directors (tier == "Director" or kind == "director") and
    # roles with no escalates_to.  Both are valid chain terminals.
    def _is_director(role: dict) -> bool:
        tier = role.get("tier", "")
        # tier may be a string ("Director") or an expr dict ({"expr":"number","value":1})
        if isinstance(tier, dict):
            # tier 1 = Director
            return tier.get("value") == 1
        kind = role.get("kind", "")
        return str(tier).lower() == "director" or str(kind).lower() == "director"

    # Validate each role's escalates_to target
    escalation_edges: list[tuple[str, str]] = []
    for name, role in role_map.items():
        target = role.get("escalates_to")
        if target is None:
            continue  # chain terminal — allowed for anyone without escalates_to
        if target not in known_names:
            errors.append(
                f"role '{name}': escalates_to '{target}' is not a known role"
            )
        else:
            escalation_edges.append((name, target))
        if _is_director(role):
            errors.append(
                f"role '{name}' is a Director-tier role and must not have escalates_to"
            )

    # Use Z3 to prove acyclicity via ordinal assignment.
    # We create one Int variable per role, then add:
    #   ord[A] < ord[B]  for every edge A → B
    # If SAT → acyclic.  If UNSAT → cycle exists (the constraints contradict).
    if escalation_edges:
        ord_vars = {name: Int(f"ord_{name}") for name in role_map}
        s = Solver()
        # All ordinals must be non-negative
        for v in ord_vars.values():
            s.add(v >= IntVal(0))
        # For each escalation edge, the target must have a strictly higher ordinal
        for (src, dst) in escalation_edges:
            if src in ord_vars and dst in ord_vars:
                s.add(ord_vars[src] < ord_vars[dst])

        result = s.check()
        if result == unsat:
            # The constraints are contradictory → cycles exist.
            # Detect cycles via plain graph DFS so we can report which roles
            # are involved.
            cycle_roles = _find_cycle_roles(escalation_edges, known_names)
            if cycle_roles:
                errors.append(
                    f"Escalation cycle detected involving roles: "
                    f"{', '.join(sorted(cycle_roles))}"
                )
            else:
                errors.append("Escalation cycle detected (unable to identify specific roles)")
        elif result == sat:
            pass  # acyclic — no errors from this check
        else:
            # Z3 returned unknown — treat as a warning, not a hard failure
            errors.append(
                "Z3 could not determine escalation acyclicity (UNKNOWN result)"
            )

    return errors


def _find_cycle_roles(edges: list[tuple[str, str]], all_names: set) -> set:
    """DFS-based cycle detection; returns all role names that are part of a cycle."""
    adj: dict[str, list[str]] = {n: [] for n in all_names}
    for src, dst in edges:
        adj[src].append(dst)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in all_names}
    cycle_nodes: set = set()

    def dfs(node: str, path: list) -> bool:
        color[node] = GRAY
        path.append(node)
        for nbr in adj.get(node, []):
            if color[nbr] == GRAY:
                # Found a back edge → cycle
                cycle_start = path.index(nbr)
                cycle_nodes.update(path[cycle_start:])
                return True
            if color[nbr] == WHITE:
                if dfs(nbr, path):
                    return True
        path.pop()
        color[node] = BLACK
        return False

    for node in list(all_names):
        if color[node] == WHITE:
            dfs(node, [])

    return cycle_nodes


# ============================================================
# CHECK 2: Command-Role Resolution
# ============================================================

def verify_command_resolution(commands: list, roles: list) -> list:
    """Check that every command's required_role references an existing role
    and that the role's tools set is sufficient for the command's needs.

    For each command with a required_role:
      - The role must exist in the roles list.
      - If the command declares 'required_tools', every listed tool must
        appear in the role's 'tools' list.
      - If the command declares 'required_tools' but the role has no 'tools'
        list at all, that is reported as a missing-tool error.

    Returns a list of error strings; empty list means all checks passed.
    """
    errors: list[str] = []

    # Build role map: name → role dict
    role_map: dict[str, dict] = {}
    for role in roles:
        name = role.get("name") or role.get("role")
        if name:
            role_map[name] = role

    for cmd in commands:
        cmd_name = cmd.get("name") or cmd.get("command") or "<unnamed>"
        required_role = cmd.get("required_role") or cmd.get("role")
        if required_role is None:
            continue  # no role constraint — skip

        # Check 1: role must exist
        if required_role not in role_map:
            errors.append(
                f"command '{cmd_name}': required_role '{required_role}' "
                f"is not a known role"
            )
            continue  # skip tool check if role is unknown

        # Check 2: role must have sufficient tools for the command
        role = role_map[required_role]
        role_tools_raw = role.get("tools") or []
        role_tools: set[str] = set()
        for t in role_tools_raw:
            tool_name = t if isinstance(t, str) else t.get("name", str(t))
            role_tools.add(tool_name)

        required_tools = cmd.get("required_tools") or cmd.get("tools") or []
        if isinstance(required_tools, str):
            required_tools = [required_tools]
        for tool in required_tools:
            tool_name = tool if isinstance(tool, str) else tool.get("name", str(tool))
            if tool_name not in role_tools:
                errors.append(
                    f"command '{cmd_name}': required_role '{required_role}' "
                    f"is missing required tool '{tool_name}'"
                )

    return errors


# ============================================================
# CHECK 3: Hook Event Validity
# ============================================================

def verify_hook_events(hooks: list,
                       allowed_events: set | None = None) -> list:
    """Check that every hook's event is in the allowed set.

    Returns a list of error strings; empty list means all checks passed.
    """
    errors: list[str] = []
    if allowed_events is None:
        allowed_events = ALLOWED_HOOK_EVENTS

    for hook in hooks:
        hook_name = hook.get("name") or hook.get("hook") or "<unnamed>"
        event = hook.get("event")
        if event is None:
            errors.append(f"hook '{hook_name}': missing 'event' field")
            continue
        if event not in allowed_events:
            errors.append(
                f"hook '{hook_name}': event '{event}' is not in the allowed "
                f"set {sorted(allowed_events)}"
            )

    return errors


# ============================================================
# CHECK 4: Rule Constraints
# ============================================================

def verify_rule_constraints(rules: list) -> list:
    """Check that every rule has a non-empty path (glob) and constraint.

    Returns a list of error strings; empty list means all checks passed.
    """
    errors: list[str] = []

    for i, rule in enumerate(rules):
        rule_name = rule.get("name") or f"rule[{i}]"
        path = rule.get("path") or rule.get("glob") or rule.get("pattern")
        constraint = rule.get("constraint") or rule.get("rule")

        if not path or not str(path).strip():
            errors.append(f"rule '{rule_name}': missing or empty path/glob")
        if not constraint or not str(constraint).strip():
            errors.append(f"rule '{rule_name}': missing or empty constraint")

    return errors


# ============================================================
# CHECK 5: Rule Satisfiability (Z3 SAT)
# ============================================================

def verify_rule_satisfiability(rules: list) -> list:
    """Use Z3 to check that each rule's constraint is satisfiable.

    Supported constraint expressions (parsed from the constraint string):
      - Simple boolean literal: "true" / "false"
      - Comparisons with a single variable: "x > 0", "count <= 10",
        "value == 5", "flag != false"
      - Conjunction/disjunction: "a > 0 AND b < 100", "x > 0 OR y > 0"

    If a constraint string cannot be parsed into a Z3 expression the check
    is skipped for that rule (reported as a warning, not an error).  Only
    a provably UNSAT constraint is reported as an error.

    Returns a list of error strings; empty list means all checks passed.
    """
    errors: list[str] = []

    def _parse_constraint(expr: str):
        """Parse a simple constraint expression into a Z3 formula.

        Returns a Z3 BoolRef or None if the expression cannot be parsed.
        """
        expr = expr.strip()
        if not expr:
            return None

        # Boolean literal shortcuts
        low = expr.lower()
        if low == "true":
            return BoolVal(True)
        if low == "false":
            return BoolVal(False)

        # Handle AND / OR conjunctions (case-insensitive)
        # Split on the outermost AND/OR (left-to-right, simple one-level)
        for sep, combiner in [(" AND ", And), (" and ", And),
                               (" OR ", Or), (" or ", Or)]:
            idx = expr.upper().find(" AND ") if combiner is And else expr.upper().find(" OR ")
            if idx != -1:
                left_str = expr[:idx].strip()
                right_str = expr[idx + len(" AND "):].strip() if combiner is And else expr[idx + len(" OR "):].strip()
                left = _parse_constraint(left_str)
                right = _parse_constraint(right_str)
                if left is not None and right is not None:
                    return combiner(left, right)
                return None  # can't parse sub-expressions

        # Simple comparison: VAR OP VALUE
        import re
        m = re.match(
            r'^([A-Za-z_][A-Za-z0-9_]*)\s*(==|!=|>=|<=|>|<)\s*(.+)$',
            expr
        )
        if m:
            var_name, op, val_str = m.group(1), m.group(2), m.group(3).strip()
            # Determine value type and create Z3 variable + constraint
            val_lower = val_str.lower()
            if val_lower in ("true", "false"):
                var = Bool(f"rule_var_{var_name}")
                val = BoolVal(val_lower == "true")
            elif "." in val_str:
                try:
                    val = RealVal(float(val_str))
                    var = Real(f"rule_var_{var_name}")
                except ValueError:
                    return None
            else:
                try:
                    val = IntVal(int(val_str))
                    var = Int(f"rule_var_{var_name}")
                except ValueError:
                    return None

            if op == "==":
                return var == val
            elif op == "!=":
                return var != val
            elif op == ">":
                return var > val
            elif op == "<":
                return var < val
            elif op == ">=":
                return var >= val
            elif op == "<=":
                return var <= val

        return None  # unable to parse

    for i, rule in enumerate(rules):
        rule_name = rule.get("name") or f"rule[{i}]"
        constraint_str = (
            rule.get("constraint") or rule.get("rule") or ""
        ).strip()

        if not constraint_str:
            # verify_rule_constraints() already reports empty constraints
            continue

        formula = _parse_constraint(constraint_str)
        if formula is None:
            # Cannot parse — skip SAT check, not an error
            continue

        s = Solver()
        s.add(formula)
        result = s.check()
        if result == unsat:
            errors.append(
                f"rule '{rule_name}': constraint '{constraint_str}' is "
                f"unsatisfiable (trivially false)"
            )
        elif result != sat:
            # Z3 returned unknown — warn but don't fail
            errors.append(
                f"rule '{rule_name}': Z3 could not determine satisfiability "
                f"of constraint '{constraint_str}' (UNKNOWN result)"
            )

    return errors


# ============================================================
# CHECK 6: Tool Permission Consistency
# ============================================================

def verify_tool_permissions(roles: list,
                            allowed_tools: set | None = None) -> list:
    """Check that no role declares a tool outside the allowed set.

    Returns a list of error strings; empty list means all checks passed.
    """
    errors: list[str] = []
    if allowed_tools is None:
        allowed_tools = DEFAULT_ALLOWED_TOOLS

    for role in roles:
        name = role.get("name") or role.get("role") or "<unnamed>"
        tools = role.get("tools") or []
        for tool in tools:
            tool_name = tool if isinstance(tool, str) else tool.get("name", str(tool))
            if tool_name not in allowed_tools:
                errors.append(
                    f"role '{name}': tool '{tool_name}' is not in the allowed "
                    f"tool set {sorted(allowed_tools)}"
                )

    return errors


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def verify_studio(ark_file: dict) -> dict:
    """Run all studio checks on a parsed ArkFile dict.

    Expected keys in ark_file (all optional):
      - items: list of parsed ARK items (may include role, command, hook, rule kinds)
      - roles: list of role dicts (alternative flat structure)
      - commands: list of command dicts
      - hooks: list of hook dicts
      - rules: list of rule dicts

    Returns a dict:
      {
        "checks": {check_name: [result_record, ...]},
        "errors": [str, ...],   # all combined error strings
        "summary": {"total": N, "passed": N, "failed": N}
      }
    """
    # Collect items either from flat lists or from items[] by kind
    items = ark_file.get("items", [])

    def _collect(kind_set: set) -> list:
        collected = []
        for it in items:
            if isinstance(it, dict) and it.get("kind") in kind_set:
                collected.append(it)
        return collected

    def _to_list(val):
        """Normalize dict-index or list to a list of dicts."""
        if isinstance(val, dict):
            # name-keyed index → list of values
            return [v for v in val.values() if isinstance(v, dict)]
        if isinstance(val, list):
            return val
        return []

    roles = _to_list(ark_file.get("roles")) or _collect({"role", "studio_role"})
    commands = _to_list(ark_file.get("commands")) or _collect({"command", "command_def"})
    hooks = _to_list(ark_file.get("hooks")) or _collect({"hook"})
    rules = _to_list(ark_file.get("rules")) or _collect({"rule"})
    allowed_tools = ark_file.get("allowed_tools")

    all_errors: list[str] = []
    checks: dict[str, list] = {}

    def _run_check(check_name: str, error_list: list) -> None:
        records = []
        if error_list:
            for err in error_list:
                records.append({
                    "check": check_name,
                    "status": "FAIL",
                    "detail": err,
                })
            all_errors.extend(error_list)
        else:
            records.append({
                "check": check_name,
                "status": "PASS",
                "detail": "All checks passed",
            })
        checks[check_name] = records
        # Print summary line for each check
        if error_list:
            icon = "x"
            print(f"  {icon} [{check_name}] {len(error_list)} error(s)")
            for err in error_list:
                print(f"    -> {err}")
        else:
            icon = "v"
            print(f"  {icon} [{check_name}] OK")

    print(f"\n{'='*60}")
    print("  Studio Verification")
    print(f"{'='*60}")

    _run_check("escalation_acyclicity",
               verify_escalation_acyclicity(roles))

    _run_check("command_role_resolution",
               verify_command_resolution(commands, roles))

    _run_check("hook_event_validity",
               verify_hook_events(hooks))

    _run_check("rule_constraints",
               verify_rule_constraints(rules))

    _run_check("rule_satisfiability",
               verify_rule_satisfiability(rules))

    _run_check("tool_permissions",
               verify_tool_permissions(
                   roles,
                   set(allowed_tools) if allowed_tools else None
               ))

    total = sum(len(v) for v in checks.values())
    passed = sum(1 for v in checks.values() for r in v if r["status"] == "PASS")
    failed = sum(1 for v in checks.values() for r in v if r["status"] == "FAIL")

    print(f"\n  Studio summary: {passed}/{total} passed, {failed} failed")
    print(f"{'='*60}")

    return {
        "checks": checks,
        "errors": all_errors,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
        },
    }
