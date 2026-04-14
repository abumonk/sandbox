"""Tests for tools/codegen/agent_codegen.py — 5 generators and orchestrator.

Covers TC-031 through TC-035.
"""

import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "codegen"))

from agent_codegen import (  # noqa: E402
    gen_agent_config,
    gen_gateway_routes,
    gen_cron_entries,
    gen_skill_markdown,
    gen_docker_compose,
    generate,
)


# ---------------------------------------------------------------------------
# gen_agent_config
# ---------------------------------------------------------------------------

def test_gen_agent_config_basic():
    """gen_agent_config() produces valid YAML with agent name and model info."""
    agent = {
        "name": "TestBot",
        "persona": "A test assistant",
        "capabilities": ["search", "code"],
    }
    model = {
        "provider": "Anthropic",
        "model_id": "claude-sonnet-4-6",
        "temperature": 0.5,
        "max_tokens": 2048,
    }
    yaml_str = gen_agent_config(agent, model)
    assert "name: TestBot" in yaml_str
    assert "provider: Anthropic" in yaml_str
    assert "model_id: claude-sonnet-4-6" in yaml_str
    assert "temperature: 0.5" in yaml_str
    assert "max_tokens: 2048" in yaml_str
    assert "capabilities:" in yaml_str
    assert "search" in yaml_str


def test_gen_agent_config_defaults_when_no_model():
    """gen_agent_config() fills defaults when model_config is None."""
    agent = {"name": "DefaultBot"}
    yaml_str = gen_agent_config(agent, None)
    assert "name: DefaultBot" in yaml_str
    assert "temperature:" in yaml_str
    assert "max_tokens:" in yaml_str


def test_gen_agent_config_fallback_in_model():
    """gen_agent_config() includes fallback field when model has fallback."""
    agent = {"name": "BotA"}
    model = {"provider": "openai", "model_id": "gpt-4", "fallback": "gpt-3.5-turbo"}
    yaml_str = gen_agent_config(agent, model)
    assert "fallback: gpt-3.5-turbo" in yaml_str


def test_gen_agent_config_learning_section():
    """gen_agent_config() includes learning section."""
    agent = {
        "name": "LearningBot",
        "learning_ref": {"mode": "Active", "skill_generation": True, "memory_persist": True},
    }
    yaml_str = gen_agent_config(agent, None)
    assert "learning:" in yaml_str
    assert "mode: Active" in yaml_str


def test_gen_agent_config_empty_capabilities():
    """gen_agent_config() handles empty capabilities gracefully."""
    agent = {"name": "NoCapBot", "capabilities": []}
    yaml_str = gen_agent_config(agent, None)
    assert "capabilities: []" in yaml_str


# ---------------------------------------------------------------------------
# gen_gateway_routes
# ---------------------------------------------------------------------------

def test_gen_gateway_routes_basic():
    """gen_gateway_routes() produces YAML with agent_ref and routes."""
    gateway = {
        "name": "TestGateway",
        "agent_ref": "TestBot",
        "routes": [
            {"platform": "terminal", "pattern": ".*", "priority": 1},
        ],
    }
    yaml_str = gen_gateway_routes(gateway)
    assert "agent_ref: TestBot" in yaml_str
    assert "routes:" in yaml_str
    assert "platform: terminal" in yaml_str
    assert "priority: 1" in yaml_str


def test_gen_gateway_routes_with_platforms():
    """gen_gateway_routes() includes platforms section when platforms provided."""
    gateway = {
        "name": "gw",
        "agent_ref": "bot",
        "routes": [],
    }
    platforms = [{"name": "telegram", "type": "Telegram", "format": "markdown"}]
    yaml_str = gen_gateway_routes(gateway, platforms=platforms)
    assert "platforms:" in yaml_str
    assert "telegram" in yaml_str


def test_gen_gateway_routes_no_routes():
    """gen_gateway_routes() with empty routes outputs 'routes: []'."""
    gateway = {"name": "gw", "agent_ref": "bot", "routes": []}
    yaml_str = gen_gateway_routes(gateway)
    assert "routes: []" in yaml_str


def test_gen_gateway_routes_pattern_quoted():
    """gen_gateway_routes() quotes patterns containing special YAML characters."""
    gateway = {
        "name": "gw",
        "agent_ref": "bot",
        "routes": [{"platform": "telegram", "pattern": "^/start", "priority": 2}],
    }
    yaml_str = gen_gateway_routes(gateway)
    assert "pattern:" in yaml_str
    # Pattern with special chars should be quoted
    assert "/start" in yaml_str


# ---------------------------------------------------------------------------
# gen_cron_entries
# ---------------------------------------------------------------------------

def test_gen_cron_entries_basic():
    """gen_cron_entries() produces crontab-format lines with expression and action."""
    tasks = [
        {
            "name": "daily_report",
            "expression": "0 9 * * *",
            "action": "ark agent run bot --action report",
            "deliver_to": "telegram",
        }
    ]
    cron_txt = gen_cron_entries(tasks)
    assert "0 9 * * *" in cron_txt
    assert "daily_report" in cron_txt
    assert "ark agent run" in cron_txt


def test_gen_cron_entries_includes_header():
    """gen_cron_entries() includes a header comment."""
    tasks = []
    cron_txt = gen_cron_entries(tasks)
    assert cron_txt.startswith("#")


def test_gen_cron_entries_multiple_tasks():
    """gen_cron_entries() handles multiple tasks correctly."""
    tasks = [
        {"name": "task1", "expression": "0 9 * * *", "action": "run1"},
        {"name": "task2", "expression": "0 0 * * 0", "action": "run2"},
    ]
    cron_txt = gen_cron_entries(tasks)
    assert "task1" in cron_txt
    assert "task2" in cron_txt
    assert "run1" in cron_txt
    assert "run2" in cron_txt


def test_gen_cron_entries_deliver_to():
    """gen_cron_entries() includes deliver_to info in comment."""
    tasks = [
        {"name": "t1", "expression": "0 0 * * *", "deliver_to": "slack"}
    ]
    cron_txt = gen_cron_entries(tasks)
    assert "deliver to: slack" in cron_txt


def test_gen_cron_entries_default_action():
    """gen_cron_entries() generates a default action when action is missing."""
    tasks = [{"name": "unnamed_task", "expression": "0 0 * * *"}]
    cron_txt = gen_cron_entries(tasks)
    assert "unnamed_task" in cron_txt


# ---------------------------------------------------------------------------
# gen_skill_markdown
# ---------------------------------------------------------------------------

def test_gen_skill_markdown_frontmatter():
    """gen_skill_markdown() produces YAML frontmatter with name, trigger, status."""
    skill = {
        "name": "search_skill",
        "trigger": "search|find",
        "status": "active",
        "version": "1.0",
        "steps": ["Search for info", "Return results"],
    }
    md = gen_skill_markdown(skill)
    assert md.startswith("---")
    assert "name: search_skill" in md
    assert "trigger:" in md
    assert "status: active" in md


def test_gen_skill_markdown_steps():
    """gen_skill_markdown() outputs numbered steps."""
    skill = {
        "name": "my_skill",
        "steps": ["Step A", "Step B", "Step C"],
    }
    md = gen_skill_markdown(skill)
    assert "## Steps" in md
    assert "1. Step A" in md
    assert "2. Step B" in md
    assert "3. Step C" in md


def test_gen_skill_markdown_improvement_history():
    """gen_skill_markdown() includes improvement history section."""
    skill = {
        "name": "evolving_skill",
        "steps": ["do something"],
        "improvement_history": [
            {"version": "1.0", "notes": "Initial", "score": 0.7},
            {"version": "1.1", "notes": "Improved", "score": 0.9},
        ],
    }
    md = gen_skill_markdown(skill)
    assert "## Improvement History" in md
    assert "0.7" in md
    assert "0.9" in md


def test_gen_skill_markdown_heading():
    """gen_skill_markdown() includes skill heading."""
    skill = {"name": "my_skill", "steps": []}
    md = gen_skill_markdown(skill)
    assert "# Skill: my_skill" in md


def test_gen_skill_markdown_empty_steps_placeholder():
    """gen_skill_markdown() includes placeholder when steps are empty."""
    skill = {"name": "empty_skill", "steps": []}
    md = gen_skill_markdown(skill)
    assert "## Steps" in md


# ---------------------------------------------------------------------------
# gen_docker_compose
# ---------------------------------------------------------------------------

def test_gen_docker_compose_services_section():
    """gen_docker_compose() produces a services: section."""
    backends = [
        {"name": "agent_sandbox", "backend_type": "docker", "image": "ubuntu:22.04",
         "memory_mb": 2048, "cpus": 2.0}
    ]
    yaml_str = gen_docker_compose(backends)
    assert "services:" in yaml_str
    assert "agent_sandbox:" in yaml_str
    assert "image: ubuntu:22.04" in yaml_str


def test_gen_docker_compose_resource_limits():
    """gen_docker_compose() includes memory and CPU limits."""
    backends = [
        {"name": "backend", "backend_type": "docker", "image": "alpine",
         "memory_mb": 512, "cpus": 1.0}
    ]
    yaml_str = gen_docker_compose(backends)
    assert "memory: 512M" in yaml_str
    assert "cpus:" in yaml_str


def test_gen_docker_compose_env_vars():
    """gen_docker_compose() includes environment variables."""
    backends = [
        {"name": "env_backend", "backend_type": "docker", "image": "ubuntu",
         "environment": {"AGENT_MODE": "prod", "DEBUG": "false"}}
    ]
    yaml_str = gen_docker_compose(backends)
    assert "AGENT_MODE" in yaml_str
    assert "prod" in yaml_str


def test_gen_docker_compose_no_docker_backends():
    """gen_docker_compose() outputs placeholder comment for non-docker backends."""
    backends = [{"name": "local_b", "backend_type": "local"}]
    yaml_str = gen_docker_compose(backends)
    assert "services:" in yaml_str


def test_gen_docker_compose_version():
    """gen_docker_compose() includes version field."""
    yaml_str = gen_docker_compose([])
    assert "version:" in yaml_str


# ---------------------------------------------------------------------------
# generate() — orchestrator
# ---------------------------------------------------------------------------

_SAMPLE_AST = {
    "items": [
        {
            "kind": "agent",
            "name": "TestAgent",
            "persona": "You are a test agent.",
            "capabilities": ["search"],
            "learning_ref": {"mode": "Passive", "skill_generation": False, "memory_persist": False},
            "model_config_ref": "TestModel",
        },
        {
            "kind": "model_config",
            "name": "TestModel",
            "provider": "Anthropic",
            "model_id": "claude-sonnet-4-6",
            "temperature": 0.5,
            "max_tokens": 2048,
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
        },
        {
            "kind": "skill",
            "name": "TestSkill",
            "trigger": "user asks for help",
            "status": "draft",
            "version": "0.1",
            "steps": ["Step 1", "Step 2"],
            "improvement_history": [],
        },
        {
            "kind": "execution_backend",
            "name": "test_docker",
            "backend_type": "docker",
            "image": "alpine:latest",
            "memory_mb": 512,
            "cpus": 1.0,
            "environment": {},
        },
    ]
}


def test_generate_produces_agent_config():
    """generate() produces agent config YAML artifact."""
    artifacts = generate(_SAMPLE_AST)
    assert "agents/TestAgent_config.yaml" in artifacts
    assert "name: TestAgent" in artifacts["agents/TestAgent_config.yaml"]


def test_generate_produces_gateway_routes():
    """generate() produces gateway routes YAML artifact."""
    artifacts = generate(_SAMPLE_AST)
    assert "agents/TestGateway_routes.yaml" in artifacts
    assert "agent_ref: TestAgent" in artifacts["agents/TestGateway_routes.yaml"]


def test_generate_produces_cron_entries():
    """generate() produces cron entries text artifact."""
    artifacts = generate(_SAMPLE_AST)
    assert "agents/agent_cron.txt" in artifacts
    assert "TestTask" in artifacts["agents/agent_cron.txt"]


def test_generate_produces_skill_markdown():
    """generate() produces skill markdown artifact."""
    artifacts = generate(_SAMPLE_AST)
    assert "skills/TestSkill.md" in artifacts
    assert "TestSkill" in artifacts["skills/TestSkill.md"]


def test_generate_produces_docker_compose():
    """generate() produces docker-compose fragment artifact."""
    artifacts = generate(_SAMPLE_AST)
    assert "docker-compose.agent.yaml" in artifacts
    assert "services:" in artifacts["docker-compose.agent.yaml"]


def test_generate_writes_to_disk(tmp_path):
    """generate() writes files to disk when output_dir is provided."""
    generate(_SAMPLE_AST, output_dir=tmp_path)
    assert (tmp_path / "agents" / "TestAgent_config.yaml").exists()
    assert (tmp_path / "agents" / "TestGateway_routes.yaml").exists()
    assert (tmp_path / "skills" / "TestSkill.md").exists()
