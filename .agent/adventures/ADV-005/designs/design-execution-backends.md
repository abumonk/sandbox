# Execution Backends — Design

## Overview
Implement `tools/agent/backend.py` — execution backend abstraction supporting local and Docker backends for v1. Each backend can execute commands, return output, and enforce resource limits. Additional backends (SSH, Daytona, Singularity, Modal) are defined as extension points.

## Target Files
- `ark/tools/agent/backend.py` — Backend abstraction and implementations

## Approach

### Architecture

```python
class ExecutionBackend(ABC):
    """Abstract execution backend."""
    
    @abstractmethod
    def execute(self, command: str, timeout: int = 300) -> ExecutionResult:
        """Execute a command and return the result."""
        ...
    
    @abstractmethod
    def check_health(self) -> bool:
        """Check if the backend is available."""
        ...
    
    @abstractmethod
    def get_resource_usage(self) -> dict:
        """Return current resource usage."""
        ...

@dataclass
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    backend_type: str

class LocalBackend(ExecutionBackend):
    """Execute commands on the local machine."""
    def __init__(self, limits: dict):
        ...

class DockerBackend(ExecutionBackend):
    """Execute commands in a Docker container."""
    def __init__(self, image: str, limits: dict, connection: str = ""):
        ...

class SSHBackend(ExecutionBackend):
    """Execute commands on a remote machine via SSH. Stub for v1."""
    ...
```

### Backend Factory
```python
def backend_from_spec(backend_def: dict) -> ExecutionBackend:
    """Build ExecutionBackend from parsed execution_backend_def."""
    backend_type = backend_def.get("backend_type", "local")
    if backend_type == "Local":
        return LocalBackend(...)
    elif backend_type == "Docker":
        return DockerBackend(...)
    else:
        raise ValueError(f"Unsupported backend: {backend_type}")
```

### Resource Limits
Parsed from `limits` block in execution_backend spec:
- `max_memory_mb`, `max_cpu_cores`, `max_disk_gb`, `timeout_seconds`
- LocalBackend: enforces timeout via subprocess timeout
- DockerBackend: maps to `--memory`, `--cpus`, docker run flags

### Design Decisions
- v1 implements Local and Docker only; SSH/Daytona/Singularity/Modal are stubs
- LocalBackend uses subprocess.run with timeout
- DockerBackend shells out to `docker run` (no Docker SDK dependency)
- Resource limits are validated at spec-parse time (Z3 verifier checks positivity)
- Backend selection is derived from execution_backend_def.backend_type

## Dependencies
- design-dsl-surface (execution_backend_def must be parseable)
- design-stdlib-agent-schema (BackendType, ResourceLimits)

## Target Conditions
- TC-011: LocalBackend executes a command and returns ExecutionResult
- TC-012: DockerBackend constructs correct docker run command with limits
- TC-013: backend_from_spec correctly dispatches to Local/Docker backends
