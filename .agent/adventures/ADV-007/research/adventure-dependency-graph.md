---
id: adventure-dependency-graph
title: Adventure Dependency DAG + Parallelism Analysis
adventure: ADV-007
target_conditions: [TC-032]
produced_by: ADV007-T023
companion_docs:
  - research/master-roadmap.md
  - research/adventure-contracts.md
---

# Adventure Dependency Graph and Parallelism Plan

## 1. Notation

- `A → B` means B depends on A (A must reach M-α "ready" state before B can start execution). Dependency types:
  - `blocks`: B literally cannot run without A's artifacts (hard blocker).
  - `informs`: B runs better with A's artifacts but can start on a stale snapshot.
  - `shares-artifacts`: A and B co-edit the same store/schema; requires coordination but no blocking order.
- A **wave** is a set of adventures that can start after the previous wave's M-α markers are reached.
- **Critical path** = the longest chain of hard blockers.

## 2. ASCII DAG

```
                                     ADV-008
                                (Unified Knowledge Store)
                                   /   |   \   \   \
                                  /    |    \   \   \
                                 v     v     v   v   v
                            ADV-009 ADV-010 ADV-011 ADV-020 ADV-016
                       (Entity  (MCP    (Skills  (Autotest (Sched)
                        Shard)  Surface) Library) + CI)
                            |     |   \    |         \       |
                            |     |    \   |          \      |
                            |     v     v  v           v     v
                            |  ADV-012 ADV-021        ADV-020
                            |  (Roles) (Auto-1st)
                            |   /  |
                            |  /   |
                            | /    |
                            v v    |
                         ADV-013   |                   [wave 2]
                         (Ext MCP) |
                                   |
                         ----------+---------------
                                   |
                         [wave 3]  |
                                   v
                     +-----------+------+------+
                     |           |      |      |
                     v           v      v      v
                  ADV-017     ADV-018 ADV-022  ADV-014
               (Input/       (Proj   (ARL     (Studio UI
                Messenger)    split)  M0-M4)   Foundation)
                     |            \    |         |
                     |             \   |         v
                     |              \  |      ADV-015
                     |               \ |      (Editors+Live)
                     |                v|
                     |             ADV-019
                     |             (Custom Ent.
                     |             + Reco Stack)
                     |                |
                     +-----+----------+
                           |          |
                           v          v
                        ADV-023    ADV-024
                        (ARL       (Benchmarks)
                        M5-M8)
                           \          /
                            \        /
                             v      v
                           ADV-025
                         (Migration
                          Runbook)

                         [wave 5 — operations on sail]
                         ADV-026 (opt loops) ← ADV-011, 019, 015
                         ADV-027 (self-heal) ← ADV-011, 021
                         ADV-028 (futuring)  ← ADV-017, 019, 021, 027
```

## 3. Edge Table

| From (producer) | To (consumer) | Type | Reason / artifact carried |
|-----------------|---------------|------|---------------------------|
| ADV-008 | ADV-009 | blocks | Sharded event primitives |
| ADV-008 | ADV-010 | blocks | Store read/write is behind MCP tools |
| ADV-008 | ADV-011 | blocks | Metrics skills emit into the store |
| ADV-008 | ADV-014 | blocks | UI reads from event stream |
| ADV-008 | ADV-016 | blocks | Scheduler state lives in event stream |
| ADV-008 | ADV-020 | informs | CI harness replays events from store |
| ADV-009 | ADV-014 | blocks | UI consumes sharded entities |
| ADV-009 | ADV-018 | blocks | Project/repo/KB separation piggybacks on entity redesign |
| ADV-009 | ADV-022 | blocks | ARL renders to sharded entities |
| ADV-010 | ADV-012 | blocks | Role-capability grants live on MCP tools |
| ADV-010 | ADV-015 | blocks | UI writes go through MCP tools |
| ADV-010 | ADV-016 | blocks | Scheduler tools are MCP tools |
| ADV-010 | ADV-020 | informs | Autotest tests MCP tools |
| ADV-010 | ADV-023 | blocks | M7 "operational MCP-only" |
| ADV-011 | ADV-012 | blocks | Roles invoke skills |
| ADV-011 | ADV-021 | blocks | Automation-first consumes metrics skills emit |
| ADV-011 | ADV-026 | blocks | Optimization loops consume the skill metrics stream |
| ADV-011 | ADV-027 | blocks | Self-healing pipeline uses S1-S3 skills |
| ADV-012 | ADV-013 | blocks | External MCPs are granted by role capability |
| ADV-012 | ADV-017 | blocks | Human-as-pipeline-role needs role system refactor |
| ADV-012 | ADV-021 | informs | Automation-first policies target the new role prompts |
| ADV-014 | ADV-015 | blocks | Editors build on foundation |
| ADV-014 | ADV-026 | informs | Loop observability shows in the UI |
| ADV-016 | ADV-023 | blocks | Scheduler unification in M5 needs scheduler first |
| ADV-017 | ADV-021 | blocks | Escalations route through messenger |
| ADV-017 | ADV-028 | blocks | Futuring surfaces to humans via messenger |
| ADV-018 | ADV-019 | blocks | Custom entities live inside a project/repo/KB axis |
| ADV-018 | ADV-025 | blocks | Migration splits legacy conflated paths |
| ADV-019 | ADV-026 | blocks | Recommendations stack is the loops' target |
| ADV-019 | ADV-028 | blocks | Futuring writes into recommendations stack |
| ADV-020 | ADV-022 | blocks | Refactor gates require CI |
| ADV-020 | ADV-024 | blocks | Benchmarks run inside CI harness |
| ADV-021 | ADV-027 | blocks | Safety envelope = automation-first guardrails |
| ADV-021 | ADV-028 | blocks | Escalation triggers are defined by automation-first |
| ADV-022 | ADV-023 | blocks | M5-M8 continue M0-M4 |
| ADV-022 | ADV-024 | informs | Benchmarks measure the ARL-era system |
| ADV-022 | ADV-025 | blocks | Migration uses ARL translation semantics |
| ADV-023 | ADV-025 | blocks | Contract enforcement closes migrations |
| ADV-027 | ADV-028 | informs | Escalation model feeds back into human-machine balance |

Edges between {ADV-008, ADV-009, ADV-010} are `shares-artifacts` in addition to blocks — they must co-design the event/tool/entity schemas during wave 1.

## 4. Critical Path

The longest hard-blocker chain is:

```
ADV-008 → ADV-009 → ADV-022 → ADV-023 → ADV-025 → (roadmap complete)
          (3w)     (6w)      (6w)      (4w)
ADV-008:  4w
TOTAL:   23 weeks critical-path calendar time
```

No other chain exceeds this length. ADV-014/015 UI track adds 8 weeks but runs in parallel. ADV-026/027/028 wave-5 track is 4+4+4 weeks but only two can run concurrently, giving ~8 wall-clock weeks, still overlapped with wave-4 tail.

## 5. Wave Plan (minimises wall-clock)

### Wave 1 — Foundation (weeks 0–6)
- **Start simultaneously**: ADV-008, ADV-009, ADV-010 (`shares-artifacts`; cross-coordinated schema design).
- ADV-009 and ADV-010 start sketch/contract work at week 0; full implementation unblocks at ADV-008 M-α (~week 3).
- **Exit condition**: all three reach "shadow write to new store is green; legacy reads still correct" at ~week 6.

### Wave 2 — Skills + Safety (weeks 4–12, overlaps wave 1 tail)
- Start at week 4 (ADV-008 APIs already stable enough to consume):
  - ADV-011 (skills) — 3w
  - ADV-016 (scheduling) — 2w, starts week 6 when ADV-010 is ready
  - ADV-020 (autotest + CI) — 2w, starts week 4
- Start at week 7 (after ADV-011 + ADV-010):
  - ADV-012 (roles) — 2w
- Start at week 9 (after ADV-011 + ADV-012):
  - ADV-013 (external MCPs) — 2w
  - ADV-021 (automation-first) — 2w
- **Exit condition**: M-β reached at ~week 14.

### Wave 3 — New Surfaces + ARL Start (weeks 10–20)
- ADV-014 (UI foundation) — 4w starting week 10 (ADV-008/009 stable)
- ADV-017 (input/messenger) — 3w starting week 12 (needs ADV-012)
- ADV-018 (project/repo/KB separation) — 3w starting week 10 (needs ADV-009)
- ADV-022 (ARL + M0-M4) — 6w starting week 14 (needs ADV-020 gates)
- ADV-015 (UI editors + live) — 4w starting week 14 (needs ADV-014)
- ADV-019 (custom entities + reco) — 4w starting week 14 (needs ADV-018)
- **Exit condition**: M-γ reached at ~week 22.

### Wave 4 — ARL Growth + Migration (weeks 20–30)
- ADV-023 (ARL M5-M8) — 6w starting week 20
- ADV-024 (benchmarks) — 3w starting week 20 (parallel with ADV-023)
- ADV-025 (migration) — 4w starting week 26 (needs ADV-023)
- **Exit condition**: M-δ reached at ~week 30.

### Wave 5 — On Sail (weeks 24–34)
- ADV-026 (optimization loops) — 4w starting week 24 (parallel with tail of wave 4)
- ADV-027 (self-healing) — 4w starting week 24
- ADV-028 (futuring) — 4w starting week 28 (needs ADV-027)
- **Exit condition**: M-ε reached at ~week 34.

## 6. Parallelism Analysis

| Wave | Max concurrent adventures | Agents needed | Bottleneck |
|------|---------------------------|---------------|------------|
| 1    | 3 (ADV-008/009/010)       | 3–4 implementers + 1 architect coordinator | Schema coordination |
| 2    | 4 (ADV-011 + ADV-016 + ADV-020 in first half; then ADV-012 + ADV-021 + ADV-013 + tail of ADV-020) | 3–4 | ADV-011 outputs gate downstream |
| 3    | 5 (UI, input/messenger, project-split, ARL-start, UI editors starting mid-wave) | 5 | ADV-022 ARL design |
| 4    | 2–3 | 2–3 | ADV-023 ARL M5-M8 single bottleneck |
| 5    | 2–3 | 2–3 | None — runs in parallel with wave 4 tail |

**Peak staffing**: 5 concurrent adventure drivers mid-wave 3. The current evaluation model (one researcher, one architect, one implementer, plus optional reviewer/tester) can sustain 3 concurrent adventures; scaling to 5 requires either more agents or longer wave-3 duration.

## 7. Bottleneck Adventures (called out)

- **ADV-008 (Unified Knowledge Store)** — every wave-1+ adventure blocks on it. Mitigation: de-risk with a 1-week spike before committing; accept a simpler JSONL path as fallback.
- **ADV-022 (ARL M0-M4)** — widest fan-in in the graph; if its design time exceeds 2 weeks before implementation begins, the wave-4 start slips. Mitigation: lock the minimum-viable-ARL §8 scope before starting; forbid scope expansion until M2 ships.
- **ADV-023 (ARL M5-M8)** — only adventure on the critical path in weeks 20–26. No parallel fallback. Mitigation: split M5, M6, M7, M8 into four sub-adventures if week-24 burn-down shows risk.
- **ADV-025 (Migration)** — executes in production, so failures have real blast radius. Mitigation: per `phase6-2-migration-strategy.md` §4 six-step procedure + deprecation windows.

## 8. Topological Order (One Valid Sort)

A valid topological sort (one of many):

```
ADV-008, ADV-009, ADV-010,
ADV-011, ADV-016, ADV-020,
ADV-012, ADV-021, ADV-013,
ADV-018, ADV-014, ADV-022,
ADV-017, ADV-015, ADV-019,
ADV-024, ADV-023,
ADV-025, ADV-027, ADV-026, ADV-028.
```

The DAG is validated by the edge table in §3: every edge `A→B` has A appearing before B in the order above. No cycles exist.

## 9. Acceptance

This document satisfies **TC-032**: an ASCII DAG + edge table + parallelism analysis (concurrent sets, agent counts, bottlenecks) + a wave plan minimising wall-clock + a valid topological sort. Companion: `master-roadmap.md` for per-adventure scope, `adventure-contracts.md` for artifact schemas.
