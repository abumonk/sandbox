# Architecture Decisions

Decisions made during task implementation.

## Kebab-case scope restriction in Ark
- **Context**: Ark grammar supports both IDENT (underscores) and pipe_fn_ident (hyphens) for naming. Allowing hyphens everywhere creates ambiguity with the minus operator.
- **Decision**: Kebab-case (hyphenated names like text-to-lower) is permitted only inside pipe stages via pipe_fn_ident. Top-level expression and predicate names must use standard IDENT (underscores). This avoids grammar ambiguity with the minus operator.
- **From**: ADV-001

## PASS_OPAQUE for domain-specific Z3 verification
- **Context**: Domain-specific operations (graph-callers, graph-dead-code, etc.) require complex semantics that would be prohibitively expensive to encode fully in SMT.
- **Decision**: Domain-specific operations are registered as opaque primitives in Z3 verification rather than fully modeled. This allows structural verification (no dangling edges, type correctness) without encoding full graph semantics in SMT.
- **From**: ADV-002

## Z3 ordinals for DAG acyclicity verification
- **Context**: Any Ark item type with directed references (studio escalation paths, visual review cycles, etc.) must be verified cycle-free. Simple DFS could be used but diverges from Ark's verification philosophy.
- **Decision**: Z3 ordinal assignment is the standard Ark pattern for DAG acyclicity checks. Assign each node an integer ordinal; require edges to strictly increase. This generalizes across any item type with directed references, and was reused in ADV-006 (visual_review cycles) without modification to the approach.
- **From**: ADV-003, ADV-006

## Dual Lark+Pest grammar maintenance
- **Context**: Ark supports both a Python runtime (using Lark grammar) and a Rust runtime (using Pest grammar). Grammar extensions must be kept in sync.
- **Decision**: Every grammar extension requires parallel updates to both `ark_grammar.lark` (Python) and `ark.pest` (Rust). Dedicated tasks (T003/T004) ensure neither falls behind. This is a maintenance cost but preserves Ark's dual-runtime capability.
- **From**: ADV-003

## LLM-as-Judge Callback Pattern for Evolution Fitness
- **Context**: The evolution fitness scorer needs LLM evaluation but the implementation should not hardcode a specific LLM API.
- **Decision**: Fitness scoring uses a callback/dependency-injection pattern where the LLM judge function is passed as a parameter. This allows unit testing with mock scorers while supporting any LLM backend in production. The same pattern is used for semantic preservation checks in constraint_checker.py.
- **From**: ADV-004

## Phased Optimizer Engine Implementation
- **Context**: The Hermes project defines three optimizer engines (GEPA, MIPROv2, Darwinian) with different maturity levels.
- **Decision**: Implement GEPA and MIPROv2 as functional engines in the initial adventure; Darwinian (code evolution) as a NotImplementedError stub. This delivers immediate value for text-based evolution (skills, prompts, roles) while deferring the more complex code evolution to a future adventure with proper git integration and pytest guardrails.
- **From**: ADV-004

## Skill-first message routing in AgentRunner
- **Context**: AgentRunner receives messages that may match learned skills or require model inference. Need a dispatch strategy.
- **Decision**: Messages are first matched against skill triggers (by priority). Only if no skill matches does the runner fall back to model inference. This prioritizes procedural knowledge over expensive LLM calls, reduces latency for known tasks, and incentivizes skill generation.
- **From**: ADV-005

## ViewportSize as enum with dimension lookup
- **Context**: Visual preview items need viewport sizing. A struct with width/height is flexible but verbose in DSL; an enum of presets (mobile, tablet, desktop, custom) is simpler to author.
- **Decision**: Use an enum of viewport presets with a dimension lookup table in the renderer. Custom sizes are supported via the "custom" variant with explicit dimensions in render_config.
- **From**: ADV-006

## Single-platform deploy-MCP commitment
- **Context**: Phase 6 has overlapping MCP options for deployment (Vercel, Railway, four-server Cloudflare suite, Supabase). Adopting multiple inflates agent permission surface, doubles observability tooling, and complicates role permission manifests.
- **Decision**: Phase 6 must make a one-time platform commitment (Cloudflare suite OR Vercel+Railway OR Vercel+Supabase) and adopt the matching MCPs as a unit. No mix-and-match. Decision must precede any deploy-MCP integration task.
- **From**: ADV007-T015

## github and memory as the only CORE MCPs
- **Context**: Of 14 MCP servers in the Phase 3.2 catalog, only two unlock capabilities the filesystem-only architecture cannot achieve cheaply: durable cross-session graph state (memory) and centralized git automation with PR-level review surface (github).
- **Decision**: Tier `github` and `memory` as CORE; integrate before any other MCP. All others are OPTIONAL or SKIP. Adoption order: github (Phase 3.2 wrap-up) → memory (Phase 2 start).
- **From**: ADV007-T015

## Ark as the single DSL trunk; ARL as the type backbone
- **Context**: Claudovka has three DSLs (PDSL PEG, binartlab YAML, Ark), four copies of the pipeline state machine, and five schema dialects. Each domain surface (markdown, jsonl, SQL, event wire) is currently designed independently.
- **Decision**: Pick Ark as the unification trunk. Every entity (22 total: 15 existing + 7 Phase-5 additions) is defined as an Ark type and every concrete store (markdown, jsonl, SQL, event) is a renderer over the same ARL value. PDSL becomes a dialect of Ark; binartlab YAML is generated from Ark via codegen. Round-trip property tests protect every renderer pair.
- **From**: ADV007-T020

## Non-flag-day refactoring with feature-flag matrix
- **Context**: The Phase-6 reconstruction touches every entity; a big-bang migration would be unreviewable and unrollback-able.
- **Decision**: Ship via milestones M0-M8 where each stage is independently reversible via a named flag in `.agent/config.md` (`events_shadow`, `canonical_task_dir`, `lead_state_v2`, `knowledge_lessons`, `hooks_v2`, `registry_generated`, `mcp_only_ops`, `contract_enforcement`). Rendered-view shims keep legacy consumers working across every rename. Rollback is a flag flip + `state_rebuild` replay, never a `git revert`. Three consecutive green CI runs required before a forward-only trapdoor opens.
- **From**: ADV007-T020

## Ark-as-host-language dogfooded via external package
- **Context**: ADV-008 needed to build ShapeML-style procedural shape grammar. Options were: extend Ark core with new syntax, or build a consumer package that imports Ark as a library.
- **Decision**: `shape_grammar/` sits next to `ark/` in R:/Sandbox with a strict one-way `shape_grammar -> ark` dependency. Shape grammars are ordinary Ark islands using existing syntax (no Lark grammar changes, no new AST nodes). The `shape_grammar` package provides evaluator, verifier passes, codegen, and runtime. Rationale: keeps Ark core stable while proving real external-consumer ergonomics. Feasibility study (T03) found 9 EXPRESSIBLE entities, 2 NEEDS_WORKAROUND, 0 BLOCKED — host-language adequacy confirmed.
- **From**: ADV-008
