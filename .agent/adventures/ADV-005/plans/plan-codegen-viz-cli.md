# Codegen, Visualization, and CLI Integration

## Designs Covered
- design-codegen: Agent code generation
- design-visualization: Agent architecture visualization

## Tasks

### Create agent codegen module
- **ID**: ADV005-T014
- **Description**: Create `tools/codegen/agent_codegen.py` with 5 generators: gen_agent_config (YAML), gen_gateway_routes (YAML), gen_cron_entries (crontab), gen_skill_markdown (agentskills.io format), gen_docker_compose (docker-compose fragment). Follow studio_codegen.py pattern.
- **Files**: ark/tools/codegen/agent_codegen.py
- **Acceptance Criteria**:
  - gen_agent_config produces valid YAML from agent + model_config
  - gen_gateway_routes produces valid YAML from gateway + platforms
  - gen_cron_entries produces valid crontab format
  - gen_skill_markdown produces agentskills.io-compatible .md
  - gen_docker_compose produces valid docker-compose fragment
  - gen_agent entry point generates all artifacts
- **Target Conditions**: TC-030, TC-031, TC-032, TC-033, TC-034
- **Depends On**: [ADV005-T005]
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: python, yaml
  - Estimated duration: 30min
  - Estimated tokens: 40000

### Add CLI integration for agent subcommands
- **ID**: ADV005-T015
- **Description**: Add `ark agent codegen` and `ark agent verify` subcommands to ark.py. Wire agent_codegen and agent_verify modules. Update sys.path to include tools/agent/.
- **Files**: ark/ark.py
- **Acceptance Criteria**:
  - `ark agent codegen <file> [--out <dir>]` generates agent artifacts
  - `ark agent verify <file>` runs agent verification checks
  - Existing CLI commands unchanged
  - Help text updated
- **Target Conditions**: TC-030, TC-024
- **Depends On**: [ADV005-T012, ADV005-T014]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python
  - Estimated duration: 15min
  - Estimated tokens: 15000

### Extend visualizer for agent architecture
- **ID**: ADV005-T016
- **Description**: Extend `tools/visualizer/ark_visualizer.py` to detect agent items in AST and generate agent-specific graph nodes and edges. Add color scheme for agent, platform, gateway, backend, skill, model_config, cron_task nodes.
- **Files**: ark/tools/visualizer/ark_visualizer.py
- **Acceptance Criteria**:
  - Agent items detected in AST
  - Graph nodes created with correct colors and labels
  - Edges created between agent, gateway, platform, backend nodes
  - Skills grouped by status in graph
  - HTML output renders correctly
- **Target Conditions**: TC-035, TC-036
- **Depends On**: [ADV005-T005]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, html, d3js
  - Estimated duration: 25min
  - Estimated tokens: 30000
