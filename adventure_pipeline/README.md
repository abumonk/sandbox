# adventure_pipeline

## Purpose

Sibling Ark spec package that models the agent pipeline domain —
adventures, phases, waves, tasks, documents, decisions, target conditions,
agents, roles, and permissions — as first-class Ark entities and processes.
Follows the architectural precedent established by `shape_grammar/` (ADV-008):
Ark itself is never modified; the domain is expressed in vanilla Ark syntax
(abstractions, classes, islands, processes, enums). Cross-file unification
happens in the IR extractor (`tools/ir.py`, implemented in T016).

## Layout

```
adventure_pipeline/
├── __init__.py                        # package marker
├── README.md                          # this file
└── specs/
    ├── adventure.ark                  # entity declarations (Adventure, Phase,
    │                                  # Wave, Task, Document + subtypes,
    │                                  # TargetCondition, Decision, Permission,
    │                                  # Agent, Role + 7 enums)
    ├── pipeline.ark                   # process declarations (AdventureStateMachine,
    │                                  # TaskLifecycle, ReviewPipeline)
    ├── entities.ark                   # runtime snapshot entities (RunningAgent,
    │                                  # ActiveTask, PendingDecision,
    │                                  # KnowledgeSuggestion, ReviewArtifact)
    └── verify/
        ├── state_transitions.ark      # verify block: absorbing-terminal,
        │                              # blocked-reentry invariants
        ├── permission_coverage.ark    # verify block: permission coverage checks
        └── tc_traceability.ark        # verify block: TC-to-task traceability
```

## Usage

```bash
# Parse entity declarations
python ark/ark.py parse adventure_pipeline/specs/adventure.ark

# Parse process declarations
python ark/ark.py parse adventure_pipeline/specs/pipeline.ark

# Parse runtime entity declarations
python ark/ark.py parse adventure_pipeline/specs/entities.ark

# Parse verification specs
python ark/ark.py parse adventure_pipeline/specs/verify/state_transitions.ark
python ark/ark.py parse adventure_pipeline/specs/verify/permission_coverage.ark
python ark/ark.py parse adventure_pipeline/specs/verify/tc_traceability.ark

# IR extraction (implemented in T016)
# python adventure_pipeline/tools/ir.py .agent/adventures/ADV-NNN/
```

## Deferred invariants

The following invariants were not expressible in or not evaluated by the vanilla
Ark verifier (as of T015–T017) and are deferred to a Python post-IR pass:

- **permission_coverage.ark / every_task_has_permission**: Cross-entity
  existential quantification (`exists Permission as p: p.tasks contains t.id`)
  is not expressible in the Ark `verify` block grammar. The check block
  contains a stub `true` expression. The real check is deferred to T017's
  Python verifier.

- **permission_coverage.ark / shell_covers_proof_command**: Cross-entity
  join between `TargetCondition.proof_command` and `Permission.scope` cannot
  be expressed in a single-entity `verify` block. Deferred to T017.

- **tc_traceability.ark / tc_has_tasks**: The condition `tc.tasks != ""`
  approximates the intended check (every TC references at least one Task id).
  Full referential integrity (ids exist in the Task set) is deferred to T017.

- **tc_traceability.ark / task_has_tc**: The condition `t.target_conditions != ""`
  approximates the intended check. Full cardinality and referential integrity
  deferred to T017.

- **state_transitions.ark, permission_coverage.ark, tc_traceability.ark /
  standalone verify-block checks (terminal_absorbing, non_terminal_state_valid,
  permission_has_agent, task_has_id, tc_has_tasks, task_has_tc)**: The vanilla
  Ark verifier (`ark_verify.py`) processes items of kind `abstraction`, `class`,
  and `island` only. Standalone `verify { check ... for_all ... }` blocks
  (AST kind: `"verify"`) are parsed and round-trip cleanly but are silently
  skipped by `verify_file` — the `for_all` quantifier checks in these blocks
  are not dispatched to Z3. All three specs exit 0 because the verifier runs
  against the stub class declarations only (enum default checks, temporal BMC),
  not the intended semantic invariants.
  Rationale: vanilla Ark lacks a verifier dispatch path for top-level
  `verify ClassName { check ... }` items; adding one would require patching
  `ark/tools/verify/ark_verify.py`, which is explicitly prohibited for this task.
  Follow-up: awaiting Ark verifier extension (future adventure — extend
  `verify_file` to dispatch `kind="verify"` items to a new
  `verify_check_block()` function; then re-run this task to upgrade from
  DEFERRED to CLEAN).
