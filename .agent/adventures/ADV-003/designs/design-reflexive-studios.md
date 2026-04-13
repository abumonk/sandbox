# Reflexive Studio Specs — Design

## Overview
Author two studio .ark specifications: (1) `ark_studio.ark` describing Ark's own development team (~8-10 roles), and (2) `game_studio.ark` porting a representative subset of the upstream 49-role game studio hierarchy (~15-20 roles, ~20 commands, ~6 hooks, ~5 rules, ~10 templates).

## Target Files
- `specs/meta/ark_studio.ark` — Ark's own team as a studio hierarchy
- `specs/meta/game_studio.ark` — Game studio exemplar (representative subset)

## Approach

### ark_studio.ark (Reflexive Use-Case)

Describes the actual Ark development roles from `.agent/roles/`:

```ark
import stdlib.types
import stdlib.studio

// Ark development roles
role Lead {
    tier: 1
    description: "Technical lead — architecture, coordination, approvals"
    escalates_to: null  // top of chain
    skills: [architecture, planning, review]
    tools: [Read, Glob, Grep, Write, Edit, Bash, WebSearch, WebFetch]
}

role Planner {
    tier: 2
    description: "Creates designs, breaks down tasks, explores codebase"
    escalates_to: Lead
    skills: [architecture, design, analysis]
    tools: [Read, Glob, Grep, Write, Edit, WebSearch, WebFetch]
}

role Coder {
    tier: 3
    description: "Implements features, writes code, runs tests"
    escalates_to: Planner
    skills: [python, rust, testing]
    tools: [Read, Glob, Grep, Write, Edit, Bash]
}

role CodeReviewer { ... }
role Researcher { ... }
role QATester { ... }
role Messenger { ... }

studio ArkStudio {
    description: "Ark DSL development team"
    tier 1 { Lead }
    tier 2 { Planner }
    tier 3 { Coder, CodeReviewer, Researcher, QATester, Messenger }
}
```

Plus ~3 commands (plan, implement, review), ~2 hooks (pre-commit, task-complete), ~2 rules (tests-required, convention-check).

### game_studio.ark (Imported Use-Case)

Representative subset of upstream Game Studios:

**Roles (~18)**:
- Tier 1: CreativeDirector, TechnicalDirector, Producer
- Tier 2: GameDesigner, LeadProgrammer, ArtDirector, AudioLead, NarrativeLead, QALead, ReleaseManager
- Tier 3: GameplayProgrammer, EngineProgrammer, AIProgrammer, ToolsProgrammer, SystemsDesigner, LevelDesigner, TechnicalArtist, SoundDesigner

**Commands (~20)**: start, brainstorm, design_system, create_epics, dev_story, code_review, qa_plan, release_checklist, etc.

**Hooks (~6)**: pre_commit_validate, post_push_notify, asset_naming, session_lifecycle, agent_audit, gap_detection

**Rules (~5)**: gameplay_data_driven, core_zero_alloc, ai_perf_budget, network_server_authority, design_docs_required

**Templates (~10)**: GDD, UXSpec, ADR, SprintPlan, AccessibilityGuide, etc.

### Verification Blocks
Both files include `verify` blocks that exercise the studio verifier:
```ark
verify ArkStudioChecks {
    check escalation_acyclic: studio.ArkStudio.escalation_graph |> is_acyclic
    check all_commands_resolved: studio.ArkStudio.commands |> all_roles_exist
}
```

## Dependencies
- design-grammar-extensions (grammar must support new items)
- design-parser-support (parser must handle new items)
- design-stdlib-schema (types must be available)

## Target Conditions
- TC-023: ark_studio.ark parses without errors and correctly models Ark's team
- TC-024: game_studio.ark parses without errors with ~18 roles, ~20 commands
- TC-025: Both studios pass escalation acyclicity verification
- TC-026: Both studios pass command-role resolution verification
- TC-027: Both files are registered in root.ark
