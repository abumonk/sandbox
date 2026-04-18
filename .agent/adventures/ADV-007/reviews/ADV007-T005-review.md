---
task_id: ADV007-T005
adventure_id: ADV-007
status: FAILED
timestamp: 2026-04-15T00:00:00Z
build_result: N/A
test_result: N/A
---

# Review: ADV007-T005

## Summary
| Field | Value |
|-------|-------|
| Task | ADV007-T005 |
| Title | Research Marketplace and Pipeline DSL projects |
| Status | FAILED |
| Timestamp | 2026-04-15T00:00:00Z |

## Build Result
- Command: `(none — build_command is empty in .agent/config.md)`
- Result: N/A
- Output: No build step applicable to this research task.

## Test Result
- Command: `(none — test_command is empty in .agent/config.md)`
- Result: N/A
- Output: No automated test step applicable to this research task.

## Acceptance Criteria
| # | Criterion | Met? | Notes |
|---|-----------|------|-------|
| 1 | Both repositories located or absence documented | Partial/No | The marketplace cache at `C:/Users/borod/.claude/plugins/cache/claudovka-marketplace/` was located and its absence-of-a-true-marketplace-server documented. The Pipeline DSL inside `team-pipeline/0.14.3/dsl/` was also found. However, the output was written to `marketplace-and-dsl.md` rather than the two separate canonical output files (`phase1-marketplace.md` and `phase1-pipeline-dsl.md`) specified in both the task's `files` frontmatter and the design document. |
| 2 | Marketplace plugin lifecycle documented | Partial/No | `marketplace-and-dsl.md` §1 documents the plugin manifest shape and cache directory layout. However, no plugin *lifecycle* (install → activate → update → remove flow) is documented — only the cache structure and manifest format. Lifecycle events from `hooks/hooks.json` are not analyzed. |
| 3 | Pipeline DSL syntax and semantics analyzed | Yes | `marketplace-and-dsl.md` §2 provides thorough grammar analysis (PEG v0.1.0, four declaration kinds, lexical rules, validator rules, examples, visual rendering). This criterion is substantively met. |
| 4 | Integration points with other projects mapped | Yes | §5 of `marketplace-and-dsl.md` provides a detailed PDSL↔Ark integration map with direct construct mappings, comparison of capabilities, and a recommended integration path with four concrete steps. |

## Target Conditions
| ID | Description | Proof Method | Command | Result | Output |
|----|-------------|-------------|---------|--------|--------|
| TC-001 | All 5 Claudovka projects researched with documented findings | poc | `grep -l "## Findings" .agent/adventures/ADV-007/research/phase1-*.md` | FAIL | Command exits 1 — no `phase1-*.md` files exist in the research directory (only `phase1-cross-project-issues.md`, which does not contain `## Findings`). The T005 deliverable was written to `marketplace-and-dsl.md` instead, and that file also contains no `## Findings` heading. |

## Issues Found
| # | Severity | Description | File | Line |
|---|----------|-------------|------|------|
| 1 | high | Output files do not match declared `files` frontmatter. Task declares `phase1-marketplace.md` and `phase1-pipeline-dsl.md` as deliverables; researcher wrote to `marketplace-and-dsl.md` instead. TC-001 proof command finds no matching files and fails. | `.agent/adventures/ADV-007/tasks/ADV007-T005.md` frontmatter `files:` field | 10 |
| 2 | high | TC-001 proof command fails (`grep -l "## Findings" .agent/adventures/ADV-007/research/phase1-*.md` exits 1). Neither the expected `phase1-marketplace.md` / `phase1-pipeline-dsl.md` nor `marketplace-and-dsl.md` contains a `## Findings` heading. | `.agent/adventures/ADV-007/research/marketplace-and-dsl.md` | — |
| 3 | medium | Plugin lifecycle not documented. AC-2 requires the marketplace plugin lifecycle (install/activate/update/remove) to be documented, but `marketplace-and-dsl.md` only covers manifest structure and cache layout. Hooks in `hooks/hooks.json` — the primary lifecycle signal — are referenced but not analyzed. | `.agent/adventures/ADV-007/research/marketplace-and-dsl.md` | §1 |

## Recommendations

The task must be reworked or its deliverables corrected before it can pass. Ordered by priority:

1. **Create the two canonical output files** specified in the design document and task `files` frontmatter:
   - `.agent/adventures/ADV-007/research/phase1-marketplace.md` — Marketplace analysis
   - `.agent/adventures/ADV-007/research/phase1-pipeline-dsl.md` — Pipeline DSL analysis

   The content in `marketplace-and-dsl.md` is high quality and can be split into these two files. Alternatively, update the task `files` frontmatter and design document to reflect the combined file — but TC-001's proof command pattern (`phase1-*.md`) must also be satisfied, which requires the `phase1-` prefix naming convention.

2. **Add `## Findings` heading to each output file** so the TC-001 proof command (`grep -l "## Findings" .agent/adventures/ADV-007/research/phase1-*.md`) succeeds and returns at least the two new files.

3. **Document the plugin lifecycle** (install → activate → version switch → remove) by reading `hooks/hooks.json` from the cached plugin and mapping the hook event names to lifecycle stages. This is required by AC-2.

4. Once the above are complete, update the task `files` frontmatter to reference the corrected deliverable paths and set `status: passed`.
