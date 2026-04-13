## Entities

### RoleDef
- kind: String ("role")
- name: String (unique identifier)
- inherits: [String] (parent role names)
- tier: Int (1=Director, 2=Lead, 3=Specialist)
- responsibilities: [String] (list of responsibility descriptions)
- escalates_to: String? (name of superior role, null for top)
- skills: [String] (skill identifiers)
- tools: [String] (AgentTool enum values)
- data_fields: [DataField] (same as entity data_fields)
- in_ports: [InPort]
- out_ports: [OutPort]
- processes: [ProcessRule]
- description: String?
- Relations: belongs to StudioDef via tier_group membership

### TierGroup
- level: Int (1, 2, or 3)
- members: [String] (role names in this tier)
- Relations: contained by StudioDef

### StudioDef
- kind: String ("studio")
- name: String (unique identifier)
- tiers: [TierGroup] (ordered tier groupings)
- contains: [String] (flat list of all role names — derived from tiers)
- data_fields: [DataField]
- invariants: [Expr]
- processes: [ProcessRule]
- bridges: [BridgeDef]
- description: String?
- Relations: contains RoleDef via tiers; may contain BridgeDef

### CommandDef
- kind: String ("command")
- name: String (slash-command name, e.g. "start", "brainstorm")
- phase: String? (WorkflowPhase enum value)
- prompt: String? (the prompt template text)
- role: String? (required role name)
- output: String? (output schema/format identifier)
- data_fields: [DataField]
- description: String?
- Relations: references RoleDef via role field

### HookDef
- kind: String ("hook")
- name: String (unique identifier)
- event: String? (HookEvent enum value)
- pattern: String? (file glob pattern)
- action: String? (action description/script)
- data_fields: [DataField]
- description: String?
- Relations: standalone, no direct entity references

### RuleDef
- kind: String ("rule")
- name: String (unique identifier)
- path: String? (glob pattern for scoped files)
- constraint: String? (constraint expression as text)
- severity: String? (Severity enum value)
- data_fields: [DataField]
- description: String?
- Relations: standalone, path-scoped

### TemplateDef
- kind: String ("template")
- name: String (unique identifier)
- sections: [String] (required section names)
- bound_to: String? (role name this template is bound to)
- data_fields: [DataField]
- description: String?
- Relations: references RoleDef via bound_to

### ArkFile (extended)
- roles: {String: RoleDef} (name -> role index)
- studios: {String: StudioDef} (name -> studio index)
- commands: {String: CommandDef} (name -> command index)
- (existing fields unchanged)
