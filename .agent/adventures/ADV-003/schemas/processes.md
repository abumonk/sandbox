## Processes

### StudioParsing
1. Lark grammar tokenizes .ark source containing role/studio/command/hook/rule/template items
2. ArkTransformer visits each rule and constructs AST dataclass instances
3. ArkFile._build_indices() populates roles, studios, commands dicts
4. Import resolution loads stdlib/studio.ark types
5. JSON serialization via asdict() includes all new fields
Error paths: Lark UnexpectedToken -> ArkParseError with snippet; unknown tier/event values caught at verify time, not parse time

### StudioVerification
1. Extract all role items from AST
2. Build escalation graph (adjacency list from escalates_to edges)
3. Check acyclicity: assign Z3 Int ordinals, prove escalates_to strictly increases
4. For each command: check role field references an existing role
5. For each command: check role's tools cover command requirements
6. For each hook: check event field is in allowed HookEvent set
7. For each rule: parse constraint, check Z3 satisfiability
8. For each role: check tools against permissions manifest
9. Collect results as list of VerifyResult dicts
Error paths: cycle detected -> report all roles in cycle; missing role -> report command name + expected role; unsatisfiable constraint -> report rule name + counterexample

### StudioCodegen
1. Read parsed AST with studio items
2. For each role: generate .claude/agents/{name}.md with role definition
3. For each command: generate .claude/commands/{name}.md with prompt and metadata
4. For all hooks: generate settings.json fragment
5. For each template: generate template skeleton .md with required sections
6. Write all files to --out directory
Error paths: missing role for command -> skip with warning; empty sections list -> generate stub

### OrgChartVisualization
1. Extract studio items from AST
2. Build node list: one node per role, colored by tier
3. Build edge list: escalation edges (role -> escalates_to)
4. Group nodes into tier bands (y-axis constraint in layout)
5. Render into HTML template with d3.js force-directed layout
6. Add toggle button for entity-graph vs org-chart view
Error paths: role with unknown tier -> default to Specialist color; missing escalates_to -> orphan node warning

### ReflexiveStudioAuthoring
1. Read existing .agent/roles/*.md to extract current Ark team roles
2. Map each role to a role_def item in ark_studio.ark
3. Map team pipeline stages to workflow_command items
4. Add verify block with escalation and resolution checks
5. Parse the authored file to validate
6. Register in root.ark registry
Error paths: parse failure -> fix syntax; verify failure -> fix escalation/reference errors
