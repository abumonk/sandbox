# Agent Verification — Design

## Overview
Implement `tools/verify/agent_verify.py` — Z3-based verification for agent specifications. Checks referential integrity, constraint validity, and structural properties across agent, gateway, platform, model_config, cron_task, skill, and execution_backend items.

## Target Files
- `ark/tools/verify/agent_verify.py` — Agent-specific Z3 verifier (new module)
- `ark/tools/verify/ark_verify.py` — Integration point (add agent verify dispatch)

## Approach

### Verification Checks

#### Check 1: Gateway Reference Validity
Every gateway must reference a valid agent and valid platforms.
```python
def verify_gateway_references(gateways, agents, platforms) -> list:
    """For each gateway:
    - gateway.agent must exist in agents dict
    - each platform in gateway.platforms must exist in platforms dict
    """
```

#### Check 2: Cron Task Reference Validity
Every cron_task must reference a valid agent and platform for delivery.
```python
def verify_cron_references(cron_tasks, agents, platforms) -> list:
    """For each cron_task:
    - cron_task.agent must exist in agents dict
    - cron_task.deliver_to must exist in platforms dict
    """
```

#### Check 3: Model Fallback Acyclicity
Model fallback chains must be cycle-free (same pattern as escalation acyclicity in ADV-003).
```python
def verify_model_fallback_acyclicity(model_configs) -> list:
    """Use Z3 ordinals: assign each model_config an Int ordinal.
    For each fallback edge (A -> B): ordinal(B) > ordinal(A).
    UNSAT means cycle exists.
    """
```

#### Check 4: Resource Limit Positivity
Execution backend resource limits must be positive and within sane bounds.
```python
def verify_resource_limits(backends) -> list:
    """For each execution_backend:
    - max_memory_mb > 0 and <= 1048576 (1TB)
    - max_cpu_cores > 0 and <= 1024
    - max_disk_gb > 0 and <= 65536 (64TB)
    - timeout_seconds > 0 and <= 86400 (24h)
    """
```

#### Check 5: Skill Trigger Overlap Detection
Skill triggers with the same priority should not match the same patterns.
```python
def verify_skill_trigger_overlap(skills) -> list:
    """For each pair of skills with equal priority:
    Z3 check if both trigger patterns can match the same string.
    Uses Z3 string theory for regex intersection.
    Warn (not error) if overlap detected.
    """
```

#### Check 6: Agent Completeness
Every agent must have at least one backend and a valid model reference.
```python
def verify_agent_completeness(agents, backends, model_configs) -> list:
    """For each agent:
    - agent.model must exist in model_configs
    - at least one backend in agent.backends must exist in backends
    """
```

### Integration
```python
def verify_agent(ast: dict) -> list:
    """Entry point: run all agent checks. Returns list of result dicts."""
    results = []
    results += verify_gateway_references(...)
    results += verify_cron_references(...)
    results += verify_model_fallback_acyclicity(...)
    results += verify_resource_limits(...)
    results += verify_skill_trigger_overlap(...)
    results += verify_agent_completeness(...)
    return results
```

In `ark_verify.py`, add dispatch:
```python
# After studio verify dispatch
if has_agent_items(ast_json):
    from agent_verify import verify_agent
    agent_results = verify_agent(ast_json)
    # merge into results
```

### Design Decisions
- Follow separate domain module pattern (agent_verify.py, not extending ark_verify.py core)
- Model fallback acyclicity uses Z3 ordinals (same proven approach as escalation paths in ADV-003)
- Resource limit checks use concrete Z3 Int bounds (deterministic, fast)
- Skill trigger overlap uses Z3 string regex (may be slow for complex patterns, bounded)
- PASS_OPAQUE not needed here: all checks are concrete structural properties

## Dependencies
- design-dsl-surface (parser must produce agent AST items)

## Target Conditions
- TC-024: Gateway references validated — invalid agent/platform names caught
- TC-025: Cron task references validated — invalid agent/platform names caught
- TC-026: Model fallback cycles detected via Z3 ordinals
- TC-027: Resource limit violations (non-positive, out-of-bounds) detected
- TC-028: Skill trigger overlap warnings generated for ambiguous triggers
- TC-029: Agent completeness check catches missing model/backend references
