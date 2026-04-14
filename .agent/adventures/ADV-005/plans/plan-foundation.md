# Foundation — Schema, Grammar, Parser

## Designs Covered
- design-stdlib-agent-schema: Agent stdlib type definitions
- design-dsl-surface: Grammar and parser extensions for 8 agent items

## Tasks

### Create stdlib/agent.ark type definitions
- **ID**: ADV005-T002
- **Description**: Create `dsl/stdlib/agent.ark` with enum and struct definitions for Platform, BackendType, ModelProvider, SkillStatus, MessageFormat, LearningMode, CronSchedule, GatewayRoute, ModelParams, ResourceLimits, SkillTrigger, ImprovementEntry. Follow existing types.ark and studio.ark patterns.
- **Files**: ark/dsl/stdlib/agent.ark
- **Acceptance Criteria**:
  - All 6 enums and 6 structs defined and well-formed
  - File parses via `python ark.py parse dsl/stdlib/agent.ark`
  - Types are consistent with existing stdlib patterns
- **Target Conditions**: TC-001, TC-002
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: ark-dsl
  - Estimated duration: 15min
  - Estimated tokens: 12000

### Extend Lark grammar with agent item rules
- **ID**: ADV005-T003
- **Description**: Add grammar rules for agent_def, platform_def, gateway_def, execution_backend_def, skill_def, learning_config_def, cron_task_def, model_config_def to ark_grammar.lark. Update the item rule to include all 8 new alternatives. Add all supporting statement rules (persona_stmt, backend_type_stmt, provider_stmt, etc.).
- **Files**: ark/tools/parser/ark_grammar.lark
- **Acceptance Criteria**:
  - All 8 new item rules are syntactically correct Lark EBNF
  - All supporting statement rules added
  - Existing .ark files still parse (no regressions)
  - New rules follow existing naming conventions
- **Target Conditions**: TC-003, TC-007
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: lark-grammar, ark-dsl
  - Estimated duration: 25min
  - Estimated tokens: 30000

### Extend pest grammar with agent item rules
- **ID**: ADV005-T004
- **Description**: Mirror the Lark grammar changes in dsl/grammar/ark.pest. Add pest PEG rules for all 8 new agent items and supporting statements.
- **Files**: ark/dsl/grammar/ark.pest
- **Acceptance Criteria**:
  - Pest rules mirror Lark rules for all 8 items
  - Pest syntax is correct
  - Existing pest rules unchanged
- **Target Conditions**: TC-004
- **Depends On**: [ADV005-T003]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: pest-peg, ark-dsl
  - Estimated duration: 20min
  - Estimated tokens: 25000

### Add parser AST dataclasses for agent items
- **ID**: ADV005-T005
- **Description**: Add AgentDef, PlatformDef, GatewayDef, ExecutionBackendDef, SkillDef, LearningConfigDef, CronTaskDef, ModelConfigDef dataclasses to ark_parser.py. Add transformer methods for all new grammar rules. Update ArkFile with agents/platforms/gateways/backends/skills/learning_configs/cron_tasks/model_configs indices and _build_indices().
- **Files**: ark/tools/parser/ark_parser.py
- **Acceptance Criteria**:
  - All 8 new dataclasses added with correct fields
  - Transformer methods produce correct AST dicts
  - ArkFile indices populated for all 8 new item types
  - `python ark.py parse` works on .ark files with agent items
- **Target Conditions**: TC-005, TC-006
- **Depends On**: [ADV005-T003]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, lark-parser, ark-dsl
  - Estimated duration: 30min
  - Estimated tokens: 45000
