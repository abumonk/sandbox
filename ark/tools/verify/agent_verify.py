"""
Agent Verifier
Checks agent-specific invariants in ARK agent specs using Z3.

Checks:
  1. Gateway references      — each gateway's agent_ref exists in agents dict;
                               each platform listed in gateway exists in platforms dict
  2. Cron references         — each cron_task's agent_ref and platform_delivery exist
  3. Model fallback acyclicity — uses Z3 Int ordinals to detect cycles in fallback chains
  4. Resource limits          — uses Z3 to check cpu_cores > 0, memory_mb > 0,
                               timeout_seconds > 0
  5. Skill trigger overlap    — warns when two active skills share a trigger pattern
                               with overlapping priorities
  6. Agent completeness       — each agent's model_ref exists in model_configs;
                               backend refs exist in execution_backends
"""

from z3 import Int, And, Solver, sat, unsat, IntVal

# ============================================================
# RESULT HELPERS
# ============================================================


def _pass(check: str, message: str) -> dict:
    return {"check": check, "status": "pass", "message": message}


def _fail(check: str, message: str) -> dict:
    return {"check": check, "status": "fail", "message": message}


def _warn(check: str, message: str) -> dict:
    return {"check": check, "status": "warn", "message": message}


# ============================================================
# HELPERS
# ============================================================

def _items_from_ark(ark_file: dict) -> list:
    """Extract the flat items list from an ARK AST dict."""
    raw = ark_file.get("items", [])
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return list(raw.values())
    return []


def _collect(items: list, kind: str) -> list:
    """Return all items whose 'kind' matches the given kind string."""
    return [it for it in items if isinstance(it, dict) and it.get("kind") == kind]


def _name(item: dict, fallback: str = "<unnamed>") -> str:
    return item.get("name") or item.get("id") or fallback


def _to_list(val) -> list:
    """Normalise dict-index or list to a list of dicts."""
    if isinstance(val, dict):
        return [v for v in val.values() if isinstance(v, dict)]
    if isinstance(val, list):
        return val
    return []


# ============================================================
# CHECK 1: Gateway References
# ============================================================

def verify_gateway_references(gateways: list, agents: dict, platforms: dict) -> list:
    """Check that each gateway's agent_ref exists in agents and each platform
    listed in the gateway exists in the platforms dict.

    Args:
        gateways:  list of gateway dicts (each may have 'agent_ref' and
                   'platforms' or 'platform_list' keys)
        agents:    dict mapping agent name → agent dict
        platforms: dict mapping platform name → platform dict

    Returns a list of result dicts.
    """
    results = []

    for gw in gateways:
        gw_name = _name(gw)

        # Check agent_ref
        agent_ref = gw.get("agent_ref") or gw.get("agent")
        if agent_ref is None:
            results.append(_warn(
                "agent_gateway_refs",
                f"Gateway '{gw_name}' has no agent_ref — skipping agent check"
            ))
        elif agent_ref not in agents:
            results.append(_fail(
                "agent_gateway_refs",
                f"Gateway '{gw_name}' references unknown agent '{agent_ref}'"
            ))
        else:
            results.append(_pass(
                "agent_gateway_refs",
                f"Gateway '{gw_name}' agent_ref '{agent_ref}' resolved"
            ))

        # Check platform references
        platform_refs = (
            gw.get("platforms")
            or gw.get("platform_list")
            or gw.get("platform_refs")
            or []
        )
        if isinstance(platform_refs, str):
            platform_refs = [platform_refs]

        for pref in platform_refs:
            pref_name = pref if isinstance(pref, str) else _name(pref)
            if pref_name not in platforms:
                results.append(_fail(
                    "agent_gateway_refs",
                    f"Gateway '{gw_name}' references unknown platform '{pref_name}'"
                ))
            else:
                results.append(_pass(
                    "agent_gateway_refs",
                    f"Gateway '{gw_name}' platform '{pref_name}' resolved"
                ))

    return results


# ============================================================
# CHECK 2: Cron References
# ============================================================

def verify_cron_references(cron_tasks: list, agents: dict, platforms: dict) -> list:
    """Check that each cron_task's agent_ref exists in agents and its
    platform_delivery exists in platforms.

    Args:
        cron_tasks: list of cron task dicts
        agents:     dict mapping agent name → agent dict
        platforms:  dict mapping platform name → platform dict

    Returns a list of result dicts.
    """
    results = []

    for task in cron_tasks:
        task_name = _name(task)

        # Check agent_ref
        agent_ref = task.get("agent_ref") or task.get("agent")
        if agent_ref is None:
            results.append(_warn(
                "agent_cron_refs",
                f"Cron task '{task_name}' has no agent_ref — skipping"
            ))
        elif agent_ref not in agents:
            results.append(_fail(
                "agent_cron_refs",
                f"Cron task '{task_name}' references unknown agent '{agent_ref}'"
            ))
        else:
            results.append(_pass(
                "agent_cron_refs",
                f"Cron task '{task_name}' agent_ref '{agent_ref}' resolved"
            ))

        # Check platform_delivery
        platform_delivery = (
            task.get("platform_delivery")
            or task.get("platform")
            or task.get("delivery_platform")
        )
        if platform_delivery is None:
            results.append(_warn(
                "agent_cron_refs",
                f"Cron task '{task_name}' has no platform_delivery — skipping"
            ))
        elif platform_delivery not in platforms:
            results.append(_fail(
                "agent_cron_refs",
                f"Cron task '{task_name}' references unknown platform '{platform_delivery}'"
            ))
        else:
            results.append(_pass(
                "agent_cron_refs",
                f"Cron task '{task_name}' platform_delivery '{platform_delivery}' resolved"
            ))

    return results


# ============================================================
# CHECK 3: Model Fallback Acyclicity
# ============================================================

def verify_model_fallback_acyclicity(model_configs: dict) -> list:
    """Detect cycles in model fallback chains using Z3 Int ordinals.

    For each model config that declares a 'fallback' (or 'fallback_model'),
    we assert that the fallback target's ordinal is strictly greater than the
    current model's ordinal.  If the resulting constraint system is UNSAT,
    a cycle exists (e.g. A → B → A would require ord_A < ord_B < ord_A).

    Args:
        model_configs: dict mapping model name → model config dict.
                       Each config may have a 'fallback' or 'fallback_model' key.

    Returns a list of result dicts.
    """
    results = []

    if not model_configs:
        return results

    # Build fallback edges: list of (src_name, dst_name)
    fallback_edges: list[tuple[str, str]] = []
    unknown_refs: list[tuple[str, str]] = []

    for model_name, cfg in model_configs.items():
        if not isinstance(cfg, dict):
            continue
        fallback = cfg.get("fallback") or cfg.get("fallback_model")
        if fallback is None:
            continue
        if fallback not in model_configs:
            unknown_refs.append((model_name, fallback))
        else:
            fallback_edges.append((model_name, fallback))

    # Report unresolved fallback refs
    for (src, dst) in unknown_refs:
        results.append(_fail(
            "agent_model_fallback_acyclicity",
            f"Model '{src}' fallback references unknown model '{dst}'"
        ))

    if not fallback_edges:
        # Nothing to check for cycles
        if not unknown_refs:
            results.append(_pass(
                "agent_model_fallback_acyclicity",
                "No model fallback chains defined — nothing to check"
            ))
        return results

    # Z3 acyclicity check via ordinal assignment.
    # Create one Int variable per model, assert ord[src] < ord[dst] for each edge.
    # SAT → acyclic;  UNSAT → cycle exists.
    ord_vars = {name: Int(f"model_ord_{name}") for name in model_configs}
    s = Solver()
    for v in ord_vars.values():
        s.add(v >= IntVal(0))
    for (src, dst) in fallback_edges:
        s.add(ord_vars[src] < ord_vars[dst])

    result = s.check()
    if result == unsat:
        # Identify cycle members via DFS
        cycle_members = _find_cycle_nodes(fallback_edges, set(model_configs.keys()))
        if cycle_members:
            results.append(_fail(
                "agent_model_fallback_acyclicity",
                f"Fallback cycle detected among models: {', '.join(sorted(cycle_members))}"
            ))
        else:
            results.append(_fail(
                "agent_model_fallback_acyclicity",
                "Fallback cycle detected (unable to identify specific models)"
            ))
    elif result == sat:
        results.append(_pass(
            "agent_model_fallback_acyclicity",
            f"Model fallback chains are acyclic ({len(fallback_edges)} edge(s) checked)"
        ))
    else:
        results.append(_warn(
            "agent_model_fallback_acyclicity",
            "Z3 returned UNKNOWN for model fallback acyclicity check"
        ))

    return results


def _find_cycle_nodes(edges: list[tuple[str, str]], all_names: set) -> set:
    """DFS-based cycle detection; returns all node names that are part of a cycle."""
    adj: dict[str, list[str]] = {n: [] for n in all_names}
    for src, dst in edges:
        if src in adj:
            adj[src].append(dst)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in all_names}
    cycle_nodes: set = set()

    def dfs(node: str, path: list) -> bool:
        color[node] = GRAY
        path.append(node)
        for nbr in adj.get(node, []):
            if color[nbr] == GRAY:
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
# CHECK 4: Resource Limits
# ============================================================

def verify_resource_limits(execution_backends: dict) -> list:
    """Use Z3 to verify that each execution backend's resource limits are positive.

    Checks per backend:
      - cpu_cores > 0
      - memory_mb > 0
      - timeout_seconds > 0

    Args:
        execution_backends: dict mapping backend name → backend config dict.

    Returns a list of result dicts.
    """
    results = []

    RESOURCE_FIELDS = ("cpu_cores", "memory_mb", "timeout_seconds")

    for backend_name, cfg in execution_backends.items():
        if not isinstance(cfg, dict):
            continue

        backend_ok = True

        for field in RESOURCE_FIELDS:
            raw_val = cfg.get(field)
            if raw_val is None:
                results.append(_warn(
                    "agent_resource_limits",
                    f"Backend '{backend_name}' missing '{field}' — skipping bound check"
                ))
                continue

            try:
                int_val = int(raw_val)
            except (TypeError, ValueError):
                results.append(_warn(
                    "agent_resource_limits",
                    f"Backend '{backend_name}' non-integer {field}='{raw_val}'"
                ))
                backend_ok = False
                continue

            # Z3 check: field > 0
            z_var = Int(field)
            s = Solver()
            s.add(z_var == IntVal(int_val))
            s.add(z_var > IntVal(0))

            res = s.check()
            if res == unsat:
                results.append(_fail(
                    "agent_resource_limits",
                    f"Backend '{backend_name}' has invalid {field}: {int_val} (must be > 0)"
                ))
                backend_ok = False
            elif res != sat:
                results.append(_warn(
                    "agent_resource_limits",
                    f"Backend '{backend_name}' Z3 returned UNKNOWN for {field} check"
                ))
                backend_ok = False

        if backend_ok:
            results.append(_pass(
                "agent_resource_limits",
                f"Backend '{backend_name}' resource limits are valid"
            ))

    return results


# ============================================================
# CHECK 5: Skill Trigger Overlap
# ============================================================

def verify_skill_trigger_overlap(agent_skills: list) -> list:
    """Warn when two active skills share the same trigger pattern and have
    overlapping (equal) priorities, since ambiguous dispatch order may occur.

    A skill is considered "active" if it has no 'enabled' key (default active)
    or its 'enabled' field is True / "true".

    Args:
        agent_skills: list of skill dicts, each with optional fields:
                      'trigger' or 'trigger_pattern', 'priority' (int),
                      'enabled' (bool/str, default True).

    Returns a list of result dicts (warn on overlap, pass if no overlap found).
    """
    results = []

    def _is_active(skill: dict) -> bool:
        enabled = skill.get("enabled")
        if enabled is None:
            return True
        if isinstance(enabled, bool):
            return enabled
        return str(enabled).lower() not in ("false", "0", "no", "off")

    # Group active skills by trigger pattern
    trigger_map: dict[str, list[dict]] = {}
    for skill in agent_skills:
        if not _is_active(skill):
            continue
        trigger = skill.get("trigger") or skill.get("trigger_pattern") or ""
        if not trigger:
            continue
        trigger_map.setdefault(trigger, []).append(skill)

    overlap_found = False
    for trigger, skills in trigger_map.items():
        if len(skills) < 2:
            continue
        # Check for same-priority pairs
        priority_groups: dict = {}
        for skill in skills:
            prio = skill.get("priority")
            if prio is None:
                prio = "__unset__"
            priority_groups.setdefault(prio, []).append(_name(skill))

        for prio, names in priority_groups.items():
            if len(names) >= 2:
                prio_label = str(prio) if prio != "__unset__" else "unset"
                results.append(_warn(
                    "agent_skill_trigger_overlap",
                    f"Skills {names} share trigger '{trigger}' with priority={prio_label} "
                    f"— dispatch order is ambiguous"
                ))
                overlap_found = True

    if not overlap_found:
        results.append(_pass(
            "agent_skill_trigger_overlap",
            "No ambiguous skill trigger overlaps found"
        ))

    return results


# ============================================================
# CHECK 6: Agent Completeness
# ============================================================

def verify_agent_completeness(agents: dict,
                              model_configs: dict,
                              execution_backends: dict) -> list:
    """Check that each agent's model_ref and backend_ref resolve to known entries.

    For each agent:
      - 'model_ref' or 'model' must exist as a key in model_configs
      - 'backend_ref' or 'execution_backend' or 'backend' must exist in
        execution_backends (if specified)

    Args:
        agents:              dict mapping agent name → agent dict
        model_configs:       dict mapping model name → model config dict
        execution_backends:  dict mapping backend name → backend config dict

    Returns a list of result dicts.
    """
    results = []

    for agent_name, agent in agents.items():
        if not isinstance(agent, dict):
            continue

        agent_ok = True

        # Check model_ref
        model_ref = agent.get("model_ref") or agent.get("model")
        if model_ref is None:
            results.append(_warn(
                "agent_completeness",
                f"Agent '{agent_name}' has no model_ref — skipping model check"
            ))
        elif model_ref not in model_configs:
            results.append(_fail(
                "agent_completeness",
                f"Agent '{agent_name}' references unknown model '{model_ref}'"
            ))
            agent_ok = False
        else:
            results.append(_pass(
                "agent_completeness",
                f"Agent '{agent_name}' model_ref '{model_ref}' resolved"
            ))

        # Check backend_ref (optional field — only fail if present and unresolved)
        backend_ref = (
            agent.get("backend_ref")
            or agent.get("execution_backend")
            or agent.get("backend")
        )
        if backend_ref is not None:
            if backend_ref not in execution_backends:
                results.append(_fail(
                    "agent_completeness",
                    f"Agent '{agent_name}' references unknown backend '{backend_ref}'"
                ))
                agent_ok = False
            else:
                results.append(_pass(
                    "agent_completeness",
                    f"Agent '{agent_name}' backend_ref '{backend_ref}' resolved"
                ))

    return results


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def verify_agent(ark_file: dict) -> list:
    """Run all agent verification checks on a parsed ARK AST dict.

    Expected structure of ark_file (all keys optional):
      - agents:              dict or list of agent dicts (kind='agent')
      - model_configs:       dict or list of model config dicts (kind='model_config')
      - execution_backends:  dict or list of backend dicts (kind='execution_backend')
      - gateways:            list of gateway dicts (kind='gateway')
      - cron_tasks:          list of cron task dicts (kind='cron_task')
      - agent_skills:        list of skill dicts (kind='agent_skill')
      - items:               flat list of all items (used as fallback)

    Returns a flat list of result dicts, each with keys:
      - check:   str — check identifier
      - status:  "pass" | "fail" | "warn"
      - message: str — human-readable detail
    """
    items = _items_from_ark(ark_file)

    def _collect_kind(kind: str) -> list:
        return _collect(items, kind)

    def _to_dict_by_name(source) -> dict:
        """Convert list or dict to a name-keyed dict."""
        if isinstance(source, dict):
            return source
        if isinstance(source, list):
            out = {}
            for item in source:
                if isinstance(item, dict):
                    key = _name(item)
                    out[key] = item
            return out
        return {}

    # Collect agents
    agents_raw = (
        ark_file.get("agents")
        or _collect_kind("agent")
    )
    agents = _to_dict_by_name(agents_raw)

    # Collect model configs
    model_configs_raw = (
        ark_file.get("model_configs")
        or _collect_kind("model_config")
    )
    model_configs = _to_dict_by_name(model_configs_raw)

    # Collect execution backends
    backends_raw = (
        ark_file.get("execution_backends")
        or _collect_kind("execution_backend")
    )
    execution_backends = _to_dict_by_name(backends_raw)

    # Collect platforms
    platforms_raw = (
        ark_file.get("platforms")
        or _collect_kind("platform")
    )
    platforms = _to_dict_by_name(platforms_raw)

    # Collect gateways
    gateways = (
        _to_list(ark_file.get("gateways"))
        or _collect_kind("gateway")
    )

    # Collect cron tasks
    cron_tasks = (
        _to_list(ark_file.get("cron_tasks"))
        or _collect_kind("cron_task")
    )

    # Collect agent skills
    agent_skills = (
        _to_list(ark_file.get("agent_skills"))
        or _collect_kind("agent_skill")
    )

    print(f"\n{'='*60}")
    print("  Agent Verification")
    print(f"{'='*60}")

    results: list = []

    def _run_check(label: str, check_results: list) -> None:
        results.extend(check_results)
        fails = [r for r in check_results if r["status"] == "fail"]
        warns = [r for r in check_results if r["status"] == "warn"]
        if fails:
            print(f"  x [{label}] {len(fails)} failure(s)")
            for r in fails:
                print(f"    -> {r['message']}")
        elif warns:
            print(f"  ? [{label}] {len(warns)} warning(s)")
            for r in warns:
                print(f"    -> {r['message']}")
        elif check_results:
            print(f"  v [{label}] {len(check_results)} item(s) OK")
        else:
            print(f"  - [{label}] no items to check")

    _run_check("gateway_refs",
               verify_gateway_references(gateways, agents, platforms))

    _run_check("cron_refs",
               verify_cron_references(cron_tasks, agents, platforms))

    _run_check("model_fallback_acyclicity",
               verify_model_fallback_acyclicity(model_configs))

    _run_check("resource_limits",
               verify_resource_limits(execution_backends))

    _run_check("skill_trigger_overlap",
               verify_skill_trigger_overlap(agent_skills))

    _run_check("agent_completeness",
               verify_agent_completeness(agents, model_configs, execution_backends))

    total  = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    warned = sum(1 for r in results if r["status"] == "warn")

    print(f"\n  Agent summary: {passed}/{total} passed, {failed} failed, {warned} warnings")
    print(f"{'='*60}")

    return results
