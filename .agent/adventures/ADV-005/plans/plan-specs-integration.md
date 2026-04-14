# Specs and Integration

## Designs Covered
- design-reflexive-agent: Exemplar and reflexive agent specs

## Tasks

### Author exemplar agent_system.ark spec
- **ID**: ADV005-T017
- **Description**: Create `specs/infra/agent_system.ark` — a complete autonomous agent spec exercising all 8 item types: 1 agent, 2 platforms (Terminal, Telegram), 1 gateway, 2 execution backends (Local, Docker), 1 model config with fallback, 3 skills, 1 learning config, 2 cron tasks, and a verify block with all agent checks.
- **Files**: ark/specs/infra/agent_system.ark
- **Acceptance Criteria**:
  - Spec uses all 8 agent item types
  - File parses via `python ark.py parse`
  - All agent verification checks pass
  - Codegen produces valid artifacts
- **Target Conditions**: TC-037, TC-038, TC-042
- **Depends On**: [ADV005-T005, ADV005-T012, ADV005-T014]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: ark-dsl
  - Estimated duration: 25min
  - Estimated tokens: 30000

### Author reflexive ark_agent.ark spec
- **ID**: ADV005-T018
- **Description**: Create `specs/meta/ark_agent.ark` — model Ark's own `.agent/` pipeline as an agent system. Map pipeline roles to skills, commands to capabilities, and model the planning/implementation/review cycle as agent processes.
- **Files**: ark/specs/meta/ark_agent.ark
- **Acceptance Criteria**:
  - Spec models Ark pipeline as an agent system
  - File parses via `python ark.py parse`
  - All agent verification checks pass
- **Target Conditions**: TC-039, TC-040
- **Depends On**: [ADV005-T005, ADV005-T012]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: ark-dsl
  - Estimated duration: 20min
  - Estimated tokens: 25000

### Register agent specs in root.ark
- **ID**: ADV005-T019
- **Description**: Update `specs/root.ark` SystemRegistry to register AgentSystem (phase: infra, priority: 40) and ArkAgent (phase: meta, priority: 3).
- **Files**: ark/specs/root.ark
- **Acceptance Criteria**:
  - Both specs registered in SystemRegistry
  - root.ark still parses without error
  - No conflicts with existing registry entries
- **Target Conditions**: TC-041
- **Depends On**: [ADV005-T017, ADV005-T018]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: ark-dsl
  - Estimated duration: 10min
  - Estimated tokens: 8000

### End-to-end integration test run
- **ID**: ADV005-T020
- **Description**: Run the full pipeline on both agent specs: parse, verify, codegen, and graph. Verify all commands succeed. Run `python ark.py pipeline specs/infra/agent_system.ark` and `python ark.py agent verify specs/infra/agent_system.ark` and `python ark.py agent codegen specs/infra/agent_system.ark`. Check no regressions on existing specs.
- **Files**: (no new files — validation task)
- **Acceptance Criteria**:
  - Full pipeline succeeds on agent_system.ark
  - Full pipeline succeeds on ark_agent.ark
  - Agent verify succeeds on both specs
  - Agent codegen produces correct artifacts
  - Existing specs still parse and verify (no regression)
- **Target Conditions**: TC-037, TC-038, TC-039, TC-040, TC-042, TC-007
- **Depends On**: [ADV005-T015, ADV005-T017, ADV005-T018, ADV005-T019]
- **Evaluation**:
  - Access requirements: Read, Bash
  - Skill set: ark-cli
  - Estimated duration: 15min
  - Estimated tokens: 15000
