"""Integration tests for the Autonomous Agent System.

End-to-end tests that parse/verify agent .ark specs and check CLI behavior.
Covers TC-039 through TC-044.
"""

import sys
import subprocess
import pathlib
import json
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "parser"))
sys.path.insert(0, str(REPO_ROOT / "tools" / "verify"))
sys.path.insert(0, str(REPO_ROOT / "tools" / "codegen"))

AGENT_SYSTEM_ARK = REPO_ROOT / "specs" / "infra" / "agent_system.ark"
ARK_AGENT_ARK = REPO_ROOT / "specs" / "meta" / "ark_agent.ark"
ARK_PY = REPO_ROOT / "ark.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_ark(*args, timeout=30):
    """Run ark.py with given args. Returns CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(ARK_PY)] + list(args),
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _parse_spec(path):
    """Parse a .ark file and return ArkFile."""
    from ark_parser import parse as _ark_parse
    source = pathlib.Path(path).read_text(encoding="utf-8")
    return _ark_parse(source, file_path=pathlib.Path(path))


# ---------------------------------------------------------------------------
# TC-039: agent_system.ark parses via CLI
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_agent_system_ark_parse_cli():
    """CLI `ark.py parse specs/infra/agent_system.ark` returns exit code 0."""
    if not AGENT_SYSTEM_ARK.exists():
        pytest.skip(f"agent_system.ark not found at {AGENT_SYSTEM_ARK}")
    result = _run_ark("parse", str(AGENT_SYSTEM_ARK))
    assert result.returncode == 0, f"Parse failed:\n{result.stderr}"


@pytest.mark.integration
def test_agent_system_ark_parse_python():
    """agent_system.ark parses via Python ArkParser without errors."""
    if not AGENT_SYSTEM_ARK.exists():
        pytest.skip(f"agent_system.ark not found at {AGENT_SYSTEM_ARK}")
    ark_file = _parse_spec(AGENT_SYSTEM_ARK)
    assert ark_file is not None


# ---------------------------------------------------------------------------
# TC-040: agent_system.ark ArkFile indices populated
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_agent_system_ark_registry():
    """agent_system.ark populates all 8 agent ArkFile indices."""
    if not AGENT_SYSTEM_ARK.exists():
        pytest.skip(f"agent_system.ark not found at {AGENT_SYSTEM_ARK}")
    ark_file = _parse_spec(AGENT_SYSTEM_ARK)

    # Check that at least one item was indexed in each category
    assert len(ark_file.agents) >= 1, f"No agents found in {AGENT_SYSTEM_ARK}"
    assert len(ark_file.platforms) >= 1, f"No platforms found"
    assert len(ark_file.gateways) >= 1, f"No gateways found"
    assert len(ark_file.execution_backends) >= 1, f"No execution_backends found"
    assert len(ark_file.agent_skills) >= 1, f"No agent_skills found"
    assert len(ark_file.learning_configs) >= 1, f"No learning_configs found"
    assert len(ark_file.cron_tasks) >= 1, f"No cron_tasks found"
    assert len(ark_file.model_configs) >= 1, f"No model_configs found"


@pytest.mark.integration
def test_agent_system_ark_known_items():
    """agent_system.ark contains the known named items from the spec."""
    if not AGENT_SYSTEM_ARK.exists():
        pytest.skip(f"agent_system.ark not found at {AGENT_SYSTEM_ARK}")
    ark_file = _parse_spec(AGENT_SYSTEM_ARK)

    assert "autonomous_agent" in ark_file.agents
    assert "agent_gateway" in ark_file.gateways
    assert "active_learning" in ark_file.learning_configs
    assert "primary_model" in ark_file.model_configs


# ---------------------------------------------------------------------------
# TC-041: ark_agent.ark parses via CLI
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_ark_agent_ark_parse_cli():
    """CLI `ark.py parse specs/meta/ark_agent.ark` returns exit code 0."""
    if not ARK_AGENT_ARK.exists():
        pytest.skip(f"ark_agent.ark not found at {ARK_AGENT_ARK}")
    result = _run_ark("parse", str(ARK_AGENT_ARK))
    assert result.returncode == 0, f"Parse failed:\n{result.stderr}"


@pytest.mark.integration
def test_ark_agent_ark_parse_python():
    """ark_agent.ark parses via Python ArkParser without errors."""
    if not ARK_AGENT_ARK.exists():
        pytest.skip(f"ark_agent.ark not found at {ARK_AGENT_ARK}")
    ark_file = _parse_spec(ARK_AGENT_ARK)
    assert ark_file is not None


# ---------------------------------------------------------------------------
# TC-042: verify agent_system.ark via CLI
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_agent_system_ark_verify_cli():
    """CLI `ark.py verify specs/infra/agent_system.ark` returns exit code 0."""
    if not AGENT_SYSTEM_ARK.exists():
        pytest.skip(f"agent_system.ark not found at {AGENT_SYSTEM_ARK}")
    result = _run_ark("verify", str(AGENT_SYSTEM_ARK))
    assert result.returncode == 0, f"Verify failed:\n{result.stderr}\n{result.stdout}"


@pytest.mark.integration
def test_agent_system_ark_verify_python():
    """agent_system.ark passes agent_verify.verify_agent() without critical failures."""
    if not AGENT_SYSTEM_ARK.exists():
        pytest.skip(f"agent_system.ark not found at {AGENT_SYSTEM_ARK}")
    from ark_parser import parse as _ark_parse, to_json as _ark_to_json
    from agent_verify import verify_agent

    source = AGENT_SYSTEM_ARK.read_text(encoding="utf-8")
    ark_file = _ark_parse(source, file_path=AGENT_SYSTEM_ARK)

    import json
    ast_dict = json.loads(_ark_to_json(ark_file))
    results = verify_agent(ast_dict)

    # Count failures
    failures = [r for r in results if r["status"] == "fail"]
    # The spec is designed to be valid — we allow warnings but no hard fails
    # from gateway/cron/completeness checks (only fallback cycle check may vary)
    critical_failures = [
        r for r in failures
        if r["check"] in ("agent_gateway_refs", "agent_cron_refs", "agent_completeness")
    ]
    assert critical_failures == [], f"Critical failures: {critical_failures}"


# ---------------------------------------------------------------------------
# TC-043: codegen from agent_system.ark via CLI
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_agent_system_ark_codegen_cli(tmp_path):
    """CLI `ark.py codegen specs/infra/agent_system.ark` runs without error."""
    if not AGENT_SYSTEM_ARK.exists():
        pytest.skip(f"agent_system.ark not found at {AGENT_SYSTEM_ARK}")
    result = _run_ark("codegen", str(AGENT_SYSTEM_ARK), "--out", str(tmp_path))
    assert result.returncode == 0, f"Codegen failed:\n{result.stderr}"


@pytest.mark.integration
def test_agent_system_ark_codegen_python(tmp_path):
    """agent_codegen.generate() produces artifacts from agent_system.ark."""
    if not AGENT_SYSTEM_ARK.exists():
        pytest.skip(f"agent_system.ark not found at {AGENT_SYSTEM_ARK}")
    from ark_parser import parse as _ark_parse, to_json as _ark_to_json
    from agent_codegen import generate

    source = AGENT_SYSTEM_ARK.read_text(encoding="utf-8")
    ark_file = _ark_parse(source, file_path=AGENT_SYSTEM_ARK)

    import json
    ast_dict = json.loads(_ark_to_json(ark_file))
    artifacts = generate(ast_dict, output_dir=tmp_path)

    assert len(artifacts) > 0, "No artifacts generated"
    # Should produce at least one agent config
    agent_configs = [k for k in artifacts if k.startswith("agents/") and k.endswith("_config.yaml")]
    assert len(agent_configs) >= 1, f"No agent configs. Keys: {list(artifacts.keys())}"


# ---------------------------------------------------------------------------
# TC-044: Smoke test — all agent test files importable and no crashes
# ---------------------------------------------------------------------------

def test_agent_schema_module_importable():
    """dsl/stdlib/agent.ark path exists and is readable."""
    agent_ark = REPO_ROOT / "dsl" / "stdlib" / "agent.ark"
    assert agent_ark.exists(), f"agent.ark not found at {agent_ark}"
    content = agent_ark.read_text(encoding="utf-8")
    assert "enum Platform" in content


def test_agent_runner_module_importable():
    """tools/agent/agent_runner.py is importable."""
    from agent_runner import AgentRunner, AgentConfig, build_agent_runtime
    assert AgentRunner is not None


def test_agent_backend_module_importable():
    """tools/agent/backend.py is importable."""
    from backend import LocalBackend, DockerBackend, backend_from_spec
    assert LocalBackend is not None


def test_agent_gateway_module_importable():
    """tools/agent/gateway.py is importable."""
    from gateway import Gateway, Message, gateway_from_spec
    assert Gateway is not None


def test_agent_skill_manager_importable():
    """tools/agent/skill_manager.py is importable."""
    from skill_manager import SkillManager, Skill, skill_from_spec
    assert SkillManager is not None


def test_agent_learning_importable():
    """tools/agent/learning.py is importable."""
    from learning import LearningEngine, SessionEntry, learning_from_spec
    assert LearningEngine is not None


def test_agent_scheduler_importable():
    """tools/agent/scheduler.py is importable."""
    from scheduler import Scheduler, ScheduledTask, scheduler_from_spec
    assert Scheduler is not None


def test_agent_verify_importable():
    """tools/verify/agent_verify.py is importable."""
    from agent_verify import verify_agent
    assert verify_agent is not None


def test_agent_codegen_importable():
    """tools/codegen/agent_codegen.py is importable."""
    from agent_codegen import generate, gen_agent_config
    assert generate is not None


def test_agent_visualizer_importable():
    """tools/visualizer/ark_visualizer.py is importable."""
    from ark_visualizer import extract_agent_data, generate_graph_data
    assert extract_agent_data is not None
