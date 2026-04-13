"""
Tests for studio verification functions (TC-010 through TC-014).

Tests the studio_verify.py module functions for:
  - escalation acyclicity (verify_escalation_acyclicity)
  - command-role resolution (verify_command_resolution)
  - hook event validity (verify_hook_events)
  - rule constraints (verify_rule_constraints)
  - tool permission consistency (verify_tool_permissions)
  - combined verify_studio entry point
"""

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_VERIFY_DIR = REPO_ROOT / "tools" / "verify"
if str(_VERIFY_DIR) not in sys.path:
    sys.path.insert(0, str(_VERIFY_DIR))

from studio_verify import (  # noqa: E402
    verify_escalation_acyclicity,
    verify_command_resolution,
    verify_hook_events,
    verify_rule_constraints,
    verify_rule_satisfiability,
    verify_tool_permissions,
    verify_studio,
    ALLOWED_HOOK_EVENTS,
    DEFAULT_ALLOWED_TOOLS,
)


# ============================================================
# TC-010: Escalation Acyclicity
# ============================================================

def test_acyclic_escalation_passes():
    """TC-010: Valid linear escalation chain produces no errors."""
    roles = [
        {"name": "Specialist", "tier": 3, "escalates_to": "Lead"},
        {"name": "Lead", "tier": 2, "escalates_to": "Director"},
        {"name": "Director", "tier": 1},
    ]
    errors = verify_escalation_acyclicity(roles)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_direct_cycle_detected():
    """TC-010: Direct cycle A→B→A is detected as an error."""
    roles = [
        {"name": "Alpha", "tier": 2, "escalates_to": "Beta"},
        {"name": "Beta", "tier": 2, "escalates_to": "Alpha"},
    ]
    errors = verify_escalation_acyclicity(roles)
    assert len(errors) > 0, "Expected cycle error"
    assert any("cycle" in e.lower() for e in errors)


def test_indirect_cycle_detected():
    """TC-010: Indirect cycle A→B→C→A is detected as an error."""
    roles = [
        {"name": "A", "tier": 2, "escalates_to": "B"},
        {"name": "B", "tier": 2, "escalates_to": "C"},
        {"name": "C", "tier": 2, "escalates_to": "A"},
    ]
    errors = verify_escalation_acyclicity(roles)
    assert len(errors) > 0, "Expected cycle error for indirect cycle"
    assert any("cycle" in e.lower() for e in errors)


def test_director_with_no_escalates_to_passes():
    """TC-010: Director-tier role with no escalates_to is valid."""
    roles = [
        {"name": "ChiefDirector", "tier": 1},
    ]
    errors = verify_escalation_acyclicity(roles)
    # No escalates_to on a director — should pass
    assert all("ChiefDirector" not in e or "escalates_to" not in e for e in errors), \
        f"Unexpected errors for director: {errors}"


def test_multiple_independent_chains_pass():
    """TC-010: Multiple independent escalation chains all pass."""
    roles = [
        # Chain 1
        {"name": "SpecA", "tier": 3, "escalates_to": "LeadA"},
        {"name": "LeadA", "tier": 2, "escalates_to": "DirA"},
        {"name": "DirA", "tier": 1},
        # Chain 2
        {"name": "SpecB", "tier": 3, "escalates_to": "LeadB"},
        {"name": "LeadB", "tier": 2, "escalates_to": "DirB"},
        {"name": "DirB", "tier": 1},
    ]
    errors = verify_escalation_acyclicity(roles)
    assert errors == [], f"Expected no errors for independent chains, got: {errors}"


def test_missing_escalation_target_detected():
    """TC-010: escalates_to referencing a non-existent role is an error."""
    roles = [
        {"name": "Specialist", "tier": 3, "escalates_to": "NonExistentLead"},
    ]
    errors = verify_escalation_acyclicity(roles)
    assert len(errors) > 0, "Expected error for missing escalation target"
    assert any("NonExistentLead" in e for e in errors)


def test_empty_roles_passes():
    """TC-010: Empty roles list produces no errors."""
    errors = verify_escalation_acyclicity([])
    assert errors == []


# ============================================================
# TC-011: Command-Role Resolution
# ============================================================

def test_command_resolves_existing_role_passes():
    """TC-011: Command with a valid required_role produces no errors."""
    roles = [{"name": "Planner", "tools": ["Read", "Write"]}]
    commands = [{"name": "WriteSpec", "role": "Planner"}]
    errors = verify_command_resolution(commands, roles)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_command_missing_role_detected():
    """TC-011: Command referencing a non-existent role is reported."""
    roles = [{"name": "Planner", "tools": ["Read", "Write"]}]
    commands = [{"name": "WriteSpec", "role": "NonExistentRole"}]
    errors = verify_command_resolution(commands, roles)
    assert len(errors) > 0, "Expected error for missing role"
    assert any("NonExistentRole" in e for e in errors)


def test_command_role_has_required_tools_passes():
    """TC-011: Command whose role has all required tools produces no errors."""
    roles = [{"name": "Coder", "tools": ["Read", "Write", "Edit", "Bash"]}]
    commands = [{"name": "CodeFeature", "role": "Coder", "required_tools": ["Read", "Bash"]}]
    errors = verify_command_resolution(commands, roles)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_command_role_missing_tool_detected():
    """TC-011: Command whose role is missing a required tool is reported."""
    roles = [{"name": "Coder", "tools": ["Read", "Write"]}]
    commands = [{"name": "DeployCmd", "role": "Coder", "required_tools": ["Bash"]}]
    errors = verify_command_resolution(commands, roles)
    assert len(errors) > 0, "Expected error for missing tool"
    assert any("Bash" in e for e in errors)


def test_command_without_role_constraint_passes():
    """TC-011: Command without a role field is not checked."""
    roles = []
    commands = [{"name": "GlobalCmd"}]
    errors = verify_command_resolution(commands, roles)
    assert errors == []


# ============================================================
# TC-012: Hook Event Validity
# ============================================================

def test_valid_hook_event_passes():
    """TC-012: Hook with a known event type produces no errors."""
    hooks = [{"name": "OnCommit", "event": "pre_commit"}]
    errors = verify_hook_events(hooks)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_invalid_hook_event_detected():
    """TC-012: Hook with an unknown event type is reported."""
    hooks = [{"name": "BadHook", "event": "on_teleport"}]
    errors = verify_hook_events(hooks)
    assert len(errors) > 0, "Expected error for invalid event"
    assert any("on_teleport" in e for e in errors)


def test_all_allowed_events_pass():
    """TC-012: All events in ALLOWED_HOOK_EVENTS pass validation."""
    hooks = [{"name": f"Hook_{event}", "event": event} for event in ALLOWED_HOOK_EVENTS]
    errors = verify_hook_events(hooks)
    assert errors == [], f"Expected no errors for allowed events, got: {errors}"


def test_unknown_event_name_detected():
    """TC-012: A completely made-up event name is detected."""
    hooks = [{"name": "WeirdHook", "event": "on_magic_unicorn"}]
    errors = verify_hook_events(hooks)
    assert len(errors) > 0, "Expected error for unknown event"


def test_hook_missing_event_field_detected():
    """TC-012: Hook without an event field is reported."""
    hooks = [{"name": "NoEventHook"}]
    errors = verify_hook_events(hooks)
    assert len(errors) > 0, "Expected error for missing event field"


# ============================================================
# TC-013: Rule Constraints
# ============================================================

def test_satisfiable_constraint_passes():
    """TC-013: Rule with a satisfiable constraint produces no errors."""
    rules = [{"name": "FileSizeRule", "path": "*.ark", "constraint": "x > 0"}]
    errors = verify_rule_satisfiability(rules)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_unsatisfiable_constraint_detected():
    """TC-013: Rule with constraint 'false' is reported as unsatisfiable."""
    rules = [{"name": "ImpossibleRule", "path": "*.ark", "constraint": "false"}]
    errors = verify_rule_satisfiability(rules)
    assert len(errors) > 0, "Expected unsatisfiability error"
    assert any("unsatisfiable" in e.lower() or "trivially" in e.lower() for e in errors)


def test_empty_constraint_passes():
    """TC-013: Rule with empty constraint is skipped by satisfiability check."""
    # verify_rule_satisfiability skips empty constraints (verify_rule_constraints handles them)
    rules = [{"name": "EmptyRule", "path": "*.ark", "constraint": ""}]
    errors = verify_rule_satisfiability(rules)
    # Should not report SAT error for empty constraint
    assert not any("unsatisfiable" in e.lower() for e in errors)


def test_complex_satisfiable_constraint_passes():
    """TC-013: Complex satisfiable constraint (AND expression) produces no errors."""
    rules = [{"name": "ComplexRule", "path": "*.ark", "constraint": "x > 0 AND y < 100"}]
    errors = verify_rule_satisfiability(rules)
    assert errors == [], f"Expected no errors for satisfiable AND constraint, got: {errors}"


def test_rule_constraint_empty_path_error():
    """TC-013: Rule with empty path field is reported by verify_rule_constraints."""
    rules = [{"name": "NoPathRule", "constraint": "valid_constraint"}]
    errors = verify_rule_constraints(rules)
    assert len(errors) > 0, "Expected error for empty path"
    assert any("path" in e.lower() or "glob" in e.lower() for e in errors)


def test_rule_constraint_empty_constraint_error():
    """TC-013: Rule with empty constraint is reported by verify_rule_constraints."""
    rules = [{"name": "NoConstraintRule", "path": "*.ark"}]
    errors = verify_rule_constraints(rules)
    assert len(errors) > 0, "Expected error for empty constraint"
    assert any("constraint" in e.lower() for e in errors)


# ============================================================
# TC-014: Tool Permission Consistency
# ============================================================

def test_role_within_allowed_tools_passes():
    """TC-014: Role using only allowed tools produces no errors."""
    roles = [{"name": "Planner", "tools": ["Read", "Write", "Edit"]}]
    errors = verify_tool_permissions(roles)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_role_using_unpermitted_tool_detected():
    """TC-014: Role using a tool outside the allowed set is reported."""
    roles = [{"name": "Hacker", "tools": ["Read", "Exec", "SudoRm"]}]
    errors = verify_tool_permissions(roles)
    assert len(errors) > 0, "Expected error for unpermitted tools"
    assert any("Exec" in e or "SudoRm" in e for e in errors)


def test_director_full_toolset_passes():
    """TC-014: Director-tier role using all DEFAULT_ALLOWED_TOOLS passes."""
    roles = [{"name": "Director", "tier": 1, "tools": list(DEFAULT_ALLOWED_TOOLS)}]
    errors = verify_tool_permissions(roles)
    assert errors == [], f"Expected no errors for full default toolset, got: {errors}"


def test_specialist_restricted_toolset_passes():
    """TC-014: Specialist with a small subset of tools passes."""
    roles = [{"name": "Specialist", "tier": 3, "tools": ["Read", "Grep", "Glob"]}]
    errors = verify_tool_permissions(roles)
    assert errors == [], f"Expected no errors for restricted toolset, got: {errors}"


def test_custom_allowed_tools_enforced():
    """TC-014: verify_tool_permissions respects a custom allowed_tools set."""
    custom_allowed = {"Read", "Write"}
    roles = [{"name": "LimitedRole", "tools": ["Read", "Write", "Bash"]}]
    errors = verify_tool_permissions(roles, allowed_tools=custom_allowed)
    assert len(errors) > 0, "Expected error for Bash not in custom allowed set"
    assert any("Bash" in e for e in errors)


# ============================================================
# verify_studio — combined full check
# ============================================================

def _make_valid_ark_file():
    """Build a minimal valid ArkFile-like dict for verify_studio."""
    return {
        "roles": [
            {"name": "Specialist", "tier": 3, "escalates_to": "Lead",
             "tools": ["Read", "Write"]},
            {"name": "Lead", "tier": 2, "escalates_to": "Director",
             "tools": ["Read", "Write", "Edit"]},
            {"name": "Director", "tier": 1, "tools": ["Read", "Write", "Edit", "Bash"]},
        ],
        "commands": [
            {"name": "WriteSpec", "role": "Lead", "required_tools": ["Read"]},
        ],
        "hooks": [
            {"name": "OnCommit", "event": "pre_commit"},
        ],
        "rules": [
            {"name": "ArkRule", "path": "*.ark", "constraint": "x > 0"},
        ],
    }


def test_verify_studio_passes_on_valid_input():
    """verify_studio returns summary with 0 failed checks for valid data."""
    result = verify_studio(_make_valid_ark_file())
    assert "errors" in result
    assert "summary" in result
    summary = result["summary"]
    assert summary["failed"] == 0, f"Expected 0 failures, got: {result['errors']}"


def test_verify_studio_detects_cycle():
    """verify_studio reports escalation cycle in combined results."""
    ark_file = {
        "roles": [
            {"name": "A", "tier": 2, "escalates_to": "B"},
            {"name": "B", "tier": 2, "escalates_to": "A"},
        ],
        "commands": [],
        "hooks": [],
        "rules": [],
    }
    result = verify_studio(ark_file)
    assert len(result["errors"]) > 0, "Expected errors for cyclic escalation"
    assert any("cycle" in e.lower() for e in result["errors"])


def test_verify_studio_result_structure():
    """verify_studio result has expected keys: checks, errors, summary."""
    result = verify_studio(_make_valid_ark_file())
    assert "checks" in result
    assert "errors" in result
    assert "summary" in result
    summary = result["summary"]
    assert "total" in summary
    assert "passed" in summary
    assert "failed" in summary


def test_verify_studio_detects_invalid_hook_event():
    """verify_studio reports invalid hook event in combined results."""
    ark_file = {
        "roles": [],
        "commands": [],
        "hooks": [{"name": "BadHook", "event": "on_unicorn"}],
        "rules": [],
    }
    result = verify_studio(ark_file)
    assert any("on_unicorn" in e for e in result["errors"]), \
        f"Expected hook event error, got: {result['errors']}"
