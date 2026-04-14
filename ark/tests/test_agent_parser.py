"""Tests for Lark grammar agent section and resulting AST dataclasses.

Covers TC-003, TC-005, TC-006, TC-007.
"""

import sys
import pathlib
import json

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "parser"))

from ark_parser import parse as _ark_parse, to_json as _ark_to_json  # noqa: E402
from ark_parser import (  # noqa: E402
    AgentDef, PlatformDef, GatewayDef, ExecutionBackendDef,
    AgentSkillDef, LearningConfigDef, CronTaskDef, ModelConfigDef,
    ArkFile,
)


# ---------------------------------------------------------------------------
# Minimal snippets for each item kind
# ---------------------------------------------------------------------------

_PLATFORM_SNIPPET = """\
platform my_terminal {
    type: terminal
    format: text
}
"""

_GATEWAY_SNIPPET = """\
platform gw_terminal {
    type: terminal
}
gateway my_gateway {
    agent: my_agent
    platforms: [gw_terminal]
    routes: [gw_terminal -> my_agent]
}
"""

_EXECUTION_BACKEND_SNIPPET = """\
execution_backend my_backend {
    backend_type: local
    connection: "unix:///tmp/test.sock"
}
"""

_MODEL_CONFIG_SNIPPET = """\
model_config my_model {
    provider: anthropic
    model_id: "claude-sonnet-4-6"
}
"""

_SKILL_SNIPPET = """\
skill my_skill {
    trigger: "search|find"
    steps: ["step1", "step2"]
    status: active
}
"""

_LEARNING_CONFIG_SNIPPET = """\
learning_config my_learning {
    mode: passive
    skill_generation: false
    memory_persist: false
}
"""

_CRON_TASK_SNIPPET = """\
cron_task my_task {
    schedule: "0 9 * * *"
    agent: my_agent
    deliver_to: terminal
}
"""

_AGENT_SNIPPET = """\
model_config agent_model {
    provider: anthropic
    model_id: "claude-sonnet-4-6"
}
learning_config agent_learning {
    mode: passive
}
platform agent_terminal {
    type: terminal
}
execution_backend agent_backend {
    backend_type: local
}
agent my_agent {
    persona: "Test agent"
    model: agent_model
    capabilities: [search]
    learning: agent_learning
    backends: [agent_backend]
}
"""

# A combined snippet covering all 8 item kinds for index tests
_ALL_KINDS_SNIPPET = """\
platform all_terminal {
    type: terminal
    format: text
}
gateway all_gateway {
    agent: all_agent
    platforms: [all_terminal]
    routes: [all_terminal -> all_agent]
}
execution_backend all_backend {
    backend_type: local
}
model_config all_model {
    provider: anthropic
    model_id: "claude-sonnet-4-6"
}
skill all_skill {
    trigger: "test"
    steps: ["do something"]
    status: draft
}
learning_config all_learning {
    mode: active
    skill_generation: true
    memory_persist: true
}
cron_task all_cron {
    schedule: "0 0 * * *"
    agent: all_agent
    deliver_to: all_terminal
}
agent all_agent {
    persona: "All kinds agent"
    model: all_model
    capabilities: [search]
    learning: all_learning
    backends: [all_backend]
}
"""


# ---------------------------------------------------------------------------
# TC-003: All 8 item kinds parse without error
# ---------------------------------------------------------------------------

def test_lark_agent_items():
    """All 8 agent item kinds parse without errors via the Lark grammar."""
    snippets = {
        "agent": _AGENT_SNIPPET,
        "platform": _PLATFORM_SNIPPET,
        "gateway": _GATEWAY_SNIPPET,
        "execution_backend": _EXECUTION_BACKEND_SNIPPET,
        "skill": _SKILL_SNIPPET,
        "learning_config": _LEARNING_CONFIG_SNIPPET,
        "cron_task": _CRON_TASK_SNIPPET,
        "model_config": _MODEL_CONFIG_SNIPPET,
    }
    for kind, src in snippets.items():
        result = _ark_parse(src)
        assert result is not None, f"Parse returned None for {kind}"


# ---------------------------------------------------------------------------
# TC-005: Parser produces correct AST dataclasses
# ---------------------------------------------------------------------------

def test_parser_dataclasses():
    """Parsing each item kind snippet produces the correct AST dataclass."""
    # agent
    af = _ark_parse(_AGENT_SNIPPET)
    agents = [it for it in af.items if isinstance(it, AgentDef)]
    assert agents, "No AgentDef found"
    assert agents[-1].name == "my_agent"

    # platform
    af = _ark_parse(_PLATFORM_SNIPPET)
    platforms = [it for it in af.items if isinstance(it, PlatformDef)]
    assert platforms, "No PlatformDef found"
    assert platforms[0].name == "my_terminal"

    # gateway
    af = _ark_parse(_GATEWAY_SNIPPET)
    gateways = [it for it in af.items if isinstance(it, GatewayDef)]
    assert gateways, "No GatewayDef found"
    assert gateways[0].name == "my_gateway"

    # execution_backend
    af = _ark_parse(_EXECUTION_BACKEND_SNIPPET)
    backends = [it for it in af.items if isinstance(it, ExecutionBackendDef)]
    assert backends, "No ExecutionBackendDef found"
    assert backends[0].name == "my_backend"

    # skill
    af = _ark_parse(_SKILL_SNIPPET)
    skills = [it for it in af.items if isinstance(it, AgentSkillDef)]
    assert skills, "No AgentSkillDef found"
    assert skills[0].name == "my_skill"

    # learning_config
    af = _ark_parse(_LEARNING_CONFIG_SNIPPET)
    learnings = [it for it in af.items if isinstance(it, LearningConfigDef)]
    assert learnings, "No LearningConfigDef found"
    assert learnings[0].name == "my_learning"

    # cron_task
    af = _ark_parse(_CRON_TASK_SNIPPET)
    crons = [it for it in af.items if isinstance(it, CronTaskDef)]
    assert crons, "No CronTaskDef found"
    assert crons[0].name == "my_task"

    # model_config
    af = _ark_parse(_MODEL_CONFIG_SNIPPET)
    models = [it for it in af.items if isinstance(it, ModelConfigDef)]
    assert models, "No ModelConfigDef found"
    assert models[0].name == "my_model"


# ---------------------------------------------------------------------------
# TC-006: ArkFile indices populated
# ---------------------------------------------------------------------------

def test_arkfile_indices():
    """Parsing a multi-item snippet populates all ArkFile agent index dicts."""
    af = _ark_parse(_ALL_KINDS_SNIPPET)

    assert "all_agent" in af.agents, f"agents index missing: {list(af.agents.keys())}"
    assert "all_terminal" in af.platforms, f"platforms index missing: {list(af.platforms.keys())}"
    assert "all_gateway" in af.gateways, f"gateways index missing: {list(af.gateways.keys())}"
    assert "all_backend" in af.execution_backends, f"execution_backends index missing"
    assert "all_skill" in af.agent_skills, f"agent_skills index missing"
    assert "all_learning" in af.learning_configs, f"learning_configs index missing"
    assert "all_cron" in af.cron_tasks, f"cron_tasks index missing"
    assert "all_model" in af.model_configs, f"model_configs index missing"


# ---------------------------------------------------------------------------
# TC-007: Regression — existing .ark files still parse
# ---------------------------------------------------------------------------

def test_parser_smoke():
    """Existing .ark files parse without exception after grammar extension."""
    existing_files = [
        REPO_ROOT / "specs" / "meta" / "ark_studio.ark",
        REPO_ROOT / "dsl" / "stdlib" / "studio.ark",
        REPO_ROOT / "dsl" / "stdlib" / "types.ark",
    ]
    for p in existing_files:
        if p.exists():
            source = p.read_text(encoding="utf-8")
            result = _ark_parse(source, file_path=p)
            assert result is not None, f"Parse returned None for {p}"


# ---------------------------------------------------------------------------
# Supporting field tests (TC-003 detail)
# ---------------------------------------------------------------------------

def test_agent_item_fields():
    """Parsed AgentDef has name, persona, capabilities, model, learning fields."""
    af = _ark_parse(_AGENT_SNIPPET)
    agents = [it for it in af.items if isinstance(it, AgentDef)]
    assert agents
    a = agents[-1]
    assert a.name == "my_agent"
    assert a.persona is not None
    assert isinstance(a.capabilities, list)
    assert a.model_ref is not None or a.model_ref == "agent_model"
    assert a.learning_ref is not None


def test_gateway_item_fields():
    """Parsed GatewayDef has name, agent_ref, platforms, routes fields."""
    af = _ark_parse(_GATEWAY_SNIPPET)
    gateways = [it for it in af.items if isinstance(it, GatewayDef)]
    assert gateways
    g = gateways[0]
    assert g.name == "my_gateway"
    assert g.agent_ref is not None
    assert isinstance(g.platforms, list)
    assert isinstance(g.routes, list)


def test_skill_item_fields():
    """Parsed AgentSkillDef has name, trigger, steps, status fields."""
    af = _ark_parse(_SKILL_SNIPPET)
    skills = [it for it in af.items if isinstance(it, AgentSkillDef)]
    assert skills
    s = skills[0]
    assert s.name == "my_skill"
    assert s.trigger is not None
    assert isinstance(s.steps, list)
    assert s.status is not None


def test_cron_task_item_fields():
    """Parsed CronTaskDef has name, schedule, agent_ref, platform_delivery fields."""
    af = _ark_parse(_CRON_TASK_SNIPPET)
    crons = [it for it in af.items if isinstance(it, CronTaskDef)]
    assert crons
    c = crons[0]
    assert c.name == "my_task"
    assert c.schedule is not None
    assert c.agent_ref is not None
    assert c.platform_delivery is not None
