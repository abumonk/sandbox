## Entities

### AgentDef
- kind: String ("agent")
- name: String (unique identifier)
- persona: String (agent persona/system prompt)
- model: String (reference to ModelConfigDef name)
- capabilities: [String] (capability identifiers)
- learning: String? (reference to LearningConfigDef name)
- backends: [String] (references to ExecutionBackendDef names)
- data_fields: [DataField]
- in_ports: [InPort]
- out_ports: [OutPort]
- processes: [ProcessRule]
- description: String?
- Relations: references ModelConfigDef via model, LearningConfigDef via learning, ExecutionBackendDef via backends

### PlatformDef
- kind: String ("platform")
- name: String (unique identifier)
- platform_type: String (Platform enum value: Terminal, Telegram, Discord, Slack, WhatsApp, Signal, Webhook)
- auth: String? (auth configuration string)
- format: String? (MessageFormat enum value)
- data_fields: [DataField]
- description: String?
- Relations: referenced by GatewayDef and CronTaskDef

### GatewayDef
- kind: String ("gateway")
- name: String (unique identifier)
- agent: String (reference to AgentDef name)
- platforms: [String] (references to PlatformDef names)
- routes: [RouteEntry] (platform -> format routing rules)
- data_fields: [DataField]
- in_ports: [InPort]
- out_ports: [OutPort]
- processes: [ProcessRule]
- description: String?
- Relations: references AgentDef via agent, PlatformDef via platforms

### RouteEntry
- from_platform: String (PlatformDef name)
- to_handler: String (handler/format identifier)
- Relations: contained by GatewayDef

### ExecutionBackendDef
- kind: String ("execution_backend")
- name: String (unique identifier)
- backend_type: String (BackendType enum value: Local, Docker, SSH, Daytona, Singularity, Modal)
- connection: String? (connection string)
- limits: dict (resource limits: max_memory_mb, max_cpu_cores, max_disk_gb, timeout_seconds)
- data_fields: [DataField]
- description: String?
- Relations: referenced by AgentDef via backends

### SkillDef
- kind: String ("skill")
- name: String (unique identifier)
- trigger: String? (trigger pattern)
- steps: [String] (procedural steps)
- status: String? (SkillStatus enum value)
- improvement: dict? (improvement metadata)
- data_fields: [DataField]
- description: String?
- Relations: standalone, matched by trigger to agent context

### LearningConfigDef
- kind: String ("learning_config")
- name: String (unique identifier)
- mode: String? (LearningMode enum value: Passive, Active, Autonomous)
- skill_generation: Bool/Expr? (enable skill generation from traces)
- memory_persist: Bool/Expr? (enable persistent memory)
- session_search: Bool/Expr? (enable session search)
- self_improve: Bool/Expr? (enable self-improvement loop)
- data_fields: [DataField]
- description: String?
- Relations: referenced by AgentDef via learning

### CronTaskDef
- kind: String ("cron_task")
- name: String (unique identifier)
- schedule: String? (cron expression)
- agent: String? (reference to AgentDef name)
- deliver_to: String? (reference to PlatformDef name)
- action: String? (action description)
- data_fields: [DataField]
- description: String?
- Relations: references AgentDef via agent, PlatformDef via deliver_to

### ModelConfigDef
- kind: String ("model_config")
- name: String (unique identifier)
- provider: String? (ModelProvider enum value)
- model_id: String? (provider-specific model identifier)
- fallback: String? (reference to another ModelConfigDef name)
- params: dict? (model parameters: temperature, max_tokens, top_p)
- cost_limit: Float/Expr? (cost limit per invocation)
- data_fields: [DataField]
- description: String?
- Relations: references ModelConfigDef via fallback (forms chain)

### ArkFile (extended)
- agents: {String: AgentDef} (name -> agent index)
- platforms: {String: PlatformDef} (name -> platform index)
- gateways: {String: GatewayDef} (name -> gateway index)
- backends: {String: ExecutionBackendDef} (name -> backend index)
- skills: {String: SkillDef} (name -> skill index)
- learning_configs: {String: LearningConfigDef} (name -> learning config index)
- cron_tasks: {String: CronTaskDef} (name -> cron task index)
- model_configs: {String: ModelConfigDef} (name -> model config index)
- (existing fields unchanged)
