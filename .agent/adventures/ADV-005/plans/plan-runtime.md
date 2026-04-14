# Runtime — Gateway, Backends, Skills, Learning, Scheduler, Agent Runner

## Designs Covered
- design-gateway-messaging: Multi-platform gateway
- design-execution-backends: Execution backend abstraction
- design-skill-learning: Skill and learning system
- design-scheduler: Cron scheduler
- design-agent-runner: Agent lifecycle orchestrator

## Tasks

### Implement gateway messaging module
- **ID**: ADV005-T006
- **Description**: Create `tools/agent/__init__.py` and `tools/agent/gateway.py` with Message dataclass, GatewayRoute, Gateway class (normalize, route, format_response, dispatch), TerminalAdapter, WebhookAdapter stub, and gateway_from_spec factory.
- **Files**: ark/tools/agent/__init__.py, ark/tools/agent/gateway.py
- **Acceptance Criteria**:
  - Message and GatewayRoute dataclasses defined
  - Gateway.normalize() converts terminal input to Message
  - Gateway.route() matches messages with priority ordering
  - Gateway.format_response() adapts output per platform
  - gateway_from_spec() builds Gateway from parsed spec
- **Target Conditions**: TC-008, TC-009, TC-010
- **Depends On**: [ADV005-T005]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: python
  - Estimated duration: 25min
  - Estimated tokens: 30000

### Implement execution backend module
- **ID**: ADV005-T007
- **Description**: Create `tools/agent/backend.py` with ExecutionResult, ExecutionBackend ABC, LocalBackend (subprocess.run), DockerBackend (docker run command builder), SSHBackend stub, and backend_from_spec factory.
- **Files**: ark/tools/agent/backend.py
- **Acceptance Criteria**:
  - ExecutionBackend ABC with execute/check_health/get_resource_usage
  - LocalBackend executes commands via subprocess with timeout
  - DockerBackend constructs correct docker run commands
  - backend_from_spec dispatches correctly
- **Target Conditions**: TC-011, TC-012, TC-013
- **Depends On**: [ADV005-T005]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: python, subprocess
  - Estimated duration: 20min
  - Estimated tokens: 25000

### Implement skill manager module
- **ID**: ADV005-T008
- **Description**: Create `tools/agent/skill_manager.py` with Skill dataclass, SkillTrigger, SkillManager class (match_trigger, execute_skill, add_skill, improve_skill, deprecate_skill), and skill_from_spec factory. Includes file-based persistence (JSON).
- **Files**: ark/tools/agent/skill_manager.py
- **Acceptance Criteria**:
  - Skill and SkillTrigger dataclasses defined
  - match_trigger returns priority-ordered matches
  - CRUD operations work correctly
  - Skills persist to and load from JSON files
  - skill_from_spec builds Skill from parsed spec
- **Target Conditions**: TC-014, TC-015
- **Depends On**: [ADV005-T005]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: python, regex
  - Estimated duration: 25min
  - Estimated tokens: 30000

### Implement learning engine module
- **ID**: ADV005-T009
- **Description**: Create `tools/agent/learning.py` with SessionEntry dataclass, LearningEngine class (record_session, search_sessions, generate_skill_from_trace, score_skill, self_improve_loop), and learning_from_spec factory. Includes JSONL-based session persistence.
- **Files**: ark/tools/agent/learning.py
- **Acceptance Criteria**:
  - SessionEntry dataclass defined
  - record_session persists to JSONL file
  - search_sessions returns relevant entries by keyword match
  - generate_skill_from_trace extracts repeated patterns as skills
  - learning_from_spec builds LearningEngine from parsed spec
- **Target Conditions**: TC-016, TC-017
- **Depends On**: [ADV005-T008]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: python
  - Estimated duration: 25min
  - Estimated tokens: 30000

### Implement scheduler module
- **ID**: ADV005-T010
- **Description**: Create `tools/agent/scheduler.py` with ScheduledTask dataclass, Scheduler class (compute_next_run, get_due_tasks, execute_task, tick), cron expression parser, and scheduler_from_spec factory.
- **Files**: ark/tools/agent/scheduler.py
- **Acceptance Criteria**:
  - Cron expression parser handles standard 5-field syntax
  - compute_next_run returns correct next execution time
  - get_due_tasks returns tasks ready to execute
  - tick() executes due tasks and updates timestamps
  - scheduler_from_spec builds Scheduler from parsed specs
- **Target Conditions**: TC-018, TC-019, TC-020
- **Depends On**: [ADV005-T005]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: python, cron
  - Estimated duration: 25min
  - Estimated tokens: 30000

### Implement agent runner module
- **ID**: ADV005-T011
- **Description**: Create `tools/agent/agent_runner.py` with AgentConfig dataclass, AgentRunner class (init, process_message, tick, persist, shutdown), and build_agent_runtime factory that wires together Gateway, ExecutionBackend, SkillManager, LearningEngine, and Scheduler from specs.
- **Files**: ark/tools/agent/agent_runner.py
- **Acceptance Criteria**:
  - AgentRunner initializes all subsystems
  - process_message routes through skill check then fallback
  - tick delegates to scheduler
  - build_agent_runtime resolves all spec references
- **Target Conditions**: TC-021, TC-022, TC-023
- **Depends On**: [ADV005-T006, ADV005-T007, ADV005-T008, ADV005-T009, ADV005-T010]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: python
  - Estimated duration: 25min
  - Estimated tokens: 35000
