# Z3 Verification for Studio Hierarchy — Design

## Overview
Extend the Z3 verifier to check studio-specific invariants: escalation cycle detection, command-role resolution, hook event validity, rule satisfiability, and tool permission consistency.

## Target Files
- `tools/verify/ark_verify.py` — Add studio verification functions
- `tools/verify/studio_verify.py` — New module for studio-specific Z3 checks (keeps ark_verify.py manageable)

## Approach

### Check 1: Escalation Acyclicity
Build a directed graph from role.escalates_to edges. Use Z3 to prove no cycles exist (every chain terminates at a role with no escalates_to — a Director).

```python
def verify_escalation_acyclicity(roles):
    # Build adjacency: role_name -> escalates_to
    # Z3: assign ordinal to each role, prove escalates_to always increases
    # If SAT with cycle constraint → report cycle
```

### Check 2: Command-Role Resolution
For each command_def, verify that its `role:` field references an existing role in the studio, and that the role's `tools:` set is sufficient for the command's needs.

```python
def verify_command_resolution(commands, roles):
    # For each command: check role exists, check role has required tools
```

### Check 3: Hook Event Validity
Each hook's `event:` must be in the allowed HookEvent enum. Check exhaustively.

```python
def verify_hook_events(hooks, allowed_events):
    # Simple set membership check, but using Z3 for consistency
```

### Check 4: Rule Satisfiability
Each rule's `constraint:` must be satisfiable (not trivially false). Use Z3 to check SAT.

```python
def verify_rule_satisfiability(rules):
    # Parse constraint expression, check Z3 SAT
```

### Check 5: Tool Permission Consistency
Cross-check: no role declares a tool it does not have permission to use. Check against a permissions manifest if available.

```python
def verify_tool_permissions(roles, permissions):
    # roles.tools subset of permissions.allowed_tools
```

### Integration
Add a `verify_studio()` entry point called from `ark_verify.py` when studio items are present in the AST. Follow the existing pattern of returning a list of `VerifyResult` dicts.

## Dependencies
- design-parser-support (need parsed studio AST)
- design-stdlib-schema (need enum values for validation)

## Target Conditions
- TC-010: Escalation cycle detection catches cycles and passes acyclic hierarchies
- TC-011: Command verification catches missing roles and insufficient tools
- TC-012: Hook event verification catches invalid event types
- TC-013: Rule constraint satisfiability check works correctly
- TC-014: Tool permission cross-check detects violations
