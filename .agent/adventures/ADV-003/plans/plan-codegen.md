# Code Generation — Studio Artifacts

## Designs Covered
- design-codegen-agents: Code generation for agent definitions, commands, hooks, templates

## Tasks

### Implement studio codegen module
- **ID**: ADV003-T008
- **Description**: Create tools/codegen/studio_codegen.py with functions: gen_agent_md(), gen_command_md(), gen_hooks_json(), gen_template_md(). Each takes parsed AST items and returns generated file content. Add codegen_studio() orchestrator function.
- **Files**: tools/codegen/studio_codegen.py
- **Acceptance Criteria**:
  - gen_agent_md() produces valid agent .md with frontmatter
  - gen_command_md() produces valid command .md
  - gen_hooks_json() produces valid JSON fragment
  - gen_template_md() produces valid template skeleton
  - codegen_studio() writes all output files to specified directory
- **Target Conditions**: TC-015, TC-016, TC-017, TC-018
- **Depends On**: [ADV003-T005]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, codegen
  - Estimated duration: 25min
  - Estimated tokens: 30000

### Integrate studio target into ark.py CLI
- **ID**: ADV003-T009
- **Description**: Add `--target studio` option to ark.py codegen command. Wire it to call codegen_studio() from studio_codegen.py. Update help text and CLI argument handling.
- **Files**: ark.py, tools/codegen/ark_codegen.py
- **Acceptance Criteria**:
  - `python ark.py codegen file.ark --target studio --out dir/` works
  - Help text includes studio target
  - Error messages clear for missing studio items
- **Target Conditions**: TC-019
- **Depends On**: [ADV003-T008]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, cli
  - Estimated duration: 15min
  - Estimated tokens: 15000
