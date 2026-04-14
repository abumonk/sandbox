# Agent Codegen — Design

## Overview
Implement `tools/codegen/agent_codegen.py` — code generation from agent specs. Generates agent configuration YAML, gateway routing tables, cron entries, skill markdown files, and Docker compose fragments.

## Target Files
- `ark/tools/codegen/agent_codegen.py` — Agent codegen module (new)
- `ark/tools/codegen/ark_codegen.py` — Integration point (add agent target)
- `ark/ark.py` — CLI: add `ark agent codegen` subcommand

## Approach

### Generated Artifacts

#### 1. Agent Configuration YAML
From `agent` + `model_config` items:
```yaml
# agent_config.yaml
name: my_agent
persona: "You are a helpful assistant..."
model:
  provider: Anthropic
  model_id: claude-opus-4-5
  params:
    temperature: 0.7
    max_tokens: 4096
  fallback: fallback_model
capabilities: [search, code_execution, file_ops]
learning:
  mode: Active
  skill_generation: true
  memory_persist: true
```

#### 2. Gateway Routing Table
From `gateway` specs:
```yaml
# gateway_routes.yaml
agent: my_agent
platforms:
  - name: terminal
    type: Terminal
    format: text
  - name: telegram
    type: Telegram
    format: markdown
routes:
  - platform: terminal
    pattern: ".*"
    priority: 1
    format: text
```

#### 3. Cron Entries
From `cron_task` items:
```crontab
# agent_cron.txt
# my_daily_report — deliver to: telegram
0 9 * * 1 ark agent run my_agent --action "Generate weekly report" --deliver telegram
```

#### 4. Skill Markdown Files
From `skill` items (compatible with agentskills.io):
```markdown
# Skill: {name}

## Status: {status}
## Version: {version}
## Trigger
{trigger_pattern}
## Steps
1. {step1}
2. {step2}
## Improvement History
- v{N}: {notes} (score: {score})
```

#### 5. Docker Compose Fragment
From `execution_backend` specs with Docker type:
```yaml
# docker-compose.agent.yaml
services:
  agent_sandbox:
    image: ubuntu:22.04
    deploy:
      resources:
        limits:
          memory: 2048M
          cpus: '2.0'
    volumes:
      - ./workspace:/workspace
```

### CLI Integration
Add to `ark.py`:
```
ark agent codegen <file.ark> [--out <dir>]    -> generate agent artifacts
ark agent verify <file.ark>                   -> verify agent specs
```

### Code Structure
```python
def gen_agent_config(agent_def, model_configs) -> dict[str, str]:
    """Generate agent config YAML."""

def gen_gateway_routes(gateway_def, platforms) -> dict[str, str]:
    """Generate routing table YAML."""

def gen_cron_entries(cron_tasks) -> dict[str, str]:
    """Generate crontab-format entries."""

def gen_skill_markdown(skill_defs) -> dict[str, str]:
    """Generate skill .md files (agentskills.io compatible)."""

def gen_docker_compose(backends) -> dict[str, str]:
    """Generate docker-compose fragments for Docker backends."""

def gen_agent(ark_file, out_dir=None) -> dict[str, str]:
    """Entry point: generate all agent artifacts."""
```

### Design Decisions
- Follow studio_codegen.py pattern: separate module, called from ark.py
- YAML output for config files (human-readable, widely supported)
- Skill markdown follows agentskills.io standard for interop
- Docker compose fragment is mergeable (services section only)
- Crontab format for scheduling (standard, usable on any Unix)
- All generators return `{filename: content}` dict for consistent output

## Dependencies
- design-dsl-surface (all agent items must be parseable)
- design-stdlib-agent-schema (enum values for validation)

## Target Conditions
- TC-030: Agent config YAML generated correctly from agent + model_config specs
- TC-031: Gateway routing table YAML generated from gateway specs
- TC-032: Cron entries generated in valid crontab format
- TC-033: Skill markdown generated in agentskills.io-compatible format
- TC-034: Docker compose fragment generated from Docker backend specs
