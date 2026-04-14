## Entities

### ResearchDocument
- id: string (unique, format: "phase{N}-{slug}")
- phase: enum (1, 2, 3.1, 3.2, 4, 5, 6, 6.1, 6.2, 7)
- title: string (max 120 chars)
- status: enum (pending, in_progress, complete)
- findings: list[Finding]
- recommendations: list[Recommendation]
- Relations: belongs_to Phase, references ExternalProject|ExternalTool

### Phase
- id: string (1, 2, 3.1, 3.2, 4, 5, 6, 6.1, 6.2, 7)
- title: string
- planned_adventure_id: string (ADV-0xx format)
- depends_on: list[Phase.id]
- status: enum (research_pending, researched, adventure_created)
- Relations: contains ResearchDocument[], produces AdventureConcept

### ExternalProject
- name: string (Team Pipeline, Team MCP, Binartlab, Marketplace, Pipeline DSL)
- repo_url: string (nullable - needs discovery)
- tech_stack: list[string]
- status: enum (not_found, found, analyzed)
- issues: list[Issue]
- Relations: part_of Ecosystem

### ExternalTool
- name: string
- category: enum (qmd, cgc, claude_ecosystem, lsp, mcp_server, orchestrator)
- repo_url: string (nullable)
- integration_rating: enum (must_have, nice_to_have, reference_only)
- target_phases: list[Phase.id]
- Relations: integrates_with Phase[]

### AdventureConcept
- adventure_id: string (planned, format ADV-0xx)
- phase: Phase.id
- title: string
- scope: string (description of what the adventure implements)
- estimated_tasks: integer
- depends_on: list[AdventureConcept.adventure_id]
- Relations: implements Phase, depends_on AdventureConcept[]

### Issue
- severity: enum (critical, major, minor, info)
- category: enum (architecture, code_quality, missing_feature, bug, performance)
- description: string
- project: ExternalProject.name
- Relations: found_in ExternalProject

### Finding
- type: enum (strength, weakness, opportunity, threat)
- description: string
- evidence: string (file path, URL, or code snippet reference)
- Relations: part_of ResearchDocument

### Recommendation
- priority: enum (p0_critical, p1_high, p2_medium, p3_low)
- description: string
- target_phase: Phase.id
- Relations: part_of ResearchDocument, targets Phase
