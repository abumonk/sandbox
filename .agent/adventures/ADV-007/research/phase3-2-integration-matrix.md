# Phase 3.2 — External Tools Integration Matrix

**Task:** ADV007-T016
**Target Condition:** TC-011
**Date:** 2026-04-14
**Synthesizes:** T012 (QMD + CGC), T013 (ECC + CCGS), T014 (LSP + Agent Orchestrator), T015 (14 MCP servers)

---

## 1. Phase Legend

The 10 roadmap phases serve as the matrix columns. Compressed reminders so cells can be read in isolation:

| Code | Phase | Theme |
|------|-------|-------|
| **P1** | Phase 1 | Project review (Team Pipeline, Team MCP, Binartlab, Marketplace, Pipeline DSL) |
| **P2** | Phase 2 | Unified knowledge base + token economy redesign of `.agent` entities |
| **P3.1** | Phase 3.1 | Pipeline management review, profiling/optimization/self-healing skills, role review |
| **P3.2** | Phase 3.2 | External tools research (this phase) — adoption decisions land here |
| **P4** | Phase 4 | UI: workflow entities, live updates, node/graph/DSL editor, tabs/panes |
| **P5** | Phase 5 | New concepts: scheduling, human-as-role, input store, messenger, recommendations |
| **P6** | Phase 6 | Infra: MCP-only deploy/compile/build, autotest, automation-first |
| **P6.1** | Phase 6.1 | Final reconstruction — simplify, abstract representation, iterative refactor |
| **P6.2** | Phase 6.2 | Post-final — benchmarks, profile/test, migrations |
| **P7** | Phase 7 | On sail — daily optimization, self-healing, human-machine balance, futuring |

Cell values: **PRI** = primary (the tool is load-bearing for that phase), **SEC** = secondary (useful but the phase succeeds without it), **n/a** = no meaningful contribution.

---

## 2. Master Matrix (Tool × Phase)

| # | Tool | Tier | P1 | P2 | P3.1 | P3.2 | P4 | P5 | P6 | P6.1 | P6.2 | P7 | Blockers |
|---|------|------|----|----|------|------|----|----|----|------|------|----|----------|
| 1 | **QMD** (knowledge retrieval) | Tier-1 Adopt | SEC: index P1 reports for cross-project search | **PRI**: hybrid retrieval over knowledge files (FTS5 + vector + rerank) | SEC: planner queries past patterns before designing | **PRI**: lookup engine for the research corpus produced this phase | n/a | SEC: backs messenger / recommendations grounding | n/a | SEC: corpus-aware refactor planning | n/a | SEC: futuring queries against historical decisions | None blocking; +2 GB GGUF disk, Node 22 runtime |
| 2 | **CGC** (CodeGraphContext) | Tier-1 Adopt | SEC: surface call graphs of the 5 reviewed projects | n/a | **PRI**: reviewer impact analysis (`who calls X?`) | SEC: substrate for evaluating other graph tools | n/a | n/a | **PRI**: implements `code_graph.ark` island; live watcher | SEC: dead-code + complexity inputs to refactor plan | SEC: analytics on call-graph deltas | SEC: drift detection via watch-mode | Needs Python 3.10+; `.ark` indexing requires future tree-sitter grammar |
| 3 | **Everything Claude Code (ECC)** | Tier-3 Cherry-pick | n/a | SEC: instinct schema as KB upgrade target | **PRI**: hook profile env-gating, observer re-entrancy guard, `/quality-gate` pattern | n/a | n/a | SEC: SQLite session adapter for messenger metrics | SEC: selective install manifest for distributing skills | SEC: `configure-ecc` wizard pattern for repo onboarding | n/a | SEC: model-routing visibility | Catalog inflation and product sprawl — DO NOT bulk import |
| 4 | **Claude Code Game Studios (CCGS)** | Tier-2 Adapt | n/a | SEC: workflow-catalog YAML schema for entity lifecycle | **PRI**: 3-tier model mapping, `disallowedTools`, review-intensity modes, `/team-*` orchestration | n/a | SEC: path-scoped rules for UI subtrees | **PRI**: human-as-role gating via Collaboration Protocol; team-orchestration commands | n/a | SEC: workflow-catalog formalizes phase gates | n/a | SEC: review-mode `solo` for hot-fix loops | Bash-only hooks fragile on Windows — must port to Python/Node |
| 5 | **LSP (Ark DSL language server)** | Tier-1 Adopt | n/a | n/a | SEC: live diagnostics surface profiling/lint findings | **PRI**: editor-side proof of pipeline maturity | **PRI**: in-IDE editing experience for `.ark` files; codegen preview docs | SEC: `human-as-role` author flow uses LSP for spec edits | n/a | SEC: rename/refactor refactorings driven by LSP code actions | n/a | SEC: inline verify lens flags drift in real time | Phase A blocked on `pygls` install path; Phase B blocked on Rust verify parity (z3-sys binding) |
| 6 | **Agent Orchestrator (ComposioHQ AO)** | Tier-2 Adapt | n/a | n/a | **PRI**: reactions engine pattern → `reaction_def` item; worktree-per-agent | n/a | n/a | **PRI**: state-machine session lifecycle generalizes scheduling + messenger triggers | **PRI**: plugin-slot architecture for execution backends; PR/CI hooks | SEC: hash-namespacing prevents collisions during multi-agent refactor | n/a | **PRI**: declarative reactions are the natural shape for self-healing | Skip Node toolchain, tmux runtime, dashboard; native `.ark` re-implementation only |
| 7 | **MCP: github** (`@modelcontextprotocol/server-github`) | Tier-1 CORE | SEC: cross-repo issue/PR enumeration during review | n/a | SEC: routes reviewer comments through PRs | **PRI**: enables PR-per-adventure starting now | SEC: UI consumes PR/issue lists for live view | SEC: messenger watches PR events | **PRI**: replaces shell git/`gh` calls in pipeline scripts | n/a | SEC: PR-driven migration rollouts | **PRI**: stale-PR / branch hygiene checks | Needs fine-grained PAT per repo; revisit official Go server at GA |
| 8 | **MCP: memory** (`@modelcontextprotocol/server-memory`) | Tier-1 CORE | SEC: load P1 findings as entities for graph queries | **PRI**: canonical store for unified KB; entity schema (Adventure/Task/Role/Skill/...) | SEC: planner queries graph for similar tasks | n/a | SEC: graph drives UI relationship views | **PRI**: graph traversal = recommendations engine | n/a | n/a | n/a | **PRI**: long-horizon learning across adventures | Schema discipline required; capture schema as `.ark` spec under `meta/` |
| 9 | **MCP: sequential-thinking** | Tier-3 Cherry-pick | n/a | n/a | **PRI**: planner/reviewer reasoning audit trail | n/a | n/a | SEC: messenger diagnoses why a recommendation triggered | n/a | n/a | n/a | SEC: self-healing diagnosis trace | Token tax — enable per-role only |
| 10 | **MCP: firecrawl** | Tier-3 On-demand | SEC: ingest external project READMEs in bulk | n/a | n/a | SEC: would have helped this very phase | n/a | SEC: input-store ingestion of upstream docs | n/a | n/a | n/a | SEC: futuring crawls of upstream tool changelogs | Paid tier beyond free quota; API key |
| 11 | **MCP: supabase** | Tier-3 Conditional | n/a | n/a | n/a | n/a | **PRI**: realtime UI persistence + auth | SEC: input store backing | **PRI** (if chosen): managed Postgres + edge functions | n/a | n/a | SEC: log queries for ops | Single-deploy-platform decision blocker — pick ONE of {Supabase, Vercel+Railway, Cloudflare suite} |
| 12 | **MCP: vercel** | Tier-3 Conditional | n/a | n/a | n/a | n/a | **PRI** (if chosen): UI deploy target | n/a | **PRI** (if chosen): MCP-only deploy automation | n/a | n/a | SEC: deployment log queries | Single-deploy-platform decision blocker |
| 13 | **MCP: railway** | Tier-3 Conditional | n/a | n/a | n/a | n/a | n/a | SEC: hosts messenger/scheduler workers | **PRI** (if chosen): backend services + DB provisioning | n/a | n/a | SEC: log tail for ops | Single-deploy-platform decision blocker; only when stateful backend appears |
| 14 | **MCP: cloudflare-docs** | Tier-3 Conditional | n/a | n/a | n/a | n/a | SEC: reference during UI infra setup | n/a | **PRI** (if CF chosen): canonical reference for Workers/Pages config | n/a | n/a | SEC: lookups during incident response | Bound to platform decision; OAuth |
| 15 | **MCP: cloudflare-workers-bindings** | Tier-3 Conditional | n/a | n/a | n/a | n/a | n/a | n/a | **PRI** (if CF chosen): provision KV/D1/R2/DO/Queues from agent | SEC: rebind during refactor | n/a | n/a | Bound to platform decision; OAuth leaves sandbox |
| 16 | **MCP: cloudflare-workers-builds** | Tier-3 Conditional | n/a | n/a | n/a | n/a | n/a | n/a | **PRI** (if CF chosen): build/deploy automation for Workers | n/a | n/a | SEC: rollback on failure | Bound to platform decision |
| 17 | **MCP: cloudflare-observability** | Tier-3 Conditional | n/a | n/a | n/a | n/a | n/a | n/a | SEC (if CF chosen): set up logpush during deploy | n/a | n/a | **PRI** (if CF chosen): logs/metrics/traces for live ops | Bound to platform decision |
| 18 | **MCP: clickhouse** | Tier-3 On-scale | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | **PRI**: benchmark warehouse + variance analytics | SEC: cross-adventure metrics dashboards | Only at >10k rows; consider local DuckDB-MCP first |
| 19 | **MCP: magic** (`@magicuidesign/mcp`) | Tier-3 One-shot | n/a | n/a | n/a | n/a | **PRI** for spike, then drop | n/a | n/a | n/a | n/a | n/a | Design-system drift if used past spike |
| 20 | **MCP: AbletonMCP** | Skip | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | Out of scope |

**Tier glossary**
- **Tier-1 Adopt / CORE** — Schedule integration in the next adventure; load-bearing for downstream phases.
- **Tier-2 Adapt** — Adopt the *patterns* natively (re-implement in `.ark` / Rust / Python), not the upstream binaries.
- **Tier-3 Cherry-pick / Conditional / On-demand / On-scale / One-shot** — Defer until a specific trigger fires (deploy-platform decision, metrics volume, UI spike, etc.).
- **Skip** — No path to value within the 7-phase roadmap.

---

## 3. Consolidated Recommendation List

### 3.1 Adopt immediately (next 1–2 adventures, drives Phase 3.2 → Phase 4)

| Tool | Trigger | Effort | Payoff |
|------|---------|--------|--------|
| **MCP: github** | Phase 3.2 wrap | <0.5 day (npx + PAT + permission row) | PR-per-adventure, replaces shell git, foundation for Phase 6 deploys |
| **MCP: memory** | Phase 2 kickoff | ~2 days (entity schema + migration of existing `.agent/knowledge/*.md`) | Typed knowledge graph; deduplication; planner can query "similar tasks" |
| **QMD** | Phase 3.2 wrap | ~2 days (plugin install + 4 collections + post-task hook) | Hybrid retrieval over markdown corpus; researcher token cost ↓ ~80% |
| **CGC** (wrapper for `code_graph.ark`) | Early Phase 3.x | ~3 days Pattern A wrapper, ~1 week extra for Pattern B bridge | Implements planned `code_graph.ark` island; reviewer gains call-graph queries |
| **LSP Phase A (pygls)** | Phase 3.2 / Phase 4 enablement | ~10 dev-days (M1–M6) | Editor diagnostics, completion, hover, codegen preview; sets stage for Phase 4 UI |

**Aggregate effort:** ~3 weeks of focused work for the five Tier-1 adoptions, all within the Phase 3.2 → Phase 4 transition window.

### 3.2 Evaluate (decision required before adoption)

| Tool | Decision Owner | Decision Trigger | Open Question |
|------|---------------|------------------|---------------|
| **Agent Orchestrator** patterns | architect | Phase 3.1 role review + Phase 6 runtime planning | Native `.ark` `reaction_def` item + `WorktreeManager` — wrap or in-house? Prefer in-house. |
| **CCGS workflow-catalog YAML** | architect | Phase 3.1 / Phase 6.1 | Replace prose pipeline descriptions with YAML phase/artifact catalog driving `/gate-check`? |
| **CCGS three-tier model mapping + `disallowedTools`** | architect | Phase 3.1 | Codify Director/Lead/Specialist model tiers in `.agent/config.md`? |
| **ECC instinct schema** | architect | Phase 2 | Migrate `.agent/knowledge/*.md` to per-pattern files with confidence scores — worth the cost at ~7 adventures? |
| **MCP: sequential-thinking** | role designer | Phase 3.1 | Worth the token tax for planner/reviewer audit trails? Scope to those two roles only. |
| **MCP: supabase OR vercel OR cloudflare suite OR railway** | architect | Phase 4 / Phase 6 | **Pick exactly one platform stack.** Adopting all = permission/observability sprawl. |
| **MCP: clickhouse** | ops | Phase 6.2 | Adopt at first metrics-volume pain point; consider local DuckDB-MCP as cheaper alternative |
| **MCP: firecrawl** | researcher | Any phase | Adopt the first time an adventure needs >5-page web ingestion |
| **MCP: magic** | UI lead | Phase 4 | Use for first UI scaffolding spike only; do not let generated components persist |
| **LSP Phase B (tower-lsp Rust)** | architect | After Rust verify parity | Defer until Rust pipeline closes the verify gap (z3-sys binding) |

### 3.3 Skip

| Tool | Reason |
|------|--------|
| **MCP: AbletonMCP** | Out of domain; reconsider only if Phase 5 introduces a creative-tools vertical |
| **ECC product layer** (AgentShield, ECC Tools SaaS, dashboard, GitHub App) | Out of scope; product sprawl |
| **CCGS engine specialist sets** (godot, unity, unreal sub-specialists) | Domain mismatch — port the *structure*, not the *roster* |
| **AO Node toolchain + tmux runtime + Next.js dashboard** | Forks UI story and regresses Windows dev path; adopt patterns natively instead |

---

## 4. Cross-Tool Conflicts and Redundancies

### 4.1 Confirmed redundancies that force a choice

1. **CGC vs Ark `code_graph.ark` self-build.** Ark already plans this island. Decision: **do not build twice** — wrap CGC behind the planned spec interface. Keep the spec as the contract; let CGC be the implementation.
2. **CGC vs LSP `references` capability.** Both can answer "who calls X?". Resolution: LSP routes its `textDocument/references` *into* CGC for non-`.ark` files and uses Ark's existing `ark impact` graph for `.ark` files. No duplication; LSP becomes a thin façade for both backends.
3. **MCP: memory vs Ark knowledge files vs ECC instinct schema.** Three contenders for the knowledge layer. Resolution: **memory MCP is the canonical store**, instinct schema informs the *entity schema*, markdown files become a human-readable export. QMD indexes the markdown export for retrieval. Single write path, multiple read surfaces.
4. **Deploy MCPs (Vercel | Railway | Supabase | Cloudflare suite).** All four overlap on the deploy concern. Resolution: **single-deploy-platform decision** required at Phase 4/6 boundary — the T015 carry-forward blocker. Recommendation: one of {Cloudflare-only, Vercel+Supabase, Vercel+Railway} — never all.
5. **AO reactions engine vs `cron_task_def`.** Time-triggered vs event-triggered overlap. Resolution: generalize `cron_task_def` into `reaction_def` (event-triggered including `time.tick`), Z3-verifiable for acyclicity.
6. **CCGS `/team-*` vs ECC `/multi-*` orchestration commands.** Two naming conventions for the same idea. Resolution: adopt CCGS naming (`/claudovka:team-*`) — closer to Claudovka's hierarchical/collaborative ethos.
7. **ECC SQLite session store vs `.agent/adventures/*/metrics.md`.** Both hold per-task metrics. Resolution: keep markdown as source of truth; load into SQLite (or ClickHouse at scale) for analytics, not as primary store.

### 4.2 Apparent conflicts that are actually complementary

- **QMD vs MCP: memory.** QMD = unstructured markdown retrieval (BM25 + vector + rerank). memory = typed entity graph. Disjoint substrates; both useful, no overlap.
- **CGC vs MCP: memory.** Code graph vs knowledge graph — different node types, different query workloads. Bridge them via shared entity IDs (`function:repo/path:name`).
- **LSP vs ECC `/harness-audit`.** LSP gives in-IDE feedback per-file; harness audit is a CLI pass over the whole repo. Both legitimate; no overlap.

---

## 5. Dependency Ordering (which tool enables which)

```
                                   [github MCP]
                                        |
                                        v
                              [PR-per-adventure flow]
                                        |
   [memory MCP] -- entity schema --> [unified KB (P2)]
        |                                   |
        |                                   +--> [QMD index over KB exports]
        |                                                |
        |                                                v
        |                                  [planner/researcher retrieval (P3.1)]
        v
   [CCGS workflow-catalog YAML] --> [/gate-check, /team-*]
                                            |
                                            v
                                  [Phase gate enforcement]

   [CGC wrapper] ----+
                     |
                     +--> [code_graph.ark island lit] --> [reviewer impact queries]
                     |
                     +--> [LSP textDocument/references backend]
                                            |
   [LSP Phase A pygls] <---+----------------+
        |                  |
        v                  |
   [Editor experience]     +--> [LSP Phase B tower-lsp]
                                       ^
                                       |
                              (blocked: Rust verify parity)

   [AO patterns: reactions, worktrees, plugin slots]
        |
        +--> [reaction_def in .ark]   --> [P3.1 self-healing skills]
        +--> [WorktreeManager]        --> [P6 parallel agent isolation]
        +--> [Backend trait]          --> [P6 multi-runtime: local/docker/k8s]
                                            |
                                            v
                              [single-deploy-platform pick (BLOCKER)]
                                  |       |       |
                                  v       v       v
                             [Vercel | CF suite | Supabase|+Railway]

   [sequential-thinking MCP] --> per-role opt-in (P3.1 planner/reviewer only)

   [magic MCP] --> P4 spike only --> [discard]

   [clickhouse MCP] --> activated when metrics > 10k rows (P6.2)

   [firecrawl MCP] --> activated on first crawl-heavy task
```

### 5.1 Critical-path ordering

1. **github MCP** (no dependencies, unblocks PR workflow) — adopt **first**.
2. **memory MCP** (no dependencies, unblocks unified KB) — adopt **second**, in parallel with github MCP.
3. **QMD** (depends on KB markdown corpus existing — i.e., on memory MCP exports + existing `.agent/` files) — adopt **third**.
4. **CGC wrapper** (depends on `code_graph.ark` interface stabilization in Phase 3.x) — adopt **fourth**.
5. **LSP Phase A** (independent but most useful after CGC for `references`) — adopt **fifth**, can run in parallel with CGC.
6. **AO native patterns** (`reaction_def`, `WorktreeManager`, plugin slots) — adopt **sixth**, drives Phase 6 runtime.
7. **CCGS workflow-catalog YAML + 3-tier model mapping** — adopt **seventh**, formalizes what Phase 3.1 reviews.
8. **Single deploy MCP** — gated on the platform decision; do not adopt any until decision is made.
9. **sequential-thinking, magic, firecrawl, clickhouse** — opportunistic, no critical-path role.

### 5.2 Carry-forward blockers (from T015 + T012 + T014)

- **B-1: Single-deploy-platform decision** (T015) — blocks 5 MCPs (supabase, vercel, railway, four cloudflare). Owner: architect. Trigger: Phase 4 UI hosting choice.
- **B-2: Memory-graph schema authority** (T015) — does the entity schema live in `ark/specs/meta/` (preferred — Z3-verifiable) or `.agent/knowledge/schema.md`? Owner: architect. Trigger: Phase 2 kickoff.
- **B-3: Permission-string convention** (T015) — `mcp.<server>.<resource>.<action>`? Owner: role designer. Trigger: any MCP rollout — needed before github MCP lands.
- **B-4: Ark tree-sitter grammar** (T012) — blocks CGC from indexing `.ark` source. Owner: DSL maintainer. Trigger: when spec corpus justifies the cost (defer).
- **B-5: Rust verify parity (z3-sys binding)** (T014) — blocks LSP Phase B port to `tower-lsp`. Owner: Rust pipeline lead. Trigger: after Rust SMT-LIB writer reaches feature parity.
- **B-6: github MCP variant choice** (T015) — `@modelcontextprotocol/server-github` (TS, current) vs `github/github-mcp-server` (Go, official). Owner: architect. Trigger: when official Go server reaches GA. Default: pin TS for now.
- **B-7: Bash-only hooks on Windows** (T013 CCGS) — port to Python/Node before adopting CCGS hook patterns.

---

## 6. Cost / Effort Estimates

| Adoption | Dev-days | Token cost (initial) | Recurring cost | Notes |
|----------|---------:|---------------------|----------------|-------|
| github MCP | 0.5 | minimal | API rate-limit only | PAT setup + permission row |
| memory MCP | 2 | ~5k for migration | minimal | Schema design dominates effort |
| QMD | 2 | ~10k for index walks | ~1k/day re-embed | +2 GB GGUF on disk, Node 22 runtime |
| CGC wrapper (Pattern A) | 3 | ~5k for island wiring | minimal | Python 3.10+ dep |
| CGC bridge (Pattern B, optional) | +5 | ~10k for codegen comments | minimal | Adds `// ark:gen <hash>` traceability |
| LSP Phase A (pygls) | 10 | ~20k for VS Code ext scaffold | minimal per session | M1–M6 milestones |
| LSP Phase B (tower-lsp) | 10–15 | ~30k | minimal | **Blocked on B-5** |
| AO native patterns (reaction_def, WorktreeManager, Backend trait) | 10–15 | ~25k for DSL+codegen+orchestrator changes | minimal | Spread across DSL, parser, codegen, orchestrator crates |
| CCGS workflow-catalog YAML | 2 | ~5k | minimal | YAML schema + `/gate-check` skill |
| CCGS 3-tier model mapping | 0.5 | minimal | minimal | Codify in `.agent/config.md` |
| ECC hook-profile env-gating | 0.5 | minimal | minimal | Wrap existing `.claude/hooks/` |
| ECC instinct schema migration | 3 | ~15k for migration | per-write overhead | Optional — defer to Phase 2 |
| sequential-thinking MCP | 0.5 | ongoing token tax per call | per-role token cost | Per-role opt-in only |
| magic MCP | 0.5 | per-spike API tokens | discard after spike | One-shot use |
| Deploy MCP (whichever platform) | 1–2 | minimal | platform API quotas | Gated on B-1 |
| firecrawl MCP | 0.5 | per-crawl API cost (paid) | per-crawl | On-demand |
| clickhouse MCP | 1 | minimal | hosted DB cost | On-scale only |

**Sum of Tier-1 adoptions (immediate):** ~17.5 dev-days, ~70k initial tokens, negligible recurring.

---

## 7. Synthesis Rules Used (transferable to future research syntheses)

When merging multiple research documents into a decision matrix:

1. **Phase coverage first** — if a tool fits zero phases, it skips, regardless of internal merit.
2. **Distinguish primary from secondary** — every cell should answer *would the phase fail without this tool?* If no, downgrade to SEC.
3. **Single-decision blockers are first-class outputs** — surface them at the matrix layer (column or table) rather than hiding in prose.
4. **Conflict resolution before recommendation** — apparent overlaps must be tagged as either *redundant* (force a choice) or *complementary* (separate substrates).
5. **Native re-implementation is a tier** — when a tool's *patterns* are valuable but the *binary* drags toolchain weight, codify "Tier-2 Adapt" so the recommendation is unambiguous.
6. **Critical-path ordering ≠ priority ordering** — list both. Priority drives funding; ordering drives execution.

---

## 8. Open Questions Forwarded to Architect

1. **B-1 platform pick** — recommend Cloudflare suite (closes provision/build/run/docs loop) unless team prefers Vercel+Supabase developer ergonomics.
2. **B-2 schema authority** — recommend `ark/specs/meta/knowledge_schema.ark` so Z3 can verify entity invariants.
3. **B-3 permission convention** — recommend `mcp.<server>.<resource>.<action>` exactly as drafted in T015.
4. Should LSP Phase A target `pygls` (current Python tooling) or skip straight to a Rust `tower-lsp` skeleton with a stubbed verifier? Recommendation: pygls now, port later — the Rust pipeline gap (B-5) is real.
5. Adopt CCGS `review_mode: solo` per-task, or keep always-on review as a Claudovka identity invariant?

---

## 9. Target Conditions Touched

- **TC-011** — Integration potential matrix produced (this document).
- Carries forward open items from TC-010 (capability summaries) and TC-012 (MCP catalog).
- Feeds TC-031 (master roadmap) and TC-032 (adventure dependency graph) downstream.
