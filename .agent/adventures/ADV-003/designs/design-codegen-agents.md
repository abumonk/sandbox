# Code Generation for Studio Artifacts — Design

## Overview
Extend ark_codegen.py with a new codegen target `studio` that generates Claude Code agent definitions, command files, hook configurations, and template skeletons from studio .ark specs.

## Target Files
- `tools/codegen/ark_codegen.py` — Add studio codegen functions
- `tools/codegen/studio_codegen.py` — New module for studio-specific code generation

## Approach

### Output 1: Agent Definition Files (.md)
For each `role` item, generate a `.claude/agents/{role_name}.md` file:

```markdown
---
name: {role_name}
description: {role.description}
model: {derived from tier: Director=opus, Lead=opus, Specialist=sonnet}
tools: [{role.tools joined}]
---

You are the {role_name} agent.

## Tier
{tier_level} — {tier_description}

## Responsibilities
{role.responsibilities joined}

## Skills
{role.skills joined}

## Escalation
Reports to: {role.escalates_to}
```

### Output 2: Command Files (.md)
For each `command` item, generate a `.claude/commands/{command_name}.md`:

```markdown
# /{command_name}

Phase: {command.phase}
Role: {command.role}

{command.prompt}

## Output
{command.output}
```

### Output 3: Hook Configuration (JSON)
Collect all `hook` items and generate a `settings.json` fragment:

```json
{
  "hooks": {
    "{hook_name}": {
      "event": "{hook.event}",
      "pattern": "{hook.pattern}",
      "action": "{hook.action}"
    }
  }
}
```

### Output 4: Template Skeletons (.md)
For each `template` item, generate a template file:

```markdown
# {template_name}

{for each section in template.sections:}
## {section}

<!-- Required section — fill in content -->
```

### CLI Integration
Add `--target studio` to the codegen CLI:
```
python ark.py codegen specs/meta/ark_studio.ark --target studio --out generated/studio/
```

## Dependencies
- design-parser-support (need parsed studio AST)

## Target Conditions
- TC-015: Agent .md files generated correctly from role items
- TC-016: Command .md files generated correctly from command items
- TC-017: Hook settings.json fragment generated correctly
- TC-018: Template skeleton files generated correctly
- TC-019: `--target studio` CLI flag works end-to-end
