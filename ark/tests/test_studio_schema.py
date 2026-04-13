"""
Tests for dsl/stdlib/studio.ark — Schema validation (TC-001, TC-002, TC-003).

Validates that studio.ark parses cleanly and that all enum and struct
definitions are present and well-formed.
"""

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_PARSER_DIR = REPO_ROOT / "tools" / "parser"
if str(_PARSER_DIR) not in sys.path:
    sys.path.insert(0, str(_PARSER_DIR))

from ark_parser import parse as ark_parse, to_json as ark_to_json  # noqa: E402
import json


STUDIO_ARK = REPO_ROOT / "dsl" / "stdlib" / "studio.ark"


# ============================================================
# Helpers
# ============================================================

def parse_studio_ark():
    """Parse the actual studio.ark stdlib file and return the AST dict."""
    source = STUDIO_ARK.read_text(encoding="utf-8")
    ark_file = ark_parse(source, file_path=STUDIO_ARK)
    return json.loads(ark_to_json(ark_file))


def parse_snippet(source: str) -> dict:
    """Parse an inline ARK snippet and return the AST dict."""
    ark_file = ark_parse(source)
    return json.loads(ark_to_json(ark_file))


def items_by_name(ast: dict) -> dict:
    """Return a dict of {name: item} from ast['items']."""
    return {i.get("name"): i for i in ast.get("items", []) if i.get("name")}


# ============================================================
# TC-001: Lark grammar parses all 6 new item kinds — inline snippets
# ============================================================

def test_role_item_parses():
    """TC-001: role item kind parses without errors."""
    src = """
role Planner {
    tier: 2
    responsibility: "Plan features"
    responsibility: "Write specs"
    escalates_to: Lead
    skills: [planning, communication]
    tools: [Read, Write, Edit]
}
"""
    ast = parse_snippet(src)
    kinds = {i["kind"] for i in ast["items"]}
    assert "role" in kinds


def test_studio_item_parses():
    """TC-001: studio item kind parses without errors."""
    src = """
studio ArkStudio {
    tier 1 { Lead }
    tier 2 { Planner }
}
"""
    ast = parse_snippet(src)
    kinds = {i["kind"] for i in ast["items"]}
    assert "studio" in kinds


def test_command_item_parses():
    """TC-001: command item kind parses without errors."""
    src = """
command CreateSpec {
    phase: planning
    prompt: "Create a spec for the given feature"
    role: Planner
    output: spec_md
}
"""
    ast = parse_snippet(src)
    kinds = {i["kind"] for i in ast["items"]}
    assert "command" in kinds


def test_hook_item_parses():
    """TC-001: hook item kind parses without errors."""
    src = """
hook OnCommit {
    event: pre_commit
    pattern: "*.ark"
    action: "python ark.py verify"
}
"""
    ast = parse_snippet(src)
    kinds = {i["kind"] for i in ast["items"]}
    assert "hook" in kinds


def test_rule_item_parses():
    """TC-001: rule item kind parses without errors."""
    src = """
rule NoDirectCycles {
    path: "specs/**/*.ark"
    constraint: "acyclic"
    severity: error
}
"""
    ast = parse_snippet(src)
    kinds = {i["kind"] for i in ast["items"]}
    assert "rule" in kinds


def test_template_item_parses():
    """TC-001: template item kind parses without errors."""
    src = """
template AgentSpec {
    sections: ["Overview", "Responsibilities", "Tools"]
    bound_to: role
}
"""
    ast = parse_snippet(src)
    kinds = {i["kind"] for i in ast["items"]}
    assert "template" in kinds


# ============================================================
# TC-002: Pest grammar — stub tests (grammar mirrors Lark)
# ============================================================

def test_pest_role_item_parses():
    """TC-002: role item is expressible in the Lark grammar (mirrors Pest)."""
    src = """
role Director {
    tier: 1
    responsibility: "Vision"
    responsibility: "Strategy"
}
"""
    ast = parse_snippet(src)
    roles = [i for i in ast["items"] if i.get("kind") == "role"]
    assert len(roles) == 1
    assert roles[0]["name"] == "Director"


def test_pest_studio_item_parses():
    """TC-002: studio item is expressible in the Lark grammar (mirrors Pest)."""
    src = """
studio GameStudio {
    tier 1 { Director }
}
"""
    ast = parse_snippet(src)
    studios = [i for i in ast["items"] if i.get("kind") == "studio"]
    assert len(studios) == 1
    assert studios[0]["name"] == "GameStudio"


def test_pest_command_item_parses():
    """TC-002: command item is expressible in the Lark grammar (mirrors Pest)."""
    src = """
command ReviewSpec {
    phase: review
    role: Reviewer
}
"""
    ast = parse_snippet(src)
    commands = [i for i in ast["items"] if i.get("kind") == "command"]
    assert len(commands) == 1
    assert commands[0]["name"] == "ReviewSpec"


def test_pest_hook_item_parses():
    """TC-002: hook item is expressible in the Lark grammar (mirrors Pest)."""
    src = """
hook OnPush {
    event: pre_push
    pattern: "*.ark"
    action: "ark verify"
}
"""
    ast = parse_snippet(src)
    hooks = [i for i in ast["items"] if i.get("kind") == "hook"]
    assert len(hooks) == 1
    assert hooks[0]["name"] == "OnPush"


def test_pest_rule_item_parses():
    """TC-002: rule item is expressible in the Lark grammar (mirrors Pest)."""
    src = """
rule FileSize {
    path: "*.ark"
    constraint: "size < 1000"
    severity: warning
}
"""
    ast = parse_snippet(src)
    rules = [i for i in ast["items"] if i.get("kind") == "rule"]
    assert len(rules) == 1
    assert rules[0]["name"] == "FileSize"


def test_pest_template_item_parses():
    """TC-002: template item is expressible in the Lark grammar (mirrors Pest)."""
    src = """
template CommandSpec {
    sections: ["Prompt", "Output"]
    bound_to: command
}
"""
    ast = parse_snippet(src)
    templates = [i for i in ast["items"] if i.get("kind") == "template"]
    assert len(templates) == 1
    assert templates[0]["name"] == "CommandSpec"


# ============================================================
# TC-003: Regression — existing .ark files still parse
# ============================================================

def test_existing_code_graph_still_parses():
    """TC-003: Existing code graph spec still parses after grammar changes."""
    p = REPO_ROOT / "specs" / "test_minimal.ark"
    if not p.exists():
        pytest.skip("test_minimal.ark not found")
    source = p.read_text(encoding="utf-8")
    ark_file = ark_parse(source, file_path=p)
    ast = json.loads(ark_to_json(ark_file))
    assert len(ast["items"]) >= 1


def test_existing_root_ark_still_parses():
    """TC-003: root.ark still parses after grammar changes."""
    p = REPO_ROOT / "specs" / "root.ark"
    if not p.exists():
        pytest.skip("root.ark not found")
    source = p.read_text(encoding="utf-8")
    ark_file = ark_parse(source, file_path=p)
    ast = json.loads(ark_to_json(ark_file))
    assert len(ast["items"]) >= 1


def test_existing_stdlib_types_still_parses():
    """TC-003: stdlib/types.ark still parses after grammar changes."""
    p = REPO_ROOT / "dsl" / "stdlib" / "types.ark"
    if not p.exists():
        pytest.skip("stdlib/types.ark not found")
    source = p.read_text(encoding="utf-8")
    ark_file = ark_parse(source, file_path=p)
    ast = json.loads(ark_to_json(ark_file))
    assert len(ast["items"]) >= 1


# ============================================================
# studio.ark content validation — enum/struct presence
# ============================================================

@pytest.fixture(scope="module")
def studio_ast():
    """Parse studio.ark once and return the AST dict."""
    if not STUDIO_ARK.exists():
        pytest.skip("dsl/stdlib/studio.ark not found")
    return parse_studio_ark()


def test_studio_ark_parses_without_error(studio_ast):
    """studio.ark parses cleanly with no exception."""
    assert "items" in studio_ast
    assert len(studio_ast["items"]) > 0


def test_tier_enum_present(studio_ast):
    """Tier enum is present in studio.ark."""
    enums = [i for i in studio_ast["items"] if i.get("kind") == "enum"]
    names = {e["name"] for e in enums}
    assert "Tier" in names


def test_agent_tool_enum_present(studio_ast):
    """AgentTool enum is present in studio.ark."""
    enums = [i for i in studio_ast["items"] if i.get("kind") == "enum"]
    names = {e["name"] for e in enums}
    assert "AgentTool" in names


def test_hook_event_enum_present(studio_ast):
    """HookEvent enum is present in studio.ark."""
    enums = [i for i in studio_ast["items"] if i.get("kind") == "enum"]
    names = {e["name"] for e in enums}
    assert "HookEvent" in names


def test_severity_enum_present(studio_ast):
    """Severity enum is present in studio.ark."""
    enums = [i for i in studio_ast["items"] if i.get("kind") == "enum"]
    names = {e["name"] for e in enums}
    assert "Severity" in names


def test_workflow_phase_enum_present(studio_ast):
    """WorkflowPhase enum is present in studio.ark."""
    enums = [i for i in studio_ast["items"] if i.get("kind") == "enum"]
    names = {e["name"] for e in enums}
    assert "WorkflowPhase" in names


def test_skill_struct_present(studio_ast):
    """Skill struct is present in studio.ark."""
    structs = [i for i in studio_ast["items"] if i.get("kind") == "struct"]
    names = {s["name"] for s in structs}
    assert "Skill" in names


def test_escalation_path_struct_present(studio_ast):
    """EscalationPath struct is present in studio.ark."""
    structs = [i for i in studio_ast["items"] if i.get("kind") == "struct"]
    names = {s["name"] for s in structs}
    assert "EscalationPath" in names


def test_command_output_struct_present(studio_ast):
    """CommandOutput struct is present in studio.ark."""
    structs = [i for i in studio_ast["items"] if i.get("kind") == "struct"]
    names = {s["name"] for s in structs}
    assert "CommandOutput" in names


def _variant_names(enum_item: dict) -> list:
    """Extract variant name strings from an enum item's variants list."""
    variants = enum_item.get("variants", [])
    return [v["name"] if isinstance(v, dict) else v for v in variants]


def test_tier_enum_variants(studio_ast):
    """Tier enum has Director, Lead, Specialist variants."""
    enums = {i["name"]: i for i in studio_ast["items"] if i.get("kind") == "enum"}
    tier = enums.get("Tier")
    assert tier is not None
    names = _variant_names(tier)
    assert "Director" in names
    assert "Lead" in names
    assert "Specialist" in names


def test_skill_struct_fields(studio_ast):
    """Skill struct has 'name' and 'category' fields."""
    structs = {i["name"]: i for i in studio_ast["items"] if i.get("kind") == "struct"}
    skill = structs.get("Skill")
    assert skill is not None
    field_names = [f["name"] for f in skill.get("fields", [])]
    assert "name" in field_names
    assert "category" in field_names


def test_escalation_path_struct_fields(studio_ast):
    """EscalationPath struct has 'from_role', 'to_role', 'condition' fields."""
    structs = {i["name"]: i for i in studio_ast["items"] if i.get("kind") == "struct"}
    ep = structs.get("EscalationPath")
    assert ep is not None
    field_names = [f["name"] for f in ep.get("fields", [])]
    assert "from_role" in field_names
    assert "to_role" in field_names
    assert "condition" in field_names


def test_command_output_struct_fields(studio_ast):
    """CommandOutput struct has 'format' and 'sections' fields."""
    structs = {i["name"]: i for i in studio_ast["items"] if i.get("kind") == "struct"}
    co = structs.get("CommandOutput")
    assert co is not None
    field_names = [f["name"] for f in co.get("fields", [])]
    assert "format" in field_names
    assert "sections" in field_names
