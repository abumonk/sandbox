---
id: ADV-007-test-strategy
title: Validation Strategy — Claudovka Ecosystem Roadmap
adventure_id: ADV-007
target_conditions: [TC-034]
created: 2026-04-14T02:05:00Z
status: active
scope: research-only (no executable code)
---

# Validation Strategy — Claudovka Ecosystem Roadmap

ADV-007 is a research adventure: outputs are markdown artifacts (research, designs, integration matrices, roadmap), not code. Validation therefore tests **completeness, structural conformance, cross-reference integrity, and analytic depth** rather than runtime behavior. All checks are POC-style (file existence, grep counts, structural assertions) executable from a bash prompt at repo root `R:/Sandbox`.

## 1. Validation Criteria by Artifact Type

### 1.1 Research Documents (`research/phase{N}-*.md`)
Every research file MUST contain:
- YAML frontmatter with `id`, `phase`, `title`, `created`, `sources` (list).
- `## Summary` — 100-300 word abstract.
- `## Findings` (or `## Concepts`/`## Capabilities` for Phase 2/3.2 catalogs) — primary content section.
- `## Sources` or inline citations — at least 3 distinct citations for external research (Phase 3.2), at least 1 internal `.agent/` reference for internal reviews (Phase 1, 3.1).
- `## Open Questions` — explicitly empty list permitted, but section MUST exist to flag downstream design needs.

Per-document quality gate: **minimum 800 words** for single-topic research, **1500 words** for catalog/overview documents (Phase 1 project reviews, Phase 3.2 MCP catalog, Phase 5 concept designs).

Validation command pattern:
```
test -f research/phase1-team-pipeline.md \
  && grep -q "^## Findings" research/phase1-team-pipeline.md \
  && grep -q "^## Sources" research/phase1-team-pipeline.md \
  && [ "$(wc -w < research/phase1-team-pipeline.md)" -ge 800 ]
```

### 1.2 Design Documents (`designs/design-*.md`)
Per project convention (compatible with prior ADV-001..006):
- Frontmatter: `id`, `adventure_id`, `phase`, `target_conditions` (list of TC IDs covered).
- `## Context` — references prior research artifacts by relative path.
- `## Design` — proposed entities/skills/architecture.
- `## Alternatives Considered` — at least 2 alternatives listed.
- `## Acceptance Mapping` — explicit table TC ID → design section satisfying it.
- `## Risks` — at least 2 entries with mitigation.

Quality gate: each design document MUST be referenced by exactly the TCs declared in its `target_conditions` frontmatter (bidirectional consistency with `manifest.md`).

### 1.3 Integration Matrix (`research/phase3-2-integration-matrix.md`)
Special structure — MUST contain:
- A markdown table with header row `| Tool | P1 | P2 | P3.1 | P3.2 | P4 | P5 | P6 | P6.1 | P6.2 | P7 |` (10 phase columns plus tool name).
- One row per tool researched in T012/T013/T014/T015 (target: at least 18 rows = QMD, CodeGraphContext, Everything Claude Code, Game Studios, LSP, Agent Orchestrator + 14 MCP servers minus duplicates, with documented overlaps).
- Each cell either empty, `-`, `H`/`M`/`L` (high/medium/low integration potential), or an inline note (≤80 chars).
- Trailing `## Rationale` section explaining scoring rubric.

### 1.4 Roadmap (`research/master-roadmap.md`)
MUST contain:
- `## Phase Index` — table listing all 10 phases with: phase ID, title, source design, source plan, list of adventure IDs proposed (e.g., `ADV-008`, `ADV-009`, ...).
- `## Adventure Catalog` — one subsection per proposed adventure with: title, scope summary, depends_on (other proposed adventure IDs), TC count estimate, effort band (S/M/L/XL).
- `## Critical Path` — ordered list (or DAG description) showing the longest dependency chain.
- `## Parallelism Map` — sets of adventures that can run concurrently after their dependencies clear.
- `## Open Decisions` — outstanding architectural choices that block adventure scoping.

## 2. Completeness Checklist — All 10 Phases

For each phase, the listed artifacts MUST exist before the phase is marked complete. Phases share plans (e.g., Phase 3.1 + 3.2 use `plan-phase3-reviews-and-tools`), but each phase's artifact set is independently verified.

### Phase 1 — Project Review
- [ ] `research/phase1-team-pipeline.md`
- [ ] `research/phase1-team-mcp.md`
- [ ] `research/phase1-binartlab.md`
- [ ] `research/phase1-marketplace.md`
- [ ] `research/phase1-pipeline-dsl.md`
- [ ] `research/phase1-cross-project-issues.md` (covers TC-002, TC-003)
- [ ] Severity ratings present: `grep -c "^severity:" research/phase1-cross-project-issues.md` ≥ 5

### Phase 2 — Unified Knowledge Base
- [ ] `research/phase2-concept-catalog.md` (TC-004) — must enumerate ≥30 concepts with project provenance.
- [ ] `research/phase2-knowledge-architecture.md` (TC-005) — must contain `## Parallelism` and `## Token Economy` sections.
- [ ] `research/phase2-entity-redesign.md` (TC-006) — must contain literal "Before/After" headings and side-by-side proposals.

### Phase 3.1 — Pipeline Management Review
- [ ] `research/phase3-1-management-failures.md` (TC-007) — references at least ADV-001..006 by ID.
- [ ] `research/phase3-1-profiling-skills.md`, `research/phase3-1-optimization-skills.md`, `research/phase3-1-self-healing-skills.md` (TC-008, ≥3 files matching `phase3-1-*-skills.md`).
- [ ] `research/phase3-1-role-review.md` (TC-009) — covers planner, implementer, reviewer, researcher, orchestrator.

### Phase 3.2 — External Tools Research
- [ ] `research/phase3-2-{tool}.md` for each researched tool (≥6 individual tool files).
- [ ] `research/phase3-2-mcp-servers.md` (TC-012) — `grep -c "^### "` ≥ 14 (one heading per server).
- [ ] `research/phase3-2-integration-matrix.md` (TC-011) — see §1.3.

### Phase 4 — UI System
- [ ] `research/phase4-ui-requirements.md` (TC-013) — enumerates entity types: tasks, plans, designs, adventures, target conditions, evaluations, metrics.
- [ ] `research/phase4-ui-architecture.md` (TC-014) — contains `## Data Flow` section with diagram (mermaid or ascii).
- [ ] `research/phase4-technology-evaluation.md` (TC-015) — comparison table of ≥3 stacks, explicit recommendation.

### Phase 5 — New Concepts
- [ ] `research/phase5-concept-designs.md` (TC-016) — H2 sections for: scheduling, human-as-pipeline-role, input storage, messenger agent, project/repo/knowledge separation, custom entities, recommendations stack (7 required).
- [ ] `research/phase5-integration-map.md` (TC-017) — dependency table or graph.

### Phase 6 — Infrastructure
- [ ] `research/phase6-mcp-operations.md` (TC-018) — covers deploy, compile, build via MCP.
- [ ] `research/phase6-autotest-strategy.md` (TC-019) — coverage targets numerical (`%`).
- [ ] `research/phase6-automation-first.md` (TC-020) — explicit "human escalation criteria" subsection.

### Phase 6.1 — Final Reconstruction
- [ ] `research/phase6-1-complexity-analysis.md` (TC-021) — quantified reduction targets.
- [ ] `research/phase6-1-refactoring-strategy.md` (TC-022) — milestone list with criteria.
- [ ] `research/phase6-1-abstract-representation.md` (TC-023) — spec for representation layer.

### Phase 6.2 — Post-Final
- [ ] `research/phase6-2-benchmark-design.md` (TC-024) — baseline and target metrics tabulated.
- [ ] `research/phase6-2-test-profiles.md` (TC-025) — full-stack scenarios.
- [ ] `research/phase6-2-migration-strategy.md` (TC-026) — backward compatibility plan.

### Phase 7 — On Sail
- [ ] `research/phase7-optimization-loops.md` (TC-027)
- [ ] `research/phase7-self-healing.md` (TC-028) — error classification taxonomy.
- [ ] `research/phase7-human-machine.md` (TC-029) — escalation criteria.
- [ ] `research/phase7-operational-model.md` (TC-030) — futuring system design.

### Master (Phase Aggregation)
- [ ] `research/master-roadmap.md` (TC-031)
- [ ] `research/adventure-dependency-graph.md` (TC-032) — DAG with parallelism analysis.
- [ ] `research/adventure-contracts.md` (TC-033) — inter-adventure data contracts.
- [ ] `tests/validation-report.md` (TC-034)

## 3. Cross-Reference Verification Rules

Cross-references are the connective tissue of a research adventure. The following invariants MUST hold:

**R1. Phase prerequisite citation.** Every research document for phase P (P > 1) MUST cite at least one document from a prior phase in its `## Context` or `## Sources`. Verifiable as:
```
for f in research/phase{2,3-1,3-2,4,5,6,6-1,6-2,7}-*.md; do
  grep -lq "research/phase[12]\|research/phase[3-6]" "$f" || echo "MISSING_REF: $f"
done
```
Phase 2 references Phase 1; Phase 3.1 references Phase 1+2; Phase 3.2 may stand alone (external research) but MUST be cited from Phase 4+; Phase 4-7 reference Phase 2 (knowledge base) and Phase 3.x.

**R2. Adventure dependency completeness.** In `research/adventure-dependency-graph.md`, every proposed adventure MUST appear with an explicit `depends_on` list (empty `[]` allowed for roots). No forward reference to undefined adventure IDs; every referenced ID MUST be defined elsewhere in the same file.

**R3. TC ↔ artifact bijection.** Every TC in `manifest.md` MUST correspond to at least one artifact path that resolves to a real file. Verifiable by extracting `Proof Command` column and running each. Conversely, every research artifact MUST be referenced by at least one TC (no orphan files).

**R4. Design ↔ TC consistency.** For each design document, its `target_conditions:` frontmatter list MUST equal the set of TCs whose `Design` column points to that design ID in the manifest. Bidirectional check.

**R5. Plan ↔ task coverage.** For each plan file, the union of TCs across its tasks MUST equal the set of TCs whose `Plan` column points to that plan in the manifest.

**R6. Roadmap closure.** Every phase listed in `master-roadmap.md` Phase Index MUST appear in §2 of this strategy AND have at least one proposed adventure ID. No phase referenced in the concept (Phase 1..7) is omitted.

## 4. Quality Gates

| Gate | Threshold | Verification |
|------|-----------|-------------|
| Research doc word count (single-topic) | ≥ 800 words | `wc -w` |
| Research doc word count (catalog/overview) | ≥ 1500 words | `wc -w` |
| Required sections present | Frontmatter + Summary + Findings/Concepts + Sources + Open Questions | `grep -E "^## "` count ≥ 4 |
| External-tool research citations | ≥ 3 distinct URLs/refs | `grep -cE "https?://" $f` ≥ 3 |
| Internal review citations | ≥ 1 `.agent/` path reference | `grep -c "\.agent/" $f` ≥ 1 |
| Severity ratings (Phase 1 issues) | ≥ 5 entries | `grep -c "^severity:"` |
| MCP server entries | ≥ 14 H2/H3 headings | `grep -c "^### "` |
| Phase 5 concept count | exactly 7 H2 concept sections | manual `grep -c "^## "` (excluding meta sections) |
| UI tech stack candidates | ≥ 3 stacks evaluated | table row count |
| Roadmap parallelism | ≥ 1 documented parallel set | `grep -q "## Parallelism Map"` |
| Adventure dependency cycles | none | DAG validation (manual or script) |

Failure of any gate marks the relevant TC as `failed` until remediated.

## 5. Validation Proof Methods per Target Condition

Each TC's proof method (from manifest column 8) is `poc`. The expanded validation per TC:

| TC | Proof Command | Pass Criterion | Quality Gate(s) |
|----|---------------|----------------|-----------------|
| TC-001 | `ls research/phase1-{team-pipeline,team-mcp,binartlab,marketplace,pipeline-dsl}.md \| wc -l` = 5; each contains `## Findings` | 5 files, all with Findings | §1.1, §4 word count |
| TC-002 | `test -f research/phase1-cross-project-issues.md` | exists | §1.1 |
| TC-003 | `grep -c "^severity:" research/phase1-cross-project-issues.md` ≥ 5 | rating count | §4 severity gate |
| TC-004 | `test -f research/phase2-concept-catalog.md` AND ≥30 concept entries | exists + count | §2 Phase 2 |
| TC-005 | `grep -E "^## (Parallelism\|Token Economy)" research/phase2-knowledge-architecture.md \| wc -l` = 2 | both sections | §2 Phase 2 |
| TC-006 | `grep -E "Before/After\|before/after" research/phase2-entity-redesign.md` | match present | §1.1 |
| TC-007 | `test -f research/phase3-1-management-failures.md` AND `grep -E "ADV-00[1-6]"` matches | exists + cites prior advs | R1 |
| TC-008 | `ls research/phase3-1-*-skills.md \| wc -l` ≥ 3 | three skill files | §2 Phase 3.1 |
| TC-009 | `test -f research/phase3-1-role-review.md` AND covers ≥5 roles | exists + role coverage | §2 |
| TC-010 | `ls research/phase3-2-*.md \| wc -l` ≥ 8 (6 tool files + matrix + mcp) | file count | §2 Phase 3.2 |
| TC-011 | `test -f research/phase3-2-integration-matrix.md` AND header matches §1.3 | matrix structure | §1.3 |
| TC-012 | `grep -c "^### " research/phase3-2-mcp-servers.md` ≥ 14 | server count | §4 MCP gate |
| TC-013 | `test -f research/phase4-ui-requirements.md` AND lists ≥7 entity types | exists + entity coverage | §2 Phase 4 |
| TC-014 | `test -f research/phase4-ui-architecture.md` AND `grep -q "^## Data Flow"` | exists + section | §2 Phase 4 |
| TC-015 | `test -f research/phase4-technology-evaluation.md` AND ≥3 stack rows | exists + comparison | §4 UI gate |
| TC-016 | `test -f research/phase5-concept-designs.md` AND 7 concept H2s | exists + 7 concepts | §2 Phase 5 |
| TC-017 | `test -f research/phase5-integration-map.md` | exists + dependency table | §2 |
| TC-018 | `test -f research/phase6-mcp-operations.md` AND covers deploy/compile/build | exists + 3 operations | §2 Phase 6 |
| TC-019 | `test -f research/phase6-autotest-strategy.md` AND `grep -E "[0-9]+%"` matches | numeric coverage targets | §2 |
| TC-020 | `test -f research/phase6-automation-first.md` AND escalation subsection | exists + subsection | §2 |
| TC-021 | `test -f research/phase6-1-complexity-analysis.md` AND quantified targets | exists + numbers | §2 |
| TC-022 | `test -f research/phase6-1-refactoring-strategy.md` AND milestones listed | exists + milestone list | §2 |
| TC-023 | `test -f research/phase6-1-abstract-representation.md` | exists + spec | §2 |
| TC-024 | `test -f research/phase6-2-benchmark-design.md` AND baseline+target table | exists + metrics | §2 |
| TC-025 | `test -f research/phase6-2-test-profiles.md` | exists + scenarios | §2 |
| TC-026 | `test -f research/phase6-2-migration-strategy.md` AND BC plan | exists + compatibility | §2 |
| TC-027 | `test -f research/phase7-optimization-loops.md` | exists + metrics+triggers | §2 |
| TC-028 | `test -f research/phase7-self-healing.md` AND taxonomy section | exists + taxonomy | §2 |
| TC-029 | `test -f research/phase7-human-machine.md` AND escalation criteria | exists + criteria | §2 |
| TC-030 | `test -f research/phase7-operational-model.md` | exists + futuring design | §2 |
| TC-031 | `test -f research/master-roadmap.md` AND all 10 phases indexed | exists + index complete | §1.4, R6 |
| TC-032 | `test -f research/adventure-dependency-graph.md` AND DAG valid | exists + acyclic | R2, §4 cycles |
| TC-033 | `test -f research/adventure-contracts.md` | exists + contracts | §1.4 |
| TC-034 | `test -f tests/validation-report.md` AND all TC-001..TC-033 status recorded | report present + complete | this strategy applied to all TCs |

All paths are relative to `R:/Sandbox/.agent/adventures/ADV-007/`.

## 6. Validation Workflow (T024)

The final validation task (ADV007-T024) MUST execute, in order:
1. Iterate every TC, run its expanded proof command, record pass/fail.
2. Apply §3 cross-reference rules R1-R6, record violations.
3. Apply §4 quality gates per artifact, record warnings vs. failures.
4. Produce `tests/validation-report.md` containing:
   - YAML frontmatter with run timestamp.
   - Summary counts (TCs passed / failed / warning).
   - Per-TC results table.
   - Cross-reference violations list.
   - Quality-gate warnings list.
   - Final verdict: `accepted` (all TCs pass, ≤2 warnings) | `accepted-with-warnings` (all pass, ≤10 warnings) | `rejected` (any TC fail OR >10 warnings).

A `rejected` verdict triggers remediation tasks before adventure closure.
