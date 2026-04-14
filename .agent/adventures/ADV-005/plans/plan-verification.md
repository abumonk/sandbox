# Verification — Agent Z3 Checks

## Designs Covered
- design-verification: Agent-specific Z3 verification checks

## Tasks

### Create agent verification module
- **ID**: ADV005-T012
- **Description**: Create `tools/verify/agent_verify.py` with 6 verification checks: gateway reference validity, cron task reference validity, model fallback acyclicity (Z3 ordinals), resource limit positivity (Z3 bounds), skill trigger overlap detection (Z3 string regex), and agent completeness. Follow studio_verify.py pattern.
- **Files**: ark/tools/verify/agent_verify.py
- **Acceptance Criteria**:
  - verify_gateway_references catches invalid agent/platform refs
  - verify_cron_references catches invalid agent/platform refs
  - verify_model_fallback_acyclicity detects cycles via Z3
  - verify_resource_limits catches non-positive/out-of-bounds values
  - verify_skill_trigger_overlap warns on ambiguous triggers
  - verify_agent_completeness catches missing model/backend refs
  - verify_agent entry point runs all checks
- **Target Conditions**: TC-024, TC-025, TC-026, TC-027, TC-028, TC-029
- **Depends On**: [ADV005-T005]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, z3-solver
  - Estimated duration: 30min
  - Estimated tokens: 45000

### Integrate agent verify into ark_verify.py
- **ID**: ADV005-T013
- **Description**: Add agent item detection and verify_agent dispatch to ark_verify.py. When AST contains agent items, import agent_verify and merge results. Also add agent verify path to conftest.py.
- **Files**: ark/tools/verify/ark_verify.py, ark/tests/conftest.py
- **Acceptance Criteria**:
  - ark_verify.py detects agent items and dispatches to agent_verify
  - `python ark.py verify` works on .ark files with agent items
  - conftest.py includes agent verify module path
- **Target Conditions**: TC-024
- **Depends On**: [ADV005-T012]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python
  - Estimated duration: 15min
  - Estimated tokens: 15000
