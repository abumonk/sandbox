# Phase 2: Unified Knowledge Base Design - Design

## Overview
Design a unified knowledge base that combines concepts from all Claudovka projects, researches organic connections between them, and redesigns `.agent` entities for parallelism and token economy. This phase produces the architectural blueprint for how knowledge flows across projects.

## Approach
1. Catalog all concept types across projects (tasks, adventures, roles, skills, agents, pipelines, etc.)
2. Identify overlapping/duplicate concepts that should be unified
3. Research organic connections - where concepts naturally compose
4. Design new `.agent` entity structure optimized for:
   - Parallel agent execution (minimize contention on shared files)
   - Token economy (reduce context size per agent invocation)
   - Cross-project consistency
5. Produce a future adventure concept document

## Target Files (output artifacts)
- `.agent/adventures/ADV-007/research/phase2-concept-catalog.md` - All concepts across projects
- `.agent/adventures/ADV-007/research/phase2-knowledge-architecture.md` - Unified KB design
- `.agent/adventures/ADV-007/research/phase2-entity-redesign.md` - Parallelism/token-optimized entities

## Dependencies
- design-phase1-project-review: Needs project analysis to identify concepts

## Target Conditions
- TC-004: Concept catalog covering all 5 projects created
- TC-005: Knowledge architecture design with parallelism/token constraints documented
- TC-006: Entity redesign proposal produced with before/after comparison
