# Studio Specs — Reflexive and Exemplar

## Designs Covered
- design-reflexive-studios: Ark studio and game studio .ark specifications

## Tasks

### Author ark_studio.ark — Ark's own team hierarchy
- **ID**: ADV003-T011
- **Description**: Create specs/meta/ark_studio.ark defining Ark's development team as a studio hierarchy. Model ~8 roles (Lead, Planner, Coder, CodeReviewer, Researcher, QATester, Messenger, AdventurePlanner), ~3 commands, ~2 hooks, ~2 rules. Include verify block. Register in root.ark.
- **Files**: specs/meta/ark_studio.ark, specs/root.ark
- **Acceptance Criteria**:
  - File parses via `python ark.py parse specs/meta/ark_studio.ark`
  - All roles map to actual .agent/roles/ entries
  - Escalation graph is acyclic (Lead at top)
  - Verify block included with escalation and resolution checks
  - Registered in root.ark registry
- **Target Conditions**: TC-023, TC-025, TC-026, TC-027
- **Depends On**: [ADV003-T005, ADV003-T006]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: ark-dsl
  - Estimated duration: 20min
  - Estimated tokens: 25000

### Author game_studio.ark — Game studio exemplar
- **ID**: ADV003-T012
- **Description**: Create specs/meta/game_studio.ark with a representative subset of the upstream Game Studios hierarchy. Define ~18 roles across 3 tiers, ~20 commands, ~6 hooks, ~5 rules, ~10 templates. Include verify block. Register in root.ark.
- **Files**: specs/meta/game_studio.ark, specs/root.ark
- **Acceptance Criteria**:
  - File parses via `python ark.py parse specs/meta/game_studio.ark`
  - ~18 roles properly organized into 3 tiers
  - ~20 commands reference valid roles
  - Escalation graph is acyclic
  - Verify block included
  - Registered in root.ark registry
- **Target Conditions**: TC-024, TC-025, TC-026, TC-027
- **Depends On**: [ADV003-T005, ADV003-T006]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: ark-dsl
  - Estimated duration: 25min
  - Estimated tokens: 35000

### Run end-to-end pipeline on both studio specs
- **ID**: ADV003-T013
- **Description**: Run the full pipeline (parse -> verify -> codegen -> graph) on both ark_studio.ark and game_studio.ark. Fix any issues. Verify that codegen produces agent .md files and command .md files. Verify that the visualizer renders org-charts.
- **Files**: specs/meta/ark_studio.ark, specs/meta/game_studio.ark
- **Acceptance Criteria**:
  - `python ark.py pipeline specs/meta/ark_studio.ark --target studio` succeeds
  - `python ark.py pipeline specs/meta/game_studio.ark --target studio` succeeds
  - Generated agent .md files are well-formed
  - Generated command .md files are well-formed
  - Org-chart HTML renders correctly
- **Target Conditions**: TC-015, TC-019, TC-020, TC-025
- **Depends On**: [ADV003-T009, ADV003-T010, ADV003-T011, ADV003-T012]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: ark-dsl, testing
  - Estimated duration: 20min
  - Estimated tokens: 20000
