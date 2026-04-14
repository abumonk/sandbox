# Agent Runner and Lifecycle — Design

## Overview
Implement `tools/agent/agent_runner.py` — the orchestrator for agent lifecycle: init, listen, process, learn, persist. This is the top-level runtime that wires together gateway, backends, skills, learning, and scheduler into a coherent agent runtime.

## Target Files
- `ark/tools/agent/agent_runner.py` — Agent lifecycle orchestrator

## Approach

### Architecture
```
AgentRunner
  ├── Gateway (messaging)
  ├── ExecutionBackend (command execution)
  ├── SkillManager (procedural knowledge)
  ├── LearningEngine (memory + improvement)
  ├── Scheduler (cron tasks)
  └── ModelConfig (LLM provider)
```

### Core Class

```python
@dataclass
class AgentConfig:
    name: str
    persona: str
    model_config: dict
    capabilities: list[str]
    learning_mode: str

class AgentRunner:
    def __init__(self, config: AgentConfig, gateway: Gateway,
                 backend: ExecutionBackend, skill_manager: SkillManager,
                 learning: LearningEngine, scheduler: Scheduler):
        self.config = config
        self.gateway = gateway
        self.backend = backend
        self.skills = skill_manager
        self.learning = learning
        self.scheduler = scheduler
        self._running = False
    
    def init(self):
        """Initialize all subsystems, load persisted state."""
        ...
    
    def process_message(self, message: Message) -> Message:
        """Core processing loop:
        1. Check skill triggers
        2. If skill matches, execute skill steps
        3. If no skill, delegate to model
        4. Record session for learning
        5. If learning mode >= Active, attempt skill generation
        """
        ...
    
    def tick(self, now: float):
        """Periodic tick: check scheduler, run maintenance."""
        self.scheduler.tick(now, self)
        ...
    
    def persist(self):
        """Save all state: skills, sessions, scheduler state."""
        ...
    
    def shutdown(self):
        """Graceful shutdown: persist and cleanup."""
        ...
```

### Agent from Spec
```python
def build_agent_runtime(agent_def: dict, specs: dict) -> AgentRunner:
    """Build complete AgentRunner from parsed agent_def and related specs.
    
    Resolves references:
    - agent.model -> model_config_def
    - agent.learning -> learning_config_def
    - agent.backends -> execution_backend_defs
    - gateway referencing this agent -> Gateway
    - cron_tasks referencing this agent -> Scheduler tasks
    - skill_defs -> SkillManager
    """
```

### Design Decisions
- AgentRunner is the single entry point; all subsystems are injected
- Process flow: skill-first (if trigger matches), model-fallback (if not)
- Learning happens post-processing: record session, optionally generate skill
- Tick-based scheduler integration aligns with Ark's tick loop model
- Persistence is file-based in v1 (JSON/JSONL)

## Dependencies
- design-gateway-messaging
- design-execution-backends
- design-skill-learning
- design-scheduler

## Target Conditions
- TC-021: AgentRunner initializes all subsystems from config
- TC-022: AgentRunner.process_message routes through skill check then model fallback
- TC-023: AgentRunner.tick delegates to scheduler correctly
