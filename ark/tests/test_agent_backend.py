"""Tests for tools/agent/backend.py — LocalBackend, DockerBackend, factory.

Covers TC-011 through TC-013.
"""

import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "agent"))

from backend import (  # noqa: E402
    ExecutionResult,
    ExecutionBackend,
    LocalBackend,
    DockerBackend,
    SSHBackend,
    backend_from_spec,
)


# ---------------------------------------------------------------------------
# ExecutionResult
# ---------------------------------------------------------------------------

def test_execution_result_fields():
    """ExecutionResult has correct fields."""
    r = ExecutionResult(stdout="ok", stderr="", exit_code=0, duration_ms=10.0, backend_type="local")
    assert r.stdout == "ok"
    assert r.exit_code == 0
    assert r.backend_type == "local"


# ---------------------------------------------------------------------------
# LocalBackend
# ---------------------------------------------------------------------------

def test_local_backend_execute_echo():
    """LocalBackend.execute() runs a simple echo command successfully."""
    backend = LocalBackend()
    result = backend.execute("echo hello_ark")
    assert result.exit_code == 0
    assert "hello_ark" in result.stdout
    assert result.backend_type == "local"
    assert result.duration_ms >= 0


def test_local_backend_execute_nonzero():
    """LocalBackend.execute() captures non-zero exit codes."""
    backend = LocalBackend()
    result = backend.execute("exit 42", timeout=5)
    assert result.exit_code == 42


def test_local_backend_check_health():
    """LocalBackend.check_health() returns True."""
    backend = LocalBackend()
    assert backend.check_health() is True


def test_local_backend_get_resource_usage_returns_dict():
    """LocalBackend.get_resource_usage() returns a dict."""
    backend = LocalBackend()
    usage = backend.get_resource_usage()
    assert isinstance(usage, dict)


def test_local_backend_respects_limit_timeout():
    """LocalBackend respects timeout_seconds from limits."""
    backend = LocalBackend(limits={"timeout_seconds": 1})
    # A command that tries to sleep longer than the limit
    result = backend.execute("sleep 5")
    # Should time out (exit_code 124) or complete quickly
    assert result.exit_code != 0 or result.duration_ms < 3000


# ---------------------------------------------------------------------------
# DockerBackend
# ---------------------------------------------------------------------------

def test_docker_backend_requires_image():
    """DockerBackend raises ValueError when image is empty."""
    try:
        DockerBackend(image="")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_docker_backend_build_command_basic():
    """DockerBackend._build_docker_command() contains the image name."""
    backend = DockerBackend(image="alpine:latest")
    cmd = backend._build_docker_command("echo test")
    assert "docker" in cmd
    assert "alpine:latest" in cmd
    assert "echo test" in cmd


def test_docker_backend_build_command_memory_limit():
    """DockerBackend._build_docker_command() includes --memory when max_memory_mb set."""
    backend = DockerBackend(image="alpine:latest", limits={"max_memory_mb": 512})
    cmd = backend._build_docker_command("echo test")
    assert "--memory" in cmd
    assert "512m" in cmd


def test_docker_backend_build_command_cpu_limit():
    """DockerBackend._build_docker_command() includes --cpus when max_cpu_cores set."""
    backend = DockerBackend(image="alpine:latest", limits={"max_cpu_cores": 2})
    cmd = backend._build_docker_command("echo test")
    assert "--cpus" in cmd


def test_docker_backend_build_command_rm_flag():
    """DockerBackend._build_docker_command() includes --rm flag."""
    backend = DockerBackend(image="alpine:latest")
    cmd = backend._build_docker_command("echo test")
    assert "--rm" in cmd


def test_docker_backend_get_resource_usage_returns_dict():
    """DockerBackend.get_resource_usage() returns a dict (best-effort)."""
    backend = DockerBackend(image="alpine:latest")
    usage = backend.get_resource_usage()
    assert isinstance(usage, dict)


# ---------------------------------------------------------------------------
# SSHBackend
# ---------------------------------------------------------------------------

def test_ssh_backend_execute_raises():
    """SSHBackend.execute() raises NotImplementedError."""
    backend = SSHBackend(host="localhost")
    try:
        backend.execute("echo test")
        assert False, "Expected NotImplementedError"
    except NotImplementedError:
        pass


def test_ssh_backend_check_health_raises():
    """SSHBackend.check_health() raises NotImplementedError."""
    backend = SSHBackend()
    try:
        backend.check_health()
        assert False, "Expected NotImplementedError"
    except NotImplementedError:
        pass


# ---------------------------------------------------------------------------
# Factory — backend_from_spec
# ---------------------------------------------------------------------------

def test_factory_local():
    """backend_from_spec() with backend_type=Local returns LocalBackend."""
    spec = {"backend_type": "Local"}
    backend = backend_from_spec(spec)
    assert isinstance(backend, LocalBackend)


def test_factory_docker():
    """backend_from_spec() with backend_type=Docker returns DockerBackend."""
    spec = {"backend_type": "Docker", "image": "ubuntu:22.04"}
    backend = backend_from_spec(spec)
    assert isinstance(backend, DockerBackend)
    assert backend.image == "ubuntu:22.04"


def test_factory_docker_no_image_raises():
    """backend_from_spec() with backend_type=Docker and no image raises ValueError."""
    spec = {"backend_type": "Docker"}
    try:
        backend_from_spec(spec)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_factory_ssh():
    """backend_from_spec() with backend_type=SSH returns SSHBackend."""
    spec = {"backend_type": "SSH", "host": "myhost"}
    backend = backend_from_spec(spec)
    assert isinstance(backend, SSHBackend)
    assert backend.host == "myhost"


def test_factory_unknown_raises():
    """backend_from_spec() with unknown backend_type raises ValueError."""
    spec = {"backend_type": "Daytona"}
    try:
        backend_from_spec(spec)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_factory_default_is_local():
    """backend_from_spec() with no backend_type defaults to LocalBackend."""
    spec = {}
    backend = backend_from_spec(spec)
    assert isinstance(backend, LocalBackend)


def test_factory_passes_limits():
    """backend_from_spec() passes limits to LocalBackend."""
    spec = {"backend_type": "Local", "limits": {"timeout_seconds": 60}}
    backend = backend_from_spec(spec)
    assert isinstance(backend, LocalBackend)
    assert backend.limits.get("timeout_seconds") == 60
