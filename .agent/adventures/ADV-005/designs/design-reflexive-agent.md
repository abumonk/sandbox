# Reflexive Agent Spec — Design

## Overview
Author an Ark spec that describes Ark's own `.agent/` pipeline as an agent system — modeling the existing roles, skills, and commands as `agent` + `skill` + `platform` + `gateway` items. Also author an exemplar multi-platform agent spec. Both serve as integration tests for the full agent pipeline.

## Target Files
- `ark/specs/infra/agent_system.ark` — Exemplar multi-platform autonomous agent spec
- `ark/specs/meta/ark_agent.ark` — Reflexive spec: Ark's own pipeline as an agent
- `ark/specs/root.ark` — Register both in SystemRegistry

## Approach

### Exemplar Agent Spec (`agent_system.ark`)
A complete autonomous agent with:
- 2 platforms (Terminal, Telegram)
- 1 gateway binding them
- 2 execution backends (Local, Docker)
- 1 model config with fallback chain
- 3 skills (search, code_gen, summarize)
- 1 learning config (Active mode)
- 2 cron tasks (daily report, weekly cleanup)
- 1 verify block with all agent checks

### Reflexive Spec (`ark_agent.ark`)
Model Ark's `.agent/` pipeline:
- Agent: "ark-pipeline" with persona describing the pipeline orchestrator
- Platforms: Terminal (stdin/stdout interaction)
- Skills: map existing role capabilities (planner, coder, reviewer) as skills
- Model config: opus for planning, sonnet for implementation
- Learning config: describes how the pipeline learns from adventure outcomes

### Registry Updates
```ark
registry SystemRegistry {
  // ... existing entries ...
  register AgentSystem    { phase: infra, priority: 40 }
  register ArkAgent       { phase: meta, priority: 3 }
}
```

### Design Decisions
- Exemplar spec exercises all 8 item types and all verify checks
- Reflexive spec demonstrates Ark describing its own tooling (same pattern as ADV-002 self-indexing, ADV-003 ark_studio)
- Both specs serve as integration test fixtures
- Verify blocks in both specs ensure referential integrity

## Dependencies
- design-dsl-surface (all 8 item types)
- design-verification (verify block semantics)
- design-codegen (generated artifacts from these specs)

## Target Conditions
- TC-037: agent_system.ark parses without errors
- TC-038: agent_system.ark passes all agent verification checks
- TC-039: ark_agent.ark parses without errors
- TC-040: ark_agent.ark passes all agent verification checks
- TC-041: Both specs registered in root.ark SystemRegistry
- TC-042: Codegen produces valid artifacts from agent_system.ark
