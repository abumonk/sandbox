# Phase 6: Infrastructure - Design

## Overview
Design the infrastructure layer: MCP-only deploy/compile/build, autotest orientation, and automation-first principle. This phase transforms the ecosystem from manual-heavy to fully automated operation.

## Approach
1. **MCP-only operations**: Design how deploy, compile, and build operations are exposed exclusively through MCP servers rather than direct CLI
2. **Autotest orientation**: Design a testing philosophy where every feature ships with automated proof, and manual testing is the exception
3. **Automation-first principle**: Design the system so that human intervention is only needed for novel decisions, not routine operations

### Research Areas
- Current CI/CD patterns in the ecosystem
- MCP server capabilities for build/deploy operations
- Existing test coverage and gaps
- Automation opportunities in the current pipeline

## Target Files (output artifacts)
- `.agent/adventures/ADV-007/research/phase6-mcp-operations.md` - MCP-only operations design
- `.agent/adventures/ADV-007/research/phase6-autotest-strategy.md` - Autotest orientation design
- `.agent/adventures/ADV-007/research/phase6-automation-first.md` - Automation-first architecture

## Dependencies
- design-phase3-2-external-tools-research: MCP server capabilities
- design-phase5-new-concepts: Scheduling and automation concepts

## Target Conditions
- TC-018: MCP-only operations architecture designed
- TC-019: Autotest orientation strategy with coverage targets defined
- TC-020: Automation-first principle with human escalation criteria documented
