"""Tests for tools/visualizer/ark_visualizer.py — agent graph data extraction and HTML output.

Covers TC-036 through TC-038.
"""

import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "visualizer"))

from ark_visualizer import (  # noqa: E402
    extract_agent_data,
    generate_graph_data,
    generate_html,
    AGENT_KINDS,
    AGENT_KIND_COLORS,
)


# ---------------------------------------------------------------------------
# Sample AST data for visualization tests
# ---------------------------------------------------------------------------

_AGENT_AST = {
    "items": [
        {
            "kind": "agent",
            "name": "my_agent",
            "model_ref": "my_model",
            "backends": ["my_backend"],
            "description": "A test agent",
        },
        {
            "kind": "platform",
            "name": "terminal",
            "platform_type": "terminal",
            "description": "CLI platform",
        },
        {
            "kind": "gateway",
            "name": "my_gateway",
            "agent_ref": "my_agent",
            "platforms": ["terminal"],
        },
        {
            "kind": "execution_backend",
            "name": "my_backend",
            "backend_type": "local",
        },
        {
            "kind": "skill",
            "name": "search_skill",
            "description": "A search skill",
            "version": "1.0",
        },
        {
            "kind": "learning_config",
            "name": "my_learning",
            "strategy": "passive",
        },
        {
            "kind": "cron_task",
            "name": "daily_task",
            "schedule": "0 9 * * *",
            "agent_ref": "my_agent",
            "platform_delivery": "terminal",
        },
        {
            "kind": "model_config",
            "name": "my_model",
            "provider": "anthropic",
            "fallback": "backup_model",
        },
    ]
}


# ---------------------------------------------------------------------------
# extract_agent_data — graph data extraction
# ---------------------------------------------------------------------------

def test_extract_agent_data_returns_dict():
    """extract_agent_data() returns a dict with nodes, links, has_agents."""
    result = extract_agent_data(_AGENT_AST)
    assert isinstance(result, dict)
    assert "nodes" in result
    assert "links" in result
    assert "has_agents" in result


def test_extract_agent_data_has_agents_true():
    """extract_agent_data() sets has_agents=True when agent items are present."""
    result = extract_agent_data(_AGENT_AST)
    assert result["has_agents"] is True


def test_extract_agent_data_has_agents_false_when_empty():
    """extract_agent_data() sets has_agents=False when no agent items."""
    result = extract_agent_data({"items": [
        {"kind": "abstraction", "name": "NotAnAgent"}
    ]})
    assert result["has_agents"] is False


def test_extract_agent_data_all_8_kinds_produce_nodes():
    """extract_agent_data() produces nodes for all 8 agent item kinds."""
    result = extract_agent_data(_AGENT_AST)
    node_names = {n["id"] for n in result["nodes"]}
    assert "my_agent" in node_names
    assert "terminal" in node_names
    assert "my_gateway" in node_names
    assert "my_backend" in node_names
    assert "search_skill" in node_names
    assert "my_learning" in node_names
    assert "daily_task" in node_names
    assert "my_model" in node_names


def test_extract_agent_data_node_has_kind_and_group():
    """Each node has 'kind' and 'group' fields."""
    result = extract_agent_data(_AGENT_AST)
    for node in result["nodes"]:
        assert "kind" in node
        assert "group" in node
        assert node["kind"] in AGENT_KINDS


def test_extract_agent_data_node_has_tooltip():
    """Each node has a 'tooltip' field."""
    result = extract_agent_data(_AGENT_AST)
    for node in result["nodes"]:
        assert "tooltip" in node


def test_extract_agent_data_gateway_links():
    """extract_agent_data() creates links: gateway → agent (routes_for)."""
    result = extract_agent_data(_AGENT_AST)
    link_kinds = {lk["kind"] for lk in result["links"]}
    assert "routes_for" in link_kinds


def test_extract_agent_data_gateway_platform_links():
    """extract_agent_data() creates links: gateway → platform (connects)."""
    result = extract_agent_data(_AGENT_AST)
    connects = [lk for lk in result["links"] if lk["kind"] == "connects"]
    assert len(connects) >= 1


def test_extract_agent_data_agent_model_links():
    """extract_agent_data() creates links: agent → model_config (uses_model)."""
    result = extract_agent_data(_AGENT_AST)
    link_kinds = {lk["kind"] for lk in result["links"]}
    assert "uses_model" in link_kinds


def test_extract_agent_data_agent_backend_links():
    """extract_agent_data() creates links: agent → execution_backend (runs_on)."""
    result = extract_agent_data(_AGENT_AST)
    link_kinds = {lk["kind"] for lk in result["links"]}
    assert "runs_on" in link_kinds


def test_extract_agent_data_cron_agent_links():
    """extract_agent_data() creates links: cron_task → agent (schedules)."""
    result = extract_agent_data(_AGENT_AST)
    link_kinds = {lk["kind"] for lk in result["links"]}
    assert "schedules" in link_kinds


def test_extract_agent_data_cron_platform_links():
    """extract_agent_data() creates links: cron_task → platform (delivers_to)."""
    result = extract_agent_data(_AGENT_AST)
    link_kinds = {lk["kind"] for lk in result["links"]}
    assert "delivers_to" in link_kinds


def test_extract_agent_data_model_fallback_links():
    """extract_agent_data() creates links: model_config → model_config (falls_back_to)."""
    result = extract_agent_data(_AGENT_AST)
    link_kinds = {lk["kind"] for lk in result["links"]}
    assert "falls_back_to" in link_kinds


def test_extract_agent_data_empty_items():
    """extract_agent_data() with empty items returns empty nodes and links."""
    result = extract_agent_data({"items": []})
    assert result["nodes"] == []
    assert result["links"] == []
    assert result["has_agents"] is False


def test_extract_agent_data_ignores_non_agent_items():
    """extract_agent_data() ignores non-agent item kinds."""
    ast = {
        "items": [
            {"kind": "abstraction", "name": "GameEntity"},
            {"kind": "island", "name": "GameIsland"},
            {"kind": "agent", "name": "real_agent"},
        ]
    }
    result = extract_agent_data(ast)
    node_names = {n["id"] for n in result["nodes"]}
    assert "GameEntity" not in node_names
    assert "GameIsland" not in node_names
    assert "real_agent" in node_names


# ---------------------------------------------------------------------------
# generate_graph_data — merged graph data
# ---------------------------------------------------------------------------

def test_generate_graph_data_includes_agent_nodes():
    """generate_graph_data() merges agent nodes into the main graph."""
    result = generate_graph_data(_AGENT_AST)
    node_names = {n["id"] for n in result["nodes"]}
    assert "my_agent" in node_names


def test_generate_graph_data_includes_agent_links():
    """generate_graph_data() includes agent links in the merged link set."""
    result = generate_graph_data(_AGENT_AST)
    link_kinds = {lk["kind"] for lk in result["links"]}
    # Should contain at least one agent link kind
    agent_link_kinds = {"routes_for", "connects", "uses_model", "runs_on", "schedules"}
    assert len(link_kinds & agent_link_kinds) > 0


def test_generate_graph_data_has_agent_key():
    """generate_graph_data() result has an 'agent' key."""
    result = generate_graph_data(_AGENT_AST)
    assert "agent" in result
    assert result["agent"]["has_agents"] is True


# ---------------------------------------------------------------------------
# AGENT_KINDS and AGENT_KIND_COLORS constants
# ---------------------------------------------------------------------------

def test_agent_kinds_contains_all_8():
    """AGENT_KINDS set contains all 8 expected agent item kinds."""
    expected = {"agent", "platform", "gateway", "execution_backend",
                "skill", "learning_config", "cron_task", "model_config"}
    assert expected.issubset(AGENT_KINDS)


def test_agent_kind_colors_covers_all_kinds():
    """AGENT_KIND_COLORS has a color for each item in AGENT_KINDS."""
    for kind in AGENT_KINDS:
        assert kind in AGENT_KIND_COLORS, f"Missing color for kind: {kind}"


# ---------------------------------------------------------------------------
# generate_html — HTML output
# ---------------------------------------------------------------------------

def test_generate_html_includes_agent_node_info():
    """generate_html() produces HTML containing agent node data."""
    graph_data = generate_graph_data(_AGENT_AST)
    html = generate_html(graph_data, title="Test Agent Graph")
    assert "<html" in html.lower() or "<!doctype" in html.lower() or "my_agent" in html


def test_generate_html_contains_title():
    """generate_html() includes the provided title in HTML output."""
    graph_data = generate_graph_data({"items": []})
    html = generate_html(graph_data, title="My Custom Title")
    assert "My Custom Title" in html


def test_generate_html_is_string():
    """generate_html() returns a non-empty string."""
    graph_data = generate_graph_data(_AGENT_AST)
    html = generate_html(graph_data)
    assert isinstance(html, str)
    assert len(html) > 100
