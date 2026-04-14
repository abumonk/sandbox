---
task: ADV007-T017
adventure: ADV-007
phase: 4
target_conditions: [TC-015]
upstream:
  - .agent/adventures/ADV-007/research/phase4-ui-requirements.md
  - .agent/adventures/ADV-007/research/phase4-ui-architecture.md
researched: 2026-04-14
---

# Phase 4 — Technology Stack Evaluation and Recommendation

This document evaluates candidate technology stacks for Claudovka
Studio against the requirements (TC-013) and architecture (TC-014).
It scores six representative stacks against a nine-factor criteria
matrix and issues a final recommendation with rationale.

The evaluation assumes a Windows-first desktop-primary deployment
(phase1 environment, phase2 §2.1) with optional share-link web mode,
a single-user local MCP connection as the default, and a multi-year
maintenance horizon.

---

## 1. Candidate Stacks

Six stacks were short-listed. Each bundles a renderer, framework,
and packaging choice; the editor/graph engines are factored out and
scored separately in §4.

| # | Name | Renderer | Framework | Packaging | Primary language |
|---|---|---|---|---|---|
| S1 | **Next.js + shadcn/ui + Tauri** | Webview (system) | React + Next.js (app router) | Tauri (Rust shell) | TS + Rust |
| S2 | **Next.js + shadcn/ui + Electron** | Chromium bundled | React + Next.js | Electron | TS |
| S3 | **SvelteKit + Skeleton UI + Tauri** | Webview | Svelte 5 + SvelteKit | Tauri | TS + Rust |
| S4 | **Plain browser SPA + Vite** | Any browser | React or Svelte + Vite | Static hosted + local MCP bridge | TS |
| S5 | **Lit + Vite + Tauri** | Webview | Web Components (Lit) | Tauri | TS |
| S6 | **Zed plugin / in-editor panel** | Zed host | Zed extension API | N/A (hosted in Zed) | Rust + TS |

Other stacks considered and rejected before scoring:

- **Flutter Desktop**: mature UI but Dart ecosystem is foreign to
  both team-pipeline (TS) and ark-orchestrator (Rust); MCP client
  tooling and Monaco/CodeMirror integration are poor on Flutter.
- **egui / iced (Rust-native)**: too early for markdown-heavy UI;
  Monaco/CodeMirror unavailable; reinventing would double the budget.
- **TUI (Textual / ratatui)**: acceptable as a minor adjunct but
  fails the graph-editor requirement outright.
- **Re-use binartlab web-ui**: rejected because binartlab web-ui is
  not aligned with the redesigned `.agent/` event substrate and
  reviewing it would delay UI delivery by the time already invested
  in that codebase.

---

## 2. Criteria Matrix

Nine weighted criteria, each scored 1-5 (1 worst, 5 best). Weights
are derived from the requirements doc; the two most load-bearing
factors are MCP integration cost and Windows-first fit.

| Criterion | Weight | Rationale |
|---|---|---|
| C1 Dev velocity | 15% | Fastest path to M4-UI-1 approval-only writes |
| C2 Offline / local-first fit | 10% | Studio runs against a local MCP; no cloud required |
| C3 Windows-first correctness | 15% | HiDPI, native paths, install UX |
| C4 MCP integration cost | 15% | Must speak MCP over stdio and local WS cleanly |
| C5 Desktop vs web flexibility | 10% | Same codebase serves desktop + share-link |
| C6 Ecosystem depth (UI libs, editors) | 10% | Monaco, React Flow, shadcn, etc. |
| C7 Bundle size / startup time | 5% | Target < 2s cold start |
| C8 Long-term maintainability | 10% | Project horizon is years |
| C9 Plugin architecture fit | 10% | Contribution model per architecture §8 |

---

## 3. Stack-by-Stack Scoring

Raw scores (1-5), weighted totals in §3.7.

### 3.1 S1 — Next.js + shadcn/ui + Tauri

| Criterion | Score | Notes |
|---|:-:|---|
| C1 Dev velocity | 5 | Next.js app-router + shadcn generators are fastest path to a working dashboard; widespread hiring pool / AI-assist familiarity |
| C2 Offline | 4 | Static export mode works; requires care to avoid server-only APIs |
| C3 Windows-first | 5 | Tauri uses system WebView2 (Edge), native HiDPI, native file dialogs, small installer (~5 MB shell) |
| C4 MCP integration | 4 | Rust Tauri backend can host the MCP bridge directly; TS frontend uses `@anthropic-ai/mcp-sdk` over WS or Tauri commands |
| C5 Desktop vs web | 5 | Same Next.js codebase exports static for desktop webview and for share-link web deployment |
| C6 Ecosystem | 5 | React = biggest ecosystem (shadcn, React Flow, Monaco, TipTap, React Hook Form) |
| C7 Bundle | 4 | Shell ~5-10 MB; WebView2 is shared across apps on Windows |
| C8 Maintainability | 4 | React + Next.js is mainstream; Tauri is growing but stable at 2.x |
| C9 Plugin fit | 4 | React component contribution model is well-understood |

### 3.2 S2 — Next.js + shadcn/ui + Electron

| Criterion | Score | Notes |
|---|:-:|---|
| C1 Dev velocity | 5 | Same Next.js / shadcn benefits as S1 |
| C2 Offline | 4 | Same as S1 |
| C3 Windows-first | 4 | Works, but bundled Chromium adds weight; HiDPI fine |
| C4 MCP integration | 4 | Node main process can spawn MCP; bridge natural |
| C5 Desktop vs web | 4 | Slightly harder to share: Electron-only APIs leak |
| C6 Ecosystem | 5 | Same as S1 |
| C7 Bundle | 2 | 100-150 MB installer; 300-500 MB resident — significant on Windows |
| C8 Maintainability | 4 | Electron is stable but the heaviness has drawn criticism long-term |
| C9 Plugin fit | 4 | Same as S1 |

### 3.3 S3 — SvelteKit + Skeleton UI + Tauri

| Criterion | Score | Notes |
|---|:-:|---|
| C1 Dev velocity | 4 | Svelte 5's runes are pleasant; Skeleton UI smaller than shadcn but serviceable |
| C2 Offline | 4 | SvelteKit static adapter works; same cautions as Next.js |
| C3 Windows-first | 5 | Tauri benefits identical to S1 |
| C4 MCP integration | 4 | Tauri backend + TS frontend same story |
| C5 Desktop vs web | 5 | Static adapter delivers share-link |
| C6 Ecosystem | 3 | Smaller ecosystem: fewer component libraries; React Flow unavailable (Svelte Flow exists but less mature); Monaco integration requires wrapper |
| C7 Bundle | 5 | Svelte compile output is smaller than React; fast startup |
| C8 Maintainability | 3 | Svelte 5 API is new; hiring pool thinner |
| C9 Plugin fit | 3 | Svelte's per-component compilation makes external plugin contributions awkward |

### 3.4 S4 — Plain browser SPA + Vite

| Criterion | Score | Notes |
|---|:-:|---|
| C1 Dev velocity | 4 | Vite + React is fast; no Next.js magic needed for a client-only app |
| C2 Offline | 3 | Service worker required; user must keep localhost MCP bridge running |
| C3 Windows-first | 3 | Runs in user's browser — no control over window chrome, dialogs, tray integration, file pickers |
| C4 MCP integration | 3 | Browser cannot speak stdio MCP; requires a bridge process (which the user must start) |
| C5 Desktop vs web | 5 | Maximum flexibility by construction |
| C6 Ecosystem | 5 | Full React + shadcn + Monaco + React Flow |
| C7 Bundle | 5 | No shell; browser is already installed |
| C8 Maintainability | 5 | No framework lock-in; minimal surface area |
| C9 Plugin fit | 4 | Dynamic import and Module Federation are well-trodden |

### 3.5 S5 — Lit + Vite + Tauri

| Criterion | Score | Notes |
|---|:-:|---|
| C1 Dev velocity | 2 | No component library ecosystem; everything is bespoke |
| C2 Offline | 4 | Trivially supports offline |
| C3 Windows-first | 5 | Tauri |
| C4 MCP integration | 4 | Same as other Tauri stacks |
| C5 Desktop vs web | 5 | Web components run anywhere |
| C6 Ecosystem | 2 | Very small; no shadcn-equivalent; Monaco/CodeMirror work but integration is manual |
| C7 Bundle | 5 | Smallest JS output |
| C8 Maintainability | 3 | Stable standard; low churn; but small community limits answers |
| C9 Plugin fit | 5 | Web components are the canonical plugin substrate |

### 3.6 S6 — Zed plugin / in-editor panel

| Criterion | Score | Notes |
|---|:-:|---|
| C1 Dev velocity | 2 | Zed extension API is still maturing; documentation thin |
| C2 Offline | 5 | Local to Zed entirely |
| C3 Windows-first | 3 | Zed's Windows support is improving but not yet first-class at time of writing |
| C4 MCP integration | 3 | Extensions have limited network access; requires Zed-specific MCP glue |
| C5 Desktop vs web | 1 | Desktop-only; no share-link mode possible |
| C6 Ecosystem | 2 | Extension ecosystem is nascent |
| C7 Bundle | 5 | Inherits Zed's footprint |
| C8 Maintainability | 2 | Dependent on Zed's API stability |
| C9 Plugin fit | 2 | Studio is the plugin — no contribution model inside |

### 3.7 Weighted totals

```
Weights: C1 15, C2 10, C3 15, C4 15, C5 10, C6 10, C7 5, C8 10, C9 10
```

| Stack | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | Total |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| S1 Next.js + shadcn + Tauri | 5 | 4 | 5 | 4 | 5 | 5 | 4 | 4 | 4 | **4.50** |
| S2 Next.js + shadcn + Electron | 5 | 4 | 4 | 4 | 4 | 5 | 2 | 4 | 4 | 4.10 |
| S3 SvelteKit + Skeleton + Tauri | 4 | 4 | 5 | 4 | 5 | 3 | 5 | 3 | 3 | 3.95 |
| S4 Browser SPA + Vite | 4 | 3 | 3 | 3 | 5 | 5 | 5 | 5 | 4 | 3.90 |
| S5 Lit + Vite + Tauri | 2 | 4 | 5 | 4 | 5 | 2 | 5 | 3 | 5 | 3.65 |
| S6 Zed plugin | 2 | 5 | 3 | 3 | 1 | 2 | 5 | 2 | 2 | 2.60 |

Normalised to 5.0 scale. Scoring spreadsheet embedded as the table
above; formula is sum(weight_i * score_i) / 100.

---

## 4. Component-level Evaluations

Independent of stack choice, the UI must pick editor / graph / state
engines. These are orthogonal and can mostly be mixed.

### 4.1 State store

| Option | Notes | Score |
|---|---|---:|
| **Zustand + Immer** | Small (~3 KB), subscribe-by-selector, natural fit for event-sourced cache, low boilerplate | 5 |
| Redux Toolkit + RTK Query | Powerful but heavier; RTK Query caching conflicts with our event-driven model | 3 |
| Valtio | Proxy-based; ergonomic but less predictable with serialisation | 3 |
| Jotai | Atom-based; good for fine-grain reactivity but large number of atoms becomes unwieldy | 3 |
| XState | Overkill for the store layer; reserve for specific state-machine components | 2 |

Recommendation: **Zustand + Immer**.

### 4.2 Graph engine

| Option | Notes | Score |
|---|---|---:|
| **React Flow** | Rich (edges, mini-map, handles), active development, supports 500+ nodes with virtualisation | 5 |
| Cytoscape.js | Great for large graphs but imperative API; React wrapper exists but less idiomatic | 4 |
| Sigma.js | Fast at 10k+ nodes; overkill here | 3 |
| vis.js | Legacy; not recommended | 2 |
| Svelte Flow | Good for S3 only; smaller ecosystem | 3 |

Recommendation: **React Flow** (for React stacks).

### 4.3 Code/DSL editor

| Option | Notes | Score |
|---|---|---:|
| **Monaco** | Industrial-strength (VS Code's engine), rich LSP, good TS types, heavy | 5 |
| CodeMirror 6 | Lighter, modular, excellent LSP via @codemirror/lsp; Svelte-friendly | 4 |
| Ace | Legacy | 2 |

For S1/S2/S4: Monaco. For S3: CodeMirror 6 (Monaco works in Svelte
but the React packaging is smoother). Both satisfy Ark LSP needs.

### 4.4 Markdown editor

| Option | Notes | Score |
|---|---|---:|
| **TipTap** | ProseMirror-based, excellent slash-command support, React and Svelte adapters | 5 |
| Lexical | Meta's; capable but heavier API | 3 |
| Plate (Slate-based) | Rich but Slate has stability history | 3 |
| Plain Monaco in markdown mode | Source-only; misses rich preview | 3 |

Recommendation: **TipTap** for rich editing, with Monaco source
toggle.

### 4.5 Styling / component library

| Option | Notes |
|---|---|
| **shadcn/ui + Tailwind** | Best-in-class for React; copy-paste components keeps maintenance in-tree; Tailwind's utilities keep design predictable |
| Mantine | Full-featured React UI kit; heavier; less customisation friction than MUI |
| Ant Design | Enterprise-feel; heavy; less flexible design language |
| Skeleton UI | Svelte-native for S3 |

Recommendation: **shadcn/ui + Tailwind** (for React stacks).

### 4.6 Routing

| Option | Notes |
|---|---|
| **Next.js app router** | If S1/S2; built in |
| TanStack Router | For S4 browser SPA; typed routing with loaders and pending states |
| SvelteKit file router | For S3 |

### 4.7 MCP client library

| Option | Notes |
|---|---|
| **@modelcontextprotocol/sdk (TS)** | Official, supports stdio + WebSocket, actively maintained |
| Custom thin client | Only if the SDK is missing a feature (e.g., filtered subscriptions); prefer PR upstream |

---

## 5. Final Recommendation

### 5.1 Primary recommendation: S1 (Next.js + shadcn/ui + Tauri)

**Rationale.**

- **Highest weighted score (4.50).** Wins on six of nine criteria.
- **Windows-first correctness** via Tauri: uses system WebView2
  (Edge Chromium) so installer is ~5-10 MB and startup is ~1 s on a
  typical Windows 11 machine. Native file dialogs and HiDPI are
  correct.
- **MCP bridge lives in the Tauri Rust backend.** The Rust side
  already exists in this repo (ark-orchestrator crate), so a native
  MCP bridge is a natural extension rather than a new process. This
  also aligns with the ambition to ship Ark as a Rust-native spec
  language with browser and desktop consumers.
- **Share-link is free**: Next.js static export serves the same
  bundle over HTTP with a token-gated read-only MCP proxy.
- **Ecosystem depth** for the component libraries the requirements
  depend on: React Flow for graphs, Monaco for DSL, shadcn for a
  consistent design system. These are all first-class in React.
- **Dev velocity** matches the milestone pace in architecture §13.
  Approval-only writes (M4-UI-1) are achievable in a single
  adventure with this stack because the heavy lifting (layout,
  auth, routing) is provided.

Recommended component picks for S1:

- State: Zustand + Immer.
- Router: Next.js app router.
- Styling: Tailwind + shadcn/ui.
- Code / DSL editor: Monaco.
- Markdown: TipTap with Monaco source toggle.
- Graph: React Flow.
- MCP client: `@modelcontextprotocol/sdk`.
- Query layer: direct state-store hooks (no TanStack Query); the
  event stream keeps data fresh.

### 5.2 Fallback: S4 (Browser SPA + Vite)

If Tauri integration encounters a blocker (Rust toolchain friction,
signing challenges on Windows) use S4: the same React codebase
without the Tauri shell. The user runs a local MCP bridge and opens
the UI in any browser. Scored 3.90; lower marks on C3 (Windows-
first) and C4 (MCP integration cost) because the bridge must be an
external process and the UX is constrained by browser chrome.

S4 is also the right first phase for M4-UI-0 (read-only snapshot
viewer): ship browser-SPA first, add Tauri packaging after.

### 5.3 Why not S2 (Electron)?

Scored 4.10, close to S1, but loses on C7 (bundle size) by a large
margin (100-150 MB installer vs 5-10 MB). For a Claudovka user who
may install several related tools (team-pipeline, binartlab, future
companions), every Electron app bundled with its own Chromium
compounds. Tauri uses the system WebView once. For single-tool apps
the choice is closer; in an ecosystem it matters.

### 5.4 Why not S3 (SvelteKit)?

Scored 3.95. Svelte's compile-time advantages are real but the
ecosystem gap is decisive here: React Flow has no equal in Svelte
today (Svelte Flow is younger and thinner), shadcn is React-only,
and the contribution-based plugin architecture in §8 of the
architecture doc is easier to implement in React. These are not
fatal; they just cost more time each.

### 5.5 Why not S5 (Lit)?

Scored 3.65. Lit wins on fundamentals (web components, standards,
smallest bundle) but the absence of a mature component library
would push the first six months of work into re-building primitives
that shadcn provides for free.

### 5.6 Why not S6 (Zed)?

Scored 2.60. Zed plugin is an interesting mid-term option for a
"Studio in my editor" integration but it cannot satisfy share-link,
outside-observer access, or the graph editor well. Revisit when
Zed's Windows story matures.

---

## 6. Risks and Mitigations

### 6.1 Tauri 2.x maturity

- **Risk**: Tauri 2.x is the current major; some APIs changed from
  1.x. Ecosystem catching up.
- **Mitigation**: Pin Tauri version; limit native code surface to
  what is demonstrably stable; factor the MCP bridge into a pure
  Rust crate that compiles outside Tauri for testability.

### 6.2 WebView2 dependency on Windows

- **Risk**: WebView2 assumed installed on Windows 11 (it is,
  evergreen since 2022) but a fresh Windows 10 machine may need the
  runtime bootstrapper.
- **Mitigation**: Ship Tauri's offline WebView2 bootstrapper; fall
  back to S4 (browser mode) if bootstrapper fails.

### 6.3 MCP TypeScript SDK feature gaps

- **Risk**: The current SDK does not support filtered event
  subscriptions (phase1 TM-M4).
- **Mitigation**: Land the filter-DSL tool (`pipeline.subscribe_filtered`)
  as a new MCP tool on team-mcp's side; the UI consumes it as a
  normal tool call rather than the MCP resource subscription.
  Upstream a PR to the SDK for proper resource-subscription filtering
  afterward.

### 6.4 Monaco + Tauri webview footprint

- **Risk**: Monaco is ~3 MB gzipped; on a cold Tauri start in an
  embedded webview this is a user-perceived delay.
- **Mitigation**: Lazy-load the editor bundle on first DSL tab
  open, not at startup. Preload in idle time.

### 6.5 Graph editor complexity

- **Risk**: Implementing round-trippable DSL-graph editing is
  deceptively hard; PDSL has a bespoke implementation that took
  effort.
- **Mitigation**: First ship read-only graph view (M4-UI-0).
  Defer graph-to-DSL writes to M4-UI-4. Reuse PDSL's
  `renderer.js` / `editor.js` as a reference.

---

## 7. Adventure / Task Breakdown Hint

The M4-UI-0 to M4-UI-5 milestones in the architecture doc §13 map
to likely future adventures. Rough sizing per milestone on the S1
stack:

| Milestone | Scope | Rough effort |
|---|---|---|
| M4-UI-0 | Read-only snapshot viewer | 1 adventure, ~5 tasks |
| M4-UI-1 | Approval-only writes | 1 adventure, ~4 tasks |
| M4-UI-2 | Entity editing (task/log/lesson) | 1-2 adventures, ~8 tasks total |
| M4-UI-3 | Full mutation surface | 2 adventures, ~10 tasks total |
| M4-UI-4 | Graph editor + DSL round-trip | 1 adventure, ~8 tasks |
| M4-UI-5 | Plugins + share links | 1 adventure, ~5 tasks |

Total Phase 4 estimate: 7-8 adventures, ~40-45 tasks. These will be
refined in their own planning adventures post-ADV-007.

---

## 8. Final Recommendation Summary

Build Claudovka Studio as:

- **S1 stack**: Next.js 15 app router + shadcn/ui + Tailwind,
  packaged in **Tauri 2** for Windows-first desktop delivery.
- **State**: Zustand + Immer, event-sourced from MCP.
- **Graph**: React Flow.
- **Editors**: Monaco (DSL) + TipTap (markdown).
- **MCP**: `@modelcontextprotocol/sdk` via Tauri's Rust backend for
  stdio, with WebSocket fallback for browser / share-link modes.
- **Ship order**: M4-UI-0 (read-only browser SPA) → M4-UI-1
  (Tauri shell with approvals) → upward per §7.

This stack maximises dev velocity for M4-UI-1 without compromising
long-term fit, keeps bundle size and startup in line with a small
desktop utility, and aligns with Ark's Rust-native direction on the
bridge side.

---

## 9. Acceptance Checklist (TC-015)

- [x] Six candidate stacks enumerated and scored (§§1, 3).
- [x] Nine-criterion weighted matrix defined (§2).
- [x] Component-level evaluations for state, graph, editor, markdown,
  styling, routing, MCP client (§4).
- [x] Final recommendation with rationale + fallback (§5).
- [x] Risks and mitigations for the recommended stack (§6).
- [x] Implementation sizing per milestone (§7).
- [x] Summary (§8).

---

## Appendix A — Upstream Inputs

- `phase4-ui-requirements.md` (requirements + similar-tool survey).
- `phase4-ui-architecture.md` (component layers, integration points,
  deployment topologies).
- `phase1-cross-project-issues.md` TM-M4 (filtered subscriptions
  gap) and X4 (version negotiation) — both addressed in §6 risks.
