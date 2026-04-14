# ADV-005 Test Strategy — Hermes-style Autonomous Agent System

## Overview

This document maps every target condition (TC-001 through TC-044) from the ADV-005 manifest
to specific test files, test functions, proof commands, and test runners. Tests are grouped
by subsystem following the Ark project's existing conventions (established in ADV-001 through
ADV-004).

### Conventions (aligned with `R:/Sandbox/ark/tests/conftest.py`)

- **pytest** is the primary test runner for all Python code
- Fixtures `parse_src` and `parse_file` are session-scoped in `conftest.py`
- Test files follow `test_agent_{subsystem}.py` naming
- All test files live under `R:/Sandbox/ark/tests/`
- All commands assume `cd R:/Sandbox/ark` as working directory
- CLI tests use `subprocess.run(['python', 'ark.py', ...], cwd=REPO_ROOT)` and assert `returncode == 0`
- Unit tests use direct Python API calls (no subprocess overhead)
- `@pytest.mark.integration` marks tests requiring real spec files on disk
- A `REPO_ROOT` constant at the top of each test file points to `R:/Sandbox/ark/`

## Proof Methods

- **autotest** — automated pytest or CLI command with deterministic pass/fail
- **poc** — proof-of-concept command that must produce non-trivial output (human judges output)
- **manual** — human inspection of generated artifact

---

## Tests by Subsystem

### 1. Schema Tests — `tests/test_agent_schema.py`

Covers TC-001 and TC-002. Tests that `dsl/stdlib/agent.ark` parses without errors and that all
enum/struct definitions are well-formed and referenceable.

**Fixture approach**: Parse the real file at `dsl/stdlib/agent.ark` using `ArkParser`. Inspect
the returned `ArkFile` object for presence and correctness of all expected enum and struct items.
Additional functions verify each enum's variants individually.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-001 | `test_agent_ark_parses` | `dsl/stdlib/agent.ark` parses via `ArkParser` without raising exceptions; result is a non-None `ArkFile` |
| TC-002 | `test_agent_types_complete` | All 12 expected items present: enums `Platform`, `BackendType`, `ModelProvider`, `SkillStatus`, `MessageFormat`, `LearningMode`; structs `CronSchedule`, `GatewayRoute`, `AgentCapabilities`, `ModelConfig`, `ExecutionLimits`, `SkillTrigger` — verified by name lookup in `arkfile` |

Additional test functions (supporting TC-002):
- `test_platform_enum_variants` — `Platform` has `terminal`, `telegram`, `discord`, `slack`, `whatsapp`, `signal` variants
- `test_backend_type_enum_variants` — `BackendType` has `local`, `docker`, `ssh`, `daytona`, `singularity`, `modal` variants
- `test_model_provider_enum_variants` — `ModelProvider` has `nous_portal`, `openrouter`, `openai`, `anthropic` variants
- `test_skill_status_enum_variants` — `SkillStatus` has `draft`, `active`, `deprecated`, `improving` variants
- `test_message_format_enum_variants` — `MessageFormat` has `text`, `markdown`, `html`, `json` variants
- `test_learning_mode_enum_variants` — `LearningMode` has `passive`, `active`, `aggressive`, `disabled` variants

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_agent_schema.py::test_agent_ark_parses -q
cd R:/Sandbox/ark && pytest tests/test_agent_schema.py::test_agent_types_complete -q
cd R:/Sandbox/ark && pytest tests/test_agent_schema.py -q
```

---

### 2. Parser Tests — `tests/test_agent_parser.py`

Covers TC-003 through TC-007. Tests that the Lark grammar handles all 8 new agent item types,
that the Pest grammar mirrors them, that the parser produces correct AST dataclasses, that
`ArkFile` indices are populated, and that existing `.ark` files parse without regression.

**Fixture approach**: In-memory `.ark` snippet strings for each of the 8 item kinds. Parser
tests instantiate `ArkParser`, call `parse()` on the snippet, and assert no exception is raised.
AST tests assert field values on the returned dataclasses. Regression tests call the parser on
real files under `dsl/stdlib/` and `specs/`. Index tests parse a multi-item snippet and inspect
the `arkfile` attribute dict.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-003 | `test_lark_agent_items` | One snippet per item kind — `agent`, `platform`, `gateway`, `execution_backend`, `skill`, `learning_config`, `cron_task`, `model_config` — all parse without errors via the Lark grammar |
| TC-004 | (manual inspection) | Pest grammar `ark.pest` mirrors all 8 new Lark rules — human counts rule definitions |
| TC-005 | `test_parser_dataclasses` | Parsing each item kind snippet produces the correct AST dataclass: `AgentDef`, `PlatformDef`, `GatewayDef`, `ExecutionBackendDef`, `SkillDef`, `LearningConfigDef`, `CronTaskDef`, `ModelConfigDef` — key fields (name, body) match the input snippet |
| TC-006 | `test_arkfile_indices` | Parsing a multi-item `.ark` snippet populates `arkfile.agents`, `arkfile.platforms`, `arkfile.gateways`, `arkfile.execution_backends`, `arkfile.skills`, `arkfile.learning_configs`, `arkfile.cron_tasks`, `arkfile.model_configs` with correct name keys |
| TC-007 | `test_parser_smoke` | Representative existing `.ark` files (`specs/meta/ark_studio.ark`, `dsl/stdlib/studio.ark`, `dsl/stdlib/types.ark`) still parse after the grammar extension with no exceptions |

Additional test functions (supporting TC-003):
- `test_agent_item_fields` — parsed `AgentDef` has `name`, `persona`, `capabilities`, `model`, `learning` fields
- `test_gateway_item_fields` — parsed `GatewayDef` has `name`, `agent`, `platforms`, `routes` fields
- `test_skill_item_fields` — parsed `SkillDef` has `name`, `trigger`, `steps`, `status` fields
- `test_cron_task_item_fields` — parsed `CronTaskDef` has `name`, `schedule`, `agent`, `delivery_platform` fields

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_agent_parser.py::test_lark_agent_items -q
cd R:/Sandbox/ark && pytest tests/test_agent_parser.py::test_parser_dataclasses -q
cd R:/Sandbox/ark && pytest tests/test_agent_parser.py::test_arkfile_indices -q
cd R:/Sandbox/ark && pytest tests/test_agent_parser.py::test_parser_smoke -q
cd R:/Sandbox/ark && pytest tests/test_agent_parser.py -q
```

---

### 3. Gateway Tests — `tests/test_agent_gateway.py`

Covers TC-008 through TC-010. Tests that `tools/agent/gateway.py` normalizes platform-specific
input into the `Message` dataclass, that route matching respects priority ordering, and that
response formatting adapts to platform format specifications.

**Fixture approach**: Direct unit tests against `gateway.py` functions. `normalize_input()` is
called with simulated raw terminal input dicts. `route_message()` is called with a list of
`GatewayRoute` objects (constructed in-memory) and a `Message`. `format_response()` is called
with a `MessageFormat` enum value and a string payload. No external platform SDKs are involved.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-008 | `test_normalize_terminal` | `normalize_input(raw, platform="terminal")` with a `{"text": "hello", "user": "u1"}` dict returns a `Message` dataclass with `text="hello"`, `user="u1"`, `platform=Platform.terminal`, `timestamp` is a datetime |
| TC-009 | `test_route_priority` | `route_message(message, routes)` with two routes (priority 1 and priority 2) where only the lower-priority route matches returns the matching route; when both match, the higher-priority route is returned |
| TC-010 | `test_format_response` | `format_response(text, fmt=MessageFormat.markdown)` returns a string with markdown formatting; `fmt=MessageFormat.text` returns plain text; `fmt=MessageFormat.json` returns valid JSON with a `content` field |

Additional test functions:
- `test_normalize_missing_user` — `normalize_input` with no `user` field defaults to `"anonymous"`
- `test_route_no_match` — `route_message` with no matching routes returns `None` or raises `NoRouteError`
- `test_format_response_html` — `format_response(text, fmt=MessageFormat.html)` returns HTML with a `<p>` or similar wrapper

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_agent_gateway.py::test_normalize_terminal -q
cd R:/Sandbox/ark && pytest tests/test_agent_gateway.py::test_route_priority -q
cd R:/Sandbox/ark && pytest tests/test_agent_gateway.py::test_format_response -q
cd R:/Sandbox/ark && pytest tests/test_agent_gateway.py -q
```

---

### 4. Backend Tests — `tests/test_agent_backend.py`

Covers TC-011 through TC-013. Tests that `tools/agent/backend.py` executes commands via
`LocalBackend`, constructs correct Docker run commands via `DockerBackend`, and that
`backend_from_spec()` dispatches to the correct backend class.

**Fixture approach**: `LocalBackend` tests use a harmless command (`echo hello`) and assert
on the returned `ExecutionResult` fields. `DockerBackend` tests inspect the constructed command
string without actually running Docker (command construction is a pure function). Factory tests
use minimal `ExecutionBackendDef` AST dicts with `type` field set to `"local"` or `"docker"`.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-011 | `test_local_execute` | `LocalBackend().execute("echo hello")` returns an `ExecutionResult` with `returncode=0`, `stdout` containing `"hello"`, and `stderr=""` or empty |
| TC-012 | `test_docker_command` | `DockerBackend(image="python:3.11", limits=ExecutionLimits(memory_mb=512, cpu_cores=1)).build_command("echo hi")` returns a list/string starting with `"docker run"` and containing `"--memory=512m"` and `"--cpus=1"` |
| TC-013 | `test_factory_dispatch` | `backend_from_spec({"type": "local"})` returns a `LocalBackend` instance; `backend_from_spec({"type": "docker", "image": "python:3.11"})` returns a `DockerBackend` instance; unknown type raises `ValueError` |

Additional test functions:
- `test_local_execute_failure` — `LocalBackend().execute("false")` returns `ExecutionResult` with `returncode != 0`
- `test_local_execute_timeout` — `LocalBackend(timeout=0.01).execute("sleep 10")` returns `ExecutionResult` with `timed_out=True`
- `test_docker_image_in_command` — `DockerBackend` command contains the specified image name

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_agent_backend.py::test_local_execute -q
cd R:/Sandbox/ark && pytest tests/test_agent_backend.py::test_docker_command -q
cd R:/Sandbox/ark && pytest tests/test_agent_backend.py::test_factory_dispatch -q
cd R:/Sandbox/ark && pytest tests/test_agent_backend.py -q
```

---

### 5. Skill Tests — `tests/test_agent_skill.py`

Covers TC-014 through TC-017. Tests that `tools/agent/skill_manager.py` and
`tools/agent/learning.py` correctly match triggers, perform CRUD operations, record and search
sessions, and generate skills from execution traces.

**Fixture approach**: `SkillManager` tests use a small in-memory skills dict (3 skills with
distinct trigger patterns and priorities). `LearningEngine` tests use a temporary directory
(`tmp_path`) for session storage. Skill generation tests use a deterministic stub trace dict
(tool calls, duration, outcome) to avoid LLM dependency — the generator should produce a skill
from the trace structure alone at this test level.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-014 | `test_trigger_match_priority` | `SkillManager.match(message)` with 3 skills — one matching on exact keyword (priority 1), one matching on regex (priority 2), and one not matching — returns the priority-1 skill; when only priority-2 matches, returns that skill |
| TC-015 | `test_skill_crud` | `SkillManager.add(skill)` adds a skill; `get(name)` retrieves it with all fields intact; `update(name, updates)` merges updates; `delete(name)` removes it; subsequent `get(name)` raises `KeyError` or returns `None` |
| TC-016 | `test_learning_session_search` | `LearningEngine.record_session(session_dict)` persists the session; `search(query="deploy")` returns sessions containing "deploy" in their `summary` or `tags`; sessions not matching the query are excluded |
| TC-017 | `test_skill_generation` | `LearningEngine.generate_skill(trace)` with a trace dict containing `tool_calls`, `duration_ms`, `outcome="success"`, `query="deploy app"` returns a `SkillDef`-compatible dict with `name`, `trigger`, `steps`, `status="draft"` fields |

Additional test functions:
- `test_skill_crud_update_preserves_fields` — `update()` only modifies specified keys; unmentioned fields remain unchanged
- `test_trigger_no_match_returns_none` — `match(message)` with no matching skill returns `None`
- `test_session_search_empty_result` — `search(query="xyznomatch")` returns an empty list
- `test_skill_generation_from_empty_trace` — `generate_skill({})` returns a minimal draft skill or raises `ValueError` with a meaningful message

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_agent_skill.py::test_trigger_match_priority -q
cd R:/Sandbox/ark && pytest tests/test_agent_skill.py::test_skill_crud -q
cd R:/Sandbox/ark && pytest tests/test_agent_skill.py::test_learning_session_search -q
cd R:/Sandbox/ark && pytest tests/test_agent_skill.py::test_skill_generation -q
cd R:/Sandbox/ark && pytest tests/test_agent_skill.py -q
```

---

### 6. Scheduler Tests — `tests/test_agent_scheduler.py`

Covers TC-018 through TC-020. Tests that `tools/agent/scheduler.py` parses cron expressions
correctly, returns the right due tasks for a given timestamp, and that `tick()` executes due
tasks and updates their last-run timestamps.

**Fixture approach**: Cron parsing tests use well-known expressions (`"0 * * * *"` for hourly,
`"*/5 * * * *"` for every 5 minutes) and assert the next-run datetime. `get_due_tasks()` tests
construct a minimal `Scheduler` with 3 tasks (one past-due, one future-due, one exactly at
epoch boundary) and assert which are returned. `tick()` tests use a stub `execute_fn` callback
that records calls, then assert the callback was called exactly for past-due tasks.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-018 | `test_cron_parse` | `parse_cron("0 9 * * 1")` (every Monday 9am) returns a `CronSchedule` object where `next_run(from_dt=datetime(2026, 4, 13, 0, 0))` returns `datetime(2026, 4, 13, 9, 0)` (Monday); `parse_cron("*/30 * * * *")` returns next run within 30 minutes of `from_dt` |
| TC-019 | `test_due_tasks` | `Scheduler.get_due_tasks(now)` with 3 tasks — last_run 2 hours ago (due), last_run 1 minute ago with 1-hour interval (not due), and never-run (due) — returns exactly the 2 due tasks |
| TC-020 | `test_tick_execution` | `Scheduler.tick(now, execute_fn)` with 2 due tasks calls `execute_fn` twice (once per task), updates each task's `last_run` to `now`, and does not call `execute_fn` for non-due tasks |

Additional test functions:
- `test_cron_parse_invalid` — `parse_cron("not a cron")` raises `ValueError` with a descriptive message
- `test_cron_next_run_wrap` — hourly cron at minute 0 correctly wraps from hour 23 to hour 0 of next day
- `test_tick_updates_last_run` — after `tick()`, `task.last_run` equals the `now` argument passed to `tick()`

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_agent_scheduler.py::test_cron_parse -q
cd R:/Sandbox/ark && pytest tests/test_agent_scheduler.py::test_due_tasks -q
cd R:/Sandbox/ark && pytest tests/test_agent_scheduler.py::test_tick_execution -q
cd R:/Sandbox/ark && pytest tests/test_agent_scheduler.py -q
```

---

### 7. Runner Tests — `tests/test_agent_runner.py`

Covers TC-021 through TC-023. Tests that `tools/agent/agent_runner.py` initializes all
subsystems from a config dict, routes messages through skill matching before falling back to
a default handler, and that `tick()` correctly delegates to the `Scheduler`.

**Fixture approach**: `AgentRunner` is instantiated with a minimal config dict (no real platform
connections). Subsystem initialization tests assert that `runner.gateway`, `runner.skill_manager`,
`runner.scheduler`, `runner.learning_engine`, and `runner.backend` are all non-None after init.
`process_message()` tests use a stub `Message` and a stub skill that returns a canned response.
Fallback tests use a message with no matching skill and assert the fallback handler is invoked.
`tick()` tests assert that `runner.scheduler.tick()` is called (using a spy/mock on the scheduler).

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-021 | `test_init_subsystems` | `AgentRunner(config).init()` with a minimal config dict sets `runner.gateway` to a `Gateway` instance, `runner.skill_manager` to a `SkillManager`, `runner.scheduler` to a `Scheduler`, `runner.learning_engine` to a `LearningEngine`, and `runner.backend` to a backend instance — all non-None |
| TC-022 | `test_process_message` | `runner.process_message(message)` with a `Message` matching a registered skill returns the skill's canned response; with a `Message` matching no skill, the fallback handler is called and returns a non-empty string |
| TC-023 | `test_tick_scheduler` | `runner.tick(now)` calls `runner.scheduler.tick(now, ...)` exactly once — verified by replacing `runner.scheduler.tick` with a spy function and asserting call count == 1 after `runner.tick(now)` |

Additional test functions:
- `test_init_raises_on_missing_backend` — `AgentRunner(config_without_backend).init()` raises `ConfigError` or `KeyError` with a message mentioning "backend"
- `test_process_message_records_session` — after `process_message()`, `runner.learning_engine.sessions` contains one new entry for the interaction
- `test_process_message_returns_response_object` — return type of `process_message()` has `text` and `platform` fields

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_agent_runner.py::test_init_subsystems -q
cd R:/Sandbox/ark && pytest tests/test_agent_runner.py::test_process_message -q
cd R:/Sandbox/ark && pytest tests/test_agent_runner.py::test_tick_scheduler -q
cd R:/Sandbox/ark && pytest tests/test_agent_runner.py -q
```

---

### 8. Verification Tests — `tests/test_agent_verify.py`

Covers TC-024 through TC-029. Tests that `tools/verify/agent_verify.py` catches invalid gateway
references, invalid cron task references, model fallback cycles (via Z3), resource limit
violations, ambiguous skill trigger overlaps, and agent completeness errors.

**Fixture approach**: Direct unit tests against `agent_verify.py` functions using in-memory AST
dicts. "Failing" tests assert that the returned result list contains at least one entry with
`status="fail"` and a meaningful `message`. "Passing" tests assert all entries have
`status="pass"`. Z3 cycle tests construct a 2-node fallback chain that is cyclic (A → B → A)
and one that is acyclic (A → B). Trigger overlap tests use two skills with identical pattern
strings.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-024 | `test_gateway_refs` | `verify_gateway_refs([gateway_ast], all_items)` with `gateway.agent` referencing a non-existent agent name returns `status="fail"` with message mentioning the unknown ref; valid ref returns `status="pass"` |
| TC-025 | `test_cron_refs` | `verify_cron_refs([cron_ast], all_items)` with `cron_task.agent` or `cron_task.delivery_platform` referencing non-existent items returns `status="fail"`; valid refs return `status="pass"` |
| TC-026 | `test_fallback_cycle` | `verify_fallback_cycles([model_config_a, model_config_b], ...)` where `model_config_a.fallback = "b"` and `model_config_b.fallback = "a"` returns `status="fail"` with message mentioning "cycle"; acyclic chain `a → b` (no b fallback) returns `status="pass"` |
| TC-027 | `test_resource_limits` | `verify_resource_limits([backend_ast_negative_memory])` with `memory_mb=-1` returns `status="fail"`; `memory_mb=0` returns `status="fail"`; `memory_mb=512` returns `status="pass"` |
| TC-028 | `test_trigger_overlap` | `verify_trigger_overlap([skill_a, skill_b])` where both have `trigger.pattern="help"` returns a result with `status="warn"` (not block) and a message mentioning the overlapping pattern; non-overlapping patterns return `status="pass"` |
| TC-029 | `test_agent_completeness` | `verify_agent_completeness([agent_ast], all_items)` with `agent.model` referencing a non-existent `model_config` returns `status="fail"`; `agent.backend` referencing a non-existent `execution_backend` returns `status="fail"`; all refs present returns `status="pass"` |

Additional test functions:
- `test_gateway_refs_multiple_platforms` — gateway with multiple platform refs where one is invalid fails, with the valid refs passing
- `test_fallback_chain_max_depth` — chain of depth 5 without cycles returns `status="pass"`
- `test_resource_limits_cpu_bounds` — `cpu_cores=0` fails; `cpu_cores=0.5` passes
- `test_trigger_overlap_different_platforms` — two skills with the same pattern but different platform scopes may warn at lower severity

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_agent_verify.py::test_gateway_refs -q
cd R:/Sandbox/ark && pytest tests/test_agent_verify.py::test_cron_refs -q
cd R:/Sandbox/ark && pytest tests/test_agent_verify.py::test_fallback_cycle -q
cd R:/Sandbox/ark && pytest tests/test_agent_verify.py::test_resource_limits -q
cd R:/Sandbox/ark && pytest tests/test_agent_verify.py::test_trigger_overlap -q
cd R:/Sandbox/ark && pytest tests/test_agent_verify.py::test_agent_completeness -q
cd R:/Sandbox/ark && pytest tests/test_agent_verify.py -q
```

---

### 9. Codegen Tests — `tests/test_agent_codegen.py`

Covers TC-030 through TC-034. Tests that `tools/codegen/agent_codegen.py` generates valid
agent configuration YAML, gateway routing table YAML, cron entries in crontab format, skill
markdown in agentskills.io format, and Docker Compose fragments from backend specs.

**Fixture approach**: Unit tests against `agent_codegen.py` functions using minimal AST dicts
as inputs. Output is returned as a string or written to `tmp_path`. All assertions check
structural validity (YAML parses, crontab line format, markdown has expected headers) without
asserting exact string matches (to allow formatting flexibility). CLI tests use `subprocess.run`
with a temp directory.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-030 | `test_agent_config_yaml` | `gen_agent_config(agent_ast, model_config_ast)` returns a string that parses as valid YAML containing keys `name`, `model`, `parameters`, `fallback_chain`; values match the input AST fields |
| TC-031 | `test_gateway_routes_yaml` | `gen_gateway_routes(gateway_ast)` returns a string that parses as valid YAML containing a `routes` list where each entry has `priority`, `platform`, `pattern`, and `action` keys |
| TC-032 | `test_cron_entries` | `gen_cron_entries([cron_task_ast])` returns a string where each line matches the crontab format `"<min> <hr> <dom> <mon> <dow> <command>"`; the generated command references the task name and delivery platform |
| TC-033 | `test_skill_markdown` | `gen_skill_markdown(skill_ast)` returns a string containing `# <skill_name>` heading, a `## Trigger` section with the trigger pattern, and a `## Steps` section listing each step; output is valid Markdown |
| TC-034 | `test_docker_compose` | `gen_docker_compose(backend_ast)` returns a string that parses as valid YAML containing a `services` key with the backend name as a service, `image`, `mem_limit`, and `cpus` fields matching the AST limits |

Additional test functions:
- `test_agent_config_yaml_is_valid_yaml` — `yaml.safe_load()` on the generated config raises no exception
- `test_gateway_routes_yaml_priority_order` — routes in the generated YAML are sorted by `priority` field ascending
- `test_cron_entries_multiple_tasks` — calling with 3 cron tasks returns exactly 3 lines
- `test_skill_markdown_is_valid_markdown` — generated string contains at least one `#` heading and at least one list item (`-`)
- `test_docker_compose_is_valid_yaml` — `yaml.safe_load()` on the compose fragment raises no exception

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_agent_codegen.py::test_agent_config_yaml -q
cd R:/Sandbox/ark && pytest tests/test_agent_codegen.py::test_gateway_routes_yaml -q
cd R:/Sandbox/ark && pytest tests/test_agent_codegen.py::test_cron_entries -q
cd R:/Sandbox/ark && pytest tests/test_agent_codegen.py::test_skill_markdown -q
cd R:/Sandbox/ark && pytest tests/test_agent_codegen.py::test_docker_compose -q
cd R:/Sandbox/ark && pytest tests/test_agent_codegen.py -q
```

---

### 10. Visualization Tests — `tests/test_agent_viz.py`

Covers TC-035 and TC-036. Tests that the Ark visualizer generates correct graph data for
agent architecture and that the HTML output renders agent nodes with the correct colors and
labels.

**Fixture approach**: Visualizer API tests parse a minimal in-memory `.ark` snippet containing
one agent, one gateway, one platform, and one execution backend, then call the visualizer's
`build_graph(arkfile)` function and assert on the returned dict structure. HTML tests parse a
real or in-memory spec and call `render_html(graph)`, asserting on substrings in the output.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-035 | `test_agent_graph_data` | `build_graph(arkfile)` with an arkfile containing one agent, one gateway, and two platforms returns a dict with `nodes` and `edges` lists; `nodes` contains entries for all 4 items; each node has `id`, `type`, `label` fields; edges connect gateway to agent and gateway to platforms |
| TC-036 | `test_agent_html_output` | `render_html(graph)` or `python ark.py graph <spec>` produces an HTML string containing CSS color assignments for `agent`, `gateway`, `platform`, and `execution_backend` node types; the agent's name appears as a label in the output |

Additional test functions:
- `test_agent_graph_node_types` — node `type` field matches the item kind (`"agent"`, `"gateway"`, `"platform"`, `"execution_backend"`)
- `test_agent_graph_edges_directional` — edges from gateway to platform have source=gateway-id, target=platform-id
- `test_agent_html_skill_nodes` — when spec includes skills, skill nodes appear in the HTML with a distinct color class

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_agent_viz.py::test_agent_graph_data -q
cd R:/Sandbox/ark && pytest tests/test_agent_viz.py::test_agent_html_output -q
cd R:/Sandbox/ark && pytest tests/test_agent_viz.py -q
```

---

### 11. Integration Tests — `tests/test_agent_integration.py`

Covers TC-037 through TC-042. End-to-end tests that parse real reflexive spec files
(`specs/agent/agent_system.ark`, `specs/agent/ark_agent.ark`), verify them, check that both
are registered in `specs/root.ark`, and that codegen produces valid artifacts from
`agent_system.ark`.

**Fixture approach**: `subprocess.run` calls to `python ark.py` with real `.ark` spec files.
Assert exit code and, where applicable, parse stdout JSON. Tests that require spec files created
in later tasks are marked `@pytest.mark.integration` and use `pytest.mark.skipif` with a file
existence check so they skip gracefully when the files do not yet exist. Parsing and verification
tests that depend on `agent_system.ark` and `ark_agent.ark` being on disk will be skipped in
earlier task waves.

| TC | Test Function(s) | Description |
|----|-----------------|-------------|
| TC-037 | `test_agent_system_parses` | `python ark.py parse specs/agent/agent_system.ark` exits 0; Python API parse of the same file also returns a non-None `ArkFile` with no exceptions |
| TC-038 | `test_agent_system_verifies` | `python ark.py verify specs/agent/agent_system.ark` exits 0 with no error lines in stdout/stderr; all verification checks pass |
| TC-039 | `test_ark_agent_parses` | `python ark.py parse specs/agent/ark_agent.ark` exits 0; Python API parse also returns a non-None `ArkFile` with no exceptions |
| TC-040 | `test_ark_agent_verifies` | `python ark.py verify specs/agent/ark_agent.ark` exits 0 with no error lines in stdout/stderr |
| TC-041 | `test_registry_updated` | Parsing `specs/root.ark` via Python API confirms both `"agent_system"` and `"ark_agent"` spec names appear in the registry or import list |
| TC-042 | `test_agent_codegen_e2e` | `python ark.py codegen specs/agent/agent_system.ark --target agent --out <tmp_dir>` exits 0; the output directory contains at least one YAML file and at least one Markdown file |

Additional test functions:
- `test_agent_system_item_count` — parsed `agent_system.ark` contains at least one `agent`, one `gateway`, and one `platform` item
- `test_ark_agent_reflexive_skills` — `ark_agent.ark` parsed `ArkFile` contains skills that reference Ark pipeline roles by name
- `test_codegen_output_valid_yaml` — all YAML files in the codegen output directory parse without errors via `yaml.safe_load()`

**Proof commands:**
```bash
cd R:/Sandbox/ark && pytest tests/test_agent_integration.py::test_agent_system_parses -q
cd R:/Sandbox/ark && pytest tests/test_agent_integration.py::test_agent_system_verifies -q
cd R:/Sandbox/ark && pytest tests/test_agent_integration.py::test_ark_agent_parses -q
cd R:/Sandbox/ark && pytest tests/test_agent_integration.py::test_ark_agent_verifies -q
cd R:/Sandbox/ark && pytest tests/test_agent_integration.py::test_registry_updated -q
cd R:/Sandbox/ark && pytest tests/test_agent_integration.py::test_agent_codegen_e2e -q
cd R:/Sandbox/ark && pytest tests/test_agent_integration.py -q
```

---

## Complete TC-to-Test Mapping

| TC | Description | Test File | Test Function(s) | Runner | Proof Method |
|----|-------------|-----------|-----------------|--------|-------------|
| TC-001 | stdlib/agent.ark parses without errors | `test_agent_schema.py` | `test_agent_ark_parses` | pytest | autotest |
| TC-002 | All agent enum/struct definitions well-formed | `test_agent_schema.py` | `test_agent_types_complete` | pytest | autotest |
| TC-003 | Lark grammar parses all 8 new agent item types | `test_agent_parser.py` | `test_lark_agent_items` | pytest | autotest |
| TC-004 | Pest grammar mirrors all 8 new Lark rules | (manual inspection) | N/A | manual | manual |
| TC-005 | Parser produces correct AST dataclasses | `test_agent_parser.py` | `test_parser_dataclasses` | pytest | autotest |
| TC-006 | ArkFile indices populated for all 8 agent types | `test_agent_parser.py` | `test_arkfile_indices` | pytest | autotest |
| TC-007 | Existing .ark files parse without regression | `test_agent_parser.py` | `test_parser_smoke` | pytest | autotest |
| TC-008 | Gateway normalizes terminal input to Message | `test_agent_gateway.py` | `test_normalize_terminal` | pytest | autotest |
| TC-009 | Gateway route matching respects priority ordering | `test_agent_gateway.py` | `test_route_priority` | pytest | autotest |
| TC-010 | Gateway formats responses per platform format spec | `test_agent_gateway.py` | `test_format_response` | pytest | autotest |
| TC-011 | LocalBackend executes a command and returns ExecutionResult | `test_agent_backend.py` | `test_local_execute` | pytest | autotest |
| TC-012 | DockerBackend constructs correct docker run command | `test_agent_backend.py` | `test_docker_command` | pytest | autotest |
| TC-013 | backend_from_spec dispatches to correct backend | `test_agent_backend.py` | `test_factory_dispatch` | pytest | autotest |
| TC-014 | SkillManager matches triggers with priority ordering | `test_agent_skill.py` | `test_trigger_match_priority` | pytest | autotest |
| TC-015 | SkillManager CRUD operations work correctly | `test_agent_skill.py` | `test_skill_crud` | pytest | autotest |
| TC-016 | LearningEngine records sessions and searches by query | `test_agent_skill.py` | `test_learning_session_search` | pytest | autotest |
| TC-017 | LearningEngine generates a skill from execution trace | `test_agent_skill.py` | `test_skill_generation` | pytest | autotest |
| TC-018 | Cron expression parsing computes correct next run times | `test_agent_scheduler.py` | `test_cron_parse` | pytest | autotest |
| TC-019 | Scheduler.get_due_tasks returns correct tasks | `test_agent_scheduler.py` | `test_due_tasks` | pytest | autotest |
| TC-020 | Scheduler.tick executes due tasks and updates timestamps | `test_agent_scheduler.py` | `test_tick_execution` | pytest | autotest |
| TC-021 | AgentRunner initializes all subsystems from config | `test_agent_runner.py` | `test_init_subsystems` | pytest | autotest |
| TC-022 | AgentRunner.process_message routes through skill then fallback | `test_agent_runner.py` | `test_process_message` | pytest | autotest |
| TC-023 | AgentRunner.tick delegates to scheduler | `test_agent_runner.py` | `test_tick_scheduler` | pytest | autotest |
| TC-024 | Gateway references validated — invalid names caught | `test_agent_verify.py` | `test_gateway_refs` | pytest | autotest |
| TC-025 | Cron task references validated — invalid names caught | `test_agent_verify.py` | `test_cron_refs` | pytest | autotest |
| TC-026 | Model fallback cycles detected via Z3 ordinals | `test_agent_verify.py` | `test_fallback_cycle` | pytest | autotest |
| TC-027 | Resource limit violations detected | `test_agent_verify.py` | `test_resource_limits` | pytest | autotest |
| TC-028 | Skill trigger overlap warnings generated | `test_agent_verify.py` | `test_trigger_overlap` | pytest | autotest |
| TC-029 | Agent completeness catches missing model/backend refs | `test_agent_verify.py` | `test_agent_completeness` | pytest | autotest |
| TC-030 | Agent config YAML generated from agent + model_config | `test_agent_codegen.py` | `test_agent_config_yaml` | pytest | autotest |
| TC-031 | Gateway routing table YAML generated from gateway specs | `test_agent_codegen.py` | `test_gateway_routes_yaml` | pytest | autotest |
| TC-032 | Cron entries generated in valid crontab format | `test_agent_codegen.py` | `test_cron_entries` | pytest | autotest |
| TC-033 | Skill markdown generated in agentskills.io format | `test_agent_codegen.py` | `test_skill_markdown` | pytest | autotest |
| TC-034 | Docker compose fragment generated from backend specs | `test_agent_codegen.py` | `test_docker_compose` | pytest | autotest |
| TC-035 | Visualizer generates graph data with agent nodes/edges | `test_agent_viz.py` | `test_agent_graph_data` | pytest | autotest |
| TC-036 | HTML output renders agent architecture with colors/labels | `test_agent_viz.py` | `test_agent_html_output` | pytest | autotest |
| TC-037 | agent_system.ark parses without errors | `test_agent_integration.py` | `test_agent_system_parses` | pytest | autotest |
| TC-038 | agent_system.ark passes all agent verification checks | `test_agent_integration.py` | `test_agent_system_verifies` | pytest | autotest |
| TC-039 | ark_agent.ark parses without errors | `test_agent_integration.py` | `test_ark_agent_parses` | pytest | autotest |
| TC-040 | ark_agent.ark passes all agent verification checks | `test_agent_integration.py` | `test_ark_agent_verifies` | pytest | autotest |
| TC-041 | Both specs registered in root.ark SystemRegistry | `test_agent_integration.py` | `test_registry_updated` | pytest | autotest |
| TC-042 | Codegen produces valid artifacts from agent_system.ark | `test_agent_integration.py` | `test_agent_codegen_e2e` | pytest | autotest |
| TC-043 | Test strategy document covers all target conditions | (manual inspection) | N/A | manual | manual |
| TC-044 | All automated tests pass | `tests/test_agent_*.py` | (all functions) | pytest | autotest |

---

## Test Files Summary

| Test File | TCs Covered | Subsystem | Implementation Task |
|-----------|-------------|-----------|---------------------|
| `tests/test_agent_schema.py` | TC-001, TC-002 | stdlib enums/structs | ADV005-T021 (after T002) |
| `tests/test_agent_parser.py` | TC-003, TC-004 (partial), TC-005, TC-006, TC-007 | Lark grammar, AST dataclasses, ArkFile indices | ADV005-T021 (after T003, T005) |
| `tests/test_agent_gateway.py` | TC-008, TC-009, TC-010 | Multi-platform message routing | ADV005-T021 (after T006) |
| `tests/test_agent_backend.py` | TC-011, TC-012, TC-013 | Execution backends, factory dispatch | ADV005-T021 (after T007) |
| `tests/test_agent_skill.py` | TC-014, TC-015, TC-016, TC-017 | SkillManager CRUD/trigger, LearningEngine | ADV005-T021 (after T008, T009) |
| `tests/test_agent_scheduler.py` | TC-018, TC-019, TC-020 | Cron scheduling, tick execution | ADV005-T021 (after T010) |
| `tests/test_agent_runner.py` | TC-021, TC-022, TC-023 | Agent runner lifecycle orchestration | ADV005-T021 (after T011) |
| `tests/test_agent_verify.py` | TC-024, TC-025, TC-026, TC-027, TC-028, TC-029 | Z3 verification, cross-refs, resource limits | ADV005-T021 (after T012, T013) |
| `tests/test_agent_codegen.py` | TC-030, TC-031, TC-032, TC-033, TC-034 | YAML/crontab/markdown/compose codegen | ADV005-T021 (after T014) |
| `tests/test_agent_viz.py` | TC-035, TC-036 | Visualizer graph data and HTML output | ADV005-T021 (after T016) |
| `tests/test_agent_integration.py` | TC-037, TC-038, TC-039, TC-040, TC-041, TC-042 | Reflexive specs, root.ark registry, codegen e2e | ADV005-T021 (after T017, T018, T019, T020) |

---

## Approximate Test Count by File

| Test File | Named Test Functions | Notes |
|-----------|---------------------|-------|
| `test_agent_schema.py` | ~8 | 2 primary TCs + 6 enum variant checks |
| `test_agent_parser.py` | ~11 | 4 primary TCs (TC-004 manual) + item field checks |
| `test_agent_gateway.py` | ~6 | 3 primary TCs + missing-user default + no-match + HTML format |
| `test_agent_backend.py` | ~6 | 3 primary TCs + failure + timeout + image-in-command |
| `test_agent_skill.py` | ~8 | 4 primary TCs + update-preserves + no-match + empty-search + empty-trace |
| `test_agent_scheduler.py` | ~6 | 3 primary TCs + invalid-cron + wrap + last-run update |
| `test_agent_runner.py` | ~6 | 3 primary TCs + missing-backend + session-record + response-type |
| `test_agent_verify.py` | ~10 | 6 primary TCs + multi-platform + chain-depth + cpu-bounds + platform-scope |
| `test_agent_codegen.py` | ~10 | 5 primary TCs + valid-yaml × 2 + priority-order + line-count + markdown |
| `test_agent_viz.py` | ~5 | 2 primary TCs + node-types + directional-edges + skill-nodes |
| `test_agent_integration.py` | ~9 | 6 primary TCs + item-count + reflexive-skills + valid-yaml |
| **Total** | **~85** | All 44 TCs covered; each has at least one dedicated test function |

---

## Summary by Proof Method

| Method | Count | TC IDs |
|--------|-------|--------|
| autotest | 41 | TC-001–003, TC-005–042, TC-044 |
| manual | 3 | TC-004, TC-043, (TC-044 is auto) |

(TC-043 is this document's existence; TC-004 is Pest grammar parity — both are human-reviewed.)

---

## Tooling

- **Framework**: pytest (existing Ark convention)
- **Fixtures**: `tmp_path` for codegen output; inline `.ark` snippet strings for grammar/parser/verify
- **Integration marker**: `@pytest.mark.integration` on tests requiring real spec files (`agent_system.ark`, `ark_agent.ark`); skip gracefully with `pytest.mark.skipif(not path.exists(), reason="spec not yet created")` when files do not exist
- **CLI tests**: `subprocess.run(['python', 'ark.py', ...], cwd=REPO_ROOT)`, assert `returncode == 0`
- **Stub callbacks**: `execute_fn`, `judge_fn`, `mutate_fn` are deterministic Python functions — no LLM SDK dependency in any test
- **Constants**: `REPO_ROOT = Path('R:/Sandbox/ark')` at top of each file
- **Z3**: `agent_verify.py` tests require `z3-solver` installed; if absent, tests are skipped via `pytest.importorskip('z3')`

---

## Execution Order

Tests must be developed in dependency order (matching task wave order):

1. **Wave 1 — Schema** (`test_agent_schema.py`) — after T002 (`agent.ark` stdlib file)
2. **Wave 2 — Parser** (`test_agent_parser.py`) — after T003 (Lark grammar), T005 (AST dataclasses)
3. **Wave 3 — Gateway** (`test_agent_gateway.py`) — after T006 (`gateway.py`)
4. **Wave 4 — Backend** (`test_agent_backend.py`) — after T007 (`backend.py`)
5. **Wave 5 — Skill** (`test_agent_skill.py`) — after T008 (`skill_manager.py`), T009 (`learning.py`)
6. **Wave 6 — Scheduler** (`test_agent_scheduler.py`) — after T010 (`scheduler.py`)
7. **Wave 7 — Runner** (`test_agent_runner.py`) — after T011 (`agent_runner.py`)
8. **Wave 8 — Verify** (`test_agent_verify.py`) — after T012 (`agent_verify.py`), T013 (verify CLI hook)
9. **Wave 9 — Codegen** (`test_agent_codegen.py`) — after T014 (`agent_codegen.py`), T015 (codegen CLI hook)
10. **Wave 10 — Viz** (`test_agent_viz.py`) — after T016 (visualizer extension)
11. **Wave 11 — Integration** (`test_agent_integration.py`) — after T017 (`agent_system.ark`), T018 (`ark_agent.ark`), T019 (root.ark update), T020 (pipeline smoke)

Run all agent tests: `pytest tests/test_agent_*.py -q`

---

## TC→File Quick Reference

| TC Range | File | Subsystem |
|----------|------|-----------|
| TC-001–002 | `test_agent_schema.py` | stdlib enums/structs |
| TC-003–007 | `test_agent_parser.py` | Grammar, AST, ArkFile indices |
| TC-008–010 | `test_agent_gateway.py` | Multi-platform messaging gateway |
| TC-011–013 | `test_agent_backend.py` | Execution backends |
| TC-014–017 | `test_agent_skill.py` | SkillManager + LearningEngine |
| TC-018–020 | `test_agent_scheduler.py` | Cron scheduler |
| TC-021–023 | `test_agent_runner.py` | Agent runner orchestration |
| TC-024–029 | `test_agent_verify.py` | Z3 verification |
| TC-030–034 | `test_agent_codegen.py` | Code generation |
| TC-035–036 | `test_agent_viz.py` | Visualization |
| TC-037–042 | `test_agent_integration.py` | Reflexive specs, root.ark, codegen e2e |
| TC-043 | Manual inspection | This document exists and is complete |
| TC-044 | `pytest tests/test_agent_*.py` | All automated tests pass |
