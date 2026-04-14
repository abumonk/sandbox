"""Tests for tools/agent/gateway.py — Message normalization, route matching, response formatting.

Covers TC-008 through TC-010 (gateway checks).
"""

import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "agent"))

from gateway import (  # noqa: E402
    Message,
    GatewayRoute,
    Gateway,
    TerminalAdapter,
    WebhookAdapter,
    gateway_from_spec,
    _adapt_for_platform,
)


# ---------------------------------------------------------------------------
# Message normalization
# ---------------------------------------------------------------------------

def test_terminal_adapter_normalize_produces_message():
    """TerminalAdapter.normalize() returns a valid Message."""
    adapter = TerminalAdapter()
    msg = adapter.normalize("hello world")
    assert isinstance(msg, Message)
    assert msg.platform == "terminal"
    assert msg.content == "hello world"
    assert msg.id  # non-empty UUID
    assert msg.timestamp


def test_terminal_adapter_normalize_strips_whitespace():
    """TerminalAdapter.normalize() strips leading/trailing whitespace."""
    adapter = TerminalAdapter()
    msg = adapter.normalize("  trimmed  ")
    assert msg.content == "trimmed"


def test_terminal_adapter_format_strips_markdown():
    """TerminalAdapter.format() strips **bold**, *italic*, __underline__ markup."""
    adapter = TerminalAdapter()
    result = adapter.format("**bold** and *italic* text")
    assert "**" not in result
    assert "*" not in result
    assert "bold" in result
    assert "italic" in result


def test_gateway_normalize_generic_fallback():
    """Gateway.normalize() uses generic fallback for unknown platforms."""
    gw = Gateway(agent_name="test_agent", routes=[])
    msg = gw.normalize("some text", platform="slack")
    assert isinstance(msg, Message)
    assert msg.platform == "slack"
    assert msg.content == "some text"


def test_gateway_normalize_uses_adapter():
    """Gateway.normalize() delegates to registered adapter."""
    adapter = TerminalAdapter()
    gw = Gateway(
        agent_name="test_agent",
        routes=[],
        adapters={"terminal": adapter},
    )
    msg = gw.normalize("test input", platform="terminal")
    assert isinstance(msg, Message)
    assert msg.platform == "terminal"


# ---------------------------------------------------------------------------
# Route matching
# ---------------------------------------------------------------------------

def test_route_matching_by_platform():
    """Gateway.route() matches a route by exact platform name."""
    route = GatewayRoute(platform="telegram", pattern="", priority=1)
    gw = Gateway(agent_name="bot", routes=[route])
    msg = Message(id="1", platform="telegram", sender="user",
                  content="hello", timestamp="2024-01-01T00:00:00Z")
    matched = gw.route(msg)
    assert matched is route


def test_route_matching_wildcard_platform():
    """Gateway.route() matches route with platform='*' on any platform."""
    route = GatewayRoute(platform="*", pattern="", priority=1)
    gw = Gateway(agent_name="bot", routes=[route])
    msg = Message(id="2", platform="discord", sender="user",
                  content="hello", timestamp="2024-01-01T00:00:00Z")
    matched = gw.route(msg)
    assert matched is route


def test_route_matching_pattern():
    """Gateway.route() matches a route whose pattern matches message content."""
    route = GatewayRoute(platform="*", pattern=r"^/start", priority=1)
    gw = Gateway(agent_name="bot", routes=[route])
    msg = Message(id="3", platform="telegram", sender="user",
                  content="/start bot", timestamp="2024-01-01T00:00:00Z")
    matched = gw.route(msg)
    assert matched is route


def test_route_no_match():
    """Gateway.route() returns None when no route matches."""
    route = GatewayRoute(platform="telegram", pattern=r"^/special", priority=1)
    gw = Gateway(agent_name="bot", routes=[route])
    msg = Message(id="4", platform="terminal", sender="user",
                  content="hello", timestamp="2024-01-01T00:00:00Z")
    matched = gw.route(msg)
    assert matched is None


def test_route_priority_ordering():
    """Gateway.route() selects the highest-priority matching route."""
    low = GatewayRoute(platform="*", pattern="", priority=1, handler="low_handler")
    high = GatewayRoute(platform="*", pattern="", priority=10, handler="high_handler")
    gw = Gateway(agent_name="bot", routes=[low, high])
    msg = Message(id="5", platform="telegram", sender="user",
                  content="hello", timestamp="2024-01-01T00:00:00Z")
    matched = gw.route(msg)
    assert matched is high


# ---------------------------------------------------------------------------
# Response formatting
# ---------------------------------------------------------------------------

def test_format_response_plain_strips_markdown():
    """format_response() for terminal platform strips markdown."""
    gw = Gateway(agent_name="bot", routes=[])
    result = gw.format_response("**bold** text", platform="terminal")
    assert "**" not in result
    assert "bold" in result


def test_format_response_markdown_passthrough():
    """format_response() for telegram preserves markdown."""
    gw = Gateway(agent_name="bot", routes=[])
    result = gw.format_response("**bold** text", platform="telegram")
    assert "**bold**" in result


def test_format_response_json_platform():
    """format_response() for webhook platform returns JSON string."""
    import json
    gw = Gateway(agent_name="bot", routes=[])
    result = gw.format_response("hello", platform="webhook")
    parsed = json.loads(result)
    assert parsed["response"] == "hello"


def test_adapt_for_platform_unknown_defaults_to_passthrough():
    """_adapt_for_platform() for unknown platform returns text unchanged."""
    result = _adapt_for_platform("some text", "unknown_platform")
    assert result == "some text"


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def test_dispatch_returns_dict_with_required_keys():
    """Gateway.dispatch() returns dict with route, handler, output."""
    route = GatewayRoute(platform="*", pattern="", priority=1, handler="main_handler")
    gw = Gateway(agent_name="bot", routes=[route])
    msg = Message(id="6", platform="terminal", sender="user",
                  content="hello", timestamp="2024-01-01T00:00:00Z")
    result = gw.dispatch(msg)
    assert "route" in result
    assert "handler" in result
    assert "output" in result
    assert result["handler"] == "main_handler"


def test_dispatch_no_route_uses_agent_name():
    """Gateway.dispatch() with no matching route uses agent_name as handler."""
    gw = Gateway(agent_name="default_agent", routes=[])
    msg = Message(id="7", platform="terminal", sender="user",
                  content="hello", timestamp="2024-01-01T00:00:00Z")
    result = gw.dispatch(msg)
    assert result["handler"] is None
    assert "default_agent" in result["output"]


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def test_gateway_from_spec_builds_gateway():
    """gateway_from_spec() constructs a Gateway from a spec dict."""
    spec = {
        "name": "test_gw",
        "routes": [
            {"platform": "terminal", "pattern": ".*", "priority": 1, "handler": "main"}
        ],
    }
    gw = gateway_from_spec(spec)
    assert isinstance(gw, Gateway)
    assert gw.agent_name == "test_gw"
    assert len(gw.routes) == 1
    assert gw.routes[0].handler == "main"


def test_gateway_from_spec_installs_terminal_adapter():
    """gateway_from_spec() installs a TerminalAdapter by default."""
    spec = {"name": "gw", "routes": []}
    gw = gateway_from_spec(spec)
    assert "terminal" in gw.adapters
    assert isinstance(gw.adapters["terminal"], TerminalAdapter)


def test_webhook_adapter_normalize_raises():
    """WebhookAdapter.normalize() raises NotImplementedError."""
    adapter = WebhookAdapter()
    try:
        adapter.normalize("data")
        assert False, "Expected NotImplementedError"
    except NotImplementedError:
        pass


def test_webhook_adapter_format_raises():
    """WebhookAdapter.format() raises NotImplementedError."""
    adapter = WebhookAdapter()
    try:
        adapter.format("text")
        assert False, "Expected NotImplementedError"
    except NotImplementedError:
        pass
