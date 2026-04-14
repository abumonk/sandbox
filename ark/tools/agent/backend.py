"""
Execution backend abstraction for the ARK agent runner.

Provides ExecutionResult, ExecutionBackend ABC, LocalBackend, DockerBackend,
SSHBackend stub, and backend_from_spec factory.
"""

from __future__ import annotations

import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class ExecutionResult:
    """Result of a command executed by an ExecutionBackend."""
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    backend_type: str = "unknown"


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class ExecutionBackend(ABC):
    """Abstract execution backend."""

    @abstractmethod
    def execute(self, command: str, timeout: int = 30) -> ExecutionResult:
        """Execute *command* and return an ExecutionResult."""
        ...

    @abstractmethod
    def check_health(self) -> bool:
        """Return True if the backend is reachable and ready."""
        ...

    @abstractmethod
    def get_resource_usage(self) -> dict:
        """Return a dict describing current resource usage."""
        ...


# ---------------------------------------------------------------------------
# Local backend
# ---------------------------------------------------------------------------

class LocalBackend(ExecutionBackend):
    """Execute commands on the local machine via subprocess."""

    def __init__(self, limits: Optional[dict] = None) -> None:
        self.limits: dict = limits or {}

    # ------------------------------------------------------------------
    def execute(self, command: str, timeout: int = 30) -> ExecutionResult:
        """Run *command* in a local subprocess with *timeout* seconds."""
        effective_timeout = self.limits.get("timeout_seconds", timeout)

        start = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed_ms = (time.monotonic() - start) * 1000.0
            stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            return ExecutionResult(
                stdout=stdout,
                stderr=stderr + f"\n[timeout after {effective_timeout}s]",
                exit_code=124,
                duration_ms=round(elapsed_ms, 3),
                backend_type="local",
            )

        elapsed_ms = (time.monotonic() - start) * 1000.0
        return ExecutionResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            duration_ms=round(elapsed_ms, 3),
            backend_type="local",
        )

    # ------------------------------------------------------------------
    def check_health(self) -> bool:
        """Always healthy — local machine is always available."""
        return True

    # ------------------------------------------------------------------
    def get_resource_usage(self) -> dict:
        """Return basic resource info from the local environment."""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            return {
                "disk_total_gb": round(total / (1024 ** 3), 2),
                "disk_used_gb": round(used / (1024 ** 3), 2),
                "disk_free_gb": round(free / (1024 ** 3), 2),
            }
        except Exception:
            return {}


# ---------------------------------------------------------------------------
# Docker backend
# ---------------------------------------------------------------------------

class DockerBackend(ExecutionBackend):
    """Execute commands inside a Docker container via `docker run`."""

    def __init__(
        self,
        image: str,
        limits: Optional[dict] = None,
        connection: str = "",
    ) -> None:
        if not image:
            raise ValueError("DockerBackend requires a non-empty image name")
        self.image = image
        self.limits: dict = limits or {}
        self.connection = connection  # reserved for remote Docker hosts

    # ------------------------------------------------------------------
    def _build_docker_command(self, command: str) -> str:
        """Construct the full `docker run ...` command string."""
        parts = ["docker", "run", "--rm"]

        # Resource limits
        max_memory_mb = self.limits.get("max_memory_mb")
        if max_memory_mb is not None:
            parts += ["--memory", f"{int(max_memory_mb)}m"]

        max_cpu_cores = self.limits.get("max_cpu_cores")
        if max_cpu_cores is not None:
            parts += ["--cpus", str(float(max_cpu_cores))]

        # GPU flag (simple device passthrough)
        gpu = self.limits.get("gpu")
        if gpu:
            parts += ["--gpus", str(gpu)]

        parts.append(self.image)

        # Append the user command as a shell invocation
        parts += ["sh", "-c", command]

        return " ".join(parts)

    # ------------------------------------------------------------------
    def execute(self, command: str, timeout: int = 30) -> ExecutionResult:
        """Build and run a docker command, capturing stdout/stderr."""
        effective_timeout = self.limits.get("timeout_seconds", timeout)
        docker_cmd = self._build_docker_command(command)

        start = time.monotonic()
        try:
            proc = subprocess.run(
                docker_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed_ms = (time.monotonic() - start) * 1000.0
            stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            return ExecutionResult(
                stdout=stdout,
                stderr=stderr + f"\n[docker timeout after {effective_timeout}s]",
                exit_code=124,
                duration_ms=round(elapsed_ms, 3),
                backend_type="docker",
            )

        elapsed_ms = (time.monotonic() - start) * 1000.0
        return ExecutionResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            duration_ms=round(elapsed_ms, 3),
            backend_type="docker",
        )

    # ------------------------------------------------------------------
    def check_health(self) -> bool:
        """Run `docker info` to verify the Docker daemon is reachable."""
        try:
            proc = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return proc.returncode == 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    def get_resource_usage(self) -> dict:
        """Query `docker stats` for the running container (best-effort)."""
        try:
            proc = subprocess.run(
                ["docker", "stats", "--no-stream", "--format",
                 "{{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                return {"docker_stats": proc.stdout.strip()}
        except Exception:
            pass
        return {}


# ---------------------------------------------------------------------------
# SSH backend (stub)
# ---------------------------------------------------------------------------

class SSHBackend(ExecutionBackend):
    """Remote execution over SSH — stub, not implemented in v1."""

    def __init__(self, host: str = "", limits: Optional[dict] = None) -> None:
        self.host = host
        self.limits: dict = limits or {}

    def execute(self, command: str, timeout: int = 30) -> ExecutionResult:
        raise NotImplementedError("SSHBackend is not implemented in v1")

    def check_health(self) -> bool:
        raise NotImplementedError("SSHBackend is not implemented in v1")

    def get_resource_usage(self) -> dict:
        raise NotImplementedError("SSHBackend is not implemented in v1")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def backend_from_spec(spec: dict) -> ExecutionBackend:
    """Build an ExecutionBackend from a parsed execution_backend_def dict.

    Expected keys
    -------------
    backend_type : str     — "Local" | "Docker" | "SSH"
    image        : str     — (Docker only) container image
    limits       : dict    — resource limits block
    connection   : str     — (Docker/SSH) remote endpoint
    host         : str     — (SSH) remote host
    """
    backend_type = spec.get("backend_type", "Local")
    limits = spec.get("limits", {})

    if backend_type == "Local":
        return LocalBackend(limits=limits)

    elif backend_type == "Docker":
        image = spec.get("image", "")
        if not image:
            raise ValueError("DockerBackend spec must include a non-empty 'image' field")
        connection = spec.get("connection", "")
        return DockerBackend(image=image, limits=limits, connection=connection)

    elif backend_type == "SSH":
        host = spec.get("host", spec.get("connection", ""))
        return SSHBackend(host=host, limits=limits)

    else:
        raise ValueError(
            f"Unsupported backend_type: {backend_type!r}. "
            "Expected one of: Local, Docker, SSH"
        )
