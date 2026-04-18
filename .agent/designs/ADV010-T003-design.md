# Event Payload Schema Contract - Design

## Approach

Verify and finalize the three schema documents (`event_payload.md`, `row_schema.md`, `processes.md`) so they serve as the single source of truth for the capture pipeline. Cross-reference against `design-capture-contract.md` and `design-hook-integration.md` to ensure field names, types, constraints, and alias mappings are consistent. Update the alias table in `design-hook-integration.md` only if the existing schemas use different field names than the wire payload.

This is a documentation-only task. No Python code is written. The deliverables are three finalized schema files that downstream implementation tasks (T004 schema.py, T005 capture.py) will code against.

## Target Files

- `.agent/adventures/ADV-010/schemas/event_payload.md` - Finalize the SubagentEvent dataclass specification with every required field, its type, and validation constraints. Currently has 12 fields listed; verify completeness against design-capture-contract.md and design-hook-integration.md.
- `.agent/adventures/ADV-010/schemas/row_schema.md` - Finalize the MetricsRow specification declaring all 12 columns in fixed order with types, derivation rules, and the ManifestEvaluationRow specification. Currently has columns listed but needs verification of column order and completeness.
- `.agent/adventures/ADV-010/schemas/processes.md` - Finalize the 3 workflow descriptions (live capture, backfill, task actuals). Currently documented but needs verification against the full design set.
- `.agent/adventures/ADV-010/designs/design-hook-integration.md` - Update alias table only (section "Hook payload") if any wire-to-internal field name mapping has drifted from the schemas.

## Implementation Steps

1. **Read and cross-reference sources.** Compare `event_payload.md` field list against `design-capture-contract.md` SubagentEvent dataclass definition and `design-hook-integration.md` wire payload JSON example. Identify any field name, type, or constraint mismatches.

2. **Finalize `event_payload.md`.** Ensure it contains:
   - All 12 fields from SubagentEvent (event_type, timestamp, adventure_id, agent, task, model, tokens_in, tokens_out, duration_ms, turns, result, session_id)
   - For each field: Python type annotation, required/optional status, validation constraint (regex pattern, value range, enum set)
   - The wire-to-internal alias mapping table (mirroring design-hook-integration.md)
   - The adventure_id resolution order (5-step fallback from design-hook-integration.md)
   - The validation error catalog (6 rejection cases from design-capture-contract.md)

3. **Finalize `row_schema.md`.** Ensure it declares all 12 columns in the exact order specified by design-capture-contract.md:
   - Run ID (str, 12 hex chars, SHA-1 derivation formula)
   - Timestamp (str, ISO-8601 UTC)
   - Agent (str)
   - Task (str, task ID or literal `-`)
   - Model (str, normalized family)
   - Tokens In (int, non-negative)
   - Tokens Out (int, non-negative)
   - Duration (s) (int, positive, derived from duration_ms)
   - Turns (int, non-negative)
   - Cost (USD) (float, 4dp, derived from cost_model)
   - Result (str, enum set)
   - Confidence (str, high|medium|low|estimated)
   Also verify MetricsFrontmatter fields and ManifestEvaluationRow columns (10 columns).

4. **Finalize `processes.md`.** Verify the 3 workflows cover:
   - Live capture: hook trigger -> stdin parse -> normalize -> validate -> build_row -> append (idempotent) -> recompute frontmatter -> task_actuals (conditional) -> exit 0
   - Backfill: CLI invocation -> evidence collection from 4 reconstructors -> merge candidates -> write .new file -> diff -> optional apply + aggregate
   - Task-actuals propagation: trigger condition -> parse manifest evaluations table -> find task row -> compute actuals from metrics rows -> rewrite row in place -> atomic rename

5. **Cross-check alias table.** Verify the 5-row alias table in `design-hook-integration.md` matches the wire payload field names used in event_payload.md. Update only if mismatched.

## Testing Strategy

This task produces documentation, not code. Verification is by review:
- Each field in event_payload.md must have a corresponding entry in design-capture-contract.md's SubagentEvent dataclass.
- Each column in row_schema.md must appear in design-capture-contract.md's row shape section.
- Each process in processes.md must correspond to a flow described in design-capture-contract.md or design-hook-integration.md.
- The alias table in design-hook-integration.md must be consistent with event_payload.md's wire-vs-internal naming.

Downstream automated verification comes from T016 (test implementation) which will have schema tests that enforce column order, field types, and validation rules against these specifications.

## Risks

- **Schema documents may already be complete.** The existing drafts appear well-aligned with the design docs. The implementer should verify rather than assume, but should not introduce gratuitous changes.
- **Alias table drift.** If the implementer updates field names in event_payload.md without updating the alias table in design-hook-integration.md, downstream tasks (T005 capture.py) will have conflicting specifications. The cross-check in step 5 guards against this.
- **Scope creep.** This task must not add fields or columns beyond what the design docs specify. Any proposed additions must be escalated via the research doc's "Open escalations" section.
