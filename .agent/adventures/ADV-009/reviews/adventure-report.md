---
adventure_id: ADV-009
generated_at: 2026-04-18T00:00:10Z
task_count: 21
tc_total: 61
tc_passed: 61
tc_pass_rate: "100%"
total_iterations: 0
knowledge_suggestions_count: 8
---

# Adventure Report: ADV-009

## 1. Executive Summary

| Field | Value |
|-------|-------|
| Adventure | ADV-009 |
| Title | Adventure Console UI v2 — Simple, Reader-First Layout |
| Duration | 2026-04-14T21:36Z → 2026-04-18T00:00Z (~3.1 days wall) |
| Total Cost | ~$3.10 (estimated from metrics; opus planners + sonnet implementers/reviewers) |
| Tasks | 21 / 21 complete |
| TC Pass Rate | 61 / 61 (100%) |

ADV-009 delivered a full v2 rewrite of the Adventure Console: a simpler, reader-first
HTML/JS UI (4-tab collapsed-from-9 layout plus a 5th Pipeline tab added by addendum),
a custom-per-type document renderer, an Overview with TC progress bars and a
state-driven next-action card, a cytoscape-based live Pipeline graph with drag-to-wire
editing, three stdlib-only backend endpoints (`/summary`, `/documents`, `/graph`,
`POST .../depends_on`), a sibling `adventure_pipeline/` package providing the Ark
representation (entities/processes/runtime specs + IR extractor + Python adapter),
optional verifier passes, and a 79-test stdlib `unittest` suite. Every one of the 21
tasks passed review on the first cycle; every target condition passes or has a
documented deferral. The adventure nevertheless surfaces several high-quality
process signals worth extracting into the shared knowledge base.

## 2. Target Conditions Analysis

All 61 TCs resolved PASS (or PASS-with-documented-deferral for TC-045). Grouped summary:

| Group | Range | Result | Notes |
|-------|-------|--------|-------|
| Audit & research | TC-001..003 | 3/3 PASS | 66 rows, all verdicts valid, all 9 dispatch branches covered |
| Tab bar / header | TC-004..007 | 4/4 PASS | TC-004 "exactly four tabs" *passes against 5 tabs* — test was updated to match addendum; AC wording drift noted |
| Tasks tab | TC-008..012 | 5/5 PASS | Status-bucketed cards; structured Description/AC components; disclosure toggle works |
| Documents tab | TC-013..017 | 5/5 PASS | Chip filter client-side; design header; plan wave groups; review PASS/FAIL strip |
| Overview | TC-018..021 | 4/4 PASS | Progress bar (not table), ≤5 non-passing TCs preview, next-action card, concept disclosure |
| Decisions | TC-022..025 | 4/4 PASS | 3 cards with empty-bucket hiding; state POST; knowledge JSON regression holds |
| Backend | TC-026..030 | 5/5 PASS | `/summary`, `/documents`, next_action dispatch, stdlib-only preserved |
| Visual system | TC-031..033 | 3/3 PASS | .card/.pill/.progress/.chip-bar rules live; no new external deps; all cards use .card |
| Test strategy / harness | TC-034..038 | 5/5 PASS | Strategy maps every autotest TC; discover exits 0; README updated; 5s-glance manual verified |
| Ark spec | TC-039..041 | 3/3 PASS | Three `.ark` files parse cleanly; processes + runtime entities declared |
| IR extractor | TC-042..044 | 3/3 PASS | ADV-007 → 24 tasks/84 docs/34 tcs/33 perms; ADV-008 populated; task ID sets match manifest |
| Verifier | TC-045 | 1/1 PASS (deferral) | 3 spec files verify clean at class/temporal level; standalone `verify{}` blocks documented as Ark-level deferral |
| Graph endpoint | TC-046, TC-052..054, TC-058..061 | 7/7 PASS | nodes/edges/explanations shape; depends_on happy + self-cycle + transitive-cycle; cycle-free helper; stdlib-only |
| Pipeline tab | TC-047..051, TC-055..057 | 8/8 PASS | CDN cytoscape; 5-tab ordering; status colours; setTimeout polling (no WS); tooltips from backend; drag emits one POST; rollback on 4xx; context menu allowlisted |

**Overall assessment**: all target conditions met. The only partial is TC-045 where
standalone `verify {}` block dispatch in the Ark verifier is documented as a deferral
rather than achieved — this is an Ark core limitation and was explicitly scoped as
deferrable by the plan.

## 3. Task Review Synthesis

### ADV009-T001: Design test strategy for ADV-009 console v2
- **Planned**: stdlib `unittest`, 3 test files + extensions, `data-testid` appendix
- **Actual**: doc maps all 52 autotest TCs; 24 testids documented; Playwright skip-guard pattern spelled out verbatim
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0

### ADV009-T002: Simplification audit of the current console
- **Planned**: ~40 audit rows covering each UI element with keep/hide/remove verdicts
- **Actual**: 66 rows delivered (well above ≥30 minimum); all 9 dispatch branches covered; 5 open questions flagged for downstream reconciliation
- **Iterations**: 0
- **Design Accuracy**: accurate — exceeded minimum with generous headroom
- **Issues Found**: 0

### ADV009-T003: Implement `/summary` endpoint + `compute_next_action`
- **Planned**: pure helper mapping (state, permissions.status) → {kind, label, state_hint}
- **Actual**: helper shipped module-level, 6-state dispatch working, stdlib-only preserved
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0

### ADV009-T004: Implement `/documents` endpoint with plan-wave detection
- **Planned**: unified doc list with type tag + wave count regex on `## Wave N`
- **Actual**: all doc types returned with correct typing; wave detection works
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0

### ADV009-T005: Visual system (.card/.pill/.progress/.chip-bar/.stack/.disclosure)
- **Planned**: stdlib-only CSS rules; no new external deps
- **Actual**: rules landed; marked.js remains sole external dep
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0

### ADV009-T006: Rebuild tab bar and header to v2 shape
- **Planned**: exactly four tabs; header with ID/title/state/TC progress/CTA
- **Actual**: five tabs rendered (Pipeline added per addendum); header shape matches design; CTA_TAB_MAP covers four next-action kinds + unknown fallback
- **Iterations**: 0
- **Design Accuracy**: minor_drift (task AC-1 says "four", addendum made it five; tests updated, AC text did not)
- **Issues Found**: 1 (low, cosmetic AC wording drift)

### ADV009-T007: Implement Overview tab
- **Planned**: progress bar, ≤5 non-passing TC preview, state-driven next-action card, hidden concept
- **Actual**: all six ACs met cleanly; `deriveSummary`/`deriveNextAction` fallbacks keep Overview functional even when T003 `summary` block is absent
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0 (recommendations flagged duplicate `tc-progress-bar` testid at header and Overview — not a defect, but a live-DOM-test hazard)

### ADV009-T008: Tasks tab cards + detail panel
- **Planned**: status-bucketed cards; structured AC/Description; disclosure for raw content
- **Actual**: all ACs met; TC checklist reflects manifest status
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0

### ADV009-T009: Documents tab with chip filter + custom layouts
- **Planned**: chip filter bar; client-side filtering; design header; plan wave groups; review strip
- **Actual**: all five ACs met
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0

### ADV009-T010: Decisions tab (3 cards)
- **Planned**: Permissions / Knowledge / State transitions; empty buckets hidden
- **Actual**: three cards with proper gating; state-transition POST wired; knowledge JSON unchanged (regression TC-025 holds)
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0

### ADV009-T011: Remove legacy tabs from rendering
- **Planned**: purge Log/Knowledge/Permissions/Designs/Plans/Research/Reviews dispatch paths
- **Actual**: all legacy labels absent; TC-005 regression passes
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0

### ADV009-T012: Implement stdlib `unittest` harness
- **Planned**: test_server.py, test_ui_smoke.py, test_ui_layout.py; Playwright skip-gate
- **Actual**: full harness landed; discover exits 0; 79 passed / 8 skipped (all Playwright-gated skips)
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0

### ADV009-T013: 5-second-glance manual verification
- **Planned**: open console, time how fast state/blocker/action are visible on ADV-007 and ADV-008
- **Actual**: verification report written; both adventures passed the 5-second-glance test
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0

### ADV009-T014: README update for v2
- **Planned**: document four v2 tabs + new endpoint
- **Actual**: README reflects current tab set and endpoints; diff minimal
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0

### ADV009-T015: Author Ark pipeline spec files (entities + processes + runtime)
- **Planned**: adventure.ark / pipeline.ark / entities.ark parse cleanly under vanilla Ark
- **Actual**: all three parse; 11 entities + 7 enums in adventure.ark, 3 processes in pipeline.ark, 5 runtime entities in entities.ark; ark/ untouched
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 1 (low, manifest proof commands for TC-040/TC-041 use leading-dot dotted path that fails Python's `-m unittest` CLI)

### ADV009-T016: IR extractor (live adventure dir → populated IR)
- **Planned**: Python stdlib extractor; dataclasses; regex + markdown parsing
- **Actual**: `python -m adventure_pipeline.tools <ADV-ID>` works; ADV-007 → 24/84/34/33 (tasks/docs/tcs/perms); ADV-008 populated; task IDs match manifest
- **Iterations**: 0
- **Design Accuracy**: minor_drift (task wording says `.tools.ir` submodule CLI; implementation exposes `.tools` via `__main__.py` — equivalent via package entry point)
- **Issues Found**: 0

### ADV009-T017: Wire optional verifier passes (mark deferrable)
- **Planned**: three verify files (state_transitions / permission_coverage / tc_traceability) — clean or documented deferral
- **Actual**: all three exit 0 at class/temporal level; standalone `verify {}` block checks documented in README § "Deferred invariants" with file+invariant+rationale; ark/ untouched
- **Iterations**: 0
- **Design Accuracy**: accurate — implementer correctly refused to patch ark/ and documented the verifier dispatch limitation instead
- **Issues Found**: 0

### ADV009-T018: Graph endpoint + depends_on POST + _cycle_free helper
- **Planned**: stdlib HTTP; graph payload {nodes, edges, explanations}; cycle detection
- **Actual**: all ACs met; direct + transitive cycles rejected with 400; stdlib-only preserved; server.py imports `adventure_pipeline.tools.ir`
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0

### ADV009-T019: Pipeline tab rendering (cytoscape + polling)
- **Planned**: CDN cytoscape, setTimeout polling, no WebSocket/EventSource, tooltips from backend
- **Actual**: all six ACs met; polling timer cleared on every exit path (tab switch / adventure switch / detail refresh); `queueMicrotask` deferral for canvas mount
- **Iterations**: 0
- **Design Accuracy**: minor_drift (design specified `nodeStyleFor(kind, status)` helper; implementation consolidated into `buildCyStyle(colours)` — sound cytoscape-idiomatic choice)
- **Issues Found**: 0

### ADV009-T020: Graph edit affordances (drag-to-wire, context menu, rollback)
- **Planned**: drag emits exactly one POST; 4xx rolls back optimistic edge; context-menu routes only to allowlisted endpoints
- **Actual**: all three ACs met
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0

### ADV009-T021: Automated tests for Pipeline + IR extractor
- **Planned**: stdlib unittest; per-TC mapping; discover exits 0
- **Actual**: 79 passed / 8 skipped; every autotest TC from TC-039..TC-061 has a named test function; ast-walk confirms stdlib-only imports
- **Iterations**: 0
- **Design Accuracy**: accurate
- **Issues Found**: 0 (recommendations: `TestDependsOn` writes a synthetic `ADV-998` under real `.agent/adventures/` because `extract_ir()` has a hardcoded root — acceptable pragmatic workaround with cleanup)

**Tasks needing multiple review cycles**: none. Every task passed on first review.

## 4. Process Analysis

### Iterations
- Total review-cycle iterations across all tasks: **0**
- Tasks requiring 0 iterations: all 21
- Tasks requiring 1+ iterations: none

This is unusually clean. Contributing factors: exhaustive design phase before coding
(22 design docs across the adventure), clear TC→test function mapping in the test
strategy, stdlib-only constraint reducing dependency risk, and small per-task scope
(all at or under the 30min/100k token thresholds).

### Common Issue Patterns
- **Manifest proof-command drift** (TC-040, TC-041, TC-002, TC-042..044 mentions):
  proof commands written as `python -m unittest .agent.adventures.ADV-009.tests.X`
  fail because (a) leading `.` is not a valid module path and (b) `ADV-009` contains a
  hyphen which is illegal in Python package names. Reviewers reliably caught and
  worked around via `discover -s ... -p ...`. Observed in reviews: T002, T015, T021.
- **AC wording drift after addendum** (T006): task AC said "exactly four tabs"; the
  addendum (documented in manifest) added Pipeline as 5th tab; tests were updated,
  task AC text was not, producing a cosmetic flag in review. Observed: T006.
- **CTA routing divergence for `open_plan`** (T006 vs T007): the header CTA map
  (T006) routes `open_plan` via `CTA_TAB_MAP` — T006 AC-6 explicitly says
  "Tasks for `open_plan`"; the Overview next-action card (T007 AC-7 comment)
  routes `open_plan` / `open_report` through `switchTab('documents')`. Both tasks
  passed review, but the two CTAs land on different tabs for the same next_action
  kind. Observed: T006, T007.
- **Vanilla Ark verifier dispatch limitation** (T015, T017): standalone top-level
  `verify { check ... }` blocks are not dispatched by `verify_file()` — only
  abstraction / class / island items are. Correctly handled as documented deferral
  rather than Ark-core patch. Observed: T015, T017.

### Phase Distribution (estimated from metrics.md)
| Phase | Tokens (in+out) | Share |
|-------|-----------------|-------|
| Planning (planner runs) | ~475k | ~27% |
| Implementing | ~1,100k | ~64% |
| Reviewing | ~165k | ~9% |

Implementation dominates token spend; review is lean precisely because nothing
needed re-review.

### Bottlenecks
- **T012, T019, T021** sat at the 30-minute / ~95k-token ceiling — the testing and
  pipeline-visualization tasks were the largest. All three finished within budget
  but represent the upper bound of per-task scope for this kind of adventure.
- **T019 took 12 implementer turns** (tied for highest, with T012). Cytoscape
  integration involved layout, status-colour mapping, polling lifecycle, and
  tooltip wiring — worth watching if future visualization work grows.

## 5. Timeline Analysis

| Task | Est. Duration | Impl. Duration (metrics) | Delta |
|------|---------------|--------------------------|-------|
| T001 | 12 min | ~8 min | -33% |
| T002 | 20 min | ~10 min | -50% |
| T003 | 18 min | ~8 min | -56% |
| T004 | 20 min | ~8 min | -60% |
| T005 | 12 min | ~5 min | -58% |
| T006 | 25 min | ~10 min | -60% |
| T007 | 22 min | ~8 min | -64% |
| T008 | 28 min | ~12 min | -57% |
| T009 | 28 min | ~15 min | -46% |
| T010 | 22 min | ~10 min | -55% |
| T011 | 15 min | ~8 min | -47% |
| T012 | 28 min | ~15 min | -46% |
| T013 | 12 min | ~10 min | -17% |
| T014 | 8 min | ~4 min | -50% |
| T015 | 25 min | ~20 min | -20% |
| T016 | 28 min | ~10 min | -64% |
| T017 | 18 min | ~8 min | -56% |
| T018 | 28 min | ~12 min | -57% |
| T019 | 30 min | ~15 min | -50% |
| T020 | 28 min | ~12 min | -57% |
| T021 | 30 min | ~90 sec reviewer + ~impl not listed | review fast, impl missing from metrics row |

**Observation**: actual durations ran **~50% under estimates** across the board —
the estimator was consistently conservative. For a 21-task adventure with stdlib-only
constraints and well-scoped per-task designs, the model is overestimating by roughly
2×. Estimation calibration is a worthwhile process adjustment.

## 6. Knowledge Extraction Suggestions

| # | Type | Target File | Title |
|---|------|-------------|-------|
| 1 | pattern | .agent/knowledge/patterns.md | Stdlib-only-Python constraint produces exceptional first-pass review rate |
| 2 | pattern | .agent/knowledge/patterns.md | Single-file `index.html` + CDN libraries keeps console build-free |
| 3 | pattern | .agent/knowledge/patterns.md | Wave-based task dispatch with documented deferrals preserves Ark-core cleanliness |
| 4 | issue | .agent/knowledge/issues.md | Manifest proof commands with leading-dot module paths fail Python CLI |
| 5 | issue | .agent/knowledge/issues.md | Hyphenated adventure IDs (`ADV-009`) are illegal in Python module paths |
| 6 | issue | .agent/knowledge/issues.md | Vanilla Ark verifier does not dispatch standalone `verify{}` blocks |
| 7 | feedback | .claude/agent-memory/team-pipeline-adventure-planner/addendum-consistency.md | Update task AC text when adventure scope changes via addendum |
| 8 | process | (informational) | Calibrate duration estimator — ADV-009 ran ~50% under estimate |

### Suggestion 1: Stdlib-only-Python constraint produces exceptional first-pass review rate
- **Type**: pattern
- **Target File**: `.agent/knowledge/patterns.md`
- **Content**:
  ```
  - **Stdlib-only Python + CDN-only JS for tools**: Constraining ancillary tooling
    (server.py, IR extractor, test harness) to Python stdlib and limiting the
    browser side to CDN-loaded libraries eliminates an entire class of
    environment/dependency failures, enables ast-walk verifiability of the
    constraint itself, and correlates strongly with first-pass review success
    (ADV-009: 21/21 tasks passed review on first cycle).
  ```

### Suggestion 2: Single-file index.html + CDN libraries keeps console build-free
- **Type**: pattern
- **Target File**: `.agent/knowledge/patterns.md`
- **Content**:
  ```
  - **Build-free frontend via single-file index.html**: Keep
    `.agent/adventure-console/index.html` self-contained, load external libraries
    (marked.js, cytoscape.js) from CDN `<script>` tags, ship no bundler. Testable
    via a single static-source grep (`TestCdn`, `TestNoExternal`). Scales through
    at least a 2000+ line, cytoscape-driven Pipeline tab without pressure to
    introduce a build step (from ADV-009).
  ```

### Suggestion 3: Wave-based task dispatch with documented deferrals preserves Ark-core cleanliness
- **Type**: pattern
- **Target File**: `.agent/knowledge/patterns.md`
- **Content**:
  ```
  - **Wave dispatch + documented deferrals over core patches**: When a planned
    verification or feature bumps into a core-tool limitation (e.g., vanilla Ark
    verifier not dispatching standalone `verify{}` blocks), prefer documenting
    the deferral in the sibling package README with file+invariant+rationale
    over patching the core tool. Keeps `git diff --exit-code ark/` clean as a
    regression gate (ADV-009 T015, T017).
  ```

### Suggestion 4: Manifest proof commands with leading-dot module paths fail Python CLI
- **Type**: issue
- **Target File**: `.agent/knowledge/issues.md`
- **Content**:
  ```
  - **Leading-dot module paths in manifest proof commands**: Writing proof
    commands as `python -m unittest .agent.adventures.ADV-NNN.tests.X` fails
    with `ValueError: Empty module name` because `-m` does not accept a leading
    dot. Solution: author manifest proof commands using the `discover` form
    (`python -m unittest discover -s .agent/adventures/ADV-NNN/tests -p "test_X.py" -k name`)
    which is portable and cross-platform (ADV-009 T002/T015/T021).
  ```

### Suggestion 5: Hyphenated adventure IDs are illegal in Python module paths
- **Type**: issue
- **Target File**: `.agent/knowledge/issues.md`
- **Content**:
  ```
  - **Hyphenated adventure IDs break `-m unittest` dotted paths**: `ADV-009`
    contains a hyphen, which is not allowed in Python package/module names.
    Any manifest command of the form `python -m unittest
    adventures.ADV-009.tests...` will fail even if the leading dot is removed.
    Use `discover -s <path>` with an actual filesystem path, not a dotted module
    path, when the adventure ID has a hyphen (ADV-009 T021 Windows observation).
  ```

### Suggestion 6: Vanilla Ark verifier does not dispatch standalone `verify{}` blocks
- **Type**: issue
- **Target File**: `.agent/knowledge/issues.md`
- **Content**:
  ```
  - **Ark verifier dispatch limited to abstraction/class/island**: `verify_file()`
    in the current vanilla Ark toolchain only dispatches checks attached to
    `abstraction`, `class`, and `island` items; top-level standalone
    `verify { check ... }` blocks parse but are not executed. Workaround:
    attach invariants to the relevant class/abstraction, or document the check
    as a deferral awaiting an Ark extension. Do NOT patch `ark/` from an
    adventure's sibling package (ADV-009 T015/T017).
  ```

### Suggestion 7: Update task AC text when adventure scope changes via addendum
- **Type**: feedback
- **Target File**: `.claude/agent-memory/team-pipeline-adventure-planner/addendum-consistency.md`
- **Role**: adventure-planner
- **Content**:
  ```markdown
  ---
  name: Addendum consistency with task AC text
  description: When an adventure manifest is extended with an addendum that changes scope (added tabs, new TCs, new tasks), retroactively update task AC text in existing task files so reviewers don't flag cosmetic drift.
  type: feedback
  ---

  **Rule**: When an addendum changes scope that affects already-written task files
  (new tab count, altered CTA routing, additional fields), update the affected
  task AC bullets at the same time the addendum is merged.

  **Why**: In ADV-009, the manifest addendum added a 5th Pipeline tab after T006's
  AC had been written saying "exactly four tabs". Tests were updated to match the
  new 5-tab state, but T006's AC text was not. The reviewer correctly passed the
  task (structural intent met) but filed a low-severity flag; this costs review
  attention that should be spent on substantive issues.

  **How to apply**: At addendum-merge time, grep `tasks/` for language affected
  by the scope change (tab counts, endpoint names, tab order) and update AC
  bullets in place. Consider a short "Addendum reconciliation" pass as a
  first-class planner step after any addendum.
  ```

### Suggestion 8: Calibrate duration estimator — ADV-009 ran ~50% under estimate
- **Type**: process
- **Target File**: (informational only — not auto-applied)
- **Content**:
  ```
  ADV-009 per-task actual durations ran consistently ~50% under estimate
  (21 tasks, median ~-55% delta). Proposed process adjustment: re-fit the
  duration estimator for stdlib-only Python + single-file HTML/JS work, or
  document a "conservative by 2x" calibration note so capacity planning isn't
  distorted. Does not affect token budgets (which tracked actuals more closely)
  — specifically a wall-clock estimation correction.
  ```

## 7. Recommendations

High priority:
1. **Reconcile CTA routing for `open_plan`** between the header CTA (T006: routes to
   Tasks) and the Overview next-action card (T007: routes to Documents). Same
   next_action kind should produce the same destination, or the design should
   explicitly distinguish "open the plan document" vs "work the plan tasks" as two
   different kinds. File: `.agent/adventure-console/index.html` — see
   `CTA_TAB_MAP` and `renderNextActionCard`.
2. **Normalize manifest proof-command style** across all adventures: prefer
   `discover -s <path> -p <pattern> -k <testname>` form over dotted module paths.
   This removes Windows/hyphen/leading-dot failure modes in one stroke.
3. **Retroactively fix T006 AC-1 wording** from "exactly four tabs" to "exactly five
   tabs" to match the addendum-ratified current scope, eliminating the cosmetic
   review flag.

Medium priority:
4. **De-duplicate the `tc-progress-bar` data-testid** by scoping the header element
   to `header-tc-progress` (or similar) so future live-DOM tests don't accidentally
   match the Overview card's bar when querying `[data-testid=tc-progress-bar]`.
5. **Promote `TempAdventure` to actually isolate `TestDependsOn`** rather than
   writing synthetic `ADV-998` under real `.agent/adventures/`. Requires
   `extract_ir()` to accept a root override; low churn, high test-hygiene value.

Lower priority:
6. **Document the Ark verifier dispatch limitation in `.agent/knowledge/issues.md`**
   (see Suggestion 6) so the next adventure that authors `verify{}` blocks doesn't
   re-discover it.
7. **Calibrate the duration estimator** — current planner overestimates by ~2×
   for adventures in this class.

Areas needing hardening or refactoring:
- **Ark verifier**: standalone `verify{}` block dispatch is the most impactful
  open item — if extended, three pre-written ADV-009 verify files become runnable
  gates rather than documented deferrals.
- **IR extractor root**: `extract_ir()` currently resolves `.agent/adventures/`
  from a hardcoded root, which forced `TestDependsOn` to write to the real
  directory. Parameterizing the root would tighten test isolation.
- **Estimation calibration**: systematic 2× overestimate on per-task wall time.
