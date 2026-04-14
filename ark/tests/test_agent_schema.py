"""Tests for dsl/stdlib/agent.ark — schema parsing and type completeness.

Covers TC-001 and TC-002.
"""

import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "parser"))

from ark_parser import parse as _ark_parse  # noqa: E402

AGENT_ARK = REPO_ROOT / "dsl" / "stdlib" / "agent.ark"


def _parse_agent_ark():
    """Parse dsl/stdlib/agent.ark and return the ArkFile."""
    source = AGENT_ARK.read_text(encoding="utf-8")
    return _ark_parse(source, file_path=AGENT_ARK)


# ---------------------------------------------------------------------------
# TC-001
# ---------------------------------------------------------------------------

def test_agent_ark_parses():
    """agent.ark parses without raising exceptions; result is a non-None ArkFile."""
    result = _parse_agent_ark()
    assert result is not None


# ---------------------------------------------------------------------------
# TC-002 — all expected items present
# ---------------------------------------------------------------------------

EXPECTED_ENUMS = {
    "Platform",
    "BackendType",
    "ModelProvider",
    "SkillStatus",
    "MessageFormat",
    "LearningMode",
}

EXPECTED_STRUCTS = {
    "GatewayRoute",
    "ModelParams",
    "ResourceLimits",
    "SkillTrigger",
    "ImprovementEntry",
    "CronSchedule",
}


def test_agent_types_complete():
    """All expected enum and struct items are present in the ArkFile."""
    ark_file = _parse_agent_ark()
    import json
    from ark_parser import to_json as _ark_to_json
    ast = json.loads(_ark_to_json(ark_file))
    items = ast.get("items", [])

    found_enums = {it["name"] for it in items if it.get("kind") == "enum"}
    found_structs = {it["name"] for it in items if it.get("kind") in ("struct", "primitive")}

    for enum_name in EXPECTED_ENUMS:
        assert enum_name in found_enums, f"Missing enum: {enum_name}"

    for struct_name in EXPECTED_STRUCTS:
        assert struct_name in found_structs, f"Missing struct: {struct_name}"


# ---------------------------------------------------------------------------
# Individual enum variant tests (supporting TC-002)
# ---------------------------------------------------------------------------

def _get_enum_variants(ark_file_ast: dict, enum_name: str) -> set:
    """Return the set of variant names for a given enum."""
    for item in ark_file_ast.get("items", []):
        if item.get("kind") == "enum" and item.get("name") == enum_name:
            variants = item.get("variants", [])
            result = set()
            for v in variants:
                if isinstance(v, str):
                    result.add(v)
                elif isinstance(v, dict):
                    result.add(v.get("name", ""))
            return result
    return set()


def _get_ast():
    import json
    from ark_parser import to_json as _ark_to_json
    ark_file = _parse_agent_ark()
    return json.loads(_ark_to_json(ark_file))


def test_platform_enum_variants():
    """Platform enum has expected variants."""
    ast = _get_ast()
    variants = _get_enum_variants(ast, "Platform")
    for v in ("terminal", "telegram", "discord", "slack", "whatsapp", "signal"):
        assert v in variants, f"Platform missing variant: {v}"


def test_backend_type_enum_variants():
    """BackendType enum has expected variants."""
    ast = _get_ast()
    variants = _get_enum_variants(ast, "BackendType")
    for v in ("local", "docker", "ssh", "daytona", "singularity", "modal"):
        assert v in variants, f"BackendType missing variant: {v}"


def test_model_provider_enum_variants():
    """ModelProvider enum has expected variants."""
    ast = _get_ast()
    variants = _get_enum_variants(ast, "ModelProvider")
    for v in ("nous", "openrouter", "openai", "anthropic"):
        assert v in variants, f"ModelProvider missing variant: {v}"


def test_skill_status_enum_variants():
    """SkillStatus enum has expected variants."""
    ast = _get_ast()
    variants = _get_enum_variants(ast, "SkillStatus")
    for v in ("active", "deprecated", "draft", "archived"):
        assert v in variants, f"SkillStatus missing variant: {v}"


def test_message_format_enum_variants():
    """MessageFormat enum has expected variants."""
    ast = _get_ast()
    variants = _get_enum_variants(ast, "MessageFormat")
    for v in ("plain", "markdown", "html", "json"):
        assert v in variants, f"MessageFormat missing variant: {v}"


def test_learning_mode_enum_variants():
    """LearningMode enum has expected variants."""
    ast = _get_ast()
    variants = _get_enum_variants(ast, "LearningMode")
    for v in ("passive", "active", "supervised"):
        assert v in variants, f"LearningMode missing variant: {v}"
