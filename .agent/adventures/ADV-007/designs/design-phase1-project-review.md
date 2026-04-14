# Phase 1: Claudovka Project Review - Design

## Overview
Deep-dive review of all five Claudovka ecosystem projects to identify problems, failures, strange architectural decisions, and improvement opportunities. This forms the foundation for all subsequent phases.

## Projects to Review
1. **Team Pipeline** (`claudovka-marketplace/team-pipeline`) - 6-stage multi-agent task processing pipeline plugin
2. **Team MCP** - MCP server providing pipeline state access
3. **Binartlab** - Agent orchestration platform (8 npm workspace packages)
4. **Marketplace** - Local plugin marketplace (`claudovka-marketplace`)
5. **Pipeline DSL** - Visual schema language for pipeline definitions

## Approach
For each project:
1. Locate the repository (GitHub search, npm registry, web research)
2. Analyze project structure, dependencies, and architecture
3. Read core source files (entry points, config, key modules)
4. Identify code smells, anti-patterns, and architectural issues
5. Document strengths to preserve during redesign
6. Map inter-project dependencies and integration points

## Target Files (output artifacts)
- `.agent/adventures/ADV-007/research/phase1-team-pipeline.md` - Team Pipeline analysis
- `.agent/adventures/ADV-007/research/phase1-team-mcp.md` - Team MCP analysis
- `.agent/adventures/ADV-007/research/phase1-binartlab.md` - Binartlab analysis
- `.agent/adventures/ADV-007/research/phase1-marketplace.md` - Marketplace analysis
- `.agent/adventures/ADV-007/research/phase1-pipeline-dsl.md` - Pipeline DSL analysis
- `.agent/adventures/ADV-007/research/phase1-cross-project-issues.md` - Cross-cutting issues

## Dependencies
None - this is the first phase.

## Target Conditions
- TC-001: All 5 Claudovka projects researched with documented findings
- TC-002: Cross-project dependency map created
- TC-003: Problem/failure catalog with severity ratings produced
