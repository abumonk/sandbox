"""
gateway.py — Multi-platform message routing and format adaptation for the agent runtime.

Architecture:
    Platform -> GatewayRouter -> normalize(msg) -> AgentDispatch -> format(response) -> Platform
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Message:
    """Unified message representation across all platforms."""
    id: str
    platform: str          # "terminal", "telegram", "webhook", etc.
    sender: str
    content: str
    timestamp: str         # ISO 8601 string
    metadata: dict = field(default_factory=dict)


@dataclass
class GatewayRoute:
    """A routing rule that matches messages by platform and content pattern."""
    platform: str          # platform this route applies to, or "*" for any
    pattern: str           # regex pattern matched against message content
    priority: int          # higher value = higher priority
    handler: Optional[str] = None  # handler name / agent key; None = default


# ---------------------------------------------------------------------------
# Platform adapters
# ---------------------------------------------------------------------------

class TerminalAdapter:
    """Adapter for stdin/stdout (terminal) interactions."""

    PLATFORM = "terminal"

    def normalize(self, raw_input: str, sender: str = "user") -> Message:
        """Convert a raw terminal string into a Message."""
        return Message(
            id=str(uuid.uuid4()),
            platform=self.PLATFORM,
            sender=sender,
            content=raw_input.strip(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={},
        )

    def format(self, response_text: str) -> str:
        """Return plain text — strip markdown markup for terminal output."""
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", response_text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"__(.+?)__", r"\1", text)
        text = re.sub(r"_(.+?)_", r"\1", text)
        return text


class WebhookAdapter:
    """Stub adapter for HTTP webhook interactions (not yet implemented)."""

    PLATFORM = "webhook"

    def normalize(self, raw_input, sender: str = "webhook") -> Message:  # noqa: ANN001
        raise NotImplementedError(
            "WebhookAdapter.normalize() is not implemented in v1. "
            "Extend this class for your webhook platform."
        )

    def format(self, response_text: str) -> str:
        raise NotImplementedError(
            "WebhookAdapter.format() is not implemented in v1. "
            "Extend this class for your webhook platform."
        )


# ---------------------------------------------------------------------------
# Platform format lookup
# ---------------------------------------------------------------------------

# Maps platform name -> response format style
_PLATFORM_FORMATS: dict[str, str] = {
    "terminal": "plain",
    "telegram": "markdown",
    "slack": "markdown",
    "discord": "markdown",
    "webhook": "json",
}

def _adapt_for_platform(response_text: str, platform: str) -> str:
    """Apply minimal format adaptation based on platform format style."""
    fmt = _PLATFORM_FORMATS.get(platform, "plain")

    if fmt == "plain":
        # Strip common markdown bold/italic markers for plain terminals
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", response_text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"__(.+?)__", r"\1", text)
        text = re.sub(r"_(.+?)_", r"\1", text)
        return text

    if fmt == "markdown":
        # Markdown platforms receive the text as-is (already markdown)
        return response_text

    if fmt == "json":
        import json
        return json.dumps({"response": response_text})

    return response_text


# ---------------------------------------------------------------------------
# Gateway
# ---------------------------------------------------------------------------

class Gateway:
    """
    Central message gateway.

    Responsibilities:
    - Normalize raw platform input into unified Message objects.
    - Route messages to the appropriate handler using priority-ordered regex rules.
    - Format agent responses back to the correct platform representation.
    - Dispatch the full normalize -> route -> format pipeline.
    """

    def __init__(
        self,
        agent_name: str,
        routes: list[GatewayRoute],
        adapters: Optional[dict[str, object]] = None,
    ) -> None:
        self.agent_name = agent_name
        # Sort routes highest-priority first; stable sort preserves insertion order for ties
        self.routes: list[GatewayRoute] = sorted(routes, key=lambda r: r.priority, reverse=True)
        self.adapters: dict[str, object] = adapters or {}

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_input, platform: str = "terminal") -> Message:  # noqa: ANN001
        """
        Convert raw input to a unified Message.

        If an adapter is registered for the platform, it delegates to the adapter's
        normalize() method. For unregistered platforms a generic Message is built
        from the string representation of raw_input.
        """
        adapter = self.adapters.get(platform)
        if adapter is not None and hasattr(adapter, "normalize"):
            if isinstance(raw_input, str):
                return adapter.normalize(raw_input)
            return adapter.normalize(raw_input)

        # Generic fallback — treat raw_input as string content
        content = raw_input if isinstance(raw_input, str) else str(raw_input)
        return Message(
            id=str(uuid.uuid4()),
            platform=platform,
            sender="unknown",
            content=content.strip(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={},
        )

    # ------------------------------------------------------------------
    # route
    # ------------------------------------------------------------------

    def route(self, message: Message) -> Optional[GatewayRoute]:
        """
        Return the highest-priority GatewayRoute that matches the message.

        Matching criteria:
        - route.platform == message.platform OR route.platform == "*"
        - re.search(route.pattern, message.content) is not None
          (empty pattern "" matches everything)

        Returns None if no route matches.
        """
        for route in self.routes:  # already sorted high -> low priority
            platform_match = route.platform in (message.platform, "*")
            if not platform_match:
                continue
            try:
                pattern_match = route.pattern == "" or re.search(route.pattern, message.content)
            except re.error:
                pattern_match = False
            if pattern_match:
                return route
        return None

    # ------------------------------------------------------------------
    # format_response
    # ------------------------------------------------------------------

    def format_response(self, response_text: str, platform: str) -> str:
        """
        Adapt response_text for the target platform.

        Delegates to a registered adapter's format() method when available,
        otherwise falls back to the built-in _adapt_for_platform() helper.
        """
        adapter = self.adapters.get(platform)
        if adapter is not None and hasattr(adapter, "format"):
            return adapter.format(response_text)
        return _adapt_for_platform(response_text, platform)

    # ------------------------------------------------------------------
    # dispatch
    # ------------------------------------------------------------------

    def dispatch(self, message: Message) -> dict:
        """
        Full routing + formatting chain.

        Returns a dict with:
            route   — the matched GatewayRoute (or None)
            handler — handler name from the route (or None)
            output  — formatted response placeholder
        """
        matched_route = self.route(message)
        handler = matched_route.handler if matched_route else None

        # In v1 the dispatch result is a routing decision record.
        # Actual handler invocation is the responsibility of the caller / agent runner.
        formatted = self.format_response(
            f"[dispatched to {handler or self.agent_name}]",
            message.platform,
        )
        return {
            "route": matched_route,
            "handler": handler,
            "output": formatted,
        }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def gateway_from_spec(
    gateway_spec: dict,
    ark_file: Optional[str] = None,
) -> Gateway:
    """
    Build a Gateway from a parsed gateway spec dict.

    Expected gateway_spec shape (mirrors .ark DSL gateway block):
    {
        "name": str,                          # agent/gateway name
        "routes": [                           # list of route dicts
            {
                "platform": str,
                "pattern": str,
                "priority": int,
                "handler": str | None
            },
            ...
        ],
        "adapters": {                         # optional adapter overrides
            "terminal": <adapter instance>,
            ...
        }
    }

    ark_file is accepted for future use (e.g., resolving relative handler paths)
    but is not consumed in v1.
    """
    name: str = gateway_spec.get("name", "agent")

    raw_routes = gateway_spec.get("routes", [])
    routes: list[GatewayRoute] = []
    for r in raw_routes:
        routes.append(
            GatewayRoute(
                platform=r.get("platform", "*"),
                pattern=r.get("pattern", ""),
                priority=int(r.get("priority", 0)),
                handler=r.get("handler", None),
            )
        )

    # Adapters: caller may supply pre-built adapter instances via spec or
    # they can be registered post-construction.
    adapters: dict[str, object] = {}

    # Install TerminalAdapter by default unless overridden
    adapters["terminal"] = TerminalAdapter()

    spec_adapters = gateway_spec.get("adapters", {})
    adapters.update(spec_adapters)

    return Gateway(agent_name=name, routes=routes, adapters=adapters)
