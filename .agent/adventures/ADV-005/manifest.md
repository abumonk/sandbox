---
id: ADV-005
title: Hermes-style Autonomous Agent System in Ark DSL
state: completed
created: 2026-04-13T00:00:00Z
updated: 2026-04-13T19:30:00Z
tasks: [ADV005-T001, ADV005-T002, ADV005-T003, ADV005-T004, ADV005-T005, ADV005-T006, ADV005-T007, ADV005-T008, ADV005-T009, ADV005-T010, ADV005-T011, ADV005-T012, ADV005-T013, ADV005-T014, ADV005-T015, ADV005-T016, ADV005-T017, ADV005-T018, ADV005-T019, ADV005-T020, ADV005-T021]
depends_on: [ADV-003]
---

## Concept

Review the Hermes Agent project (https://github.com/NousResearch/hermes-agent) — an autonomous AI agent system with multi-platform messaging, persistent learning, procedural skill generation, and flexible execution backends — and define/implement an Ark-native equivalent.

### What Hermes Agent does

- **Purpose**: autonomous conversational AI agent that grows with users, executing complex tasks across platforms with minimal human intervention.
- **Multi-platform messaging gateway**: unified handler for Terminal TUI, Telegram, Discord, Slack, WhatsApp, and Signal — users interact from any channel simultaneously.
- **Learning system**:
  - Persistent memory across sessions.
  - Autonomous skill generation after complex tasks — procedural knowledge is created from experience.
  - Session search for contextual understanding of users over time.
  - Self-improvement loop: creates skills, improves them during use, persists knowledge.
- **Model flexibility**: switch between LLM providers (Nous Portal, OpenRouter, OpenAI, Anthropic) via simple commands without code changes.
- **Execution backends**: 6 terminal backends — local, Docker, SSH, Daytona, Singularity, Modal — from $5 VPS to enterprise GPU clusters.
- **Skills system**: procedural memory compatible with agentskills.io standard.
- **Cron scheduler**: built-in task automation with platform delivery.
- **MCP integration**: external tools through Model Context Protocol.
- **Terminal UI**: full TUI with multiline editing, slash-command autocomplete, streaming output.

### Goal in Ark

Define and implement an **autonomous agent runtime subsystem as an Ark island** so that Ark can describe, configure, and orchestrate autonomous agents with multi-platform messaging, learning loops, and flexible execution — all through declarative specs verified by the Ark pipeline.

Concretely:

- **DSL surface** — introduce Ark items to describe:
  - `agent` — a named autonomous agent with persona, model config, capabilities, and learning settings.
  - `platform` — a messaging platform endpoint (terminal, telegram, discord, slack, etc.) with auth config and routing rules.
  - `gateway` — a unified messaging gateway binding an agent to multiple platforms with message routing and format adaptation.
  - `execution_backend` — a runtime environment (local, docker, ssh, cloud) with resource limits and connection config.
  - `skill` — a procedural knowledge unit with trigger conditions, steps, and improvement history.
  - `learning_config` — settings for skill generation, memory persistence, session search, and self-improvement loops.
  - `cron_task` — scheduled automation with platform delivery target and execution context.
  - `model_config` — LLM provider configuration with fallback chain, parameters, and cost limits.
- **Schema** — Ark `struct`/`enum` definitions in `dsl/stdlib/agent.ark` for: Platform, BackendType, ModelProvider, SkillStatus, MessageFormat, LearningMode, CronSchedule, GatewayRoute.
- **Runtime framework** — `tools/agent/` containing:
  - `gateway.py` — multi-platform message routing (simplified: stdin/stdout + webhook patterns).
  - `skill_manager.py` — skill CRUD, trigger matching, improvement loop.
  - `learning.py` — session memory, skill generation from traces, self-improvement scoring.
  - `backend.py` — execution backend abstraction (local + docker for v1).
  - `scheduler.py` — cron-based task scheduling with delivery routing.
  - `agent_runner.py` — orchestrates agent lifecycle: init → listen → process → learn → persist.
- **Reflexive use-case** — describe Ark's own `.agent/` pipeline as an agent spec:
  - Model the existing roles, skills, and commands as `agent` + `skill` items.
  - Generate agent runner config from the spec.
- **Verification** — Z3 checks:
  - Every gateway references valid platforms and a valid agent.
  - Every cron_task references a valid agent and platform for delivery.
  - Model fallback chains have no cycles.
  - Execution backend resource limits are positive and within bounds.
  - Skill trigger conditions don't overlap ambiguously.
- **Codegen** — generate:
  - Agent configuration YAML/JSON from `agent` + `model_config` items.
  - Gateway routing tables from `gateway` specs.
  - Cron entries from `cron_task` items.
  - Skill markdown files from `skill` items.
  - Docker compose fragments from `execution_backend` specs.
- **Visualization** — extend the visualizer to render agent architecture: agent ↔ gateway ↔ platforms, with execution backend and skill inventory.

### Why this matters

ADV-003 formalized team structure (roles, studios, commands). ADV-004 adds self-evolution. This adventure adds the **runtime agent layer** — the actual autonomous agent that executes tasks, learns from experience, and communicates across platforms. Together they form a complete agent lifecycle: structure (ADV-003) → runtime (ADV-005) → evolution (ADV-004).

## Target Conditions
| ID | Description | Source | Design | Plan | Task(s) | Proof Method | Proof Command | Status |
|----|-------------|--------|--------|------|---------|-------------|---------------|--------|
| TC-001 | stdlib/agent.ark parses without errors | concept | design-stdlib-agent-schema | plan-foundation | T002 | autotest | `pytest tests/test_agent_schema.py::test_agent_ark_parses` | pending |
| TC-002 | All agent enum/struct definitions well-formed and referenceable | concept | design-stdlib-agent-schema | plan-foundation | T002 | autotest | `pytest tests/test_agent_schema.py::test_agent_types_complete` | pending |
| TC-003 | Lark grammar parses all 8 new agent item types | concept | design-dsl-surface | plan-foundation | T003 | autotest | `pytest tests/test_agent_parser.py::test_lark_agent_items` | pending |
| TC-004 | Pest grammar mirrors all 8 new Lark rules | concept | design-dsl-surface | plan-foundation | T004 | poc | `grep -c "agent_def\|platform_def\|gateway_def\|execution_backend_def\|skill_def\|learning_config_def\|cron_task_def\|model_config_def" ark/dsl/grammar/ark.pest` | pending |
| TC-005 | Parser produces correct AST dataclasses for each agent item | concept | design-dsl-surface | plan-foundation | T005 | autotest | `pytest tests/test_agent_parser.py::test_parser_dataclasses` | pending |
| TC-006 | ArkFile indices populated for all 8 agent item types | concept | design-dsl-surface | plan-foundation | T005 | autotest | `pytest tests/test_agent_parser.py::test_arkfile_indices` | pending |
| TC-007 | Existing .ark files still parse without regression | concept | design-dsl-surface | plan-foundation | T003,T020 | autotest | `pytest tests/test_parser_smoke.py` | pending |
| TC-008 | Gateway normalizes terminal input to Message dataclass | concept | design-gateway-messaging | plan-runtime | T006 | autotest | `pytest tests/test_agent_gateway.py::test_normalize_terminal` | pending |
| TC-009 | Gateway route matching works with priority ordering | concept | design-gateway-messaging | plan-runtime | T006 | autotest | `pytest tests/test_agent_gateway.py::test_route_priority` | pending |
| TC-010 | Gateway formats responses per platform format spec | concept | design-gateway-messaging | plan-runtime | T006 | autotest | `pytest tests/test_agent_gateway.py::test_format_response` | pending |
| TC-011 | LocalBackend executes a command and returns ExecutionResult | concept | design-execution-backends | plan-runtime | T007 | autotest | `pytest tests/test_agent_backend.py::test_local_execute` | pending |
| TC-012 | DockerBackend constructs correct docker run command with limits | concept | design-execution-backends | plan-runtime | T007 | autotest | `pytest tests/test_agent_backend.py::test_docker_command` | pending |
| TC-013 | backend_from_spec dispatches to Local/Docker backends | concept | design-execution-backends | plan-runtime | T007 | autotest | `pytest tests/test_agent_backend.py::test_factory_dispatch` | pending |
| TC-014 | SkillManager matches triggers correctly with priority ordering | concept | design-skill-learning | plan-runtime | T008 | autotest | `pytest tests/test_agent_skill.py::test_trigger_match_priority` | pending |
| TC-015 | SkillManager CRUD operations work correctly | concept | design-skill-learning | plan-runtime | T008 | autotest | `pytest tests/test_agent_skill.py::test_skill_crud` | pending |
| TC-016 | LearningEngine records sessions and searches by query | concept | design-skill-learning | plan-runtime | T009 | autotest | `pytest tests/test_agent_skill.py::test_learning_session_search` | pending |
| TC-017 | LearningEngine generates a skill from execution trace | concept | design-skill-learning | plan-runtime | T009 | autotest | `pytest tests/test_agent_skill.py::test_skill_generation` | pending |
| TC-018 | Cron expression parsing correctly computes next run times | concept | design-scheduler | plan-runtime | T010 | autotest | `pytest tests/test_agent_scheduler.py::test_cron_parse` | pending |
| TC-019 | Scheduler.get_due_tasks returns correct tasks for timestamp | concept | design-scheduler | plan-runtime | T010 | autotest | `pytest tests/test_agent_scheduler.py::test_due_tasks` | pending |
| TC-020 | Scheduler.tick executes due tasks and updates timestamps | concept | design-scheduler | plan-runtime | T010 | autotest | `pytest tests/test_agent_scheduler.py::test_tick_execution` | pending |
| TC-021 | AgentRunner initializes all subsystems from config | concept | design-agent-runner | plan-runtime | T011 | autotest | `pytest tests/test_agent_runner.py::test_init_subsystems` | pending |
| TC-022 | AgentRunner.process_message routes through skill then fallback | concept | design-agent-runner | plan-runtime | T011 | autotest | `pytest tests/test_agent_runner.py::test_process_message` | pending |
| TC-023 | AgentRunner.tick delegates to scheduler | concept | design-agent-runner | plan-runtime | T011 | autotest | `pytest tests/test_agent_runner.py::test_tick_scheduler` | pending |
| TC-024 | Gateway references validated — invalid names caught | concept | design-verification | plan-verification | T012,T013,T015 | autotest | `pytest tests/test_agent_verify.py::test_gateway_refs` | pending |
| TC-025 | Cron task references validated — invalid names caught | concept | design-verification | plan-verification | T012 | autotest | `pytest tests/test_agent_verify.py::test_cron_refs` | pending |
| TC-026 | Model fallback cycles detected via Z3 ordinals | concept | design-verification | plan-verification | T012 | autotest | `pytest tests/test_agent_verify.py::test_fallback_cycle` | pending |
| TC-027 | Resource limit violations detected | concept | design-verification | plan-verification | T012 | autotest | `pytest tests/test_agent_verify.py::test_resource_limits` | pending |
| TC-028 | Skill trigger overlap warnings generated | concept | design-verification | plan-verification | T012 | autotest | `pytest tests/test_agent_verify.py::test_trigger_overlap` | pending |
| TC-029 | Agent completeness catches missing model/backend refs | concept | design-verification | plan-verification | T012 | autotest | `pytest tests/test_agent_verify.py::test_agent_completeness` | pending |
| TC-030 | Agent config YAML generated from agent + model_config specs | concept | design-codegen | plan-codegen-viz-cli | T014,T015 | autotest | `pytest tests/test_agent_codegen.py::test_agent_config_yaml` | pending |
| TC-031 | Gateway routing table YAML generated from gateway specs | concept | design-codegen | plan-codegen-viz-cli | T014 | autotest | `pytest tests/test_agent_codegen.py::test_gateway_routes_yaml` | pending |
| TC-032 | Cron entries generated in valid crontab format | concept | design-codegen | plan-codegen-viz-cli | T014 | autotest | `pytest tests/test_agent_codegen.py::test_cron_entries` | pending |
| TC-033 | Skill markdown generated in agentskills.io format | concept | design-codegen | plan-codegen-viz-cli | T014 | autotest | `pytest tests/test_agent_codegen.py::test_skill_markdown` | pending |
| TC-034 | Docker compose fragment generated from Docker backend specs | concept | design-codegen | plan-codegen-viz-cli | T014 | autotest | `pytest tests/test_agent_codegen.py::test_docker_compose` | pending |
| TC-035 | Visualizer generates graph data with agent nodes and edges | concept | design-visualization | plan-codegen-viz-cli | T016 | autotest | `pytest tests/test_agent_viz.py::test_agent_graph_data` | pending |
| TC-036 | HTML output renders agent architecture with colors and labels | concept | design-visualization | plan-codegen-viz-cli | T016 | autotest | `pytest tests/test_agent_viz.py::test_agent_html_output` | pending |
| TC-037 | agent_system.ark parses without errors | concept | design-reflexive-agent | plan-specs-integration | T017,T020 | autotest | `pytest tests/test_agent_integration.py::test_agent_system_parses` | pending |
| TC-038 | agent_system.ark passes all agent verification checks | concept | design-reflexive-agent | plan-specs-integration | T017,T020 | autotest | `pytest tests/test_agent_integration.py::test_agent_system_verifies` | pending |
| TC-039 | ark_agent.ark parses without errors | concept | design-reflexive-agent | plan-specs-integration | T018,T020 | autotest | `pytest tests/test_agent_integration.py::test_ark_agent_parses` | pending |
| TC-040 | ark_agent.ark passes all agent verification checks | concept | design-reflexive-agent | plan-specs-integration | T018,T020 | autotest | `pytest tests/test_agent_integration.py::test_ark_agent_verifies` | pending |
| TC-041 | Both specs registered in root.ark SystemRegistry | concept | design-reflexive-agent | plan-specs-integration | T019 | autotest | `pytest tests/test_agent_integration.py::test_registry_updated` | pending |
| TC-042 | Codegen produces valid artifacts from agent_system.ark | concept | design-reflexive-agent | plan-specs-integration | T017,T020 | autotest | `pytest tests/test_agent_integration.py::test_agent_codegen_e2e` | pending |
| TC-043 | Test strategy document covers all target conditions | design | all | plan-test-strategy | T001 | manual | review tests/test-strategy.md | pending |
| TC-044 | All automated tests pass | design | all | plan-testing | T021 | autotest | `pytest tests/test_agent_*.py` | pending |

## Evaluations
| Task | Access Requirements | Skill Set | Est. Duration | Est. Tokens | Est. Cost | Actual Duration | Actual Tokens | Actual Cost | Variance |
|------|-------------------|-----------|---------------|-------------|-----------|-----------------|---------------|-------------|----------|
| ADV005-T001 | Read, Write, Glob, Grep | test design, pytest | 20min | 20000 | $0.30 | - | - | - | - |
| ADV005-T002 | Read, Write, Bash | ark-dsl | 15min | 12000 | $0.18 | - | - | - | - |
| ADV005-T003 | Read, Write, Bash | lark-grammar, ark-dsl | 25min | 30000 | $0.45 | - | - | - | - |
| ADV005-T004 | Read, Write | pest-peg, ark-dsl | 20min | 25000 | $0.38 | - | - | - | - |
| ADV005-T005 | Read, Write, Bash | python, lark-parser | 30min | 45000 | $0.68 | - | - | - | - |
| ADV005-T006 | Read, Write | python | 25min | 30000 | $0.45 | - | - | - | - |
| ADV005-T007 | Read, Write | python, subprocess | 20min | 25000 | $0.38 | - | - | - | - |
| ADV005-T008 | Read, Write | python, regex | 25min | 30000 | $0.45 | - | - | - | - |
| ADV005-T009 | Read, Write | python | 25min | 30000 | $0.45 | - | - | - | - |
| ADV005-T010 | Read, Write | python, cron | 25min | 30000 | $0.45 | - | - | - | - |
| ADV005-T011 | Read, Write | python | 25min | 35000 | $0.53 | - | - | - | - |
| ADV005-T012 | Read, Write, Bash | python, z3-solver | 30min | 45000 | $0.68 | - | - | - | - |
| ADV005-T013 | Read, Write, Bash | python | 15min | 15000 | $0.23 | - | - | - | - |
| ADV005-T014 | Read, Write | python, yaml | 30min | 40000 | $0.60 | - | - | - | - |
| ADV005-T015 | Read, Write, Bash | python | 15min | 15000 | $0.23 | - | - | - | - |
| ADV005-T016 | Read, Write, Bash | python, html, d3js | 25min | 30000 | $0.45 | - | - | - | - |
| ADV005-T017 | Read, Write, Bash | ark-dsl | 25min | 30000 | $0.45 | - | - | - | - |
| ADV005-T018 | Read, Write, Bash | ark-dsl | 20min | 25000 | $0.38 | - | - | - | - |
| ADV005-T019 | Read, Write, Bash | ark-dsl | 10min | 8000 | $0.12 | - | - | - | - |
| ADV005-T020 | Read, Bash | ark-cli | 15min | 15000 | $0.23 | - | - | - | - |
| ADV005-T021 | Read, Write, Bash | python, pytest, z3 | 30min | 60000 | $0.90 | - | - | - | - |
| **TOTAL** | | | **470min** | **565000** | **$8.48** | - | - | - | - |

## Environment
- **Project**: ARK (Architecture Kernel) — declarative MMO game-engine DSL
- **Workspace**: R:/Sandbox (Ark tree at R:/Sandbox/ark)
- **Repo**: local (no git remote)
- **Branch**: local (not a git repo)
- **PC**: TTT
- **Platform**: Windows 11 Pro 10.0.26200
- **Runtime**: Node v24.12.0 (project runtime: Python 3 + Rust/Cargo)
- **Shell**: bash
