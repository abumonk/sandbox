# Concept Inventory — ADV-011 Raw Harvest

**Purpose.** Enumerate every distinct concept introduced by ADV-001..008 and ADV-010, tagged with the
source adventure and the concrete artefact it came from. This file is the raw feed for
ADV011-T003 (classification), ADV011-T004 (deduplication), and ADV011-T005 (pruning).

**Schema reference.** Columns follow `schemas/entities.md#ConceptInventoryRow`: `concept`,
`source_adventure`, `source_artefact`, `description`.

**Invariant.** Each row belongs to exactly one adventure. Cross-adventure repetitions are preserved
intentionally — deduplication is T004's responsibility, not this file's.

**Downstream dedup.** Canonical merged forms live in `research/deduplication-matrix.md` (produced by ADV011-T004).

| concept | source_adventure | source_artefact | description |
|---------|------------------|-----------------|-------------|
<!-- ADV-001 -->
| Item::Expression | ADV-001 | ADV-001/manifest.md#Concept | Top-level DSL item kind that declares a left-to-right pipe chain over a typed value, producing an AST node with `in`, `out`, and `chain` fields. |
| Item::Predicate | ADV-001 | ADV-001/manifest.md#Concept | Top-level DSL item kind that declares a boolean predicate with `in` and `check` fields for use in invariants and verify blocks. |
| pipe_chain | ADV-001 | ADV-001/manifest.md#Concept | Grammar rule for left-associative `\|>` operator sequences that thread a value through a sequence of named pipe stages. |
| predicate_combinator | ADV-001 | ADV-001/manifest.md#Concept | Grammar extension for short-circuit logical operators `\|AND`, `\|OR`, `\|XOR` and negation `!` that combine predicate expressions. |
| param_ref | ADV-001 | ADV-001/manifest.md#Concept | Grammar rule for typed parameter-reference sigils: `@var` (variable), `[prop]` (object property), `#idx` (collection index), `{nested}` (function call). |
| Dual-grammar parity | ADV-001 | ADV-001/manifest.md#Concept | Pattern of maintaining parity between Lark EBNF (Python parser) and Pest PEG (Rust parser) grammar extensions so both parsers produce equivalent JSON AST. |
| Z3 expression verifier | ADV-001 | ADV-001/manifest.md#Concept | Verification pass that translates expression pipe chains and predicate `check:` clauses into Z3 SMT constraints to prove type-safety and satisfiability. |
| PASS_OPAQUE | ADV-001 | ADV-001/manifest.md#Concept | Verification outcome for pipe stages whose semantics are undecidable by Z3 (regex, temporal, file-io); reported as structurally sound but unmodelled. |
| expression_codegen | ADV-001 | ADV-001/manifest.md#Concept | Codegen module that emits one `pub fn` per `expression` item for the Rust target, following the strategy model (tensor/code/script/verified). |
| expression_primitives | ADV-001 | ADV-001/manifest.md#Concept | Registry table mapping kebab-case pipe-stage names to target-language primitive implementations (e.g., `abs`, `ceil`, `str-lower`). |
| numeric expression stdlib | ADV-001 | ark/dsl/stdlib/expression.ark | Set of 11 `expression` declarations for numeric operations: absolute, add, subtract, multiply, divide, ceiling, floor, round, power, clamp, negate. |
| text expression stdlib | ADV-001 | ark/dsl/stdlib/expression.ark | Set of 9 `expression` declarations for string operations: lower, upper, trim, length, pad_right, pad_left, remove_chars, substring, replace. |
| null-handling expression stdlib | ADV-001 | ark/dsl/stdlib/expression.ark | Set of 3 `expression` declarations for null/missing value handling: null_to_zero, null_to_value, neutral. |
| string predicate stdlib | ADV-001 | ark/dsl/stdlib/predicate.ark | Set of 5 `predicate` declarations for string testing: is-empty, starts-with, ends-with, contains, matches-regex. |
| numeric predicate stdlib | ADV-001 | ark/dsl/stdlib/predicate.ark | Set of 4 `predicate` declarations for numeric comparison: is-within, is-equal-to, is-greater-than, is-less-than. |
| is-null predicate | ADV-001 | ark/dsl/stdlib/predicate.ark | Predicate that tests whether a Float value represents a null or missing sentinel. |
| expression_smt | ADV-001 | ADV-001/reviews/adventure-report.md | Module `expression_smt.py` containing the PRIMITIVE_Z3 dispatch table and opaque-usage tracking (reset/read cycle) for expression verification. |
| opaque-usage tracking | ADV-001 | ADV-001/reviews/adventure-report.md | Module-global set that accumulates opaque primitive identifiers during a verify run so the summary can distinguish PASS from PASS_OPAQUE per file. |
<!-- ADV-002 -->
| GraphStore | ADV-002 | ADV-002/manifest.md#Concept | Ark class that wraps a pluggable storage backend (kuzu, falkor, neo4j, in_memory) and exposes a uniform graph read/write interface. |
| CodeIndexer | ADV-002 | ADV-002/manifest.md#Concept | Ark abstraction for the ingestion pipeline that parses source repositories and produces a conformant CodeGraph, with contracts on graph well-formedness. |
| QueryEngine | ADV-002 | ADV-002/manifest.md#Concept | Ark component exposing query expressions (callers, call_chain, dead_code, complexity) over a stored CodeGraph. |
| Watcher | ADV-002 | ADV-002/manifest.md#Concept | Ark class that monitors a source tree for file changes and emits delta events to trigger incremental re-indexing. |
| AST-over-tree-sitter | ADV-002 | ADV-002/manifest.md#Concept | Ingestion strategy that uses the tree-sitter library to parse source files into language-agnostic ASTs before extracting graph nodes and edges. |
| struct Module | ADV-002 | ark/dsl/stdlib/code_graph.ark | Struct declaring graph node fields for a source file: name, path, language, line_count. |
| struct Function | ADV-002 | ark/dsl/stdlib/code_graph.ark | Struct declaring graph node fields for a function: name, module, line, end_line, params, is_async, decorators. |
| struct Class | ADV-002 | ark/dsl/stdlib/code_graph.ark | Struct declaring graph node fields for a class: name, module, line, end_line, bases. |
| struct Method | ADV-002 | ark/dsl/stdlib/code_graph.ark | Struct declaring graph node fields for a method: name, class_name, module, line, end_line, is_static, is_async. |
| struct Parameter | ADV-002 | ark/dsl/stdlib/code_graph.ark | Struct declaring graph node fields for a function/method parameter: name, type_hint, default_value, owner. |
| struct Variable | ADV-002 | ark/dsl/stdlib/code_graph.ark | Struct declaring graph node fields for a variable: name, scope, module, line. |
| enum EdgeKind | ADV-002 | ark/dsl/stdlib/code_graph.ark | Enum of edge types in the code graph: calls, imports, inherits, contains, references, ark_bridge. |
| struct Edge | ADV-002 | ark/dsl/stdlib/code_graph.ark | Struct declaring a directed edge between two graph nodes with source, target, kind, module, line. |
| struct Complexity | ADV-002 | ark/dsl/stdlib/code_graph.ark | Struct declaring complexity metrics for a function: function_name, module, cyclomatic, language. |
| struct ArkEntity | ADV-002 | ark/dsl/stdlib/code_graph.ark | Struct declaring a node that represents an Ark DSL entity in the code graph: name, kind, module, line. |
| struct GraphMetadata | ADV-002 | ark/dsl/stdlib/code_graph.ark | Struct declaring top-level metadata for a CodeGraph: indexed_at, root_path, node_count, edge_count, languages. |
| struct CodeGraph | ADV-002 | ark/dsl/stdlib/code_graph.ark | Aggregate struct that holds a CodeGraph instance keyed by its metadata. |
| expression callers | ADV-002 | ark/dsl/stdlib/code_graph_queries.ark | Query expression that returns all callers of a named function in the graph using the graph-callers primitive. |
| expression call-chain | ADV-002 | ark/dsl/stdlib/code_graph_queries.ark | Query expression that returns the transitive call chain from an entry point using graph-call-chain. |
| expression dead-code | ADV-002 | ark/dsl/stdlib/code_graph_queries.ark | Query expression that returns unreferenced functions using the graph-dead-code primitive. |
| expression complex-functions | ADV-002 | ark/dsl/stdlib/code_graph_queries.ark | Query expression that returns functions above a cyclomatic complexity threshold. |
| expression subclasses | ADV-002 | ark/dsl/stdlib/code_graph_queries.ark | Query expression that returns all subclasses of a named class using graph-subclasses. |
| expression importers | ADV-002 | ark/dsl/stdlib/code_graph_queries.ark | Query expression that returns all modules that import a given module. |
| expression module-deps | ADV-002 | ark/dsl/stdlib/code_graph_queries.ark | Query expression that returns the dependency graph of a module. |
| predicate is-reachable | ADV-002 | ark/dsl/stdlib/code_graph_queries.ark | Predicate that checks whether a target node is reachable from a source node in the graph. |
| predicate has-cycles | ADV-002 | ark/dsl/stdlib/code_graph_queries.ark | Predicate that checks whether the code graph contains inheritance cycles. |
| predicate is-dead | ADV-002 | ark/dsl/stdlib/code_graph_queries.ark | Predicate that checks whether a named function is dead code (unreferenced). |
| reflexive self-indexing | ADV-002 | ADV-002/manifest.md#Concept | Pattern of running the CodeIndexer over Ark's own `.ark` specs and `tools/` directory as the first real consumer of the code-graph island. |
| MCP query surface | ADV-002 | ADV-002/manifest.md#Concept | MCP skill that exposes Ark's code graph to Claude Code for natural-language structural queries during spec authoring. |
<!-- ADV-003 -->
| Item::StudioJob (role) | ADV-003 | ADV-003/manifest.md#Concept | DSL item kind `role` that declares a studio specialist with tier, responsibilities, escalation target, required skills, and allowed tools. |
| Item::StudioJob (studio) | ADV-003 | ADV-003/manifest.md#Concept | DSL item kind `studio` that groups roles into tiers and declares the reporting graph and cross-role contracts for a studio island. |
| Item::WorkflowCommand | ADV-003 | ADV-003/manifest.md#Concept | DSL item kind `workflow_command` that declares a named slash-command binding: phase, prompt, required role, and output schema. |
| Item::Hook | ADV-003 | ADV-003/manifest.md#Concept | DSL item kind `hook` that declares an event-driven rule binding a HookEvent to an action, formalising the informal `.agent/hooks.md`. |
| Item::Rule | ADV-003 | ADV-003/manifest.md#Concept | DSL item kind `rule` that declares a path-scoped policy: glob, constraint, and severity. |
| Item::Template | ADV-003 | ADV-003/manifest.md#Concept | DSL item kind `template` that declares a document skeleton with required sections, bound to a role. |
| enum Tier | ADV-003 | ark/dsl/stdlib/studio.ark | Enum of studio hierarchy levels: Director (Tier 1), Lead (Tier 2), Specialist (Tier 3). |
| enum AgentTool | ADV-003 | ark/dsl/stdlib/studio.ark | Enum of tool permissions available to agents: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch, MCP. |
| enum HookEvent | ADV-003 | ark/dsl/stdlib/studio.ark | Enum of event types that can trigger a hook: pre/post commit, push, session, file_change, task_complete, build, test. |
| enum Severity | ADV-003 | ark/dsl/stdlib/studio.ark | Enum of rule and hook severity levels: error, warning, info. |
| enum WorkflowPhase | ADV-003 | ark/dsl/stdlib/studio.ark | Enum of workflow phases for command scoping: concept, design, planning, implementation, review, testing, release, maintenance. |
| struct Skill | ADV-003 | ark/dsl/stdlib/studio.ark | Struct declaring a skill definition with name and category for agent capability declarations. |
| struct EscalationPath | ADV-003 | ark/dsl/stdlib/studio.ark | Struct declaring a directed escalation relationship between two roles with a triggering condition. |
| struct CommandOutput | ADV-003 | ark/dsl/stdlib/studio.ark | Struct declaring the output schema for a workflow command: format and required sections list. |
| studio_verify | ADV-003 | ADV-003/reviews/adventure-report.md | Standalone module `studio_verify.py` that implements Z3 ordinal-based acyclicity checking for escalation paths and other studio verification rules. |
| Z3 ordinals for DAG acyclicity | ADV-003 | ADV-003/reviews/adventure-report.md | Z3 verification pass that assigns integer ordinals to roles and proves no escalation cycle exists, consistent with Ark's verification-first philosophy. |
| studio_codegen | ADV-003 | ADV-003/reviews/adventure-report.md | Standalone module `studio_codegen.py` that generates Claude Code agent definitions, slash-command files, hook config fragments, and template skeletons from studio items. |
| separate domain module pattern | ADV-003 | ADV-003/reviews/adventure-report.md | Architectural pattern of creating `{domain}_verify.py` and `{domain}_codegen.py` as standalone modules rather than extending `ark_verify.py`/`ark_codegen.py` to keep core pipeline manageable. |
<!-- ADV-004 -->
| Item::EvolutionTarget | ADV-004 | ADV-004/manifest.md#Concept | DSL item kind for a named entity to optimize (skill, prompt, tool description, or code file) with tier, current version, and size/semantic constraints. |
| Item::EvalDataset | ADV-004 | ADV-004/manifest.md#Concept | DSL item kind for an evaluation dataset definition with source, split ratios, and scoring rubric. |
| Item::FitnessFunction | ADV-004 | ADV-004/manifest.md#Concept | DSL item kind for a scoring specification with rubric dimensions, weights, penalties, and aggregation method. |
| Item::Optimizer | ADV-004 | ADV-004/manifest.md#Concept | DSL item kind for optimizer configuration: engine (gepa, miprov2, darwinian), iterations, population size, and mutation strategy. |
| Item::BenchmarkGate | ADV-004 | ADV-004/manifest.md#Concept | DSL item kind for a validation gate specifying benchmark name, regression tolerance, and pass criteria. |
| Item::EvolutionRun | ADV-004 | ADV-004/manifest.md#Concept | DSL item kind that tracks an optimization run instance: target, optimizer, dataset, results, best variant, and status. |
| Item::Constraint | ADV-004 | ADV-004/manifest.md#Concept | DSL item kind for a safety constraint (test_suite, size_limit, caching_compat, semantic_preservation) with enforcement level. |
| enum EvolutionTier | ADV-004 | ark/dsl/stdlib/evolution.ark | Enum of risk-ordered optimization tiers: skill (Tier 1), tool_desc (Tier 2), system_prompt (Tier 3), code (Tier 4). |
| enum OptimizerEngine | ADV-004 | ark/dsl/stdlib/evolution.ark | Enum of available optimization engines: gepa (genetic-Pareto prompt evolution), miprov2 (Bayesian), darwinian (Git-based code evolution). |
| enum DataSource | ADV-004 | ark/dsl/stdlib/evolution.ark | Enum of evaluation dataset sources: synthetic, session_db, golden, auto_eval. |
| enum EnforcementLevel | ADV-004 | ark/dsl/stdlib/evolution.ark | Enum of constraint enforcement behaviors on violation: block (hard fail) or warn (soft, allow variant). |
| enum RunStatus | ADV-004 | ark/dsl/stdlib/evolution.ark | Enum of lifecycle statuses for an evolution run: pending, running, completed, failed. |
| enum MutationStrategy | ADV-004 | ark/dsl/stdlib/evolution.ark | Enum of mutation strategies: reflective (failure-analysis-informed GEPA), random, crossover. |
| enum AggregationMethod | ADV-004 | ark/dsl/stdlib/evolution.ark | Enum of fitness aggregation methods: weighted_sum, min (bottleneck), harmonic mean. |
| struct FitnessScore | ADV-004 | ark/dsl/stdlib/evolution.ark | Struct for composite fitness score with ordered rubric dimensions, per-dimension weights, and aggregation method. |
| struct Variant | ADV-004 | ark/dsl/stdlib/evolution.ark | Struct for a single evolved candidate with content, fitness score, generation number, and parent ID for lineage tracking. |
| struct ConstraintDef | ADV-004 | ark/dsl/stdlib/evolution.ark | Struct for a safety constraint definition with type, numeric threshold, and enforcement level. |
| struct BenchmarkResult | ADV-004 | ark/dsl/stdlib/evolution.ark | Struct for a single benchmark gate evaluation result: benchmark name, score, and pass/fail verdict. |
| struct RunResult | ADV-004 | ark/dsl/stdlib/evolution.ark | Struct for the outcome of a completed evolution run: best variant, fitness trajectory, generation count, and status. |
| struct SplitRatio | ADV-004 | ark/dsl/stdlib/evolution.ark | Struct for train/validation/test split ratios with the invariant that they sum to 1.0. |
| struct RubricDimension | ADV-004 | ark/dsl/stdlib/evolution.ark | Struct for a single LLM-as-judge rubric dimension with name, weight, and scoring criteria description. |
| evolution_verify | ADV-004 | ADV-004/reviews/adventure-report.md | Module `tools/verify/evolution_verify.py` implementing Z3-based numeric interval checks on split ratios, fitness weights, and gate tolerances. |
| numeric_interval Z3 pass | ADV-004 | ADV-004/reviews/adventure-report.md | Z3 verification pass that checks numeric values (split ratios sum to 1.0, fitness weights sum to 1.0, tolerances in bounds) using real-arithmetic constraints. |
| evolution_codegen | ADV-004 | ADV-004/reviews/adventure-report.md | Module `tools/codegen/evolution_codegen.py` that generates JSONL dataset templates, Python scoring skeletons, and JSON run-config files from evolution items. |
| evolution_skills.ark | ADV-004 | ADV-004/reviews/adventure-report.md | Reflexive spec `specs/meta/evolution_skills.ark` that uses the evolution subsystem to describe optimization of Ark's own skill files — first dogfooding of the evolution DSL. |
| dataset_builder | ADV-004 | ADV-004/manifest.md#Concept | Python module `tools/evolution/dataset_builder.py` that generates evaluation datasets from synthetic sources using LLM-as-judge pattern. |
| fitness scorer | ADV-004 | ADV-004/manifest.md#Concept | Python module `tools/evolution/fitness.py` that implements LLM-as-judge scoring with configurable rubric dimensions and aggregation. |
| optimizer engine | ADV-004 | ADV-004/manifest.md#Concept | Python module `tools/evolution/optimizer.py` implementing GEPA-inspired reflective text mutation without DSPy dependency. |
| constraint_checker | ADV-004 | ADV-004/manifest.md#Concept | Python module `tools/evolution/constraint_checker.py` that validates evolved variants against size, semantic, test-suite, and caching constraints. |
| evolution_runner | ADV-004 | ADV-004/manifest.md#Concept | Python module `tools/evolution/evolution_runner.py` that orchestrates the full evolution loop: target → dataset → optimize → evaluate → gate → output. |
<!-- ADV-005 -->
| Item::Agent | ADV-005 | ADV-005/manifest.md#Concept | DSL item kind for a named autonomous agent with persona, model config, capabilities, and learning settings. |
| Item::Platform | ADV-005 | ADV-005/manifest.md#Concept | DSL item kind for a messaging platform endpoint (terminal, telegram, discord, slack) with auth config and routing rules. |
| Item::Gateway | ADV-005 | ADV-005/manifest.md#Concept | DSL item kind for a unified messaging gateway binding an agent to multiple platforms with message routing and format adaptation. |
| Item::ExecutionBackend | ADV-005 | ADV-005/manifest.md#Concept | DSL item kind for a runtime environment (local, docker, ssh, cloud) with resource limits and connection config. |
| Item::Skill | ADV-005 | ADV-005/manifest.md#Concept | DSL item kind for a procedural knowledge unit with trigger conditions, steps, and improvement history (agentskills.io compatible). |
| Item::LearningConfig | ADV-005 | ADV-005/manifest.md#Concept | DSL item kind for settings governing skill generation, memory persistence, session search, and self-improvement loops. |
| Item::CronTask | ADV-005 | ADV-005/manifest.md#Concept | DSL item kind for scheduled automation with platform delivery target and execution context. |
| Item::ModelConfig | ADV-005 | ADV-005/manifest.md#Concept | DSL item kind for LLM provider configuration with fallback chain, parameters, and cost limits. |
| enum Platform | ADV-005 | ark/dsl/stdlib/agent.ark | Enum of supported messaging platforms: terminal, telegram, discord, slack, whatsapp, signal, webhook. |
| enum BackendType | ADV-005 | ark/dsl/stdlib/agent.ark | Enum of execution backend environments: local, docker, ssh, daytona, singularity, modal. |
| enum ModelProvider | ADV-005 | ark/dsl/stdlib/agent.ark | Enum of LLM provider integrations: nous, openrouter, openai, anthropic, local. |
| enum SkillStatus | ADV-005 | ark/dsl/stdlib/agent.ark | Enum of skill lifecycle statuses: active, deprecated, draft, archived. |
| enum MessageFormat | ADV-005 | ark/dsl/stdlib/agent.ark | Enum of message formatting modes: plain, markdown, html, json. |
| enum LearningMode | ADV-005 | ark/dsl/stdlib/agent.ark | Enum of learning data collection modes: passive, active, supervised. |
| struct GatewayRoute | ADV-005 | ark/dsl/stdlib/agent.ark | Struct for a routing rule mapping a platform to an input pattern with priority ordering. |
| struct ModelParams | ADV-005 | ark/dsl/stdlib/agent.ark | Struct for LLM sampling parameters: temperature, max_tokens, top_p. |
| struct ResourceLimits | ADV-005 | ark/dsl/stdlib/agent.ark | Struct for execution backend resource constraints: cpu_cores, memory_mb, timeout_seconds, gpu. |
| struct SkillTrigger | ADV-005 | ark/dsl/stdlib/agent.ark | Struct for a trigger rule that activates a skill based on pattern matching with priority. |
| struct ImprovementEntry | ADV-005 | ark/dsl/stdlib/agent.ark | Struct for a recorded self-improvement event with before/after scores and change summary. |
| struct CronSchedule | ADV-005 | ark/dsl/stdlib/agent.ark | Struct for a cron-style schedule with expression, timezone, and enabled flag. |
| AgentRunner | ADV-005 | ADV-005/manifest.md#Concept | Python module `tools/agent/agent_runner.py` that orchestrates agent lifecycle: init → listen → process → learn → persist. |
| gateway module | ADV-005 | ADV-005/manifest.md#Concept | Python module `tools/agent/gateway.py` implementing multi-platform message routing with normalize/route/format_response functions. |
| skill_manager | ADV-005 | ADV-005/manifest.md#Concept | Python module `tools/agent/skill_manager.py` providing skill CRUD, trigger matching with priority ordering, and JSON persistence. |
| learning engine | ADV-005 | ADV-005/manifest.md#Concept | Python module `tools/agent/learning.py` implementing session memory, skill generation from execution traces, and self-improvement scoring. |
| execution backend | ADV-005 | ADV-005/manifest.md#Concept | Python module `tools/agent/backend.py` abstracting execution environments with Local and Docker implementations for v1. |
| scheduler | ADV-005 | ADV-005/manifest.md#Concept | Python module `tools/agent/scheduler.py` implementing cron-based task scheduling with platform delivery routing. |
| agent_verify | ADV-005 | ADV-005/reviews/adventure-report.md | Module `tools/verify/agent_verify.py` implementing Z3-based reference-exists pass: validates gateway/cron references, model fallback acyclicity, resource limits, and trigger overlap. |
| reference_exists Z3 pass | ADV-005 | ADV-005/reviews/adventure-report.md | Z3 verification pass that checks all gateway, cron_task, model_config cross-references resolve to declared items (no dangling references). |
| _get dual-input AST helper | ADV-005 | ADV-005/reviews/adventure-report.md | Utility function `_get(obj, field)` that transparently handles both dataclass and dict AST representations, enabling parser-version compatibility. |
| agent_codegen | ADV-005 | ADV-005/reviews/adventure-report.md | Module `tools/codegen/agent_codegen.py` generating agent YAML configs, gateway routing tables, cron entries, skill markdown, and Docker compose fragments. |
<!-- ADV-006 -->
| Item::Diagram | ADV-006 | ADV-006/manifest.md#Concept | DSL item kind for a named visual artifact with type (mermaid, flowchart, etc.), source content, and rendering config. |
| Item::Preview | ADV-006 | ADV-006/manifest.md#Concept | DSL item kind for an HTML/component preview with source, viewport config, and interaction mode. |
| Item::Annotation | ADV-006 | ADV-006/manifest.md#Concept | DSL item kind for a markup layer on an image/screenshot with spatial elements (rect, arrow, text, blur, segment). |
| Item::VisualReview | ADV-006 | ADV-006/manifest.md#Concept | DSL item kind for a review cycle: render visual → present to user → collect feedback → return structured result. |
| Item::Screenshot | ADV-006 | ADV-006/manifest.md#Concept | DSL item kind for a captured image with metadata (timestamp, source, tags) and optional AI-generated description. |
| Item::VisualSearch | ADV-006 | ADV-006/manifest.md#Concept | DSL item kind for a semantic search query over screenshot/diagram library using keyword, tag, or embedding modes. |
| Item::RenderConfig | ADV-006 | ADV-006/manifest.md#Concept | DSL item kind for output format, resolution, theme, and layout settings for visual artifacts. |
| enum DiagramType | ADV-006 | ark/dsl/stdlib/visual.ark | Enum of supported diagram types: mermaid, flowchart, architecture, sequence, class_diagram, state, er, gantt. |
| enum PreviewMode | ADV-006 | ark/dsl/stdlib/visual.ark | Enum of preview interaction modes: static (screenshot), interactive (live HTML), responsive (viewport testing). |
| enum AnnotationType | ADV-006 | ark/dsl/stdlib/visual.ark | Enum of annotation element types: rect, arrow, text, blur, segment, highlight, circle, freehand. |
| enum FeedbackStatus | ADV-006 | ark/dsl/stdlib/visual.ark | Enum of feedback statuses from human review: pending, approved, rejected, changes_requested, annotated. |
| enum RenderFormat | ADV-006 | ark/dsl/stdlib/visual.ark | Enum of render output formats: svg, png, html, pdf. |
| enum ViewportSize | ADV-006 | ark/dsl/stdlib/visual.ark | Enum of viewport size presets: mobile (375x667), tablet, desktop (1920x1080), custom. |
| enum SearchMode | ADV-006 | ark/dsl/stdlib/visual.ark | Enum of visual search modes: keyword, tag, semantic (embedding-based, v2), combined. |
| enum VisualTag | ADV-006 | ark/dsl/stdlib/visual.ark | Enum of visual artifact tags for categorization: architecture, workflow, data_model, ui_mockup, screenshot, annotation, review, diagram. |
| struct RenderConfig | ADV-006 | ark/dsl/stdlib/visual.ark | Struct for render configuration: format, width, height, theme, background, scale. |
| struct Position | ADV-006 | ark/dsl/stdlib/visual.ark | Struct for a spatial position and bounding box for annotation elements: x, y, width, height. |
| struct ArrowEndpoints | ADV-006 | ark/dsl/stdlib/visual.ark | Struct for an arrow annotation's start and end coordinates: start_x, start_y, end_x, end_y. |
| struct AnnotationElement | ADV-006 | ark/dsl/stdlib/visual.ark | Struct for an annotation markup element with kind, position, label, color, and opacity. |
| struct ReviewFeedback | ADV-006 | ark/dsl/stdlib/visual.ark | Struct for structured human review feedback: status, comments, annotation elements, change requests, reviewer, timestamp. |
| struct ScreenshotMeta | ADV-006 | ark/dsl/stdlib/visual.ark | Struct for screenshot metadata: path, timestamp, source, tags, description, width, height. |
| struct SearchQuery | ADV-006 | ark/dsl/stdlib/visual.ark | Struct for a visual search query with mode, query string, tag filter, and result count limit. |
| struct SearchResult | ADV-006 | ark/dsl/stdlib/visual.ark | Struct for a visual search result entry with path, relevance score, tags, and description. |
| visual_verify | ADV-006 | ADV-006/reviews/adventure-report.md | Module `tools/verify/visual_verify.py` with 5 Z3 check functions: diagram type validity, review target existence, annotation bounds, render config dimensions, and review cycle acyclicity. |
| Z3 ordinals for review acyclicity | ADV-006 | ADV-006/reviews/adventure-report.md | Z3 verification pass using integer ordinals to prove visual review cycles are acyclic — same ordinal pattern as ADV-003's escalation check. |
| visual_codegen | ADV-006 | ADV-006/reviews/adventure-report.md | Module `tools/codegen/visual_codegen.py` generating `.mmd` files from diagram items, HTML from preview items, annotation JSON, and render config JSON. |
| mermaid_renderer | ADV-006 | ADV-006/manifest.md#Concept | Python module `tools/visual/mermaid_renderer.py` that renders Mermaid diagram specs to SVG/PNG using mermaid CLI or inline JS. |
| html_previewer | ADV-006 | ADV-006/manifest.md#Concept | Python module `tools/visual/html_previewer.py` that renders HTML previews to self-contained HTML files with viewport configuration. |
| annotator | ADV-006 | ADV-006/manifest.md#Concept | Python module `tools/visual/annotator.py` that applies annotation layers to images using Pillow with rect, arrow, text, blur overlays. |
| review_loop | ADV-006 | ADV-006/manifest.md#Concept | Python module `tools/visual/review_loop.py` that orchestrates visual review cycle: render → present → collect feedback → return manifest JSON. |
| mermaid/Pillow optional-deps pattern | ADV-006 | ADV-006/manifest.md#Concept | Pattern of declaring Mermaid.js and Pillow as optional dependencies with graceful fallback to JSON stub output when not installed. |
| visual screenshot surfaces | ADV-006 | ADV-006/manifest.md#Concept | Screenshot capture and catalog features (screenshot_manager.py, search.py) enabling semantic search over visual artifact library. |
<!-- ADV-007 -->
| MCP tier catalogue | ADV-007 | ADV-007/research/phase3-2-mcp-servers.md | Research artefact cataloguing 14 MCP servers analyzed for integration potential, with capability summaries and Ark fit assessments. |
| synthesis matrix | ADV-007 | ADV-007/manifest.md#Target Conditions | Research artefact (TC-004) mapping concepts across all 5 Claudovka projects to identify organic connections and design alignments. |
| interaction matrix | ADV-007 | ADV-007/manifest.md#Target Conditions | Research artefact (TC-011) scoring each external tool against each Claudovka phase using a C/R/U/D/O interaction model. |
| phase1-cross-project-issues | ADV-007 | ADV-007/research/phase1-cross-project-issues.md | Research artefact cataloguing cross-project dependency failures and design problems with severity ratings across Team Pipeline, Team MCP, Binartlab, Marketplace, Pipeline DSL. |
| phase2-concept-catalog | ADV-007 | ADV-007/research/phase2-concept-catalog.md | Research artefact enumerating all concepts from 5 Claudovka projects as the basis for unified knowledge architecture. |
| phase2-knowledge-architecture | ADV-007 | ADV-007/research/phase2-knowledge-architecture.md | Research artefact documenting knowledge architecture with parallelism and token-economy constraints for the redesigned entity system. |
| phase2-entity-redesign | ADV-007 | ADV-007/research/phase2-entity-redesign.md | Research artefact with before/after comparison of .agent entity schema redesign proposals targeting parallelism and token economy. |
| phase3-1-management-failures | ADV-007 | ADV-007/manifest.md#Target Conditions | Research artefact (TC-007) cataloguing management failures from past adventures with root-cause analysis. |
| phase3-1-profiling-skills | ADV-007 | ADV-007/research/phase3-1-profiling-skills.md | Research artefact specifying profiling skill designs for the team-pipeline self-improvement loop. |
| phase3-1-optimization-skills | ADV-007 | ADV-007/research/phase3-1-optimization-skills.md | Research artefact specifying optimization skill designs for the team-pipeline self-healing subsystem. |
| phase3-1-self-healing-skills | ADV-007 | ADV-007/research/phase3-1-self-healing-skills.md | Research artefact specifying self-healing skill designs for automated recovery from pipeline failures. |
| phase3-1-role-review | ADV-007 | ADV-007/research/phase3-1-role-review.md | Research artefact reviewing current agent role effectiveness with improvement recommendations. |
| phase3-2-integration-matrix | ADV-007 | ADV-007/research/phase3-2-integration-matrix.md | Research artefact (TC-011) producing a tool-by-phase integration potential matrix for external tools. |
| phase4-ui-requirements | ADV-007 | ADV-007/research/phase4-ui-requirements.md | Research artefact cataloguing UI requirements for all workflow entity types (tasks, adventures, roles, skills, metrics). |
| phase4-ui-architecture | ADV-007 | ADV-007/research/phase4-ui-architecture.md | Research artefact documenting UI component architecture with data-flow design for the live-updates node/graph/DSL editor. |
| phase4-technology-evaluation | ADV-007 | ADV-007/research/phase4-technology-evaluation.md | Research artefact with technology stack evaluation and recommendation for the UI system (Electron, web, TUI candidates). |
| phase5-concept-designs | ADV-007 | ADV-007/research/phase5-concept-designs.md | Research artefact designing 7 new concepts: scheduling, human-as-pipeline-role, input storage, messenger agent, project/repo/knowledge separation, custom entities, recommendations stack. |
| phase5-integration-map | ADV-007 | ADV-007/research/phase5-integration-map.md | Research artefact showing concept dependency map and interaction points for the 7 new Phase 5 concepts. |
| phase6-mcp-operations | ADV-007 | ADV-007/research/phase6-mcp-operations.md | Research artefact designing MCP-only operations architecture for deploy/compile/build without local shell access. |
| phase6-autotest-strategy | ADV-007 | ADV-007/research/phase6-autotest-strategy.md | Research artefact defining autotest orientation strategy with coverage targets for the automation-first infrastructure. |
| phase6-automation-first | ADV-007 | ADV-007/research/phase6-automation-first.md | Research artefact documenting automation-first principle with human escalation criteria and intervention thresholds. |
| phase6-1-complexity-analysis | ADV-007 | ADV-007/research/phase6-1-complexity-analysis.md | Research artefact analysing system complexity with reduction targets for the final reconstruction phase. |
| phase6-1-refactoring-strategy | ADV-007 | ADV-007/research/phase6-1-refactoring-strategy.md | Research artefact defining iterative refactoring strategy with milestone criteria for the lightweight reconstruction. |
| phase6-1-abstract-representation | ADV-007 | ADV-007/research/phase6-1-abstract-representation.md | Research artefact specifying the abstract representation layer for the unified system. |
| phase6-2-benchmark-design | ADV-007 | ADV-007/research/phase6-2-benchmark-design.md | Research artefact specifying benchmark design with baseline and target metrics for the post-final evaluation phase. |
| phase6-2-test-profiles | ADV-007 | ADV-007/research/phase6-2-test-profiles.md | Research artefact defining test and profile scenarios covering the full Claudovka stack. |
| phase6-2-migration-strategy | ADV-007 | ADV-007/research/phase6-2-migration-strategy.md | Research artefact defining migration strategy with backward compatibility plan for the post-final reconstruction. |
| phase7-optimization-loops | ADV-007 | ADV-007/research/phase7-optimization-loops.md | Research artefact designing day-to-day optimization loop with metrics and triggers for the on-sail operational model. |
| phase7-self-healing | ADV-007 | ADV-007/research/phase7-self-healing.md | Research artefact specifying self-healing architecture with error classification taxonomy for autonomous pipeline recovery. |
| phase7-human-machine | ADV-007 | ADV-007/research/phase7-human-machine.md | Research artefact defining human-machine balance model with escalation criteria for the on-sail phase. |
| phase7-operational-model | ADV-007 | ADV-007/research/phase7-operational-model.md | Research artefact designing the futuring (proactive improvement) system for the on-sail operational model. |
| master-roadmap | ADV-007 | ADV-007/research/master-roadmap.md | Research artefact mapping all 10 Claudovka phases to adventure IDs, producing the master sequencing roadmap. |
| adventure-dependency-graph | ADV-007 | ADV-007/research/adventure-dependency-graph.md | Research artefact providing adventure dependency graph with parallelism analysis across the full roadmap. |
| adventure-contracts | ADV-007 | ADV-007/research/adventure-contracts.md | Research artefact defining inter-adventure data contracts specifying what each adventure consumes and produces. |
<!-- ADV-008 -->
| sibling-package DSL consumer | ADV-008 | ADV-008/manifest.md#Concept | Architectural pattern where `shape_grammar/` is a sibling package in `R:/Sandbox/` that consumes Ark DSL as its host language with a strict one-way `shape_grammar → ark` dependency. |
| host-language contract | ADV-008 | ADV-008/manifest.md#Target Conditions | Feasibility assessment (TC-02, TC-10, TC-18) proving that Ark can serve as a host language for external packages with zero modifications to `ark/`. |
| shape grammar termination Z3 pass | ADV-008 | ADV-008/manifest.md#Target Conditions | Z3 verification pass (TC-04a, TC-04d) that proves shape grammar derivation depth is bounded, and fails on deliberate unbounded-derivation counterexample. |
| shape grammar determinism Z3 pass | ADV-008 | ADV-008/manifest.md#Target Conditions | Z3 verification pass (TC-04b) that proves shape grammar rule application is order-independent and produces deterministic output. |
| shape grammar scope-safety Z3 pass | ADV-008 | ADV-008/manifest.md#Target Conditions | Z3 verification pass (TC-04c) that checks attribute scope safety: attributes are declared before use and do not escape their scope. |
| baseline-diff snapshot | ADV-008 | ADV-008/manifest.md#Target Conditions | Pattern of capturing a `baseline-ark.diff` snapshot at adventure start and comparing against it at end (TC-10) to prove no unauthorized Ark modifications. |
| lazy-import circular-dep break | ADV-008 | ADV-008/reviews/adventure-report.md | Implementation pattern of using deferred imports inside functions to break circular module dependencies in the shape_grammar package (discovered during T12/T13 integration). |
| ShapeGrammarIR | ADV-008 | ADV-008/manifest.md#Concept | Intermediate representation extracted from shape grammar `.ark` islands by `shape_grammar/tools/ir.py` for use by verifier, evaluator, and codegen. |
| Python shape grammar evaluator | ADV-008 | ADV-008/manifest.md#Concept | Module `shape_grammar/tools/evaluator.py` implementing the reference evaluator: grammar → deterministic terminal derivation → OBJ output under fixed RNG seed. |
| Rust shape grammar skeleton | ADV-008 | ADV-008/manifest.md#Concept | Rust crate at `shape_grammar/tools/rust/` providing typed IR structs and the skeleton of a performant shape grammar evaluator (passes `cargo check`). |
| semantic label propagation | ADV-008 | ADV-008/manifest.md#Concept | Feature whereby every terminal in a shape grammar derivation inherits or overrides a semantic label (e.g., window, load-bearing) enabling material/shader/LOD selection by semantic class. |
| semantic-rendering research | ADV-008 | ADV-008/manifest.md#Concept | Research document `ADV-008/research/semantic-rendering.md` exploring 2 concrete prototype recipes for rendering driven by rule-tree meaning, not just geometry. |
| Ark-tool adapters | ADV-008 | ADV-008/manifest.md#Concept | Integration modules under `shape_grammar/tools/integrations/` that wrap Ark's visualizer, impact, and diff tools to handle shape grammar island items. |
<!-- ADV-010 -->
| metrics.md row schema | ADV-010 | ADV-010/manifest.md#Concept | 12-column pipe-table row schema for agent run telemetry: Run ID, Timestamp, Agent, Task, Model, Tokens In, Tokens Out, Duration (s), Turns, Cost (USD), Result, Confidence. |
| metrics.md frontmatter schema | ADV-010 | ADV-010/manifest.md#Concept | 6-key YAML frontmatter block in metrics.md: total_tokens_in, total_tokens_out, total_duration, total_cost, agent_runs — recomputed from rows on every write. |
| SubagentStop hook | ADV-010 | ADV-010/manifest.md#Concept | Claude Code hook event that fires on every subagent completion and serves as the primary trigger for telemetry capture, forwarding event payload to `capture.py` via stdin. |
| SubagentEvent | ADV-010 | ADV-010/designs/design-capture-contract.md | Frozen dataclass defining the wire format for a subagent-completion event: event_type, timestamp, adventure_id, agent, task, model, tokens_in, tokens_out, duration_ms, turns, result, session_id. |
| SDK usage field | ADV-010 | ADV-010/manifest.md#Concept | Claude Code SDK field `usage` containing `input_tokens` and `output_tokens` per agent completion, used as the raw token signal for telemetry rows. |
| duration_ms field | ADV-010 | ADV-010/manifest.md#Concept | SDK field providing wall-clock milliseconds for an agent run, converted to integer seconds for the metrics.md `Duration (s)` column. |
| cost model | ADV-010 | ADV-010/designs/design-cost-model.md | Pure function `cost_for(model, tokens_in, tokens_out)` in `cost_model.py` that computes USD cost from a rates table loaded from `.agent/config.md` frontmatter. |
| idempotent append | ADV-010 | ADV-010/manifest.md#Concept | Guarantee that replaying a SubagentStop event with the same Run ID does not produce a duplicate row (checked via SHA1 Run ID collision detection). |
| aggregator | ADV-010 | ADV-010/designs/design-aggregation-rules.md | Module `aggregator.py` that reads all metrics rows and rewrites frontmatter totals atomically; idempotent by design so re-running produces byte-identical output. |
| task-actuals pipeline | ADV-010 | ADV-010/designs/design-aggregation-rules.md | Module `task_actuals.py` that updates a task's Actual Duration / Actual Tokens / Actual Cost / Variance columns in the manifest `## Evaluations` table on task completion. |
| metrics-capture-error entry | ADV-010 | ADV-010/designs/design-capture-contract.md | Error-isolation pattern: capture failures write a JSON line to `capture-errors.log` with `{ts, exc, msg}` and exit 0 so pipeline execution is never blocked by telemetry failure. |
| backfill mechanism | ADV-010 | ADV-010/manifest.md#Concept | Tool `tools/backfill.py` that reconstructs historical telemetry from adventure.log entries, git log, task file logs, and existing rows, emitting best-effort rows with confidence: medium/low/estimated. |
| normalize_model | ADV-010 | ADV-010/designs/design-cost-model.md | Function that maps model ID aliases (claude-opus-4-6, claude-sonnet-*, etc.) to canonical short names (opus, sonnet, haiku) before cost lookup. |
| capture.py hook entrypoint | ADV-010 | ADV-010/designs/design-capture-contract.md | Python script `.agent/telemetry/capture.py` that receives SubagentStop payload on stdin, validates it, computes cost, appends a row to metrics.md, and recomputes frontmatter. |

## Harvest Notes

### Per-adventure row counts (approximate)

| Adventure | Rows | Primary sources |
|-----------|------|-----------------|
| ADV-001 | 18 | manifest#Concept, expression.ark, predicate.ark, adventure-report |
| ADV-002 | 26 | manifest#Concept, code_graph.ark, code_graph_queries.ark |
| ADV-003 | 19 | manifest#Concept, studio.ark, adventure-report |
| ADV-004 | 30 | manifest#Concept, evolution.ark, adventure-report |
| ADV-005 | 31 | manifest#Concept, agent.ark, adventure-report |
| ADV-006 | 33 | manifest#Concept, visual.ark, adventure-report |
| ADV-007 | 33 | manifest#Target Conditions, research/*.md listing |
| ADV-008 | 13 | manifest#Concept, manifest#Target Conditions, adventure-report |
| ADV-010 | 14 | manifest#Concept, designs/design-capture-contract, designs/design-cost-model, designs/design-aggregation-rules |

**Total rows**: ~217

### Stdlib files read

- `ark/dsl/stdlib/expression.ark` (ADV-001)
- `ark/dsl/stdlib/predicate.ark` (ADV-001)
- `ark/dsl/stdlib/code_graph.ark` (ADV-002)
- `ark/dsl/stdlib/code_graph_queries.ark` (ADV-002)
- `ark/dsl/stdlib/studio.ark` (ADV-003)
- `ark/dsl/stdlib/evolution.ark` (ADV-004)
- `ark/dsl/stdlib/agent.ark` (ADV-005)
- `ark/dsl/stdlib/visual.ark` (ADV-006)
- No stdlib file for ADV-007 (ecosystem research, no stdlib additions)
- No stdlib file for ADV-008 (sibling package, no Ark stdlib changes per TC-10/TC-23)
- No stdlib file for ADV-010 (telemetry infrastructure, no `.ark` stdlib)

### Expected concepts skipped or consolidated

- **ADV-001 temporal expressions**: Expressif has temporal stdlib (age, forward/backward, first-of-month). The ADV-001 manifest scope decision (Q3) chose "B — core subset (numeric+text+special+predicates)"; temporal expressions are out of v1 scope and were not implemented. Omitted per traversal rule (not in source artefacts).
- **ADV-001 file expressions**: Similarly excluded from v1 scope (Q3 decision). Omitted.
- **ADV-002 Python ast module**: Mentioned in manifest as "Python `ast` module adoption" for indexing. Not a declared Ark concept (it's an external dependency); omitted per granularity rules.
- **ADV-002 query DSL as standalone item**: The manifest mentions a "query DSL" but the actual implementation uses expression items in `code_graph_queries.ark`. Individual query expressions already harvested; omitted the vague "query DSL" meta-concept.
- **ADV-003 Item::StudioJob**: Manifest uses `role`, `studio`, `workflow_command`, `hook`, `rule`, `template` as item kinds. "StudioJob" is not the actual item name. Harvested as the actual 6 item kinds declared in the manifest concept section.
- **ADV-004 Item::ConstraintDef vs Item::Constraint**: Manifest concept section uses `constraint` as item kind; stdlib uses `ConstraintDef` as struct name. Both harvested separately (one for item kind, one for struct).
- **ADV-007 team-pipeline.md, team-mcp.md, binartlab.md, marketplace-and-dsl.md, qmd-and-cgc.md, claude-ecosystem.md, lsp-and-orchestrator.md**: These are phase 1/3.2 project-research files but are not named deliverables referenced by TC slugs in the manifest. The manifest TCs (TC-001..TC-003, TC-010) reference `phase1-cross-project-issues.md` (the synthesis), not individual project files. Individual project research files omitted; synthesis artefacts included.
- **ADV-008 ShapeML item kinds in shape_grammar.ark**: The shape grammar is expressed using existing Ark item kinds (abstraction, class, island, bridge). No new Ark item kinds were introduced (per TC-10 / TC-23 no-modification constraint). Omitted as there are no new item kinds to harvest.
- **ADV-010 design-hook-integration, design-backfill-strategy, design-error-isolation, design-test-strategy**: These design docs specify implementation details of concepts already captured from manifest and capture-contract/cost-model/aggregation designs. The additional named constructs (settings.local.json hook config, backfill confidence columns) are sub-features covered by `SubagentStop hook` and `backfill mechanism` rows. Not harvested separately to avoid granularity bloat.
