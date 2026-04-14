# DSL Surface for Agent Items — Design

## Overview
Extend the Ark grammar (both Lark and pest) and parser to support 8 new item types: `agent`, `platform`, `gateway`, `execution_backend`, `skill`, `learning_config`, `cron_task`, `model_config`. Each follows the established pattern of `keyword IDENT "{" body "}"` with domain-specific body members.

## Target Files
- `ark/tools/parser/ark_grammar.lark` — Add Lark EBNF rules for 8 new items
- `ark/dsl/grammar/ark.pest` — Mirror rules in pest PEG
- `ark/tools/parser/ark_parser.py` — Add dataclasses, transformer methods, ArkFile indices

## Approach

### Grammar Rules (Lark)

Add to the `item` rule:
```
item: ... | agent_def | platform_def | gateway_def | execution_backend_def
    | skill_def | learning_config_def | cron_task_def | model_config_def
```

#### 1. agent_def
```lark
agent_def: "agent" IDENT "{" agent_body "}"
agent_body: agent_member*
agent_member: persona_stmt
            | model_ref_stmt
            | capabilities_stmt
            | learning_ref_stmt
            | backends_stmt
            | data_field
            | description_stmt
            | in_port
            | out_port
            | process_rule

persona_stmt: "persona:" STRING
model_ref_stmt: "model:" IDENT
capabilities_stmt: "capabilities:" "[" ident_list "]"
learning_ref_stmt: "learning:" IDENT
backends_stmt: "backends:" "[" ident_list "]"
```

#### 2. platform_def
```lark
platform_def: "platform" IDENT "{" platform_body "}"
platform_body: platform_member*
platform_member: platform_type_stmt
               | auth_stmt
               | format_stmt
               | data_field
               | description_stmt

platform_type_stmt: "type:" IDENT
auth_stmt: "auth:" STRING
format_stmt: "format:" IDENT
```

#### 3. gateway_def
```lark
gateway_def: "gateway" IDENT "{" gateway_body "}"
gateway_body: gateway_member*
gateway_member: agent_ref_stmt
              | platforms_stmt
              | routes_stmt
              | data_field
              | description_stmt
              | in_port
              | out_port
              | process_rule

agent_ref_stmt: "agent:" IDENT
platforms_stmt: "platforms:" "[" ident_list "]"
routes_stmt: "routes:" "[" route_entry ("," route_entry)* "]"
route_entry: IDENT "->" IDENT
```

#### 4. execution_backend_def
```lark
execution_backend_def: "execution_backend" IDENT "{" exec_backend_body "}"
exec_backend_body: exec_backend_member*
exec_backend_member: backend_type_stmt
                   | connection_stmt
                   | limits_stmt
                   | data_field
                   | description_stmt

backend_type_stmt: "backend_type:" IDENT
connection_stmt: "connection:" STRING
limits_stmt: "limits:" "{" limit_entry ("," limit_entry)* "}"
limit_entry: IDENT ":" expr
```

#### 5. skill_def
```lark
skill_def: "skill" IDENT "{" skill_body "}"
skill_body: skill_member*
skill_member: trigger_stmt
            | steps_stmt
            | status_stmt
            | improvement_stmt
            | data_field
            | description_stmt

trigger_stmt: "trigger:" STRING
steps_stmt: "steps:" "[" string_list "]"
status_stmt: "status:" IDENT
improvement_stmt: "improvement:" "{" meta_pair_list "}"
```

#### 6. learning_config_def
```lark
learning_config_def: "learning_config" IDENT "{" learning_body "}"
learning_body: learning_member*
learning_member: mode_stmt
               | skill_gen_stmt
               | memory_persist_stmt
               | session_search_stmt
               | self_improve_stmt
               | data_field
               | description_stmt

mode_stmt: "mode:" IDENT
skill_gen_stmt: "skill_generation:" expr
memory_persist_stmt: "memory_persist:" expr
session_search_stmt: "session_search:" expr
self_improve_stmt: "self_improve:" expr
```

#### 7. cron_task_def
```lark
cron_task_def: "cron_task" IDENT "{" cron_body "}"
cron_body: cron_member*
cron_member: schedule_stmt
           | agent_ref_stmt
           | platform_delivery_stmt
           | action_stmt
           | data_field
           | description_stmt

schedule_stmt: "schedule:" STRING
platform_delivery_stmt: "deliver_to:" IDENT
```

#### 8. model_config_def
```lark
model_config_def: "model_config" IDENT "{" model_config_body "}"
model_config_body: model_config_member*
model_config_member: provider_stmt
                   | model_id_stmt
                   | fallback_stmt
                   | params_stmt
                   | cost_limit_stmt
                   | data_field
                   | description_stmt

provider_stmt: "provider:" IDENT
model_id_stmt: "model_id:" STRING
fallback_stmt: "fallback:" IDENT
params_stmt: "params:" "{" meta_pair_list "}"
cost_limit_stmt: "cost_limit:" expr
```

### Parser Dataclasses

Add 8 new dataclasses (AgentDef, PlatformDef, GatewayDef, ExecutionBackendDef, SkillDef, LearningConfigDef, CronTaskDef, ModelConfigDef) following the pattern of RoleDef/StudioDef/CommandDef from ADV-003.

### ArkFile Extensions

Add new indices:
```python
agents: dict      # name -> AgentDef
platforms: dict   # name -> PlatformDef
gateways: dict    # name -> GatewayDef
backends: dict    # name -> ExecutionBackendDef
skills: dict      # name -> SkillDef
learning_configs: dict  # name -> LearningConfigDef
cron_tasks: dict  # name -> CronTaskDef
model_configs: dict     # name -> ModelConfigDef
```

### Pest Grammar

Mirror all Lark rules in pest PEG syntax with matching rule names per the dual-grammar parity pattern.

### Design Decisions
- Reuse existing grammar patterns: `agent_ref_stmt` reuses IDENT pattern
- `routes_stmt` uses arrow syntax `IDENT "->" IDENT` for readable routing
- `limits_stmt` uses nested `{ key: value }` consistent with existing meta syntax
- `steps_stmt` reuses `string_list` from ADV-003 template sections
- All items support `data_field` and `description_stmt` for consistency

## Dependencies
- design-stdlib-agent-schema (types must exist before grammar references them)

## Target Conditions
- TC-003: Lark grammar parses all 8 new agent item types without error
- TC-004: Pest grammar mirrors all 8 new Lark rules
- TC-005: Parser produces correct AST dataclasses for each item type
- TC-006: ArkFile indices populated for agents, platforms, gateways, backends, skills, learning_configs, cron_tasks, model_configs
- TC-007: Existing .ark files still parse without regression
