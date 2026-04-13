# Stdlib Schema for Studio Types — Design

## Overview
Create `dsl/stdlib/studio.ark` defining struct and enum types for roles, studios, commands, hooks, rules, and templates. These are the data-model types that .ark specs reference when declaring studio hierarchies.

## Target Files
- `dsl/stdlib/studio.ark` — New stdlib file with all studio-related struct/enum definitions

## Approach

### Type Definitions

```ark
import stdlib.types

// Tier levels for role hierarchy
enum Tier {
    Director,      // Tier 1 — vision, cross-domain coordination
    Lead,          // Tier 2 — domain leads
    Specialist     // Tier 3 — domain specialists
}

// Tool permissions
enum AgentTool {
    Read, Write, Edit, Glob, Grep, Bash,
    WebSearch, WebFetch, MCP
}

// Hook event types
enum HookEvent {
    pre_commit, post_commit,
    pre_push, post_push,
    session_start, session_end,
    file_change, task_complete,
    build_start, build_end,
    test_start, test_end
}

// Rule severity levels
enum Severity {
    error,
    warning,
    info
}

// Workflow phases
enum WorkflowPhase {
    concept, design, planning,
    implementation, review,
    testing, release, maintenance
}

// Escalation path entry
struct EscalationPath {
    from_role: String,
    to_role: String,
    condition: String
}

// Skill definition
struct Skill {
    name: String,
    category: String
}

// Command output schema
struct CommandOutput {
    format: String,
    sections: [String]
}
```

### Design Decisions
- Use enums for closed sets (Tier, HookEvent, Severity, WorkflowPhase)
- Use structs for open data (EscalationPath, Skill, CommandOutput)
- AgentTool enum covers the Claude Code tool surface
- Keep it flat — these types are referenced by the grammar-level items (role, studio, etc.)

## Dependencies
- None (stdlib is standalone)

## Target Conditions
- TC-008: stdlib/studio.ark parses without errors via `python ark.py parse`
- TC-009: All enum and struct definitions are well-formed and referenceable
