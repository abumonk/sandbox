# ADV-003 Test Strategy — Studio Hierarchy

## Overview

This document maps every target condition (TC-001 through TC-029) from ADV-003 to a proof
method, proof command, test file assignment, and subsystem grouping. The studio hierarchy
feature adds six new Ark DSL item kinds (`role`, `studio`, `command`, `hook`, `rule`,
`template`), a new stdlib schema, Z3 verification, and codegen for Claude Code artifacts.

## Proof Methods

- **autotest** — automated pytest or CLI command with deterministic pass/fail
- **poc** — proof-of-concept command that must produce non-trivial output (human judges "meaningful")
- **manual** — human inspection of generated artifact

## Test File Assignments by Subsystem

### `tests/test_studio_schema.py` — Stdlib Schema (TC-001 through TC-003)

Validates that `dsl/stdlib/studio.ark` parses cleanly and that all enum and struct definitions
are present and well-formed.

| TC | Description | Proof Method | Proof Command | Test Function(s) |
|----|-------------|-------------|---------------|------------------|
| TC-001 | Lark grammar parses all 6 new item kinds without errors | autotest | `pytest tests/test_studio_schema.py -k grammar -q` | `test_role_item_parses`, `test_studio_item_parses`, `test_command_item_parses`, `test_hook_item_parses`, `test_rule_item_parses`, `test_template_item_parses` |
| TC-002 | Pest grammar mirrors Lark for all 6 new item kinds | autotest | `pytest tests/test_studio_schema.py -k pest -q` | `test_pest_role_item_parses`, `test_pest_studio_item_parses`, `test_pest_command_item_parses`, `test_pest_hook_item_parses`, `test_pest_rule_item_parses`, `test_pest_template_item_parses` |
| TC-003 | Existing .ark files continue to parse after grammar changes (no regressions) | autotest | `pytest tests/test_studio_schema.py -k regression -q` | `test_existing_code_graph_still_parses`, `test_existing_root_ark_still_parses`, `test_existing_stdlib_types_still_parses` |

**Fixture approach**: In-memory .ark snippet strings covering each item kind. Each test
instantiates `ArkParser`, calls `parse()` on the snippet, and asserts no exception is raised.
Regression tests call the parser on real files under `dsl/stdlib/` and `specs/`.

---

### `tests/test_studio_parser.py` — Parser AST Support (TC-004 through TC-009)

Tests that the Lark transformer correctly converts parse trees into the new AST dataclasses
(`RoleDef`, `StudioDef`, `CommandDef`, `HookDef`, `RuleDef`, `TemplateDef`) and that
`ArkFile` indices are populated.

| TC | Description | Proof Method | Proof Command | Test Function(s) |
|----|-------------|-------------|---------------|------------------|
| TC-004 | Parser produces correct JSON AST for role_def items | autotest | `pytest tests/test_studio_parser.py -k role -q` | `test_role_def_name`, `test_role_def_tier`, `test_role_def_escalates_to`, `test_role_def_skills`, `test_role_def_tools`, `test_role_def_responsibilities`, `test_role_def_description`, `test_role_def_kind_field` |
| TC-005 | Parser produces correct JSON AST for studio_def items | autotest | `pytest tests/test_studio_parser.py -k studio -q` | `test_studio_def_name`, `test_studio_def_tier_groups`, `test_studio_def_tier_group_members`, `test_studio_def_description`, `test_studio_def_kind_field` |
| TC-006 | Parser produces correct JSON AST for command, hook, rule, template items | autotest | `pytest tests/test_studio_parser.py -k "command or hook or rule or template" -q` | `test_command_def_phase`, `test_command_def_role`, `test_command_def_prompt`, `test_command_def_output`, `test_hook_def_event`, `test_hook_def_pattern`, `test_hook_def_action`, `test_rule_def_path`, `test_rule_def_constraint`, `test_rule_def_severity`, `test_template_def_sections`, `test_template_def_bound_to` |
| TC-007 | ArkFile indices include roles, studios, commands dicts | autotest | `pytest tests/test_studio_parser.py -k indices -q` | `test_arkfile_has_roles_dict`, `test_arkfile_has_studios_dict`, `test_arkfile_has_commands_dict`, `test_roles_dict_keyed_by_name`, `test_studios_dict_keyed_by_name`, `test_commands_dict_keyed_by_name` |
| TC-008 | stdlib/studio.ark parses without errors via `python ark.py parse` | autotest | `pytest tests/test_studio_parser.py -k stdlib -q` | `test_stdlib_studio_ark_parses`, `test_stdlib_studio_ark_has_tier_enum`, `test_stdlib_studio_ark_has_agent_tool_enum`, `test_stdlib_studio_ark_has_hook_event_enum` |
| TC-009 | All enum and struct definitions are well-formed and referenceable | autotest | `pytest tests/test_studio_parser.py -k enums -q` | `test_tier_enum_has_director_lead_specialist`, `test_agent_tool_enum_covers_claude_tools`, `test_hook_event_enum_covers_required_events`, `test_severity_enum_has_error_warning_info`, `test_workflow_phase_enum_has_required_phases`, `test_struct_escalation_path_fields`, `test_struct_skill_fields`, `test_struct_command_output_fields` |

**Fixture approach**: Parameterized pytest fixtures that parse small, self-contained .ark
snippets. For each dataclass test, assert field values match input. For ArkFile index tests,
parse a multi-item file and check that `arkfile.roles`, `arkfile.studios`, `arkfile.commands`
are populated with the expected keys. For stdlib tests, parse the real file at
`dsl/stdlib/studio.ark` and inspect the resulting AST.

---

### `tests/test_studio_verify.py` — Z3 Verification (TC-010 through TC-014)

Tests the `studio_verify.py` module functions for escalation acyclicity, command-role
resolution, hook event validity, rule satisfiability, and tool permission consistency.
Each check is exercised with both a passing case and a failing case.

| TC | Description | Proof Method | Proof Command | Test Function(s) |
|----|-------------|-------------|---------------|------------------|
| TC-010 | Escalation cycle detection catches cycles and passes acyclic hierarchies | autotest | `pytest tests/test_studio_verify.py -k escalation -q` | `test_acyclic_escalation_passes`, `test_direct_cycle_detected`, `test_indirect_cycle_detected`, `test_director_with_no_escalates_to_passes`, `test_multiple_independent_chains_pass` |
| TC-011 | Command verification catches missing roles and insufficient tools | autotest | `pytest tests/test_studio_verify.py -k command -q` | `test_command_resolves_existing_role_passes`, `test_command_missing_role_detected`, `test_command_role_has_required_tools_passes`, `test_command_role_missing_tool_detected` |
| TC-012 | Hook event verification catches invalid event types | autotest | `pytest tests/test_studio_verify.py -k hook -q` | `test_valid_hook_event_passes`, `test_invalid_hook_event_detected`, `test_all_allowed_events_pass`, `test_unknown_event_name_detected` |
| TC-013 | Rule constraint satisfiability check works correctly | autotest | `pytest tests/test_studio_verify.py -k rule -q` | `test_satisfiable_constraint_passes`, `test_unsatisfiable_constraint_detected`, `test_empty_constraint_passes`, `test_complex_satisfiable_constraint_passes` |
| TC-014 | Tool permission cross-check detects violations | autotest | `pytest tests/test_studio_verify.py -k permissions -q` | `test_role_within_allowed_tools_passes`, `test_role_using_unpermitted_tool_detected`, `test_director_full_toolset_passes`, `test_specialist_restricted_toolset_passes` |

**Fixture approach**: Direct unit tests against `studio_verify.py` functions. Each test
constructs minimal in-memory data structures (lists of dicts or dataclass instances) representing
roles, commands, hooks, and rules — no file I/O required. The "failing" tests assert that the
verifier returns a non-empty error list or raises the expected exception. Allowed hook events and
tool permissions are taken from the `HookEvent` and `AgentTool` enums defined in `studio.ark`.

---

### `tests/test_studio_codegen.py` — Code Generation (TC-015 through TC-019)

Tests that `studio_codegen.py` generates correctly formatted output files (agent `.md`,
command `.md`, hook settings JSON, template skeletons) from parsed studio AST objects.

| TC | Description | Proof Method | Proof Command | Test Function(s) |
|----|-------------|-------------|---------------|------------------|
| TC-015 | Agent .md files generated correctly from role items | autotest | `pytest tests/test_studio_codegen.py -k agent -q` | `test_agent_md_has_frontmatter`, `test_agent_md_name_field`, `test_agent_md_description_field`, `test_agent_md_model_derived_from_tier`, `test_agent_md_tools_list`, `test_agent_md_has_responsibilities_section`, `test_agent_md_has_escalation_section`, `test_director_gets_opus_model`, `test_specialist_gets_sonnet_model` |
| TC-016 | Command .md files generated correctly from command items | autotest | `pytest tests/test_studio_codegen.py -k command -q` | `test_command_md_has_title`, `test_command_md_phase_present`, `test_command_md_role_present`, `test_command_md_prompt_body`, `test_command_md_output_section` |
| TC-017 | Hook settings.json fragment generated correctly | autotest | `pytest tests/test_studio_codegen.py -k hook -q` | `test_hook_json_has_hooks_key`, `test_hook_json_entry_has_event`, `test_hook_json_entry_has_pattern`, `test_hook_json_entry_has_action`, `test_multiple_hooks_all_present`, `test_hook_json_is_valid_json` |
| TC-018 | Template skeleton files generated correctly | autotest | `pytest tests/test_studio_codegen.py -k template -q` | `test_template_md_has_title`, `test_template_md_has_required_sections`, `test_template_md_section_placeholder_present`, `test_template_md_bound_to_comment` |
| TC-019 | `--target studio` CLI flag works end-to-end | autotest | `pytest tests/test_studio_codegen.py -k cli -q` | `test_cli_studio_target_exits_zero`, `test_cli_generates_agent_files`, `test_cli_generates_command_files`, `test_cli_generates_hook_json`, `test_cli_output_dir_created` |

**Fixture approach**: Unit tests against `studio_codegen.py` functions, using minimal
`RoleDef`, `CommandDef`, `HookDef`, `TemplateDef` dataclass instances as inputs. Output is
captured as a string (not written to disk) for assertion. CLI tests use `subprocess.run` with
a temporary output directory (`tmp_path` pytest fixture) and assert on exit code and file
existence. For TC-019, a small helper .ark fixture file is pre-written to `tmp_path`.

---

### `tests/test_studio_integration.py` — End-to-End Pipeline (TC-020 through TC-027)

End-to-end tests that parse the real studio spec files (`specs/meta/ark_studio.ark` and
`specs/meta/game_studio.ark`), run verification, and optionally trigger codegen.

| TC | Description | Proof Method | Proof Command | Test Function(s) |
|----|-------------|-------------|---------------|------------------|
| TC-020 | `ark.py parse specs/meta/ark_studio.ark` exits 0 | autotest | `pytest tests/test_studio_integration.py -k ark_studio_parse -q` | `test_ark_studio_parses_exit_zero`, `test_ark_studio_has_lead_role`, `test_ark_studio_has_ark_studio_item` |
| TC-021 | `ark.py parse specs/meta/game_studio.ark` exits 0 | autotest | `pytest tests/test_studio_integration.py -k game_studio_parse -q` | `test_game_studio_parses_exit_zero`, `test_game_studio_role_count_at_least_15`, `test_game_studio_command_count_at_least_10` |
| TC-022 | `ark.py verify specs/meta/ark_studio.ark` passes all studio checks | autotest | `pytest tests/test_studio_integration.py -k ark_studio_verify -q` | `test_ark_studio_verify_exits_zero`, `test_ark_studio_escalation_acyclic`, `test_ark_studio_commands_all_resolve` |
| TC-023 | ark_studio.ark parses without errors and correctly models Ark's team | autotest | `pytest tests/test_studio_integration.py -k ark_studio_model -q` | `test_ark_studio_has_planner_role`, `test_ark_studio_has_coder_role`, `test_ark_studio_has_reviewer_role`, `test_ark_studio_tier_groups_populated`, `test_ark_studio_lead_at_tier_1` |
| TC-024 | game_studio.ark parses without errors with ~18 roles, ~20 commands | autotest | `pytest tests/test_studio_integration.py -k game_studio_model -q` | `test_game_studio_has_creative_director`, `test_game_studio_has_technical_director`, `test_game_studio_has_lead_programmer`, `test_game_studio_tier_1_has_directors`, `test_game_studio_tier_3_has_specialists` |
| TC-025 | Both studios pass escalation acyclicity verification | autotest | `pytest tests/test_studio_integration.py -k escalation_both -q` | `test_ark_studio_no_escalation_cycles`, `test_game_studio_no_escalation_cycles`, `test_ark_studio_chain_terminates_at_lead`, `test_game_studio_chain_terminates_at_director` |
| TC-026 | Both studios pass command-role resolution verification | autotest | `pytest tests/test_studio_integration.py -k command_resolution_both -q` | `test_ark_studio_all_commands_resolve`, `test_game_studio_all_commands_resolve` |
| TC-027 | Both files are registered in root.ark | autotest | `pytest tests/test_studio_integration.py -k root_registration -q` | `test_ark_studio_registered_in_root`, `test_game_studio_registered_in_root` |

**Fixture approach**: `subprocess.run` calls to `python ark.py parse` and `python ark.py verify`
with the real spec files. Assert exit code and, where applicable, parse stdout JSON. For model
accuracy tests (TC-023, TC-024), load the AST via the Python API and check ArkFile index
contents. A `@pytest.mark.integration` marker allows skipping these tests when spec files do
not yet exist.

---

### Aggregate

| TC | Description | Proof Method | Proof Command |
|----|-------------|-------------|---------------|
| TC-028 | All autotest TCs have passing tests | autotest | `pytest tests/test_studio_schema.py -q` |
| TC-029 | All autotest TCs have passing tests (full suite) | autotest | `pytest tests/test_studio_*.py -q` |

---

## Summary by Proof Method

| Method | Count | TC IDs |
|--------|-------|--------|
| autotest | 29 | TC-001 through TC-029 (all) |
| poc | 0 | — |
| manual | 0 | — |

## Test Files Summary

| Test File | TCs Covered | Subsystem |
|-----------|-------------|-----------|
| `tests/test_studio_schema.py` | TC-001, TC-002, TC-003 | Grammar parsing — all 6 item kinds + regressions |
| `tests/test_studio_parser.py` | TC-004, TC-005, TC-006, TC-007, TC-008, TC-009 | AST dataclasses, ArkFile indices, stdlib schema |
| `tests/test_studio_verify.py` | TC-010, TC-011, TC-012, TC-013, TC-014 | Z3 verification — 5 studio invariant checks |
| `tests/test_studio_codegen.py` | TC-015, TC-016, TC-017, TC-018, TC-019 | Code generation — agent/command/hook/template output |
| `tests/test_studio_integration.py` | TC-020 through TC-027 | End-to-end pipeline with real .ark spec files |

## Approximate Test Count by File

| Test File | Min Test Functions | Notes |
|-----------|-------------------|-------|
| `test_studio_schema.py` | 15 | 6 lark + 6 pest item-kind tests + 3 regression |
| `test_studio_parser.py` | 30 | 8 role + 5 studio + 12 command/hook/rule/template + 6 indices + 3 stdlib + 8 enums |
| `test_studio_verify.py` | 22 | 5 escalation + 4 command + 4 hook + 4 rule + 4 tool-permission + 1 combined |
| `test_studio_codegen.py` | 25 | 9 agent + 5 command + 6 hook + 4 template + 5 CLI |
| `test_studio_integration.py` | 20 | 3+3 parse + 3 verify + 4+5 model + 4 both-studios |
| **Total** | **112** | Well above the 40-test minimum |

## Tooling

- **Framework**: pytest (already used throughout Ark)
- **Fixtures**: `tmp_path` for codegen output; inline .ark snippet strings for grammar/parser
- **Integration marker**: `@pytest.mark.integration` on tests that require real spec files;
  skip gracefully with `pytest.importorskip` / `skipif` when files do not exist
- **CLI tests**: `subprocess.run(['python', 'ark.py', ...], cwd=REPO_ROOT)`, assert `returncode == 0`
- **Z3 tests**: direct calls to `studio_verify.py` functions with in-memory data structures —
  no subprocess overhead
- **Constants**: a `REPO_ROOT` constant in each test file pointing to `R:/Sandbox/ark/`

## Execution Order

Tests should run in dependency order, matching subsystem build order:

1. `test_studio_schema.py` — grammar must parse first (no runtime dependencies)
2. `test_studio_parser.py` — parser transforms on top of grammar; also validates stdlib
3. `test_studio_verify.py` — verifier depends on parsed AST types
4. `test_studio_codegen.py` — codegen depends on parsed AST types
5. `test_studio_integration.py` — end-to-end; requires all prior subsystems + real spec files

Run all: `pytest tests/test_studio_*.py -q`

## TC→File Quick Reference

| TC Range | File | Subsystem |
|----------|------|-----------|
| TC-001–003 | test_studio_schema.py | Grammar — lark, pest, regression |
| TC-004–009 | test_studio_parser.py | Parser AST + stdlib schema |
| TC-010–014 | test_studio_verify.py | Z3 verification |
| TC-015–019 | test_studio_codegen.py | Code generation |
| TC-020–027 | test_studio_integration.py | End-to-end integration |
| TC-028–029 | (aggregate) | Full suite pass |
