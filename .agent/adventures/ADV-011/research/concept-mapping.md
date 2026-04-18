# Concept Mapping — ADV-011 Classification Pass

**Purpose.** Classify every concept from `research/concept-inventory.md` into exactly one of four buckets: `descriptor`, `builder`, `controller`, or `out-of-scope`. This file is the structural input for ADV011-T004 (deduplication), ADV011-T005 (pruning), and the three unified-design deltas (T006/T007/T008).

**Schema reference.** Columns follow `schemas/entities.md#ConceptMappingRow`: `concept`, `source_adventure`, `bucket`, `canonical_name`, `notes`.

**Bucket allowlist.** Exactly four values are permitted in the `bucket` column: `descriptor`, `builder`, `controller`, `out-of-scope`.

**Rationale.** See `## Per-Bucket Rationale` below for the classification boundary reasoning per bucket.

| concept | source_adventure | bucket | canonical_name | notes |
|---------|------------------|--------|----------------|-------|
| Item::Expression | ADV-001 | descriptor | Item::Expression | DSL top-level item kind; user-authored schema |
| Item::Predicate | ADV-001 | descriptor | Item::Predicate | DSL top-level item kind; user-authored schema |
| pipe_chain | ADV-001 | descriptor | pipe_chain | Grammar rule; part of what user writes |
| predicate_combinator | ADV-001 | descriptor | predicate_combinator | Grammar extension for logical operators; alt: builder (combinator is impl'd in codegen) |
| param_ref | ADV-001 | descriptor | param_ref | Parameter-reference sigils (@var, [prop], #idx, {nested}); pure syntax |
| Dual-grammar parity | ADV-001 | descriptor | dual_grammar_parity | Pattern maintaining Lark/Pest equivalence; variant: "Dual-grammar parity (Lark + Pest)" in ADV-001 |
| Z3 expression verifier | ADV-001 | builder | z3_expression_verifier | Z3 SMT pass over expression/predicate chains |
| PASS_OPAQUE | ADV-001 | builder | pass_opaque | Verification outcome for undecidable Z3 pipe stages; single inventory source |
| expression_codegen | ADV-001 | builder | expression_codegen | Codegen module emitting Rust fns from expression items |
| expression_primitives | ADV-001 | builder | expression_primitives | Registry table for pipe-stage primitive implementations |
| numeric expression stdlib | ADV-001 | descriptor | numeric_expression_stdlib | 11 stdlib expression decls; user-facing DSL schema |
| text expression stdlib | ADV-001 | descriptor | text_expression_stdlib | 9 stdlib expression decls; user-facing DSL schema |
| null-handling expression stdlib | ADV-001 | descriptor | null_handling_expression_stdlib | 3 stdlib expression decls; user-facing DSL schema |
| string predicate stdlib | ADV-001 | descriptor | string_predicate_stdlib | 5 stdlib predicate decls; user-facing DSL schema |
| numeric predicate stdlib | ADV-001 | descriptor | numeric_predicate_stdlib | 4 stdlib predicate decls; user-facing DSL schema |
| is-null predicate | ADV-001 | descriptor | is_null_predicate | Single predicate stdlib decl; user-facing DSL schema |
| expression_smt | ADV-001 | builder | expression_smt | Module with PRIMITIVE_Z3 dispatch table; implements Z3 verification |
| opaque-usage tracking | ADV-001 | builder | opaque_usage_tracking | Module-global set accumulating opaque primitive IDs during verify run; alt: controller |
| GraphStore | ADV-002 | builder | GraphStore | Storage backend wrapper; transforms/indexes graph data from descriptors |
| CodeIndexer | ADV-002 | builder | CodeIndexer | Ingestion pipeline producing conformant CodeGraph; static-analysis tool |
| QueryEngine | ADV-002 | builder | QueryEngine | Query component over stored CodeGraph; analysis tool operating on descriptors |
| Watcher | ADV-002 | builder | Watcher | Monitors source tree for changes to trigger re-indexing; alt: controller |
| AST-over-tree-sitter | ADV-002 | builder | ast_over_tree_sitter | Ingestion strategy producing language-agnostic ASTs; builder analysis step |
| struct Module | ADV-002 | descriptor | struct_Module | Stdlib struct declaring graph node fields; schema decl |
| struct Function | ADV-002 | descriptor | struct_Function | Stdlib struct declaring function node fields; schema decl |
| struct Class | ADV-002 | descriptor | struct_Class | Stdlib struct declaring class node fields; schema decl |
| struct Method | ADV-002 | descriptor | struct_Method | Stdlib struct declaring method node fields; schema decl |
| struct Parameter | ADV-002 | descriptor | struct_Parameter | Stdlib struct declaring parameter node fields; schema decl |
| struct Variable | ADV-002 | descriptor | struct_Variable | Stdlib struct declaring variable node fields; schema decl |
| enum EdgeKind | ADV-002 | descriptor | enum_EdgeKind | Stdlib enum of graph edge types; schema decl |
| struct Edge | ADV-002 | descriptor | struct_Edge | Stdlib struct for directed graph edge; schema decl |
| struct Complexity | ADV-002 | descriptor | struct_Complexity | Stdlib struct for complexity metrics; schema decl |
| struct ArkEntity | ADV-002 | descriptor | struct_ArkEntity | Stdlib struct for an Ark DSL entity node; schema decl |
| struct GraphMetadata | ADV-002 | descriptor | struct_GraphMetadata | Stdlib struct for CodeGraph metadata; schema decl |
| struct CodeGraph | ADV-002 | descriptor | struct_CodeGraph | Aggregate stdlib struct for CodeGraph instance; schema decl |
| expression callers | ADV-002 | descriptor | expression_callers | Query expression decl in stdlib; user-authored DSL item |
| expression call-chain | ADV-002 | descriptor | expression_call_chain | Query expression decl in stdlib; user-authored DSL item |
| expression dead-code | ADV-002 | descriptor | expression_dead_code | Query expression decl in stdlib; user-authored DSL item |
| expression complex-functions | ADV-002 | descriptor | expression_complex_functions | Query expression decl in stdlib; user-authored DSL item |
| expression subclasses | ADV-002 | descriptor | expression_subclasses | Query expression decl in stdlib; user-authored DSL item |
| expression importers | ADV-002 | descriptor | expression_importers | Query expression decl in stdlib; user-authored DSL item |
| expression module-deps | ADV-002 | descriptor | expression_module_deps | Query expression decl in stdlib; user-authored DSL item |
| predicate is-reachable | ADV-002 | descriptor | predicate_is_reachable | Predicate stdlib decl; user-authored DSL item |
| predicate has-cycles | ADV-002 | descriptor | predicate_has_cycles | Predicate stdlib decl; user-authored DSL item |
| predicate is-dead | ADV-002 | descriptor | predicate_is_dead | Predicate stdlib decl; user-authored DSL item |
| reflexive self-indexing | ADV-002 | controller | reflexive_dogfooding | Pattern of running CodeIndexer over own .ark specs; dogfooding at execution time; alt: descriptor |
| MCP query surface | ADV-002 | out-of-scope | mcp_query_surface | OUT-OF-SCOPE -> ADV-007 Ecosystem/MCP tier tooling; not an ark-core DSL or builder concern |
| Item::StudioJob (role) | ADV-003 | descriptor | Item_StudioJob_role | DSL item kind `role`; user-authored schema |
| Item::StudioJob (studio) | ADV-003 | descriptor | Item_StudioJob_studio | DSL item kind `studio`; user-authored schema |
| Item::WorkflowCommand | ADV-003 | descriptor | Item::WorkflowCommand | DSL item kind; user-authored schema |
| Item::Hook | ADV-003 | descriptor | Item::Hook | DSL item kind; user-authored schema |
| Item::Rule | ADV-003 | descriptor | Item::Rule | DSL item kind; user-authored schema |
| Item::Template | ADV-003 | descriptor | Item::Template | DSL item kind; user-authored schema |
| enum Tier | ADV-003 | descriptor | enum_Tier | Stdlib enum in studio.ark; schema decl |
| enum AgentTool | ADV-003 | descriptor | enum_AgentTool | Stdlib enum in studio.ark; schema decl |
| enum HookEvent | ADV-003 | descriptor | enum_HookEvent | Stdlib enum in studio.ark; schema decl |
| enum Severity | ADV-003 | descriptor | enum_Severity | Stdlib enum in studio.ark; schema decl |
| enum WorkflowPhase | ADV-003 | descriptor | enum_WorkflowPhase | Stdlib enum in studio.ark; schema decl |
| struct Skill | ADV-003 | descriptor | struct_Skill | Stdlib struct for skill definitions in studio.ark; schema decl |
| struct EscalationPath | ADV-003 | descriptor | struct_EscalationPath | Stdlib struct in studio.ark; schema decl |
| struct CommandOutput | ADV-003 | descriptor | struct_CommandOutput | Stdlib struct in studio.ark; schema decl |
| studio_verify | ADV-003 | builder | studio_verify | Verification module with Z3 ordinal acyclicity check; builder |
| Z3 ordinals for DAG acyclicity | ADV-003 | builder | z3_ordinal_pass | Z3 ordinal-based acyclicity pass; semantically equivalent to z3_ordinal_review_pass (ADV-006); alt: merge via T004 |
| studio_codegen | ADV-003 | builder | studio_codegen | Codegen module for studio items; builder |
| separate domain module pattern | ADV-003 | builder | domain_module_pattern | Architectural pattern for {domain}_verify + {domain}_codegen; builder infrastructure |
| Item::EvolutionTarget | ADV-004 | descriptor | Item::EvolutionTarget | DSL item kind; user-authored schema |
| Item::EvalDataset | ADV-004 | descriptor | Item::EvalDataset | DSL item kind; user-authored schema |
| Item::FitnessFunction | ADV-004 | descriptor | Item::FitnessFunction | DSL item kind; user-authored schema |
| Item::Optimizer | ADV-004 | descriptor | Item::Optimizer | DSL item kind; user-authored schema |
| Item::BenchmarkGate | ADV-004 | descriptor | Item::BenchmarkGate | DSL item kind; user-authored schema |
| Item::EvolutionRun | ADV-004 | descriptor | Item::EvolutionRun | DSL item kind; user-authored schema |
| Item::Constraint | ADV-004 | descriptor | Item::Constraint | DSL item kind; user-authored schema |
| enum EvolutionTier | ADV-004 | descriptor | enum_EvolutionTier | Stdlib enum in evolution.ark; schema decl |
| enum OptimizerEngine | ADV-004 | descriptor | enum_OptimizerEngine | Stdlib enum in evolution.ark; schema decl |
| enum DataSource | ADV-004 | descriptor | enum_DataSource | Stdlib enum in evolution.ark; schema decl |
| enum EnforcementLevel | ADV-004 | descriptor | enum_EnforcementLevel | Stdlib enum in evolution.ark; schema decl |
| enum RunStatus | ADV-004 | descriptor | enum_RunStatus | Stdlib enum in evolution.ark; schema decl |
| enum MutationStrategy | ADV-004 | descriptor | enum_MutationStrategy | Stdlib enum in evolution.ark; schema decl |
| enum AggregationMethod | ADV-004 | descriptor | enum_AggregationMethod | Stdlib enum in evolution.ark; schema decl |
| struct FitnessScore | ADV-004 | descriptor | struct_FitnessScore | Stdlib struct in evolution.ark; schema decl |
| struct Variant | ADV-004 | descriptor | struct_Variant | Stdlib struct in evolution.ark; schema decl |
| struct ConstraintDef | ADV-004 | descriptor | struct_ConstraintDef | Stdlib struct in evolution.ark; schema decl |
| struct BenchmarkResult | ADV-004 | descriptor | struct_BenchmarkResult | Stdlib struct in evolution.ark; schema decl |
| struct RunResult | ADV-004 | descriptor | struct_RunResult | Stdlib struct in evolution.ark; schema decl |
| struct SplitRatio | ADV-004 | descriptor | struct_SplitRatio | Stdlib struct in evolution.ark; schema decl |
| struct RubricDimension | ADV-004 | descriptor | struct_RubricDimension | Stdlib struct in evolution.ark; schema decl |
| evolution_verify | ADV-004 | builder | evolution_verify | Z3-based numeric interval verification module; builder |
| numeric_interval Z3 pass | ADV-004 | builder | numeric_interval_z3_pass | Z3 pass for split ratios / fitness weights / tolerances |
| evolution_codegen | ADV-004 | builder | evolution_codegen | Codegen module generating JSONL / Python / JSON from evolution items |
| evolution_skills.ark | ADV-004 | controller | evolution_skills_ark | Reflexive spec consumed at runtime by evolution subsystem; dogfooding at execution time; alt: descriptor |
| dataset_builder | ADV-004 | builder | dataset_builder | Python module generating eval datasets; analysis/build tool |
| fitness scorer | ADV-004 | builder | fitness_scorer | LLM-as-judge scoring module; transforms descriptors into scored artefacts |
| optimizer engine | ADV-004 | builder | optimizer_engine | GEPA-inspired mutation module; transforms/verifies evolved variants |
| constraint_checker | ADV-004 | builder | constraint_checker | Validates evolved variants against constraints; builder verification step |
| evolution_runner | ADV-004 | controller | evolution_runner | Orchestrates full evolution loop; runtime orchestration |
| Item::Agent | ADV-005 | descriptor | Item::Agent | DSL item kind; user-authored schema |
| Item::Platform | ADV-005 | descriptor | Item::Platform | DSL item kind; user-authored schema |
| Item::Gateway | ADV-005 | descriptor | Item::Gateway | DSL item kind; user-authored schema |
| Item::ExecutionBackend | ADV-005 | descriptor | Item::ExecutionBackend | DSL item kind; user-authored schema |
| Item::Skill | ADV-005 | descriptor | Item_Skill | DSL item kind for procedural knowledge unit with trigger/steps; distinct from struct Skill (schema decl) |
| Item::LearningConfig | ADV-005 | descriptor | Item::LearningConfig | DSL item kind; user-authored schema |
| Item::CronTask | ADV-005 | descriptor | Item::CronTask | DSL item kind; user-authored schema |
| Item::ModelConfig | ADV-005 | descriptor | Item::ModelConfig | DSL item kind; user-authored schema |
| enum Platform | ADV-005 | descriptor | enum_Platform | Stdlib enum in agent.ark; schema decl |
| enum BackendType | ADV-005 | descriptor | enum_BackendType | Stdlib enum in agent.ark; schema decl |
| enum ModelProvider | ADV-005 | descriptor | enum_ModelProvider | Stdlib enum in agent.ark; schema decl |
| enum SkillStatus | ADV-005 | descriptor | enum_SkillStatus | Stdlib enum in agent.ark; schema decl |
| enum MessageFormat | ADV-005 | descriptor | enum_MessageFormat | Stdlib enum in agent.ark; schema decl |
| enum LearningMode | ADV-005 | descriptor | enum_LearningMode | Stdlib enum in agent.ark; schema decl |
| struct GatewayRoute | ADV-005 | descriptor | struct_GatewayRoute | Stdlib struct in agent.ark; schema decl |
| struct ModelParams | ADV-005 | descriptor | struct_ModelParams | Stdlib struct in agent.ark; schema decl |
| struct ResourceLimits | ADV-005 | descriptor | struct_ResourceLimits | Stdlib struct in agent.ark; schema decl |
| struct SkillTrigger | ADV-005 | descriptor | struct_SkillTrigger | Stdlib struct in agent.ark; schema decl |
| struct ImprovementEntry | ADV-005 | descriptor | struct_ImprovementEntry | Stdlib struct in agent.ark; schema decl |
| struct CronSchedule | ADV-005 | descriptor | struct_CronSchedule | Stdlib struct in agent.ark; schema decl |
| AgentRunner | ADV-005 | controller | AgentRunner | Runtime orchestrator for agent lifecycle; controller |
| gateway module | ADV-005 | controller | gateway_module | Multi-platform message routing runtime; controller |
| skill_manager | ADV-005 | controller | skill_manager | Skill CRUD + trigger matching at runtime; controller |
| learning engine | ADV-005 | controller | learning_engine | Session memory and self-improvement runtime loop; controller |
| execution backend | ADV-005 | controller | execution_backend | Execution environment abstraction (Local/Docker); controller |
| scheduler | ADV-005 | controller | scheduler | Cron-based task scheduling runtime; controller |
| agent_verify | ADV-005 | builder | agent_verify | Z3-based reference-exists verification module; builder |
| reference_exists Z3 pass | ADV-005 | builder | reference_exists_z3_pass | Z3 pass checking cross-references resolve to declared items |
| _get dual-input AST helper | ADV-005 | builder | get_dual_input_ast_helper | Utility bridging dataclass/dict AST forms during verification; builder |
| agent_codegen | ADV-005 | builder | agent_codegen | Codegen module for agent items; builder |
| Item::Diagram | ADV-006 | descriptor | Item::Diagram | DSL item kind; user-authored schema |
| Item::Preview | ADV-006 | descriptor | Item::Preview | DSL item kind; user-authored schema |
| Item::Annotation | ADV-006 | descriptor | Item::Annotation | DSL item kind; user-authored schema |
| Item::VisualReview | ADV-006 | descriptor | Item::VisualReview | DSL item kind; user-authored schema |
| Item::Screenshot | ADV-006 | descriptor | Item::Screenshot | DSL item kind; user-authored schema |
| Item::VisualSearch | ADV-006 | descriptor | Item::VisualSearch | DSL item kind; user-authored schema |
| Item::RenderConfig | ADV-006 | descriptor | Item::RenderConfig | DSL item kind; user-authored schema |
| enum DiagramType | ADV-006 | descriptor | enum_DiagramType | Stdlib enum in visual.ark; schema decl |
| enum PreviewMode | ADV-006 | descriptor | enum_PreviewMode | Stdlib enum in visual.ark; schema decl |
| enum AnnotationType | ADV-006 | descriptor | enum_AnnotationType | Stdlib enum in visual.ark; schema decl |
| enum FeedbackStatus | ADV-006 | descriptor | enum_FeedbackStatus | Stdlib enum in visual.ark; schema decl |
| enum RenderFormat | ADV-006 | descriptor | enum_RenderFormat | Stdlib enum in visual.ark; schema decl |
| enum ViewportSize | ADV-006 | descriptor | enum_ViewportSize | Stdlib enum in visual.ark; schema decl |
| enum SearchMode | ADV-006 | descriptor | enum_SearchMode | Stdlib enum in visual.ark; schema decl |
| enum VisualTag | ADV-006 | descriptor | enum_VisualTag | Stdlib enum in visual.ark; schema decl |
| struct RenderConfig | ADV-006 | descriptor | struct_RenderConfig | Stdlib struct in visual.ark; schema decl |
| struct Position | ADV-006 | descriptor | struct_Position | Stdlib struct in visual.ark; schema decl |
| struct ArrowEndpoints | ADV-006 | descriptor | struct_ArrowEndpoints | Stdlib struct in visual.ark; schema decl |
| struct AnnotationElement | ADV-006 | descriptor | struct_AnnotationElement | Stdlib struct in visual.ark; schema decl |
| struct ReviewFeedback | ADV-006 | descriptor | struct_ReviewFeedback | Stdlib struct in visual.ark; schema decl |
| struct ScreenshotMeta | ADV-006 | descriptor | struct_ScreenshotMeta | Stdlib struct in visual.ark; schema decl |
| struct SearchQuery | ADV-006 | descriptor | struct_SearchQuery | Stdlib struct in visual.ark; schema decl |
| struct SearchResult | ADV-006 | descriptor | struct_SearchResult | Stdlib struct in visual.ark; schema decl |
| visual_verify | ADV-006 | builder | visual_verify | Verification module with 5 Z3 check functions; builder |
| Z3 ordinals for review acyclicity | ADV-006 | builder | z3_ordinal_review_pass | Ordinal acyclicity pass for visual review cycles; semantically equivalent to ADV-003 pattern; alt: merge into z3_ordinal_pass via T004 |
| visual_codegen | ADV-006 | builder | visual_codegen | Codegen module generating .mmd, HTML, annotation JSON; builder |
| mermaid_renderer | ADV-006 | builder | mermaid_renderer | Renders Mermaid specs to SVG/PNG; renders built artefacts (not live UI) |
| html_previewer | ADV-006 | builder | html_previewer | Renders HTML previews to self-contained files; renders built artefacts |
| annotator | ADV-006 | builder | annotator | Applies Pillow annotation layers; transforms images using built descriptors |
| review_loop | ADV-006 | controller | review_loop | Orchestrates visual review cycle at runtime; controller |
| mermaid/Pillow optional-deps pattern | ADV-006 | builder | optional_deps_pattern | Pattern of optional deps with graceful fallback; builder infrastructure |
| visual screenshot surfaces | ADV-006 | out-of-scope | visual_screenshot_surfaces | OUT-OF-SCOPE -> ADV-007 Interactive UI screenshot catalog; not codegen output |
| MCP tier catalogue | ADV-007 | out-of-scope | mcp_tier_catalogue | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| synthesis matrix | ADV-007 | out-of-scope | synthesis_matrix | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| interaction matrix | ADV-007 | out-of-scope | interaction_matrix | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| phase1-cross-project-issues | ADV-007 | out-of-scope | phase1_cross_project_issues | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| phase2-concept-catalog | ADV-007 | out-of-scope | phase2_concept_catalog | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| phase2-knowledge-architecture | ADV-007 | out-of-scope | phase2_knowledge_architecture | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| phase2-entity-redesign | ADV-007 | out-of-scope | phase2_entity_redesign | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| phase3-1-management-failures | ADV-007 | out-of-scope | phase3_1_management_failures | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| phase3-1-profiling-skills | ADV-007 | out-of-scope | phase3_1_profiling_skills | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| phase3-1-optimization-skills | ADV-007 | out-of-scope | phase3_1_optimization_skills | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| phase3-1-self-healing-skills | ADV-007 | out-of-scope | phase3_1_self_healing_skills | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| phase3-1-role-review | ADV-007 | out-of-scope | phase3_1_role_review | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| phase3-2-integration-matrix | ADV-007 | out-of-scope | phase3_2_integration_matrix | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| phase4-ui-requirements | ADV-007 | out-of-scope | phase4_ui_requirements | OUT-OF-SCOPE -> ADV-007 UI/Electron surface; not ark-core |
| phase4-ui-architecture | ADV-007 | out-of-scope | phase4_ui_architecture | OUT-OF-SCOPE -> ADV-007 UI/Electron surface; not ark-core |
| phase4-technology-evaluation | ADV-007 | out-of-scope | phase4_technology_evaluation | OUT-OF-SCOPE -> ADV-007 Ecosystem technology evaluation |
| phase5-concept-designs | ADV-007 | out-of-scope | phase5_concept_designs | OUT-OF-SCOPE -> ADV-007 Speculative/research-only concepts |
| phase5-integration-map | ADV-007 | out-of-scope | phase5_integration_map | OUT-OF-SCOPE -> ADV-007 Speculative/research-only artefact |
| phase6-mcp-operations | ADV-007 | out-of-scope | phase6_mcp_operations | OUT-OF-SCOPE -> ADV-007 Ecosystem MCP operations |
| phase6-autotest-strategy | ADV-007 | out-of-scope | phase6_autotest_strategy | OUT-OF-SCOPE -> ADV-007 Ecosystem tooling strategy |
| phase6-automation-first | ADV-007 | out-of-scope | phase6_automation_first | OUT-OF-SCOPE -> ADV-007 Ecosystem automation principle |
| phase6-1-complexity-analysis | ADV-007 | out-of-scope | phase6_1_complexity_analysis | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| phase6-1-refactoring-strategy | ADV-007 | out-of-scope | phase6_1_refactoring_strategy | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| phase6-1-abstract-representation | ADV-007 | out-of-scope | phase6_1_abstract_representation | OUT-OF-SCOPE -> ADV-007 Ecosystem research artefact |
| phase6-2-benchmark-design | ADV-007 | out-of-scope | phase6_2_benchmark_design | OUT-OF-SCOPE -> ADV-007 Ecosystem benchmark artefact |
| phase6-2-test-profiles | ADV-007 | out-of-scope | phase6_2_test_profiles | OUT-OF-SCOPE -> ADV-007 Ecosystem test artefact |
| phase6-2-migration-strategy | ADV-007 | out-of-scope | phase6_2_migration_strategy | OUT-OF-SCOPE -> ADV-007 Ecosystem migration artefact |
| phase7-optimization-loops | ADV-007 | out-of-scope | phase7_optimization_loops | OUT-OF-SCOPE -> ADV-007 Ecosystem on-sail operations |
| phase7-self-healing | ADV-007 | out-of-scope | phase7_self_healing | OUT-OF-SCOPE -> ADV-007 Ecosystem self-healing artefact |
| phase7-human-machine | ADV-007 | out-of-scope | phase7_human_machine | OUT-OF-SCOPE -> ADV-007 Ecosystem human-machine model |
| phase7-operational-model | ADV-007 | out-of-scope | phase7_operational_model | OUT-OF-SCOPE -> ADV-007 Ecosystem operational artefact |
| master-roadmap | ADV-007 | out-of-scope | master_roadmap | OUT-OF-SCOPE -> ADV-007 Ecosystem roadmap artefact |
| adventure-dependency-graph | ADV-007 | out-of-scope | adventure_dependency_graph | OUT-OF-SCOPE -> ADV-007 Ecosystem dependency graph artefact |
| adventure-contracts | ADV-007 | out-of-scope | adventure_contracts | OUT-OF-SCOPE -> ADV-007 Ecosystem inter-adventure contract artefact |
| sibling-package DSL consumer | ADV-008 | descriptor | sibling_package_dsl_consumer | Architectural pattern of how user writes specs as sibling package consumer; alt: out-of-scope |
| host-language contract | ADV-008 | out-of-scope | host_language_contract | OUT-OF-SCOPE -> ADV-008 Host-language feasibility study; not ark-core DSL concern |
| shape grammar termination Z3 pass | ADV-008 | builder | shape_grammar_termination_z3_pass | Z3 pass proving bounded derivation depth; builder verification |
| shape grammar determinism Z3 pass | ADV-008 | builder | shape_grammar_determinism_z3_pass | Z3 pass proving order-independent rule application; builder verification |
| shape grammar scope-safety Z3 pass | ADV-008 | builder | shape_grammar_scope_safety_z3_pass | Z3 pass for attribute scope safety; builder verification |
| baseline-diff snapshot | ADV-008 | builder | baseline_diff_snapshot | Pattern capturing ark.diff to prove no unauthorized modifications; builder tooling |
| lazy-import circular-dep break | ADV-008 | out-of-scope | lazy_import_circular_dep_break | OUT-OF-SCOPE -> ADV-008 Host-language implementation detail; not ark-core |
| ShapeGrammarIR | ADV-008 | builder | ShapeGrammarIR | Intermediate representation for shape grammar; builder pipeline artefact |
| Python shape grammar evaluator | ADV-008 | builder | python_shape_grammar_evaluator | Reference evaluator for shape grammar; builder |
| Rust shape grammar skeleton | ADV-008 | builder | rust_shape_grammar_skeleton | Rust crate skeleton for shape grammar evaluator; builder |
| semantic label propagation | ADV-008 | descriptor | semantic_label_propagation | Terminal label inheritance in derivations; part of what user writes/specifies |
| semantic-rendering research | ADV-008 | out-of-scope | semantic_rendering_research | OUT-OF-SCOPE -> ADV-008 Speculative research-only artefact |
| Ark-tool adapters | ADV-008 | builder | ark_tool_adapters | Integration modules wrapping Ark visualizer/impact/diff for shape grammar items; builder |
| metrics.md row schema | ADV-010 | controller | metrics_md_row_schema | Telemetry row schema for agent run capture; controller observability |
| metrics.md frontmatter schema | ADV-010 | controller | metrics_md_frontmatter_schema | YAML frontmatter totals recomputed from telemetry rows; controller observability |
| SubagentStop hook | ADV-010 | controller | SubagentStop_hook | Hook event triggering telemetry capture on subagent completion; controller |
| SubagentEvent | ADV-010 | controller | SubagentEvent | Frozen dataclass defining wire format for subagent-completion event; controller event contract |
| SDK usage field | ADV-010 | controller | sdk_usage_field | SDK field providing raw token counts for telemetry; controller observability |
| duration_ms field | ADV-010 | controller | duration_ms_field | SDK field providing wall-clock milliseconds for agent run; controller observability |
| cost model | ADV-010 | controller | cost_model | Pure function computing USD cost from rates table; controller telemetry |
| idempotent append | ADV-010 | controller | idempotent_append | Guarantee against duplicate telemetry rows via SHA1 Run ID; controller |
| aggregator | ADV-010 | controller | aggregator | Module rewriting frontmatter totals atomically; controller observability |
| task-actuals pipeline | ADV-010 | controller | task_actuals_pipeline | Module updating task Actual columns on completion; controller |
| metrics-capture-error entry | ADV-010 | controller | metrics_capture_error_entry | Error-isolation pattern for telemetry failures; controller observability |
| backfill mechanism | ADV-010 | controller | backfill_mechanism | Tool reconstructing historical telemetry from adventure.log; controller |
| normalize_model | ADV-010 | controller | normalize_model | Function mapping model ID aliases to canonical names; controller telemetry |
| capture.py hook entrypoint | ADV-010 | controller | capture_py_hook_entrypoint | Script receiving SubagentStop payload and writing telemetry; controller |

## Per-Bucket Rationale

**Descriptor.**
The descriptor bucket answers the question: "Is this part of what a user types, or is it the schema the parser produces?" Every top-level DSL item kind — from `Item::Expression` and `Item::Predicate` in ADV-001 through `Item::Agent`, `Item::Gateway`, `Item::Diagram`, `Item::EvolutionTarget`, and all six studio item kinds — belongs here because these are the constructs a user writes when authoring a spec. All stdlib struct and enum declarations (`struct Skill`, `enum HookEvent`, `enum DiagramType`, etc.) also land in descriptor because they define the schema of user-authored `.ark` files, not transformations over those schemas. Grammar rules (`pipe_chain`, `predicate_combinator`) and parameter-reference sigils (`param_ref`) are pure syntax anchors that the parser consumes to produce AST nodes. The boundary with the builder bucket is sharp: a concept moves to builder the moment it transforms or verifies a descriptor artefact rather than declaring one.

**Builder.**
The builder bucket answers the question: "Does this transform, verify, or analyse a descriptor to produce a checked or executable artefact?" All domain verification modules (`studio_verify`, `evolution_verify`, `agent_verify`, `visual_verify`) land here because they apply Z3 passes — `z3_ordinal_pass`, `numeric_interval_z3_pass`, `reference_exists_z3_pass`, `shape_grammar_termination_z3_pass` — to prove correctness properties of user-authored specs. All domain codegen modules (`expression_codegen`, `studio_codegen`, `evolution_codegen`, `agent_codegen`, `visual_codegen`) land here because they emit target-language artefacts from descriptors. Static-analysis and indexing tools that operate over descriptor graphs (`CodeIndexer`, `QueryEngine`, `GraphStore`) are builders because they analyse rather than declare. Renderers (`mermaid_renderer`, `annotator`) are builders because they render a built artefact; they are not live UI surfaces. The `PASS_OPAQUE` outcome, `opaque_usage_tracking`, and `expression_smt` are builder concerns because they are internal to the verification pipeline, not runtime execution. The boundary with controller is equally clear: builder concepts are applied at build/verify time, not at execution time when a system is running and adapting.

**Controller.**
The controller bucket answers the question: "Does this run, observe, or adapt a built system at execution time?" The ADV-005 runtime orchestrators form the core of this bucket: `AgentRunner`, `gateway_module`, `skill_manager`, `scheduler`, `learning_engine`, and `execution_backend` all manage a live agent process rather than transforming specs. The ADV-010 telemetry subsystem — `SubagentStop_hook`, `SubagentEvent`, `aggregator`, `task_actuals_pipeline`, `metrics_capture_error_entry`, `backfill_mechanism`, and the cost model — is entirely observability infrastructure that runs alongside and after agent execution. `evolution_runner` lands here because it orchestrates the full optimization loop at runtime, even though its inputs are evolution descriptors. `reflexive_dogfooding` and `evolution_skills_ark` are controller because their primary role is consuming the DSL at runtime to self-improve the pipeline, not declaring new schema. The boundary with builder is that controller concepts operate on live execution state and running processes; builder concepts never observe runtime state.

**Out-of-scope.**
The out-of-scope bucket holds concepts that do not fit within the three core roles of the unified Ark DSL system. The dominant volume source is ADV-007, which contributed 33 rows of ecosystem research artefacts — synthesis matrices, phase-by-phase research documents, UI architecture studies, MCP server catalogues, roadmaps, and speculative operational models. All 33 ADV-007 rows are tagged `OUT-OF-SCOPE -> ADV-007` and will collapse into the pruning catalog (T005) where they can be dispositioned for a future dedicated ecosystem adventure. Beyond ADV-007, a small set of host-language sibling concerns from ADV-008 (`host_language_contract`, `lazy_import_circular_dep_break`) and one speculative research document (`semantic_rendering_research`) land here because they describe the package consumer relationship or experimental ideas that are not ark-core DSL constructs. `visual_screenshot_surfaces` and `mcp_query_surface` are excluded because they are interactive UI catalog features and external MCP tooling respectively — neither a codegen output nor a builder analysis step. Every out-of-scope row carries either an `OUT-OF-SCOPE -> ADV-NNN` pointer or `DROP` so T005 can build the pruning catalog without ambiguity.
