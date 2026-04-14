"""
agent_codegen.py — Code generation for agent .ark artifacts.

Generates from agent .ark specs:
  - agents/{name}_config.yaml      — Agent configuration YAML
  - agents/{name}_routes.yaml      — Gateway routing table YAML
  - agents/{name}_cron.txt         — Crontab-format scheduler entries
  - skills/{name}.md               — Skill markdown (agentskills.io compatible)
  - docker-compose.agent.yaml      — Docker compose fragment for backends

Pipeline:  .ark → parse → ArkFile AST → agent_codegen → .yaml / .txt / .md
"""

import os
from pathlib import Path
from typing import Optional, Union


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(obj, key: str, default=None):
    """Get a field from either a dict or a dataclass instance."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default) or default


def _yaml_str(value) -> str:
    """Safely quote a YAML scalar string value."""
    if value is None:
        return '""'
    s = str(value)
    # Quote if contains special characters
    if any(c in s for c in (':', '#', '{', '}', '[', ']', ',', '&', '*', '?',
                             '|', '-', '<', '>', '=', '!', '%', '@', '`', '"', "'")):
        escaped = s.replace('"', '\\"')
        return f'"{escaped}"'
    return s


# ---------------------------------------------------------------------------
# gen_agent_config
# ---------------------------------------------------------------------------

def gen_agent_config(agent, model_config=None) -> str:
    """
    Generate an agent configuration YAML from an AgentDef and optional ModelConfigDef.

    Produces a YAML file with agent name, persona, model provider/id/params,
    capabilities, and learning reference.

    Args:
        agent: An AgentDef dataclass instance or dict with fields:
            name, persona, capabilities, learning_ref, description.
        model_config: Optional ModelConfigDef dataclass instance or dict with fields:
            provider, model_id, temperature, max_tokens, fallback.

    Returns:
        A string containing the YAML configuration content.
    """
    name = _get(agent, "name", "agent")
    persona = _get(agent, "persona") or f"You are the {name} agent."
    capabilities = _get(agent, "capabilities") or []
    learning_ref = _get(agent, "learning_ref") or _get(agent, "learning") or {}
    description = _get(agent, "description") or ""

    # Normalise capabilities to list of strings
    if isinstance(capabilities, str):
        capabilities = [capabilities]
    elif not isinstance(capabilities, list):
        capabilities = list(capabilities) if capabilities else []

    # Model config fields
    provider = ""
    model_id = ""
    temperature = None
    max_tokens = None
    fallback = None

    if model_config is not None:
        provider = _get(model_config, "provider") or _get(model_config, "model_provider") or ""
        model_id = _get(model_config, "model_id") or _get(model_config, "id") or ""
        temperature = _get(model_config, "temperature")
        max_tokens = _get(model_config, "max_tokens")
        fallback = _get(model_config, "fallback")
    else:
        # Inline model info on the agent itself
        provider = _get(agent, "model_provider") or _get(agent, "provider") or ""
        model_id = _get(agent, "model_id") or _get(agent, "model") or ""
        temperature = _get(agent, "temperature")
        max_tokens = _get(agent, "max_tokens")
        fallback = _get(agent, "fallback")

    # Learning config
    if isinstance(learning_ref, dict):
        learning_mode = learning_ref.get("mode") or "Passive"
        skill_generation = learning_ref.get("skill_generation", False)
        memory_persist = learning_ref.get("memory_persist", False)
    else:
        learning_mode = _get(learning_ref, "mode") or "Passive"
        skill_generation = _get(learning_ref, "skill_generation") or False
        memory_persist = _get(learning_ref, "memory_persist") or False

    lines = []
    if description:
        lines.append(f"# {description}")
        lines.append("")

    lines.append(f"name: {name}")
    lines.append(f"persona: {_yaml_str(persona)}")
    lines.append("model:")
    lines.append(f"  provider: {provider or 'Anthropic'}")
    lines.append(f"  model_id: {model_id or 'claude-sonnet-4-5'}")
    lines.append("  params:")

    if temperature is not None:
        lines.append(f"    temperature: {temperature}")
    else:
        lines.append("    temperature: 0.7")

    if max_tokens is not None:
        lines.append(f"    max_tokens: {max_tokens}")
    else:
        lines.append("    max_tokens: 4096")

    if fallback:
        lines.append(f"  fallback: {fallback}")

    if capabilities:
        caps_str = ", ".join(str(c) for c in capabilities)
        lines.append(f"capabilities: [{caps_str}]")
    else:
        lines.append("capabilities: []")

    lines.append("learning:")
    lines.append(f"  mode: {learning_mode}")
    lines.append(f"  skill_generation: {str(skill_generation).lower()}")
    lines.append(f"  memory_persist: {str(memory_persist).lower()}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# gen_gateway_routes
# ---------------------------------------------------------------------------

def gen_gateway_routes(gateway, platforms=None) -> str:
    """
    Generate a gateway routing table YAML from a GatewayDef and platform list.

    Produces a YAML file with the agent reference and a list of routes with
    platform, pattern, and priority.

    Args:
        gateway: A GatewayDef dataclass instance or dict with fields:
            name, agent_ref, routes.
        platforms: Optional list of PlatformDef dataclass instances or dicts
            with fields: name, type, format.

    Returns:
        A string containing the YAML routing table content.
    """
    name = _get(gateway, "name", "gateway")
    agent_ref = _get(gateway, "agent_ref") or _get(gateway, "agent") or name
    routes = _get(gateway, "routes") or []
    gateway_platforms = _get(gateway, "platforms") or []

    # Merge provided platforms with gateway-embedded platforms
    all_platforms = list(platforms) if platforms else []
    for gp in gateway_platforms:
        gp_name = _get(gp, "name", "")
        if not any(_get(p, "name", "") == gp_name for p in all_platforms):
            all_platforms.append(gp)

    lines = []
    lines.append(f"agent_ref: {agent_ref}")
    lines.append("")

    if all_platforms:
        lines.append("platforms:")
        for plat in all_platforms:
            plat_name = _get(plat, "name", "unknown")
            plat_type = _get(plat, "type") or _get(plat, "platform_type") or "Generic"
            plat_format = _get(plat, "format") or "text"
            lines.append(f"  - name: {plat_name}")
            lines.append(f"    type: {plat_type}")
            lines.append(f"    format: {plat_format}")
        lines.append("")

    if routes:
        lines.append("routes:")
        for route in routes:
            route_platform = _get(route, "platform") or _get(route, "platform_ref") or "default"
            route_pattern = _get(route, "pattern") or ".*"
            route_priority = _get(route, "priority") or 1
            route_format = _get(route, "format") or ""
            lines.append(f"  - platform: {route_platform}")
            lines.append(f"    pattern: {_yaml_str(route_pattern)}")
            lines.append(f"    priority: {route_priority}")
            if route_format:
                lines.append(f"    format: {route_format}")
    else:
        lines.append("routes: []")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# gen_cron_entries
# ---------------------------------------------------------------------------

def gen_cron_entries(cron_tasks) -> str:
    """
    Generate crontab-format entries from a list of CronTaskDef items.

    Each cron task becomes one crontab line preceded by a comment.
    Format: <expression> <action>  # <name> — deliver to: <deliver_to>

    Args:
        cron_tasks: An iterable of CronTaskDef dataclass instances or dicts
            with fields: name, expression, action, deliver_to, description.

    Returns:
        A string containing valid crontab-format content.
    """
    lines = []
    lines.append("# Generated crontab entries — agent scheduler")
    lines.append("# Format: <cron expression> <command>")
    lines.append("")

    for task in cron_tasks:
        task_name = _get(task, "name", "task")
        expression = _get(task, "expression") or _get(task, "cron_expression") or "0 0 * * *"
        action = _get(task, "action") or f'ark agent run --action "{task_name}"'
        deliver_to = _get(task, "deliver_to") or _get(task, "deliver") or ""
        description = _get(task, "description") or ""

        # Build comment line
        comment_parts = [task_name]
        if description:
            comment_parts.append(description)
        if deliver_to:
            comment_parts.append(f"deliver to: {deliver_to}")
        lines.append(f"# {' — '.join(comment_parts)}")

        # Build crontab entry
        cron_line = f"{expression} {action}"
        lines.append(cron_line)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# gen_skill_markdown
# ---------------------------------------------------------------------------

def gen_skill_markdown(skill) -> str:
    """
    Generate an agentskills.io-compatible markdown file from a SkillDef.

    Produces YAML frontmatter followed by structured markdown body with
    trigger pattern, steps as a numbered list, and improvement history.

    Args:
        skill: A SkillDef dataclass instance or dict with fields:
            name, trigger, status, version, steps, improvement_history, description.

    Returns:
        A string containing the complete skill markdown content.
    """
    name = _get(skill, "name", "skill")
    trigger = _get(skill, "trigger") or _get(skill, "trigger_pattern") or ""
    status = _get(skill, "status") or "draft"
    version = _get(skill, "version") or "1.0"
    steps = _get(skill, "steps") or []
    improvement_history = _get(skill, "improvement_history") or []
    description = _get(skill, "description") or ""

    # Normalise steps to list of strings
    if isinstance(steps, str):
        steps = [s.strip() for s in steps.split("\n") if s.strip()]
    elif not isinstance(steps, list):
        steps = list(steps) if steps else []

    lines = []

    # YAML frontmatter
    lines.append("---")
    lines.append(f"name: {name}")
    lines.append(f"trigger: {_yaml_str(trigger)}")
    lines.append(f"status: {status}")
    lines.append(f"version: {version}")
    lines.append("---")
    lines.append("")

    lines.append(f"# Skill: {name}")
    lines.append("")

    if description:
        lines.append(f"> {description}")
        lines.append("")

    lines.append(f"## Status: {status}")
    lines.append(f"## Version: {version}")
    lines.append("")

    lines.append("## Trigger")
    if trigger:
        lines.append(trigger)
    else:
        lines.append("<!-- Define trigger pattern -->")
    lines.append("")

    lines.append("## Steps")
    if steps:
        for i, step in enumerate(steps, 1):
            step_text = step if isinstance(step, str) else str(_get(step, "description") or step)
            lines.append(f"{i}. {step_text}")
    else:
        lines.append("<!-- Define skill steps -->")
        lines.append("1. (step 1)")
    lines.append("")

    if improvement_history:
        lines.append("## Improvement History")
        for entry in improvement_history:
            if isinstance(entry, dict):
                v = entry.get("version") or entry.get("v") or "?"
                notes = entry.get("notes") or entry.get("description") or ""
                score = entry.get("score")
                if score is not None:
                    lines.append(f"- v{v}: {notes} (score: {score})")
                else:
                    lines.append(f"- v{v}: {notes}")
            else:
                lines.append(f"- {entry}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# gen_docker_compose
# ---------------------------------------------------------------------------

def gen_docker_compose(execution_backends) -> str:
    """
    Generate a docker-compose YAML fragment from Docker execution backends.

    Only Docker-type backends are included. Each backend becomes a service
    with image, resource limits, and environment variables.

    Args:
        execution_backends: An iterable of ExecutionBackendDef dataclass
            instances or dicts with fields:
            name, backend_type (or type), image, memory_mb, cpus, environment.

    Returns:
        A string containing the docker-compose YAML fragment (services section).
    """
    # Filter to Docker-type backends only
    docker_backends = []
    for backend in execution_backends:
        btype = (
            _get(backend, "backend_type")
            or _get(backend, "type")
            or _get(backend, "kind")
            or ""
        )
        if str(btype).lower() in ("docker", "container", "docker_container"):
            docker_backends.append(backend)
        elif not btype:
            # Include if no type specified (assume Docker)
            image = _get(backend, "image") or ""
            if image:
                docker_backends.append(backend)

    lines = []
    lines.append("version: '3.8'")
    lines.append("")
    lines.append("services:")

    if docker_backends:
        for backend in docker_backends:
            svc_name = _get(backend, "name", "agent_service")
            image = _get(backend, "image") or "ubuntu:22.04"
            memory_mb = _get(backend, "memory_mb") or _get(backend, "memory") or 2048
            cpus = _get(backend, "cpus") or _get(backend, "cpu") or 2.0
            environment = _get(backend, "environment") or {}
            volumes = _get(backend, "volumes") or []

            lines.append(f"  {svc_name}:")
            lines.append(f"    image: {image}")
            lines.append("    deploy:")
            lines.append("      resources:")
            lines.append("        limits:")
            lines.append(f"          memory: {memory_mb}M")
            lines.append(f"          cpus: '{float(cpus):.1f}'")

            if environment:
                lines.append("    environment:")
                if isinstance(environment, dict):
                    for k, v in environment.items():
                        lines.append(f"      {k}: {_yaml_str(str(v))}")
                elif isinstance(environment, list):
                    for env_entry in environment:
                        if isinstance(env_entry, dict):
                            for k, v in env_entry.items():
                                lines.append(f"      {k}: {_yaml_str(str(v))}")
                        else:
                            lines.append(f"      - {env_entry}")

            if volumes:
                lines.append("    volumes:")
                for vol in volumes:
                    vol_str = vol if isinstance(vol, str) else str(vol)
                    lines.append(f"      - {vol_str}")
            else:
                lines.append("    volumes:")
                lines.append("      - ./workspace:/workspace")

    else:
        lines.append("  # No Docker backends defined")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# generate — main orchestrator
# ---------------------------------------------------------------------------

def generate(ark_file, output_dir: Optional[Union[str, Path]] = None) -> dict:
    """
    Generate all agent artifacts from a parsed ArkFile or JSON dict.

    Produces:
      - agents/{agent_name}_config.yaml     for each AgentDef
      - agents/{gateway_name}_routes.yaml   for each GatewayDef
      - agents/{agent_name}_cron.txt        grouping all CronTaskDef items
      - skills/{skill_name}.md              for each SkillDef
      - docker-compose.agent.yaml           for all Docker ExecutionBackendDef items

    Args:
        ark_file: A parsed ArkFile instance or JSON AST dict.
            When a dict, uses the "items" list with kind-tagged entries.
            When an ArkFile, uses index dicts: .agents, .gateways,
            .cron_tasks, .skills, .execution_backends.
        output_dir: Optional path. If provided, files are written to disk.

    Returns:
        dict mapping relative filename (str) → file content (str).
    """
    artifacts = {}

    agents = []
    model_configs = {}
    gateways = []
    cron_tasks = []
    skills = []
    execution_backends = []

    if isinstance(ark_file, dict):
        # JSON AST path — iterate items list
        for item in ark_file.get("items", []):
            kind = item.get("kind", "")
            if kind in ("agent", "agent_def"):
                agents.append(item)
            elif kind in ("model_config", "model_configuration"):
                mc_name = item.get("name", "")
                model_configs[mc_name] = item
            elif kind in ("gateway", "gateway_def"):
                gateways.append(item)
            elif kind in ("cron_task", "cron", "scheduler_task"):
                cron_tasks.append(item)
            elif kind in ("skill", "skill_def"):
                skills.append(item)
            elif kind in ("execution_backend", "backend"):
                execution_backends.append(item)
    else:
        # ArkFile dataclass path — use pre-built indices
        for a in getattr(ark_file, "agents", {}).values():
            agents.append(a)
        for mc in getattr(ark_file, "model_configs", {}).values():
            mc_name = getattr(mc, "name", "") if not isinstance(mc, dict) else mc.get("name", "")
            model_configs[mc_name] = mc
        for g in getattr(ark_file, "gateways", {}).values():
            gateways.append(g)
        for ct in getattr(ark_file, "cron_tasks", {}).values():
            cron_tasks.append(ct)
        for s in getattr(ark_file, "skills", {}).values():
            skills.append(s)
        for eb in getattr(ark_file, "execution_backends", {}).values():
            execution_backends.append(eb)

        # Also scan items list in case indices are incomplete
        for item in getattr(ark_file, "items", []):
            item_kind = type(item).__name__.lower()
            item_name = getattr(item, "name", None)

            if "agentdef" in item_kind or item_kind == "agentdef":
                if not any((getattr(a, "name", None) or a.get("name")) == item_name
                           for a in agents if item_name):
                    agents.append(item)
            elif "modelconfig" in item_kind:
                if item_name and item_name not in model_configs:
                    model_configs[item_name] = item
            elif "gatewaydef" in item_kind or item_kind == "gatewaydef":
                if not any((getattr(g, "name", None) or g.get("name")) == item_name
                           for g in gateways if item_name):
                    gateways.append(item)
            elif "crontask" in item_kind or "schedulertask" in item_kind:
                if not any((getattr(c, "name", None) or c.get("name")) == item_name
                           for c in cron_tasks if item_name):
                    cron_tasks.append(item)
            elif "skilldef" in item_kind or item_kind == "skilldef":
                if not any((getattr(s, "name", None) or s.get("name")) == item_name
                           for s in skills if item_name):
                    skills.append(item)
            elif "executionbackend" in item_kind:
                if not any((getattr(e, "name", None) or e.get("name")) == item_name
                           for e in execution_backends if item_name):
                    execution_backends.append(item)

    # Generate agent config YAML files
    for agent in agents:
        a_name = _get(agent, "name", "agent")
        # Find matching model config via agent's model_config_ref
        model_ref = _get(agent, "model_config_ref") or _get(agent, "model_ref") or ""
        mc = model_configs.get(model_ref)
        filename = f"agents/{a_name}_config.yaml"
        artifacts[filename] = gen_agent_config(agent, mc)

    # Generate gateway routing YAML files
    for gateway in gateways:
        g_name = _get(gateway, "name", "gateway")
        filename = f"agents/{g_name}_routes.yaml"
        artifacts[filename] = gen_gateway_routes(gateway)

    # Generate cron entries (one file grouping all tasks)
    if cron_tasks:
        artifacts["agents/agent_cron.txt"] = gen_cron_entries(cron_tasks)

    # Generate skill markdown files
    for skill in skills:
        s_name = _get(skill, "name", "skill")
        filename = f"skills/{s_name}.md"
        artifacts[filename] = gen_skill_markdown(skill)

    # Generate docker-compose fragment
    if execution_backends:
        artifacts["docker-compose.agent.yaml"] = gen_docker_compose(execution_backends)

    # Write to disk if output_dir is provided
    if output_dir is not None:
        out = Path(output_dir)
        for rel_path, content in artifacts.items():
            full_path = out / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")

    return artifacts


# ---------------------------------------------------------------------------
# Inline smoke-test
# ---------------------------------------------------------------------------

def _smoke_test():
    """Quick self-test using mock dataclass instances (no parser needed)."""
    import json as _json
    from dataclasses import dataclass, field as dc_field
    from typing import Optional as Opt, List

    @dataclass
    class MockAgent:
        kind: str = "agent"
        name: str = "ResearchBot"
        persona: Opt[str] = "You are a meticulous research assistant."
        capabilities: List[str] = dc_field(default_factory=lambda: ["search", "code_execution", "file_ops"])
        learning_ref: dict = dc_field(default_factory=lambda: {
            "mode": "Active",
            "skill_generation": True,
            "memory_persist": True,
        })
        model_config_ref: Opt[str] = "GptModelCfg"
        description: Opt[str] = "Research agent"

    @dataclass
    class MockModelConfig:
        kind: str = "model_config"
        name: str = "GptModelCfg"
        provider: str = "Anthropic"
        model_id: str = "claude-opus-4-5"
        temperature: float = 0.7
        max_tokens: int = 4096
        fallback: Opt[str] = "claude-sonnet-4-5"

    @dataclass
    class MockRoute:
        platform: str = "terminal"
        pattern: str = ".*"
        priority: int = 1
        format: str = "text"

    @dataclass
    class MockPlatform:
        name: str = "terminal"
        type: str = "Terminal"
        format: str = "text"

    @dataclass
    class MockGateway:
        kind: str = "gateway"
        name: str = "MainGateway"
        agent_ref: str = "ResearchBot"
        routes: List = dc_field(default_factory=lambda: [
            {"platform": "terminal", "pattern": ".*", "priority": 1, "format": "text"},
            {"platform": "telegram", "pattern": r"^/", "priority": 2, "format": "markdown"},
        ])
        platforms: List = dc_field(default_factory=list)

    @dataclass
    class MockCronTask:
        kind: str = "cron_task"
        name: str = "DailyReport"
        expression: str = "0 9 * * *"
        action: str = 'ark agent run ResearchBot --action "Generate daily report"'
        deliver_to: Opt[str] = "telegram"
        description: Opt[str] = "Daily research summary"

    @dataclass
    class MockSkill:
        kind: str = "skill"
        name: str = "WebSearch"
        trigger: str = "user mentions searching or finding information"
        status: str = "active"
        version: str = "1.2"
        steps: List[str] = dc_field(default_factory=lambda: [
            "Parse the user query",
            "Execute web search",
            "Summarize top results",
            "Return formatted answer",
        ])
        improvement_history: List[dict] = dc_field(default_factory=lambda: [
            {"version": "1.0", "notes": "Initial version", "score": 0.72},
            {"version": "1.2", "notes": "Improved summarization", "score": 0.88},
        ])
        description: Opt[str] = "Web search skill"

    @dataclass
    class MockBackend:
        kind: str = "execution_backend"
        name: str = "agent_sandbox"
        backend_type: str = "docker"
        image: str = "ubuntu:22.04"
        memory_mb: int = 2048
        cpus: float = 2.0
        environment: dict = dc_field(default_factory=lambda: {"AGENT_MODE": "production"})
        volumes: List[str] = dc_field(default_factory=lambda: ["./workspace:/workspace"])

    # --- gen_agent_config ---
    agent = MockAgent()
    mc = MockModelConfig()
    config_yaml = gen_agent_config(agent, mc)
    assert "name: ResearchBot" in config_yaml, f"Missing agent name in: {config_yaml}"
    assert "provider: Anthropic" in config_yaml, f"Missing provider in: {config_yaml}"
    assert "model_id: claude-opus-4-5" in config_yaml, f"Missing model_id in: {config_yaml}"
    assert "temperature: 0.7" in config_yaml, f"Missing temperature in: {config_yaml}"
    assert "max_tokens: 4096" in config_yaml, f"Missing max_tokens in: {config_yaml}"
    assert "fallback: claude-sonnet-4-5" in config_yaml, f"Missing fallback in: {config_yaml}"
    assert "capabilities: [search, code_execution, file_ops]" in config_yaml, f"Missing caps in: {config_yaml}"
    assert "mode: Active" in config_yaml, f"Missing learning mode in: {config_yaml}"
    assert "skill_generation: true" in config_yaml, f"Missing skill_gen in: {config_yaml}"
    assert "memory_persist: true" in config_yaml, f"Missing memory_persist in: {config_yaml}"
    print("gen_agent_config: PASS")

    # --- gen_gateway_routes ---
    gateway = MockGateway()
    platforms = [{"name": "telegram", "type": "Telegram", "format": "markdown"}]
    routes_yaml = gen_gateway_routes(gateway, platforms)
    assert "agent_ref: ResearchBot" in routes_yaml, f"Missing agent_ref in: {routes_yaml}"
    assert "platform: terminal" in routes_yaml, f"Missing terminal route in: {routes_yaml}"
    assert "platform: telegram" in routes_yaml, f"Missing telegram route in: {routes_yaml}"
    assert "priority: 1" in routes_yaml, f"Missing priority in: {routes_yaml}"
    print("gen_gateway_routes: PASS")

    # --- gen_cron_entries ---
    cron_task = MockCronTask()
    cron_txt = gen_cron_entries([cron_task])
    assert "0 9 * * *" in cron_txt, f"Missing expression in: {cron_txt}"
    assert "DailyReport" in cron_txt, f"Missing task name in: {cron_txt}"
    assert "ark agent run" in cron_txt, f"Missing action in: {cron_txt}"
    assert "deliver to: telegram" in cron_txt, f"Missing deliver_to in: {cron_txt}"
    lines = [l for l in cron_txt.split("\n") if l.strip() and not l.startswith("#")]
    assert len(lines) == 1, f"Expected 1 cron line, got {len(lines)}: {lines}"
    print("gen_cron_entries: PASS")

    # --- gen_skill_markdown ---
    skill = MockSkill()
    skill_md = gen_skill_markdown(skill)
    assert "---" in skill_md, f"Missing frontmatter in: {skill_md}"
    assert "name: WebSearch" in skill_md, f"Missing name in: {skill_md}"
    assert "trigger:" in skill_md, f"Missing trigger in: {skill_md}"
    assert "status: active" in skill_md, f"Missing status in: {skill_md}"
    assert "# Skill: WebSearch" in skill_md, f"Missing heading in: {skill_md}"
    assert "## Steps" in skill_md, f"Missing steps section in: {skill_md}"
    assert "1. Parse the user query" in skill_md, f"Missing step 1 in: {skill_md}"
    assert "4. Return formatted answer" in skill_md, f"Missing step 4 in: {skill_md}"
    assert "## Improvement History" in skill_md, f"Missing history in: {skill_md}"
    assert "score: 0.72" in skill_md, f"Missing score in: {skill_md}"
    assert "score: 0.88" in skill_md, f"Missing score in: {skill_md}"
    print("gen_skill_markdown: PASS")

    # --- gen_docker_compose ---
    backend = MockBackend()
    compose_yaml = gen_docker_compose([backend])
    assert "version: '3.8'" in compose_yaml, f"Missing version in: {compose_yaml}"
    assert "services:" in compose_yaml, f"Missing services in: {compose_yaml}"
    assert "agent_sandbox:" in compose_yaml, f"Missing service name in: {compose_yaml}"
    assert "image: ubuntu:22.04" in compose_yaml, f"Missing image in: {compose_yaml}"
    assert "memory: 2048M" in compose_yaml, f"Missing memory in: {compose_yaml}"
    assert "cpus: '2.0'" in compose_yaml, f"Missing cpus in: {compose_yaml}"
    assert "AGENT_MODE" in compose_yaml, f"Missing env in: {compose_yaml}"
    print("gen_docker_compose: PASS")

    # --- generate (orchestrator with dict input) ---
    ast_json = {
        "items": [
            {
                "kind": "agent",
                "name": "TestAgent",
                "persona": "You are a test agent.",
                "capabilities": ["search"],
                "learning_ref": {"mode": "Passive", "skill_generation": False, "memory_persist": False},
                "model_config_ref": "TestModel",
                "description": "",
            },
            {
                "kind": "model_config",
                "name": "TestModel",
                "provider": "Anthropic",
                "model_id": "claude-sonnet-4-5",
                "temperature": 0.5,
                "max_tokens": 2048,
                "fallback": None,
            },
            {
                "kind": "gateway",
                "name": "TestGateway",
                "agent_ref": "TestAgent",
                "routes": [{"platform": "terminal", "pattern": ".*", "priority": 1}],
                "platforms": [{"name": "terminal", "type": "Terminal", "format": "text"}],
            },
            {
                "kind": "cron_task",
                "name": "TestTask",
                "expression": "0 0 * * 0",
                "action": "ark agent run TestAgent",
                "deliver_to": "email",
                "description": "",
            },
            {
                "kind": "skill",
                "name": "TestSkill",
                "trigger": "user asks for help",
                "status": "draft",
                "version": "0.1",
                "steps": ["Step 1", "Step 2"],
                "improvement_history": [],
                "description": "",
            },
            {
                "kind": "execution_backend",
                "name": "test_backend",
                "backend_type": "docker",
                "image": "alpine:latest",
                "memory_mb": 512,
                "cpus": 1.0,
                "environment": {},
                "volumes": [],
            },
        ]
    }

    result = generate(ast_json)
    assert "agents/TestAgent_config.yaml" in result, f"Missing agent config. Keys: {list(result.keys())}"
    assert "agents/TestGateway_routes.yaml" in result, f"Missing gateway routes. Keys: {list(result.keys())}"
    assert "agents/agent_cron.txt" in result, f"Missing cron. Keys: {list(result.keys())}"
    assert "skills/TestSkill.md" in result, f"Missing skill. Keys: {list(result.keys())}"
    assert "docker-compose.agent.yaml" in result, f"Missing docker-compose. Keys: {list(result.keys())}"

    # Validate config content
    cfg = result["agents/TestAgent_config.yaml"]
    assert "name: TestAgent" in cfg
    assert "provider: Anthropic" in cfg
    assert "model_id: claude-sonnet-4-5" in cfg

    # Validate cron content
    cron = result["agents/agent_cron.txt"]
    assert "0 0 * * 0" in cron
    assert "TestTask" in cron

    print("generate (dict AST): PASS")
    print("\nAll smoke tests passed.")


if __name__ == "__main__":
    _smoke_test()
