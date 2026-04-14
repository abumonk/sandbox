# Plan: Ark Pipeline Spec + IR Extractor (Wave D — addendum)

This plan is an **extension** of the original ADV-009 plan (Waves A/B/C
remain untouched). It lands in a new Wave D that runs in parallel with
Wave B where possible (no file conflicts — disjoint package), and blocks
Wave E's graph-view backend endpoint.

## Designs Covered

- design-ark-pipeline-spec

## Tasks

### Author Ark pipeline spec files (entities + processes + runtime)
- **ID**: ADV009-T015
- **Description**: Create the sibling package `R:/Sandbox/adventure_pipeline/`
  with `specs/adventure.ark`, `specs/pipeline.ark`, `specs/entities.ark`,
  `specs/verify/state_transitions.ark`, `specs/verify/permission_coverage.ark`,
  `specs/verify/tc_traceability.ark`, plus package `__init__.py` scaffolding
  and a 1-page `README.md`. Ark itself is **not modified**. Use only
  vanilla Ark syntax (abstractions, classes, islands, processes, enums).
  If any intended invariant cannot be expressed, record it in the README
  under "Deferred invariants" — do not patch Ark.
- **Files**:
  - `adventure_pipeline/README.md`
  - `adventure_pipeline/__init__.py`
  - `adventure_pipeline/specs/adventure.ark`
  - `adventure_pipeline/specs/pipeline.ark`
  - `adventure_pipeline/specs/entities.ark`
  - `adventure_pipeline/specs/verify/state_transitions.ark`
  - `adventure_pipeline/specs/verify/permission_coverage.ark`
  - `adventure_pipeline/specs/verify/tc_traceability.ark`
- **Acceptance Criteria**:
  - `python ark/ark.py parse adventure_pipeline/specs/adventure.ark` exits 0.
  - `python ark/ark.py parse adventure_pipeline/specs/pipeline.ark` exits 0.
  - `python ark/ark.py parse adventure_pipeline/specs/entities.ark` exits 0.
  - `adventure.ark` declares: Adventure, Phase, Wave, Task, Document
    (+ Design/Plan/Research/Review subclasses), TargetCondition, Decision,
    Permission, Agent, Role, and the supporting enums.
  - `pipeline.ark` declares processes: AdventureStateMachine,
    TaskLifecycle, ReviewPipeline.
  - `entities.ark` declares: RunningAgent, ActiveTask, PendingDecision,
    KnowledgeSuggestion, ReviewArtifact.
  - No files under `ark/` are modified by this task.
- **Target Conditions**: TC-039, TC-040, TC-041
- **Depends On**: []
- **Evaluation**:
  - Access requirements: Read, Write
  - Skill set: Ark DSL authoring, domain modelling
  - Estimated duration: 25 min
  - Estimated tokens: 60000

### Implement IR extractor (live adventure dir → populated IR)
- **ID**: ADV009-T016
- **Description**: Author `adventure_pipeline/tools/ir.py` and
  `adventure_pipeline/tools/__main__.py`. The extractor reads a live
  `.agent/adventures/ADV-NNN/` directory (manifest frontmatter + TC
  table + `designs/`, `plans/`, `research/`, `reviews/`, `tasks/`,
  `permissions.md`) and returns an `AdventurePipelineIR` dataclass
  mirroring the Ark entity shapes. Stdlib only. Provide `to_json(ir)`
  and a CLI `python -m adventure_pipeline.tools.ir ADV-NNN` that prints
  JSON. Follow the parsing patterns already used by `server.py` (regex
  for frontmatter, markdown-table scan for the TC block).
- **Files**:
  - `adventure_pipeline/tools/__init__.py`
  - `adventure_pipeline/tools/ir.py`
  - `adventure_pipeline/tools/__main__.py`
- **Acceptance Criteria**:
  - `python -m adventure_pipeline.tools.ir ADV-007` exits 0 and prints
    JSON with non-empty `tasks`, `documents`, `tcs`, `permissions`.
  - Same for ADV-008.
  - Every task id emitted matches the manifest `tasks:` frontmatter list.
  - Module uses stdlib only.
- **Target Conditions**: TC-042, TC-043, TC-044
- **Depends On**: [ADV009-T015]
- **Evaluation**:
  - Access requirements: Read, Write, Bash (python CLI)
  - Skill set: Python stdlib, regex, markdown parsing
  - Estimated duration: 28 min
  - Estimated tokens: 85000

### Wire optional verifier passes (mark deferrable)
- **ID**: ADV009-T017
- **Description**: Invoke Ark's existing verifier on the three verifier
  specs. If all three verify clean, the task passes. If any invariant
  cannot be expressed in vanilla Ark, record the gap in
  `adventure_pipeline/README.md` § "Deferred invariants" with a clear
  rationale; the task still passes *iff* every deferral is documented.
  **Under no circumstances should this task patch `ark/`.** If Ark's
  verifier fundamentally cannot model the domain, defer the pass entirely
  — this task is explicitly marked optional/deferrable in the plan.
- **Files**:
  - `adventure_pipeline/README.md` (append "Deferred invariants" section if needed)
  - `adventure_pipeline/specs/verify/*.ark` (already authored in T015;
    may be refined here)
- **Acceptance Criteria**:
  - `python ark/ark.py verify adventure_pipeline/specs/verify/state_transitions.ark`
    exits 0 **OR** README has a documented deferral.
  - Same for `permission_coverage.ark` and `tc_traceability.ark`.
  - `ark/**` remains untouched (git diff on `ark/` is empty).
- **Target Conditions**: TC-045
- **Depends On**: [ADV009-T015]
- **Optional**: yes — marker `priority: deferrable`. Skipping this task
  does NOT fail the adventure, but the TC stays `pending` with a
  `deferred` note.
- **Evaluation**:
  - Access requirements: Read, Write, Bash (python ark/ark.py verify)
  - Skill set: Ark verifier, Z3 invariants
  - Estimated duration: 18 min
  - Estimated tokens: 35000
