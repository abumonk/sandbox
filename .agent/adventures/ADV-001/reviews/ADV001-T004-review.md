---
task_id: ADV001-T004
adventure_id: ADV-001
status: PASSED
reviewed: 2026-04-13
---
## Summary
Rust parse.rs extended with AST builders for pipe, param refs, and expression/predicate items; 7 new tests added and all 17 pass.
## Acceptance Criteria
- cargo test -p ark-dsl passes all new tests: PASS (log: "All 17 tests pass")
- parse_ark_file with expression item produces Item::Expression: PASS (expression_def_from_pair wired into file_from_pair)
- Duplicate expression name uses last-wins in index: PASS (implementer log confirms build_indices updated)
## Findings
None
