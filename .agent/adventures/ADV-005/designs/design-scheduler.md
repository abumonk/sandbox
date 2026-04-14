# Cron Scheduler — Design

## Overview
Implement `tools/agent/scheduler.py` — cron-based task scheduling with platform delivery routing. Scheduled tasks run at specified intervals, execute via an agent, and deliver results to a target platform.

## Target Files
- `ark/tools/agent/scheduler.py` — Scheduler runtime module

## Approach

### Core Classes

```python
@dataclass
class ScheduledTask:
    name: str
    schedule: str         # cron expression (e.g., "0 9 * * 1")
    agent: str            # agent name to execute the task
    action: str           # action description / command
    deliver_to: str       # platform name for result delivery
    enabled: bool
    last_run: float       # timestamp of last execution
    next_run: float       # computed next run timestamp

class Scheduler:
    def __init__(self, tasks: list[ScheduledTask]):
        self._tasks = tasks
        self._running = False
    
    def compute_next_run(self, task: ScheduledTask, now: float) -> float:
        """Parse cron expression, compute next execution time."""
        ...
    
    def get_due_tasks(self, now: float) -> list[ScheduledTask]:
        """Return tasks whose next_run <= now."""
        ...
    
    def execute_task(self, task: ScheduledTask, agent_runner) -> dict:
        """Run the task via the agent, deliver result to platform."""
        ...
    
    def tick(self, now: float, agent_runner):
        """Check for due tasks and execute them. Called periodically."""
        ...
```

### Cron Expression Parsing
- Support standard 5-field cron syntax: minute, hour, day-of-month, month, day-of-week
- Use a simple parser (no external dependency) for basic expressions
- Support `*`, specific values, ranges (`1-5`), and step values (`*/5`)

### Integration with Specs
```python
def scheduler_from_spec(cron_defs: list[dict], agents: dict) -> Scheduler:
    """Build Scheduler from parsed cron_task_defs and agent registry."""
```

### Design Decisions
- No external cron library dependency; implement a minimal parser
- Scheduler is polled (tick-based), not event-driven, matching Ark's tick loop model
- Task execution delegates to agent_runner which owns the agent lifecycle
- Delivery routing reuses Gateway's format_response for platform-specific output

## Dependencies
- design-dsl-surface (cron_task_def must be parseable)
- design-gateway-messaging (delivery uses gateway routing)

## Target Conditions
- TC-018: Cron expression parsing correctly computes next run times
- TC-019: Scheduler.get_due_tasks returns correct tasks for a given timestamp
- TC-020: Scheduler.tick executes due tasks and updates last_run/next_run
