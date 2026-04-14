# Visual Verification

## Designs Covered
- design-visual-verification: Z3-based verification checks for visual items

## Tasks

### Create visual verifier with Z3 checks
- **ID**: ADV006-T014
- **Description**: Create `ark/tools/verify/visual_verify.py`. Implement `verify_visual()` with 5 Z3-based checks: diagram type validity, visual review target resolution, annotation bounds checking, render config validity (positive dimensions), and review cycle acyclicity (ordinal assignment). Follow studio_verify.py pattern.
- **Files**: `ark/tools/verify/visual_verify.py`
- **Acceptance Criteria**:
  - Every diagram type checked against valid DiagramType variants
  - Every visual_review target checked against existing item names
  - Z3 proves annotation coordinates within viewport bounds (when specified)
  - Z3 proves render_config dimensions are positive integers
  - Z3 ordinals prove review cycles are acyclic
  - Return format matches ark_verify.py conventions (check/status/message dicts)
  - Integrated into pipeline when visual items detected
- **Target Conditions**: TC-025, TC-026, TC-027, TC-028, TC-029
- **Depends On**: [ADV006-T005]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, z3-solver, SMT, ark verification patterns
  - Estimated duration: 25min
  - Estimated tokens: 35000

### Integrate visual verify into pipeline
- **ID**: ADV006-T015
- **Description**: Update `ark/ark.py` pipeline command to detect visual items and call `visual_verify.verify_visual()` alongside existing verification. Add `ark visual verify <file.ark>` sub-command. Ensure visual verification runs in the `ark pipeline` flow when visual items are present.
- **Files**: `ark/ark.py`
- **Acceptance Criteria**:
  - `ark visual verify <file.ark>` runs visual verification
  - `ark pipeline <file.ark>` auto-detects visual items and runs visual verify
  - Failed visual checks reported in pipeline output
  - No regression in existing verify behavior
- **Target Conditions**: TC-025, TC-029
- **Depends On**: [ADV006-T013, ADV006-T014]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, CLI integration
  - Estimated duration: 10min
  - Estimated tokens: 12000
