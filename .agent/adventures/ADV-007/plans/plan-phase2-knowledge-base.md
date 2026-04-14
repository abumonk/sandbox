# Phase 2: Unified Knowledge Base Plan

## Designs Covered
- design-phase2-unified-knowledge-base: Knowledge base unification

## Tasks

### Design unified concept catalog
- **ID**: ADV007-T007
- **Description**: Create a comprehensive catalog of all concepts across the 5 Claudovka projects. Map entity types, their properties, and usage patterns. Identify overlaps and duplicates that should be unified. Research organic connections between concepts.
- **Files**:
  - `.agent/adventures/ADV-007/research/phase2-concept-catalog.md`
- **Acceptance Criteria**:
  - [ ] All concept types from all 5 projects cataloged
  - [ ] Overlap/duplicate matrix produced
  - [ ] Organic connections between concepts identified
  - [ ] Unification recommendations with rationale
- **Target Conditions**: TC-004
- **Depends On**: ADV007-T006
- **Evaluation**:
  - Access requirements: Read, Write, WebSearch
  - Skill set: domain modeling, knowledge engineering
  - Estimated duration: 25min
  - Estimated tokens: 40000

### Design parallelism-optimized entity architecture
- **ID**: ADV007-T008
- **Description**: Redesign `.agent` entities for parallelism and token economy. Analyze current entity structure, identify contention points when multiple agents access shared files, and propose a new structure that minimizes lock contention and context size per agent invocation.
- **Files**:
  - `.agent/adventures/ADV-007/research/phase2-knowledge-architecture.md`
  - `.agent/adventures/ADV-007/research/phase2-entity-redesign.md`
- **Acceptance Criteria**:
  - [ ] Current entity structure analyzed with contention points identified
  - [ ] New entity structure proposed with parallelism guarantees
  - [ ] Token economy analysis (context size reduction targets)
  - [ ] Before/after comparison with concrete examples
- **Target Conditions**: TC-005, TC-006
- **Depends On**: ADV007-T007
- **Evaluation**:
  - Access requirements: Read, Write, Glob, Grep
  - Skill set: concurrent systems, file-based architecture
  - Estimated duration: 25min
  - Estimated tokens: 40000
