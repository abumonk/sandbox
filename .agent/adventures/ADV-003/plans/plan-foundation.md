# Foundation — Grammar, Parser, Stdlib

## Designs Covered
- design-grammar-extensions: Grammar extensions for studio hierarchy items
- design-parser-support: Parser AST dataclasses and transformer
- design-stdlib-schema: Stdlib type definitions for studio entities

## Tasks

### Design test strategy for Studio Hierarchy
- **ID**: ADV003-T001
- **Description**: Design automated tests covering all target conditions. Create test strategy document mapping TCs to test files, frameworks, and commands.
- **Files**: tests/test-strategy.md
- **Acceptance Criteria**:
  - Test strategy document exists at tests/test-strategy.md
  - All target conditions are mapped to specific test cases
  - Test approach, tooling, and coverage expectations are defined
- **Target Conditions**: TC-028
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read, Write, Glob, Grep
  - Skill set: test design, pytest
  - Estimated duration: 15min
  - Estimated tokens: 15000

### Create stdlib/studio.ark type definitions
- **ID**: ADV003-T002
- **Description**: Create the studio stdlib file with enum and struct definitions for Tier, AgentTool, HookEvent, Severity, WorkflowPhase, EscalationPath, Skill, CommandOutput.
- **Files**: dsl/stdlib/studio.ark
- **Acceptance Criteria**:
  - All enums and structs defined and well-formed
  - File parses via `python ark.py parse dsl/stdlib/studio.ark`
  - Types are consistent with existing stdlib patterns (types.ark)
- **Target Conditions**: TC-008, TC-009
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: ark-dsl
  - Estimated duration: 15min
  - Estimated tokens: 12000

### Extend Lark grammar with studio item rules
- **ID**: ADV003-T003
- **Description**: Add grammar rules for role_def, studio_def, command_def, hook_def, rule_def, template_def to ark_grammar.lark. Update the item rule to include all 6 new alternatives.
- **Files**: tools/parser/ark_grammar.lark
- **Acceptance Criteria**:
  - All 6 new item rules are syntactically correct Lark EBNF
  - Existing .ark files still parse (no regressions)
  - New rules follow existing naming conventions
- **Target Conditions**: TC-001, TC-003
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: lark-grammar, ark-dsl
  - Estimated duration: 20min
  - Estimated tokens: 20000

### Extend pest grammar with studio item rules
- **ID**: ADV003-T004
- **Description**: Mirror the Lark grammar changes in dsl/grammar/ark.pest. Add pest PEG rules for all 6 new studio items.
- **Files**: dsl/grammar/ark.pest
- **Acceptance Criteria**:
  - Pest rules mirror Lark rules for all 6 items
  - Pest syntax is correct (compiles with pest if applicable)
  - Existing pest rules unchanged
- **Target Conditions**: TC-002
- **Depends On**: [ADV003-T003]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: pest-peg, ark-dsl
  - Estimated duration: 15min
  - Estimated tokens: 15000

### Add parser AST dataclasses and transformer for studio items
- **ID**: ADV003-T005
- **Description**: Add RoleDef, TierGroup, StudioDef, CommandDef, HookDef, RuleDef, TemplateDef dataclasses to ark_parser.py. Add transformer methods for all new grammar rules. Update ArkFile with roles/studios/commands indices and _build_indices().
- **Files**: tools/parser/ark_parser.py
- **Acceptance Criteria**:
  - All 7 new dataclasses added with correct fields
  - Transformer methods produce correct AST dicts
  - ArkFile indices populated for roles, studios, commands
  - `python ark.py parse` works on .ark files with studio items
- **Target Conditions**: TC-004, TC-005, TC-006, TC-007
- **Depends On**: [ADV003-T003]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, lark-parser, ark-dsl
  - Estimated duration: 25min
  - Estimated tokens: 35000
