# Phase 3.2 Research — QMD and CodeGraphContext

**Task:** ADV007-T012
**Date:** 2026-04-14
**Sources:** README.md of `tobi/qmd` and `CodeGraphContext/CodeGraphContext` (fetched live).

---

## 1. QMD — Query Markup Documents

### Purpose and core concept
QMD is an **on-device hybrid search engine** for Markdown corpora (notes, meeting transcripts, documentation). It is positioned as the long-term memory layer for "agentic flows" — agents call it to retrieve grounded snippets instead of stuffing context. Everything runs locally; no cloud round-trip.

### Key features and capabilities
- **Three search modes** layered into one pipeline:
  1. **BM25 / FTS5** keyword search (SQLite FTS5).
  2. **Vector** semantic search (cosine over embeddings).
  3. **LLM re-ranking** (qwen3-reranker, yes/no with logprob confidence).
- **Reciprocal Rank Fusion (RRF)** with a position-aware blend (top 1-3 trusts retrieval 75 %, top 11+ trusts reranker 60 %) — explicit, tuned, documented.
- **Query expansion** through a fine-tuned 1.7 B model (`qmd-query-expansion-1.7B`) that produces 2 alternate queries.
- **Collections + Context tree**: each collection (a glob over a folder) carries a human-written "context" string that is returned with every hit. This is QMD's distinguishing trick — agents get *why this folder matters* as part of every result.
- **Indexer** with auto chunking (`auto` = AST for code files, `regex` for prose).
- **MCP server** (stdio or HTTP daemon) exposing 4 tools: `query`, `get`, `multi_get`, `status`.
- **TypeScript SDK** (`@tobilu/qmd`) — embeddable as a library, no CLI required.
- **Claude Code plugin** marketplace entry (`tobi/qmd`) for one-line install.

### Technology stack
- Node.js >= 22 / Bun >= 1.0.
- SQLite + FTS5 (storage + lexical index).
- `node-llama-cpp` running GGUF models locally:
  - `embeddinggemma-300M-Q8_0` (~300 MB) for embeddings.
  - `qwen3-reranker-0.6b-q8_0` (~640 MB) for reranking.
  - `qmd-query-expansion-1.7B-q4_k_m` (~1.1 GB) for expansion.
- Models cached in `~/.cache/qmd/models/`. Auto-downloaded on first use.
- HTTP transport: `POST /mcp` (Streamable HTTP, stateless) + `GET /health`.

### Integration fit with Ark / Claudovka
Concrete hooks:
- **`.agent/knowledge/`, `.agent/designs/`, `.agent/adventures/**/research/`, `docs/sessions/`** — the four obvious collections. Add them with `qmd collection add` and attach context strings (e.g. *"Adventure designs — proposed implementations awaiting review"*).
- **MCP**: register QMD's HTTP server in `.claude/settings.json` (or per-adventure permissions). The pipeline agents (planner, designer, reviewer, researcher) gain a `query` / `get` tool — they retrieve prior decisions *without a Read+Glob roundtrip*.
- **Pipeline data flow**: when the **planner** receives a new task, it calls `qmd query "<task title>"` against `knowledge/` and `designs/` collections to surface prior patterns/issues/decisions before producing a plan. This collapses the "look up similar past work" step from O(N) Reads to one MCP call.
- **Shared model**: QMD speaks plain Markdown — there is **no schema impedance** with `.agent/knowledge/{patterns,issues,decisions}.md` or with adventure manifests/designs. Zero data migration.

### Profits / advantages
- **Dramatic context savings.** Hybrid retrieval over the knowledge base means agents stop re-Reading large markdown files. Researcher agent benefits most: today it Reads the full design + report; tomorrow it pulls a 200-token snippet.
- **Re-ranking quality.** The position-aware RRF + LLM rerank is genuinely better than naive embedding search — measured by their own published curve, but also a known-good architecture.
- **Local, deterministic, offline.** No API keys, no rate limits, no leak surface for Ark internals.
- **Tree-of-context** is unique. Maps cleanly onto Ark's adventure/phase/task hierarchy — each folder gets a description that grounds the LLM.
- **Drop-in**: ships an MCP server and a Claude Code plugin. Install cost is one `claude plugin install`.
- **Embeddable SDK** — the orchestrator (Rust or Python) could call the TS SDK via a thin FFI/HTTP shim if pure-MCP is too coarse.

### Damages / costs / risks
- **~2 GB of GGUF model downloads** on first use; ~2 GB of VRAM / RAM resident when daemonized. Heavy for a CI box, fine for a workstation.
- **Node 22 + Bun runtime** is a new dependency for a project that is otherwise Python + Rust. Adds a maintenance surface.
- **Markdown only.** Source code (`.ark`, `.py`, `.rs`) is *not* a first-class citizen — the `auto` chunker handles code files, but QMD's value prop is prose retrieval, not call-graph traversal.
- **Index drift.** Without `qmd embed` re-runs, vector results go stale. Need a file watcher or a pre-commit hook.
- **Single-author project** (tobi). Bus-factor 1, but the code is small and MIT/permissive enough to fork.
- **No write API for agents** — QMD is read-only retrieval. The pipeline still writes through normal file tools.

### Recommended integration pattern
**Adopt for the knowledge layer; do not use for code.**

1. Phase 3 — install via `claude plugin install qmd@qmd`, register an HTTP daemon on port 8181 in `.claude/settings.json`.
2. Define four collections with context strings:
   - `knowledge` ← `.agent/knowledge/**/*.md`, ctx: *"Cross-adventure patterns, issues, decisions"*
   - `designs` ← `.agent/adventures/**/designs/*.md`, ctx: *"Proposed designs, one per task"*
   - `research` ← `.agent/adventures/**/research/*.md`, ctx: *"External research findings"*
   - `sessions` ← `docs/sessions/*.md`, ctx: *"Daily session summaries"*
3. Add a post-task hook: when the **researcher** agent finishes, run `qmd embed --collection knowledge` to keep the index hot.
4. Update planner/designer/reviewer prompts to *prefer* `qmd query` over Read+Glob for prior-work lookup.
5. Estimate: ~2 days to integrate, recovers itself in token cost within ~10 adventures.

---

## 2. CodeGraphContext (CGC)

### Purpose and core concept
CGC turns a code repository into a **queryable graph** stored in a graph DB (KùzuDB / FalkorDB Lite / Neo4j). Tree-sitter parses 14 languages into nodes (functions, classes, methods, parameters) and edges (calls, inheritance, imports). The graph is then exposed both as a CLI (`cgc analyze ...`) and as an MCP server so AI assistants can ask *"who calls X?"* in natural language.

### Key features and capabilities
- **Indexer**: tree-sitter based; 14 languages (Python, JS, TS, Java, C/C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, Dart, Perl). Extracts functions, classes, methods, parameters, inheritance, calls, imports.
- **Graph backends**: KùzuDB (default on Windows, embedded), FalkorDB Lite (embedded on Unix when Python ≥ 3.12), Neo4j (server, all platforms).
- **Live watch** (`cgc watch .`) — re-indexes on file change.
- **Pre-indexed `.cgc` bundles** for famous repos (skip indexing).
- **Analysis primitives**: callers, callees, call chains (multi-hop), class hierarchies, dead-code detection, cyclomatic complexity, dependency tracing.
- **Interactive HTML visualizer** (`--viz`) with force-directed / hierarchical layouts.
- **Dual mode**: standalone CLI **or** MCP server. `cgc mcp setup` auto-configures VS Code, Cursor, Claude, Gemini CLI, Cline, RooCode, Kiro, etc.
- **`.cgcignore`** (gitignore syntax) for scope control.

### Technology stack
- Python 3.10–3.14, distributed via PyPI (`pip install codegraphcontext`).
- `tree-sitter` + `tree-sitter-language-pack`.
- `neo4j>=5.15.0`, `watchdog`, `typer`, `rich`, `inquirerpy`.
- Optional `kuzu` or `falkordblite` for embedded graph DB.

### Can Ark's node-graph pipeline be combined or paired with CGC?

**Yes — and the alignment is unusually tight.** Ark already has `ark/specs/infra/code_graph.ark` declaring exactly this subsystem:

```ark
class GraphStore        // backend: in_memory  → could be KùzuDB
class CodeIndexer       // languages: python, rust, ark
class QueryEngine
class Watcher           // event_count tracking
island CodeGraphIsland
```

So the question is **not** *should we build a code graph?* — Ark already plans to. The question is *do we implement that island ourselves, or wrap CGC?*

#### Concrete hooks / data flow

| Ark concept | CGC binding |
|---|---|
| `class CodeIndexer` (`languages: python, rust, ark`) | Wrap `cgc index <path>`. CGC handles Python and Rust out of the box; `.ark` would need a tree-sitter grammar (Ark already maintains `dsl/grammar/ark.pest` and `tools/parser/ark_grammar.lark` — porting to tree-sitter is mechanical). |
| `class GraphStore` (`backend: in_memory`) | Replace `in_memory` with `kuzudb` (or `neo4j` in workspace mode). Keep abstraction; swap implementation. |
| `class QueryEngine` (`last_query`) | Forward to CGC's MCP `find_callers`, `find_callees`, `analyze_complexity`, `find_dead_code` tools. |
| `class Watcher` | Replace bespoke polling watcher with `cgc watch .` subprocess; pipe events back into the orchestrator's re-verify trigger. |
| `bridge CodeGraph_to_Orchestrator` | CGC's MCP server is the bridge transport. The orchestrator subscribes via the MCP client. |

#### Pairing patterns

**A. Read-through wrapper (lowest risk).** Implement Ark's `CodeGraphIsland` as a thin façade over CGC. Generated Rust calls into CGC's CLI/MCP. Ark keeps its declarative spec; CGC keeps the actual graph store.

**B. Federated graph (higher upside).** Run two graphs in parallel:
- *CGC graph* — physical code (Python/Rust files, tree-sitter AST).
- *Ark self-graph* (`ark_self_graph.ark` already exists) — declarative spec graph (islands, bridges, abstractions).
  Add a bridge node type that links a CGC `Function` node to the Ark `class.process` it implements (via a generated `// ark:gen <hash>` comment that codegen emits and CGC indexes). Result: agents can ask *"which Ark spec generated this Rust function?"* and *"which generated functions did this spec change touch?"*.

**C. Replace `ark impact` with graph queries.** Today `ark impact` walks the AST manually. With CGC indexing the *generated* Rust output, impact analysis becomes a Cypher/Kùzu query (`MATCH (changed)-[:CALLS*]->(downstream)`).

### Profits / advantages
- **Free implementation of a planned Ark subsystem.** Saves 2–4 weeks of Watcher + indexer + query engine work that's currently in the backlog (P3/P4).
- **14-language parsing** out of the box vs Ark's current 3 (python, rust, ark).
- **Known-good graph backends.** KùzuDB embedded means zero infra burden on dev machines.
- **MCP-first.** Pipeline agents (reviewer especially) gain *"who else calls this?"* as a one-line tool call, instead of grep-and-hope.
- **Generated-code awareness.** If codegen embeds traceability comments, CGC indexes them and reviewer can verify a change touched only the intended generated artifacts.
- **Visualization for free** (`--viz`) — Ark already invests in `tools/visualizer/`; CGC's HTML output can complement (it's call-graph oriented; Ark's is island/bridge oriented).
- **Active project**, multi-language docs, MIT-style permissive.

### Damages / costs / risks
- **Python-only runtime** — Ark is migrating to Rust. CGC pulls in Python ≥ 3.10, neo4j-driver, tree-sitter-language-pack, typer, rich. That's ~30–50 MB of deps and a Python interpreter on the critical path.
- **`.ark` is unsupported.** A tree-sitter grammar must be written. Until then, CGC indexes the *generated* Rust/Python only — the spec graph stays in Ark's hands. Acceptable, but limits Pattern B above.
- **Two graph stores** to keep coherent (CGC's KùzuDB + any Ark in-memory store) unless we fully delegate.
- **Maintainer concentration** — single primary author (Shashank Shekhar Singh), v0.4.2 (pre-1.0). Track upstream carefully; pin versions.
- **Neo4j path** (if chosen) means Docker / a long-lived server. Avoid for dev; use only for shared/team graphs.
- **Live watch can thrash** on large monorepos; need `.cgcignore` discipline.
- **Schema lock-in.** CGC's node/edge labels are fixed (`Function`, `Class`, `CALLS`, `INHERITS`). Custom Ark concepts (`Island`, `Bridge`, `Process`) must be modelled as auxiliary node properties or via external join keys.

### Recommended integration pattern
**Pair, don't merge. Adopt CGC as the implementation behind `code_graph.ark` for non-`.ark` languages; keep Ark's declarative spec graph separate.**

1. **Phase 3.x — Wrap.** Generate `class GraphStore { backend: "kuzudb" }` codegen that shells out to CGC. Replace the stub `Watcher` with `cgc watch`.
2. **Phase 4 — MCP wire-up.** Run `cgc mcp setup` for Claude. Add `cgc.find_callers`, `cgc.analyze_complexity` to the reviewer's allowed tool list — reviewer becomes much sharper at impact assessment.
3. **Phase 5 — Bridge to spec graph.** Emit `// ark:gen <spec_path>:<entity>` comments from `ark_codegen.py`. Write a small post-index hook that joins CGC's `Function` nodes to Ark's `class` entities by parsing those comments. This realizes Pattern B without writing a tree-sitter grammar for `.ark`.
4. **Phase 6 — Optional: tree-sitter `.ark`.** Only worthwhile if we want CGC to index the spec files directly. Defer until spec corpus is large enough to justify.
5. **Backend choice:** KùzuDB on Windows (matches Ark dev environment), Neo4j only if the team grows and a shared graph is needed.

**Estimate:** ~3 days for Pattern A wrapper + MCP wiring; ~1 week extra for Pattern B bridge.

---

## 3. Combined verdict

| | QMD | CGC |
|---|---|---|
| Layer | Knowledge / prose / `.md` | Code structure / call graph |
| Storage | SQLite + FTS5 + GGUF | KùzuDB / FalkorDB / Neo4j |
| Interface to agents | MCP (stdio or HTTP) | MCP (stdio) + CLI |
| Overlap with each other | None — orthogonal | None — orthogonal |
| Overlap with Ark | None today | Implements `code_graph.ark` |
| Recommendation | **Adopt** | **Adopt as wrapper** |
| Phase | 3 (knowledge layer) | 3.x → 4 (graph + reviewer) |

The two tools are complementary: QMD answers *"what did we decide / discover?"* against the knowledge base, CGC answers *"what calls what?"* against the code. Together they cover both halves of the agent context problem with zero overlap and a small, well-defined dependency footprint.

**Headline action:** install QMD as a knowledge MCP this phase, fold CGC into the existing `code_graph.ark` plan as the concrete backend.

---

## 4. Target Conditions touched
- **TC-010** — both tools researched with capability summaries (this document).
- Feeds into TC-011 (integration matrix) and TC-012 (MCP catalog) handled by sibling tasks.
