## Processes

### ProjectResearch
1. Web search for repository URL (WebSearch)
2. Fetch and analyze README, package.json, key source files (WebFetch)
3. Map project structure and dependencies
4. Identify issues (architecture, code quality, bugs)
5. Document strengths to preserve
6. Write ResearchDocument to adventure research directory
Error paths:
- Repository not found: Document as "not_found", search alternative sources
- Repository private/inaccessible: Document available public information only
- Large repo: Focus on entry points, config, and architecture files

### ExternalToolResearch
1. Web search for tool (name + category keywords)
2. Fetch documentation and README
3. Analyze architecture and capabilities
4. Assess integration potential with Claudovka ecosystem
5. Rate integration value (must_have / nice_to_have / reference_only)
6. Write ExternalTool analysis to research directory
Error paths:
- Tool deprecated or unmaintained: Note status, analyze last known version
- Tool behind paywall: Document public information, note access limitations

### PhaseDesignProduction
1. Read all ResearchDocuments for the phase
2. Read cross-project issues and dependency map
3. Synthesize findings into adventure concept
4. Define scope, estimated tasks, and dependencies
5. Write phase design document
6. Update master roadmap
Error paths:
- Insufficient research: Block and request additional research tasks
- Circular dependency detected: Escalate to user for phase reordering

### MasterRoadmapAssembly
1. Read all phase designs
2. Assign adventure IDs to each phase
3. Build dependency DAG (topological sort validation)
4. Identify parallel execution opportunities
5. Define inter-adventure data contracts
6. Write master roadmap, dependency graph, and contracts
Error paths:
- Dependency cycle: Report cycle path, suggest phase restructuring
- Scope too large for single adventure: Split phase into sub-adventures

### ResearchValidation
1. Read all ResearchDocuments
2. Cross-reference findings across documents
3. Check completeness (every entity has required fields)
4. Verify all external links are accessible
5. Produce validation report
Error paths:
- Stale links: Mark as stale, note when last verified
- Missing coverage: List uncovered areas for additional research tasks
