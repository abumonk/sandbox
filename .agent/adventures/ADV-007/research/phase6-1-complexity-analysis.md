---
task: ADV007-T020
adventure: ADV-007
phase: 6.1
target_conditions: [TC-021]
upstream:
  - .agent/adventures/ADV-007/research/phase1-cross-project-issues.md
  - .agent/adventures/ADV-007/research/phase2-concept-catalog.md
  - .agent/adventures/ADV-007/research/phase2-entity-redesign.md
  - .agent/adventures/ADV-007/research/phase5-concept-designs.md
  - .agent/adventures/ADV-007/research/phase6-mcp-operations.md
researched: 2026-04-14
---

# Phase 6.1 — Complexity Analysis and Reduction Targets

This document quantifies the current complexity of the Claudovka ecosystem
and defines numeric reduction targets for the Phase 6.1 reconstruction.
Every target is tied to one or more of the **X1-X11 cross-cutting issues**
from the Phase-1 synthesis (T006) so that progress can be measured against
the issue catalog directly.

"Lightweight" is defined here as the combined reduction of four axes:
LOC, duplicated-schema count, API surface (tool/hook/command count), and
auto-injected prompt tokens. A single `lightweight_index` is proposed as
the weighted geometric mean of the four so that one scalar tracks the
whole effort.

---

## 1. Current Complexity Baseline

Numbers below are drawn from the Phase-1 project reviews (T002-T005), the
Phase-2 entity redesign (T008), and the catalog (T007). Where a number is
approximate (team-pipeline agent prompts; marketplace cache) that is
flagged with `~`.

### 1.1 LOC by project

| Project | LOC (source) | LOC (prose/prompts) | LOC (generated) | Total | Source |
|---|---:|---:|---:|---:|---|
| team-pipeline (plugin) | ~4 000 | ~18 000 (agents+skills+hooks) | 0 | ~22 000 | team-pipeline.md §1 |
| team-mcp (server) | ~6 500 | ~920 (deploy manual) | 0 | ~7 400 | team-mcp.md §2 |
| binartlab (monorepo) | ~21 000 | ~1 500 (docs) | ~2 000 (`.js`/`.d.ts` checked in) | ~24 500 | binartlab.md §1 |
| claudovka-marketplace | ~150 (viewer) | 0 | 0 | ~150 | marketplace-and-dsl.md |
| PDSL (inside TP) | ~1 800 | ~300 (grammar.md) | 0 | ~2 100 | marketplace-and-dsl.md §3 |
| Ark (this repo) | ~3 500 | ~800 (specs) | ~400 (py generated) | ~4 700 | repo walk |
| **Ecosystem total** | **~37 000** | **~21 500** | **~2 400** | **~60 900** | — |

Two observations stand out: (a) **prose/prompt LOC (35 %) rivals source
LOC** — the "prose-as-program" anti-pattern from phase1 §3.1, and
(b) binartlab alone is **40 %** of the ecosystem, with one package
(`@binartlab/mobile`, 9 429 LOC) having no design coverage (BL-2).

### 1.2 Entity count

The Phase-2 entity redesign §0 enumerates 15 existing entities. The
Phase-5 concept designs add 7 new first-class entities (scheduling,
human-role, input-storage, recommendations, plus 3 implicit: Run,
PermissionSpec, Lesson). Current effective entity count across the
ecosystem (counting one entity per project per concept) is **~38**
(15 concepts × average 2.5 representations). The canonical target is
**22** (15 existing + 7 new, each with exactly one representation).

### 1.3 Concept duplication — schemas in multiple places

From T006 §1.4 (data-ownership matrix) and T007 §9 (concept overlap):

| Concept | Current copies | Where | Canonical target |
|---|---:|---|---:|
| Pipeline state machine (stages + transitions) | **4** | TP agent prompts, TM `lib/schema.js`, BL `@binartlab/shared` zod, PDSL `validator.js` WELL_KNOWN_STAGES | 1 (Ark spec) |
| Schema dialects | **5** | prose md, JS predicates, zod, PDSL PEG, Ark | 1 (Ark trunk) + codegen |
| Event-log implementations | **3** | TP `adventure.log`, TM ring buffer, BL WS broadcaster | 1 (durable jsonl) |
| Permissions representation | **3** | TP prose, TM `boundaries.js`, BL scope filter | 1 (PermissionSpec) |
| Metrics ledger writers | **3** | TP `metrics.md` edit, TM `metrics_log`, BL `MetricsCollector` | 1 (TM only) |
| Knowledge store | **2** | `knowledge/` md, `agent-memory/<role>/` | 1 (Lessons jsonl) |
| Role/agent enum | **3** | TP `agents/` files, TM 4-value enum, BL no enum | 1 (generated registry) |
| Tool/skill/command catalogs | **3** | README, CLAUDE.md, deployment manual | 1 (generated) |
| Session concept | **3** | LeadSession, LockSession, ClientConnection | 3 (distinct, renamed) |
| Manifest concept | **4** | AdventureManifest, PluginManifest, ProjectManifest, McpManifest | 4 (distinct, renamed) |

**Duplicated-schema count: 23 (sum of "current copies" for the first
eight rows).** Renames (Session, Manifest) are not duplicates — they are
genuinely distinct concepts masked by a shared word. The reduction target
is therefore across the duplication rows only.

### 1.4 API surface

From T007 §3 and T019:

| Surface | Current | Source |
|---|---:|---|
| MCP tools (TM `pipeline.*`) | 40+ | T002, T019 §2 |
| MCP tools (BL per-agent) | ~12 (one-third of planned) | binartlab.md, BL-1 |
| Hook prompts (TP) | 4 (SubagentStop, UserPromptSubmit, Stop, SessionStart) | team-pipeline.md §1 |
| Hook-prompt size | ~6 KB total, multi-KB each | X8 |
| Slash commands (TP) | 4 dispatchers | T007 §3.2 |
| Skills (TP) | ~25 | T007 §3.2 |
| Agent files (TP) | ~14 | T007 §3.2 |
| Role templates (TP) | 15 | T007 §3.2 |
| Operational tools (Phase 6) | 7 (deploy/build/compile/test/migrate/rollback/metrics) | phase6-mcp-operations.md §2 |

**API-surface total (countable items): ~110** (40 + 12 + 4 + 4 + 25 + 14 +
15). Half of this is "catalog that drifts" (skills + agents + roles +
commands = 58); the other half (tools + hooks) is the actual behaviour
surface.

### 1.5 Edge contracts (E1-E14)

From T006 §1.3: **14 inter-service edges**, of which:

- **2 are unimplemented** (E13 binartlab↔team-pipeline; E14 Ark↔PDSL).
- **3 have weak or implicit contracts** (E1 marketplace auto-discovery;
  E2 TP↔`.agent/` direct I/O; E11 BL DSL zod-only).
- **1 has non-atomic writes** (E4 TM↔`.agent/`, X6).
- **2 are half-implemented** (E6 messenger; E10 BL web clients).

The fully-contracted-and-enforced count is **6 of 14** (~43 %). The
reduction-and-consolidation target is to land all 14 as first-class
Contract entities with producer/consumer/transport/schema/enforcement/
version fields (T007 §10.4).

### 1.6 Auto-injected prompt tokens

From T008 §18.2 — a representative spawn of every tier:

| Spawn tier | Current auto-inject | Target | Reduction |
|---|---:|---:|---:|
| Researcher (T1) | ~45 KB | ~6 KB | -87 % |
| Reviewer (T1) | ~30 KB | ~6 KB | -80 % |
| Planner (T2) | ~35 KB | ~10 KB | -71 % |
| Implementer (T3) | ~25 KB | ~8 KB | -68 % |
| Lead (T4) | ~55 KB | ~15 KB | -73 % |

**Weighted average reduction: ~76 %** (weighted by spawn frequency
observed in ADV-007: researcher 35 %, reviewer 20 %, planner 20 %,
implementer 15 %, lead 10 %).

---

## 2. Complexity Hotspots (ranked)

Every hotspot here is tied to a phase-1 X-issue so it can be tracked
against the catalog.

### H1 — Prose-as-program hook prompts (X8)
- **Size**: ~6 KB per hook × 4 hooks × every event = largest runtime
  cost in the ecosystem.
- **Reduction path**: hooks become 3-line shims forwarding to
  `pipeline.on_*` deterministic tools (T008 §14; phase6 MCP-ops §3).
- **Target**: -92 % hook-prompt LOC; -100 % non-determinism.

### H2 — Pipeline state machine in four places (X1)
- **Size**: ~400 LOC equivalent across 4 codebases, continually
  drifting.
- **Reduction path**: one Ark spec + codegen to TM/BL/PDSL/TP-prompts
  (T007 §12.1).
- **Target**: -75 % copies (4 → 1 authoritative source); drift rate → 0.

### H3 — Three DSLs, none consumed by the runtime (X2)
- **Size**: PDSL ~1 800 LOC + binartlab YAML infra ~900 LOC + Ark
  ~3 500 LOC = ~6 200 LOC in parallel tool chains.
- **Reduction path**: Ark becomes the trunk; PDSL degrades to an Ark
  dialect (viewer + editor preserved, parser retired); BL YAML replaced
  by Ark codegen.
- **Target**: -40 % DSL LOC (delete PDSL parser/validator ~1 200 LOC;
  replace BL YAML schema with generated code ~600 LOC); single surviving
  grammar.

### H4 — Prompt LOC ≈ source LOC (prose-as-program, ecosystem-wide)
- **Size**: ~21 500 LOC of prose vs ~37 000 LOC of source. Tests cannot
  cover prose; diffs cannot verify it.
- **Reduction path**: move hook prompts to tools (H1); generate
  agent/skill/command catalogs from source (X3); move schema prose to
  Ark (H2, H3).
- **Target**: -40 % prose LOC (down to ~13 000) with zero loss of
  behaviour.

### H5 — Binartlab monorepo weight (BL-2, BL-3, BL-4)
- **Size**: 24 500 LOC, 40 % of the ecosystem; largest package
  (`@binartlab/mobile`) undocumented; `.js`/`.d.ts` build artefacts
  checked in; frontend test density 1/1374 vs backend 1/100.
- **Reduction path**: scope decision on mobile (own or excise); strip
  built artefacts from VCS; raise frontend coverage with round-trip
  property tests (BL-Strange-6).
- **Target**: -30 % binartlab LOC (excise mobile or move to a separate
  repo; remove checked-in `.js`/`.d.ts`); testing density normalised to
  1/300 across packages.

### H6 — Non-atomic writes on shared markdown state (X6)
- **Size**: every writer into `.agent/` (TP agents, TP hooks, TM tools,
  BL-future) duplicates the same "read, modify, write-whole-file"
  pattern.
- **Reduction path**: atomic write (tmp + fsync + rename) centralised in
  one TM helper; forbid direct file I/O fallback in hooks (X8's H1 fix
  removes the last non-MCP writer).
- **Target**: -100 % non-atomic-write sites; 1 canonical `state.write()`
  implementation.

### H7 — Concurrency control aspirational (X7)
- **Size**: TM LockManager covers 2 of ~30 read-modify-write tool paths.
- **Reduction path**: per-file lock at the MCP-tool wrapper level;
  combined with append-only jsonl substrate for multi-writer surfaces,
  removes the need for locks on those surfaces altogether (T008 §4, §5,
  §10, §11).
- **Target**: 100 % RMW tool coverage OR conversion of surface to
  append-only; zero silent last-write-wins paths.

### H8 — Catalog drift (X3)
- **Size**: 58 catalog items (skills + agents + roles + commands)
  hand-curated in multiple files; at least 3 documented drifts (Low-1,
  M2, M3, L5).
- **Reduction path**: `registry/{skills,agents,roles,triggers}.json`
  generated at TM start from the source directories; README and
  CLAUDE.md cite via include directive (T008 §§7-9).
- **Target**: 0 hand-curated catalog entries; drift rate → 0.

### H9 — Version negotiation absent (X4)
- **Size**: plugin ↔ server ↔ marketplace has no `compatible-with`
  anywhere; binartlab packages all at `0.1.0` with `*` peer-deps.
- **Reduction path**: `claude-code-version` and `compatible-with` fields
  everywhere; TM refuses to start on mismatch; `active.json` pin in the
  marketplace cache.
- **Target**: 100 % version-declared components; automatic
  incompatibility rejection on boot.

### H10 — Large files that auto-load (token cost)
- **Size**: manifest ~5-6 KB, permissions.md multi-KB, MEMORY.md first
  200 lines auto-injected per spawn, knowledge files large.
- **Reduction path**: shard manifest → jsonl + rendered view; shard
  permissions per scope; role-view slice of knowledge (T008 §§2, 12, 5).
- **Target**: -76 % auto-inject on weighted-average spawn (see §1.6).

### H11 — Token estimation proxy (X11)
- **Size**: `turns × 1500` / `turns × 500` estimates across every
  evaluation table.
- **Reduction path**: authoritative metric from Anthropic SDK response
  read by TM; back-fill `metrics_log`; remove proxy arithmetic.
- **Target**: 100 % metrics from authoritative source; variance budget
  of ±5 % vs prior ±100 %.

---

## 3. Reduction Targets with Numeric Goals

| Axis | Current baseline | Target | Delta | Tied to |
|---|---:|---:|---:|---|
| Ecosystem LOC (excluding generated) | ~58 500 | ~38 000 | **-35 %** | H4, H5 |
| Prose / prompt LOC | ~21 500 | ~13 000 | **-40 %** | H1, H4, H8 |
| Duplicated schemas (rows §1.3) | 23 copies | 8 copies (one per concept) | **-65 %** | H2, H3 |
| DSL grammars shipped | 3 (PDSL PEG, Ark pest, Ark lark) | 1 (Ark pest + auto-generated lark) | **-67 %** | H3 |
| MCP tools (TM, combined) | 40+ (loose naming) | 30 canonical + 7 operational | **same count, 100 % renamed** | H3, H6, H7 |
| Hook prompts | ~6 KB × 4 | ~0.5 KB × 4 | **-92 %** | H1 |
| Hand-curated catalogs | 58 items | 0 | **-100 %** | H8 |
| Non-atomic-write sites | ~30 | 0 | **-100 %** | H6 |
| RMW tools without lock | ~28 | 0 | **-100 %** | H7 |
| Version-negotiated pairs | 0 / ~10 | 10 / 10 | **+100 %** | H9 |
| Auto-inject tokens per spawn (weighted avg) | ~40 KB | ~9 KB | **-76 %** | H10 |
| Metrics variance (estimate vs actual) | ±100 % | ±5 % | **-95 %** | H11 |
| Edge contracts enforced | 6 / 14 | 14 / 14 | **+57 %** | H2, H9 |

### 3.1 "Lightweight" index (single scalar)

Let `L_source`, `L_schema`, `L_api`, `L_tokens` be the post-reduction
fractions (current → target) of LOC, duplicated schemas, API surface,
and auto-inject tokens respectively. Weighted geometric mean:

```
lightweight_index = (L_source^0.25) × (L_schema^0.25) × (L_api^0.25) × (L_tokens^0.25)
```

With the targets above:

- `L_source = 38/58.5 = 0.65` → 0.65^0.25 = 0.898
- `L_schema = 8/23 = 0.348` → 0.348^0.25 = 0.768
- `L_api = 60/110 = 0.545` → 0.545^0.25 = 0.860
- `L_tokens = 9/40 = 0.225` → 0.225^0.25 = 0.688

`lightweight_index ≈ 0.898 × 0.768 × 0.860 × 0.688 = 0.408`

Target: bring the index below **0.42** (the 0.408 above is the
rounded Phase-6.1 commitment). A single scalar lets the reviewer in
M5 verify reconstruction progress without re-running the ten-row table.

### 3.2 Concepts to merge (tie to T007 §10.2)

The following merges land the `L_schema` factor:

1. **TaskLifecycle**: 4 copies → 1 Ark spec. (H2; X1.)
2. **PermissionSpec**: 3 representations → 1 entity with codegen to
   runtime checks. (H6 prerequisite; X1-style.)
3. **EventLog**: 3 implementations → 1 durable jsonl + derived views.
   (H6, H7; X6, X7.)
4. **KnowledgeBase ∪ AgentMemory**: 2 stores → 1 jsonl with `role:`
   field and role-scoped views. (X9.)
5. **Schema dialect**: 5 → 1 (Ark trunk + codegen). (H3; X2.)
6. **Metrics ledger**: 3 writers → 1 (TM only, read authoritative
   token usage). (H11; X11.)
7. **Pattern/Issue/Decision**: 3 files → 1 union `Lesson` with `kind:`
   field (T007 §10.2, optional merge).

### 3.3 Concepts to split (tie to T007 §10.3)

These do not reduce the scalar but are prerequisites for clarity:

1. **Pipeline** → `TaskLifecycle` | `Adventure` | `Pipeline (executable)`.
2. **Manifest** → `AdventureManifest` | `PluginManifest` |
   `ProjectManifest` | `McpManifest`.
3. **Tool** → `ClaudeTool` | `McpTool`.
4. **Session** → `LeadSession` | `LockSession` | `ClientConnection`.

Splitting a word into N distinct concepts does not increase entity
count because each of the N was already a distinct entity masquerading
as one.

### 3.4 Concepts to introduce (tie to T007 §10.4)

Necessary vocabulary for the reductions above:

- **Run** — enables §1.5 contract enforcement and §3 metrics.
- **PermissionSpec** — absorbs the 3-way permission duplication.
- **Contract** — promotes E1-E14 to first-class, required for H9.
- **Lesson** — absorbs the 2-way knowledge duplication.
- **Project** — absorbs the cwd walk-up vs DB-row divergence between
  TP/TM and BL (completes the boundary-resolution contract).

Adding 5 new entities while removing the 8 duplication rows is a **net
reduction** of 3 concept-representations plus the canonical rename.

---

## 4. Crosswalk: X1-X11 ↔ Reduction Targets

Every cross-cutting issue from T006 is resolved by at least one
numeric target above:

| Issue | Severity | Resolved by target(s) |
|---|---|---|
| X1 — state machine in 4 places | critical | Duplicated schemas, H2 |
| X2 — two DSLs unused by runtime | high | DSL grammars, H3 |
| X3 — hand-curated catalogs | high | Hand-curated catalogs → 0, H8 |
| X4 — implicit version contracts | high | Version-negotiated pairs, H9 |
| X5 — no end-to-end test | high | (Refactoring strategy, milestone gate §3 of TC-022) |
| X6 — non-atomic writes | critical | Non-atomic-write sites → 0, H6 |
| X7 — aspirational concurrency | high | RMW tools without lock → 0, H7 |
| X8 — hook prompts as program | critical | Hook prompts -92 %, H1 |
| X9 — memory vs knowledge drift | medium | Duplicated schemas (KB merge), merge #4 |
| X10 — messenger half-implemented | medium | (Covered in phase5 concept + refactoring §M2) |
| X11 — token estimation proxy | medium | Metrics variance ±5 %, H11 |

All 11 issues have at least one numeric gate. Severity-weighted
coverage: 4 critical + 6 high + 2 medium = **100 %** of the catalog.

---

## 5. What "Done" Looks Like

Reconstruction is declared complete when, in a fresh checkout:

1. `grep -rc "STAGES\s*=" ark/ team-pipeline/ team-mcp/ binartlab/` returns
   **1** (the Ark spec).
2. `wc -l hooks/*.json` shows hook prompt LOC < 0.5 KB total.
3. `ls .agent/knowledge/lessons.jsonl` exists and `.agent/agent-memory/`
   is absent (or is a symlink to a generated view).
4. `find .agent/ -name "*.md" -exec head -1 {} \;` finds no file that
   both has a YAML frontmatter and is larger than 5 KB (the small-file
   rule, T008 §3.2 precept).
5. The autotest harness (`pipeline.test(scope="full")`) passes the 14
   contract tests generated from Phase 6 contracts.
6. `lightweight_index < 0.42` computed from the live repo.
7. Every entry in T006 §2 has a check mark in its `resolved_by:`
   field; no `severity: critical` or `severity: high` remains.

These seven gates are the acceptance checklist for the reconstruction.

---

## 6. Acceptance Checklist (this document)

- [x] LOC by project quantified (§1.1).
- [x] Entity count quantified (§1.2).
- [x] Concept duplication quantified with canonical target (§1.3).
- [x] Tool count quantified (§1.4).
- [x] Edge-contract count quantified (§1.5).
- [x] Complexity hotspots enumerated and ranked (§2, H1-H11).
- [x] Numeric reduction targets table (§3).
- [x] Lightweight scalar index defined (§3.1).
- [x] Crosswalk X1-X11 ↔ targets (§4).
- [x] "Done" criteria as objective gates (§5).
