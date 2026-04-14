"""Tests for tools/verify/agent_verify.py — 6 verification checks.

Covers TC-025 through TC-030.
"""

import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "verify"))

from agent_verify import (  # noqa: E402
    verify_gateway_references,
    verify_cron_references,
    verify_model_fallback_acyclicity,
    verify_resource_limits,
    verify_skill_trigger_overlap,
    verify_agent_completeness,
    verify_agent,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _statuses(results):
    return [r["status"] for r in results]


def _has_fail(results):
    return any(r["status"] == "fail" for r in results)


def _has_pass(results):
    return any(r["status"] == "pass" for r in results)


# ---------------------------------------------------------------------------
# Check 1: Gateway References
# ---------------------------------------------------------------------------

def test_gateway_refs_pass_when_resolved():
    """Gateway references pass when agent_ref and platform refs both exist."""
    gateways = [{"name": "gw1", "agent_ref": "my_agent", "platforms": ["terminal"]}]
    agents = {"my_agent": {}}
    platforms = {"terminal": {}}
    results = verify_gateway_references(gateways, agents, platforms)
    assert not _has_fail(results)


def test_gateway_refs_fail_unknown_agent():
    """Gateway reference fails when agent_ref does not exist in agents dict."""
    gateways = [{"name": "gw1", "agent_ref": "missing_agent", "platforms": []}]
    agents = {}
    platforms = {}
    results = verify_gateway_references(gateways, agents, platforms)
    assert _has_fail(results)
    assert any("missing_agent" in r["message"] for r in results if r["status"] == "fail")


def test_gateway_refs_fail_unknown_platform():
    """Gateway reference fails when a platform ref does not exist in platforms dict."""
    gateways = [{"name": "gw1", "agent_ref": "my_agent", "platforms": ["ghost_platform"]}]
    agents = {"my_agent": {}}
    platforms = {}
    results = verify_gateway_references(gateways, agents, platforms)
    assert _has_fail(results)


def test_gateway_refs_warn_no_agent_ref():
    """Gateway with no agent_ref produces a warning (not a fail)."""
    gateways = [{"name": "gw_no_ref"}]
    agents = {}
    platforms = {}
    results = verify_gateway_references(gateways, agents, platforms)
    assert any(r["status"] == "warn" for r in results)


def test_gateway_refs_empty_gateways():
    """Empty gateways list produces no results."""
    results = verify_gateway_references([], {}, {})
    assert results == []


# ---------------------------------------------------------------------------
# Check 2: Cron References
# ---------------------------------------------------------------------------

def test_cron_refs_pass_when_resolved():
    """Cron task references pass when agent_ref and platform_delivery exist."""
    cron_tasks = [{"name": "daily", "agent_ref": "bot", "platform_delivery": "terminal"}]
    agents = {"bot": {}}
    platforms = {"terminal": {}}
    results = verify_cron_references(cron_tasks, agents, platforms)
    assert not _has_fail(results)


def test_cron_refs_fail_unknown_agent():
    """Cron task fails when agent_ref does not exist."""
    cron_tasks = [{"name": "task", "agent_ref": "ghost_agent", "platform_delivery": "terminal"}]
    agents = {}
    platforms = {"terminal": {}}
    results = verify_cron_references(cron_tasks, agents, platforms)
    assert _has_fail(results)


def test_cron_refs_fail_unknown_platform():
    """Cron task fails when platform_delivery does not exist."""
    cron_tasks = [{"name": "task", "agent_ref": "bot", "platform_delivery": "ghost_platform"}]
    agents = {"bot": {}}
    platforms = {}
    results = verify_cron_references(cron_tasks, agents, platforms)
    assert _has_fail(results)


def test_cron_refs_empty():
    """Empty cron tasks list produces no results."""
    results = verify_cron_references([], {}, {})
    assert results == []


# ---------------------------------------------------------------------------
# Check 3: Model Fallback Acyclicity
# ---------------------------------------------------------------------------

def test_model_fallback_acyclic_passes():
    """Acyclic fallback chain A → B passes."""
    model_configs = {
        "primary": {"fallback": "fallback_model"},
        "fallback_model": {},
    }
    results = verify_model_fallback_acyclicity(model_configs)
    assert _has_pass(results)
    assert not _has_fail(results)


def test_model_fallback_cyclic_fails():
    """Cyclic fallback chain A → B → A is detected and fails."""
    model_configs = {
        "model_a": {"fallback": "model_b"},
        "model_b": {"fallback": "model_a"},
    }
    results = verify_model_fallback_acyclicity(model_configs)
    assert _has_fail(results)


def test_model_fallback_unknown_ref_fails():
    """Fallback reference to unknown model fails."""
    model_configs = {
        "primary": {"fallback": "nonexistent_model"},
    }
    results = verify_model_fallback_acyclicity(model_configs)
    assert _has_fail(results)


def test_model_fallback_no_fallbacks_passes():
    """Models without fallback chains pass trivially."""
    model_configs = {
        "model_a": {"provider": "anthropic"},
        "model_b": {"provider": "openai"},
    }
    results = verify_model_fallback_acyclicity(model_configs)
    assert not _has_fail(results)


def test_model_fallback_empty_passes():
    """Empty model configs dict returns empty results."""
    results = verify_model_fallback_acyclicity({})
    assert results == []


# ---------------------------------------------------------------------------
# Check 4: Resource Limits
# ---------------------------------------------------------------------------

def test_resource_limits_pass_valid():
    """Backend with valid positive resource limits passes."""
    backends = {
        "local_backend": {
            "cpu_cores": 4,
            "memory_mb": 2048,
            "timeout_seconds": 300,
        }
    }
    results = verify_resource_limits(backends)
    assert _has_pass(results)
    assert not _has_fail(results)


def test_resource_limits_fail_zero_cpu():
    """Backend with cpu_cores=0 fails resource limit check."""
    backends = {
        "bad_backend": {
            "cpu_cores": 0,
            "memory_mb": 1024,
            "timeout_seconds": 60,
        }
    }
    results = verify_resource_limits(backends)
    assert _has_fail(results)


def test_resource_limits_fail_negative_memory():
    """Backend with memory_mb=-1 fails resource limit check."""
    backends = {
        "neg_backend": {
            "cpu_cores": 1,
            "memory_mb": -1,
            "timeout_seconds": 60,
        }
    }
    results = verify_resource_limits(backends)
    assert _has_fail(results)


def test_resource_limits_warn_missing_field():
    """Backend missing a resource field produces a warning."""
    backends = {
        "partial_backend": {
            "cpu_cores": 2,
            # memory_mb and timeout_seconds missing
        }
    }
    results = verify_resource_limits(backends)
    assert any(r["status"] == "warn" for r in results)


def test_resource_limits_empty():
    """Empty backends dict produces no results."""
    results = verify_resource_limits({})
    assert results == []


# ---------------------------------------------------------------------------
# Check 5: Skill Trigger Overlap
# ---------------------------------------------------------------------------

def test_skill_trigger_overlap_no_overlap_passes():
    """Skills with different trigger patterns pass."""
    skills = [
        {"name": "skill_a", "trigger": "search|find", "priority": 1},
        {"name": "skill_b", "trigger": "hello|hi", "priority": 1},
    ]
    results = verify_skill_trigger_overlap(skills)
    assert _has_pass(results)
    assert not any(r["status"] == "warn" for r in results)


def test_skill_trigger_overlap_same_pattern_same_priority_warns():
    """Two skills with same trigger pattern and priority produce a warning."""
    skills = [
        {"name": "skill_a", "trigger": "search", "priority": 5},
        {"name": "skill_b", "trigger": "search", "priority": 5},
    ]
    results = verify_skill_trigger_overlap(skills)
    assert any(r["status"] == "warn" for r in results)


def test_skill_trigger_overlap_same_pattern_diff_priority_no_warn():
    """Two skills with same trigger but different priorities do NOT warn."""
    skills = [
        {"name": "skill_a", "trigger": "search", "priority": 5},
        {"name": "skill_b", "trigger": "search", "priority": 10},
    ]
    results = verify_skill_trigger_overlap(skills)
    assert _has_pass(results)


def test_skill_trigger_overlap_disabled_skipped():
    """Disabled skills are not included in overlap check."""
    skills = [
        {"name": "skill_a", "trigger": "search", "priority": 5},
        {"name": "skill_b", "trigger": "search", "priority": 5, "enabled": False},
    ]
    results = verify_skill_trigger_overlap(skills)
    # Only one active skill — no overlap
    assert _has_pass(results)


def test_skill_trigger_overlap_empty():
    """Empty skills list produces pass result (no overlaps)."""
    results = verify_skill_trigger_overlap([])
    assert _has_pass(results)


# ---------------------------------------------------------------------------
# Check 6: Agent Completeness
# ---------------------------------------------------------------------------

def test_agent_completeness_pass():
    """Agent with resolved model_ref and backend_ref passes."""
    agents = {
        "my_agent": {"model_ref": "my_model", "backend_ref": "my_backend"}
    }
    model_configs = {"my_model": {}}
    execution_backends = {"my_backend": {}}
    results = verify_agent_completeness(agents, model_configs, execution_backends)
    assert _has_pass(results)
    assert not _has_fail(results)


def test_agent_completeness_fail_unknown_model():
    """Agent referencing unknown model fails."""
    agents = {"my_agent": {"model_ref": "ghost_model"}}
    model_configs = {}
    execution_backends = {}
    results = verify_agent_completeness(agents, model_configs, execution_backends)
    assert _has_fail(results)


def test_agent_completeness_fail_unknown_backend():
    """Agent referencing unknown backend fails."""
    agents = {"my_agent": {"model_ref": "my_model", "backend_ref": "ghost_backend"}}
    model_configs = {"my_model": {}}
    execution_backends = {}
    results = verify_agent_completeness(agents, model_configs, execution_backends)
    assert _has_fail(results)


def test_agent_completeness_warn_no_model_ref():
    """Agent with no model_ref produces a warning."""
    agents = {"my_agent": {}}
    results = verify_agent_completeness(agents, {}, {})
    assert any(r["status"] == "warn" for r in results)


def test_agent_completeness_empty():
    """Empty agents dict produces no results."""
    results = verify_agent_completeness({}, {}, {})
    assert results == []


# ---------------------------------------------------------------------------
# verify_agent — main entry point
# ---------------------------------------------------------------------------

def test_verify_agent_full_pass():
    """verify_agent() runs all 6 checks on a well-formed ark_file dict."""
    ark_file = {
        "agents": {"my_agent": {"model_ref": "my_model"}},
        "model_configs": {"my_model": {}},
        "execution_backends": {"my_backend": {"cpu_cores": 2, "memory_mb": 1024, "timeout_seconds": 60}},
        "platforms": {"terminal": {}},
        "gateways": [{"name": "gw", "agent_ref": "my_agent", "platforms": ["terminal"]}],
        "cron_tasks": [],
        "agent_skills": [],
    }
    results = verify_agent(ark_file)
    assert isinstance(results, list)
    assert len(results) > 0


def test_verify_agent_detects_failures():
    """verify_agent() detects and returns fail results for broken references."""
    ark_file = {
        "agents": {"my_agent": {"model_ref": "ghost_model"}},
        "model_configs": {},
        "execution_backends": {},
        "platforms": {},
        "gateways": [],
        "cron_tasks": [],
        "agent_skills": [],
    }
    results = verify_agent(ark_file)
    assert _has_fail(results)


def test_verify_agent_returns_flat_list():
    """verify_agent() returns a flat list of dicts with check/status/message keys."""
    ark_file = {"items": []}
    results = verify_agent(ark_file)
    for r in results:
        assert "check" in r
        assert "status" in r
        assert "message" in r
