# Phase 5: New Concepts - Design

## Overview
Design new conceptual additions to the ecosystem: scheduling, human-as-pipeline-role, input storage, messenger agent, project/repo/knowledge separation, custom entities, and recommendations stack.

## Concepts to Design
1. **Scheduling** - Time-based task triggering, cron-like pipelines, deadline management
2. **Human-as-pipeline-role** - Humans as first-class pipeline participants with async input/approval gates
3. **Input storage** - Persistent storage for pipeline inputs, results, and intermediate artifacts
4. **Messenger agent** - Communication bridge between pipeline and external channels (Slack, Discord, email)
5. **Project/repo/knowledge separation** - Clean boundaries between project metadata, repository code, and knowledge base
6. **Custom entities** - User-defined entity types beyond the built-in set
7. **Recommendations stack** - AI-driven suggestions for next actions, improvements, and optimizations

## Approach
For each concept:
1. Define the problem it solves with concrete use cases
2. Research similar patterns in existing tools
3. Design the entity model and integration points
4. Identify dependencies on other phases
5. Estimate implementation complexity

## Target Files (output artifacts)
- `.agent/adventures/ADV-007/research/phase5-concept-designs.md` - All 7 concept designs
- `.agent/adventures/ADV-007/research/phase5-entity-models.md` - Entity model extensions
- `.agent/adventures/ADV-007/research/phase5-integration-map.md` - How concepts integrate

## Dependencies
- design-phase2-unified-knowledge-base: Entity model foundation
- design-phase4-ui-system: UI implications

## Target Conditions
- TC-016: All 7 new concepts designed with use cases and entity models
- TC-017: Integration map showing concept dependencies and interaction points
