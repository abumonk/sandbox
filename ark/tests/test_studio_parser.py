"""
Tests for Parser AST support — studio item kinds (TC-004 through TC-009).

Tests that the Lark transformer correctly converts parse trees into the new
AST dataclasses (RoleDef, StudioDef, CommandDef, HookDef, RuleDef, TemplateDef)
and that ArkFile indices (roles, studios, commands) are populated.
"""

import sys
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_PARSER_DIR = REPO_ROOT / "tools" / "parser"
if str(_PARSER_DIR) not in sys.path:
    sys.path.insert(0, str(_PARSER_DIR))

from ark_parser import parse as ark_parse, to_json as ark_to_json  # noqa: E402


def parse_src(source: str) -> dict:
    """Parse an inline ARK snippet → AST dict via JSON round-trip."""
    ark_file = ark_parse(source)
    return json.loads(ark_to_json(ark_file))


def parse_file(path: Path) -> dict:
    """Parse an .ark file on disk → AST dict with imports resolved."""
    source = path.read_text(encoding="utf-8")
    ark_file = ark_parse(source, file_path=path)
    return json.loads(ark_to_json(ark_file))


# ============================================================
# TC-004: RoleDef AST fields
# ============================================================

ROLE_SNIPPET = """
role Planner {
    tier: 2
    responsibility: "Plan features"
    responsibility: "Write specs"
    responsibility: "Break tasks"
    escalates_to: Lead
    skills: [planning, communication]
    tools: [Read, Write, Edit]
}
"""


@pytest.fixture(scope="module")
def role_ast():
    return parse_src(ROLE_SNIPPET)


@pytest.fixture(scope="module")
def role_item(role_ast):
    roles = [i for i in role_ast["items"] if i.get("kind") == "role"]
    assert roles, "Expected at least one role item"
    return roles[0]


def test_role_def_kind_field(role_item):
    """TC-004: role item has kind == 'role'."""
    assert role_item["kind"] == "role"


def test_role_def_name(role_item):
    """TC-004: role item has correct name."""
    assert role_item["name"] == "Planner"


def test_role_def_tier(role_item):
    """TC-004: role item has tier field."""
    tier = role_item.get("tier")
    assert tier is not None
    # tier is stored as an expr dict: {"expr": "number", "value": 2}
    if isinstance(tier, dict):
        assert tier.get("value") == 2
    else:
        assert tier == 2


def test_role_def_responsibilities(role_item):
    """TC-004: role item has non-empty responsibilities list."""
    resps = role_item.get("responsibilities", [])
    assert len(resps) >= 1


def test_role_def_escalates_to(role_item):
    """TC-004: role item has escalates_to field."""
    et = role_item.get("escalates_to")
    assert et == "Lead"


def test_role_def_skills(role_item):
    """TC-004: role item has skills list."""
    skills = role_item.get("skills", [])
    assert len(skills) >= 1


def test_role_def_tools(role_item):
    """TC-004: role item has tools list."""
    tools = role_item.get("tools", [])
    assert len(tools) >= 1


def test_role_def_description():
    """TC-004: role item with description field parses it correctly."""
    src = """
role Director {
    tier: 1
    responsibility: "Vision"
}
"""
    ast = parse_src(src)
    roles = [i for i in ast["items"] if i.get("kind") == "role"]
    assert roles[0]["name"] == "Director"


# ============================================================
# TC-005: StudioDef AST fields
# ============================================================

STUDIO_SNIPPET = """
studio ArkStudio {
    tier 1 { Lead }
    tier 2 { Planner, Coder }
    tier 3 { Specialist }
}
"""


@pytest.fixture(scope="module")
def studio_ast():
    return parse_src(STUDIO_SNIPPET)


@pytest.fixture(scope="module")
def studio_item(studio_ast):
    studios = [i for i in studio_ast["items"] if i.get("kind") == "studio"]
    assert studios, "Expected at least one studio item"
    return studios[0]


def test_studio_def_kind_field(studio_item):
    """TC-005: studio item has kind == 'studio'."""
    assert studio_item["kind"] == "studio"


def test_studio_def_name(studio_item):
    """TC-005: studio item has correct name."""
    assert studio_item["name"] == "ArkStudio"


def test_studio_def_tier_groups(studio_item):
    """TC-005: studio item has tiers list."""
    tiers = studio_item.get("tiers", [])
    assert len(tiers) >= 1


def test_studio_def_tier_group_members(studio_item):
    """TC-005: studio tier groups contain member names."""
    tiers = studio_item.get("tiers", [])
    # Check that at least one tier group has members
    all_members = []
    for t in tiers:
        members = t.get("members", [])
        all_members.extend(members)
    assert len(all_members) >= 1


def test_studio_def_description():
    """TC-005: studio item without description still parses."""
    src = """
studio SmallStudio {
    tier 1 { Boss }
}
"""
    ast = parse_src(src)
    studios = [i for i in ast["items"] if i.get("kind") == "studio"]
    assert studios[0]["name"] == "SmallStudio"


# ============================================================
# TC-006: CommandDef, HookDef, RuleDef, TemplateDef AST fields
# ============================================================

COMMAND_SNIPPET = """
command CreateSpec {
    phase: planning
    prompt: "Write a specification document for the given feature."
    role: Planner
    output: spec_md
}
"""

HOOK_SNIPPET = """
hook OnPreCommit {
    event: pre_commit
    pattern: "*.ark"
    action: "python ark.py verify"
}
"""

RULE_SNIPPET = """
rule NoOrphanRoles {
    path: "specs/**/*.ark"
    constraint: "all_roles_referenced"
    severity: error
}
"""

TEMPLATE_SNIPPET = """
template AgentSpec {
    sections: ["Overview", "Responsibilities", "Tools", "Escalation"]
    bound_to: role
}
"""


@pytest.fixture(scope="module")
def command_item():
    ast = parse_src(COMMAND_SNIPPET)
    cmds = [i for i in ast["items"] if i.get("kind") == "command"]
    assert cmds, "Expected command item"
    return cmds[0]


@pytest.fixture(scope="module")
def hook_item():
    ast = parse_src(HOOK_SNIPPET)
    hooks = [i for i in ast["items"] if i.get("kind") == "hook"]
    assert hooks, "Expected hook item"
    return hooks[0]


@pytest.fixture(scope="module")
def rule_item():
    ast = parse_src(RULE_SNIPPET)
    rules = [i for i in ast["items"] if i.get("kind") == "rule"]
    assert rules, "Expected rule item"
    return rules[0]


@pytest.fixture(scope="module")
def template_item():
    ast = parse_src(TEMPLATE_SNIPPET)
    templates = [i for i in ast["items"] if i.get("kind") == "template"]
    assert templates, "Expected template item"
    return templates[0]


# CommandDef
def test_command_def_kind_field(command_item):
    """TC-006: command item has kind == 'command'."""
    assert command_item["kind"] == "command"


def test_command_def_phase(command_item):
    """TC-006: command item has phase field."""
    # phase is an IDENT stored as a plain string
    assert command_item.get("phase") == "planning"


def test_command_def_role(command_item):
    """TC-006: command item has role field."""
    # role is an IDENT stored as a plain string
    assert command_item.get("role") == "Planner"


def test_command_def_prompt(command_item):
    """TC-006: command item has prompt field."""
    prompt = command_item.get("prompt")
    assert prompt is not None
    assert len(prompt) > 0


def test_command_def_output(command_item):
    """TC-006: command item has output field (stored as IDENT string)."""
    assert command_item.get("output") == "spec_md"


# HookDef
def test_hook_def_kind_field(hook_item):
    """TC-006: hook item has kind == 'hook'."""
    assert hook_item["kind"] == "hook"


def test_hook_def_event(hook_item):
    """TC-006: hook item has event field (stored as IDENT string)."""
    assert hook_item.get("event") == "pre_commit"


def test_hook_def_pattern(hook_item):
    """TC-006: hook item has pattern field (stored as quoted string in AST)."""
    pattern = hook_item.get("pattern")
    assert pattern is not None
    # Pattern is stored as a quoted string in AST: '"*.ark"' or '*.ark'
    assert "*.ark" in pattern


def test_hook_def_action(hook_item):
    """TC-006: hook item has action field."""
    action = hook_item.get("action")
    assert action is not None
    assert len(action) > 0


# RuleDef
def test_rule_def_kind_field(rule_item):
    """TC-006: rule item has kind == 'rule'."""
    assert rule_item["kind"] == "rule"


def test_rule_def_path(rule_item):
    """TC-006: rule item has path field."""
    path = rule_item.get("path")
    assert path is not None
    assert len(path) > 0


def test_rule_def_constraint(rule_item):
    """TC-006: rule item has constraint field."""
    constraint = rule_item.get("constraint")
    assert constraint is not None
    assert len(constraint) > 0


def test_rule_def_severity(rule_item):
    """TC-006: rule item has severity field."""
    assert rule_item.get("severity") == "error"


# TemplateDef
def test_template_def_kind_field(template_item):
    """TC-006: template item has kind == 'template'."""
    assert template_item["kind"] == "template"


def test_template_def_sections(template_item):
    """TC-006: template item has sections list."""
    sections = template_item.get("sections", [])
    assert len(sections) >= 1


def test_template_def_bound_to(template_item):
    """TC-006: template item has bound_to field."""
    assert template_item.get("bound_to") == "role"


# ============================================================
# TC-007: ArkFile indices — roles, studios, commands dicts
# ============================================================

MULTI_ITEM_SNIPPET = """
role Planner {
    tier: 2
    responsibility: "plan"
}

role Coder {
    tier: 3
    responsibility: "code"
    escalates_to: Planner
}

studio DevStudio {
    tier 2 { Planner }
    tier 3 { Coder }
}

command WriteSpec {
    phase: planning
    role: Planner
}
"""


@pytest.fixture(scope="module")
def multi_ast():
    return parse_src(MULTI_ITEM_SNIPPET)


def test_arkfile_has_roles_dict(multi_ast):
    """TC-007: ArkFile JSON has a 'roles' dict key."""
    assert "roles" in multi_ast


def test_arkfile_has_studios_dict(multi_ast):
    """TC-007: ArkFile JSON has a 'studios' dict key."""
    assert "studios" in multi_ast


def test_arkfile_has_commands_dict(multi_ast):
    """TC-007: ArkFile JSON has a 'commands' dict key."""
    assert "commands" in multi_ast


def test_roles_dict_keyed_by_name(multi_ast):
    """TC-007: roles dict is keyed by role name."""
    roles = multi_ast.get("roles", {})
    assert "Planner" in roles
    assert "Coder" in roles


def test_studios_dict_keyed_by_name(multi_ast):
    """TC-007: studios dict is keyed by studio name."""
    studios = multi_ast.get("studios", {})
    assert "DevStudio" in studios


def test_commands_dict_keyed_by_name(multi_ast):
    """TC-007: commands dict is keyed by command name."""
    commands = multi_ast.get("commands", {})
    assert "WriteSpec" in commands


# ============================================================
# TC-008: stdlib/studio.ark parses correctly
# ============================================================

STUDIO_ARK = REPO_ROOT / "dsl" / "stdlib" / "studio.ark"


@pytest.fixture(scope="module")
def stdlib_ast():
    if not STUDIO_ARK.exists():
        pytest.skip("dsl/stdlib/studio.ark not found")
    return parse_file(STUDIO_ARK)


def test_stdlib_studio_ark_parses(stdlib_ast):
    """TC-008: stdlib/studio.ark parses without errors."""
    assert "items" in stdlib_ast
    assert len(stdlib_ast["items"]) > 0


def test_stdlib_studio_ark_has_tier_enum(stdlib_ast):
    """TC-008: stdlib/studio.ark contains Tier enum."""
    enums = [i for i in stdlib_ast["items"] if i.get("kind") == "enum"]
    names = {e["name"] for e in enums}
    assert "Tier" in names


def test_stdlib_studio_ark_has_agent_tool_enum(stdlib_ast):
    """TC-008: stdlib/studio.ark contains AgentTool enum."""
    enums = [i for i in stdlib_ast["items"] if i.get("kind") == "enum"]
    names = {e["name"] for e in enums}
    assert "AgentTool" in names


def test_stdlib_studio_ark_has_hook_event_enum(stdlib_ast):
    """TC-008: stdlib/studio.ark contains HookEvent enum."""
    enums = [i for i in stdlib_ast["items"] if i.get("kind") == "enum"]
    names = {e["name"] for e in enums}
    assert "HookEvent" in names


# ============================================================
# TC-009: All enum and struct definitions are well-formed
# ============================================================

def _enum_variant_names(enum_item: dict) -> list:
    """Extract variant name strings from an enum item (variants may be dicts)."""
    variants = enum_item.get("variants", [])
    return [v["name"] if isinstance(v, dict) else v for v in variants]


def test_tier_enum_has_director_lead_specialist(stdlib_ast):
    """TC-009: Tier enum has Director, Lead, Specialist variants."""
    enums = {i["name"]: i for i in stdlib_ast["items"] if i.get("kind") == "enum"}
    tier = enums.get("Tier", {})
    names = _enum_variant_names(tier)
    assert "Director" in names
    assert "Lead" in names
    assert "Specialist" in names


def test_agent_tool_enum_covers_claude_tools(stdlib_ast):
    """TC-009: AgentTool enum covers Read, Write, Edit, Bash."""
    enums = {i["name"]: i for i in stdlib_ast["items"] if i.get("kind") == "enum"}
    agent_tool = enums.get("AgentTool", {})
    names = _enum_variant_names(agent_tool)
    for expected in ["Read", "Write", "Edit", "Bash"]:
        assert expected in names, f"AgentTool missing variant '{expected}'"


def test_hook_event_enum_covers_required_events(stdlib_ast):
    """TC-009: HookEvent enum covers pre_commit, post_commit, pre_push, post_push."""
    enums = {i["name"]: i for i in stdlib_ast["items"] if i.get("kind") == "enum"}
    hook_event = enums.get("HookEvent", {})
    names = _enum_variant_names(hook_event)
    for expected in ["pre_commit", "post_commit", "pre_push", "post_push"]:
        assert expected in names, f"HookEvent missing variant '{expected}'"


def test_severity_enum_has_error_warning_info(stdlib_ast):
    """TC-009: Severity enum has error, warning, info variants."""
    enums = {i["name"]: i for i in stdlib_ast["items"] if i.get("kind") == "enum"}
    severity = enums.get("Severity", {})
    names = _enum_variant_names(severity)
    assert "error" in names
    assert "warning" in names
    assert "info" in names


def test_workflow_phase_enum_has_required_phases(stdlib_ast):
    """TC-009: WorkflowPhase enum has planning, implementation, review, testing."""
    enums = {i["name"]: i for i in stdlib_ast["items"] if i.get("kind") == "enum"}
    wp = enums.get("WorkflowPhase", {})
    names = _enum_variant_names(wp)
    for expected in ["planning", "implementation", "review", "testing"]:
        assert expected in names, f"WorkflowPhase missing variant '{expected}'"


def test_struct_escalation_path_fields(stdlib_ast):
    """TC-009: EscalationPath struct has from_role, to_role, condition fields."""
    structs = {i["name"]: i for i in stdlib_ast["items"] if i.get("kind") == "struct"}
    ep = structs.get("EscalationPath", {})
    field_names = [f["name"] for f in ep.get("fields", [])]
    assert "from_role" in field_names
    assert "to_role" in field_names
    assert "condition" in field_names


def test_struct_skill_fields(stdlib_ast):
    """TC-009: Skill struct has name and category fields."""
    structs = {i["name"]: i for i in stdlib_ast["items"] if i.get("kind") == "struct"}
    skill = structs.get("Skill", {})
    field_names = [f["name"] for f in skill.get("fields", [])]
    assert "name" in field_names
    assert "category" in field_names


def test_struct_command_output_fields(stdlib_ast):
    """TC-009: CommandOutput struct has format and sections fields."""
    structs = {i["name"]: i for i in stdlib_ast["items"] if i.get("kind") == "struct"}
    co = structs.get("CommandOutput", {})
    field_names = [f["name"] for f in co.get("fields", [])]
    assert "format" in field_names
    assert "sections" in field_names
