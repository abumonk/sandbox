# Research: Claude Code Ecosystem Projects

**Task:** ADV007-T013
**Date:** 2026-04-14
**Sources:**
- Everything Claude Code (ECC) — https://github.com/affaan-m/everything-claude-code
- Claude Code Game Studios (CCGS) — https://github.com/Donchitos/Claude-Code-Game-Studios

---

## 1. Everything Claude Code (ECC)

### Purpose and Scope

ECC bills itself as a **performance-optimization system for AI agent harnesses**. It is harness-agnostic and explicitly targets cross-tool portability: Claude Code, Codex (CLI + app), Cursor, OpenCode, Gemini, and Antigravity. At v1.10.0 (Apr 2026) it ships **38 agents, 156 skills, 72 legacy command shims, multi-language rules, hooks, MCP configs, and a Tkinter desktop dashboard**. It also includes ECC 2.0 (a Rust control-plane prototype in `ecc2/`) and a sister project AgentShield (security scanner with 102 rules, 1282 tests).

The repository is positioned as production-grade: NPM packages (`ecc-universal`, `ecc-agentshield`), a GitHub Marketplace App (`ecc-tools` with free/pro/enterprise tiers), a paid SaaS layer, and 997+ internal tests.

### Organizational Patterns

- **Capability profiles**: `--profile full` vs language-targeted installs (`./install.sh typescript python`). Selective install architecture with `install-plan.js` + `install-apply.js` and a state store for incremental updates.
- **Multi-language rule directories** (`rules/common/`, `rules/typescript/`, `rules/python/`, `rules/golang/`, plus Java/PHP/Perl/Kotlin/C++/Rust). Install only the languages you use.
- **Hook runtime gating** via env vars: `ECC_HOOK_PROFILE=minimal|standard|strict` and `ECC_DISABLED_HOOKS=...`. No hook code edits required to tune intensity.
- **Package manager auto-detection** with priority chain (env var → project config → `package.json` → lockfiles → global config → fallback).
- **Plugin namespace**: `/ecc:plan` (plugin form) vs `/plan` (manual install) — same semantics, two surfaces.
- **NanoClaw v2**: model routing, skill hot-load, session branch/search/export/compact/metrics.
- **SQLite state store** for sessions plus session adapters for structured recording.

### Best Practices Identified

1. **Skills as primary surface, commands as legacy shims** — ECC is migrating off `commands/` toward skills, which are richer and discoverable via `/`.
2. **Continuous learning loop**: instinct-based pattern extraction with confidence scoring, import/export, and evolution. Sessions auto-feed reusable skills.
3. **Verification loops with grader types** — checkpoint vs continuous evals, pass@k metrics.
4. **Token-optimization discipline**: model routing per task, slimmed system prompts, background processes for long-running work.
5. **Memory persistence via hooks** — automatic save/load of context across sessions.
6. **Subagent orchestration with iterative retrieval pattern** as the answer to context window pressure.
7. **Cross-harness packaging**: same skill/agent/rule definitions ship to multiple harness formats from one source.
8. **Deterministic harness audit scoring** plus an observer loop with a 5-layer guard against re-entrancy.
9. **Slash commands for orchestration**: `/harness-audit`, `/loop-start`, `/loop-status`, `/quality-gate`, `/model-route`, `/multi-plan`, `/multi-execute`, `/multi-backend`, `/multi-frontend`, `/multi-workflow`.

### Novel Techniques Worth Adopting

- **Hook profile env-var gating** — directly applicable; we currently have no global on/off knob.
- **Instinct system** — confidence-scored pattern extraction. Could replace/augment our `.agent/knowledge/*.md` files with structured, scored entries that decay or get promoted.
- **SQLite session store + adapters** — better than our markdown-only logs for time-range queries and metrics aggregation. Could index `.agent/adventures/*/metrics.md`.
- **Selective install with state tracking** — relevant for distributing Claudovka pieces (skills, agent definitions) across multiple consumer projects (the Sandbox itself plus downstream `ark/` tooling).
- **Cascade/parallelization with git worktrees** — pattern for safe parallel agent execution we have not formalized.
- **`configure-ecc` interactive wizard** with merge/overwrite detection — useful when porting Claudovka into another repo.
- **Harness audit / quality gate as commands** — formalizes what our `reviewer` agent does loosely, and exposes it to humans.

### Anti-Patterns to Avoid

- **Catalog inflation**: 156 skills + 38 agents is impressive but creates maintenance load. Multiple changelog notes mention "catalog count enforcement," "harness audit scoring made deterministic," and a "memory explosion fix with throttling" — symptoms of scale outpacing structure. Lesson: do not grow a skill library without dedup pressure and per-skill tests.
- **Rule fragility**: ECC explicitly notes rules cannot be distributed via the plugin and must be installed manually. Their workaround is a separate `./install.sh` step. Tells us: if Claudovka adopts a plugin format, design rule distribution from day one.
- **Multi-product sprawl**: ECC, AgentShield, ECC Tools, NanoClaw, ECC 2.0 (Rust), dashboard, billing portal. The README itself acknowledges "instead of drifting into separate silos." Stay focused.
- **Hook one-liners replaced by scripts**: v1.8.0 explicitly retired "fragile inline one-liners." Skip that mistake — start with script files.
- **Instinct content loss bug** (v1.4.1): silent frontmatter parsing that dropped body content. Lesson: validate parser round-trips for every persisted artifact.

### Specific Artifacts to Port/Adapt

| Artifact | Origin | Adaptation |
|---|---|---|
| `ECC_HOOK_PROFILE` env-gating pattern | ECC hooks | Add `CLAUDOVKA_HOOK_PROFILE` for our `.claude/hooks/` |
| `/quality-gate` / `/harness-audit` commands | ECC orchestration | Map to a `/claudovka:audit` skill that runs reviewer + verifier in series |
| Instinct schema (frontmatter + Action/Evidence/Examples) | ECC continuous learning | Promote `.agent/knowledge/patterns.md` entries to per-pattern files with confidence scores |
| Selective install manifest | ECC v1.9.0 | Apply to skill/agent installation when adopting Claudovka in a sibling repo |
| Session SQLite adapter | ECC v1.9.0 | Optional — index `.agent/adventures/*/metrics.md` for cross-adventure analytics |
| Subagent observer with re-entrancy guard | ECC v1.9.0 | Adopt for our orchestrator to prevent runaway delegation loops |
| `/model-route` | ECC v1.8.0 | Pair with our existing `model:` field in task frontmatter to make routing visible/auditable |

### Integration Fit with Claudovka

**Strong fit** at the harness/infrastructure layer. ECC's skill/agent/hook mechanics map directly onto our `.claude/` layout. Where we already have stronger primitives — typed task lifecycles, the Adventure/Plan/Task hierarchy, and the Ark DSL as the artifact substrate — we should not adopt ECC's loose markdown discipline. Specifically: **do not import the catalog wholesale**. Cherry-pick the harness profile env-vars, the instinct format, and the orchestration commands.

**Weak fit** at the product/SaaS layer. AgentShield, ECC Tools, dashboard GUI, GitHub App marketplace — out of scope.

---

## 2. Claude Code Game Studios (CCGS)

### Purpose and Scope

CCGS turns a single Claude Code session into a **virtual game-development studio**. 49 agents, 72 skills, 12 hooks, 11 rules, 39 templates. Designed as a clonable template for solo+AI game development, with first-class support for Godot 4, Unity, and Unreal Engine 5 via dedicated specialist agent sets. Focus is **collaborative, not autonomous** — every workflow has explicit human approval gates.

### Organizational Patterns

- **Three-tier studio hierarchy**: Directors (Opus) → Department Leads (Sonnet) → Specialists (Sonnet/Haiku). Mirrors how human studios operate and gives a natural model-tier mapping.
- **Vertical delegation** (directors→leads→specialists), **horizontal consultation** (same-tier agents can consult but cannot make binding cross-domain decisions), **escalation** (conflicts go to shared parent — `creative-director` for design, `technical-director` for technical), **producer-coordinated change propagation**.
- **Domain boundaries**: agents do not write outside their domain without explicit delegation.
- **Engine specialist sets**: pick one of `godot-specialist`, `unity-specialist`, `unreal-specialist` plus sub-specialists (GDScript/Shaders/GDExtension, DOTS/ECS/VFX/Addressables/UI Toolkit, GAS/Blueprints/Replication/UMG).
- **Workflow catalog as machine-readable YAML** (`.claude/docs/workflow-catalog.yaml`) — phases → steps → required artifacts (glob + pattern + min_count) → next_phase. Drives `/help` and `/project-stage-detect` programmatically.
- **Path-scoped rules** (`src/gameplay/**`, `src/ai/**`, `src/networking/**`, `design/gdd/**`, `tests/**`, `prototypes/**`) that fire only on relevant edits.
- **Review intensity modes**: `full` / `lean` / `solo`, settable globally (`production/review-mode.txt`) or per-skill via `--review solo`.
- **Team orchestration commands**: `/team-combat`, `/team-narrative`, `/team-ui`, `/team-release`, `/team-polish`, `/team-audio`, `/team-level`, `/team-live-ops`, `/team-qa` — pre-bundled multi-agent flows for cross-cutting features.
- **Hooks fail gracefully** when optional tools (jq, Python) are missing. Each hook exits early on irrelevant inputs (e.g., commit hook returns 0 immediately for non-`git commit` commands).

### Best Practices Identified

1. **Strict agent frontmatter contract**: `name`, `description`, `tools`, `model`, `maxTurns`, `memory`, `disallowedTools`, `skills`. The `disallowedTools: Bash` example on `creative-director` is a clean way to deny destructive tools by role.
2. **Collaboration Protocol** as a fixed 5-step workflow embedded in every agent body: Ask → Present 2-4 options with pros/cons → User decides → Draft → Approve. Prevents autonomy drift.
3. **Strategic decision template** (Understand → Frame → Present 2-3 options → Recommend → Support): a reusable rhetorical structure for director-tier agents.
4. **Workflow phases with required-artifact verification** — `/gate-check` reads the catalog and checks files exist; verdicts are advisory, not blocking.
5. **Audit trail hooks** (`log-agent.sh` + `log-agent-stop.sh`) on subagent spawn/stop. Mirrors what we already do for adventures, but at the per-agent invocation level.
6. **Statusline integration** showing context%, model, current stage, epic breadcrumb.
7. **Templates folder (39 docs)** — every workflow output has a canonical skeleton.
8. **Theory grounding cited explicitly**: MDA, Self-Determination Theory, Flow State, Bartle Player Types. Anchors LLM reasoning in named frameworks.
9. **Prototypes isolated in `prototypes/`** with relaxed rules and required README (hypothesis documented). Prevents experimental code from polluting `src/`.

### Novel Techniques Worth Adopting

- **Workflow catalog YAML with artifact globs** — superior to our prose-style "design then implement then review" pipeline. We could express the Adventure→Plan→Task lifecycle as a similar catalog and have `/gate-check` validate phase completion.
- **Three-tier model-tier mapping** — Opus for directors, Sonnet for leads, Haiku for specialists. Maps cleanly to our existing `architect/researcher/reviewer = Opus`, `implementer = Sonnet` decision and gives a principled extension path.
- **Review intensity modes** — we currently lack a `solo` mode that bypasses the reviewer. Useful for hot-fix and prototype tasks; could be set in task frontmatter `review_mode: solo`.
- **Team orchestration commands** as pre-bundled multi-agent flows — analogue: `/claudovka:team-design` (architect + researcher in parallel), `/claudovka:team-ship` (implementer + reviewer + verifier in series).
- **Path-scoped rules** — formalize what we encode in CLAUDE.md prose. A `.claude/rules/ark-grammar.md` that fires only on `ark/dsl/grammar/**` edits would be tighter than blanket guidance.
- **Director/Lead/Specialist agent definition shape** — adopt the `disallowedTools` field and the embedded Collaboration Protocol section.
- **Hooks that early-exit on irrelevance** rather than skipping registration — keeps registry centralized while keeping execution cheap.
- **`/start` zero-assumption onboarding** that asks where the user is rather than guessing.

### Anti-Patterns to Avoid

- **49 agents for a solo developer** is overkill for most projects. The README admits "delete agent files you don't need." Lesson: ship a *minimal core* and document the optional roster, instead of installing all 49 by default.
- **Bash-only hooks on Windows** — works via Git Bash but is fragile. Our existing Node-style or Python hooks port more cleanly across platforms (ECC made the same migration explicit in v1.7.0).
- **Templates as static markdown** — risk of drift between template and what skills actually emit. Generate templates from schemas where possible.
- **No mention of inter-agent message passing** — coordination is implicit through shared files, which collides with concurrent edits in parallel sessions. We should keep our explicit Adventure manifest as the coordination point.

### Specific Artifacts to Port/Adapt

| Artifact | Origin | Adaptation |
|---|---|---|
| `workflow-catalog.yaml` schema | CCGS `.claude/docs/` | Define `.agent/workflow-catalog.yaml` for Adventure→Plan→Task phases with artifact globs |
| Director/Lead/Specialist three-tier model mapping | CCGS hierarchy | Codify in `.agent/config.md` agent settings |
| `disallowedTools` and `maxTurns` in agent frontmatter | CCGS agent files | Add to our existing agent definitions where applicable |
| `/start` onboarding skill | CCGS | Build `/claudovka:start` that detects adventure state and routes |
| `/project-stage-detect` skill | CCGS | Build `/claudovka:adventure-stage` that scans `.agent/adventures/*` for in-flight work |
| Path-scoped rules format | CCGS `.claude/rules/` | Migrate Ark-specific guidance from CLAUDE.md into `.claude/rules/ark-*.md` |
| Review intensity modes (`full`/`lean`/`solo`) | CCGS | Add `review_mode` to task frontmatter; reviewer skips when `solo` |
| Team orchestration command pattern | CCGS `/team-*` | Bundle our multi-agent flows: `/claudovka:team-design`, `/claudovka:team-ship` |
| Audit trail hooks per subagent | CCGS `log-agent.sh` | Already partially covered by adventure.log; extend to non-adventure agent invocations |
| Strategic decision template (3-option presentation) | CCGS creative-director | Embed in our architect agent prompt |

### Integration Fit with Claudovka

**Very strong fit** for organizational and workflow patterns. CCGS is closer to Claudovka's philosophy (collaborative, gated, hierarchical) than ECC (performance-optimized, harness-portable, autonomous). The workflow-catalog YAML, three-tier model mapping, path-scoped rules, and team-orchestration commands are all directly importable.

**Domain mismatch** is partial: CCGS is game-dev-specific in agent roster (gameplay-programmer, level-designer, narrative-director). The *structure* ports cleanly; the *roster* does not. We would substitute Ark-specific roles (grammar-designer, dsl-architect, codegen-engineer, verifier-specialist) in the same hierarchy.

---

## 3. Comparative Synthesis

| Dimension | ECC | CCGS | Claudovka stance |
|---|---|---|---|
| Primary value | Performance + portability | Structure + collaboration | Both — but lean CCGS |
| Catalog size | Sprawling (156 skills) | Focused (72 skills, one domain) | Stay focused, dedup aggressively |
| Autonomy | Higher (continuous loops) | Lower (5-step approval gates) | Match CCGS |
| Distribution | Plugin + npm + marketplace | Git template clone | Stay template; consider plugin later |
| Hook strategy | Env-var profile gating | Path-relevance early-exit | Adopt both |
| Knowledge persistence | SQLite + instincts w/ confidence | Markdown templates | Promote knowledge files to scored instinct format |
| Multi-agent orchestration | `/multi-*` + observer loop | `/team-*` pre-bundled flows | Adopt `/team-*` pattern |
| Workflow definition | Implicit in skills | YAML catalog with artifact checks | Adopt YAML catalog |

### Top 5 Recommended Adoptions (ranked by leverage)

1. **`workflow-catalog.yaml` for Adventure→Plan→Task phases** (CCGS) — unlocks `/gate-check`, `/help`, `/project-stage-detect` analogues.
2. **Three-tier model mapping with `disallowedTools` + `maxTurns`** (CCGS) — formalizes existing practice and prevents runaway agents.
3. **Hook profile env-var gating + path-relevance early-exit** (ECC + CCGS) — combines best of both hook strategies.
4. **Instinct schema with confidence scoring** (ECC) — replaces flat `.agent/knowledge/*.md` with structured, evolvable patterns.
5. **`/team-*` orchestration commands** (CCGS) — exposes our multi-agent flows as discoverable surface.

### Top 3 Anti-Patterns to Reject

1. ECC's catalog inflation — do not grow Claudovka's skill count without dedup tests.
2. ECC's product sprawl (SaaS, marketplace, dashboard) — out of scope.
3. CCGS's bash-only hooks — keep Python/Node hooks for Windows-first compatibility.

---

## 4. Open Questions for the Architect

1. Do we want the workflow catalog to be machine-readable YAML or stay in our existing markdown plan/manifest format? (Recommend: YAML, with manifests linking to it.)
2. Should `review_mode: solo` exist at all, or does Claudovka's identity require always-on review?
3. Is the instinct/confidence pattern worth the migration cost from flat knowledge files at our current adventure count (~7)?
4. Do we adopt `disallowedTools` per agent now, or wait until we have a security incident?

---

**Word count:** ~2,360
