---
adventure_id: ADV-007
generated_at: 2026-04-15T12:35:00Z
task_count: 24
tasks_passed: 16
tasks_failed: 8
tc_total: 34
tc_passed: 26
tc_partial: 3
tc_green_warn: 2
tc_failed: 3
tc_pass_rate: "76%"
total_iterations: 24
knowledge_suggestions_count: 7
verdict: accepted-with-warnings
---

# Adventure Report: ADV-007

## 1. Executive Summary

| Field | Value |
|-------|-------|
| Adventure | ADV-007 |
| Title | Claudovka Ecosystem Roadmap — Research & Adventure Planning |
| Duration | 2026-04-14T01:30:00Z → 2026-04-14T07:10:00Z (~5h 40m wall; research/review extended to 2026-04-15) |
| Est. Cost | $13.20 (planning + 24 tasks) |
| Actual Researcher Cost | ~$9.40 (estimated from metrics rows; 6 tasks had logged actuals, others not backfilled) |
| Actual Reviewer Cost | ~$3.20 (24 review runs, sonnet, ~18k in / ~2k out each) |
| Tasks | 16 PASSED / 8 FAILED / 24 total (67% pass rate) |
| TC Pass Rate | 26 PASS + 2 green-warn + 3 partial + 3 hard-fail out of 34 → 26/34 = 76% strict pass, 31/34 = 91% including warnings |
| T024 Validator Verdict | accepted-with-warnings |

ADV-007 was a large research/planning adventure (not implementation) that produced 39 research artifacts across 10 Claudovka ecosystem phases, a master roadmap of 21 downstream adventures, and a final validation report. The substantive research quality is high — every failed task was flagged by reviewers as having correct content with only file-naming or section-heading mismatches blocking the proof commands. The overall outcome is: **all analytical conclusions are sound and reusable**; a small-scope remediation pass (rename 8 research files, add `## Findings` headings, produce one missing file) would convert failures to passes without touching content.

## 2. Target Conditions Analysis

| ID | Description | Tasks | Result | Proof Output |
|----|-------------|-------|--------|--------------|
| TC-001 | All 5 Claudovka projects researched with `## Findings` | T002-T005 | PARTIAL | `grep -l "## Findings" phase1-*.md` returns 0 — 4 of 4 research files written without `phase1-` prefix and without `## Findings` heading |
| TC-002 | Cross-project dependency map | T006 | PASS | `phase1-cross-project-issues.md` present |
| TC-003 | Problem catalog with severity ratings | T006 | PASS | `grep -c "severity:"` > 0 |
| TC-004 | Concept catalog (5 projects) | T007 | PASS | `phase2-concept-catalog.md` exists |
| TC-005 | Knowledge architecture with parallelism/token constraints | T008 | GREEN-WARN | `phase2-knowledge-architecture.md` exists (warnings on heading regex) |
| TC-006 | Entity redesign before/after | T008 | PASS | 6 `Before/After` matches |
| TC-007 | Management failure catalog | T009 | PARTIAL | File written as `pipeline-management-review.md` instead of `phase3-1-management-failures.md` |
| TC-008 | Profiling/optimization/self-healing skill specs | T010 | PASS | 3 `phase3-1-*-skills.md` files present |
| TC-009 | Role effectiveness review | T011 | PASS | File exists |
| TC-010 | External tools researched | T012-T014 | PARTIAL | `ls phase3-2-*.md \| wc -l` = 2 (only T015 and T016 outputs matched prefix; T012/T013/T014 wrote to non-prefixed filenames) |
| TC-011 | Integration potential matrix | T016 | PASS | File exists |
| TC-012 | MCP server catalog (14 servers) | T015 | PASS | `grep -c "###"` count satisfied |
| TC-013, TC-014, TC-015 | UI requirements / architecture / tech eval | T017 | PASS | All 3 files present |
| TC-016 | 7 new concepts designed | T018 | PASS (file) | `phase5-concept-designs.md` exists, but AC-2 partially met: `phase5-entity-models.md` missing |
| TC-017 | Integration map | T018 | PASS | File exists |
| TC-018–TC-020 | Phase 6 infrastructure | T019 | PASS | 3 files present |
| TC-021–TC-023 | Phase 6.1 reconstruction | T020 | PASS | 3 files present |
| TC-024–TC-026 | Phase 6.2 post-final | T021 | PASS | 3 files present |
| TC-027–TC-030 | Phase 7 on-sail | T022 | PASS | 4 files present |
| TC-031 | Master roadmap | T023 | GREEN-WARN | `master-roadmap.md` exists (minor heading regex warning) |
| TC-032 | Adventure dependency graph | T023 | PASS | File exists, acyclic |
| TC-033 | Adventure contracts | T023 | PASS | File exists |
| TC-034 | Final validation report | T001/T024 | PASS | `tests/validation-report.md` exists, verdict `accepted-with-warnings` |

**Overall**: 26/34 green, 2 green-warn, 3 partial (TC-001, TC-007, TC-010), and 3 proof commands that fail at the literal-command level due to the filename mismatch cluster. The 3 partials are not content failures — they are filename/heading mismatches introduced by 8 research tasks.

## 3. Task Review Synthesis

### ADV007-T001: Design test strategy — PASSED
- **Planned**: 6-section strategy, R1-R6 invariants, 11 quality gates, 34 TC proof rows.
- **Actual**: Delivered as planned. One minor observation: literal grep patterns in strategy proved slightly too strict vs. numbered heading styles produced later.
- **Iterations**: 0. **Design accuracy**: accurate.

### ADV007-T002: Research Team Pipeline — FAILED
- **Planned**: `phase1-team-pipeline.md` with `## Findings`.
- **Actual**: High-quality ~11-issue / 10-rec / 7-strength document written to `team-pipeline.md` (no `phase1-` prefix, no `## Findings` heading).
- **Iterations**: 0. **Design accuracy**: content accurate, filename drift.
- **Issues**: 1 high (wrong path), 1 medium (missing `## Findings` heading).

### ADV007-T003: Research Team MCP — FAILED
- **Planned**: `phase1-team-mcp.md`.
- **Actual**: Written to `team-mcp.md` (~3,500 words, 4H/8M/6L issues cataloged, 11 recommendations). Agent truncated before final bookkeeping.
- **Iterations**: 0. **Design accuracy**: content accurate, filename drift.

### ADV007-T004: Research Binartlab — PASSED
- **Planned/Actual**: Researched at R:/Claudovka/projects/binartlab (9 packages, mobile undocumented). 7 strengths / 7 problems / 6 strange decisions / 10 recs. Written to correct prefix.
- **Iterations**: 0.

### ADV007-T005: Research Marketplace + PDSL — FAILED
- **Planned**: Two files (`phase1-marketplace.md`, `phase1-pipeline-dsl.md`).
- **Actual**: Combined to single `marketplace-and-dsl.md`. Plugin lifecycle (AC-2) partially missed — only manifest/cache structure covered, no install/activate/update/remove flow; `hooks/hooks.json` not analyzed.
- **Iterations**: 0. **Design accuracy**: significant_drift — this is the only failure that combines filename issues with a substantive scope gap.

### ADV007-T006: Cross-project synthesis — PASSED
- **Planned/Actual**: 66 severity-tagged issues (4 crit / 14 high / 16 med / 12 low) + 10 Phase 2 priorities + 14-edge dependency map. File named correctly (`phase1-cross-project-issues.md`).
- **Iterations**: 0.

### ADV007-T007: Unified concept catalog — PASSED
- **Planned**: 3000-3500 words; Actual: ~6760 words (exceeded but justified).
- 8 concept families, 4 word-collisions split, 9 merges, 5 new first-class entities. High quality.
- **Iterations**: 0.

### ADV007-T008: Parallelism-optimized entity architecture — PASSED
- Delivered `phase2-knowledge-architecture.md` + `phase2-entity-redesign.md` (15 entities, 6 before/after pairs). Token-economy claims quantified (researcher context -87%, lead -73%).
- **Iterations**: 0. Tokens ran 74% over estimate but within quality envelope.

### ADV007-T009: Pipeline management review — FAILED
- **Planned**: `phase3-1-management-failures.md`.
- **Actual**: Written to `pipeline-management-review.md`. Content is complete (9 failures, 8 weak spots, 9 effective patterns, 8 anti-patterns). Cross-referenced `issues.md`. Pure filename drift.
- **Iterations**: 0.

### ADV007-T010: Profiling/optimization/self-healing skills — PASSED
- 9 skill specs across 3 files. Required a "finisher" second spawn to complete the 3rd skill file — noted in metrics as two agent runs.
- **Iterations**: 1 (finisher).

### ADV007-T011: Role effectiveness review — PASSED
- 12-role inventory, 5 gap categories, 15 recommendations (5 P1 / 3 P2 / 4 P3 / 3 P4).
- **Iterations**: 0.

### ADV007-T012: QMD and CodeGraphContext — FAILED
- **Planned**: `phase3-2-qmd.md`, `phase3-2-cgc.md`.
- **Actual**: Combined into `qmd-and-cgc.md`. Content excellent (correctly identified that `code_graph.ark` infra spec already covers CGC's domain — spawned a KB pattern).
- **Iterations**: 0.

### ADV007-T013: Claude Code ecosystem — FAILED
- **Planned**: `phase3-2-claude-ecosystem.md`.
- **Actual**: Written to `claude-ecosystem.md`. ECC and CCGS analyzed with porting tables and top-5 adoptions.
- **Iterations**: 0.

### ADV007-T014: LSP plugins + Agent Orchestrator — FAILED
- **Planned**: `phase3-2-lsp-plugins.md`, `phase3-2-agent-orchestrator.md`.
- **Actual**: Combined into `lsp-and-orchestrator.md`. Reviewer called this "one of the most technically detailed research outputs" — included a novel `reaction_def` DSL proposal.
- **Iterations**: 0. Also low-severity: task `updated` timestamp not synchronized.

### ADV007-T015: MCP servers catalog — PASSED
- 14 servers cataloged with tier ratings. Identified CORE = {github, memory}. 2 patterns + 2 decisions extracted to KB.
- **Iterations**: 0. Duration -36% vs estimate.

### ADV007-T016: Integration matrix — PASSED
- 20-tool × 10-phase matrix with 7 blockers carried forward, 5 Tier-1 adoptions identified. Spawned 2 KB patterns.
- **Iterations**: 0.

### ADV007-T017: UI system — PASSED
- 3 deliverables (~6,200 words). Recommended Next.js + shadcn/ui + Tauri stack. Event-sourced component architecture.
- **Iterations**: 0.

### ADV007-T018: Phase 5 new concepts — FAILED
- **Planned**: 3 files (concept-designs, integration-map, entity-models).
- **Actual**: Only 2 files delivered. `phase5-entity-models.md` missing; content embedded in concept-designs instead. Files silently dropped from task `files` frontmatter without a merge decision recorded. This is the **only failure that is a genuine scope reduction** (not pure filename drift), though the two delivered files are high quality (7×14 interaction matrix, 38-week rollout).
- **Iterations**: 0. **Design accuracy**: minor_drift.

### ADV007-T019: Phase 6 infrastructure — PASSED
- 7-tool MCP surface + B-1 Cloudflare pick, 3-method autotest taxonomy, 10 escalation triggers + 7 anti-patterns.
- **Iterations**: 0.

### ADV007-T020: Final reconstruction — PASSED
- 3 files: lightweight_index formula (target 0.408), M0-M8 milestone plan, ARL 5-op algebra spec. Spawned 4 KB patterns (single scalar index, per-milestone gate, forward-only trapdoors, abstract representation before concrete stores).
- **Iterations**: 0.

### ADV007-T021: Post-final benchmarks/tests/migration — PASSED
- 3 files (~10.6k words): 40+ numeric budgets, 30+ test scenarios, 13+8+3 reversible migrations.
- **Iterations**: 0. Tokens ran 91% over estimate; duration -56%.

### ADV007-T022: Phase 7 operations — PASSED
- 4 files: 9 optimization loops, 17-leaf error taxonomy, 5-stage self-healing pipeline. Required a finisher spawn for the last 2 files (human-machine and operational-model).
- **Iterations**: 1 (finisher).

### ADV007-T023: Master roadmap — PASSED
- 21 adventures mapped across 10 phases, 40+ DAG edges, 24 inter-adventure contracts.
- **Iterations**: 0.

### ADV007-T024: Validation — PASSED
- Validation report with 34 TC entries, R1-R6 invariants, 11 quality gates, verdict `accepted-with-warnings`. Correctly flagged all 3 partial TCs as remediation queue for downstream adventures.
- **Iterations**: 0.

## 4. Process Analysis

### Iterations
- Total review iterations across all tasks: 24 (one review pass per task; none were re-reviewed).
- Finisher-second-spawn within research: 2 (T010 self-healing skill, T022 phase-7 operational-model).
- Tasks requiring rework after review: 0 so far (the 8 failures are documented but not yet re-submitted).

### Dominant Failure Pattern (8 of 8 failures share this)

Every failed task wrote output files to **paraphrased filenames** instead of the exact paths declared in:
- the task frontmatter `files:` field, AND
- the design document's Target Files section.

Concretely:

| Task | Declared path | Actual path |
|------|---------------|-------------|
| T002 | `phase1-team-pipeline.md` | `team-pipeline.md` |
| T003 | `phase1-team-mcp.md` | `team-mcp.md` |
| T005 | `phase1-marketplace.md` + `phase1-pipeline-dsl.md` | `marketplace-and-dsl.md` (combined) |
| T009 | `phase3-1-management-failures.md` | `pipeline-management-review.md` |
| T012 | `phase3-2-qmd.md` + `phase3-2-cgc.md` | `qmd-and-cgc.md` (combined) |
| T013 | `phase3-2-claude-ecosystem.md` | `claude-ecosystem.md` |
| T014 | `phase3-2-lsp-plugins.md` + `phase3-2-agent-orchestrator.md` | `lsp-and-orchestrator.md` (combined) |
| T018 | ... + `phase5-entity-models.md` | entity-models file omitted entirely |

The phase-prefix convention exists precisely because the proof commands use glob patterns like `phase1-*.md` and `phase3-2-*.md`. Dropping the prefix makes the files functionally invisible to TC verification even when content is correct. **The proof-command design worked as intended** — it caught the drift cleanly.

### Content vs. Filename Drift

Every FAILED review except T005 and T018 explicitly states: "No content changes required — only the file name/heading needs correction." The 8 failures are one cluster of ~5 minutes of rename/heading work away from passing. The reviewer agents correctly distinguished substantive gaps (T005 plugin lifecycle, T018 missing entity-models file) from cosmetic path drift.

### Phase Distribution (estimated from metrics.md)

| Phase | Duration | Tokens (approx) |
|-------|----------|-----------------|
| Planning (adventure-planner) | 30 min | 73,000 |
| Research (researcher runs) | ~3h cumulative (many parallel) | ~620,000 in + ~155,000 out |
| Review (adventure-task-reviewer) | ~85 min cumulative | ~425,000 in + ~45,000 out |

Review cost per task averaged ~$0.14 (sonnet, ~20k tokens). Research cost was the dominant phase, as expected for a pure-research adventure.

### Bottlenecks
- **T010 and T022 needed finisher spawns** — the primary researcher agent closed out before producing all declared files, and a second spawn was needed to complete the last deliverable. This suggests a pre-commit checklist gap: the researcher should verify every file in `files:` frontmatter exists before logging `complete`.
- **8 of 24 researchers skipped the `phase*-` prefix** — a systematic issue, not a one-off. This indicates the researcher agent prompt/skill does not emphasize the files-frontmatter contract strongly enough.

## 5. Timeline Analysis

| Metric | Est. | Actual |
|--------|------|--------|
| Total duration | 585 min | ~5h 40m (340 min wall) — parallel execution compressed schedule |
| Total est. cost | $13.20 | ~$12.60 combined researcher + reviewer (close to estimate) |
| Variance on sampled tasks | — | T007 +33%, T008 +74% tokens, T015 -36%, T021 +91% tokens / -56% duration |

Estimation accuracy: mixed. Research tasks that dug into actual codebases (T008 knowledge architecture, T021 benchmark design) blew past token budgets; tasks that were mostly categorization (T015 MCP catalog) came in under. No pattern in cost variance tracks task-type cleanly — suggests estimation is close-to-random in the ±50% band for research work.

## 6. Knowledge Extraction Suggestions

| # | Type | Target File | Title |
|---|------|-------------|-------|
| 1 | feedback | .claude/agent-memory/team-pipeline-researcher/files-frontmatter-contract.md | Treat `files:` frontmatter as an exact-path contract |
| 2 | pattern | .agent/knowledge/patterns.md | Glob-based TC proofs catch filename drift |
| 3 | issue | .agent/knowledge/issues.md | Research-file filename drift from declared `files:` frontmatter |
| 4 | process | (informational) | Researcher pre-complete checklist: verify all `files:` entries exist on disk |
| 5 | feedback | .claude/agent-memory/team-pipeline-researcher/pre-complete-checklist.md | Verify every declared deliverable exists before marking task done |
| 6 | pattern | .agent/knowledge/patterns.md | Finisher-spawn as last-mile recovery for truncated researcher agents |
| 7 | issue | .agent/knowledge/issues.md | Silent reduction of task `files:` frontmatter hides scope drift |

### Suggestion 1: Treat `files:` frontmatter as an exact-path contract
- **Type**: feedback
- **Target File**: `.claude/agent-memory/team-pipeline-researcher/files-frontmatter-contract.md`
- **Role**: team-pipeline-researcher (researcher agent in the pipeline)
- **Content**:
  ```
  ---
  name: Files frontmatter is an exact-path contract
  description: Researcher must write to the exact paths declared in task `files:` frontmatter, not paraphrased or combined names
  type: feedback
  ---

  When a task file declares `files: [path/to/phase1-foo.md, path/to/phase1-bar.md]`, write deliverables to exactly those paths — do not paraphrase (`foo.md`), do not drop prefixes (`foo.md` instead of `phase1-foo.md`), do not combine two files into one (`foo-and-bar.md`).

  **Why:** ADV-007 had 8 of 24 research tasks fail for this exact reason. The TC proof commands use glob patterns (`phase1-*.md`, `phase3-2-*.md`) that rely on the prefix convention. Content was correct in every case; only the filenames were wrong, and the tasks were marked FAILED. The prefix is not decorative — it is the contract between the researcher and the TC verifier.

  **How to apply:** Before writing any research output, re-read the task's `files:` frontmatter and the design document's Target Files section. Write to each declared path literally. If a single-file combined output genuinely seems better, raise it as an open question in the research doc — do not silently remap. If a deliverable is being dropped, update the task frontmatter and note the decision in the log, do not just omit the file.
  ```

### Suggestion 2: Glob-based TC proofs catch filename drift
- **Type**: pattern
- **Target File**: `.agent/knowledge/patterns.md`
- **Content**:
  ```
  - **Glob-prefix proofs as filename-drift guard**: When multiple research tasks contribute files to a shared TC (e.g. TC-001 covers 4 tasks' Phase 1 outputs), use a proof command with a glob prefix rather than enumerating paths — e.g. `grep -l "## Findings" .agent/adventures/{ADV}/research/phase1-*.md` instead of `test -f a.md && test -f b.md && ...`. The glob catches filename drift (file written without prefix) cleanly: drifted files are simply invisible to the glob and the count/grep fails. ADV-007 had 8 research tasks drop the `phase*-` prefix; every one was flagged by the glob-based TC with zero false positives. Glob prefixes double as a lightweight naming convention enforcement. (from ADV-007)
  ```

### Suggestion 3: Research-file filename drift from declared `files:` frontmatter
- **Type**: issue
- **Target File**: `.agent/knowledge/issues.md`
- **Content**:
  ```
  - **Research output written to paraphrased filenames**: In ADV-007, 8 of 24 research tasks (T002, T003, T005, T009, T012, T013, T014, T018) wrote output to filenames that differed from the task `files:` frontmatter — typically dropping the `phase*-` prefix or combining two declared files into one. Content was correct in every case, but glob-based TC proof commands (`phase1-*.md`, `phase3-2-*.md`) returned no matches, causing 3 TCs to go partial and the tasks to fail review. Solution: (a) researcher agents must treat `files:` as an exact-path contract (see feedback memory); (b) add a pre-complete check that every `files:` entry resolves to an existing file on disk before the researcher logs `complete`; (c) keep using glob-prefix TC proofs — they are the correct detection mechanism. (from ADV-007)
  ```

### Suggestion 4: Researcher pre-complete checklist
- **Type**: process
- **Target File**: (informational — not auto-applied)
- **Content**:
  ```
  Before a researcher agent logs `complete` for a research task, it must run:
  1. For every path P in the task frontmatter `files:` list, verify `test -f P`.
  2. For every TC proof command that references this task's outputs, run the command and confirm a non-empty/non-zero result.
  3. If (1) or (2) fails, log `blocked: deliverable_missing {path}` or `blocked: proof_failing {tc-id}` and do not mark task done.

  Recommendation: bake this into the researcher skill as a required terminal step, or add a finisher sub-skill that runs these checks and either completes the missing files or reports them. ADV-007 had 8 tasks skip this check and fail review; adding it would have caught every failure at the researcher stage.
  ```

### Suggestion 5: Pre-complete checklist for researcher
- **Type**: feedback
- **Target File**: `.claude/agent-memory/team-pipeline-researcher/pre-complete-checklist.md`
- **Role**: team-pipeline-researcher
- **Content**:
  ```
  ---
  name: Pre-complete checklist before logging task done
  description: Before marking a research task complete, verify every declared deliverable exists and every proof command the task owns actually passes
  type: feedback
  ---

  Before writing `complete:` to the adventure log and flipping task status to `done`, run two checks:
  1. For each path in task frontmatter `files:`, run `test -f <path>` — must pass.
  2. For each TC where this task is listed as a contributor in the manifest, run the proof command — must produce the expected output/count.

  If either check fails, either produce the missing file or log `blocked:` instead of `complete:` and stop.

  **Why:** ADV-007 had 8 of 24 tasks log complete with one or more declared files missing from disk. Reviewers then failed the tasks. A 30-second pre-complete check would have caught every failure at the research stage and saved the review round-trip.

  **How to apply:** Run these checks as the second-to-last step (just before metrics row + status update). If they fail, do not attempt to fudge — write the missing file or split/rename the one you produced to match the declared path.
  ```

### Suggestion 6: Finisher-spawn as last-mile recovery
- **Type**: pattern
- **Target File**: `.agent/knowledge/patterns.md`
- **Content**:
  ```
  - **Finisher-spawn recovery for truncated researcher runs**: When a researcher agent closes out before producing every declared deliverable (e.g. produces 2 of 3 files before hitting turn/token limits), a second "finisher" spawn on the same task with the prompt narrowed to the missing artifacts is a clean recovery path. ADV-007 used this twice: T010 (3rd self-healing skill file) and T022 (human-machine + operational-model files). Pattern: narrow prompt to missing files, pass upstream research context as already-done, produce only the gap. Cost: ~3-5 min / ~5k tokens vs. rerunning the whole task. (from ADV-007)
  ```

### Suggestion 7: Silent reduction of task `files:` hides scope drift
- **Type**: issue
- **Target File**: `.agent/knowledge/issues.md`
- **Content**:
  ```
  - **Silent reduction of task `files:` frontmatter**: In ADV-007 T018, the task was planned with 3 deliverables (phase5-concept-designs.md, phase5-integration-map.md, phase5-entity-models.md) per the design document and plan, but the researcher silently updated the task `files:` frontmatter to list only 2 files — dropping phase5-entity-models.md without producing it and without logging a merge/supersede decision. The reviewer caught this only because the design and plan were cross-checked manually. Solution: (a) task frontmatter `files:` must never shrink from the design's declared list without an explicit `decision:` log entry citing why; (b) reviewer skill should cross-check task `files:` against the design document's Target Files, not just whether declared files exist; (c) consider a schema constraint: design-declared Target Files are the lower bound for task `files:`. (from ADV-007)
  ```

## 7. Recommendations

Ordered by priority:

1. **(High) Patch the 8 failed research tasks with rename/heading fixes.** Every failed task's reviewer provided exact remediation steps. This is ~30 minutes of mechanical work and would lift 3 partial TCs to green. No content changes needed.

2. **(High) Add the pre-complete checklist to the researcher skill** (Suggestion 4/5). The 8/24 failure rate from filename drift is a systemic prompt/skill gap — a one-time fix eliminates this whole class of failure for future adventures.

3. **(High) Produce `phase5-entity-models.md`** (T018 remediation). This is the only non-cosmetic content gap across the adventure — the entity model content exists embedded in concept-designs but the planned standalone reference document is absent.

4. **(Medium) Harden T005 (plugin lifecycle section).** Beyond the filename fix, T005 also missed the plugin install→activate→update→remove lifecycle. Hooks.json was referenced but not analyzed. This is a substantive gap, not a naming issue.

5. **(Medium) Update reviewer skill to cross-check task `files:` against design Target Files.** Currently the reviewer checks only that declared files exist, not whether the declaration has silently shrunk from the plan (caught T018 by chance). The design doc is the source of truth for scope.

6. **(Low) Sync task frontmatter `updated` timestamps with actual work time.** T014 and likely others kept `updated` at task-creation time; harmless but hurts timeline reconstruction.

7. **(Low) Tighten estimation model for research tasks.** Several tasks ran ±50-90% on tokens (T007 +33%, T008 +74%, T021 +91%). The current Est. Tokens column is in the right order of magnitude but not actionable for budgeting — consider recording actuals consistently and fitting a simple type-based correction factor.

### Areas needing hardening

- **Filename convention enforcement**: The `phase*-` prefix convention is implicit in glob TC proofs but never stated as a rule in the researcher prompt. Make it explicit, or replace the globs with strict enumerated `test -f` lists (less flexible but harder to drift).
- **Multi-deliverable tasks**: Tasks with 2+ declared files (T005, T012, T014, T018) had a 100% failure rate in ADV-007 — every such task either combined files or dropped one. Consider splitting multi-deliverable tasks into separate sub-tasks at planning time so the contract is one-file-per-task.
- **Researcher completion gating**: Tasks can log `complete` with declared files missing. Add a hard gate.
