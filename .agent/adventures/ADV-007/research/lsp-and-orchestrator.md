# LSP Plugins & Agent Orchestrator — Research

**Task:** ADV007-T014
**Date:** 2026-04-14
**Scope:** (1) LSP feasibility for Ark DSL pipeline/entity interpretation; (2) ComposioHQ Agent Orchestrator analysis and integration fit with Claudovka's agent runtime subsystem.

---

## 1. LSP for the Ark DSL

### 1.1 LSP architecture in 60 seconds
The Language Server Protocol (Microsoft, JSON-RPC over stdio/socket) decouples *language intelligence* from *editor UX*. A single language server implementation serves VS Code, Neovim, Helix, JetBrains, Zed, Emacs, etc. Standard capabilities relevant to Ark:

| Capability | Ark mapping |
|---|---|
| `textDocument/completion` | item-type keywords (`abstraction`, `class`, `island`, `bridge`, `gateway`, etc.), strategy enums (`tensor`/`code`/`asm_avx2`/`gpu_compute`/`verified`/`script`), `@in`/`#process`/`@out`/`$data` sigils, registry symbol names |
| `textDocument/publishDiagnostics` | parser errors (already produce `ArkParseError` with snippet/caret/expected since `ParserRobustnessTask`); Z3 verify failures; bridge contract type mismatches |
| `textDocument/hover` | description fields, port types, strategy explanations, last verify result |
| `textDocument/definition` | jump from a port reference / bridge contract / registry entry / agent capability skill name to its declaration |
| `textDocument/references` | reverse-impact lookup — same data the `ark impact` command already computes |
| `textDocument/codeAction` | "register in root.ark", "add missing invariant", "convert abstraction → class", quick-fix on a parser caret |
| `textDocument/semanticTokens` | colorize sigils (`@in`, `#process`, `@out`, `$data`) and the three entity tiers distinctly |
| `workspace/symbol` | global index of every island/bridge/agent/skill/cron_task across `specs/**/*.ark` |

### 1.2 Existing DSL-LSP prior art worth studying
- **lark-language-server** and **lsp-from-grammar** patterns: Lark grammars expose the rule tree, and you can derive completion sets directly from the rule expecting position. Ark already has `tools/parser/ark_grammar.lark` plus an `ARK_PARSE_ERROR` containing `expected` tokens — this is a near-drop-in source for completions and diagnostic messages.
- **tree-sitter + LSP combos** (e.g., `tree-sitter-langserver`, Helix's tree-sitter-driven highlighting): tree-sitter gives incremental, error-tolerant parses ideal for editor latency. Ark would benefit from a *separate* tree-sitter grammar for editor highlighting/folding while keeping Lark/pest as ground truth for verification.
- **pygls** (Python) and **tower-lsp** (Rust): the two clean choices for the server. Given Ark already maintains a Python toolchain (`tools/parser`, `tools/verify`, `tools/codegen`) AND a parallel Rust pipeline (`dsl/`, `verify/`, `orchestrator/`), there are two viable paths:
  - **Phase A (fast):** `pygls` server reusing `ark_parser.py`, `ark_verify.py`, `ark_impact.py` directly. Single-file LSP, small surface.
  - **Phase B (canonical):** `tower-lsp` server backed by the Rust crates (`ark-orchestrator`, pest grammar, SMT-LIB writer). Ships as a static binary, matches the long-term Rust migration trajectory.

### 1.3 Pipeline & entity-interpretation hooks (Ark-specific)
Beyond standard LSP capabilities, Ark's pipeline (`parse → verify → codegen → graph`) gives unusual editor superpowers:

1. **Inline verify lens** — render Z3 PASS/FAIL/UNKNOWN as `CodeLens` above each `verify {}` block; on failure, expand the counterexample inline (the BMC trace from `TemporalBMCTask`).
2. **Impact preview on hover** — `ark impact <Entity>` already enumerates downstream nodes; surface a "12 dependents — 3 islands, 2 bridges" badge above any `class`/`abstraction` declaration.
3. **Diff peek** — `ark diff` (from `ArkDiffTask`) already does structural AST diff; LSP can show "since last save: +1 #process, contract changed on bridge X" without invoking the CLI.
4. **Codegen preview** — virtual `ark://generated/{file}.rs` document URIs that re-render whenever the source `.ark` file is saved. Lets users see SoA batch output side-by-side.
5. **Bridge contract jump** — go-to-definition from a bridge port name should also offer "go to the *other* island that consumes this port" — not standard LSP semantics, but trivially exposed via `references`.
6. **File-watcher integration** — `FileWatcherTask` already has the polling watcher. Reuse its dirty-set logic so the LSP and the standalone `ark watch` don't double-run verify.

### 1.4 Effort estimate

| Milestone | Effort | Notes |
|---|---|---|
| M1: pygls skeleton, document sync, syntax diagnostics from existing `ArkParseError` | ~1 day | Wire `ark_parser.parse_text()` into `did_change` debounced 300 ms |
| M2: completion (keywords + symbol table), hover (descriptions), workspace symbol | ~2 days | Build a symbol cache keyed on file mtime |
| M3: definition / references using `ark_impact` graph | ~2 days | Reuse impact analyzer's adjacency lists |
| M4: verify diagnostics (Z3 errors as `DiagnosticSeverity.Error` with related-info from BMC trace) | ~2 days | Run verify in a background queue per file; cancellation token |
| M5: code actions (register-in-root, add invariant, convert tier) | ~2 days | Mostly text edits over AST ranges |
| M6: VS Code extension scaffold + Neovim/Helix configs | ~1 day | TypeScript `vscode-languageclient` thin wrapper |
| **Total Phase A (Python pygls)** | **~10 dev-days** | Ships usable LSP for VS Code/Neovim/Helix |
| Phase B port to `tower-lsp` Rust | ~10–15 dev-days | Wait until Rust verify reaches feature parity (currently SMT-LIB text only, no z3-sys binding) |

**Recommendation:** Phase A is high-ROI now — every capability is already implemented in Python; the LSP is mostly a JSON-RPC veneer. Defer Phase B until the Rust pipeline closes the verify gap.

### 1.5 Risks
- Z3 verification can be slow on large specs; LSP must run it off the request thread and support cancellation. Use the same dispatcher logic as `OrchestratorRsTask`.
- Lark and pest grammars must stay in sync; the LSP should pin to one (Lark for Phase A) to avoid divergent error messages.
- The `import` resolver (`ImportResolutionTask`) needs deterministic search paths so the LSP can resolve cross-file references identically to the CLI.

---

## 2. Agent Orchestrator (ComposioHQ)

### 2.1 What it is
`@aoagents/ao` (npm). Spawns parallel AI coding agents — each in its own git worktree, branch, and PR. Reactions engine routes CI failures and review comments back to the spawning agent. One dashboard at `localhost:3000` supervises a fleet. MIT, Node 20+, requires `tmux` and `gh`.

### 2.2 Architecture highlights

**Monorepo, four packages:** `core` (types, services, config), `cli` (`ao` command), `web` (Next.js dashboard), `plugins` (21 packages across 8 slots).

**Eight plugin slots (only one is non-pluggable — Lifecycle):**

| Slot | Default | Alternatives |
|---|---|---|
| Runtime | tmux | process, docker, k8s, ssh, e2b |
| Agent | claude-code | codex, aider, opencode, cursor |
| Workspace | worktree | clone |
| Tracker | github | linear, gitlab |
| SCM | github | gitlab |
| Notifier | desktop | slack, discord, webhook, composio, openclaw |
| Terminal | iterm2 | web |
| Lifecycle | (core) | — non-pluggable |

Each plugin implements a TypeScript interface from `packages/core/src/types.ts` and exports a `PluginModule`.

**Key services (`packages/core/src/`):**
- `session-manager.ts` — spawn / list / kill / send / restore
- `lifecycle-manager.ts` — state machine, polling loop, **reactions engine**
- `prompt-builder.ts` — 3-layer prompt assembly (base + config + rules)
- `plugin-registry.ts` — discovery, loading, resolution
- `agent-selection.ts` — orchestrator vs worker role resolution
- `paths.ts` — SHA-256 hash-based namespacing so multiple AO checkouts coexist
- `observability.ts` — correlation IDs, structured logging, metrics

**Session lifecycle (state machine):**
```
spawning → working → pr_open → ci_failed
                            → review_pending → changes_requested
                            → approved → mergeable → merged
                                                   ↓
                            cleanup → done (or killed/terminated)
```
Orthogonal *activity states*: `active`, `ready`, `idle`, `waiting_input`, `blocked`, `exited`.

**Reactions engine (the killer feature):**
```yaml
reactions:
  ci-failed:           { auto: true,  action: send-to-agent, retries: 2 }
  changes-requested:   { auto: true,  action: send-to-agent, escalateAfter: 30m }
  approved-and-green:  { auto: false, action: notify }
```
Declarative event → action mapping. CI failure logs are auto-piped back into the spawning agent. Review comments become next-turn input. Human is paged only on policy-defined escalations.

**Hash-based namespacing:** `sha256(dirname(configPath))[:12]` becomes the prefix for runtime data dir (`~/.agent-orchestrator/{hash}-{projectId}`), tmux session names (`{hash}-{prefix}-{num}`), and instance IDs. Lets multiple AO installs coexist on one machine.

### 2.3 Comparison with Claudovka's agent system

| Dimension | Claudovka (`agent_system.ark`) | Agent Orchestrator |
|---|---|---|
| **Definition surface** | Declarative `.ark` DSL — 8 item types (platform, gateway, execution_backend, model_config, skill, learning_config, cron_task, agent) parsed → JSON AST → codegen | Imperative TypeScript plugins + YAML config; no DSL |
| **Execution backend** | `execution_backend` items (`local`, `docker`) with `cpu/memory/timeout` limits | `Runtime` plugin slot (tmux/process/docker/k8s/ssh/e2b) |
| **Multi-platform messaging** | First-class: `platform_def` (terminal, telegram) + `gateway_def` with route table | Out of scope; dashboard is the UI |
| **Skills / capabilities** | `skill_def` with trigger regex, ordered steps, improvement strategy, threshold | None — agent prompts are 3-layer assembled (base + config + rules) per session |
| **Learning** | `learning_config_def` (`skill_generation`, `memory_persist`, `session_search`, `self_improve`) | Not modeled — orthogonal |
| **Scheduling** | `cron_task_def` with crontab schedule + delivery target | None — assumed external |
| **Parallel work isolation** | Not modeled (single-agent runtime) | **Core competency** — git worktree per agent, hash-namespaced sessions |
| **Feedback routing** | Implicit via gateway routes | **Explicit reactions engine** with retries / escalation timers |
| **PR / CI integration** | None | Built-in (`tracker-github`, `tracker-linear`, `scm-github`, `gh` CLI) |
| **Verification** | Z3 invariants on agent specs | None |

**The two systems are largely complementary, not competitive.** Claudovka models *what an agent is and which platforms it speaks*; AO models *how dozens of disposable coding agents are orchestrated against a real git repo*.

### 2.4 Integration fit & best features to adopt

**Worth adopting into Claudovka's agent runtime:**

1. **Reactions engine as a first-class `.ark` item.** Add a `reaction_def` item type alongside `cron_task_def`:
   ```ark
   reaction ci_failed_reaction {
       trigger: "ci.failed"
       action: send_to_agent
       agent: autonomous_agent
       retries: 2
       escalate_after: "30m"
       escalate_to: telegram
   }
   ```
   This generalizes today's `cron_task_def` from "time-triggered" to "event-triggered" and gives the agent runtime declarative feedback loops. Z3 can verify reaction graphs are acyclic / cannot infinite-loop.

2. **Worktree-per-agent isolation.** When the orchestrator (`OrchestratorRsTask`, `ClaudeTaskBridgeTask`) dispatches work to a Claude Code session, spawn it in a git worktree of `specs/`. Prevents two parallel spec edits from racing on `root.ark`. Reuse the SHA-256 hash-namespacing trick verbatim.

3. **State-machine session lifecycle.** Today `dispatch` planner is fire-and-forget. Adopt AO's `spawning → working → pr_open → ci_failed → ...` lifecycle for spec-edit sessions, with `verify_failed` as the Ark-specific analog of `ci_failed`. Add a verify-failed reaction that auto-feeds the Z3 counterexample back into the agent.

4. **Plugin slot pattern for backends.** AO's eight-slot plugin registry is cleaner than Ark's current hard-coded `local_backend`/`docker_backend`. Promote `execution_backend` to a true plugin interface (Rust trait); the existing two become the first two implementations. Adds k8s/ssh/e2b/process for free conceptually.

5. **3-layer prompt assembly.** AO's `prompt-builder.ts` separates base prompt + per-config customization + per-session rules. Mirror this in `model_config_def` so personas can be composed (`base_persona + skill_overrides + per_task_rules`) instead of monolithic strings.

6. **Hash-based path/session namespacing.** Drop into `tools/orchestrator` and the Rust `orchestrator/` crate so simultaneous `ark watch` + `ark dispatch` invocations on the same repo from different worktrees never collide on cache files or generated output dirs.

7. **Observability scaffolding.** Correlation IDs, structured logs, metrics on every cross-process boundary — light touch but pays off the moment you have >1 agent running. Wire into existing `metrics.md` writer.

**What NOT to adopt:**
- AO's GitHub-PR-centric vocabulary (review comments, PR approval). Ark agents edit specs locally; PRs are handled at a higher layer if at all.
- `tmux` runtime as default. Ark already has Rust orchestration (`OrchestratorRsTask`); a tmux dependency on Linux/macOS only would regress the Windows dev path.
- Next.js dashboard. Ark visualization lives in `tools/visualizer/` (HTML graph with LOD); adding a Node dashboard would fork the UI story.

### 2.5 Concrete integration sketch (Phase 4 / Runtime backlog candidate)

```
1. Spec change: extend dsl/grammar/ark.pest + tools/parser/ark_grammar.lark
   with `reaction` item type. Add to ark_codegen.py for Rust emit.
2. Rust: add ReactionPlugin trait in orchestrator/, default impl reads
   reactions from parsed .ark, spawns handlers on event bus.
3. Rust: refactor execution_backend codegen output to implement a
   Backend trait; move `local`/`docker` behind that trait.
4. Add WorktreeManager (sha256 hash naming) under orchestrator/.
   `ark dispatch <task>` allocates a worktree per task automatically.
5. Add VerifyFailedReaction wiring: when `ark watch` re-verify fails,
   emit `verify.failed` event; reactions engine routes to agent if
   one is bound.
6. Defer: dashboard, GitHub integration, multi-agent fleet UI.
   Ark's value-add is verified specs, not PR throughput.
```

Estimated: ~2–3 weeks of work spread across DSL, parser, codegen, and orchestrator crates. Maps cleanly onto existing backlog tier "Приоритет 4 — Runtime прототип".

---

## 3. Summary

- **LSP for Ark is high-ROI and low-risk**: ~10 dev-days using `pygls` over the existing Python toolchain delivers completion, diagnostics (already structured), hover, go-to-definition, references via `ark impact`, codegen preview, and inline verify lens. Tree-sitter grammar is a complementary editor-side investment. Defer a `tower-lsp` Rust port until Rust verify reaches feature parity.
- **Agent Orchestrator is mostly orthogonal to Claudovka's agent DSL**, but its three crown jewels — the **reactions engine**, **worktree-per-agent isolation with hash namespacing**, and the **plugin-slot architecture** — would each meaningfully improve Ark's runtime story. Recommend adopting them as native `.ark` concepts (`reaction_def`, plugin-trait backends) rather than pulling in the Node toolchain. Skip the GitHub/dashboard/tmux pieces.
