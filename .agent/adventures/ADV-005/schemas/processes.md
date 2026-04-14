## Processes

### ParseAgentItems
1. Lark grammar matches one of 8 agent item rules
2. Transformer method creates dataclass instance
3. ArkFile._build_indices() populates new index dicts
4. JSON serialization via to_json() includes new items
Error paths: ArkParseError if syntax invalid, KeyError if duplicate name

### VerifyAgentSpecs
1. Check if AST contains agent items (agents, gateways, platforms, etc.)
2. If yes, import agent_verify and call verify_agent(ast)
3. verify_agent runs 6 checks in sequence:
   a. verify_gateway_references — gateway.agent and gateway.platforms exist
   b. verify_cron_references — cron_task.agent and cron_task.deliver_to exist
   c. verify_model_fallback_acyclicity — Z3 ordinal check on fallback chain
   d. verify_resource_limits — Z3 bound check on backend limits
   e. verify_skill_trigger_overlap — Z3 string regex intersection (warning-only)
   f. verify_agent_completeness — agent has valid model and backend refs
4. Return list of {check, status, message} dicts
Error paths: Z3 timeout on complex trigger patterns (bounded to 5s)

### CodegenAgentArtifacts
1. Parse .ark file to get ArkFile AST
2. Call gen_agent(ark_file, out_dir)
3. gen_agent dispatches to 5 generators:
   a. gen_agent_config — YAML from agent + model_config
   b. gen_gateway_routes — YAML from gateway + platforms
   c. gen_cron_entries — crontab from cron_tasks
   d. gen_skill_markdown — .md from skills
   e. gen_docker_compose — docker-compose fragment from Docker backends
4. Write files to out_dir or print to stdout
Error paths: Missing references resolved during verify (codegen assumes valid AST)

### GatewayMessageFlow
1. Platform adapter receives raw message
2. Gateway.normalize() converts to unified Message
3. Gateway.route() matches message against priority-ordered route patterns
4. Agent processes message (skill check -> model fallback)
5. Gateway.format_response() adapts response for target platform
6. Response delivered to platform
Error paths: No route match (use default route), platform adapter unavailable

### SkillLifecycle
1. SkillManager loads skills from JSON files
2. On message, match_trigger() checks context against all skill triggers
3. If match found, execute_skill() runs steps sequentially
4. After execution, LearningEngine.record_session() persists trace
5. If LearningMode >= Active, LearningEngine.generate_skill_from_trace() may create new skill
6. If LearningMode == Autonomous, LearningEngine.self_improve_loop() may improve existing skills
7. SkillManager.persist() saves updated skills
Error paths: Trigger conflict (logged as warning), skill step failure (recorded, not fatal)

### SchedulerTickLoop
1. Scheduler.tick(now) called periodically
2. get_due_tasks(now) returns tasks where next_run <= now
3. For each due task, execute_task() delegates to agent_runner
4. Agent processes action, result formatted for delivery platform
5. last_run and next_run updated for the task
Error paths: Agent execution failure (logged, task rescheduled), delivery failure (retried on next tick)

### AgentRunnerLifecycle
1. init(): load config, build subsystems from specs, restore persisted state
2. listen loop: receive messages from gateway, process each
3. process_message(): skill check -> model fallback -> record session -> learn
4. tick(): scheduler + maintenance
5. persist(): save skills, sessions, scheduler state
6. shutdown(): persist + cleanup
Error paths: Subsystem init failure (log + disable subsystem), persistence failure (log + retry)

### VisualizeAgentArchitecture
1. Parse .ark file to AST
2. generate_graph_data() detects agent items
3. Create nodes for agents, platforms, gateways, backends, skills, model configs, cron tasks
4. Create edges for references between items
5. Generate HTML with D3.js force graph
Error paths: No agent items found (renders standard graph without agent nodes)
