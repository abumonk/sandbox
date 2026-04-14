# Phase 3.2 — MCP Servers Catalog

**Task**: ADV007-T015
**Target Condition**: TC-012 (MCP server catalog with 14 servers analyzed)
**Date**: 2026-04-14

## Scope

Evaluate 14 MCP servers from the Phase 3.2 roadmap for integration into the Claudovka ecosystem (team-pipeline, team-mcp, binartlab, marketplace, pipeline-DSL, ark). Each server is rated:

- **CORE** — Must integrate; required for at least one foundational adventure or workflow.
- **OPTIONAL** — Useful for specific adventures/phases; integrate on demand.
- **SKIP** — Not applicable to current Claudovka scope.

## Summary Table

| # | Server | Package / URL | Tier | Phase Fit | Primary Use |
|---|--------|---------------|------|-----------|-------------|
| 1 | github | `@modelcontextprotocol/server-github` | **CORE** | All phases | PR/issue/repo automation, agent-driven git ops |
| 2 | memory | `@modelcontextprotocol/server-memory` | **CORE** | Phase 2, 5, 7 | Cross-session knowledge graph for agents |
| 3 | firecrawl | `firecrawl-mcp` | OPTIONAL | Phase 3.2, 5 | External docs/research ingestion |
| 4 | supabase | `@supabase/mcp-server-supabase` | OPTIONAL | Phase 4, 6 | UI persistence, auth, realtime |
| 5 | sequential-thinking | `@modelcontextprotocol/server-sequential-thinking` | OPTIONAL | Phase 3.1, 7 | Structured reasoning for planner/reviewer |
| 6 | vercel | `https://mcp.vercel.com` | OPTIONAL | Phase 4, 6 | UI / static deploy target |
| 7 | railway | `@railway/mcp-server` | OPTIONAL | Phase 6 | Backend service deploys |
| 8a | cloudflare-docs | Cloudflare hosted MCP | OPTIONAL | Phase 6 | CF API reference for agents |
| 8b | cloudflare-workers-bindings | Cloudflare hosted MCP | OPTIONAL | Phase 6 | Workers KV/D1/R2 binding mgmt |
| 8c | cloudflare-workers-builds | Cloudflare hosted MCP | OPTIONAL | Phase 6 | Worker build/deploy automation |
| 8d | cloudflare-observability | Cloudflare hosted MCP | OPTIONAL | Phase 7 | Logs, metrics, traces for live ops |
| 9 | clickhouse | `https://mcp.clickhouse.cloud/mcp` | OPTIONAL | Phase 6.2, 7 | Benchmark/metrics analytics warehouse |
| 10 | AbletonMCP | `ableton-mcp` | SKIP | — | Out of scope (music production) |
| 11 | magic | `@magicuidesign/mcp` | OPTIONAL | Phase 4 | UI component scaffolding |

**Adoption order**: github → memory → sequential-thinking → magic → supabase/vercel → cloudflare suite → clickhouse → firecrawl → railway → (skip ableton).

---

## 1. github — `@modelcontextprotocol/server-github`  [CORE]

### Purpose & Capabilities
Official Anthropic MCP server exposing the GitHub REST/GraphQL API as MCP tools. Tool surface includes:

- **Repos**: create/fork, list contents, get/create/update file, push multiple files in one commit, list branches, create branch.
- **Issues**: list/get/create/update/comment, search issues, assign labels.
- **Pull Requests**: create, list, get, merge, review, request reviewers, list files, get diff, post review comments.
- **Search**: code search, issue search, user search.
- **Actions/Workflows** (newer revisions): trigger and inspect workflow runs.

Authentication is a Personal Access Token (classic or fine-grained) via `GITHUB_PERSONAL_ACCESS_TOKEN` env var. Runs locally via `npx @modelcontextprotocol/server-github`.

### Why CORE for Claudovka
Roadmap explicitly calls it out. It is the *substrate* for Phase 6 (MCP-only deploy/compile/build) and Phase 6.1 (automation-first) because it lets agents:

1. **Replace shell git** in `implementer` and `reviewer` roles — no more local `git push` failures, hook-skip footguns. The pipeline already has feedback rules around `--no-verify` and amend safety; routing through MCP centralizes those guards.
2. **Open task-level PRs** automatically from `team-pipeline` adventures so each adventure produces a reviewable artifact rather than a single squashed commit.
3. **Cross-repo orchestration** for the multi-repo Claudovka mesh (binartlab, marketplace, team-mcp, team-pipeline, ark) — listing open PRs, syncing labels, triggering workflows.
4. **Issue ↔ Adventure mapping**: bidirectional sync between `.agent/adventures/*/manifest.md` Target Conditions and GitHub issues; reviewers can drop comments that flow back into review reports.
5. **Marketplace publishing** (Phase 4/5) via release/tag automation.

### Integration Plan (recommended)
- **Phase 3.2 (now)**: Wire as default MCP for orchestrator and implementer roles. Add `mcp.github` capability to role permission manifests.
- **Phase 4**: UI consumes PR/issue lists for the live workflow view.
- **Phase 6**: Replace shelled `git`/`gh` calls in pipeline scripts with MCP tool calls.
- **Phase 7**: Health checks on long-lived branches, stale PR reminders via messenger agent.

### Risks / Caveats
- Token scope sprawl — need fine-grained tokens per repo to satisfy least-privilege.
- Rate limits on heavy code-search workloads; cache via knowledge base.
- Hosted GitHub-Copilot-style MCP variant exists (github.com/github/github-mcp-server, Go binary) — evaluate against the Anthropic TS one for parity. Recommendation: pin to `@modelcontextprotocol/server-github` for reproducibility, revisit when GitHub's official server reaches GA.

---

## 2. memory — `@modelcontextprotocol/server-memory`  [CORE]

### Purpose & Capabilities
Reference MCP implementation of a **persistent knowledge graph**. Stores three primitives:

- **Entities** — typed nodes with a name and an `entityType` plus a list of observation strings.
- **Relations** — directed, named edges between entities (e.g., `agent --uses--> tool`).
- **Observations** — atomic facts attached to entities; addable/removable independently.

Tool surface: `create_entities`, `create_relations`, `add_observations`, `delete_entities`, `delete_observations`, `delete_relations`, `read_graph`, `search_nodes`, `open_nodes`. Backed by a JSON file on disk by default (`MEMORY_FILE_PATH`).

### Why CORE for Claudovka
Roadmap calls it out and Phase 2 ("unified knowledge base") and Phase 5 ("messenger agent", "recommendations stack") effectively *require* a persistent graph. Today Claudovka stores knowledge in flat markdown (`.agent/knowledge/{patterns,issues,decisions}.md`) and per-agent memory dirs. That works for append/grep but does not support:

1. **Typed cross-references** — "issue X was raised in adventure Y by reviewer role Z and resolved by decision W".
2. **Graph queries** — "what skills did role R apply across adventures with variance > 50%?".
3. **Deduplication** — entity-keyed writes prevent the duplicate-entry problem the researcher rule already warns about.

### Integration Plan
- **Phase 2**: Adopt as the canonical store for the unified knowledge base. Define entity schema:
  - Types: `Adventure`, `Task`, `Role`, `Skill`, `Pattern`, `Issue`, `Decision`, `TargetCondition`, `MCP`, `Repo`, `Concept`.
  - Core relations: `task --in--> adventure`, `role --produced--> pattern`, `pattern --addresses--> issue`, `decision --supersedes--> decision`, `task --proves--> targetCondition`.
- **Researcher role**: writes patterns/issues/decisions as entities + observations instead of (or in addition to) markdown. Keep markdown as a human-readable export.
- **Planner role**: queries graph for "similar tasks" before designing — reduces estimation variance.
- **Phase 5 messenger agent**: graph traversal becomes the recommendation engine.
- **Phase 7**: long-horizon learning — observations accumulate across adventures rather than being lost in iteration logs.

### Migration Notes
- Existing markdown KBs can be batch-loaded as observations on synthetic entities to seed the graph.
- The default JSON backing store is fine for single-machine; if multi-host, swap for a community backend (sqlite/neo4j forks exist).

### Risks
- Reference implementation has no auth — keep `MEMORY_FILE_PATH` inside `.agent/` and out of remote MCP exposure.
- Schema discipline matters: without conventions the graph rots into a tag soup. Capture the schema as an `ark` spec under `ark/specs/meta/` so it is enforceable.

---

## 3. firecrawl — `firecrawl-mcp`  [OPTIONAL]

Hosted-or-self-hosted scraping/crawling server (Mendable). Tools: `firecrawl_scrape`, `firecrawl_crawl`, `firecrawl_map`, `firecrawl_search`, `firecrawl_extract` (LLM-structured extraction), `firecrawl_deep_research`. JS-rendered pages, Markdown output, structured-schema extraction.

**Fit**: Phase 3.2 (this very task could have used it), Phase 5 (messenger / inputs ingestion), Phase 7 (futuring — monitor upstream tool docs for changes). Better than ad-hoc WebFetch when crawling multi-page docs.

**Tier rationale**: Not on the hot path, but the only listed option for systematic web ingestion. Add when an adventure first needs >5 page crawl. Requires API key (paid beyond free tier).

---

## 4. supabase — `@supabase/mcp-server-supabase`  [OPTIONAL]

Official Supabase MCP. Tools: project/branch management, `execute_sql`, `apply_migration`, `list_tables`, `get_logs`, `generate_typescript_types`, edge-function deploy, storage ops.

**Fit**: Phase 4 (UI needs a backing store for live updates / collab), Phase 6 (managed deploy path for backend services without owning Postgres ops). Pairs naturally with the Vercel deploy target.

**Tier rationale**: Optional because the Claudovka core is filesystem + git first; a hosted DB is only required when UI realtime or marketplace user accounts come online. When that happens, prefer Supabase over hand-rolled Postgres because its MCP closes the ops loop.

**Risk**: Read-write SQL exposure — gate with `--read-only` flag for reviewer/researcher roles; only allow implementer to execute migrations behind a confirmation step.

---

## 5. sequential-thinking — `@modelcontextprotocol/server-sequential-thinking`  [OPTIONAL]

Reference Anthropic server providing one tool: `sequentialthinking`. Lets the model emit numbered thought steps with `nextThoughtNeeded`, branching, and revision support; the server just records and returns them. No external state, no auth.

**Fit**: Phase 3.1 (planner/reviewer rigor), Phase 7 (self-healing diagnoses). Most useful when a role needs to expose reasoning for downstream agents to critique. Less useful for already-disciplined roles that follow a fixed template.

**Tier rationale**: OPTIONAL because Opus 4.6 already reasons strongly without it; value is the *audit trail*. Adopt selectively for the `planner` and `reviewer` roles where intermediate steps are valuable artifacts. Skip for `implementer`/`researcher` to avoid token tax.

---

## 6. vercel — `https://mcp.vercel.com`  [OPTIONAL]

Hosted MCP run by Vercel. Tools cover project/deployment listing, deployment logs, env-var management, domain operations, log search. OAuth flow.

**Fit**: Phase 4 (UI deploy target — Next.js / Vite), Phase 6 (MCP-only deploy). If the UI lives on Vercel, this is the deploy automation path.

**Tier rationale**: OPTIONAL contingent on UI hosting choice. If the team picks Cloudflare Pages instead, drop this in favor of `cloudflare-workers-builds`. Pick one to avoid double-paying complexity.

---

## 7. railway — `@railway/mcp-server`  [OPTIONAL]

Railway's deployment platform MCP. Tools: project/service/deployment management, env vars, log tail, database provisioning. Good fit for stateful backends (Postgres, workers) that don't fit Cloudflare Workers' constraints.

**Fit**: Phase 6 (backend services for marketplace, team-mcp registry). Complementary to (not competing with) Vercel/Cloudflare which are edge-focused.

**Tier rationale**: OPTIONAL — only needed once Claudovka has long-running backend services. Today everything is local/CLI.

---

## 8. Cloudflare suite  [OPTIONAL — adopt as a unit]

Cloudflare ships a family of hosted MCP servers (mcp.cloudflare.com endpoints, OAuth):

### 8a. cloudflare-docs
Search across Cloudflare's documentation. Pure read-only retrieval. Useful when an agent is configuring Workers/Pages/D1/R2 and needs canonical reference rather than a web search.

### 8b. cloudflare-workers-bindings
Manages Workers bindings: KV namespaces, D1 databases, R2 buckets, Durable Object namespaces, Queues, Hyperdrive, Vectorize indexes. Lets an agent provision the storage substrate a Worker needs without leaving the loop.

### 8c. cloudflare-workers-builds
Build/deploy automation: trigger builds, inspect build logs, manage deployments and versions for Workers projects connected to git.

### 8d. cloudflare-observability
Workers Logpush / Analytics Engine / Tail Workers access — query logs, metrics, and traces for deployed workers and Pages projects.

**Combined fit**: Phase 6 (infra-as-MCP) and Phase 7 (live ops, self-healing). The four together close the loop: provision (bindings) → build (builds) → run (observability) → reference (docs). If Claudovka chooses Cloudflare as the deploy substrate, adopt all four; mixing only some leaves gaps the agent will fall through.

**Tier rationale**: OPTIONAL pending the Phase 6 platform decision. Strong recommendation: pick **either** the Cloudflare suite **or** Vercel + Railway — running both doubles agent permission surface area and increases token spend on tool selection.

**Risk**: Hosted MCP means OAuth tokens leave the local sandbox. Confine to a dedicated agent identity, not the orchestrator.

---

## 9. clickhouse — `https://mcp.clickhouse.cloud/mcp`  [OPTIONAL]

ClickHouse Cloud's hosted MCP. Tools: list databases/tables, run SELECT queries, inspect schema, manage clusters. Read-heavy by design.

**Fit**: Phase 6.2 (benchmark warehouse), Phase 7 (metrics analytics). Today `.agent/metrics.md` and per-adventure `metrics.md` accumulate as flat tables — fine for tens of tasks, painful at thousands. ClickHouse is the right tool for the long-horizon analytics the roadmap implies (variance trends, role-cost histograms, adventure success curves).

**Tier rationale**: OPTIONAL until metrics volume exceeds ~10k rows or an adventure explicitly needs cross-adventure analytics. Until then, jq/duckdb-on-the-fly is sufficient.

**Alternative**: A local DuckDB MCP would cover 80% of the analytics need without the Cloud account. Worth a side investigation under Phase 6.2.

---

## 10. AbletonMCP — `ableton-mcp`  [SKIP]

Community MCP that drives Ableton Live (Max for Live remote-script bridge) — create tracks, add MIDI clips, set tempos, manage devices.

**Fit**: None for the current Claudovka roadmap. Music production is outside the ecosystem's stated scope (developer tooling, agent orchestration, marketplace).

**Tier rationale**: SKIP. Reconsider only if Phase 5's "custom entities" introduces a creative-tools vertical. Document existence; do not integrate.

---

## 11. magic — `@magicuidesign/mcp`  [OPTIONAL]

21st.dev / Magic UI's MCP for AI-driven UI component generation. Returns React + Tailwind component code (Magic UI / shadcn-style primitives) on request. Requires API key.

**Fit**: Phase 4 (UI bootstrap). Could accelerate the initial UI scaffolding adventure (live workflow view, node/graph editor, tabs/panes) by emitting starter components rather than hand-authoring.

**Tier rationale**: OPTIONAL — accelerator for Phase 4 only. Skip for the long-term codebase: generated components need design-system unification anyway. Use it for the *first* spike, then own the components.

**Risk**: Generated code style drift — pick a single design system (Magic UI vs shadcn/ui vs Radix) before turning the agent loose, or the UI becomes a quilt.

---

## Cross-Cutting Observations

### Two truly CORE picks
Only **github** and **memory** rise to CORE. Both are explicitly named in the roadmap and both unlock capabilities the current filesystem-only architecture cannot achieve cheaply: durable cross-session graph state (memory) and centralized git automation with PR-level review surface (github).

### Deploy tier needs a single decision
Vercel, Railway, and the four Cloudflare servers cover overlapping ground. **Phase 6 should make a one-time platform choice** — Cloudflare-only, Vercel + Railway, or Vercel + Supabase — and then adopt the matching MCPs together. Adopting all of them creates a permission/observability mess.

### Reasoning vs storage MCPs
sequential-thinking is a *behavioral* MCP (changes how the model reasons); memory is a *state* MCP (changes what persists). Treat them as orthogonal: state MCPs have permanent integration cost; behavioral MCPs are easy to add/remove per role.

### Hosted vs local
Local (npx) servers — github, memory, sequential-thinking, firecrawl-self-hosted, magic — are sandbox-friendly and reproducible. Hosted (Cloudflare suite, Vercel, ClickHouse Cloud) introduce OAuth, network dependency, and rate limits. Prefer local for the orchestrator, hosted for purpose-bound roles.

### Permissions model implication
Each adopted MCP needs a row in role permission manifests (`.agent/adventures/*/permissions.md`). Consider standardizing capability strings: `mcp.github.repo.read`, `mcp.github.pr.write`, `mcp.memory.write`, `mcp.cloudflare.observability.read`, etc. Raising this in Phase 3.1 role review (TC-009) is recommended.

### Token economy
Every active MCP inflates the tool-list prompt. Roadmap's Phase 2 token-economy goal argues for **per-role MCP enabling** rather than global enabling. The orchestrator gets github + memory; deploy roles get the platform suite; researcher gets memory + firecrawl. Keeps each role's tool list short.

## Recommended Adoption Order

1. **github** (now, Phase 3.2 wrap-up) — unblocks PR-per-adventure workflow.
2. **memory** (Phase 2 start) — required for unified KB; everything downstream benefits.
3. **sequential-thinking** (Phase 3.1) — opt-in for planner/reviewer roles only.
4. **magic** (Phase 4 spike) — one-shot UI scaffolding.
5. **supabase** *or* **vercel** *or* **cloudflare suite** (Phase 4–6) — pick one platform stack.
6. **railway** (Phase 6, only if backend services materialize).
7. **clickhouse** (Phase 6.2, only at metrics scale).
8. **firecrawl** (any phase, on first crawl-heavy task).
9. **AbletonMCP** — do not adopt.

## Open Questions Forwarded to T016 (Integration Matrix)

- Final deploy-platform choice (Vercel/Railway vs Cloudflare suite vs Supabase) — blocks 5 of the 14 servers.
- Whether to adopt official `github/github-mcp-server` (Go) or stay on `@modelcontextprotocol/server-github` (TS).
- Memory-graph schema authority: does the schema live in `ark/specs/meta/` or in a new `.agent/knowledge/schema.md`?
- Permission-string convention (`mcp.<server>.<resource>.<action>`) — needs a Phase 3.1 decision before any MCP rolls out.
