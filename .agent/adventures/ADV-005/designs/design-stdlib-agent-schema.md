# Agent Stdlib Schema — Design

## Overview
Create `dsl/stdlib/agent.ark` defining struct and enum types for the autonomous agent system: Platform, BackendType, ModelProvider, SkillStatus, MessageFormat, LearningMode, CronSchedule, GatewayRoute. These are the foundational data-model types that agent .ark specs reference.

## Target Files
- `ark/dsl/stdlib/agent.ark` — New stdlib file with all agent-related struct/enum definitions

## Approach

### Type Definitions

```ark
import stdlib.types

// ============================================================
// ENUMS
// ============================================================

// Messaging platform types
enum Platform {
    Terminal,
    Telegram,
    Discord,
    Slack,
    WhatsApp,
    Signal,
    Webhook
}

// Execution backend types
enum BackendType {
    Local,
    Docker,
    SSH,
    Daytona,
    Singularity,
    Modal
}

// LLM model providers
enum ModelProvider {
    Anthropic,
    OpenAI,
    OpenRouter,
    NousPortal,
    Local
}

// Skill lifecycle status
enum SkillStatus {
    Draft,
    Active,
    Improving,
    Deprecated
}

// Message format types for gateway routing
enum MessageFormat {
    Text,
    Markdown,
    HTML,
    JSON,
    Binary
}

// Learning mode for skill generation
enum LearningMode {
    Passive,
    Active,
    Autonomous
}

// ============================================================
// STRUCTS
// ============================================================

// Cron schedule definition
struct CronSchedule {
    expression: String,
    timezone: String
}

// Gateway routing rule
struct GatewayRoute {
    platform: Platform,
    pattern: String,
    priority: Int,
    format: MessageFormat
}

// Model parameters
struct ModelParams {
    temperature: Float,
    max_tokens: Int,
    top_p: Float
}

// Resource limits for execution backends
struct ResourceLimits {
    max_memory_mb: Int,
    max_cpu_cores: Int,
    max_disk_gb: Int,
    timeout_seconds: Int
}

// Skill trigger condition
struct SkillTrigger {
    pattern: String,
    context: String,
    priority: Int
}

// Improvement history entry
struct ImprovementEntry {
    version: Int,
    timestamp: Uint64,
    score: Float,
    notes: String
}
```

### Design Decisions
- Use enums for closed sets (Platform, BackendType, ModelProvider, SkillStatus, MessageFormat, LearningMode)
- Use structs for parameterized data (CronSchedule, GatewayRoute, ModelParams, ResourceLimits, SkillTrigger, ImprovementEntry)
- Platform enum covers all Hermes-supported platforms plus generic Webhook
- BackendType mirrors the 6 Hermes execution backends
- ModelProvider covers the 4 Hermes providers plus Local for self-hosted models
- SkillStatus tracks the full lifecycle: Draft -> Active -> Improving -> Deprecated
- LearningMode distinguishes passive observation, active skill generation, and autonomous self-improvement

## Dependencies
- None (stdlib is standalone, imports only stdlib.types)

## Target Conditions
- TC-001: stdlib/agent.ark parses without errors via `python ark.py parse`
- TC-002: All enum and struct definitions are well-formed and referenceable from agent specs
