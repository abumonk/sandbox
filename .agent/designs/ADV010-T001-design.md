# Telemetry Gap Analysis (Research) - Design

## Approach

T001 is a research-verification task. The planner has already drafted
`research/telemetry-gap-analysis.md` with 8 findings (F1-F8). The
implementer's job is to verify every cited file path and line range
against the live repo, amend any drift, and ensure the "Derived
requirements" section is complete. No code is produced; the output is
a validated research document that downstream designs (Wave B-E) depend
on.

## Target Files
- `.agent/adventures/ADV-010/research/telemetry-gap-analysis.md` - Verify and amend the existing draft. Every finding's file path and line range must be checked against current repo state. If line numbers have drifted (e.g., due to commits between planning and implementation), update them in place.

## Implementation Steps

1. **Read the existing draft** at `research/telemetry-gap-analysis.md` in full.

2. **Verify F1 (no hook in settings.local.json)**:
   - Read `.claude/settings.local.json` end-to-end.
   - Confirm there is no `hooks` key at the top level.
   - Confirm the file structure is `{ "permissions": { "allow": [...] } }` only.
   - If a `hooks` key has been added since planning, amend F1 accordingly.

3. **Verify F2 (no `.agent/telemetry/` directory)**:
   - Run `Glob` for `.agent/telemetry/**/*`.
   - If zero matches, confirm the finding as-is.
   - If the directory was created by another task, note which files exist and whether F2 is partially or fully resolved.

4. **Verify F3 (frontmatter aggregation gap)**:
   - Read frontmatter (lines 1-8) of `ADV-001/metrics.md` through `ADV-010/metrics.md`.
   - For each, compare `agent_runs` in frontmatter vs actual row count in the Agent Runs table.
   - Confirm the specific examples cited (ADV-001 all zeros with 14+ rows, ADV-008 partial, ADV-009 zeros).
   - Update line references if rows have been added/removed.

5. **Verify F4 (no task-actuals propagation)**:
   - Read `ADV-008/manifest.md` and locate the `## Evaluations` table.
   - Confirm the cited line range (L69-L80) still contains em-dash placeholders in actual columns.
   - Spot-check one other adventure's manifest for comparison.

6. **Verify F5 (cost model rates unused)**:
   - Read `.agent/config.md` L17-L20 and confirm `token_cost_per_1k` block exists.
   - Grep for `token_cost_per_1k` or `cost_model` across all `.py` files to confirm no consumer exists.
   - Update line numbers if config.md has been modified.

7. **Verify F6 (row schema drift)**:
   - Read the header row of 3+ `metrics.md` files and confirm the column set matches the finding's claim (no adventure_id, no timestamp, no run_id, no cost column).
   - Check 2-3 rows for mixed Duration formats (e.g., `16min`, `95s`, `~10min`).

8. **Verify F7 (tilde estimates)**:
   - In `ADV-001/metrics.md`, count rows with `~` prefix on token columns.
   - Confirm "14 of 14 rows" claim or update if the count has changed.
   - Spot-check `ADV-008/metrics.md` for mixed tilde/bare format.

9. **Verify F8 (unreliable log timestamps)**:
   - Read `ADV-008/adventure.log` around lines 25-27.
   - Confirm the non-monotonic timestamp example is still present.
   - Cross-reference with `knowledge/issues.md` "Log Timestamp Placeholders" entry.

10. **Verify Derived Requirements section**:
    - Confirm the 5 modules listed (`capture.py`, `cost_model.py`, `aggregator.py`, `task_actuals.py`, `schema.py`) match what the design docs expect.
    - Cross-check against `design-capture-contract.md` target files section.
    - If any design doc names a module not listed in derived requirements, add it.

11. **Verify Constraints section**:
    - Confirm "Python stdlib only" constraint is consistent with design docs.
    - Confirm "do not modify ark/" is consistent with `knowledge/patterns.md`.
    - Confirm backfill reversibility constraint matches `design-backfill-strategy.md`.

12. **Final pass**: Re-read the complete document, fix any broken markdown formatting, ensure finding numbering is sequential, and confirm the evidence base file list at the top is accurate.

## Testing Strategy

This is a research task with no code output. Verification is by acceptance criteria:
- Count findings: must be >= 8 (currently exactly 8).
- For each finding, confirm the cited file path exists and the line range contains the described content.
- Confirm "Derived requirements" lists modules under `.agent/telemetry/` with one-line purpose each.

The reviewer should spot-check 3+ findings by independently reading the cited files and confirming the current-vs-expected gap description is accurate.

## Risks

1. **Line number drift**: If other tasks have modified the cited files between planning (2026-04-15) and implementation, line numbers may be off. This is the primary expected amendment — the implementer should update line refs without changing the finding's substance.
2. **New findings**: The implementer may discover a 9th+ finding while verifying. This is acceptable and encouraged — the AC says "at least 8."
3. **Partial resolution**: If Wave B tasks have already started (unlikely since T001 is a Wave A prerequisite), some findings may be partially resolved. The implementer should note partial resolution but keep the finding for historical record, marking it with a status indicator.
