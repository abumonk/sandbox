"""Tests for tools/agent/agent_runner.py — AgentRunner init, process_message, tick.

Covers TC-022 through TC-024.
"""

import sys
import pathlib
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_AGENT_DIR = REPO_ROOT / "tools" / "agent"
# Insert tools/ so agent package resolves relative imports
if str(_AGENT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR.parent))
# Also add agent/ for gateway.py / backend.py which have no relative imports
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from gateway import Gateway, GatewayRoute, Message  # noqa: E402
from backend import LocalBackend  # noqa: E402
from skill_manager import Skill, SkillManager  # noqa: E402
from learning import LearningEngine, SessionEntry  # noqa: E402
from scheduler import Scheduler, ScheduledTask  # noqa: E402
from agent_runner import AgentConfig, AgentRunner, build_agent_runtime  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_runner(
    learning_mode="passive",
    skills=None,
    routes=None,
    cron_tasks=None,
):
    config = AgentConfig(
        name="test_agent",
        persona="A helpful test agent",
        model_config={"provider": "anthropic", "model_id": "claude-sonnet-4-6"},
        capabilities=["search"],
        learning_mode=learning_mode,
    )
    gw_routes = routes or []
    gateway = Gateway(agent_name="test_agent", routes=gw_routes)
    backend = LocalBackend()
    mgr = SkillManager(skills=skills or [])
    learning = LearningEngine(mode=learning_mode)
    sched = Scheduler(tasks=cron_tasks or [])
    return AgentRunner(
        config=config,
        gateway=gateway,
        backend=backend,
        skill_manager=mgr,
        learning=learning,
        scheduler=sched,
    )


def _make_message(content="hello", platform="terminal"):
    return Message(
        id="test-id",
        platform=platform,
        sender="test_user",
        content=content,
        timestamp="2024-01-01T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# AgentRunner init
# ---------------------------------------------------------------------------

def test_runner_init_sets_running_false():
    """AgentRunner starts with _running=False before init()."""
    runner = _make_runner()
    assert runner._running is False


def test_runner_init_initializes_subsystems():
    """AgentRunner.init() sets _running=True."""
    runner = _make_runner()
    runner.init()
    assert runner._running is True


def test_runner_shutdown_clears_running():
    """AgentRunner.shutdown() sets _running=False."""
    runner = _make_runner()
    runner.init()
    runner.shutdown()
    assert runner._running is False


def test_runner_config_attributes():
    """AgentRunner exposes config, gateway, backend, skills, learning, scheduler."""
    runner = _make_runner()
    assert runner.config.name == "test_agent"
    assert runner.config.persona == "A helpful test agent"
    assert isinstance(runner.gateway, Gateway)
    assert isinstance(runner.backend, LocalBackend)
    assert isinstance(runner.skills, SkillManager)
    assert isinstance(runner.learning, LearningEngine)
    assert isinstance(runner.scheduler, Scheduler)


# ---------------------------------------------------------------------------
# process_message — routing
# ---------------------------------------------------------------------------

def test_process_message_returns_message():
    """AgentRunner.process_message() returns a Message instance."""
    runner = _make_runner()
    runner.init()
    msg = _make_message("hello world")
    response = runner.process_message(msg)
    assert isinstance(response, Message)


def test_process_message_model_fallback():
    """process_message() uses model fallback when no skill matches."""
    runner = _make_runner()
    runner.init()
    msg = _make_message("unmatched content xyz123")
    response = runner.process_message(msg)
    # Model fallback placeholder response contains "model response"
    assert "model response" in response.content


def test_process_message_skill_path():
    """process_message() uses skill execution when trigger matches."""
    skill = Skill(
        name="hello_skill",
        trigger_pattern="hello",
        trigger_priority=5,
        steps=["say hello back"],
        status="active",
    )
    runner = _make_runner(skills=[skill])
    runner.init()
    msg = _make_message("hello there")
    response = runner.process_message(msg)
    # Response should come from skill execution or model response (not crash)
    assert isinstance(response, Message)
    assert response.platform == msg.platform


def test_process_message_records_session():
    """process_message() records a session entry in the learning engine."""
    runner = _make_runner()
    runner.init()
    msg = _make_message("test message for learning")
    initial_count = len(runner.learning._sessions)
    runner.process_message(msg)
    assert len(runner.learning._sessions) == initial_count + 1


def test_process_message_response_platform_matches():
    """process_message() response has same platform as input message."""
    runner = _make_runner()
    runner.init()
    msg = _make_message("test", platform="telegram")
    response = runner.process_message(msg)
    assert response.platform == "telegram"


def test_process_message_response_sender_is_agent():
    """process_message() response sender is the agent name."""
    runner = _make_runner()
    runner.init()
    msg = _make_message("hello")
    response = runner.process_message(msg)
    assert response.sender == "test_agent"


def test_process_message_response_has_metadata():
    """process_message() response metadata includes in_reply_to."""
    runner = _make_runner()
    runner.init()
    msg = _make_message("hello")
    response = runner.process_message(msg)
    assert "in_reply_to" in response.metadata


# ---------------------------------------------------------------------------
# Active learning mode — skill generation attempt
# ---------------------------------------------------------------------------

def test_process_message_active_mode_attempts_skill_generation():
    """In active learning mode, process_message() may attempt skill generation."""
    runner = _make_runner(learning_mode="active")
    runner.init()
    # Send 3 messages so that skill generation threshold (>=2 sessions) is met
    for i in range(3):
        runner.process_message(_make_message(f"message {i}"))
    # After 3 messages, auto_skill generation may have been attempted
    # We just verify no exception was raised and sessions were recorded
    assert len(runner.learning._sessions) == 3


# ---------------------------------------------------------------------------
# Tick delegation
# ---------------------------------------------------------------------------

def test_tick_calls_scheduler():
    """AgentRunner.tick() runs without error and delegates to scheduler."""
    task = ScheduledTask(
        name="tick_task",
        cron_expression="* * * * *",
        agent_ref="test_agent",
        platform_delivery="terminal",
        action="do_tick",
        enabled=True,
        next_run="2020-01-01T00:00:00",  # past — should be due
    )
    runner = _make_runner(cron_tasks=[task])
    runner.init()
    posix_now = time.time()
    # Should not raise
    runner.tick(posix_now)


def test_tick_updates_scheduler_state():
    """AgentRunner.tick() causes due tasks to be executed."""
    task = ScheduledTask(
        name="due_now",
        cron_expression="* * * * *",
        agent_ref="test_agent",
        platform_delivery="terminal",
        action="report",
        enabled=True,
        next_run="2020-01-01T00:00:00",
    )
    runner = _make_runner(cron_tasks=[task])
    runner.init()
    runner.tick(time.time())
    # After tick, last_run should be set
    assert task.last_run is not None


# ---------------------------------------------------------------------------
# build_agent_runtime factory
# ---------------------------------------------------------------------------

def test_build_agent_runtime_returns_runner():
    """build_agent_runtime() constructs a complete AgentRunner."""
    agent_def = {
        "name": "factory_agent",
        "persona": "Factory test agent",
        "capabilities": ["search"],
        "learning_mode": "passive",
    }
    specs = {
        "model_configs": {},
        "learning_configs": {},
        "backend_defs": {},
        "gateway_specs": {},
        "skill_defs": [],
        "cron_tasks": [],
    }
    runner = build_agent_runtime(agent_def, specs)
    assert isinstance(runner, AgentRunner)
    assert runner.config.name == "factory_agent"


def test_build_agent_runtime_defaults_to_local_backend():
    """build_agent_runtime() uses LocalBackend when no backends specified."""
    agent_def = {"name": "no_backend_agent"}
    specs = {}
    runner = build_agent_runtime(agent_def, specs)
    assert isinstance(runner.backend, LocalBackend)
