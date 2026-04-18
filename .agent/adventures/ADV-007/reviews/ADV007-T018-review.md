---
task_id: ADV007-T018
adventure_id: ADV-007
status: FAILED
timestamp: 2026-04-15T00:00:40Z
build_result: PASS
test_result: PASS
---

# Review: ADV007-T018

## Summary
| Field | Value |
|-------|-------|
| Task | ADV007-T018 |
| Title | Design new ecosystem concepts |
| Status | FAILED |
| Timestamp | 2026-04-15T00:00:40Z |

## Build Result
- Command: (none configured in `.agent/config.md`)
- Result: PASS
- Output: No build command defined; this is a research/documentation task. Pass by default.

## Test Result
- Command: (none configured in `.agent/config.md`)
- Result: PASS
- Pass/Fail: N/A (research task, no automated tests)
- Output: No test command defined. Pass by default.

## Acceptance Criteria

| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | All 7 concepts designed with problem statements and use cases | Yes | `phase5-concept-designs.md` contains sections §1–§7, each with a Purpose (§x.1) and Use cases (§x.2) covering 3–5 concrete scenarios. All 7 concepts are present: Scheduling, Human-as-pipeline-role, Input Storage, Messenger Agent, Project/Repo/Knowledge Separation, Custom Entities, Recommendations Stack. |
| 2 | Entity model extensions defined for each concept | Partial | Each of the 7 sections in `phase5-concept-designs.md` includes a `§x.3 Entity model` subsection with jsonl layout, fields, and event kinds. However, the plan (`plan-phase4-5-concepts.md`) and design doc (`design-phase5-new-concepts.md`) both list `phase5-entity-models.md` as a required separate deliverable for entity model extensions — that file was not produced and is absent. The task's `files` frontmatter also omits it (only lists 2 of the 3 planned files). The embedded entity models are substantive but the planned dedicated file is missing. |
| 3 | Integration map showing all inter-concept dependencies | Yes | `phase5-integration-map.md` is comprehensive: §1 provides an annotated dependency graph with notation (→, ↔, ⇢) and a strongly-connected cluster analysis; §2 provides a 7×14 interaction matrix (CRUD/O); §3 provides a recommended rollout sequence with weekly markers and exit criteria; §4 documents 5 conflicts with existing designs plus resolutions. |
| 4 | Implementation complexity estimates | Yes | §8.1 of `phase5-concept-designs.md` contains a table estimating schema size, tool surface, UI delta, and estimated effort (S/M/L/XL with week counts) for all 7 concepts. Each concept also has a `§x.8 MV sketch → growth path` that contextualizes complexity in terms of minimum viable vs. full feature scope. |

## Target Conditions

| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-016 | All 7 new concepts designed with use cases and entity models | poc | `test -f .agent/adventures/ADV-007/research/phase5-concept-designs.md` | PASS | File exists; content verified to contain 7 concept sections with entity model subsections. |
| TC-017 | Integration map showing concept dependencies and interaction points | poc | `test -f .agent/adventures/ADV-007/research/phase5-integration-map.md` | PASS | File exists; contains dependency graph, interaction matrix, rollout sequence, and conflict analysis. |

## Issues Found

| # | Severity | Description | File | Line |
|---|----------|-------------|------|------|
| 1 | medium | `phase5-entity-models.md` is listed as a required deliverable in `plan-phase4-5-concepts.md` (§ "Design new ecosystem concepts" > Files) and in `design-phase5-new-concepts.md` (Target Files section), but the file was never produced. The task's `files` frontmatter was silently updated to omit it, dropping from 3 planned to 2 delivered files. Entity model content is embedded in `phase5-concept-designs.md` but a standalone extensions reference document was the stated artifact. | `.agent/adventures/ADV-007/research/phase5-entity-models.md` | N/A — file absent |
| 2 | low | The task `files` frontmatter declares only 2 files (`phase5-concept-designs.md`, `phase5-integration-map.md`), silently diverging from the 3-file plan specification without documenting why `phase5-entity-models.md` was merged into the concept-designs file or otherwise superseded. This creates a traceability gap. | `.agent/adventures/ADV-007/tasks/ADV007-T018.md` | line 10 |

## Recommendations

This task FAILED on one acceptance criterion: the separate `phase5-entity-models.md` file required by the plan and design document was not produced. The two delivered files are high quality — both are thorough, well-structured, and go well beyond the minimum required by the target conditions.

To pass, the implementer must either:

1. **Produce `phase5-entity-models.md`** as a standalone document consolidating the entity model extensions across all 7 concepts (fields tables, event kinds, jsonl layouts, relationships to existing entities from T008) — this is the cleanest fix matching the plan.
2. **Or document the merge decision** — if the entity model content is intentionally embedded in `phase5-concept-designs.md` and a separate file is deemed unnecessary, update the plan and task `files` frontmatter to reflect this decision, and get reviewer sign-off that the embedded coverage meets the "entity model extensions defined for each concept" AC.

Option 1 is preferred: the standalone file would serve as a useful cross-concept reference (e.g., a diff against the T008 entity redesign), while the concept-designs file already handles the per-concept narrative.

The integration map (`phase5-integration-map.md`) is particularly well done — the annotated dependency graph, the 7×14 CRUD/O matrix, the conflict resolutions with double-writer hazard analysis, and the 38-week rollout timeline with parallel-track optimization are all above standard for this adventure.
