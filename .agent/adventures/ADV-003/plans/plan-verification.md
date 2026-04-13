# Verification — Z3 Studio Checks

## Designs Covered
- design-z3-verification: Z3 verification for studio hierarchy

## Tasks

### Implement escalation acyclicity verification
- **ID**: ADV003-T006
- **Description**: Create tools/verify/studio_verify.py with verify_escalation_acyclicity() function. Build directed graph from role.escalates_to edges. Use Z3 Int ordinals to prove no cycles. Integrate into ark_verify.py verify flow.
- **Files**: tools/verify/studio_verify.py, tools/verify/ark_verify.py
- **Acceptance Criteria**:
  - Detects cycles in escalation graph and reports all roles in the cycle
  - Passes for valid acyclic hierarchies
  - Returns VerifyResult dicts consistent with existing verify output
- **Target Conditions**: TC-010
- **Depends On**: [ADV003-T005]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, z3-solver
  - Estimated duration: 20min
  - Estimated tokens: 25000

### Implement command-role resolution and hook/rule verification
- **ID**: ADV003-T007
- **Description**: Add verify_command_resolution(), verify_hook_events(), verify_rule_satisfiability(), and verify_tool_permissions() to studio_verify.py. Each returns VerifyResult dicts. Wire all into a unified verify_studio() entry point called from ark_verify.py.
- **Files**: tools/verify/studio_verify.py, tools/verify/ark_verify.py
- **Acceptance Criteria**:
  - Command resolution catches missing roles and reports them
  - Hook event validation catches invalid event types
  - Rule satisfiability uses Z3 SAT check
  - Tool permission check detects violations
  - All checks integrated into verify_studio() flow
- **Target Conditions**: TC-011, TC-012, TC-013, TC-014
- **Depends On**: [ADV003-T006]
- **Evaluation**:
  - Access requirements: Read, Write, Bash
  - Skill set: python, z3-solver
  - Estimated duration: 25min
  - Estimated tokens: 30000
