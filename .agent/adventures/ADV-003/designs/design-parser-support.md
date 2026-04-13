# Parser Support for Studio Items — Design

## Overview
Extend the Python parser (Lark transformer + AST dataclasses) to handle the 6 new studio item kinds: role, studio, command, hook, rule, template. Add new AST dataclasses and transformer methods so `ark.py parse` produces correct JSON AST for studio .ark files.

## Target Files
- `tools/parser/ark_parser.py` — New dataclasses (RoleDef, StudioDef, CommandDef, HookDef, RuleDef, TemplateDef) + transformer methods + ArkFile index updates

## Approach

### New AST Dataclasses

```python
@dataclass
class RoleDef:
    kind: str = "role"
    name: str = ""
    inherits: list = field(default_factory=list)
    tier: Optional[int] = None
    responsibilities: list = field(default_factory=list)
    escalates_to: Optional[str] = None
    skills: list = field(default_factory=list)
    tools: list = field(default_factory=list)
    data_fields: list = field(default_factory=list)
    in_ports: list = field(default_factory=list)
    out_ports: list = field(default_factory=list)
    processes: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class TierGroup:
    level: int = 0
    members: list = field(default_factory=list)

@dataclass
class StudioDef:
    kind: str = "studio"
    name: str = ""
    tiers: list = field(default_factory=list)      # list of TierGroup
    contains: list = field(default_factory=list)
    data_fields: list = field(default_factory=list)
    invariants: list = field(default_factory=list)
    processes: list = field(default_factory=list)
    bridges: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class CommandDef:
    kind: str = "command"
    name: str = ""
    phase: Optional[str] = None
    prompt: Optional[str] = None
    role: Optional[str] = None
    output: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class HookDef:
    kind: str = "hook"
    name: str = ""
    event: Optional[str] = None
    pattern: Optional[str] = None
    action: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class RuleDef:
    kind: str = "rule"
    name: str = ""
    path: Optional[str] = None
    constraint: Optional[str] = None
    severity: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class TemplateDef:
    kind: str = "template"
    name: str = ""
    sections: list = field(default_factory=list)
    bound_to: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None
```

### Transformer Methods

Add transformer methods for each grammar rule (e.g., `role_def`, `tier_stmt`, etc.). Follow existing patterns like `abstraction_def` and `island_def`.

### ArkFile Index Updates

Add indices to ArkFile:
- `roles: dict` — name -> RoleDef
- `studios: dict` — name -> StudioDef
- `commands: dict` — name -> CommandDef

Update `_build_indices()` to populate these.

## Dependencies
- design-grammar-extensions (grammar rules must exist first)

## Target Conditions
- TC-004: Parser produces correct JSON AST for role_def items
- TC-005: Parser produces correct JSON AST for studio_def items
- TC-006: Parser produces correct JSON AST for command, hook, rule, template items
- TC-007: ArkFile indices include roles, studios, commands dicts
