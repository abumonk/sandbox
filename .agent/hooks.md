---
version: "1.0"
hooks:
  default:
    - id: enforce-working-folders
      event: PreToolUse
      matcher:
        tools: [Write, Edit, Read, Glob, Grep]
      action: block
      mode: enforce
      description: "Block file operations outside declared working folders"
      enabled: true
    - id: log-bash-usage
      event: PreToolUse
      matcher:
        tools: [Bash]
      action: log
      mode: advisory
      description: "Log Bash usage for post-hoc review"
      enabled: true
    - id: record-agent-completion
      event: SubagentStop
      matcher:
        roles: ["*"]
      action: log
      mode: always
      description: "Record agent completion metrics"
      enabled: true
    - id: adventure-completion-check
      event: TaskCompleted
      matcher:
        tags: [adventure]
      action: notify
      mode: advisory
      description: "Check if adventure is complete when an adventure task finishes"
      enabled: true
    - id: adventure-review-trigger
      event: TaskCompleted
      matcher:
        tags: [adventure]
      action: notify
      mode: advisory
      description: "When all adventure tasks are completed, suggest running /adventure-review {ADV-ID}"
      enabled: true
    - id: roadmap-task-completed
      event: TaskCompleted
      matcher:
        roles: ["*"]
      action: log
      mode: always
      description: "Update roadmap on task completion"
      enabled: true
    - id: roadmap-session-update
      event: SubagentStop
      matcher:
        roles: ["lead"]
      action: log
      mode: advisory
      description: "Remind lead to update roadmap session notes on significant events"
      enabled: true
---

# Hook Configuration

This file defines lifecycle hooks for the pipeline. The lead agent evaluates
these rules during orchestration events.

## How Hooks Work

1. An event occurs (agent completes, stage transition proposed, tool use detected)
2. The lead agent reads this file and finds matching hooks
3. For each matching hook, the lead applies the specified action

## Modes

- **enforce**: Violations block the action.
- **advisory**: Generates a recommendation.
- **always**: Always fires (logging, metrics).

## Events

| Event | When | Evaluation |
|-------|------|------------|
| PreToolUse | Before tool use | Injected as agent instructions |
| PostToolUse | After tool use | Injected as agent instructions |
| SubagentStop | Agent completes | Real-time by lead |
| StageTransition | Stage advancement | Real-time by lead |
| TaskCompleted | Task finalized | Real-time by lead |
| InstructionsLoaded | Agent prompt assembly | Real-time by lead |
