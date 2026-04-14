---
task: ADV007-T005
adventure: ADV-007
researched: 2026-04-14
targets:
  - C:/Users/borod/.claude/plugins/cache/claudovka-marketplace/
  - C:/Users/borod/.claude/plugins/cache/claudovka-marketplace/team-pipeline/0.14.3/dsl/
status: complete
---

# Marketplace and Pipeline DSL Research

## 1. The "Marketplace" Reality

The path `claudovka-marketplace/` is the local cache of the **Claudovka** plugin marketplace, but the cache itself is *not* a marketplace manifest. It is a flat directory containing a single plugin family:

```
claudovka-marketplace/
  team-pipeline/
    0.11.0/   <- versioned plugin snapshot
    0.12.0/
    0.14.0/
    0.14.3/   <- current
```

Each version directory is a fully-self-contained Claude Code plugin. The marketplace surface is implicit: Claude Code auto-discovers a plugin by the presence of `.claude-plugin/plugin.json` inside any version directory.

### Plugin manifest (`.claude-plugin/plugin.json`)

Minimal shape:
```json
{
  "name": "team-pipeline",
  "description": "...",
  "version": "0.14.3",
  "author": { "name": "Claudovka" },
  "homepage": "https://github.com/abumonk/team-pipeline",
  "repository": "https://github.com/abumonk/team-pipeline",
  "license": "MIT",
  "keywords": ["team", "pipeline", "tasks", "agents", ...]
}
```

There is **no top-level `marketplace.json`** in the cache root and no index of available plugins. The "marketplace" semantic lives inside Claude Code itself; the cache is a passive payload store.

### Plugin layout (per version)

`team-pipeline/0.14.3/` contains:
- `.claude-plugin/plugin.json` — manifest
- `agents/`, `commands/`, `roles/`, `skills/`, `templates/`, `hooks/` — Claude-Code-native artifacts
- `hooks/hooks.json` — lifecycle hook bindings
- `schema/` — three YAML-frontmatter doc schemas (`agent-schema.md`, `hooks-schema.md`, `step2step-schema.md`)
- `dsl/` — the **Pipeline DSL** (PDSL) implementation in plain Node.js
- `docs/`, `knowledge/` — supporting docs
- `check-pipeline.sh`, `pipeline-status.sh` — bash helpers

Versions 0.11.0 / 0.12.0 / 0.14.0 are nearly identical layouts but **lack the `dsl/` directory** — PDSL is a 0.14.3 addition.

## 2. The Pipeline DSL (PDSL)

PDSL is a text-based DSL for describing the team-pipeline data model and agent behavior. Source files use the `.pdsl` extension. Implementation: ~4,300 LOC of plain JavaScript, no dependencies, runs under `node --test`.

### 2.1 Implementation map (`dsl/`)

| File | LOC | Purpose |
|------|-----|---------|
| `parser.js` | 1546 | Single-pass lexer + recursive-descent parser |
| `layout.js` | 711 | AST → positioned graph (nodes/edges with x,y,w,h) |
| `validator.js` | 404 | Two-pass semantic validator (9 rules) |
| `serializer.js` | 386 | AST → canonical PDSL text (round-trippable) |
| `renderer.js` | 322 | LayoutGraph → SVG string |
| `cli.js` | 280 | `render` / `validate` / `format` commands |
| `ast.js` | 232 | Node constructors + `TokenType` table |
| `editor.js` | 220 | Programmatic AST mutations (`addField`, `renameEntity`, ...) |
| `themes.js` | 191 | Default theme + `createTheme(overrides)` deep merge |
| `index.js` | 26 | Public API surface |
| `viewer.html` | — | Browser editor with live SVG preview, no server required |

Public API (re-exported by `index.js`):
`parse`, `tokenize`, `serialize`, `TokenType`, `validate`, `layout`, `render`, `defaultTheme`, `createTheme`, `applyEdit`, `EditCommand`, `addFieldCommand`, `removeFieldCommand`, `renameEntityCommand`.

### 2.2 Grammar (PEG, version 0.1.0)

Documented formally in `dsl/grammar.md`. Four top-level declaration kinds:

1. **`lifecycle <Name> { ... }`** — agent cycle definition with sub-blocks `input`, `execute`, `transitions`, `completion`, plus simple fields `role:`, `model:`, `trigger:`. Action verbs: `read`, `write`, `update`, `explore`, `emit`, `log` (extensible).
2. **`structure <Name> { ... }`** — hierarchical artifact (Adventure, Task) with sub-blocks `contains`, `spawns`, `delegates`, `checkpoints`, plus fields `id:`, `state:`.
3. **`entity <Name> { ... }`** — typed data record. Field syntax has a fixed suffix order: `name : TypeExpr [/pattern/] [?] [= default] [Cardinality]`. Enum-only entities use `values: a | b | c`.
4. **`relation <Src> -> <Dst> { ... }`** — directed association with fields `type:`, `via:`, `cardinality:`, `constraint:`, `lifecycle:`.

Lexical features:
- `//` line and `/* */` block comments
- 24 reserved keywords (PEG negative-lookahead prevents identifier collision)
- Three literal kinds: `"string"`, `123`, `/regex/`
- Comparison ops `== != < <= > >=`, logical `&&` `||` (used only in `trigger:` expressions)
- Cardinality dual notation: bracketed suffix `[0..*]` on type refs, bare `0..*` in relation fields

### 2.3 Validator rules

`validator.js` knows eight primitive types (`string`, `number`, `boolean`, `date`, `markdown`, `yaml`, `json`, `path`) and seven well-known stage names (`planning`, `implementing`, `reviewing`, `fixing`, `completed`, `researching`, `wait`). It runs a two-pass check (symbol collection, then constraint verification) and emits `{message, severity, node, rule}` diagnostics. Severity is `error` or `warning`.

### 2.4 Worked examples shipped

- `examples/pipeline-entities.pdsl` — Task, Stage, Status, Adventure, Environment, AdventureState, TargetCondition + four relations
- `examples/pipeline-lifecycle.pdsl` — seven lifecycles (PlanningCycle, ImplementingCycle, ReviewingCycle, FixingCycle, ResearchingCycle, AdventurePlanningCycle, AdventureReportingCycle)
- `examples/adventure-structure.pdsl` — Adventure + Task structures with full state machines
- `examples/step2step.pdsl` — Step-to-Step (S2S) meta-pipeline (theme → adventure)

These examples are the *spec-by-example* for the team-pipeline domain; they are also the primary integration test corpus for the parser/validator/renderer.

### 2.5 Visual schema language

The "visual" half is delivered by `layout.js` + `renderer.js` + `viewer.html`:
- Layered graph layout (configurable `nodeWidth`, `nodeHeight`, `layerSpacing`, `nodeSpacing`)
- SVG output with theme-keyed stage colors (`theme.stages.planning.fill` etc.)
- Browser viewer is a single static HTML page with a split-pane: live editor on the left, live SVG on the right, real-time parse + render on every keystroke

There is **no separate `.vsl` or graphical source format** — PDSL text *is* the source; the SVG is a derived view.

## 3. Capabilities Summary

- Round-trippable text format (parser + serializer + `--check` flag for CI formatting gate)
- Browser-only authoring (no Node install needed for editing/viewing)
- Programmatic editing API (`applyEdit`, `addFieldCommand`, `removeFieldCommand`, `renameEntityCommand`) — enables agent-driven schema evolution without string manipulation
- Self-describing: the team-pipeline domain is itself modeled in PDSL (`pipeline-entities.pdsl`)
- Zero runtime dependencies; uses only Node stdlib + `node --test`

## 4. Issues

### High severity

- **No marketplace index file.** The cache directory has no `marketplace.json` or equivalent to enumerate available plugins. Discovery is filesystem-walk only. If Claudovka hosts more plugins than `team-pipeline`, this cache does not show them — the user has only ever installed/synced this one.
- **Validator is permissive on transition targets.** Targets outside `WELL_KNOWN_STAGES` produce only warnings, so typos in custom stage names slip through silently.
- **Verb set hard-coded.** Action verbs (`read`, `write`, `update`, `explore`, `emit`, `log`) are an enumerated PEG choice. The grammar comment says new verbs "may be added in future versions" but parsers are *not* asked to accept-with-warning today — unknown verbs are hard parse errors. This contradicts the grammar's own forward-compatibility note.

### Medium severity

- **`TypeExpr` ambiguity by design.** A single identifier matches both `EnumValues` (zero-pipe form) and `TypeRef`. The parser cannot distinguish them; resolution is deferred to the validator. This is documented but means parse trees are intentionally fuzzy and any downstream tool must duplicate the validator's resolution logic.
- **Two cardinality notations.** `[0..*]` (bracketed, suffix) vs `0..*` (bare, in `cardinality:` fields). Documented as intentional but it is a footgun — easy to write the wrong one in the wrong context.
- **No import/include mechanism.** PDSL v0.1.0 is single-file. The four shipped examples each redeclare stub entities (`entity Task {}`) to satisfy cross-file references. This forces copy-paste and is flagged as "future work" in `grammar.md` §9.
- **Pattern literal vs division ambiguity** is sidestepped only because PDSL has no arithmetic. Any future expression extension breaks `/regex/` parsing.
- **Multiple plugin versions cached side-by-side** (0.11.0, 0.12.0, 0.14.0, 0.14.3) with no GC. Total disk footprint grows monotonically.

### Low severity / strange decisions

- Plugin author is `"Claudovka"` but homepage/repo point to `github.com/abumonk/team-pipeline` — branding inconsistency.
- `viewer.html` is shipped *inside* the plugin payload but has no entry point in the manifest; users must know to open it manually.
- `keywords` array in `plugin.json` includes `"adventure"` but the manifest does not declare which stages/agents/commands the plugin exposes — Claude Code must scan subdirectories to find them.
- No `engines` or `claude-code-version` field in `plugin.json` — version compatibility is implicit.
- The four worked examples each repeat the same stub-entity preamble; an `import` would eliminate ~40 lines of duplication.

## 5. Integration Potential with Ark DSL (R:/Sandbox/ark)

Ark is a much richer DSL (pest-PEG grammar with `abstraction`, `class`, `instance`, `island`, `bridge`, `registry`, `expression`, `predicate`, `verify` items; Z3-backed verification; Rust orchestrator; Python codegen/visualizer/parser; Lark + pest dual grammars). PDSL is a focused subset. The integration story is **PDSL becomes a profile/dialect of Ark, not the other way around**:

### Direct mappings

| PDSL construct | Ark equivalent | Notes |
|---|---|---|
| `entity X { ... }` | `class X { ... }` or `abstraction X` | Ark already has typed fields with cardinality. |
| `entity X { values: a \| b \| c }` | enum class (already supported per recent commit `f43a3f9` "enum-aware Z3 verification") | Pure enums map cleanly. |
| `relation A -> B { type: ..., via: ..., cardinality: ... }` | `bridge` item | Bridges already express directed inter-island links. |
| `structure X { contains/spawns/delegates/checkpoints }` | `island` item with sub-declarations | Islands are Ark's hierarchical containers. |
| `lifecycle X { input/execute/transitions/completion }` | new `lifecycle` item OR `agent_system` spec | `specs/infra/agent_system.ark` already exists in working tree. |
| `trigger:` boolean expression | Ark `predicate` items | Ark already has predicate DSL items per commit `2af7f92`. |

### What Ark already provides that PDSL lacks

- Z3 invariant verification (`tools/verify/`)
- Multiple backends (pest + Lark parsers, Python + Rust runtimes)
- Codegen pipeline (PDSL only renders SVG; Ark generates code)
- Import/module system (Ark `import dotted.path`)
- Richer expression DSL (PDSL trigger expressions are intentionally minimal)

### What PDSL provides that Ark lacks

- Browser-based live editor with zero install (`viewer.html`)
- Round-trip serializer with `--check` CI gate
- Deterministic SVG layout pipeline tuned for stage-based pipelines
- Programmatic AST edit commands (`addFieldCommand` etc.) — directly useful for agent-driven schema evolution

### Recommended integration path (preview)

The Ark `specs/meta/` directory already contains `evolution_skills.html` and `evolution_skills.ark` — Ark is moving toward agent-evolution use cases that overlap PDSL's domain. The cleanest integration is:

1. Treat PDSL as an Ark **dialect/profile**: a subset of Ark grammar with PDSL's keyword names aliased to Ark concepts.
2. Port `examples/pipeline-lifecycle.pdsl` and `examples/adventure-structure.pdsl` into `R:/Sandbox/ark/specs/pipeline/` as `.ark` files; verify via existing Z3 pipeline.
3. Reuse PDSL's `viewer.html` + `renderer.js` as a visualization layer for Ark — Ark currently has `tools/visualizer/ark_visualizer.py` (Python) but no browser editor.
4. Promote PDSL's `editor.js` AST-mutation API into Ark's orchestrator crate so agents can evolve specs without text munging.

## 6. Recommendations

1. **Add a real marketplace index** (`marketplace.json` or equivalent) at the cache root so multi-plugin discovery does not require filesystem walks.
2. **Tighten validator transition checks**: stages referenced by `on X -> Y` should be errors, not warnings, when `Y` is not a declared lifecycle stage in the same file.
3. **Implement open-verb-set parsing**: accept unknown verbs with a warning, matching the grammar's stated forward-compatibility intent.
4. **Add PDSL `import "file.pdsl"`** to eliminate stub-entity duplication across the four shipped examples.
5. **Disambiguate `TypeExpr`** at parse time by introducing a distinct `EnumLiteral` production (single identifier with explicit `enum` marker) so downstream tools do not need to re-implement validator logic.
6. **For Ark integration**: copy the four PDSL examples into `R:/Sandbox/ark/specs/pipeline/` as a translation exercise. This will surface concrete grammar gaps (lifecycle/structure/relation items) and drive a unified Ark+PDSL grammar before the two diverge further.
7. **Clean up old plugin versions** in the cache (0.11.0, 0.12.0, 0.14.0) — keep only N most recent or only the active version.
8. **Add `claude-code-version`** to `plugin.json` to make compatibility explicit.
9. **Register `viewer.html`** in the plugin manifest (or via a `command`) so users can launch it without filesystem knowledge.
10. **Treat PDSL `editor.js` as a reference design** for the Ark orchestrator's spec-mutation API — this is the most directly portable piece.
