# Phase 4-5: UI System & New Concepts Plan

## Designs Covered
- design-phase4-ui-system: UI system design
- design-phase5-new-concepts: New ecosystem concepts

## Tasks

### Design UI requirements and architecture
- **ID**: ADV007-T017
- **Description**: Research UI patterns in similar tools (Linear, Notion, n8n, Langflow) and design the Claudovka UI architecture. Catalog all workflow entities needing UI, design component architecture with live updates, node/graph editor, DSL editor, and tabs/panes system. Evaluate technology options.
- **Files**:
  - `.agent/adventures/ADV-007/research/phase4-ui-requirements.md`
  - `.agent/adventures/ADV-007/research/phase4-ui-architecture.md`
  - `.agent/adventures/ADV-007/research/phase4-technology-evaluation.md`
- **Acceptance Criteria**:
  - [ ] UI requirements for all entity types cataloged
  - [ ] Component architecture with data flow designed
  - [ ] Node/graph editor approach defined
  - [ ] Technology stack evaluated with recommendation
  - [ ] Similar tools researched for patterns
- **Target Conditions**: TC-013, TC-014, TC-015
- **Depends On**: ADV007-T006, ADV007-T008
- **Evaluation**:
  - Access requirements: WebSearch, WebFetch, Read, Write
  - Skill set: UI/UX design, frontend architecture, real-time systems
  - Estimated duration: 30min
  - Estimated tokens: 50000

### Design new ecosystem concepts
- **ID**: ADV007-T018
- **Description**: Design all 7 new concepts: scheduling, human-as-pipeline-role, input storage, messenger agent, project/repo/knowledge separation, custom entities, and recommendations stack. For each, define the problem, use cases, entity model, and integration points.
- **Files**:
  - `.agent/adventures/ADV-007/research/phase5-concept-designs.md`
  - `.agent/adventures/ADV-007/research/phase5-entity-models.md`
  - `.agent/adventures/ADV-007/research/phase5-integration-map.md`
- **Acceptance Criteria**:
  - [ ] All 7 concepts designed with problem statements and use cases
  - [ ] Entity model extensions defined for each concept
  - [ ] Integration map showing all inter-concept dependencies
  - [ ] Implementation complexity estimates
- **Target Conditions**: TC-016, TC-017
- **Depends On**: ADV007-T008, ADV007-T017
- **Evaluation**:
  - Access requirements: Read, Write, WebSearch
  - Skill set: system design, entity modeling, pipeline architecture
  - Estimated duration: 30min
  - Estimated tokens: 50000
