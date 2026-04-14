# Gateway and Messaging Runtime — Design

## Overview
Implement `tools/agent/gateway.py` — multi-platform message routing with format adaptation. The gateway receives messages from any platform, normalizes them, routes them to the appropriate agent, and formats responses back for each platform. For v1, supports stdin/stdout (Terminal) and webhook patterns (extensible).

## Target Files
- `ark/tools/agent/gateway.py` — Gateway runtime module
- `ark/tools/agent/__init__.py` — Package init

## Approach

### Architecture
```
Platform → GatewayRouter → normalize(msg) → AgentDispatch → format(response) → Platform
```

### Core Classes

```python
@dataclass
class Message:
    platform: str       # "terminal", "telegram", etc.
    sender: str
    content: str
    format: str         # "text", "markdown", "json"
    metadata: dict
    timestamp: float

@dataclass
class GatewayRoute:
    platform: str
    pattern: str        # regex pattern for routing
    priority: int
    format: str

class Gateway:
    def __init__(self, agent_name: str, routes: list[GatewayRoute]):
        ...
    
    def normalize(self, raw_message: dict, platform: str) -> Message:
        """Normalize platform-specific message to unified Message."""
        ...
    
    def route(self, message: Message) -> str:
        """Determine which agent/handler should process this message."""
        ...
    
    def format_response(self, response: str, platform: str) -> dict:
        """Adapt response format for the target platform."""
        ...
    
    def dispatch(self, message: Message) -> Message:
        """Full cycle: normalize -> route -> process -> format."""
        ...
```

### Platform Adapters (v1)
- `TerminalAdapter` — stdin/stdout, supports multiline input
- `WebhookAdapter` — HTTP POST receiver (abstract, for extension)

### Integration with Agent Specs
Gateway configuration is derived from parsed `gateway` items in .ark specs:
```python
def gateway_from_spec(gateway_def: dict, platforms: dict) -> Gateway:
    """Build Gateway from parsed gateway_def and platform defs."""
```

### Design Decisions
- Keep v1 simple: Terminal + webhook pattern stubs
- Message normalization is platform-specific but output is uniform
- Route matching uses priority-ordered regex patterns
- Format adaptation is a simple lookup table per platform
- No external dependencies (no telegram/discord SDK in v1)

## Dependencies
- design-dsl-surface (gateway_def must be parseable)
- design-stdlib-agent-schema (Platform, MessageFormat enums)

## Target Conditions
- TC-008: Gateway normalizes terminal input to Message dataclass
- TC-009: Gateway route matching works with priority-ordered patterns
- TC-010: Gateway formats responses per platform format spec
